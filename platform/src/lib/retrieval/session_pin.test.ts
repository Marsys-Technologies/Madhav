/**
 * session_pin.test.ts — R5 W4 session-pin serving unit tests (design §10.6/§31.3/§31.5).
 *
 * Covers the PURE logic only (detectBuildDrift, readPinFromState, buildPinPatch) —
 * no DB required. The DB-backed functions (getLatestChartBuild, computeCurrentPinValues,
 * resolveSessionPin) are exercised by `sessions.integration.test.ts` against the real
 * mcp_sessions + builds tables (live Cloud SQL, per the brief's mandate to verify against
 * an actual gate, not just unit mocks).
 */
import { describe, it, expect } from 'vitest'
import {
  detectBuildDrift,
  readPinFromState,
  buildPinPatch,
  type SessionPinValues,
} from './session_pin'

const CHART_A = '11111111-1111-1111-1111-111111111111'
const CHART_B = '22222222-2222-2222-2222-222222222222'

function makePin(overrides: Partial<SessionPinValues> = {}): SessionPinValues {
  return {
    chart_id: CHART_A,
    priors_version: '1.0',
    formula_versions: { salience_formula_ver: 'v1' },
    ranking_config: { mode: 'composite_v1' },
    build_id: 'build-1',
    build_status: 'complete',
    ledger_version: '3:1800000000',
    now_context_date: '2026-07-09',
    pinned_at: '2026-07-09T00:00:00.000Z',
    ...overrides,
  }
}

/** Strip pinned_at — detectBuildDrift's `current` param never carries it (see signature). */
function asCurrent(pin: SessionPinValues): Omit<SessionPinValues, 'pinned_at'> {
  const { pinned_at, ...rest } = pin
  void pinned_at
  return rest
}

describe('detectBuildDrift', () => {
  it('reports no drift when there is no existing pin (first pin of the session)', () => {
    const result = detectBuildDrift(null, asCurrent(makePin()))
    expect(result.drift).toBe(false)
    expect(result.judgment_flags).toEqual([])
  })

  it('reports no drift when build_id is unchanged', () => {
    const existing = makePin({ build_id: 'build-1' })
    const current = asCurrent(makePin({ build_id: 'build-1', pinned_at: 'later' }))
    const result = detectBuildDrift(existing, current)
    expect(result.drift).toBe(false)
    expect(result.judgment_flags).toEqual([])
  })

  it('detects drift and raises the exact judgment_flag when build_id changes (design §31.5)', () => {
    const existing = makePin({ build_id: 'build-1' })
    const current = asCurrent(makePin({ build_id: 'build-2' }))
    const result = detectBuildDrift(existing, current)
    expect(result.drift).toBe(true)
    expect(result.judgment_flags).toEqual(['chart_rebuilt_mid_session_pin_refreshed'])
  })

  it('detects drift when the chart had no build before and now has one (null -> value)', () => {
    const existing = makePin({ build_id: null })
    const current = asCurrent(makePin({ build_id: 'build-1' }))
    const result = detectBuildDrift(existing, current)
    expect(result.drift).toBe(true)
  })

  // W3-L8 (RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-3/4, W-26): ledger_version is a SECOND,
  // independent drift signal alongside build_id.
  it('reports no drift when ledger_version is unchanged', () => {
    const existing = makePin({ ledger_version: '3:1800000000' })
    const current = asCurrent(makePin({ ledger_version: '3:1800000000', pinned_at: 'later' }))
    const result = detectBuildDrift(existing, current)
    expect(result.drift).toBe(false)
    expect(result.judgment_flags).toEqual([])
  })

  it('detects drift and raises the exact judgment_flag when ledger_version changes but build_id does not', () => {
    const existing = makePin({ build_id: 'build-1', ledger_version: '3:1800000000' })
    const current = asCurrent(makePin({ build_id: 'build-1', ledger_version: '4:1800000600' }))
    const result = detectBuildDrift(existing, current)
    expect(result.drift).toBe(true)
    expect(result.judgment_flags).toEqual(['concept_ledger_updated_mid_session_pin_refreshed'])
  })

  it('detects drift when the ledger had no rows before and now has some (null -> value)', () => {
    const existing = makePin({ ledger_version: null })
    const current = asCurrent(makePin({ ledger_version: '1:1800000000' }))
    const result = detectBuildDrift(existing, current)
    expect(result.drift).toBe(true)
    expect(result.judgment_flags).toEqual(['concept_ledger_updated_mid_session_pin_refreshed'])
  })

  it('raises BOTH flags when build_id and ledger_version drift in the same resolution (signals collected, not short-circuited)', () => {
    const existing = makePin({ build_id: 'build-1', ledger_version: '3:1800000000' })
    const current = asCurrent(makePin({ build_id: 'build-2', ledger_version: '4:1800000600' }))
    const result = detectBuildDrift(existing, current)
    expect(result.drift).toBe(true)
    expect(result.judgment_flags).toEqual([
      'chart_rebuilt_mid_session_pin_refreshed',
      'concept_ledger_updated_mid_session_pin_refreshed',
    ])
  })
})

describe('readPinFromState / buildPinPatch (chart_id re-keying, design §31.3)', () => {
  it('returns null when state_json has no pins block', () => {
    expect(readPinFromState({}, CHART_A)).toBeNull()
    expect(readPinFromState(null, CHART_A)).toBeNull()
    expect(readPinFromState(undefined, CHART_A)).toBeNull()
  })

  it('returns null when the requested chart has no pin yet, even if others do', () => {
    const pin = makePin()
    const state = buildPinPatch({}, CHART_A, pin)
    expect(readPinFromState(state, CHART_B)).toBeNull()
  })

  it('round-trips a pin through buildPinPatch -> readPinFromState', () => {
    const pin = makePin()
    const state = buildPinPatch({}, CHART_A, pin)
    expect(readPinFromState(state, CHART_A)).toEqual(pin)
  })

  it('re-keys by chart_id: pinning chart B does not clobber an existing pin for chart A (the §31.3 mitigation)', () => {
    const pinA = makePin({ chart_id: CHART_A, build_id: 'build-a' })
    const pinB = makePin({ chart_id: CHART_B, build_id: 'build-b' })

    const afterA = buildPinPatch({}, CHART_A, pinA)
    const afterB = buildPinPatch(afterA, CHART_B, pinB)

    expect(readPinFromState(afterB, CHART_A)).toEqual(pinA)
    expect(readPinFromState(afterB, CHART_B)).toEqual(pinB)
  })

  it('preserves other keys already present in state_json (additive patch)', () => {
    const pin = makePin()
    const state = buildPinPatch({ some_other_key: 'value' }, CHART_A, pin)
    expect(state['some_other_key']).toBe('value')
    expect(readPinFromState(state, CHART_A)).toEqual(pin)
  })

  it('replaces (not merges) an existing pin for the same chart_id on refresh', () => {
    const pinV1 = makePin({ build_id: 'build-1' })
    const pinV2 = makePin({ build_id: 'build-2', pinned_at: 'later' })

    const stateV1 = buildPinPatch({}, CHART_A, pinV1)
    const stateV2 = buildPinPatch(stateV1, CHART_A, pinV2)

    expect(readPinFromState(stateV2, CHART_A)).toEqual(pinV2)
  })
})

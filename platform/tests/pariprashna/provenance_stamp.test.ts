/**
 * Paripraśna Build — PB-2 (SMṚTI), Lane M-6: provenance-stamp unit tests.
 *
 * Covers `src/lib/pariprashna/provenance/stamp.ts`:
 *   1. computeTurnProvenanceStamp — shapes the five D-16 fields + computed_at
 *      from the (mocked) live `computeCurrentPinValues` source, with a
 *      genuinely-populated `now_context_date`.
 *   2. getLastTurnStamp — the PB-3 read API; reads the most recent persisted
 *      assistant turn's stamp, tolerating absent/malformed metadata honestly
 *      (returns null, never throws/fabricates).
 *   3. detectTurnProvenanceDrift — consecutive-turn-only comparison; a
 *      build_id change is the ONLY drift signal and renders the EXACT PB-1
 *      lexicon string (EDGE_STATE_LABELS.chart_rebuilt) — this is the "drift
 *      fixture" the M-6 brief asks for.
 *   4. withProvenanceStamp — additive merge, never clobbers sibling keys.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Hoisted mocks ────────────────────────────────────────────────────────────

const { queryMock, computeCurrentPinValuesMock } = vi.hoisted(() => {
  const queryMock = vi.fn()
  const computeCurrentPinValuesMock = vi.fn()
  return { queryMock, computeCurrentPinValuesMock }
})

vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('@/lib/retrieval/provenance_stamp', () => ({
  computeCurrentPinValues: computeCurrentPinValuesMock,
}))

import {
  computeTurnProvenanceStamp,
  getLastTurnStamp,
  detectTurnProvenanceDrift,
  withProvenanceStamp,
  type TurnProvenanceStamp,
} from '@/lib/pariprashna/provenance/stamp'
import { EDGE_STATE_LABELS } from '@/lib/pariprashna/lexicon'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const CONVERSATION_ID = 'c0000000-0000-0000-0000-000000000001'

function makeStamp(overrides: Partial<TurnProvenanceStamp> = {}): TurnProvenanceStamp {
  return {
    build_id: 'build-1',
    priors_version: '1.2',
    formula_versions: { salience_formula_ver: null },
    ranking_config: { mode: 'composite_v1' },
    now_context_date: '2026-07-28',
    computed_at: '2026-07-28T10:00:00.000Z',
    ...overrides,
  }
}

beforeEach(() => {
  queryMock.mockReset()
  computeCurrentPinValuesMock.mockReset()
})

// ─────────────────────────────────────────────────────────────────────────────
describe('computeTurnProvenanceStamp', () => {
  it('shapes the five D-16 fields from the live pin-value source, plus computed_at', async () => {
    computeCurrentPinValuesMock.mockResolvedValue({
      chart_id: CHART_ID,
      build_id: 'build-42',
      build_status: 'completed',
      priors_version: '1.2',
      formula_versions: { salience_formula_ver: null },
      ranking_config: { mode: 'composite_v1' },
      ledger_version: '3:1800000000',
      now_context_date: '2026-07-28',
    })

    const stamp = await computeTurnProvenanceStamp(CHART_ID)

    expect(computeCurrentPinValuesMock).toHaveBeenCalledWith(CHART_ID)
    expect(stamp.build_id).toBe('build-42')
    expect(stamp.priors_version).toBe('1.2')
    expect(stamp.formula_versions).toEqual({ salience_formula_ver: null })
    expect(stamp.ranking_config).toEqual({ mode: 'composite_v1' })
    // now_context_date is genuinely populated (not a stub) — carried verbatim
    // from the live source, never hardcoded here.
    expect(stamp.now_context_date).toBe('2026-07-28')
    expect(typeof stamp.computed_at).toBe('string')
    expect(() => new Date(stamp.computed_at).toISOString()).not.toThrow()
    // build_status / ledger_version / chart_id are NOT part of the immutable
    // per-turn stamp shape (out of the five D-16 fields) — dropped, not leaked.
    expect(stamp).not.toHaveProperty('build_status')
    expect(stamp).not.toHaveProperty('ledger_version')
    expect(stamp).not.toHaveProperty('chart_id')
  })

  it('honestly carries a null build_id through when the chart has no completed build', async () => {
    computeCurrentPinValuesMock.mockResolvedValue({
      chart_id: CHART_ID,
      build_id: null,
      build_status: null,
      priors_version: '1.2',
      formula_versions: { salience_formula_ver: null },
      ranking_config: { mode: 'composite_v1' },
      ledger_version: null,
      now_context_date: '2026-07-28',
    })
    const stamp = await computeTurnProvenanceStamp(CHART_ID)
    expect(stamp.build_id).toBeNull()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
describe('getLastTurnStamp — PB-3 ledger-confirmation read API', () => {
  it('returns null when the conversation has no prior assistant row', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })
    const result = await getLastTurnStamp(CONVERSATION_ID)
    expect(result).toBeNull()
  })

  it('returns null when the last assistant row has no provenance_stamp (pre-M-6 turn)', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ metadata_json: { custom: { model: 'x' } } }] })
    const result = await getLastTurnStamp(CONVERSATION_ID)
    expect(result).toBeNull()
  })

  it('returns null (never throws) when metadata_json.provenance_stamp is malformed', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ metadata_json: { provenance_stamp: 'not-an-object' } }] })
    const result = await getLastTurnStamp(CONVERSATION_ID)
    expect(result).toBeNull()
  })

  it('returns the stamp verbatim when the last assistant row carries a well-formed one', async () => {
    const stamp = makeStamp({ build_id: 'build-7' })
    queryMock.mockResolvedValueOnce({ rows: [{ metadata_json: { custom: {}, provenance_stamp: stamp } }] })
    const result = await getLastTurnStamp(CONVERSATION_ID)
    expect(result).toEqual(stamp)
  })

  it('queries scoped to conversation_id + role=assistant, most recent first', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })
    await getLastTurnStamp(CONVERSATION_ID)
    const [sql, params] = queryMock.mock.calls[0]
    expect(sql).toMatch(/role = 'assistant'/)
    expect(sql).toMatch(/ORDER BY created_at DESC/)
    expect(sql).toMatch(/LIMIT 1/)
    expect(params).toEqual([CONVERSATION_ID])
  })
})

// ─────────────────────────────────────────────────────────────────────────────
describe('detectTurnProvenanceDrift — consecutive-turn comparison, build_id-only signal', () => {
  it('reports no drift on the first turn (no previous stamp)', () => {
    const result = detectTurnProvenanceDrift(null, makeStamp())
    expect(result.drift).toBe(false)
    expect(result.edge_state_label).toBeNull()
    expect(result.changed_fields).toEqual([])
  })

  it('reports no drift when build_id is unchanged across consecutive turns', () => {
    const previous = makeStamp({ build_id: 'build-1' })
    const current = makeStamp({ build_id: 'build-1', computed_at: '2026-07-28T10:05:00.000Z' })
    const result = detectTurnProvenanceDrift(previous, current)
    expect(result.drift).toBe(false)
    expect(result.edge_state_label).toBeNull()
  })

  // ── THE DRIFT FIXTURE ────────────────────────────────────────────────────
  it('detects drift when build_id changes and renders the EXACT PB-1 lexicon string', () => {
    const previous = makeStamp({ build_id: 'build-1' })
    const current = makeStamp({ build_id: 'build-2' })
    const result = detectTurnProvenanceDrift(previous, current)

    expect(result.drift).toBe(true)
    expect(result.changed_fields).toEqual(['build_id'])
    // Reused verbatim from lexicon.ts's EDGE_STATE_LABELS — never invented copy.
    expect(result.edge_state_label).toBe(EDGE_STATE_LABELS.chart_rebuilt)
    expect(result.edge_state_label).toBe('The chart has been rebuilt — re-reading')
  })

  it('detects drift on null -> value (chart completed its first build since the last turn)', () => {
    const previous = makeStamp({ build_id: null })
    const current = makeStamp({ build_id: 'build-1' })
    const result = detectTurnProvenanceDrift(previous, current)
    expect(result.drift).toBe(true)
    expect(result.edge_state_label).toBe(EDGE_STATE_LABELS.chart_rebuilt)
  })

  it('does NOT drift on a priors_version-only change (process-wide constant, deploy-scoped)', () => {
    const previous = makeStamp({ priors_version: '1.1' })
    const current = makeStamp({ priors_version: '1.2' })
    const result = detectTurnProvenanceDrift(previous, current)
    expect(result.drift).toBe(false)
    expect(result.changed_fields).toEqual([])
  })

  it('does NOT drift on a ranking_config-only change', () => {
    const previous = makeStamp({ ranking_config: { mode: 'composite_v1' } })
    const current = makeStamp({ ranking_config: { mode: 'composite_v2' } })
    const result = detectTurnProvenanceDrift(previous, current)
    expect(result.drift).toBe(false)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
describe('withProvenanceStamp — additive merge', () => {
  it('adds provenance_stamp as a sibling key without touching existing keys', () => {
    const stamp = makeStamp()
    const metadata = withProvenanceStamp({ custom: { model: 'x', queryId: 'q-1' } }, stamp)
    expect(metadata.custom).toEqual({ model: 'x', queryId: 'q-1' })
    expect(metadata.provenance_stamp).toEqual(stamp)
  })
})

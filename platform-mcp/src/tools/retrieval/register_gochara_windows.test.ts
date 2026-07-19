/**
 * register_gochara_windows.test.ts — D-5 Lane G-4 serving-tool tests.
 *
 * Pure/structural tests (no DB): `dominantGraha` graha-resolution logic and
 * the §N.6 density_contract shapes. A DB-backed integration check
 * (`DATABASE_URL`-guarded, skipped when unset — same discipline as this
 * lane's Python `@pytest.mark.integration` tests) proves the three compute*
 * functions return real, shape-correct rows against the live proxy.
 */
import { describe, it, expect } from 'vitest'
import {
  dominantGraha,
  computeGocharaActivation,
  computeGocharaForecast,
  computeGocharaElectionAvoidance,
  type GocharaWindowRow,
} from './register_gochara_windows.js'

function makeRow(overrides: Partial<GocharaWindowRow> = {}): GocharaWindowRow {
  return {
    id: 1,
    chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
    event_class: 'marriage',
    temporal_shape: 'point',
    window_start: '2013-12-11',
    window_end: '2013-12-11',
    peak_date: '2013-12-11',
    milestone_id: null,
    is_irreversibility_milestone: false,
    signed_intensity: 1.2,
    raw_intensity: 1.2,
    valence: 'neutral',
    is_adverse: false,
    active_sentences: [],
    contributing_systems: [],
    suppression_state: {},
    peak_basis: 'gochara_lambda_e_v1',
    calibration_state: 'structural_prior',
    source: 'live',
    computed_at: '2026-07-19T00:00:00Z',
    ...overrides,
  }
}

describe('dominantGraha', () => {
  it('returns null when no systems are active', () => {
    expect(dominantGraha(makeRow({ contributing_systems: [] }))).toBeNull()
  })

  it('returns null when active systems carry no graha detail', () => {
    const row = makeRow({
      contributing_systems: [{ system_id: 'av_threshold', active: true, weight: 0.06, detail: {} }],
    })
    expect(dominantGraha(row)).toBeNull()
  })

  it('resolves a lord_graha from an active system detail', () => {
    const row = makeRow({
      contributing_systems: [
        { system_id: 'vimshottari', active: true, weight: 0.16, detail: { lord_graha: 'Saturn' } },
      ],
    })
    expect(dominantGraha(row)).toBe('saturn')
  })

  it('ignores inactive systems even if they carry a graha', () => {
    const row = makeRow({
      contributing_systems: [
        { system_id: 'yogini', active: false, weight: 0.07, detail: { lord_graha: 'Mars' } },
      ],
    })
    expect(dominantGraha(row)).toBeNull()
  })
})

// §N.6 density_contract presence is asserted directly on each tool's
// provenance_envelope in the live-integration checks below (the contract
// consts are module-private; the served INVARIANT — every response carries
// one — is what actually matters and is checked against real output).

// ── Integration (live proxy; skipped when DATABASE_URL is unset) ──────────

const LIVE_DSN = 'postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis'
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIntegration = process.env['RUN_DB_INTEGRATION'] === '1' ? describe : describe.skip

describeIntegration('gochara_*_get — live DB integration', () => {
  it('gochara_activation_get returns a shape-correct envelope for the marriage specimen date', async () => {
    process.env['DATABASE_URL'] = process.env['DATABASE_URL'] ?? LIVE_DSN
    const result = (await computeGocharaActivation(CHART_ID, '2013-12-11', 'marriage')) as {
      windows: GocharaWindowRow[]
      provenance_envelope: Record<string, unknown>
    }
    expect(result.provenance_envelope.density_contract).toBeDefined()
    expect(Array.isArray(result.windows)).toBe(true)
    for (const w of result.windows) {
      expect(w.window_start).toBe(w.window_end)
    }
  })

  it('gochara_forecast_get returns rows overlapping the windfall interval specimen', async () => {
    process.env['DATABASE_URL'] = process.env['DATABASE_URL'] ?? LIVE_DSN
    const result = (await computeGocharaForecast(
      CHART_ID,
      { start: '2010-06-01', end: '2011-04-01' },
      'major_gain',
      undefined,
      50
    )) as { windows: GocharaWindowRow[]; provenance_envelope: Record<string, unknown> }
    expect(result.provenance_envelope.shape_breakdown).toBeDefined()
    for (const w of result.windows) {
      expect(w.temporal_shape).toBe('interval')
      expect(w.window_start < w.window_end).toBe(true)
    }
  })

  it('gochara_election_avoidance_get carries all 5 DR-16 properties on any adverse row', async () => {
    process.env['DATABASE_URL'] = process.env['DATABASE_URL'] ?? LIVE_DSN
    const result = (await computeGocharaElectionAvoidance(
      CHART_ID,
      { start: '1950-01-01', end: '2050-01-01' },
      undefined,
      50
    )) as { windows: Array<Record<string, unknown>>; provenance_envelope: Record<string, unknown> }
    expect(result.provenance_envelope.dr16_properties).toEqual([
      'honest_clarity',
      'probabilistic_never_fatalistic',
      'falsifier_bearing',
      'mitigation_paired',
      'confidence_honest',
    ])
    for (const w of result.windows) {
      expect(w['clarity_statement']).toBeDefined()
      expect(w['framing']).toBeDefined()
      expect(w['falsifier']).toBeDefined()
      expect(w['mitigation']).toBeDefined()
      expect(w['confidence_disclosure']).toBeDefined()
    }
  })
})

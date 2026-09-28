/**
 * register_gochara_windows_era_slice_facet.test.ts — Link 3 conditioning
 * condition (c) (ADK-0023 / ADK-0016 disclosure (i)): the era_slice_key
 * facet declared in all three tools' density_contracts must be a REAL
 * detector in the served response, and a null era slice must never read as
 * "no windows that decade".
 *
 * GOVERNING FACTS:
 *   - Generation '4.0' rows DELIBERATELY carry era_slice_key NULL
 *     (migration 1091 conjunct (g): a non-null era_slice_key inside '4.0'
 *     is read as century-writer contamination; era slicing belongs to the
 *     g3_% generations only). A decade-filtered read over '4.0' therefore
 *     returns silent empty BY CONSTRUCTION — a false negative unless the
 *     response itself discloses the boundary.
 *   - computeWindowFacets now computes facets.era_slice_key =
 *     { by_key, null_count, null_semantics } from the actual served rows;
 *     null_semantics names the '4.0' contract boundary when '4.0' rows are
 *     present, the legacy (pre-556/559) reason otherwise.
 *
 * Unit tests (no live DB) — mirrors register_gochara_windows_mr11.test.ts's
 * fetch-mocking pattern for the integration-shaped cases.
 */

import { describe, it, expect, vi } from 'vitest'
import {
  computeGocharaActivation,
  computeGocharaForecast,
  computeGocharaElectionAvoidance,
} from './register_gochara_windows.js'

const LAMBDA_V3_ARGMAX = 'gochara_lambda_v3_argmax'

const MAIN_ROW_QUERY_SIGNATURE = 'id, chart_id, event_class, temporal_shape'

function fakeJsonResponse(rows: unknown[]): Response {
  return {
    ok: true,
    json: () => Promise.resolve({ rows }),
    text: () => Promise.resolve(JSON.stringify({ rows })),
  } as unknown as Response
}

function mockRowQuery(rows: Record<string, unknown>[]) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) => {
    const { sql } = JSON.parse((init as RequestInit).body as string) as { sql: string }
    if (sql.includes(MAIN_ROW_QUERY_SIGNATURE)) return Promise.resolve(fakeJsonResponse(rows))
    if (sql.includes('kala_gochara_authority')) return Promise.resolve(fakeJsonResponse([]))
    if (sql.includes('gochara_resonance_map') && !sql.includes('rm.event_class')) {
      return Promise.resolve(fakeJsonResponse([]))
    }
    if (sql.includes('brahma_event_ontology')) return Promise.resolve(fakeJsonResponse([{ domain: 'marriage' }]))
    if (sql.includes('build_substep_progress')) {
      return Promise.resolve(fakeJsonResponse([{ substeps_committed: 0, swept_event_classes: [] }]))
    }
    return Promise.resolve(fakeJsonResponse(rows))
  })
}

const PRINCIPAL = { user_uid: 'test', key_id: 'test', role: 'super_admin' as const }
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const BASE_DB_ROW = {
  id: 1,
  chart_id: CHART_ID,
  event_class: 'marriage',
  temporal_shape: 'interval',
  milestone_id: null,
  is_irreversibility_milestone: false,
  signed_intensity: 0.7,
  raw_intensity: 0.7,
  valence: 'neutral',
  is_adverse: false,
  active_sentences: [],
  contributing_systems: [],
  suppression_state: {},
  calibration_state: 'structural_prior',
  source: 'live',
  computed_at: '2026-08-11T00:00:00Z',
  continuity_state: null,
  generation: '3.0',
  era_slice_key: 'g3_1984_1994',
  term_breakdown: null,
  parent_window_id: null,
  resolution: 'month',
  peak_basis: LAMBDA_V3_ARGMAX,
}

type EraSliceFacet = {
  by_key: Record<string, number>
  null_count: number
  null_semantics: string | null
}

describe('facets.era_slice_key — Link 3 condition (c) honest era-slice disclosure', () => {
  it("'3.0' rows with era_slice_key set: by_key counts the real slices, null_count=0, null_semantics=null", async () => {
    const fetchSpy = mockRowQuery([
      { ...BASE_DB_ROW, id: 1, window_start: '1984-02-15', window_end: '1984-03-15', peak_date: '1984-03-01', era_slice_key: 'g3_1984_1994' },
      { ...BASE_DB_ROW, id: 2, window_start: '1984-02-15', window_end: '1984-03-15', peak_date: '1984-03-02', era_slice_key: 'g3_1984_1994' },
      { ...BASE_DB_ROW, id: 3, window_start: '1994-02-15', window_end: '1994-03-15', peak_date: '1994-03-01', era_slice_key: 'g3_1994_2004' },
    ])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      facets: { era_slice_key: EraSliceFacet }
    }

    expect(result.facets.era_slice_key).toEqual({
      by_key: { g3_1984_1994: 2, g3_1994_2004: 1 },
      null_count: 0,
      null_semantics: null,
    })

    fetchSpy.mockRestore()
  })

  it("'4.0' rows (era_slice_key NULL by contract): null_count counts them and null_semantics names the 1091-(g) boundary — never 'no windows that decade'", async () => {
    const fetchSpy = mockRowQuery([
      { ...BASE_DB_ROW, id: 1, generation: '4.0', era_slice_key: null, window_start: '1984-02-15', window_end: '1984-03-15', peak_date: '1984-03-01' },
      { ...BASE_DB_ROW, id: 2, generation: '4.0', era_slice_key: null, window_start: '1984-02-15', window_end: '1984-03-15', peak_date: '1984-03-02' },
    ])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      facets: { era_slice_key: EraSliceFacet }
    }

    expect(result.facets.era_slice_key.by_key).toEqual({})
    expect(result.facets.era_slice_key.null_count).toBe(2)
    expect(result.facets.era_slice_key.null_semantics).toContain("'4.0'")
    expect(result.facets.era_slice_key.null_semantics).toContain('migration 1091')
    expect(result.facets.era_slice_key.null_semantics).toContain('NOT')

    fetchSpy.mockRestore()
  })

  it("legacy null era slices WITHOUT '4.0' rows carry the legacy null_semantics (pre-556/559), not the '4.0' boundary text", async () => {
    const fetchSpy = mockRowQuery([
      { ...BASE_DB_ROW, id: 1, generation: 'v1', era_slice_key: null, window_start: '1984-02-15', window_end: '1984-03-15', peak_date: '1984-03-01' },
    ])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      facets: { era_slice_key: EraSliceFacet }
    }

    expect(result.facets.era_slice_key.null_count).toBe(1)
    expect(result.facets.era_slice_key.null_semantics).toContain('predate')
    expect(result.facets.era_slice_key.null_semantics).not.toContain('1091')

    fetchSpy.mockRestore()
  })

  it('an empty row set reports zeroed facet with null semantics null (no fabricated boundary claim)', async () => {
    const fetchSpy = mockRowQuery([])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      facets: { era_slice_key: EraSliceFacet }
    }

    expect(result.facets.era_slice_key).toEqual({ by_key: {}, null_count: 0, null_semantics: null })

    fetchSpy.mockRestore()
  })

  it('gochara_forecast_get and gochara_election_avoidance_get serve the same facet (one shared detector)', async () => {
    const rows = [
      { ...BASE_DB_ROW, id: 1, generation: '4.0', era_slice_key: null, is_adverse: true, window_start: '1984-02-15', window_end: '1984-03-15', peak_date: '1984-03-01' },
    ]
    const fetchSpy = mockRowQuery(rows)

    const forecast = (await computeGocharaForecast(CHART_ID, { start: '1984-02-15', end: '1984-04-15' }, 'marriage', undefined, 10, PRINCIPAL)) as {
      facets: { era_slice_key: EraSliceFacet }
    }
    const avoidance = (await computeGocharaElectionAvoidance(CHART_ID, { start: '1984-02-15', end: '1984-04-15' }, 'marriage', 10, PRINCIPAL)) as {
      facets: { era_slice_key: EraSliceFacet }
    }

    expect(forecast.facets.era_slice_key.null_count).toBe(1)
    expect(forecast.facets.era_slice_key.null_semantics).toContain('1091')
    expect(avoidance.facets.era_slice_key.null_count).toBe(1)
    expect(avoidance.facets.era_slice_key.null_semantics).toContain('1091')

    fetchSpy.mockRestore()
  })
})

import { describe, it, expect, vi, afterEach } from 'vitest'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function mockFetch(opts: { maxWindowEnd: string; rowWindowEnd: string }) {
  vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) => {
    const { sql } = JSON.parse((init as RequestInit).body as string) as { sql: string }
    // kala_gochara_authority standalone lookup (no kala_gochara_windows in same query):
    // must exclude the MAX(window_end) query whose AUTHORITATIVE_GENERATION_FILTER also
    // contains 'kala_gochara_authority' as a substring — without the exclusion guard that
    // query is intercepted here and returns [] instead of the horizon row (SPEC-EXIT-TEST-MOCK-ROUTING-BUG).
    if (sql.includes('kala_gochara_authority') && !sql.includes('kala_gochara_windows')) {
      return Promise.resolve(fakeJsonResponse([]))
    }
    if (sql.includes('MAX(window_end)')) {
      return Promise.resolve(fakeJsonResponse([{ materialized_through: opts.maxWindowEnd }]))
    }
    if (sql.includes('gochara_resonance_map') && !sql.includes('rm.event_class')) {
      return Promise.resolve(fakeJsonResponse([]))
    }
    if (sql.includes('brahma_event_ontology')) return Promise.resolve(fakeJsonResponse([]))
    if (sql.includes('build_substep_progress')) {
      return Promise.resolve(fakeJsonResponse([{ substeps_committed: 9, swept_event_classes: ['career'] }]))
    }
    // main overlap query — every returned row's window_end sits at the swept horizon
    return Promise.resolve(fakeJsonResponse([{
      id: 1, chart_id: CHART_ID, event_class: 'career', temporal_shape: 'point',
      window_start: '2083-06-01', window_end: opts.rowWindowEnd, peak_date: '2083-06-01',
      milestone_id: null, is_irreversibility_milestone: false, signed_intensity: 0.2,
      raw_intensity: 0.2, valence: 'benefic', calibration_state: 'structural_prior',
      suppression_state: null, contributing_systems: [], active_sentences: [],
      peak_basis: null, generation: 'v1', era_slice_key: null, term_breakdown: null,
      resolution: null, parent_window_id: null,
    }]))
  })
}

afterEach(() => vi.restoreAllMocks())

describe('CL-13 — partial-horizon truncation disclosure', () => {
  it('gochara_forecast_get: FAILS today — flags partial_truncation when the swept horizon ' +
     'falls short of a partially-overlapping requested range', async () => {
    mockFetch({ maxWindowEnd: '2084-01-31', rowWindowEnd: '2084-01-31' })
    const { computeGocharaForecast } = await import('./register_gochara_windows.js')
    const result = await computeGocharaForecast(
      CHART_ID, { start: '2083-06-01', end: '2085-06-01' },
      undefined, undefined, 50, { userId: 'test' } as never
    )
    const envelope = result['provenance_envelope'] as Record<string, unknown>
    expect(envelope['empty_reason']).toBeNull() // rows overlap the front — C2's existing correct case
    const disclosure = envelope['coverage_disclosure'] as Record<string, unknown>
    expect(disclosure).toBeDefined()
    expect(disclosure['materialized_through']).toBe('2084-01-31')
    expect(disclosure['partial_truncation']).toBe(true)
    expect(disclosure['truncation_note']).toMatch(/2084-01-31/)
  })

  it('gochara_election_avoidance_get: same shape, same sibling fix', async () => {
    mockFetch({ maxWindowEnd: '2084-01-31', rowWindowEnd: '2084-01-31' })
    const { computeGocharaElectionAvoidance } = await import('./register_gochara_windows.js')
    const result = await computeGocharaElectionAvoidance(
      CHART_ID, { start: '2083-06-01', end: '2085-06-01' },
      undefined, 50, { userId: 'test' } as never
    )
    const envelope = result['provenance_envelope'] as Record<string, unknown>
    const disclosure = envelope['coverage_disclosure'] as Record<string, unknown>
    expect(disclosure['partial_truncation']).toBe(true)
  })

  it('negative control: partial_truncation is false when the horizon covers the full request', async () => {
    mockFetch({ maxWindowEnd: '2085-06-01', rowWindowEnd: '2085-06-01' })
    const { computeGocharaForecast } = await import('./register_gochara_windows.js')
    const result = await computeGocharaForecast(
      CHART_ID, { start: '2083-06-01', end: '2085-06-01' },
      undefined, undefined, 50, { userId: 'test' } as never
    )
    const disclosure = (result['provenance_envelope'] as Record<string, unknown>)['coverage_disclosure'] as Record<string, unknown>
    expect(disclosure['partial_truncation']).toBe(false)
    expect(disclosure['truncation_note']).toBeNull()
  })
})

function fakeJsonResponse(rows: Record<string, unknown>[]) {
  return new Response(JSON.stringify({ rows }), { status: 200 })
}

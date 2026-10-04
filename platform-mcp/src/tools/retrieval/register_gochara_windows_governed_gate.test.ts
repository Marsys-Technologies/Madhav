/**
 * register_gochara_windows_governed_gate.test.ts — the windows reader's shared coverage path applies the SAME governed-generation gate as the
 * contact-ledger reader (Codex rounds 3 and 4 on PR 3110, steward follow-up (c)).
 *
 * Until now this path trusted any manifest the authority row named and was protected only by migration 1236 (the authority table refuses a
 * governed generation). It must refuse an unsealed, unpublished, superseded or test-slice governed generation BEFORE any authority flip:
 * coverage is withheld as 'unpublished' with the gate's reason, and legacy generations ('3.0', '4.x') are unchanged and issue no seal query.
 */
import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest'
import { computeGocharaActivation, computeGocharaCoverage } from './register_gochara_windows.js'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'test', key_id: 'test', role: 'super_admin' as const }

function ok(rows: unknown[]): Response {
  return { ok: true, json: () => Promise.resolve({ rows }), text: () => Promise.resolve(JSON.stringify({ rows })) } as unknown as Response
}
function failed(): Response {
  return { ok: false, status: 400, json: () => Promise.resolve({}), text: () => Promise.resolve('Rejected by whitelist') } as unknown as Response
}

const SLICE_VECTOR = { stored_scope: 'test_slice', test_slice: { schema: 'gochara_v5_test_slice/1', run: 'one_class_full', classes: ['marriage'] } }

function manifest(generation: string, status: string, vector: Record<string, unknown>) {
  return { manifest_id: `manifest-${generation}`, chart_id: CHART, generation, writer_asset_id: 'ka_gochara', convention_id: 'sha256:c',
           input_generation_vector: vector, ephemeris_backend: {}, horizon: '[2026-01-01,2027-01-01)',
           row_counts: { contacts: 1, coverage: 2, windows: 1 }, content_digest: 'sha256:d', status }
}

const COVERAGE_ROWS = [{
  partition_kind: 'event_class', partition_key: 'marriage', requested_horizon: '[2026-01-01,2027-01-01)',
  completed_horizon: '[2026-01-01,2027-01-01)', resolution: 'day', relations_searched: ['conjunction'], targets_requested: 3,
  targets_resolved: 3, targets_unresolved: 0, target_resolution_state_counts: {}, unavailable_inputs: [], unsearched_reason: null,
}]

function mockFetch(fetchSpy: Mock, o: { generation: string; status: string; vector?: Record<string, unknown>; seal?: 'sealed' | 'unsealed' | 'fails' }) {
  fetchSpy.mockImplementation((_url: string, init: RequestInit) => {
    const { sql } = JSON.parse(init.body as string) as { sql: string }
    if (sql.includes('FROM ka_gochara_generation_seal')) return Promise.resolve(o.seal === 'fails' ? failed() : ok([{ sealed: o.seal === 'sealed' }]))
    if (sql.includes('FROM kala_gochara_authority')) return Promise.resolve(ok([{ authoritative_generation: o.generation }]))
    if (sql.includes('FROM kala_gochara_publication')) return Promise.resolve(ok([manifest(o.generation, o.status, o.vector ?? {})]))
    if (sql.includes('FROM kala_gochara_coverage')) return Promise.resolve(ok(COVERAGE_ROWS))
    if (sql.includes('gochara_resonance_map')) return Promise.resolve(ok([{ event_class: 'marriage', domain: 'marriage' }]))
    if (sql.includes('brahma_event_ontology')) return Promise.resolve(ok([{ domain: 'marriage' }]))
    if (sql.includes('FROM build_substep_progress')) return Promise.resolve(ok([{ substeps_committed: 7, swept_event_classes: ['marriage'] }]))
    return Promise.resolve(ok([]))
  })
}

function sealQueries(fetchSpy: Mock): number {
  return fetchSpy.mock.calls.filter((c) => (JSON.parse((c[1] as RequestInit).body as string) as { sql: string }).sql.includes('ka_gochara_generation_seal')).length
}

describe('windows reader coverage — the governed-generation gate (follow-up c)', () => {
  let fetchSpy: Mock
  beforeEach(() => {
    fetchSpy = vi.fn()
    vi.spyOn(globalThis, 'fetch').mockImplementation(fetchSpy)
  })
  afterEach(() => vi.restoreAllMocks())

  it('a governed generation that is PUBLISHED and SEALED is served from its manifest rows', async () => {
    mockFetch(fetchSpy, { generation: '5.0', status: 'published', seal: 'sealed' })
    const { coverage } = await computeGocharaCoverage(CHART, PRINCIPAL)
    expect(coverage.status).toBeUndefined()
    expect(coverage.coverage_manifest).toBeTruthy()
    expect(coverage.event_classes_covered).toEqual(['marriage'])
  })

  it.each([
    ['a candidate (interrupted rebuild or under construction)', 'candidate', 'unsealed', /manifest candidate, not sealed/],
    ['published but NOT sealed', 'published', 'unsealed', /manifest published, not sealed/],
    ['a superseded generation that WAS sealed', 'superseded', 'sealed', /manifest superseded, sealed/],
    ['a rolled-back generation that WAS sealed', 'rolled_back', 'sealed', /manifest rolled_back, sealed/],
  ])('%s is withheld as unpublished with the gate\'s reason, and the coverage manifest is not served', async (_label, status, seal, reason) => {
    mockFetch(fetchSpy, { generation: '5.0', status, seal: seal as 'sealed' | 'unsealed' })
    const { coverage } = await computeGocharaCoverage(CHART, PRINCIPAL)
    expect(coverage.status).toBe('unpublished')
    expect(coverage.withheld_reason).toMatch(reason)
    expect(coverage.note).toMatch(/authority row names generation 5\.0/)
    expect(coverage.coverage_manifest).toBeUndefined()
    expect(coverage.event_classes_covered).toEqual([])
  })

  it('a TEST SLICE manifest is withheld whatever its status and seal', async () => {
    mockFetch(fetchSpy, { generation: '5.0', status: 'published', vector: SLICE_VECTOR, seal: 'sealed' })
    const { coverage } = await computeGocharaCoverage(CHART, PRINCIPAL)
    expect(coverage.status).toBe('unpublished')
    expect(coverage.withheld_reason).toMatch(/TEST SLICE/)
    expect(sealQueries(fetchSpy)).toBe(0)                                 // refused before any seal lookup
  })

  it('a FAILED seal lookup never serves', async () => {
    mockFetch(fetchSpy, { generation: '5.0', status: 'published', seal: 'fails' })
    const { coverage } = await computeGocharaCoverage(CHART, PRINCIPAL)
    expect(coverage.status).toBe('unpublished')
    expect(coverage.withheld_reason).toMatch(/seal lookup failed/)
  })

  it('the citation of a withheld generation names the gate\'s reason, not an absent authority row', async () => {
    mockFetch(fetchSpy, { generation: '5.0', status: 'candidate', seal: 'unsealed' })
    const result = await computeGocharaActivation(CHART, '2026-06-01', PRINCIPAL) as { provenance_envelope: { source_citation: string } }
    expect(result.provenance_envelope.source_citation).toMatch(/the authority names a generation that is not served/)
    expect(result.provenance_envelope.source_citation).not.toMatch(/no kala_gochara_authority row for this chart/)
  })

  it('legacy generations are unchanged: 4.0 is served from its manifest and no seal query is issued', async () => {
    mockFetch(fetchSpy, { generation: '4.0', status: 'published' })
    const { coverage } = await computeGocharaCoverage(CHART, PRINCIPAL)
    expect(coverage.status).toBeUndefined()
    expect(coverage.coverage_manifest).toBeTruthy()
    expect(sealQueries(fetchSpy)).toBe(0)
  })
})

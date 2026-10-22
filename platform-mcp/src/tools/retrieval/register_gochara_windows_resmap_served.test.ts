/**
 * register_gochara_windows_resmap_served.test.ts — SR-K9-RESONANCE-MAP branch B (migration 1404): the coverage block of gochara_activation_get / gochara_forecast_get /
 * gochara_election_avoidance_get reads the SERVED generation of gochara_resonance_map, never the base table that also holds a K9 candidate rebuild's rows.
 *
 * Source of the rules: root CLAUDE.md §N.6.3 (a served layer is never silently empty when grounding data exists; an honest gap is reported) and §N.7.6 (an honest null
 * beats an invented reason), and the measurement RESONANCE_MAP_READERS.md (reader R1, both branches of computeGocharaCoverage).
 *
 *   V1  the published branch reads gochara_resonance_map_served
 *   V2  the unpublished branch (no authority row) reads gochara_resonance_map_served
 *   E1  an empty served map says WHY: rows exist only in non-served generations, or none exist at all
 *   E2  a failed reason lookup is an honest absence (no invented reason), and a served map with rows carries no reason
 *
 * The queries are mocked at the fetch boundary (as every sibling suite here does); the view definition itself is tested against a real database in
 * platform/python-sidecar/tests/l3/kala_db/manifest/test_resmap_generation.py.
 */
import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest'
import { computeGocharaCoverage } from './register_gochara_windows.js'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'test', key_id: 'test', role: 'super_admin' as const }

function ok(rows: unknown[]): Response {
  return { ok: true, json: () => Promise.resolve({ rows }), text: () => Promise.resolve(JSON.stringify({ rows })) } as unknown as Response
}
function failed(): Response {
  return { ok: false, status: 400, json: () => Promise.resolve({}), text: () => Promise.resolve('rejected') } as unknown as Response
}

interface World {
  authority: string | null          // kala_gochara_authority.authoritative_generation; null = no authority row (unpublished branch)
  servedClasses: string[]           // what gochara_resonance_map_served holds for the chart
  baseCount: number | 'fails'       // COUNT(*) of the base table across every generation
}

function mockFetch(fetchSpy: Mock, world: World): string[] {
  const seen: string[] = []
  fetchSpy.mockImplementation((_url: string, init: RequestInit) => {
    const { sql } = JSON.parse(init.body as string) as { sql: string }
    seen.push(sql)
    if (sql.includes('FROM kala_gochara_authority')) return Promise.resolve(ok(world.authority == null ? [] : [{ authoritative_generation: world.authority }]))
    if (sql.includes('FROM kala_gochara_publication')) return Promise.resolve(ok([]))
    if (sql.includes('COUNT(*)') && sql.includes('FROM gochara_resonance_map WHERE')) {
      return Promise.resolve(world.baseCount === 'fails' ? failed() : ok([{ n: world.baseCount }]))
    }
    if (sql.includes('gochara_resonance_map_served')) return Promise.resolve(ok(world.servedClasses.map((c) => ({ event_class: c, domain: c }))))
    if (sql.includes('gochara_resonance_map')) return Promise.resolve(ok([{ event_class: 'BASE_TABLE_CLASS', domain: 'base' }]))   // a reader that bypasses the view lands here
    if (sql.includes('brahma_event_ontology')) return Promise.resolve(ok([{ domain: 'marriage' }, { domain: 'career' }]))
    if (sql.includes('FROM build_substep_progress')) return Promise.resolve(ok([{ substeps_committed: 3, swept_event_classes: ['marriage'] }]))
    return Promise.resolve(ok([]))
  })
  return seen
}

describe('computeGocharaCoverage — the resonance map is read through the served view (migration 1404)', () => {
  let fetchSpy: Mock
  beforeEach(() => {
    fetchSpy = vi.fn()
    vi.spyOn(globalThis, 'fetch').mockImplementation(fetchSpy)
  })
  afterEach(() => vi.restoreAllMocks())

  it('V1: the published branch reads gochara_resonance_map_served', async () => {
    const seen = mockFetch(fetchSpy, { authority: '3.0', servedClasses: ['marriage'], baseCount: 9 })
    const { coverage, eventClassDomains } = await computeGocharaCoverage(CHART, PRINCIPAL)
    expect(coverage.status).toBeUndefined()
    expect(coverage.event_classes_targeted_not_swept).toEqual([])
    expect(Object.keys(eventClassDomains)).toEqual(['marriage'])           // the served class, not BASE_TABLE_CLASS
    expect(seen.some((s) => /FROM gochara_resonance_map_served rm/.test(s))).toBe(true)
    expect(seen.some((s) => /FROM gochara_resonance_map rm/.test(s))).toBe(false)
  })

  it('V2: the unpublished branch (no authority row) reads gochara_resonance_map_served', async () => {
    const seen = mockFetch(fetchSpy, { authority: null, servedClasses: ['marriage'], baseCount: 9 })
    const { coverage, eventClassDomains } = await computeGocharaCoverage(CHART, PRINCIPAL)
    expect(coverage.status).toBe('unpublished')
    expect(Object.keys(eventClassDomains)).toEqual(['marriage'])
    expect(seen.some((s) => /FROM gochara_resonance_map_served rm/.test(s))).toBe(true)
    expect(seen.some((s) => /FROM gochara_resonance_map rm/.test(s))).toBe(false)
  })

  it.each([
    ['published', '3.0'],
    ['unpublished', null],
  ])('E1: on the %s branch an empty served map says why — rows exist only in generations that are not served', async (_branch, authority) => {
    mockFetch(fetchSpy, { authority, servedClasses: [], baseCount: 7 })
    const { coverage } = await computeGocharaCoverage(CHART, PRINCIPAL)
    expect(coverage.event_classes_covered).toEqual([])
    expect(coverage.resonance_map_empty_reason).toBe('served_generation_holds_no_rows')
  })

  it('E1: a chart with no resonance rows in any generation says so', async () => {
    mockFetch(fetchSpy, { authority: '3.0', servedClasses: [], baseCount: 0 })
    const { coverage } = await computeGocharaCoverage(CHART, PRINCIPAL)
    expect(coverage.resonance_map_empty_reason).toBe('no_resonance_rows_for_chart')
  })

  it('E2: a reason lookup that fails leaves the reason absent, never invented', async () => {
    mockFetch(fetchSpy, { authority: '3.0', servedClasses: [], baseCount: 'fails' })
    const { coverage } = await computeGocharaCoverage(CHART, PRINCIPAL)
    expect('resonance_map_empty_reason' in coverage).toBe(false)
  })

  it('E2: a served map with rows carries no empty reason and does not even look one up', async () => {
    const seen = mockFetch(fetchSpy, { authority: '3.0', servedClasses: ['marriage'], baseCount: 9 })
    const { coverage } = await computeGocharaCoverage(CHART, PRINCIPAL)
    expect('resonance_map_empty_reason' in coverage).toBe(false)
    expect(seen.some((s) => s.includes('COUNT(*)') && s.includes('FROM gochara_resonance_map WHERE'))).toBe(false)
  })
})

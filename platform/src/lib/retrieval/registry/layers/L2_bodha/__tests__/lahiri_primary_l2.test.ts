/**
 * Lahiri primary PR-2 — L2 handler specifics beyond the table-driven registry test
 * (registry/__tests__/lahiri_primary_handlers.test.ts):
 *   - traverse_chart_graph: the seed-node lookup and the topology summary are filtered to the
 *     primary ayanamsha AND ordered (they used to pick an arbitrary ayanamsha's node, heap order),
 *   - query_mechanisms / query_signals / query_ucd: omitted = Lahiri, "all" opt-out semantics.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery, mockResolveAddress } = vi.hoisted(() => ({ mockQuery: vi.fn(), mockResolveAddress: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('../../../../address_resolver', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../../address_resolver')>()
  return { ...actual, resolveAddress: (...a: unknown[]) => mockResolveAddress(...a) }
})

import { traverseChartGraphCapability } from '../traverse_chart_graph'
import { queryMechanismsCapability } from '../query_mechanisms'
import { querySignalsCapability } from '../query_signals'
import { queryUcdCapability } from '../query_ucd'

const CHART = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const LAHIRI = 'lahiri_chitrapaksha'
const FIVE = ['krishnamurti', 'lahiri_chitrapaksha', 'raman', 'surya_siddhanta_classical', 'true_chitra']
const norm = (s: unknown) => String(s).replace(/\s+/g, ' ')

const signingEnv = { kid: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID, key: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT }
const snapshot = { replacement_in_progress: false, eligible_build_id: 'build-a', cursor_build_changed: false, rows: [], facets: [], total_matching: '0' }
beforeEach(() => {
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = 'inquiry-v1'
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = Buffer.alloc(32, 3).toString('base64url')
  mockQuery.mockReset()
  mockQuery.mockImplementation(async (q: unknown) => (/^\s*WITH eligible_receipt/.test(String(q)) ? { rows: [snapshot] } : { rows: [] }))
  mockResolveAddress.mockReset()
  mockResolveAddress.mockResolvedValue({ entities: [{ kind: 'graha', graha: 'SAT' }], chain: ['Saturn'] })
})

afterEach(() => {
  if (signingEnv.kid === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID; else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = signingEnv.kid
  if (signingEnv.key === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT; else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = signingEnv.key
})

describe('traverse_chart_graph: seed-node lookup and topology summary', () => {
  const seedSql = () => (mockQuery.mock.calls as Array<[string, unknown[]]>).find((c) => /SELECT node_id FROM bodha_cgm_nodes/.test(c[0]))!
  const topoSql = () => (mockQuery.mock.calls as Array<[string, unknown[]]>).find((c) => /bodha_cgm_chart_topology_summary/.test(c[0]))!

  it('default: the seed query carries ayanamsha_id = $n (Lahiri) and an ORDER BY before its LIMIT', async () => {
    await traverseChartGraphCapability.handler({ chart_id: CHART, mode: 'neighbors', about: 'Saturn' }, undefined)
    const [sql, params] = seedSql()
    expect(norm(sql)).toMatch(/ayanamsha_id = \$\d+/)
    expect(params).toContain(LAHIRI)
    expect(norm(sql)).toMatch(/ORDER BY array_position\(ARRAY\['lahiri_chitrapaksha'.*node_subject, node_id LIMIT/)
  })

  it('"all": the seed query is unfiltered but ORDER BY puts Lahiri\'s node first (never heap order)', async () => {
    const res = await traverseChartGraphCapability.handler({ chart_id: CHART, mode: 'neighbors', about: 'Saturn', ayanamsha_id: 'all' }, undefined)
    const [sql, params] = seedSql()
    expect(norm(sql)).not.toMatch(/ayanamsha_id = \$\d+/)
    for (const id of FIVE) expect(params).not.toContain(id)
    expect(norm(sql)).toMatch(/ORDER BY array_position\(ARRAY\['lahiri_chitrapaksha'/)
    // (an empty fixture resolves no node for the address -> an honest error result, not stamped)
    expect(res.is_error).toBe(true)
  })

  it('convergence topology summary: filtered to Lahiri by default and ordered before LIMIT 1', async () => {
    await traverseChartGraphCapability.handler({ chart_id: CHART, mode: 'convergence' }, undefined)
    const [sql, params] = topoSql()
    expect(norm(sql)).toMatch(/ayanamsha_id = \$\d+/)
    expect(params).toContain(LAHIRI)
    expect(norm(sql)).toMatch(/ORDER BY array_position\(ARRAY\['lahiri_chitrapaksha'.*LIMIT 1/)
  })

  it('convergence "all": topology summary ordered Lahiri-first, not filtered', async () => {
    await traverseChartGraphCapability.handler({ chart_id: CHART, mode: 'convergence', ayanamsha_scope: 'all' }, undefined)
    const [sql] = topoSql()
    expect(norm(sql)).not.toMatch(/ayanamsha_id = \$\d+/)
    expect(norm(sql)).toMatch(/ORDER BY array_position\(ARRAY\['lahiri_chitrapaksha'.*LIMIT 1/)
    // marked on the success result
    const res = await traverseChartGraphCapability.handler({ chart_id: CHART, mode: 'convergence', ayanamsha_scope: 'all' }, undefined)
    expect((res.content as Record<string, unknown>)['ayanamsha_scope']).toBe('all')
  })

  it('edges are filtered to the primary ayanamsha when seeds are given (the whole-chart read passes none)', async () => {
    await traverseChartGraphCapability.handler({ chart_id: CHART, mode: 'neighbors', seed_node_ids: ['n1'] }, undefined)
    const edgeCalls = (mockQuery.mock.calls as Array<[string, unknown[]]>).filter((c) => /bodha_cgm_edges/.test(c[0]))
    expect(edgeCalls.length).toBeGreaterThan(0)
    expect(edgeCalls.every((c) => c[1].includes(LAHIRI))).toBe(true)
  })

  it('unknown id -> is_error, no SQL', async () => {
    const res = await traverseChartGraphCapability.handler({ chart_id: CHART, mode: 'neighbors', ayanamsha_id: 'zzz' }, undefined)
    expect(res.is_error).toBe(true)
    expect(JSON.stringify(res.content)).toContain(LAHIRI)
    expect(mockQuery).not.toHaveBeenCalled()
  })
})

describe('query_signals / query_ucd / query_mechanisms scope handling', () => {
  const bound = () => (mockQuery.mock.calls as Array<[string, unknown[]]>).flatMap((c) => c[1] ?? [])

  it.each([
    ['query_signals', querySignalsCapability],
    ['query_ucd', queryUcdCapability],
    ['query_mechanisms', queryMechanismsCapability],
  ] as const)('%s: omitted -> Lahiri, alias normalises, unknown -> is_error', async (_n, cap) => {
    await cap.handler({ chart_id: CHART }, undefined)
    expect(bound()).toContain(LAHIRI)
    mockQuery.mockClear()
    await cap.handler({ chart_id: CHART, ayanamsha_id: 'KP' }, undefined)
    expect(bound()).toContain('krishnamurti')
    mockQuery.mockClear()
    const bad = await cap.handler({ chart_id: CHART, ayanamsha_id: 'nonsense' }, undefined)
    expect(bad.is_error).toBe(true)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('query_signals "all": the signals read is unfiltered and says ayanamsha_scope:"all"', async () => {
    const res = await querySignalsCapability.handler({ chart_id: CHART, ayanamsha_id: 'all' }, undefined)
    const signalsSql = (mockQuery.mock.calls as Array<[string, unknown[]]>).find((c) => /FROM bodha_msr_signals/.test(c[0]) && /LIMIT/.test(c[0]))
    expect(signalsSql).toBeDefined()
    expect(norm(signalsSql![0])).not.toMatch(/ayanamsha_id = \$\d+/)
    expect((res.content as Record<string, unknown>)['ayanamsha_scope']).toBe('all')
  })

  it('query_ucd "all": a single-ayanamsha digest, served at Lahiri and honestly labelled (not claimed pooled)', async () => {
    const res = await queryUcdCapability.handler({ chart_id: CHART, ayanamsha_id: 'all' }, undefined)
    expect(bound()).toContain(LAHIRI)
    const content = res.content as Record<string, unknown>
    expect(content['ayanamsha_scope']).not.toBe('all')
    expect(content['ayanamsha_scope_requested']).toBe('all')
  })

  it('query_mechanisms "all": no ayanamsha filter on the page, scope marker set', async () => {
    const res = await queryMechanismsCapability.handler({ chart_id: CHART, ayanamsha_scope: 'all' }, undefined)
    for (const [sql] of mockQuery.mock.calls as Array<[string]>) expect(norm(sql)).not.toMatch(/d\.ayanamsha_id = \$\d+/)
    expect((res.content as Record<string, unknown>)['ayanamsha_scope']).toBe('all')
  })
})

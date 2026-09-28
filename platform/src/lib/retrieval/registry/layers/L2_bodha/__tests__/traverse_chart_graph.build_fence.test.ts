/**
 * traverse_chart_graph served-generation build fence (Packet A of the fence-and-successor-envelope
 * follow-up). graha_portrait composes this tool's `neighbors` mode, and bodha_cgm_* rows are
 * build-scoped, so the CGM section can be served only from the chart's served build set.
 *
 * `neighbors` (and `convergence`, its seedless fallback) honor the fence on every generation-scoped
 * read. The modes that do NOT honor it (`paths`, `contradictions`, `sub_graphs`) must refuse a
 * supplied fence by name instead of accepting and silently ignoring it.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery, mockResolveAddress } = vi.hoisted(() => ({ mockQuery: vi.fn(), mockResolveAddress: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/retrieval/address_resolver', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/retrieval/address_resolver')>()),
  resolveAddress: mockResolveAddress,
}))

import { traverseChartGraphCapability } from '../traverse_chart_graph'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SERVED = '11111111-1111-4111-8111-111111111111'
const FENCE = /build_id = ANY\(\$(\d+)::uuid\[\]\)/

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockImplementation(async (sql: string) => {
    const text = String(sql)
    if (text.includes('WITH RECURSIVE bfs')) return { rows: [{ node_id: 'node-1' }] }
    if (text.includes('FROM bodha_cgm_nodes') && text.includes('hub_flag')) return { rows: [{ node_id: 'hub-1' }] }
    return { rows: [] }
  })
})

function cgmReads(): Array<{ sql: string; params: unknown[] }> {
  return mockQuery.mock.calls
    .map(([sql, params]) => ({ sql: String(sql), params: (params ?? []) as unknown[] }))
    .filter(({ sql }) => /bodha_cgm_/.test(sql))
}

/** Every `build_id = ANY($n)` occurrence in one statement must bind the served set. */
function fencePlaceholders(sql: string): number[] {
  return [...sql.matchAll(new RegExp(FENCE.source, 'g'))].map((match) => Number(match[1]))
}

describe('traverse_chart_graph build fence', () => {
  it('declares the build_id input so planned dispatch and composing callers carry the fence', () => {
    expect(traverseChartGraphCapability.input_schema).toHaveProperty('build_id')
  })

  it('neighbors: fences the base nodes, the BFS edge expansion and the hydrated edges', async () => {
    const result = await traverseChartGraphCapability.handler(
      { chart_id: CHART_ID, mode: 'neighbors', seed_node_ids: ['node-1'], build_id: [SERVED] }, undefined,
    )
    expect(result.is_error).toBe(false)
    const reads = cgmReads()
    const bfs = reads.find(({ sql }) => sql.includes('WITH RECURSIVE bfs'))!
    // Base-node seeds AND the recursive edge join are both fenced (two placeholders in one statement).
    expect(fencePlaceholders(bfs.sql).length).toBeGreaterThanOrEqual(2)
    for (const index of fencePlaceholders(bfs.sql)) expect(bfs.params[index - 1]).toEqual([SERVED])
    const edgeRead = reads.find(({ sql }) => sql.includes('FROM bodha_cgm_edges') && !sql.includes('WITH RECURSIVE'))!
    expect(edgeRead, 'edges between visited nodes must be read').toBeDefined()
    for (const index of fencePlaceholders(edgeRead.sql)) expect(edgeRead.params[index - 1]).toEqual([SERVED])
    expect(fencePlaceholders(edgeRead.sql).length).toBeGreaterThan(0)
  })

  it('neighbors without seeds falls back to convergence and fences it too, incl. the topology summary', async () => {
    const result = await traverseChartGraphCapability.handler(
      { chart_id: CHART_ID, mode: 'neighbors', build_id: [SERVED] }, undefined,
    )
    expect(result.is_error).toBe(false)
    const reads = cgmReads()
    expect(reads.some(({ sql }) => sql.includes('bodha_cgm_chart_topology_summary'))).toBe(true)
    for (const { sql, params } of reads) {
      const placeholders = fencePlaceholders(sql)
      expect(placeholders.length, sql).toBeGreaterThan(0)
      for (const index of placeholders) expect(params[index - 1], sql).toEqual([SERVED])
    }
  })

  it('convergence: every read carries the fence', async () => {
    await traverseChartGraphCapability.handler({ chart_id: CHART_ID, mode: 'convergence', build_id: SERVED }, undefined)
    const reads = cgmReads()
    expect(reads.length).toBeGreaterThan(0)
    for (const { sql, params } of reads) {
      const placeholders = fencePlaceholders(sql)
      expect(placeholders.length, sql).toBeGreaterThan(0)
      for (const index of placeholders) expect(params[index - 1], sql).toEqual([SERVED])
    }
  })

  it.each(['neighbors', 'paths', 'convergence', 'contradictions', 'sub_graphs'])(
    '%s: refuses an explicit-empty fence without querying', async (mode) => {
      const result = await traverseChartGraphCapability.handler(
        { chart_id: CHART_ID, mode, seed_node_ids: ['a', 'b'], build_id: [] }, undefined,
      )
      expect(result.is_error).toBe(true)
      expect((result.content as Record<string, unknown>)['code']).toBe('explicit_empty_build_fence')
      expect(mockQuery).not.toHaveBeenCalled()
    })

  it.each(['paths', 'contradictions', 'sub_graphs'])(
    '%s: refuses a supplied fence by name rather than accepting and ignoring it', async (mode) => {
      const result = await traverseChartGraphCapability.handler(
        { chart_id: CHART_ID, mode, seed_node_ids: ['a', 'b'], build_id: [SERVED] }, undefined,
      )
      expect(result.is_error).toBe(true)
      expect(result.content).toMatchObject({ code: 'build_fence_unsupported_for_mode', mode })
      expect(mockQuery).not.toHaveBeenCalled()
    })

  it('leaves a standalone call that omits build_id unfenced, exactly as before', async () => {
    await traverseChartGraphCapability.handler(
      { chart_id: CHART_ID, mode: 'neighbors', seed_node_ids: ['node-1'] }, undefined,
    )
    for (const { sql } of cgmReads()) expect(sql).not.toContain('build_id')
  })
})

describe('traverse_chart_graph about-address resolution is fenced (the path graha_portrait uses)', () => {
  it('neighbors + about: the resolver receives the served build set and every downstream CGM read carries it', async () => {
    mockResolveAddress.mockResolvedValue({ entities: [{ kind: 'graha', graha: 'SAT' }], resolution_chain: [] })
    await traverseChartGraphCapability.handler(
      { chart_id: CHART_ID, mode: 'neighbors', about: 'graha:SAT', build_id: [SERVED] }, undefined,
    )
    expect(mockResolveAddress).toHaveBeenCalledWith(CHART_ID, 'graha:SAT', expect.objectContaining({ build_id: [SERVED] }))
    const reads = cgmReads()
    expect(reads.length).toBeGreaterThan(0)
    for (const { sql, params } of reads) {
      const placeholders = fencePlaceholders(sql)
      expect(placeholders.length, sql).toBeGreaterThan(0)
      for (const index of placeholders) expect(params[index - 1], sql).toEqual([SERVED])
    }
  })
})

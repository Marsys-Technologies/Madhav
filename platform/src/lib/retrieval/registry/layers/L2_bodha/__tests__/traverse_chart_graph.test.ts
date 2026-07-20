/**
 * D4 wave — traverse_chart_graph: unit tests
 * ============================================
 * Tests the capability descriptor (shape + gate compliance) without hitting
 * the database. DB-level integration is gated behind [verify-against: prod].
 *
 * Scope:
 *   1. Descriptor shape — all required D1 contract fields present
 *   2. Chart-agnostic gate — 0 violations (per_chart, chart_id required, no native bleed)
 *   3. Schema-agnostic schema adoption note — old bodha_graph reference absent
 *   4. Handler error-if-missing — chart_id absent → is_error: true
 *   5. Handler empty-on-missing — mocked DB returning 0 rows → empty arrays, not error
 *   6. Two-chart isolation — two distinct chart UUIDs produce structurally disjoint results
 *
 * [verify-against: prod] — rows in bodha_cgm_nodes/edges/contradictions require L2 build.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { traverseChartGraphCapability } from '../traverse_chart_graph'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

// ── Test chart UUIDs (distinct, never the native) ────────────────────────────

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const CHART_B = '22222222-bbbb-4bbb-bbbb-bbbbbbbbbbbb'
// Must never appear:
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

// ── DB mock ──────────────────────────────────────────────────────────────────

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('traverse_chart_graph — D4 capability descriptor', () => {

  it('has the correct URI', () => {
    expect(traverseChartGraphCapability.uri).toBe('marsys://tool/L2/traverse_chart_graph')
  })

  it('is a per_chart scope tool', () => {
    expect(traverseChartGraphCapability.scope).toBe('per_chart')
    expect(traverseChartGraphCapability.type).toBe('tool')
    expect(traverseChartGraphCapability.layer).toBe('L2')
  })

  it('has tool_role = graph (D4 brief contract)', () => {
    expect(traverseChartGraphCapability.tool_role).toBe('graph')
  })

  it('has archetype = graph_traversal', () => {
    expect(traverseChartGraphCapability.archetype).toBe('graph_traversal')
  })

  it('emits_references = true (F1 principle)', () => {
    expect(traverseChartGraphCapability.emits_references).toBe(true)
  })

  it('grounds_to l1_fact_ids (F3 principle)', () => {
    expect(traverseChartGraphCapability.grounds_to?.l1_fact_ids).toBe(true)
  })

  it('chart_id is in required_inputs', () => {
    expect(traverseChartGraphCapability.required_inputs).toContain('chart_id')
  })

  it('chart_id input_schema has no default value (Rule-4)', () => {
    const chartIdSchema = traverseChartGraphCapability.input_schema?.['chart_id']
    expect(chartIdSchema).toBeDefined()
    expect((chartIdSchema as unknown as Record<string, unknown>)?.['default']).toBeUndefined()
  })

  it('description does not contain native chart UUID (Rule-2)', () => {
    expect(traverseChartGraphCapability.description).not.toContain(NATIVE_CHART_ID)
  })

  it('description does not contain native name or birthdate (Rule-3)', () => {
    expect(traverseChartGraphCapability.description).not.toContain('Abhisek Mohanty')
    expect(traverseChartGraphCapability.description).not.toContain('1984-02-05')
    expect(traverseChartGraphCapability.description).not.toContain('Bhubaneswar')
  })

  it('chart_id field description does not contain native UUID (Rule-5)', () => {
    const chartIdDesc = traverseChartGraphCapability.input_schema?.['chart_id']?.description ?? ''
    expect(chartIdDesc).not.toContain(NATIVE_CHART_ID)
  })

  it('lel_capable = false (no LEL signals in CGM graph layer)', () => {
    expect(traverseChartGraphCapability.lel_capable).toBe(false)
  })

  it('supports the 4 required traversal modes in input_schema', () => {
    const modeSchema = traverseChartGraphCapability.input_schema?.['mode']
    expect(modeSchema).toBeDefined()
    expect((modeSchema as unknown as Record<string, unknown>)?.['enum']).toEqual(
      expect.arrayContaining(['neighbors', 'paths', 'convergence', 'contradictions'])
    )
  })

  it('supports the W2 sub_graphs mode (bodha_cgm_sub_graphs dark-set wiring)', () => {
    const modeSchema = traverseChartGraphCapability.input_schema?.['mode']
    expect((modeSchema as unknown as Record<string, unknown>)?.['enum']).toEqual(
      expect.arrayContaining(['sub_graphs'])
    )
    expect(traverseChartGraphCapability.input_schema?.['subgraph_type']).toBeDefined()
  })

  it('does NOT reference the old bodha_graph table (pre-mig 325 schema)', () => {
    const descStr = traverseChartGraphCapability.description
    const nameStr = traverseChartGraphCapability.name
    // Old table was bodha_graph; new tables are bodha_cgm_nodes/edges
    expect(descStr).not.toContain('bodha_graph')
    expect(nameStr).not.toContain('bodha_graph')
  })

})

describe('traverse_chart_graph — chart-agnostic gate', () => {

  it('passes the gate with 0 violations', () => {
    const violations = checkCapability(traverseChartGraphCapability as CapabilityDescriptor)
    if (violations.length > 0) {
      for (const v of violations) {
        console.error(`VIOLATION: ${v.rule} — ${v.detail}`)
      }
    }
    expect(violations).toHaveLength(0)
  })

})

describe('traverse_chart_graph — handler contract', () => {

  beforeEach(() => {
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('error-if-missing: returns is_error=true when chart_id absent', async () => {
    const result = await traverseChartGraphCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
    expect((result.content as Record<string, unknown>)?.['error']).toMatch(/chart_id is required/)
  })

  it('empty-on-missing: no rows in DB → empty arrays, not error', async () => {
    // Mock all queries returning empty rows
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)

    const result = await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'neighbors', seed_node_ids: ['node-uuid-1'] },
      undefined
    )

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['chart_id']).toBe(CHART_A)
    expect(content['nodes']).toEqual([])
    expect(content['edges']).toEqual([])
  })

  it('contradictions mode: empty DB → empty contradictions array', async () => {
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)

    const result = await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'contradictions' },
      undefined
    )

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['contradictions']).toEqual([])
    expect(content['contradiction_count']).toBe(0)
  })

  it('convergence mode: empty DB → empty hub_nodes array', async () => {
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)

    const result = await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'convergence' },
      undefined
    )

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['hub_nodes']).toEqual([])
    expect(content['hub_count']).toBe(0)
  })

  it('sub_graphs mode: empty DB → empty sub_graphs array, not error', async () => {
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)

    const result = await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'sub_graphs' },
      undefined
    )

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['chart_id']).toBe(CHART_A)
    expect(content['sub_graphs']).toEqual([])
    expect(content['sub_graph_count']).toBe(0)
    expect(content['member_nodes']).toEqual([])
  })

  it('sub_graphs mode: populated DB → resolves member_nodes from node_ids_array', async () => {
    vi.mocked(mockQuery).mockReset()
    // First call: the bodha_cgm_sub_graphs SELECT
    vi.mocked(mockQuery).mockResolvedValueOnce({
      rows: [
        {
          subgraph_id: 'sg-1',
          ayanamsha_id: 'LAHIRI',
          subgraph_type: 'raja_yoga_cluster',
          subgraph_label: 'test cluster',
          node_ids_array: ['node-1', 'node-2'],
          edge_ids_array: ['edge-1'],
          subgraph_density: 0.8,
        },
      ],
    } as never)
    // Second call: the bodha_cgm_nodes member resolution
    vi.mocked(mockQuery).mockResolvedValueOnce({
      rows: [
        { node_id: 'node-1', node_type: 'graha', node_subject: 'Jupiter' },
        { node_id: 'node-2', node_type: 'bhava', node_subject: '10' },
      ],
    } as never)

    const result = await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'sub_graphs', subgraph_type: 'raja_yoga_cluster' },
      undefined
    )

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['sub_graph_count']).toBe(1)
    expect(content['member_nodes']).toHaveLength(2)
    const prov = content['provenance'] as Record<string, unknown>
    expect(prov['tables']).toEqual(['bodha_cgm_sub_graphs', 'bodha_cgm_nodes'])

    // subgraph_type filter must reach the SQL params
    const firstCallParams = vi.mocked(mockQuery).mock.calls[0]?.[1] as unknown[]
    expect(firstCallParams).toContain('raja_yoga_cluster')
  })

  it('sub_graphs mode: native chart UUID never appears in any query param', async () => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)

    await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'sub_graphs' },
      undefined
    )

    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })

  it('paths mode: requires 2 seed_node_ids', async () => {
    const result = await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'paths', seed_node_ids: ['only-one'] },
      undefined
    )
    expect(result.is_error).toBe(true)
    expect((result.content as Record<string, unknown>)?.['error']).toMatch(/2 elements/)
  })

  it('two-chart isolation: Chart A vs Chart B produce separate calls with correct chart_id', async () => {
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)

    await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'convergence' },
      undefined
    )
    await traverseChartGraphCapability.handler(
      { chart_id: CHART_B, mode: 'convergence' },
      undefined
    )

    const calls = vi.mocked(mockQuery).mock.calls
    // Every query call must have chart_id as first param
    for (const [_sql, params] of calls) {
      const p = params as unknown[]
      // The first param is always chart_id — must be A or B, never native
      expect([CHART_A, CHART_B]).toContain(p[0])
      expect(p[0]).not.toBe(NATIVE_CHART_ID)
    }
  })

  it('native chart UUID never appears in any query param (no native bleed)', async () => {
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)

    await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'neighbors', seed_node_ids: ['abc'] },
      undefined
    )

    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })

  it('provenance envelope contains schema_version mig_325', async () => {
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)

    const result = await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'convergence' },
      undefined
    )

    const content = result.content as Record<string, unknown>
    const prov = content['provenance'] as Record<string, unknown>
    expect(prov?.['schema_version']).toBe('mig_325')
  })

})

describe('traverse_chart_graph — R5 W2 extension (about seeds, direction, min_strength, valence)', () => {

  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('input_schema exposes about_from/about_to/about/direction/min_strength', () => {
    const schema = traverseChartGraphCapability.input_schema as Record<string, unknown>
    expect(schema['about_from']).toBeDefined()
    expect(schema['about_to']).toBeDefined()
    expect(schema['about']).toBeDefined()
    expect(schema['direction']).toBeDefined()
    expect(schema['min_strength']).toBeDefined()
  })

  it('valence_filter enum now includes the real live-DB vocabulary (harmonious/antagonistic/neutral)', () => {
    const schema = traverseChartGraphCapability.input_schema as Record<string, { enum?: string[] }>
    const enumVals = schema['valence_filter']?.enum ?? []
    expect(enumVals).toEqual(expect.arrayContaining(['harmonious', 'antagonistic', 'neutral']))
  })

  it('normalizes a legacy D4-era valence_filter ("benefic") to "harmonious" in the edge query params', async () => {
    await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'neighbors', seed_node_ids: ['node-1'], valence_filter: 'benefic' },
      undefined
    )
    const calls = vi.mocked(mockQuery).mock.calls
    const sawHarmonious = calls.some(([, params]) => (params as unknown[])?.includes('harmonious'))
    const sawLegacyBenefic = calls.some(([, params]) => (params as unknown[])?.includes('benefic'))
    expect(sawHarmonious).toBe(true)
    expect(sawLegacyBenefic).toBe(false)
  })

  it('paths mode: about_from + about_to trigger address resolution (resolveAddress path) rather than raw seed_node_ids', async () => {
    // With the mocked DB returning zero rows, address resolution will fail to find a frame
    // sign fact — the capability must surface this as a clean is_error, not throw uncaught.
    const result = await traverseChartGraphCapability.handler(
      {
        chart_id: CHART_A,
        mode: 'paths',
        about_from: 'lord_of(bhava 10)',
        about_to: { type: 'graha', graha: 'Moon' },
      },
      undefined
    )
    expect(result.is_error).toBe(true)
    expect((result.content as Record<string, unknown>)['chart_id']).toBe(CHART_A)
  })

  it('paths mode error path never leaks the native chart UUID', async () => {
    const result = await traverseChartGraphCapability.handler(
      {
        chart_id: CHART_A,
        mode: 'paths',
        about_from: 'lord_of(bhava 10)',
        about_to: { type: 'graha', graha: 'Moon' },
      },
      undefined
    )
    expect(String((result.content as Record<string, unknown>)['error'])).not.toContain(NATIVE_CHART_ID)
  })

  it('paths mode: requires either about_from+about_to or 2 seed_node_ids', async () => {
    const result = await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'paths', seed_node_ids: ['only-one'] },
      undefined
    )
    expect(result.is_error).toBe(true)
    expect((result.content as Record<string, unknown>)?.['error']).toMatch(/about_from \+ about_to|2 elements/)
  })

  it('direction defaults to "both" and echoes back on the response envelope', async () => {
    const result = await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'neighbors', seed_node_ids: ['node-1'] },
      undefined
    )
    const content = result.content as Record<string, unknown>
    expect(content['direction']).toBe('both')
  })

  it('direction="directed" is threaded through to the response envelope', async () => {
    const result = await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'neighbors', seed_node_ids: ['node-1'], direction: 'directed' },
      undefined
    )
    const content = result.content as Record<string, unknown>
    expect(content['direction']).toBe('directed')
  })

  it('min_strength is applied to the edge query params when provided', async () => {
    await traverseChartGraphCapability.handler(
      { chart_id: CHART_A, mode: 'neighbors', seed_node_ids: ['node-1'], min_strength: 0.6 },
      undefined
    )
    const calls = vi.mocked(mockQuery).mock.calls
    const sawFloor = calls.some(([, params]) => (params as unknown[])?.includes(0.6))
    expect(sawFloor).toBe(true)
  })

})

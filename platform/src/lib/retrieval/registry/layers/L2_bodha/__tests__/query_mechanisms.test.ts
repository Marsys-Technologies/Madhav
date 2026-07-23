/**
 * query_mechanisms — unit tests
 * ===============================
 * SARVA-SIDDHI W-4 / CR-24. Covers descriptor shape (chart-agnostic gate, D1 contract
 * fields, density_contract), and handler contract (chart_id required, chain/circuit-first
 * ordering, chain_circuit_only filter, facet rollups over the full match set, honest
 * empty_reason, native-UUID leak guard).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryMechanismsCapability } from '../query_mechanisms'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('query_mechanisms — descriptor shape', () => {
  it('has the correct URI and is per_chart scope', () => {
    expect(queryMechanismsCapability.uri).toBe('marsys://tool/L2/query_mechanisms')
    expect(queryMechanismsCapability.scope).toBe('per_chart')
  })

  it('chart_id is required with no default (Rule-4)', () => {
    expect(queryMechanismsCapability.required_inputs).toContain('chart_id')
    const schema = queryMechanismsCapability.input_schema?.['chart_id'] as unknown as Record<string, unknown>
    expect(schema?.['default']).toBeUndefined()
  })

  it('exposes the chain_circuit_only filter', () => {
    expect(queryMechanismsCapability.input_schema?.['chain_circuit_only']).toBeDefined()
  })

  it('declares a density_contract with pagination + empty_reason + facets', () => {
    const dc = queryMechanismsCapability.density_contract
    expect(dc).toBeDefined()
    expect(dc?.paginated).toBe(true)
    expect(dc?.empty_reason).toBe(true)
    expect(dc?.facets).toContain('mechanism_class')
    expect(dc?.facets).toContain('chain_circuit')
  })

  it('has all required D1 contract fields', () => {
    expect(queryMechanismsCapability.archetype).toBeDefined()
    expect(queryMechanismsCapability.traversal_level).toBeDefined()
    expect(queryMechanismsCapability.tool_role).toBeDefined()
    expect(queryMechanismsCapability.emits_references).toBeDefined()
    expect(queryMechanismsCapability.lel_capable).toBeDefined()
  })

  it('description does not contain the native chart UUID', () => {
    expect(queryMechanismsCapability.description).not.toContain(NATIVE_CHART_ID)
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryMechanismsCapability as CapabilityDescriptor)
    expect(violations, JSON.stringify(violations)).toHaveLength(0)
  })
})

describe('query_mechanisms — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryMechanismsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('queries bodha_mechanisms and orders the chain/circuit family first', async () => {
    await queryMechanismsCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    const rowsSql = String(calls[0]?.[0])
    expect(rowsSql).toContain('FROM bodha_mechanisms')
    // chain/circuit priority is the first ORDER BY term (DESC on the ANY(...) boolean)
    expect(rowsSql).toMatch(/ORDER BY \(mechanism_class = ANY\([^)]*\)\) DESC/)
  })

  it('chain_circuit_only=true adds a class filter to the WHERE clause', async () => {
    await queryMechanismsCapability.handler({ chart_id: CHART_A, chain_circuit_only: true }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    const rowsSql = String(calls[0]?.[0])
    // two ANY(...) usages when filtered: one in WHERE, one in the priority sort/select
    expect((rowsSql.match(/= ANY\(/g) ?? []).length).toBeGreaterThanOrEqual(2)
    // the convergent_dispositor_chain class must be among the bound params
    const flat = calls.flatMap((c) => (c[1] as unknown[]) ?? [])
    expect(JSON.stringify(flat)).toContain('convergent_dispositor_chain')
  })

  it('empty result returns is_error:false with an honest empty_reason and zeroed facets', async () => {
    const result = await queryMechanismsCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(content['total_matching']).toBe(0)
    expect(content['empty_reason']).toBeTruthy()
    expect(content['chain_circuit_count']).toBe(0)
  })

  it('builds facet rollups over the full match set (not just the page)', async () => {
    vi.mocked(mockQuery)
      .mockResolvedValueOnce({ rows: [{ mechanism_class: 'convergent_dispositor_chain', mechanism_name: 'x' }] } as never) // page
      .mockResolvedValueOnce({ rows: [
        { mechanism_class: 'convergent_dispositor_chain', valence: 'mixed', is_chain_circuit: true, n: '1' },
        { mechanism_class: 'mutual_aspect_triangle', valence: 'mixed', is_chain_circuit: false, n: '60' },
      ] } as never) // facets
      .mockResolvedValueOnce({ rows: [{ total: '61' }] } as never) // count
    const result = await queryMechanismsCapability.handler({ chart_id: CHART_A, limit: 1 }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['total_matching']).toBe(61)
    expect(content['chain_circuit_count']).toBe(1)
    const facets = content['facets'] as Record<string, Record<string, number>>
    expect(facets['by_mechanism_class']['mutual_aspect_triangle']).toBe(60)
    expect(facets['by_mechanism_class']['convergent_dispositor_chain']).toBe(1)
    expect(content['more_available']).toBe(true)
  })

  it('native chart UUID never appears in any query param', async () => {
    await queryMechanismsCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })
})

/**
 * query_mechanisms — unit tests
 * ===============================
 * SARVA-SIDDHI W-4 / CR-24. Covers descriptor shape (chart-agnostic gate, D1 contract
 * fields, density_contract), and handler contract (chart_id required, chain/circuit-first
 * ordering, chain_circuit_only filter, facet rollups over the full match set, honest
 * empty_reason, native-UUID leak guard).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { queryMechanismsCapability } from '../query_mechanisms'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'
import { deriveInquiryPaginationReceipt } from '@/lib/vidhi/inquiry/pagination'
import { getCatalog } from '../../../catalog'
import { compileCapabilityKnowledge } from '../../../knowledge/compiler'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

const signingEnvironment = {
  INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v1',
  INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: Buffer.alloc(32, 3).toString('base64url'),
}
const originalSigningEnvironment = {
  kid: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID,
  key: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT,
}

function setSigningEnvironment() {
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = signingEnvironment.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = signingEnvironment.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT
}

function restoreSigningEnvironment() {
  if (originalSigningEnvironment.kid === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID
  else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = originalSigningEnvironment.kid
  if (originalSigningEnvironment.key === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT
  else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = originalSigningEnvironment.key
}

function pageSnapshot(overrides: Record<string, unknown> = {}) {
  return {
    replacement_in_progress: false,
    eligible_build_id: 'build-a',
    cursor_build_changed: false,
    rows: [],
    facets: [],
    total_matching: '0',
    ...overrides,
  }
}

function mechanismBinding() {
  const snapshot = compileCapabilityKnowledge(getCatalog())
  const scu = snapshot.scus.find((candidate) => candidate.scu_id === 'scu.bodha.mechanism.network')
  if (!scu) throw new Error('mechanism SCU missing from compiled snapshot')
  const binding = scu.bindings.find((candidate) => candidate.binding_id === 'registry:marsys://tool/L2/query_mechanisms')
  if (!binding) throw new Error('mechanism binding missing from compiled snapshot')
  return binding
}

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
    setSigningEnvironment()
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [pageSnapshot()] } as never)
  })

  afterEach(restoreSigningEnvironment)

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
    expect(rowsSql).toMatch(/ORDER BY \(d\.mechanism_class = ANY\([^)]*\)\) DESC/)
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
      .mockResolvedValueOnce({ rows: [pageSnapshot({
        rows: [
          { mechanism_id: 'm1', mechanism_class: 'convergent_dispositor_chain', mechanism_name: 'x' },
          { mechanism_id: 'm2', mechanism_class: 'mutual_aspect_triangle', mechanism_name: 'y' },
        ],
        facets: [
          { mechanism_class: 'convergent_dispositor_chain', valence: 'mixed', is_chain_circuit: true, n: '1' },
          { mechanism_class: 'mutual_aspect_triangle', valence: 'mixed', is_chain_circuit: false, n: '60' },
        ],
        total_matching: '61',
      })] } as never) // L+1 page, full facets, and full count share one receipt-pinned snapshot
    const result = await queryMechanismsCapability.handler({ chart_id: CHART_A, limit: 1 }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['total_matching']).toBe(61)
    expect(content['chain_circuit_count']).toBe(1)
    const facets = content['facets'] as Record<string, Record<string, number>>
    expect(facets['by_mechanism_class']['mutual_aspect_triangle']).toBe(60)
    expect(facets['by_mechanism_class']['convergent_dispositor_chain']).toBe(1)
    expect(content['more_available']).toBe(true)
    expect(content['next_offset']).toBe(1)
  })

  it('pins first, middle, and final pages to the same receipt build without duplicate progression', async () => {
    const rows = [{ mechanism_id: 'm1' }, { mechanism_id: 'm2' }, { mechanism_id: 'm3' }]
    const activeBuild = 'build-a'
    vi.mocked(mockQuery).mockImplementation((_sql: string, params: unknown[] = []) => {
      const fetchLimit = Number(params.at(-2))
      const offset = Number(params.at(-1))
      const cursorBuild = params.find((value) => value === 'build-a' || value === 'build-b') as string | undefined
      return Promise.resolve({ rows: [pageSnapshot({
        eligible_build_id: activeBuild,
        cursor_build_changed: cursorBuild !== undefined && cursorBuild !== activeBuild,
        rows: rows.slice(offset, offset + fetchLimit),
        total_matching: String(rows.length),
      })] } as never)
    })

    const first = (await queryMechanismsCapability.handler({ chart_id: CHART_A, limit: 1 }, undefined)).content as Record<string, unknown>
    const middle = (await queryMechanismsCapability.handler({ chart_id: CHART_A, limit: 1, page_cursor: first['next_page_cursor'] }, undefined)).content as Record<string, unknown>
    const final = (await queryMechanismsCapability.handler({ chart_id: CHART_A, limit: 1, page_cursor: middle['next_page_cursor'] }, undefined)).content as Record<string, unknown>
    const served = [first, middle, final].flatMap((page) => (page['rows'] as Array<{ mechanism_id: string }>).map((row) => row.mechanism_id))
    expect(served).toEqual(['m1', 'm2', 'm3'])
    expect(new Set(served).size).toBe(served.length)
    expect([first['more_available'], middle['more_available'], final['more_available']]).toEqual([true, true, false])
    expect([first['next_offset'], middle['next_offset'], final['next_offset']]).toEqual([1, 2, null])
    expect([first['build_id'], middle['build_id'], final['build_id']]).toEqual(['build-a', 'build-a', 'build-a'])
    expect(activeBuild).toBe('build-a')
  })

  it('requires restart instead of mixing a continuation with a replacement build', async () => {
    let activeBuild = 'build-a'
    vi.mocked(mockQuery).mockImplementation((_sql: string, params: unknown[] = []) => Promise.resolve({ rows: [pageSnapshot({
      eligible_build_id: activeBuild,
      cursor_build_changed: params.some((value) => (value === 'build-a' || value === 'build-b') && value !== activeBuild),
      rows: [{ mechanism_id: activeBuild === 'build-a' ? 'a1' : 'b1' }, { mechanism_id: 'more' }],
      total_matching: '2',
    })] } as never))
    const first = (await queryMechanismsCapability.handler({ chart_id: CHART_A, limit: 1 }, undefined)).content as Record<string, unknown>
    activeBuild = 'build-b'

    const rebuilt = await queryMechanismsCapability.handler({ chart_id: CHART_A, limit: 1, page_cursor: first['next_page_cursor'] }, undefined)

    expect(rebuilt).toMatchObject({
      is_error: true,
      content: { code: 'page_cursor_build_changed', restart_required: true, cursor_build_id: 'build-a', active_build_id: 'build-b' },
    })
  })

  it('derives a cursor continuation receipt only from the reviewed build-pinned envelope', async () => {
    vi.mocked(mockQuery).mockResolvedValueOnce({ rows: [pageSnapshot({
      rows: [{ mechanism_id: 'm1' }, { mechanism_id: 'm2' }],
      total_matching: '2',
    })] } as never)
    const args = { chart_id: CHART_A, limit: 1 }
    const result = await queryMechanismsCapability.handler(args, undefined)
    const content = result.content as Record<string, unknown>

    expect(mechanismBinding()).toMatchObject({
      pagination: 'cursor', pagination_verified: true, result_collection_verified: true,
      pagination_contract: {
        request_position_path: 'page_cursor', result_collection_path: 'content.rows',
        next_path: 'content.next_page_cursor',
        deterministic_order: expect.arrayContaining(['mechanism_id ASC']),
      },
    })
    expect(deriveInquiryPaginationReceipt(mechanismBinding(), result, args))
      .toEqual({ semantics: 'cursor', exhausted: false, next: content['next_page_cursor'] })
  })

  it('normalizes fractional, invalid, and nonfinite pagination before SQL', async () => {
    await queryMechanismsCapability.handler({ chart_id: CHART_A, limit: 0.5 }, undefined)
    let pageParams = vi.mocked(mockQuery).mock.calls[0]?.[1] as unknown[]
    expect(pageParams.slice(-2)).toEqual([51, 0])

    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
    await queryMechanismsCapability.handler({ chart_id: CHART_A, limit: Number.POSITIVE_INFINITY, offset: Number.POSITIVE_INFINITY }, undefined)
    pageParams = vi.mocked(mockQuery).mock.calls[0]?.[1] as unknown[]
    expect(pageParams.slice(-2)).toEqual([51, 0])

    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
    await queryMechanismsCapability.handler({ chart_id: CHART_A, limit: 'invalid', offset: 'invalid' }, undefined)
    pageParams = vi.mocked(mockQuery).mock.calls[0]?.[1] as unknown[]
    expect(pageParams.slice(-2)).toEqual([51, 0])
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

/**
 * query_muhurta_lattice — ṢAḌ-DARŚANA W3 item 36 substrate reader.
 * Covers the two things this capability must get right beyond "it runs SQL":
 * half-open overlap semantics (a candidate window must not miss a factor span that
 * straddles its edge) and the §N.6 density split (cited findings vs uncited
 * conventions counted separately, never flattened into one row count).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryMuhurtaLatticeCapability } from '../query_muhurta_lattice'

const START = '2026-08-05T00:00:00Z'
const END = '2026-08-06T00:00:00Z'

function row(over: Record<string, unknown> = {}) {
  return {
    factor_family: 'kalam',
    factor_key: 'rahu_kalam',
    start_utc: '2026-08-05T03:00:00Z',
    end_utc: '2026-08-05T04:30:00Z',
    detail: { category: 'inauspicious' },
    reference_location_key: 'reference',
    source_citation: 'Drik Panchang published index tables',
    corpus_status: 'computed_cited',
    ...over,
  }
}

describe('queryMuhurtaLatticeCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('uses half-open overlap arithmetic (row.start < end AND row.end > start), param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row()] })
    await queryMuhurtaLatticeCapability.handler({ start_utc: START, end_utc: END }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('start_utc < $1')
    expect(sql).toContain('end_utc > $2')
    expect(sql).toContain('FROM bg_muhurta_lattice')
    expect(params[0]).toBe(END)
    expect(params[1]).toBe(START)
  })

  it('counts cited and uncited-convention rows SEPARATELY (§N.6 — never one flat count)', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        row(),
        row({ factor_key: 'yamakantaka', corpus_status: 'computed_uncited_convention' }),
        row({ factor_key: 'visha_ghati', corpus_status: 'computed_uncited_convention' }),
      ],
    })
    const result = await queryMuhurtaLatticeCapability.handler({ start_utc: START, end_utc: END }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(3)
    expect(content['cited_row_count']).toBe(1)
    expect(content['convention_only_row_count']).toBe(2)
    expect(content['convention_only_keys']).toEqual(['visha_ghati', 'yamakantaka'])
    expect(String(content['convention_only_note'])).toContain('NOT cited classical findings')
  })

  it('emits a null convention note when every row is cited (no fabricated caveat)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row()] })
    const result = await queryMuhurtaLatticeCapability.handler({ start_utc: START, end_utc: END }, undefined)
    expect((result.content as Record<string, unknown>)['convention_only_note']).toBeNull()
  })

  it('carries an honest empty_reason naming the rolling-horizon cause', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryMuhurtaLatticeCapability.handler({ start_utc: START, end_utc: END }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('rolling forward horizon')
  })

  it('rejects a missing/unparseable interval and an inverted one, without touching the DB', async () => {
    for (const args of [
      {},
      { start_utc: 'not-a-date', end_utc: END },
      { start_utc: END, end_utc: START },
    ]) {
      const result = await queryMuhurtaLatticeCapability.handler(args as Record<string, unknown>, undefined)
      expect(result.is_error).toBe(true)
    }
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('rejects an unknown factor_family rather than silently returning everything', async () => {
    const result = await queryMuhurtaLatticeCapability.handler(
      { start_utc: START, end_utc: END, factor_family: 'not_a_family' }, undefined,
    )
    expect(result.is_error).toBe(true)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('caps limit and reports truncation honestly', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row(), row({ factor_key: 'abhijit' })] })
    const result = await queryMuhurtaLatticeCapability.handler(
      { start_utc: START, end_utc: END, limit: 2 }, undefined,
    )
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(params[params.length - 1]).toBe(2)
    expect((result.content as Record<string, unknown>)['truncated']).toBe(true)
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryMuhurtaLatticeCapability.handler({ start_utc: START, end_utc: END }, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id, and no native identifiers in the description', () => {
    expect(queryMuhurtaLatticeCapability.scope).toBe('global')
    expect(queryMuhurtaLatticeCapability.required_inputs).not.toContain('chart_id')
    // Chart-agnostic gate rules 3 + native-cardinality: the reference location is the
    // native's birthplace, so it must appear as row DATA and never in served prose.
    expect(queryMuhurtaLatticeCapability.description).not.toContain('Bhubaneswar')
    expect(queryMuhurtaLatticeCapability.description).not.toMatch(/\b\d{1,3}(?:,\d{3}){1,2}\b/)
  })
})

/**
 * query_domain_reading optional build fence (Pūrṇa R3 / review RC-1, RC-2).
 *
 * assess_* composes this handler and passes the chart's served build set. With a fence, every
 * bodha_* read must bind it at the placeholder it names; without one, the standalone tool keeps
 * its historical chart-scoped reads.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryDomainReadingCapability } from '../query_domain_reading'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SERVED = '11111111-1111-4111-8111-111111111111'
const SIGNAL = '44444444-4444-4444-8444-444444444444'

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockImplementation(async (sql: string) => {
    const s = String(sql)
    if (s.includes('FROM bodha_question_lenses') && s.includes('lens_id')) {
      return { rows: [{
        lens_id: 'lens-1', question_type: 'wealth',
        template_element_ids_jsonb: { signal_ids: [SIGNAL] },
        all_relevant_ranked_jsonb: { ranked_signals: [{ signal_id: SIGNAL, rank: 1 }] },
      }] }
    }
    if (s.includes('COUNT(*)')) return { rows: [{ n: 1 }] }
    return { rows: [] }
  })
})

/**
 * Served-evidence reads. The DEFECT-001 freshness note (provenance/freshness_notes.ts) is a
 * whole-chart table-health diagnostic by design — it measures orphaned references across every
 * stored row, not the served evidence — so it is deliberately outside the fence.
 */
function bodhaCalls(): Array<{ sql: string; params: unknown[] }> {
  return mockQuery.mock.calls
    .map(([sql, params]) => ({ sql: String(sql), params: (params ?? []) as unknown[] }))
    .filter(({ sql }) => sql.includes('FROM bodha_') && !sql.includes('WITH refs AS'))
}

describe('query_domain_reading build fence', () => {
  it('binds the served build set at the named placeholder of every bodha read', async () => {
    const result = await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'wealth', build_id: [SERVED] }, undefined,
    )
    expect(result.is_error).toBe(false)
    const calls = bodhaCalls()
    // lens page, lens count, CDLM cells, discriminated pool, lens anchor slice, text hydration.
    expect(calls.length).toBeGreaterThanOrEqual(5)
    for (const { sql, params } of calls) {
      const placeholders = [...sql.matchAll(/build_id = ANY\(\$(\d+)::uuid\[\]\)/g)].map((match) => Number(match[1]))
      expect(placeholders, sql).toHaveLength(1)
      expect(params[placeholders[0]! - 1], sql).toEqual([SERVED])
    }
  })

  it('fences the available-domain listing too', async () => {
    await queryDomainReadingCapability.handler({ chart_id: CHART_ID, domain: 'not-a-domain', build_id: [SERVED] }, undefined)
    const [call] = bodhaCalls()
    expect(call!.sql).toContain('build_id = ANY($3::uuid[])')
    expect(call!.params[2]).toEqual([SERVED])
  })

  it('leaves standalone reads unfenced when no build set is supplied', async () => {
    await queryDomainReadingCapability.handler({ chart_id: CHART_ID, domain: 'wealth' }, undefined)
    for (const { sql } of bodhaCalls()) expect(sql).not.toContain('build_id')
  })

  it('refuses (never reads unfenced, never matches zero rows) on an explicit-empty build fence', async () => {
    mockQuery.mockClear()
    const result = await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'wealth', build_id: [] }, undefined,
    )
    expect(result.is_error).toBe(true)
    expect((result.content as Record<string, unknown>)['code']).toBe('explicit_empty_build_fence')
    expect(mockQuery).not.toHaveBeenCalled()
  })
})

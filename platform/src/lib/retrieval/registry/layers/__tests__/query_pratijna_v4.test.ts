/**
 * query_pratijna_v4.test.ts — PRATIJÑĀ v4 Lane B4 consumer audit
 * ================================================================
 * query_pratijna is a raw pass-through envelope over bodha_pratijna (no grade/
 * status branching logic besides the no_evidence count), so under the v4 engine
 * it stays structurally safe — but two pieces of served TEXT described v3
 * semantics that are no longer true under v4:
 *   1. `reference_note` claimed supporting_signal_ids/contradicting_signal_ids
 *      are resolvable via query_signals — under v4 they are always NULL (the
 *      engine never reads bodha_msr_signals).
 *   2. `no_evidence_qualification` claimed a no_evidence row means "zero
 *      supporting/contradicting signals" — under v4 it means "no karyatva
 *      registry entry for this event class" (bo_pratijna.py's defensive path),
 *      a different condition entirely.
 * These tests prove the served text now states the v4-accurate meaning.
 */
import { describe, it, expect, vi } from 'vitest'

const CHART_A = '482012f1-710e-4a25-994a-93821f5871aa'

const mockRows = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    if (String(sql).includes('COUNT(*)')) return { rows: [{ total: '2' }] }
    return { rows: mockRows() }
  }),
}))

import { queryPratijnaCapability } from '../L2_bodha/query_pratijna'

describe('query_pratijna — PRATIJÑĀ v4 served-text accuracy (Lane B4)', () => {
  it('reference_note no longer tells the caller to resolve supporting_signal_ids via query_signals', async () => {
    mockRows.mockReturnValue([
      { pratijna_id: 'p1', event_class_id: 'marriage', status: 'promised',
        supporting_signal_ids: null, contradicting_signal_ids: null },
    ])
    const r = await queryPratijnaCapability.handler({ chart_id: CHART_A }, {})
    expect(r.is_error).toBe(false)
    const content = r.content as Record<string, unknown>
    expect(String(content['reference_note'])).not.toMatch(/resolve them via query_signals/)
    expect(String(content['reference_note'])).toMatch(/always NULL/)
    expect(String(content['reference_note'])).toMatch(/factor_ledger/)
  })

  it('no_evidence_qualification states the v4 meaning (no karyatva registry entry), not the stale v3 meaning (zero signals)', async () => {
    mockRows.mockReturnValue([
      { pratijna_id: 'p1', event_class_id: 'career_change', status: 'no_evidence', grade: null },
      { pratijna_id: 'p2', event_class_id: 'marriage', status: 'promised', grade: 8.5 },
    ])
    const r = await queryPratijnaCapability.handler({ chart_id: CHART_A }, {})
    const content = r.content as Record<string, unknown>
    const q = String(content['no_evidence_qualification'])
    expect(q).toMatch(/no karyatva registry entry/)
    expect(q).not.toMatch(/zero supporting\/contradicting signals/)
  })

  it('no_evidence_qualification is null when no row has status no_evidence', async () => {
    mockRows.mockReturnValue([
      { pratijna_id: 'p1', event_class_id: 'marriage', status: 'promised', grade: 8.5 },
    ])
    const r = await queryPratijnaCapability.handler({ chart_id: CHART_A }, {})
    const content = r.content as Record<string, unknown>
    expect(content['no_evidence_qualification']).toBeNull()
  })
})

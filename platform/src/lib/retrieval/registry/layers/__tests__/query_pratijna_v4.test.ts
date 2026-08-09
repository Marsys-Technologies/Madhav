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

describe('query_pratijna — G10 varga_confirmation serving (SAMPURTI L0e)', () => {
  it('description mentions varga_confirmation consensus with per_system, consensus_dignity, unanimous, dissent (G10/SAMPURTI L0e)', () => {
    // The description is a static string on the capability — no DB call needed.
    const desc = queryPratijnaCapability.description
    expect(desc).toMatch(/varga_confirmation/)
    expect(desc).toMatch(/per_system/)
    expect(desc).toMatch(/consensus_dignity/)
    expect(desc).toMatch(/unanimous/)
    expect(desc).toMatch(/dissent/)
    // G10 annotation
    expect(desc).toMatch(/G10/)
  })

  it('reference_note in handler output documents varga_confirmation shape and G10 provenance', async () => {
    mockRows.mockReturnValue([
      { pratijna_id: 'p1', event_class_id: 'marriage', status: 'promised', grade: 8.5,
        varga_confirmation: JSON.stringify({
          varga: 'D9', graha: 'Venus',
          per_system: { lahiri_chitrapaksha: { varga_sign: 'Pisces', dignity_state: 'own', band: 0.8 } },
          consensus_dignity: 'own', unanimous: false, dissent: [],
          source: 'cross-ayanamsha consensus, 5 L1-computed systems (G10/SAMPURTI L0e)',
        }) },
    ])
    const r = await queryPratijnaCapability.handler({ chart_id: CHART_A }, {})
    expect(r.is_error).toBe(false)
    const content = r.content as Record<string, unknown>
    const refNote = String(content['reference_note'])
    // reference_note must document varga_confirmation
    expect(refNote).toMatch(/varga_confirmation/)
    // must cite G10 or cross-ayanamsha consensus
    expect(refNote).toMatch(/G10|cross-ayanamsha/)
  })

  it('varga_confirmation column is selected (rows pass it through)', async () => {
    const vcPayload = {
      varga: 'D10', graha: 'Mercury',
      per_system: {
        lahiri_chitrapaksha: { varga_sign: 'Capricorn', dignity_state: 'great_enemy', band: 0.2 },
        raman: { varga_sign: 'Capricorn', dignity_state: 'great_enemy', band: 0.2 },
      },
      consensus_dignity: 'great_enemy', unanimous: false, dissent: [],
      source: 'cross-ayanamsha consensus, 5 L1-computed systems (G10/SAMPURTI L0e)',
    }
    mockRows.mockReturnValue([
      { pratijna_id: 'p1', event_class_id: 'career_advancement', status: 'promised',
        grade: 7.2, varga_confirmation: JSON.stringify(vcPayload) },
    ])
    const r = await queryPratijnaCapability.handler({ chart_id: CHART_A }, {})
    const content = r.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    // The served row must carry varga_confirmation through unchanged
    expect(rows[0]['varga_confirmation']).toBeTruthy()
    // The JSON payload must round-trip correctly (served as-is from DB)
    const vc = JSON.parse(rows[0]['varga_confirmation'] as string)
    expect(vc['varga']).toBe('D10')
    expect(vc['consensus_dignity']).toBe('great_enemy')
  })
})

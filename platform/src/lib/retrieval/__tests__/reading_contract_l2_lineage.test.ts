/**
 * reading_contract_l2_lineage.test.ts — N-91 between-state disclosure, reading-contract half.
 *
 * When the L2 lineage detector's flag (`l2_receipts_predate_l1`, or the fail-closed
 * `l2_lineage_check_failed`) is on the response, buildReadingContract must take the existing
 * "NOT yet anchored ... drill before treating it as confirmed" branch WITH the cause appended,
 * instead of the "grounded in N resolvable L1 fact reference(s)" count sentence. With the flag
 * unset the sentence is the unchanged count sentence (register_block_w3.test.ts pins it too).
 */
import { describe, it, expect } from 'vitest'
import { buildReadingContract, buildRetrievalEnvelope, judgmentFlag, type V3Envelope } from '@/lib/retrieval/envelope'

const NOT_ANCHORED = 'Its reading is NOT yet anchored to resolvable L1 fact references in this envelope; drill via the pointers before treating it as confirmed.'
const COUNT = /grounded in 12 resolvable L1 fact reference\(s\)/

const staleFlag = judgmentFlag('l2_receipts_predate_l1', 'bo_laksana built against ga_structural pre-rebuild', 'warning')
const failedFlag = judgmentFlag('l2_lineage_check_failed', 'permission denied', 'warning')

describe('buildReadingContract — L2 lineage flag', () => {
  it('flag unset: the count sentence is unchanged', () => {
    const t = buildReadingContract({ epistemicGrade: 'ganita_fact', groundingFactCount: 12, judgmentFlags: [] })
    expect(t).toMatch(COUNT)
    expect(t).not.toContain('NOT yet anchored')
    expect(t).not.toContain('Cause:')
    // undefined flags behave the same as an empty list
    expect(buildReadingContract({ epistemicGrade: 'ganita_fact', groundingFactCount: 12 })).toMatch(COUNT)
  })

  it('l2_receipts_predate_l1 set: NOT-anchored branch with the stale-L2 cause, and NO count sentence', () => {
    const t = buildReadingContract({ epistemicGrade: 'ganita_fact', groundingFactCount: 12, judgmentFlags: [staleFlag] })
    expect(t).toContain(NOT_ANCHORED)
    expect(t).toMatch(/Cause: the L2 receipts behind these fact_ids predate the current L1 \(chart_facts\) rebuild/)
    expect(t).toMatch(/may no longer resolve/)
    expect(t).not.toMatch(/grounded in \d+ resolvable/)
    expect(t).not.toMatch(COUNT)
  })

  it('l2_lineage_check_failed (fail closed): NOT-anchored branch naming the unchecked lineage, never the count sentence', () => {
    const t = buildReadingContract({ epistemicGrade: 'ganita_fact', groundingFactCount: 12, judgmentFlags: [failedFlag] })
    expect(t).toContain(NOT_ANCHORED)
    expect(t).toMatch(/Cause: the L2-to-L1 lineage check could not be completed/)
    expect(t).not.toMatch(/grounded in \d+ resolvable/)
  })

  it('both the structured and the bare-string flag shapes are honoured', () => {
    const t = buildReadingContract({ epistemicGrade: 'ganita_fact', groundingFactCount: 3, judgmentFlags: ['l2_receipts_predate_l1: bo_x'] })
    expect(t).toContain(NOT_ANCHORED)
  })

  it('the flag does not change the zero-grounding or floored_null branches', () => {
    const none = buildReadingContract({ epistemicGrade: 'ganita_fact', groundingFactCount: 0, judgmentFlags: [staleFlag] })
    expect(none).toContain(NOT_ANCHORED)
    expect(none).not.toContain('Cause:')
    const floored = buildReadingContract({ epistemicGrade: 'floored_null', groundingFactCount: 12, judgmentFlags: [staleFlag] })
    expect(floored).toMatch(/HONEST EMPTY/)
    expect(floored).not.toContain('NOT yet anchored')
  })

  it('an unrelated flag does not trigger the lineage branch', () => {
    const t = buildReadingContract({
      epistemicGrade: 'ganita_fact', groundingFactCount: 12,
      judgmentFlags: [judgmentFlag('karaka_unresolved', 'x')],
    })
    expect(t).toMatch(COUNT)
  })

  it('the flag still counts in the flags sentence (it is a stated limit, not decoration)', () => {
    const t = buildReadingContract({ epistemicGrade: 'ganita_fact', groundingFactCount: 12, judgmentFlags: [staleFlag] })
    expect(t).toMatch(/1 judgment flag/)
  })
})

describe('buildRetrievalEnvelope (v3) — the flag rides into reading_contract end to end', () => {
  const base = {
    tool: 'judgment_query',
    content: { verdict: { grade: 'x' } },
    epistemic: { grade: 'ganita_fact' as const, verified_fraction: 1, note: 'fixture' },
    grounding: { fact_ids: Array.from({ length: 12 }, (_, i) => `f-${i}`), citations: [], grounding_score: 1 },
  }

  it('without the flag: grounded-in-N sentence', () => {
    const env = buildRetrievalEnvelope({ ...base, judgment_flags: [] }, 'v3') as V3Envelope
    expect(env.reading_contract).toMatch(COUNT)
  })

  it('with l2_receipts_predate_l1 in judgment_flags: NOT-anchored sentence with cause', () => {
    const env = buildRetrievalEnvelope({ ...base, judgment_flags: [staleFlag] }, 'v3') as V3Envelope
    expect(env.reading_contract).toContain(NOT_ANCHORED)
    expect(env.reading_contract).toMatch(/Cause: the L2 receipts behind these fact_ids predate/)
    expect(env.reading_contract).not.toMatch(/grounded in \d+ resolvable/)
    // the grounding block itself is untouched (ids are never dropped, only disclosed)
    expect(env.grounding.fact_ids).toHaveLength(12)
  })
})

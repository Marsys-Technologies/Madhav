/**
 * V3-E-041 fix — entitlement/consent refusal codes must be classified
 * honestly, not collapsed into the generic `unknown`/"plumbing"/`retry`
 * bucket.
 *
 * Prior to this fix, `classifyKind()` (`lib/pariprashna/errors/classify.ts`)
 * had no case for any of `FORBIDDEN`, `CHART_NOT_FOUND`,
 * `SUBJECT_CONSENT_REQUIRED:*`, `CONVERSATION_NOT_FOUND` — the four codes
 * `authorizeTurn` (`pipeline/safety_gate.ts`) emits for entitlement/consent
 * refusals. All four fell through to `kind: 'unknown'`, rendering as
 * "Something failed on our side... the plumbing. It is logged." with
 * `actions: ['retry']` — actively misleading: a permission/consent refusal
 * is not a transient server error, and "retry" is wrong advice (S4 Native
 * Surrogate triage, V3-E-041, EDIR severity S2/HIGH,
 * disposition FIX_THIS_SESSION).
 *
 * This test pins the RED behavior in comments (the pre-fix assertions,
 * which the old code satisfied and the new code no longer does) and asserts
 * the GREEN behavior below: each code now gets its own honest kind, a
 * message that states what actually happened, and a `retry`-free action
 * set.
 */
import { describe, it, expect } from 'vitest'
import { classifyPariprashnaError } from '../classify'

describe('V3-E-041 — entitlement/consent codes are no longer misclassified as unknown/plumbing', () => {
  it('FORBIDDEN classifies as not_authorized, not unknown, and never offers retry', () => {
    const e = classifyPariprashnaError('FORBIDDEN')
    // RED (pre-fix): e.kind === 'unknown', e.bandLabel === 'Something failed on our side',
    //                e.actions === ['retry'].
    expect(e.kind).toBe('not_authorized')
    expect(e.kind).not.toBe('unknown')
    expect(e.bandLabel).toBe("You don't have access to this chart")
    expect(e.bandLabel).not.toBe('Something failed on our side')
    expect(e.sentence).not.toBe('Not the chart, not your question — the plumbing. It is logged.')
    expect(e.actions).not.toContain('retry')
    expect(e.actions).toEqual([])
  })

  it('CHART_NOT_FOUND classifies as chart_not_found, not unknown, and never offers retry', () => {
    const e = classifyPariprashnaError('CHART_NOT_FOUND')
    // RED (pre-fix): e.kind === 'unknown', e.actions === ['retry'].
    expect(e.kind).toBe('chart_not_found')
    expect(e.kind).not.toBe('unknown')
    expect(e.bandLabel).toBe('This chart could not be found')
    expect(e.actions).not.toContain('retry')
    expect(e.actions).toEqual([])
  })

  it('SUBJECT_CONSENT_REQUIRED:<reason> classifies as consent_required via prefix match, not unknown, and never offers retry', () => {
    const e = classifyPariprashnaError('SUBJECT_CONSENT_REQUIRED:no_consent_row')
    // RED (pre-fix): e.kind === 'unknown', e.actions === ['retry'] — actively
    // wrong advice for a consent refusal (retrying changes nothing about
    // consent state).
    expect(e.kind).toBe('consent_required')
    expect(e.kind).not.toBe('unknown')
    expect(e.bandLabel).toBe('Consent is required for this reading')
    expect(e.actions).not.toContain('retry')
    expect(e.actions).toEqual([])
  })

  it('a different SUBJECT_CONSENT_REQUIRED reason still matches via prefix, not exact-equality', () => {
    const e = classifyPariprashnaError('SUBJECT_CONSENT_REQUIRED:withdrawn')
    expect(e.kind).toBe('consent_required')
  })

  it('CONVERSATION_NOT_FOUND classifies as conversation_not_found, not unknown, and never offers retry', () => {
    const e = classifyPariprashnaError('CONVERSATION_NOT_FOUND')
    // RED (pre-fix): e.kind === 'unknown', e.actions === ['retry'].
    expect(e.kind).toBe('conversation_not_found')
    expect(e.kind).not.toBe('unknown')
    expect(e.bandLabel).toBe('This conversation could not be found')
    expect(e.actions).not.toContain('retry')
    expect(e.actions).toEqual([])
  })

  it('none of the four leak the raw code/message into the sentence (§7.5 discipline preserved)', () => {
    const codes = ['FORBIDDEN', 'CHART_NOT_FOUND', 'SUBJECT_CONSENT_REQUIRED:no_consent_row', 'CONVERSATION_NOT_FOUND']
    for (const code of codes) {
      const e = classifyPariprashnaError(code)
      expect(e.sentence.toLowerCase()).not.toContain('no_consent_row')
    }
  })

  it('a genuinely unmapped code still falls through to unknown/plumbing/retry (regression guard: fix is additive, not a removal of the fallback)', () => {
    const e = classifyPariprashnaError('SOME_UNMAPPED_CODE')
    expect(e.kind).toBe('unknown')
    expect(e.bandLabel).toBe('Something failed on our side')
    expect(e.actions).toEqual(['retry'])
  })
})

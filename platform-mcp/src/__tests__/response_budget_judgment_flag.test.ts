/**
 * response_budget_judgment_flag.test.ts — W3-L2 (RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF §E W3
 * item 2 "flags closed enum + d8/hollow-emitter migration").
 * ==========================================================================================
 * `finalizeMcpBudget` used to inject a raw, free-floating string
 * (`response_still_over_<N>kb_budget_after_full_trim`) into whatever field the caller named
 * as its judgment-flags field, once every mechanical trim lever was exhausted and the
 * response was STILL over the true byte ceiling. This pins that the injected entry is now
 * the closed enum code `budget_exceeded_after_trim`, with the `<N>kb` detail moved into
 * `detail` rather than baked into an ad-hoc string.
 */
import { describe, it, expect } from 'vitest'
import { finalizeMcpBudget, type TrimmableSection } from '../lib/response_budget.js'

type Content = { fields: Record<string, string>; judgment_flags?: unknown[]; drill_pointers?: unknown[] }

// Many SHORT (<=120 char) string fields, each individually under
// truncateLongStringsInPlace's MAX_STRING_CHARS threshold (so that last-resort lever cannot
// shrink any single one of them) but collectively far over a 1KB ceiling — the genuine
// "base content alone exceeds budget, every mechanical lever exhausted" case this test
// targets. A single giant string would instead get silently truncated to fit, which is a
// DIFFERENT (successful) code path, not the one this test needs to exercise.
function makeOverBudgetContent(fieldCount: number): Content {
  const fields: Record<string, string> = {}
  for (let i = 0; i < fieldCount; i++) fields[`field_${i}`] = 'y'.repeat(100)
  return { fields }
}

describe('finalizeMcpBudget — over-budget disclosure uses the closed enum (W3-L2)', () => {
  it('injects {code: "budget_exceeded_after_trim", detail: "<N>kb ..."} when still over budget after every lever', () => {
    const content = makeOverBudgetContent(50) // 50 x 100-char fields, none individually truncatable, all non-trimmable
    const sections: TrimmableSection<Content>[] = []
    const result = finalizeMcpBudget(content, { maxKb: 1, sections })

    const flags = (result['judgment_flags'] as Array<{ code: string; detail?: string }> | undefined) ?? []
    const injected = flags.find(f => typeof f === 'object' && f.code === 'budget_exceeded_after_trim')
    expect(injected).toBeDefined()
    expect(injected?.detail).toContain('1kb')
    // Never the old free-floating string shape.
    expect(flags.some(f => typeof f === 'string')).toBe(false)
  })

  it('does not inject the flag when the response fits under budget', () => {
    const content = makeOverBudgetContent(1)
    const sections: TrimmableSection<Content>[] = []
    const result = finalizeMcpBudget(content, { maxKb: 40, sections })
    const flags = (result['judgment_flags'] as Array<{ code: string }> | undefined) ?? []
    expect(flags.some(f => f.code === 'budget_exceeded_after_trim')).toBe(false)
  })

  it('appends to (never replaces) any judgment_flags entries already on content', () => {
    const content: Content = { ...makeOverBudgetContent(50), judgment_flags: [{ code: 'zero_rows_returned' }] }
    const result = finalizeMcpBudget(content, { maxKb: 1, sections: [] })
    const flags = (result['judgment_flags'] as Array<{ code: string }>) ?? []
    expect(flags.some(f => f.code === 'zero_rows_returned')).toBe(true)
    expect(flags.some(f => f.code === 'budget_exceeded_after_trim')).toBe(true)
  })
})

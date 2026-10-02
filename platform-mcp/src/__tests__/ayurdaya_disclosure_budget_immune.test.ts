/**
 * ayurdaya_disclosure_budget_immune.test.ts — SS N-62 Q10 (display-side).
 *
 * The Āyurdāya unreduced-base caveat (flat `caveat` on get_ayurdaya, nested
 * `ayurdaya_figure_disclosure` elsewhere) is a >120-char honesty sentence. The budget trimmer's
 * last-resort string walk truncates every long scalar it is allowed to — so both keys must be in
 * IMMUNE_HONESTY_FIELDS, or a small budget cuts the caveat mid-sentence. Mutation check: removing
 * either key from the set flips the corresponding assertion.
 */
import { describe, it, expect } from 'vitest'
import { finalizeMcpBudget, IMMUNE_HONESTY_FIELDS, type TrimmableSection } from '../lib/response_budget.js'

const CAVEAT = 'Unreduced base figure from the classical pinda/amsa/nisarga computation; no reductions (harana) are applied; not a prediction of lifespan.'

describe('Āyurdāya disclosure is budget-immune', () => {
  it('is registered in IMMUNE_HONESTY_FIELDS', () => {
    expect(CAVEAT.length).toBeGreaterThan(120)
    expect(IMMUNE_HONESTY_FIELDS.has('caveat')).toBe(true)
    expect(IMMUNE_HONESTY_FIELDS.has('ayurdaya_figure_disclosure')).toBe(true)
  })

  it('a flat get_ayurdaya `caveat` survives a tiny budget byte-for-byte', () => {
    const content = { caveat: CAVEAT, figure_kind: 'unreduced_base', padding: 'p'.repeat(20_000) }
    const sections: TrimmableSection<typeof content>[] = []
    const result = finalizeMcpBudget(content, { maxKb: 1, sections })
    expect(result.padding.length).toBeLessThan(20_000) // the mechanism really fired
    expect(result.caveat).toBe(CAVEAT)
  })

  it('the nested ayurdaya_figure_disclosure.caveat survives a tiny budget byte-for-byte', () => {
    const content = {
      ayurdaya_figure_disclosure: { figure_kind: 'unreduced_base', reductions_applied: false, caveat: CAVEAT },
      padding: 'p'.repeat(20_000),
    }
    const sections: TrimmableSection<typeof content>[] = []
    const result = finalizeMcpBudget(content, { maxKb: 1, sections })
    expect(result.padding.length).toBeLessThan(20_000)
    expect(result.ayurdaya_figure_disclosure.caveat).toBe(CAVEAT)
    expect(result.ayurdaya_figure_disclosure.reductions_applied).toBe(false)
  })
})

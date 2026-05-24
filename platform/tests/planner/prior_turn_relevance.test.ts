import { describe, expect, it } from 'vitest'
import { PipelinePlanSchema } from '@/lib/pipeline/types'

/**
 * Gate III — schema-level test that the planner type accepts a
 * `prior_turn_relevance` object with valid mode/used/reason fields, and
 * rejects malformed shapes.
 *
 * This is the safety net for the route.ts consumer; the live planner
 * regression (golden-set) is exercised separately by tests/planner/*.
 */
describe('PipelinePlan — prior_turn_relevance', () => {
  const basePlan = {
    query_class: 'factual',
    query_intent_summary: 'What house is Saturn in',
    asset_bundle: [],
    tool_calls: [
      { tool_name: 'msr_sql', params: {}, token_budget: 500, priority: 1 as const, reason: 'factual lookup' },
    ],
  }

  it('accepts independent mode with used=0', () => {
    const out = PipelinePlanSchema.safeParse({
      ...basePlan,
      prior_turn_relevance: {
        used: 0,
        reason: 'Self-contained chart lookup.',
        mode: 'independent',
      },
    })
    expect(out.success).toBe(true)
  })

  it('accepts narrative_context mode with used=1', () => {
    const out = PipelinePlanSchema.safeParse({
      ...basePlan,
      prior_turn_relevance: { used: 1, reason: 'Resolves pronoun.', mode: 'narrative_context' },
    })
    expect(out.success).toBe(true)
  })

  it('accepts continuation mode with used=1', () => {
    const out = PipelinePlanSchema.safeParse({
      ...basePlan,
      prior_turn_relevance: { used: 1, reason: 'Direct follow-up.', mode: 'continuation' },
    })
    expect(out.success).toBe(true)
  })

  it('coerces invalid used > 2 to absent (catch absorbs bad LLM output)', () => {
    const out = PipelinePlanSchema.safeParse({
      ...basePlan,
      prior_turn_relevance: { used: 3, reason: 'too many', mode: 'continuation' },
    })
    expect(out.success).toBe(true)
    expect(out.data?.prior_turn_relevance).toBeUndefined()
  })

  it('coerces unknown mode to absent (catch absorbs bad LLM output)', () => {
    const out = PipelinePlanSchema.safeParse({
      ...basePlan,
      prior_turn_relevance: { used: 0, reason: 'x', mode: 'borrow' },
    })
    expect(out.success).toBe(true)
    expect(out.data?.prior_turn_relevance).toBeUndefined()
  })

  it('is optional — plan without prior_turn_relevance still parses', () => {
    expect(PipelinePlanSchema.safeParse(basePlan).success).toBe(true)
  })
})

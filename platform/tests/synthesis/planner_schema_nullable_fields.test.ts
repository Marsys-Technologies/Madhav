/**
 * Regression tests: PipelinePlanSchema null-coercion for soft-optional string fields.
 *
 * Context: Anthropic and other providers sometimes return `null` for optional
 * narrative fields (synthesis_guidance, planning_rationale) instead of omitting
 * them. Zod's z.string().optional() accepts undefined but NOT null — the schema
 * previously rejected these responses with a 422 planner_failed error.
 *
 * The fix uses z.preprocess(v => v === null ? undefined : v, z.string()).optional()
 * so null is silently coerced to undefined before Zod validation runs.
 *
 * These tests verify:
 *  1. synthesis_guidance: null parses cleanly (the original bug).
 *  2. synthesis_guidance absent entirely parses cleanly.
 *  3. All soft-optional fields null simultaneously parses cleanly.
 *  4. HARD-REQUIRED fields (query_class, query_intent_summary) with null STILL FAIL.
 */

import { describe, it, expect } from 'vitest'
import { PipelinePlanSchema } from '@/lib/pipeline/types'

// Minimal valid planner response — all hard-required fields present
const BASE_PLAN = {
  query_class: 'predictive' as const,
  query_intent_summary: 'When does the native\'s next Saturn mahadasha begin?',
  asset_bundle: [
    { asset_id: 'FORENSIC', priority: 1 as const, reason: 'Floor: birth chart data.' },
  ],
  tool_calls: [
    { tool_name: 'query_dasha_periods', params: { dasha_lord: 'Saturn' }, token_budget: 800, priority: 1 as const, reason: 'Dasha sequence for Saturn.' },
  ],
}

describe('PipelinePlanSchema — null coercion for soft-optional string fields', () => {

  it('synthesis_guidance: null parses cleanly (the original A-S5 bug)', () => {
    const result = PipelinePlanSchema.safeParse({
      ...BASE_PLAN,
      synthesis_guidance: null,
    })
    expect(result.success).toBe(true)
    if (result.success) {
      // null is coerced to undefined — field is treated as absent
      expect(result.data.synthesis_guidance).toBeUndefined()
    }
  })

  it('synthesis_guidance absent entirely parses cleanly', () => {
    const result = PipelinePlanSchema.safeParse({ ...BASE_PLAN })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.synthesis_guidance).toBeUndefined()
    }
  })

  it('planning_rationale: null parses cleanly', () => {
    const result = PipelinePlanSchema.safeParse({
      ...BASE_PLAN,
      planning_rationale: null,
    })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.planning_rationale).toBeUndefined()
    }
  })

  it('all soft-optional fields null simultaneously parses cleanly', () => {
    const result = PipelinePlanSchema.safeParse({
      ...BASE_PLAN,
      synthesis_guidance: null,
      planning_rationale: null,
    })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.synthesis_guidance).toBeUndefined()
      expect(result.data.planning_rationale).toBeUndefined()
    }
  })

  it('synthesis_guidance with a real string parses and is preserved', () => {
    const guidance = 'Lead with exact dasha start date. State the sub-dasha sequence.'
    const result = PipelinePlanSchema.safeParse({
      ...BASE_PLAN,
      synthesis_guidance: guidance,
    })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.synthesis_guidance).toBe(guidance)
    }
  })

  // ── HARD-REQUIRED fields must still reject null ───────────────────────────

  it('query_class: null FAILS — hard-required field must surface as 422', () => {
    const result = PipelinePlanSchema.safeParse({
      ...BASE_PLAN,
      query_class: null,
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.message).toMatch(/query_class/)
    }
  })

  it('query_intent_summary: null FAILS — hard-required field must surface as 422', () => {
    const result = PipelinePlanSchema.safeParse({
      ...BASE_PLAN,
      query_intent_summary: null,
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.message).toMatch(/query_intent_summary/)
    }
  })

})

// ── Coercion detection helper (mirrors pipeline_planner.ts logic) ──────────

describe('coercion detection — mirrors pipeline_planner.ts call-site logic', () => {
  const SOFT_OPTIONAL_STRING_FIELDS = ['synthesis_guidance', 'planning_rationale'] as const

  function detectCoercedFields(rawPlannerArgs: unknown): Set<string> {
    const coercedFields = new Set<string>()
    if (rawPlannerArgs !== null && typeof rawPlannerArgs === 'object') {
      const raw = rawPlannerArgs as Record<string, unknown>
      for (const field of SOFT_OPTIONAL_STRING_FIELDS) {
        if (raw[field] === null) coercedFields.add(field)
      }
    }
    return coercedFields
  }

  it('detects synthesis_guidance: null as a coercion', () => {
    const raw = { ...BASE_PLAN, synthesis_guidance: null }
    const coerced = detectCoercedFields(raw)
    expect(coerced.has('synthesis_guidance')).toBe(true)
    expect(coerced.size).toBe(1)
  })

  it('does not report absent fields as coercions', () => {
    const coerced = detectCoercedFields(BASE_PLAN)
    expect(coerced.size).toBe(0)
  })

  it('detects both soft-optional fields when both are null', () => {
    const raw = { ...BASE_PLAN, synthesis_guidance: null, planning_rationale: null }
    const coerced = detectCoercedFields(raw)
    expect(coerced.has('synthesis_guidance')).toBe(true)
    expect(coerced.has('planning_rationale')).toBe(true)
    expect(coerced.size).toBe(2)
  })

  it('does not detect hard-required fields as soft-optional coercions', () => {
    // query_class is not in the SOFT_OPTIONAL list — setting it to null
    // would fail schema parse, not be silently coerced
    const raw = { ...BASE_PLAN, query_class: null }
    const coerced = detectCoercedFields(raw)
    expect(coerced.size).toBe(0)  // not in soft-optional list
    // Confirm the schema also rejects it
    const parsed = PipelinePlanSchema.safeParse(raw)
    expect(parsed.success).toBe(false)
  })
})

/**
 * Regression tests: PipelinePlanSchema null-coercion for soft-optional fields.
 *
 * Context: Anthropic and other providers sometimes return `null` for optional
 * fields instead of omitting them. Zod's .optional() accepts undefined but NOT
 * null in Zod v4 — the schema previously rejected these responses with a 422
 * planner_failed error.
 *
 * Two fix patterns applied in PipelinePlanSchema (§4a):
 *   (A) String fields (synthesis_guidance, planning_rationale):
 *       z.preprocess(v => v === null ? undefined : v, z.string().optional())
 *   (B) Enum/boolean/array/object fields (all other soft-optional):
 *       z.TYPE.optional().catch(undefined)
 *
 * These tests verify:
 *  1. synthesis_guidance: null parses cleanly (original A-S5 bug, pattern A).
 *  2. synthesis_guidance absent entirely parses cleanly.
 *  3. All string soft-optional fields null simultaneously parses cleanly.
 *  4. Enum/boolean/array/object soft-optional fields: null → undefined (pattern B).
 *  5. HARD-REQUIRED fields (query_class, query_intent_summary) with null STILL FAIL.
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

// ── Pattern B: enum/boolean/array/object soft-optional fields ────────────────
// These fields use .optional().catch(undefined) and must accept null without
// surfacing a 422. All fields listed here are [PLANNER OUTPUT] fields that
// Anthropic (and other providers) may return as null instead of omitting.

describe('PipelinePlanSchema — null coercion for enum/boolean/array/object soft-optional fields (pattern B)', () => {

  it('expected_output_shape: null parses cleanly → undefined', () => {
    const r = PipelinePlanSchema.safeParse({ ...BASE_PLAN, expected_output_shape: null })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.expected_output_shape).toBeUndefined()
  })

  it('panel_mode: null parses cleanly → undefined', () => {
    const r = PipelinePlanSchema.safeParse({ ...BASE_PLAN, panel_mode: null })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.panel_mode).toBeUndefined()
  })

  it('forward_looking: null parses cleanly → undefined', () => {
    const r = PipelinePlanSchema.safeParse({ ...BASE_PLAN, forward_looking: null })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.forward_looking).toBeUndefined()
  })

  it('dasha_context_required: null parses cleanly → undefined', () => {
    const r = PipelinePlanSchema.safeParse({ ...BASE_PLAN, dasha_context_required: null })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.dasha_context_required).toBeUndefined()
  })

  it('planets: null parses cleanly → undefined', () => {
    const r = PipelinePlanSchema.safeParse({ ...BASE_PLAN, planets: null })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.planets).toBeUndefined()
  })

  it('houses: null parses cleanly → undefined', () => {
    const r = PipelinePlanSchema.safeParse({ ...BASE_PLAN, houses: null })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.houses).toBeUndefined()
  })

  it('domains: null parses cleanly → undefined', () => {
    const r = PipelinePlanSchema.safeParse({ ...BASE_PLAN, domains: null })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.domains).toBeUndefined()
  })

  it('graph_seed_hints: null parses cleanly → undefined', () => {
    const r = PipelinePlanSchema.safeParse({ ...BASE_PLAN, graph_seed_hints: null })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.graph_seed_hints).toBeUndefined()
  })

  it('edge_type_filter: null parses cleanly → undefined', () => {
    const r = PipelinePlanSchema.safeParse({ ...BASE_PLAN, edge_type_filter: null })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.edge_type_filter).toBeUndefined()
  })

  it('vector_search_filter: null parses cleanly → undefined', () => {
    const r = PipelinePlanSchema.safeParse({ ...BASE_PLAN, vector_search_filter: null })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.vector_search_filter).toBeUndefined()
  })

  it('time_window: null parses cleanly → undefined', () => {
    const r = PipelinePlanSchema.safeParse({ ...BASE_PLAN, time_window: null })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.time_window).toBeUndefined()
  })

  it('prior_turn_relevance: null parses cleanly → undefined', () => {
    const r = PipelinePlanSchema.safeParse({ ...BASE_PLAN, prior_turn_relevance: null })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.prior_turn_relevance).toBeUndefined()
  })

  it('worst-case: ALL soft-optional fields null simultaneously — no 422', () => {
    const r = PipelinePlanSchema.safeParse({
      ...BASE_PLAN,
      synthesis_guidance: null,
      planning_rationale: null,
      expected_output_shape: null,
      panel_mode: null,
      forward_looking: null,
      dasha_context_required: null,
      planets: null,
      houses: null,
      domains: null,
      graph_seed_hints: null,
      edge_type_filter: null,
      vector_search_filter: null,
      time_window: null,
      prior_turn_relevance: null,
    })
    expect(r.success).toBe(true)
    if (r.success) {
      // Every soft-optional must be undefined (not null, not throw)
      expect(r.data.synthesis_guidance).toBeUndefined()
      expect(r.data.planning_rationale).toBeUndefined()
      expect(r.data.expected_output_shape).toBeUndefined()
      expect(r.data.panel_mode).toBeUndefined()
      expect(r.data.forward_looking).toBeUndefined()
      expect(r.data.dasha_context_required).toBeUndefined()
      expect(r.data.planets).toBeUndefined()
      expect(r.data.houses).toBeUndefined()
      expect(r.data.domains).toBeUndefined()
      expect(r.data.graph_seed_hints).toBeUndefined()
      expect(r.data.edge_type_filter).toBeUndefined()
      expect(r.data.vector_search_filter).toBeUndefined()
      expect(r.data.time_window).toBeUndefined()
      expect(r.data.prior_turn_relevance).toBeUndefined()
    }
  })

  it('valid values still work after .catch() is added', () => {
    const r = PipelinePlanSchema.safeParse({
      ...BASE_PLAN,
      expected_output_shape: 'time_indexed_prediction',
      panel_mode: false,
      forward_looking: true,
      dasha_context_required: true,
      planets: ['Saturn'],
      houses: [1, 7],
      domains: ['career'],
    })
    expect(r.success).toBe(true)
    if (r.success) {
      expect(r.data.expected_output_shape).toBe('time_indexed_prediction')
      expect(r.data.panel_mode).toBe(false)
      expect(r.data.forward_looking).toBe(true)
      expect(r.data.planets).toEqual(['Saturn'])
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

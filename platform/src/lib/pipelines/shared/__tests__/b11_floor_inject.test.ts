/**
 * Tests for the shared B.11 floor injection helper.
 *
 * Mirrors the inline behaviour of consult/route.ts lines 472–516 — exact
 * tool list + parameter shapes are part of AC.3 golden-transcript parity.
 */

import { describe, it, expect } from 'vitest'
import { injectB11Floor } from '../b11_floor_inject'
import type { PipelinePlan } from '@/lib/pipeline/types'

function basePlan(overrides: Partial<PipelinePlan> = {}): PipelinePlan {
  return {
    query_class: 'factual',
    query_intent_summary: 'test',
    asset_bundle: [],
    tool_calls: [],
    ...overrides,
  } as PipelinePlan
}

describe('injectB11Floor', () => {
  it('non-predictive plan without an L2.5 tool gets msr_sql + cgm_graph_walk injected', () => {
    const plan = basePlan({ query_class: 'factual', tool_calls: [] })
    const r = injectB11Floor(plan)

    expect(r.injected).toBe(true)
    const names = plan.tool_calls.map(t => t.tool_name).sort()
    expect(names).toEqual(['cgm_graph_walk', 'msr_sql'])
    expect(r.toolsAuthorized).toContain('msr_sql')
    expect(r.toolsAuthorized).toContain('cgm_graph_walk')
  })

  it('predictive plan injects msr_sql + vector_search + pattern_register (no cgm_graph_walk)', () => {
    const plan = basePlan({
      query_class: 'predictive',
      tool_calls: [],
      domains: ['career'],
    })
    const r = injectB11Floor(plan)

    expect(r.injected).toBe(true)
    const names = plan.tool_calls.map(t => t.tool_name)
    expect(names).toContain('msr_sql')
    expect(names).toContain('pattern_register')
    expect(names).toContain('vector_search')
    // cgm_graph_walk MUST NOT be injected for predictive class (R14c)
    expect(names).not.toContain('cgm_graph_walk')
  })

  it('predictive vector_search uses domain-joined query when domains given', () => {
    const plan = basePlan({
      query_class: 'predictive',
      tool_calls: [],
      domains: ['career', 'marriage'],
    })
    injectB11Floor(plan)
    const vs = plan.tool_calls.find(t => t.tool_name === 'vector_search')
    expect(vs).toBeDefined()
    expect(vs?.params).toMatchObject({ query_text: 'career marriage' })
  })

  it('predictive vector_search falls back to defaults when domains empty', () => {
    const plan = basePlan({ query_class: 'predictive', tool_calls: [] })
    injectB11Floor(plan)
    const vs = plan.tool_calls.find(t => t.tool_name === 'vector_search')
    expect(vs?.params).toMatchObject({
      query_text: 'relationships family marriage children',
    })
  })

  it('does NOT inject when an L2.5 tool is already present', () => {
    const plan = basePlan({
      tool_calls: [
        { tool_name: 'pattern_register', params: {}, token_budget: 200, priority: 1 as const, reason: 'planner' },
      ],
    })
    const r = injectB11Floor(plan)
    expect(r.injected).toBe(false)
    expect(plan.tool_calls).toHaveLength(1)
  })

  it('dasha context floor: predictive class gets chart_facts_query injected', () => {
    const plan = basePlan({ query_class: 'predictive', tool_calls: [] })
    const r = injectB11Floor(plan)
    expect(r.dashaInjected).toBe(true)
    const cf = plan.tool_calls.find(t => t.tool_name === 'chart_facts_query')
    expect(cf).toBeDefined()
    expect(cf?.params).toMatchObject({ category: 'dasha_vimshottari', limit: 50 })
  })

  it('dasha context floor: holistic class also gets chart_facts_query injected', () => {
    const plan = basePlan({ query_class: 'holistic', tool_calls: [] })
    const r = injectB11Floor(plan)
    expect(r.dashaInjected).toBe(true)
  })

  it('dasha context floor: factual class does NOT trigger chart_facts_query injection', () => {
    const plan = basePlan({ query_class: 'factual', tool_calls: [] })
    const r = injectB11Floor(plan)
    expect(r.dashaInjected).toBe(false)
  })

  it('dasha context floor: skipped when chart_facts_query already present', () => {
    const plan = basePlan({
      query_class: 'predictive',
      tool_calls: [
        { tool_name: 'chart_facts_query', params: { category: 'planet' }, token_budget: 200, priority: 1 as const, reason: 'planner' },
        { tool_name: 'msr_sql', params: {}, token_budget: 200, priority: 1 as const, reason: 'planner' },
      ],
    })
    const r = injectB11Floor(plan)
    expect(r.dashaInjected).toBe(false)
    // Plan should keep just the one chart_facts_query the planner emitted
    const cfCount = plan.tool_calls.filter(t => t.tool_name === 'chart_facts_query').length
    expect(cfCount).toBe(1)
  })

  it('toolsAuthorized de-duplicates names', () => {
    const plan = basePlan({
      tool_calls: [
        { tool_name: 'msr_sql', params: {}, token_budget: 200, priority: 1 as const, reason: 'a' },
        { tool_name: 'msr_sql', params: { x: 1 }, token_budget: 200, priority: 1 as const, reason: 'b' },
      ],
    })
    const r = injectB11Floor(plan)
    const unique = Array.from(new Set(r.toolsAuthorized))
    expect(r.toolsAuthorized.length).toBe(unique.length)
  })
})

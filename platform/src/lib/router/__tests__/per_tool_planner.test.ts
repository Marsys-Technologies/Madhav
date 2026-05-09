/**
 * per_tool_planner.test.ts — Wave 6 M2-D2
 * Tests the per-tool planner in isolation, mocking Haiku calls.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/models/resolver', () => ({
  resolveModel: vi.fn(() => ({ id: 'claude-haiku-4-5' })),
}))

const mockGenerateText = vi.fn()
vi.mock('ai', () => ({
  generateText: (...args: unknown[]) => mockGenerateText(...args),
}))

import { planPerTool, TOOL_PROMPT_TEMPLATES } from '../per_tool_planner'
import type { QueryPlan } from '@/lib/router/types'

const BASE_PLAN: QueryPlan = {
  query_plan_id: 'test-plan-001',
  query_text: 'What are the career signals for Mercury dasha?',
  query_class: 'interpretive',
  domains: ['career', 'dharma'],
  forward_looking: false,
  audience_tier: 'client',
  tools_authorized: ['msr_sql', 'pattern_register', 'temporal'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'test-fingerprint',
  schema_version: '1.0',
  planets: ['Mercury', 'Saturn'],
  houses: [1, 10],
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('planPerTool', () => {
  it('1. returns empty overrides for empty tools_authorized list', async () => {
    const result = await planPerTool(BASE_PLAN, [])
    expect(result.overrides.size).toBe(0)
    expect(result.tool_count).toBe(0)
    expect(result.planner_active).toBe(true)
    expect(result.latency_ms).toBeGreaterThanOrEqual(0)
  })

  it('2. returns an override for msr_sql when Haiku returns valid JSON', async () => {
    mockGenerateText.mockResolvedValue({
      text: '{"planets":["Saturn"],"houses":[7]}',
      usage: { promptTokens: 120, completionTokens: 15 },
    })
    const result = await planPerTool(BASE_PLAN, ['msr_sql'])
    expect(result.overrides.has('msr_sql')).toBe(true)
    expect(result.overrides.get('msr_sql')?.planets).toEqual(['Saturn'])
    expect(result.overrides.get('msr_sql')?.houses).toEqual([7])
  })

  it('3. skips override when Haiku returns {}', async () => {
    mockGenerateText.mockResolvedValue({
      text: '{}',
      usage: { promptTokens: 100, completionTokens: 3 },
    })
    const result = await planPerTool(BASE_PLAN, ['msr_sql'])
    expect(result.overrides.has('msr_sql')).toBe(false)
  })

  it('4. handles malformed JSON gracefully without throwing', async () => {
    mockGenerateText.mockResolvedValue({
      text: 'not json at all',
      usage: { promptTokens: 80, completionTokens: 5 },
    })
    await expect(planPerTool(BASE_PLAN, ['msr_sql'])).resolves.not.toThrow()
    const result = await planPerTool(BASE_PLAN, ['msr_sql'])
    expect(result.overrides.has('msr_sql')).toBe(false)
  })

  it('5. handles Haiku call rejection gracefully without throwing', async () => {
    mockGenerateText.mockRejectedValue(new Error('Network error'))
    const result = await planPerTool(BASE_PLAN, ['msr_sql'])
    expect(result.overrides.has('msr_sql')).toBe(false)
    expect(result.planner_active).toBe(true)
  })

  it('6. skips unknown tool name without throwing', async () => {
    mockGenerateText.mockResolvedValue({
      text: '{"limit":5}',
      usage: { promptTokens: 80, completionTokens: 8 },
    })
    const result = await planPerTool(BASE_PLAN, ['nonexistent_tool'])
    expect(result.overrides.size).toBe(0)
  })

  it('7. processes multiple tools in parallel and returns all overrides', async () => {
    mockGenerateText
      .mockResolvedValueOnce({
        text: '{"planets":["Mercury"]}',
        usage: { promptTokens: 110, completionTokens: 12 },
      })
      .mockResolvedValueOnce({
        text: '{"keyword":"career"}',
        usage: { promptTokens: 95, completionTokens: 10 },
      })
      .mockResolvedValueOnce({
        text: '{"dasha_context_required":true}',
        usage: { promptTokens: 100, completionTokens: 11 },
      })
    const result = await planPerTool(BASE_PLAN, ['msr_sql', 'pattern_register', 'temporal'])
    expect(result.overrides.size).toBe(3)
    expect(result.overrides.has('msr_sql')).toBe(true)
    expect(result.overrides.has('pattern_register')).toBe(true)
    expect(result.overrides.has('temporal')).toBe(true)
  })

  it('8. planner_active is true when tools are processed', async () => {
    mockGenerateText.mockResolvedValue({
      text: '{"limit":10}',
      usage: { promptTokens: 90, completionTokens: 8 },
    })
    const result = await planPerTool(BASE_PLAN, ['msr_sql'])
    expect(result.planner_active).toBe(true)
  })

  it('9. latency_ms is a non-negative number', async () => {
    mockGenerateText.mockResolvedValue({
      text: '{}',
      usage: { promptTokens: 80, completionTokens: 3 },
    })
    const result = await planPerTool(BASE_PLAN, ['msr_sql'])
    expect(result.latency_ms).toBeGreaterThanOrEqual(0)
    expect(typeof result.latency_ms).toBe('number')
  })

  it('10. temporal template output contains KETU note', () => {
    const templateFn = TOOL_PROMPT_TEMPLATES['temporal']
    expect(templateFn).toBeDefined()
    const output = templateFn(BASE_PLAN)
    expect(output).toContain('KETU')
  })

  it('11. timeline_query template output contains Ketu MD and 2027-08-21', () => {
    const templateFn = TOOL_PROMPT_TEMPLATES['timeline_query']
    expect(templateFn).toBeDefined()
    const output = templateFn(BASE_PLAN)
    expect(output).toMatch(/Ketu MD|KETU MD/)
    expect(output).toContain('2027-08-21')
  })

  it('12. override merge preserves original queryPlan immutability', async () => {
    mockGenerateText.mockResolvedValue({
      text: '{"planets":["Jupiter"],"houses":[5]}',
      usage: { promptTokens: 100, completionTokens: 12 },
    })
    const originalPlanets = [...(BASE_PLAN.planets ?? [])]
    const result = await planPerTool(BASE_PLAN, ['msr_sql'])
    const override = result.overrides.get('msr_sql')
    // Simulate the merge pattern used in route.ts
    const effectivePlan = override ? { ...BASE_PLAN, ...override } : BASE_PLAN
    // effectivePlan has new planets
    expect(effectivePlan.planets).toEqual(['Jupiter'])
    // BASE_PLAN.planets is unchanged
    expect(BASE_PLAN.planets).toEqual(originalPlanets)
  })

  it('13. all 18 tool templates are defined', () => {
    const expectedTools = [
      'msr_sql', 'pattern_register', 'resonance_register', 'cluster_atlas',
      'contradiction_register', 'temporal', 'query_msr_aggregate', 'cgm_graph_walk',
      'manifest_query', 'vector_search', 'kp_query', 'saham_query',
      'divisional_query', 'cross_varga_dignity_query',
      'chart_facts_query', 'domain_report_query',
      'remedial_codex_query', 'timeline_query',
    ]
    for (const tool of expectedTools) {
      expect(TOOL_PROMPT_TEMPLATES[tool], `missing template for ${tool}`).toBeDefined()
    }
    expect(Object.keys(TOOL_PROMPT_TEMPLATES)).toHaveLength(18)
  })

  it('14. tool_count reflects the number of tools passed in', async () => {
    mockGenerateText.mockResolvedValue({
      text: '{}',
      usage: { promptTokens: 80, completionTokens: 3 },
    })
    const result = await planPerTool(BASE_PLAN, ['msr_sql', 'temporal'])
    expect(result.tool_count).toBe(2)
  })

  it('15. skips override when Haiku returns whitespace-only string', async () => {
    mockGenerateText.mockResolvedValue({
      text: '   ',
      usage: { promptTokens: 80, completionTokens: 2 },
    })
    await expect(planPerTool(BASE_PLAN, ['msr_sql'])).resolves.not.toThrow()
    const result = await planPerTool(BASE_PLAN, ['msr_sql'])
    expect(result.overrides.has('msr_sql')).toBe(false)
  })
})

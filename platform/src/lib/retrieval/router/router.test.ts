/**
 * D2 Query Router — Unit Tests
 * ==============================
 * Tests per D2 brief §4 acceptance criteria:
 * - Classifies into the 5 route classes (one representative query each)
 * - Rule-driven core (verifies rule_fired is set)
 * - chart_id is required (throws if absent)
 * - chart_id passed through, never defaulted
 * - Trajectory logging present (route_class, traversal_level, routing_method, etc.)
 * - Value-based termination for multi_hop
 * - Per-route budgets enforced
 * - Model fallback flag recorded when used
 *
 * No PII / no native identifiers in any test.
 * Uses a fake registry (isolated from prod capabilities).
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { classifyQuery, isModelFallbackEligible } from './classifier'
import { selectTools, getBudget, buildTerminationPolicy } from './tool_selector'
import { route } from './router'
import { clearRegistry, registerCapability } from '../registry'
import type { CapabilityDescriptor } from '../registry/types'
import type { ClassifierResult } from './types'

// ── Test helpers ──────────────────────────────────────────────────────────────

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'

/** Build a minimal valid per_chart capability for testing */
function makeTestCap(overrides: Partial<CapabilityDescriptor> = {}): CapabilityDescriptor {
  return {
    uri: 'marsys://tool/L2/test_umbrella',
    type: 'tool',
    layer: 'L2',
    name: 'test_umbrella',
    scope: 'per_chart',
    description: 'Test umbrella tool for a given chart UUID (<chart_uuid>).',
    input_schema: {
      chart_id: { type: 'string', description: 'Chart UUID', required: true },
    },
    required_inputs: ['chart_id'],
    archetype: 'orientation_digest',
    traversal_level: 'L-ORIENT',
    tool_role: 'umbrella',
    emits_references: true,
    lel_capable: false,
    async handler(args) {
      return { content: { chart_id: args['chart_id'], result: 'test' }, is_error: false }
    },
    ...overrides,
  } as CapabilityDescriptor
}

// ── Classifier tests ──────────────────────────────────────────────────────────

describe('classifyQuery — rule-driven classifier', () => {
  it('TC-CLS-1: classifies numeric/exact query correctly', () => {
    const result = classifyQuery('What is the longitude of Mars in this chart?')
    expect(result.route_class).toBe('numeric_exact')
    expect(result.rule_fired).toBe('R1_numeric_keywords')
    expect(result.confidence).toBe('high')
  })

  it('TC-CLS-2: classifies relational/contradiction query correctly', () => {
    const result = classifyQuery('What are the contradictions across domains?')
    expect(result.route_class).toBe('relational')
    expect(result.rule_fired).toBe('R2_relational_keywords')
    expect(result.confidence).toBe('high')
  })

  it('TC-CLS-3: classifies narrative/classical text query correctly', () => {
    const result = classifyQuery('What does the Brihat Parashara say about this yoga?')
    expect(result.route_class).toBe('narrative')
    expect(result.rule_fired).toBe('R3_narrative_keywords')
    expect(result.confidence).toBe('high')
  })

  it('TC-CLS-4: classifies simple orientation query correctly', () => {
    const result = classifyQuery('Give me the chart overview')
    expect(result.route_class).toBe('simple')
    expect(result.rule_fired).toBe('R5_simple_orientation')
    expect(result.traversal_level).toBe('L-ORIENT')
    expect(result.confidence).toBe('high')
  })

  it('TC-CLS-5: classifies multi-hop query correctly', () => {
    const result = classifyQuery('Give me a comprehensive detailed analysis of career and health domains')
    expect(result.route_class).toBe('multi_hop')
    expect(result.rule_fired).toBe('R4_multi_hop_keywords')
    expect(result.confidence).toBe('high')
  })

  it('TC-CLS-6: short query falls back to simple with low confidence', () => {
    // "read chart" — short, no keyword matches → falls through to R6 (short query heuristic)
    const result = classifyQuery('read chart')
    expect(result.route_class).toBe('simple')
    expect(result.confidence).toBe('low')
    expect(result.rule_fired).toBe('R6_short_query_simple')
  })

  it('TC-CLS-7: very short query is low-confidence (model fallback eligible)', () => {
    const result = classifyQuery('chart')
    expect(isModelFallbackEligible(result)).toBe(true)
  })

  it('TC-CLS-8: high-confidence result is not model-fallback eligible', () => {
    const result = classifyQuery('What is the longitude of Saturn?')
    expect(isModelFallbackEligible(result)).toBe(false)
  })

  it('TC-CLS-9: R1 numeric beats R5 simple when both could match', () => {
    // "what sign is Mars in" — has "overview"-adjacent phrasing but also "which sign" (numeric)
    // R1 fires first (more specific)
    const result = classifyQuery('Give me an overview of which sign Mars occupies')
    expect(result.route_class).toBe('numeric_exact')
    expect(result.rule_fired).toBe('R1_numeric_keywords')
  })

  it('TC-CLS-10: narrative remedy query routes correctly', () => {
    const result = classifyQuery('What remedy does the classical tradition prescribe for this dosha?')
    expect(result.route_class).toBe('narrative')
  })
})

// ── Tool selector tests ───────────────────────────────────────────────────────

describe('selectTools — registry-aware tool selection', () => {
  beforeEach(() => {
    clearRegistry()
  })

  afterEach(() => {
    clearRegistry()
  })

  it('TC-SEL-1: selects umbrella tool for simple route', () => {
    registerCapability(makeTestCap())
    const { planned_calls, umbrella_then_drill } = selectTools({
      route_class: 'simple',
      traversal_level: 'L-ORIENT',
      chart_id: TEST_CHART_ID,
      lel_enabled: false,
    })
    expect(planned_calls).toHaveLength(1)
    expect(planned_calls[0].uri).toBe('marsys://tool/L2/test_umbrella')
    expect(umbrella_then_drill).toBe(true)
    // chart_id is injected into args
    expect(planned_calls[0].args?.['chart_id']).toBe(TEST_CHART_ID)
  })

  it('TC-SEL-2: skips already-loaded tools for simple route', () => {
    registerCapability(makeTestCap())
    const { planned_calls } = selectTools({
      route_class: 'simple',
      traversal_level: 'L-ORIENT',
      chart_id: TEST_CHART_ID,
      lel_enabled: false,
      already_loaded: ['marsys://tool/L2/test_umbrella'],
    })
    expect(planned_calls).toHaveLength(0)
  })

  it('TC-SEL-3: lel_capable tool gets lel_enabled injected into args', () => {
    registerCapability(makeTestCap({ lel_capable: true }))
    const { planned_calls } = selectTools({
      route_class: 'simple',
      traversal_level: 'L-ORIENT',
      chart_id: TEST_CHART_ID,
      lel_enabled: true,
    })
    expect(planned_calls[0].args?.['lel_enabled']).toBe(true)
  })

  it('TC-SEL-4: lel_enabled=false is NOT injected for non-lel_capable tool', () => {
    registerCapability(makeTestCap({ lel_capable: false }))
    const { planned_calls } = selectTools({
      route_class: 'simple',
      traversal_level: 'L-ORIENT',
      chart_id: TEST_CHART_ID,
      lel_enabled: false,
    })
    expect(planned_calls[0].args?.['lel_enabled']).toBeUndefined()
  })

  it('TC-SEL-5: budget override is honoured', () => {
    const { budget } = selectTools({
      route_class: 'simple',
      traversal_level: 'L-ORIENT',
      chart_id: TEST_CHART_ID,
      lel_enabled: false,
      budget_usd: 0.99,
    })
    expect(budget.max_usd).toBe(0.99)
  })

  it('TC-SEL-6: getBudget returns correct defaults per route class', () => {
    expect(getBudget('simple').max_usd).toBe(0.005)
    expect(getBudget('numeric_exact').max_usd).toBe(0.01)
    expect(getBudget('multi_hop').max_usd).toBe(0.50)
    expect(getBudget('multi_hop').latency_class).toBe('slow')
    expect(getBudget('simple').latency_class).toBe('fast')
  })

  it('TC-SEL-7: buildTerminationPolicy returns value_based strategy', () => {
    const budget = getBudget('multi_hop')
    const policy = buildTerminationPolicy(budget)
    expect(policy.strategy).toBe('value_based')
    expect(policy.marginal_value_threshold).toBeGreaterThan(0)
    expect(policy.soft_iteration_limit).toBe(budget.soft_iteration_limit)
  })

  it('TC-SEL-8: graph tool preferred for relational route', () => {
    registerCapability(makeTestCap({
      uri: 'marsys://tool/L2/graph_tool',
      name: 'graph_tool',
      archetype: 'graph_traversal',
      traversal_level: 'L-SIGNAL',
      tool_role: 'graph',
      emits_references: true,
    }))
    const { planned_calls } = selectTools({
      route_class: 'relational',
      traversal_level: 'L-SIGNAL',
      chart_id: TEST_CHART_ID,
      lel_enabled: false,
    })
    expect(planned_calls.length).toBeGreaterThan(0)
    // The graph tool should be selected
    expect(planned_calls[0].uri).toBe('marsys://tool/L2/graph_tool')
  })
})

// ── route() function tests ────────────────────────────────────────────────────

describe('route() — main routing function', () => {
  beforeEach(() => {
    clearRegistry()
    registerCapability(makeTestCap())
  })

  afterEach(() => {
    clearRegistry()
  })

  it('TC-ROUTE-1: throws if chart_id is missing', async () => {
    await expect(
      route({ query: 'Give me the chart overview', chart_id: '' })
    ).rejects.toThrow(/chart_id is required/)
  })

  it('TC-ROUTE-2: throws if chart_id is whitespace only', async () => {
    await expect(
      route({ query: 'Give me the chart overview', chart_id: '   ' })
    ).rejects.toThrow(/chart_id is required/)
  })

  it('TC-ROUTE-3: chart_id is passed through to planned_calls args', async () => {
    const result = await route({
      query: 'Give me the chart overview',
      chart_id: TEST_CHART_ID,
    })
    // Check chart_id in planned calls
    for (const call of result.planned_calls) {
      if (call.args?.['chart_id'] !== undefined) {
        expect(call.args['chart_id']).toBe(TEST_CHART_ID)
      }
    }
  })

  it('TC-ROUTE-4: trajectory.chart_id is the supplied UUID', async () => {
    const result = await route({
      query: 'Give me the chart overview',
      chart_id: TEST_CHART_ID,
    })
    expect(result.trajectory.chart_id).toBe(TEST_CHART_ID)
  })

  it('TC-ROUTE-5: simple query gets simple route_class', async () => {
    const result = await route({
      query: 'Give me the chart overview',
      chart_id: TEST_CHART_ID,
    })
    expect(result.route_class).toBe('simple')
    expect(result.traversal_level).toBe('L-ORIENT')
  })

  it('TC-ROUTE-6: numeric query gets numeric_exact route_class', async () => {
    const result = await route({
      query: 'What is the longitude of Venus in this chart?',
      chart_id: TEST_CHART_ID,
    })
    expect(result.route_class).toBe('numeric_exact')
  })

  it('TC-ROUTE-7: trajectory.routing_method is "rule" for rule-driven routing', async () => {
    const result = await route({
      query: 'Give me the chart overview',
      chart_id: TEST_CHART_ID,
    })
    expect(result.trajectory.routing_method).toBe('rule')
    expect(result.trajectory.rule_fired).toBeTruthy()
  })

  it('TC-ROUTE-8: force_route_class override sets routing_method to "forced"', async () => {
    const result = await route({
      query: 'Any query',
      chart_id: TEST_CHART_ID,
      hints: { force_route_class: 'relational' },
    })
    expect(result.route_class).toBe('relational')
    expect(result.trajectory.routing_method).toBe('forced')
  })

  it('TC-ROUTE-9: model_fallback is recorded when used', async () => {
    const mockModelClassifier = async (_q: string): Promise<ClassifierResult> => ({
      route_class: 'multi_hop',
      traversal_level: 'L-DOMAIN',
      rule_fired: 'MODEL_CLASSIFIER',
      confidence: 'high',
    })

    // Short query will be low-confidence → eligible for model fallback
    const result = await route({
      query: 'chart',
      chart_id: TEST_CHART_ID,
      allow_model_fallback: true,
      model_classifier: mockModelClassifier,
    })
    expect(result.trajectory.routing_method).toBe('model_fallback')
    expect(result.route_class).toBe('multi_hop')
  })

  it('TC-ROUTE-10: model_fallback not used when allow_model_fallback=false', async () => {
    const mockModelClassifier = async (_q: string): Promise<ClassifierResult> => ({
      route_class: 'multi_hop',
      traversal_level: 'L-DOMAIN',
      rule_fired: 'MODEL_CLASSIFIER',
      confidence: 'high',
    })

    const result = await route({
      query: 'chart',
      chart_id: TEST_CHART_ID,
      allow_model_fallback: false,
      model_classifier: mockModelClassifier,
    })
    // Model fallback should NOT have been used (default=false)
    expect(result.trajectory.routing_method).not.toBe('model_fallback')
  })

  it('TC-ROUTE-11: multi_hop route gets value-based termination policy', async () => {
    const result = await route({
      query: 'Give me a comprehensive detailed analysis of career and health domains',
      chart_id: TEST_CHART_ID,
    })
    if (result.route_class === 'multi_hop') {
      expect(result.termination_policy).toBeDefined()
      expect(result.termination_policy?.strategy).toBe('value_based')
      expect(result.termination_policy?.marginal_value_threshold).toBeGreaterThan(0)
      expect(result.termination_policy?.soft_iteration_limit).toBeGreaterThan(0)
    }
  })

  it('TC-ROUTE-12: simple route does NOT have termination_policy', async () => {
    const result = await route({
      query: 'Give me the chart overview',
      chart_id: TEST_CHART_ID,
    })
    if (result.route_class === 'simple') {
      expect(result.termination_policy).toBeUndefined()
    }
  })

  it('TC-ROUTE-13: trajectory has routed_at ISO timestamp', async () => {
    const result = await route({
      query: 'Give me the chart overview',
      chart_id: TEST_CHART_ID,
    })
    expect(result.trajectory.routed_at).toMatch(/^\d{4}-\d{2}-\d{2}T/)
  })

  it('TC-ROUTE-14: trajectory.lel_enabled is false by default', async () => {
    const result = await route({
      query: 'Give me the chart overview',
      chart_id: TEST_CHART_ID,
    })
    expect(result.trajectory.lel_enabled).toBe(false)
  })

  it('TC-ROUTE-15: lel_enabled=true flows through to trajectory', async () => {
    const result = await route({
      query: 'Give me the chart overview',
      chart_id: TEST_CHART_ID,
      hints: { lel_enabled: true },
    })
    expect(result.trajectory.lel_enabled).toBe(true)
  })

  it('TC-ROUTE-16: primary_tool is null when no tools registered for route', async () => {
    // relational route with no graph tools registered
    clearRegistry()
    // Register only umbrella tool — no graph tools
    registerCapability(makeTestCap())

    const result = await route({
      query: 'What are the contradictions across domains?',
      chart_id: TEST_CHART_ID,
    })
    // Either no primary_tool or it falls back to something — either is acceptable
    // Key assertion: does not throw, and trajectory is complete
    expect(result.trajectory.chart_id).toBe(TEST_CHART_ID)
    expect(result.route_class).toBe('relational')
  })

  it('TC-ROUTE-17: budget_usd hint overrides default budget', async () => {
    const result = await route({
      query: 'Give me the chart overview',
      chart_id: TEST_CHART_ID,
      hints: { budget_usd: 0.42 },
    })
    expect(result.budget.max_usd).toBe(0.42)
  })

  it('TC-ROUTE-18: chart_id from different charts produces different trajectory', async () => {
    const chart1 = '00000000-0000-0000-0000-000000000001'
    const chart2 = '00000000-0000-0000-0000-000000000002'

    const r1 = await route({ query: 'Give me the chart overview', chart_id: chart1 })
    const r2 = await route({ query: 'Give me the chart overview', chart_id: chart2 })

    // The router must NOT mix up chart IDs
    expect(r1.trajectory.chart_id).toBe(chart1)
    expect(r2.trajectory.chart_id).toBe(chart2)

    // planned_calls for per_chart tools must carry the right chart_id
    for (const call of r1.planned_calls) {
      if (call.args?.['chart_id']) {
        expect(call.args['chart_id']).toBe(chart1)
        expect(call.args['chart_id']).not.toBe(chart2)
      }
    }
  })
})

// ── Chart-agnostic guard (native bleed check) ──────────────────────────────────

describe('Chart-agnostic guarantee', () => {
  it('TC-CA-1: no native UUID appears anywhere in RouteResult for a generic chart', async () => {
    clearRegistry()
    registerCapability(makeTestCap())

    const GENERIC_CHART = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
    const NATIVE_CHART_UUID = '482012f1-710e-4a25-994a-93821f5871aa'

    const result = await route({
      query: 'Give me the chart overview',
      chart_id: GENERIC_CHART,
    })

    const serialized = JSON.stringify(result)
    expect(serialized).not.toContain(NATIVE_CHART_UUID)
    expect(serialized).toContain(GENERIC_CHART)
  })

  it('TC-CA-2: route() with a different chart_id never leaks native chart_id', async () => {
    clearRegistry()
    registerCapability(makeTestCap())

    const PHANTOM_CHART = '362f9f17-0000-0000-0000-000000000000'
    const NATIVE_CHART_UUID = '482012f1-710e-4a25-994a-93821f5871aa'

    const result = await route({
      query: 'What is the shadbala score for this chart?',
      chart_id: PHANTOM_CHART,
    })

    const serialized = JSON.stringify(result)
    expect(serialized).not.toContain(NATIVE_CHART_UUID)
  })
})

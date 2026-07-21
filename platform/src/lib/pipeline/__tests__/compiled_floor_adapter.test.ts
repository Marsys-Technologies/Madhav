import { describe, expect, it } from 'vitest'
// Bootstrap the full L0–L5 registry (side-effect import) so getToolByName() reflects
// the real, fully-populated registry — the same import consult/route.ts's path makes.
import '@/lib/retrieval/registry/catalog'
import {
  classifierIntentToCompilerIntent,
  classifierTupleToCompilerTuple,
  compileFloorForPlan,
  ensureB11WholeChartReadFloor,
  ensureDashaContextFloor,
  resolveLiveTool,
  LIVE_TOOL_TO_RETRIEVAL,
  L2_5_TOOLS,
} from '@/lib/pipeline/compiled_floor_adapter'
import type { ScopeTuple as ClassifierScopeTuple } from '@/lib/vidhi/scope_classifier'
import type { PipelinePlan, QueryClass } from '@/lib/pipeline/types'
import { getToolByName } from '@/lib/retrieval/registry/tool_name_bridge'
import { VIDHI_PRIMITIVES } from '@/lib/vidhi/registry_data'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function tuple(overrides: Partial<ClassifierScopeTuple> = {}): ClassifierScopeTuple {
  return {
    intent: 'domain_assessment',
    domains: ['career'],
    width: 'standard',
    depth: 'deep',
    horizon: 'present',
    intervention: 'none',
    entitlement: 'native',
    ...overrides,
  }
}

/** Minimal PipelinePlan stub — only the fields the floor guarantees touch. */
function plan(queryClass: QueryClass, toolNames: string[] = [], domains: string[] = []): PipelinePlan {
  return {
    query_class: queryClass,
    domains,
    tool_calls: toolNames.map((tool_name) => ({
      tool_name,
      params: {},
      token_budget: 500,
      priority: 1 as const,
      reason: 'seed',
    })),
  } as unknown as PipelinePlan
}

describe('classifier→compiler intent mapping', () => {
  it('career-shaped tuple → career_deepdive', () => {
    expect(classifierIntentToCompilerIntent(tuple({ domains: ['career'] }))).toBe('career_deepdive')
  })
  it('each domain-specific tuple → its deepdive floor', () => {
    expect(classifierIntentToCompilerIntent(tuple({ domains: ['wealth'] }))).toBe('wealth_deepdive')
    expect(classifierIntentToCompilerIntent(tuple({ domains: ['health'] }))).toBe('health_deepdive')
    expect(classifierIntentToCompilerIntent(tuple({ domains: ['marriage'] }))).toBe('marriage_deepdive')
  })
  it('broad width OR ≥3 domains → panoramic_breadth (breadth wins over domain)', () => {
    expect(classifierIntentToCompilerIntent(tuple({ width: 'broad', domains: ['career'] }))).toBe('panoramic_breadth')
    expect(
      classifierIntentToCompilerIntent(tuple({ domains: ['career', 'wealth', 'health'] })),
    ).toBe('panoramic_breadth')
  })
  it('chart_overview intent → structure_read', () => {
    expect(classifierIntentToCompilerIntent(tuple({ intent: 'chart_overview', domains: ['general'] }))).toBe(
      'structure_read',
    )
  })
  it('shallow non-domain tuple → retrieval_only', () => {
    expect(
      classifierIntentToCompilerIntent(tuple({ intent: 'planet_strength', domains: ['general'], depth: 'shallow' })),
    ).toBe('retrieval_only')
  })
  it('everything else → general_synthesis', () => {
    expect(
      classifierIntentToCompilerIntent(tuple({ intent: 'planet_strength', domains: ['general'], depth: 'standard' })),
    ).toBe('general_synthesis')
  })
})

describe('classifier→compiler tuple field mapping', () => {
  it('depth maps shallow→retrieval, standard→structure, deep→deepdive', () => {
    expect(classifierTupleToCompilerTuple(tuple({ depth: 'shallow' })).depth).toBe('retrieval')
    expect(classifierTupleToCompilerTuple(tuple({ depth: 'standard' })).depth).toBe('structure')
    expect(classifierTupleToCompilerTuple(tuple({ depth: 'deep' })).depth).toBe('deepdive')
  })
  it('intervention enum → boolean', () => {
    expect(classifierTupleToCompilerTuple(tuple({ intervention: 'none' })).intervention).toBe(false)
    expect(classifierTupleToCompilerTuple(tuple({ intervention: 'remedy' })).intervention).toBe(true)
    expect(classifierTupleToCompilerTuple(tuple({ intervention: 'muhurta' })).intervention).toBe(true)
  })
  it('produces a compiler tuple that compileContract accepts for every classifier intent', () => {
    // Exercises the totality guarantee — no classifier tuple yields an unregistered floor.
    const intents: ClassifierScopeTuple['intent'][] = [
      'dasha_timing', 'transit_analysis', 'yoga_identification', 'planet_strength',
      'house_analysis', 'remedy_lookup', 'panchanga', 'classical_rule',
      'chart_overview', 'prediction_calibration', 'domain_assessment', 'unknown',
    ]
    for (const intent of intents) {
      const r = compileFloorForPlan(tuple({ intent, domains: ['general'] }), CHART)
      expect(r.compileFailed).toBe(false)
    }
  })
})

describe('LIVE_TOOL_TO_RETRIEVAL bridge integrity', () => {
  it('every mapped retrieval name resolves via getToolByName (no no-op tool names)', () => {
    for (const retrievalName of Object.values(LIVE_TOOL_TO_RETRIEVAL)) {
      expect(getToolByName(retrievalName), `retrieval tool "${retrievalName}" must resolve`).toBeDefined()
    }
  })
})

describe('resolveLiveTool — W5 L1 generated-bridge fallback widens floor-primitive coverage', () => {
  it('resolves strictly more of the 23 distinct Vidhi live_tool names than the pre-W5 hand map alone', () => {
    const liveToolNames = [...new Set(VIDHI_PRIMITIVES.map((p) => p.live_tool))]
    const handMapOnly = liveToolNames.filter((n) => LIVE_TOOL_TO_RETRIEVAL[n] !== undefined)
    const withGeneratedFallback = liveToolNames.filter((n) => resolveLiveTool(n) !== undefined)
    // Pre-W5 baseline was exactly 4/23 (W4 close measurement, STATE.md). Asserted
    // as a floor (not the literal hand-map size) so this doesn't rot if the hand
    // map itself grows later — the point is the GENERATED layer adds coverage on
    // top, not that the hand map stays frozen at 4.
    expect(handMapOnly.length).toBeGreaterThanOrEqual(4)
    expect(withGeneratedFallback.length).toBeGreaterThan(handMapOnly.length)
  })

  it('every name resolveLiveTool maps is actually executable via getToolByName', () => {
    const liveToolNames = [...new Set(VIDHI_PRIMITIVES.map((p) => p.live_tool))]
    for (const n of liveToolNames) {
      const resolved = resolveLiveTool(n)
      if (resolved === undefined) continue
      expect(getToolByName(resolved), `live_tool "${n}" -> "${resolved}" must resolve`).toBeDefined()
    }
  })
})

describe('compileFloorForPlan — floor adoption', () => {
  it('career_deepdive tuple yields the career floor items mapped to retrieval tools', () => {
    const r = compileFloorForPlan(tuple({ domains: ['career'], depth: 'deep' }), CHART)
    expect(r.compilerIntent).toBe('career_deepdive')
    // career floor includes mechanism_read (→ cgm_graph_walk) and dhana_yoga_scan (→ get_yoga_firings)
    expect(r.mappedPrimitives).toContain('mechanism_read')
    expect(r.mappedPrimitives).toContain('dhana_yoga_scan')
    const names = r.toolCalls.map((t) => t.tool_name)
    expect(names).toContain('cgm_graph_walk')
    expect(names).toContain('get_yoga_firings')
    // MCP-native primitives with no retrieval equivalent are reported, not pushed.
    expect(r.unmappedPrimitives).toContain('bhava_condition')
    expect(names).not.toContain('ganita_structural_get')
  })

  it('chart_id is stripped from adapted params (route injects it)', () => {
    const r = compileFloorForPlan(tuple({ domains: ['career'] }), CHART)
    for (const tc of r.toolCalls) {
      expect(tc.params).not.toHaveProperty('chart_id')
    }
  })

  it('tool_calls carry valid ToolCallItem budgets/priorities', () => {
    const r = compileFloorForPlan(tuple({ domains: ['wealth'], depth: 'deep' }), CHART)
    for (const tc of r.toolCalls) {
      expect(tc.token_budget).toBeGreaterThanOrEqual(100)
      expect([1, 2, 3]).toContain(tc.priority)
      expect(tc.reason.length).toBeGreaterThan(0)
    }
  })

  it('is deterministic — identical tuple → identical tool_calls', () => {
    const a = compileFloorForPlan(tuple({ domains: ['wealth'] }), CHART)
    const b = compileFloorForPlan(tuple({ domains: ['wealth'] }), CHART)
    expect(JSON.stringify(a.toolCalls)).toBe(JSON.stringify(b.toolCalls))
  })
})

describe('ensureB11WholeChartReadFloor — B.11 invariant', () => {
  it('no-ops when an L2.5 tool is already present (e.g. compiled cgm_graph_walk)', () => {
    const p = plan('interpretive', ['cgm_graph_walk'])
    const authorized = ['cgm_graph_walk']
    expect(ensureB11WholeChartReadFloor(p, authorized)).toBe(false)
    expect(p.tool_calls).toHaveLength(1)
  })
  it('injects the registry-URI floor when no L2.5 tool present (non-predictive)', () => {
    const p = plan('interpretive', ['get_positions'])
    const authorized = ['get_positions']
    expect(ensureB11WholeChartReadFloor(p, authorized)).toBe(true)
    expect(authorized).toContain('marsys://tool/L2/query_signals')
    expect(authorized).toContain('marsys://tool/L2/traverse_chart_graph')
  })
  it('predictive class injects vector_search + pattern_register, not traverse_chart_graph', () => {
    const p = plan('predictive', [], ['marriage'])
    const authorized: string[] = []
    ensureB11WholeChartReadFloor(p, authorized)
    expect(authorized).toContain('marsys://tool/L2/query_signals')
    expect(authorized).toContain('vector_search')
    expect(authorized).toContain('pattern_register')
    expect(authorized).not.toContain('marsys://tool/L2/traverse_chart_graph')
    // domain-derived search query
    const vs = p.tool_calls.find((t) => t.tool_name === 'vector_search')
    expect((vs?.params as { query_text?: string }).query_text).toBe('marriage')
  })
})

describe('ensureDashaContextFloor', () => {
  it('injects chart_facts_query dasha floor for predictive class', () => {
    const p = plan('predictive')
    const authorized: string[] = []
    expect(ensureDashaContextFloor(p, authorized)).toBe(true)
    const cf = p.tool_calls.find((t) => t.tool_name === 'chart_facts_query')
    expect(cf?.params).toEqual({ category: 'dasha_vimshottari', limit: 50 })
  })
  it('injects for holistic class', () => {
    const authorized: string[] = []
    expect(ensureDashaContextFloor(plan('holistic'), authorized)).toBe(true)
  })
  it('no-ops for non-predictive/holistic classes', () => {
    const authorized: string[] = []
    expect(ensureDashaContextFloor(plan('interpretive'), authorized)).toBe(false)
    expect(ensureDashaContextFloor(plan('factual'), authorized)).toBe(false)
  })
  it('no-ops when chart_facts_query already authorized', () => {
    const authorized = ['chart_facts_query']
    expect(ensureDashaContextFloor(plan('predictive', ['chart_facts_query']), authorized)).toBe(false)
  })
})

describe('end-to-end floor adoption parity (route sequence)', () => {
  // Reproduces the route.ts sequence: compile → adopt → B.11 guarantee → dasha guarantee.
  function runFloor(t: ClassifierScopeTuple, queryClass: QueryClass): string[] {
    const p = plan(queryClass, [], t.domains as string[])
    const authorized = Array.from(new Set(p.tool_calls.map((tc) => tc.tool_name)))
    const compiled = compileFloorForPlan(t, CHART)
    for (const tc of compiled.toolCalls) {
      if (!authorized.includes(tc.tool_name)) {
        p.tool_calls.push(tc)
        authorized.push(tc.tool_name)
      }
    }
    ensureB11WholeChartReadFloor(p, authorized)
    ensureDashaContextFloor(p, authorized)
    return authorized
  }

  it('career deepdive: compiled cgm_graph_walk satisfies B.11 (no redundant registry floor)', () => {
    const authorized = runFloor(tuple({ domains: ['career'], depth: 'deep' }), 'interpretive')
    expect(authorized).toContain('cgm_graph_walk')
    expect(authorized).not.toContain('marsys://tool/L2/traverse_chart_graph')
    expect(authorized.some((t) => L2_5_TOOLS.includes(t))).toBe(true)
  })

  it('health deepdive (no mechanism_read primitive): B.11 guarantee fires registry floor', () => {
    const authorized = runFloor(tuple({ domains: ['health'], depth: 'deep' }), 'interpretive')
    // health floor has no L2.5-mapped primitive → the guarantee injects the registry floor
    expect(authorized).toContain('marsys://tool/L2/query_signals')
    expect(authorized.some((t) => L2_5_TOOLS.includes(t))).toBe(true)
  })

  it('predictive holistic query still gets predictive floor + dasha floor', () => {
    const authorized = runFloor(tuple({ domains: ['marriage'], depth: 'deep' }), 'predictive')
    expect(authorized).toContain('vector_search')
    expect(authorized).toContain('pattern_register')
    expect(authorized).toContain('chart_facts_query')
  })

  it('missing scope_tuple falls back to legacy floor (guarantees only)', () => {
    // Simulate route path with no scope_tuple: skip compile, run guarantees only.
    const p = plan('predictive', [], ['career'])
    const authorized: string[] = []
    ensureB11WholeChartReadFloor(p, authorized)
    ensureDashaContextFloor(p, authorized)
    expect(authorized).toContain('marsys://tool/L2/query_signals')
    expect(authorized).toContain('vector_search')
    expect(authorized).toContain('chart_facts_query')
  })
})

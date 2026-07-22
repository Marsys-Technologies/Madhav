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
import { QueryClassEnum, type PipelinePlan, type QueryClass } from '@/lib/pipeline/types'
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
  it('predictive class injects vector_search (not traverse_chart_graph); pattern_register removed (W6.2 fix-cycle)', () => {
    const p = plan('predictive', [], ['marriage'])
    const authorized: string[] = []
    ensureB11WholeChartReadFloor(p, authorized)
    expect(authorized).toContain('marsys://tool/L2/query_signals')
    expect(authorized).toContain('vector_search')
    // W6.2 fix-cycle: pattern_register was removed from the MCP whitelist in WP-1.7
    // ("no registered cap") but this predictive-floor injection kept requiring it,
    // guaranteeing an unresolved-tool gap on every predictive query. Must never
    // reappear here without a real, resolvable capability backing it.
    expect(authorized).not.toContain('pattern_register')
    expect(authorized).not.toContain('marsys://tool/L2/traverse_chart_graph')
    // domain-derived search query
    const vs = p.tool_calls.find((t) => t.tool_name === 'vector_search')
    expect((vs?.params as { query_text?: string }).query_text).toBe('marriage')
  })
})

describe('ensureDashaContextFloor', () => {
  it('injects query_dasha_periods (W6.2 fix-cycle — NOT chart_facts_query, which never held dasha data)', () => {
    const p = plan('predictive')
    const authorized: string[] = []
    expect(ensureDashaContextFloor(p, authorized)).toBe(true)
    // W6.2 fix-cycle: chart_facts_query with category:'dasha_vimshottari' always
    // returned returned_count:0 live (dasha data lives in chart_dashas, served by
    // query_dasha_periods → marsys://tool/L1/get_dashas, not chart_facts at all).
    const cf = p.tool_calls.find((t) => t.tool_name === 'chart_facts_query')
    expect(cf).toBeUndefined()
    const dp = p.tool_calls.find((t) => t.tool_name === 'query_dasha_periods')
    expect(dp?.params).toEqual({ system: 'vimshottari', level: 2 })
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
  it('no-ops when query_dasha_periods already authorized', () => {
    const authorized = ['query_dasha_periods']
    expect(ensureDashaContextFloor(plan('predictive', ['query_dasha_periods']), authorized)).toBe(false)
  })
})

describe('RC-05 — no unresolvable required floor item for ANY query class (RETRIEVAL_RESIDUAL_CLOSURE_BRIEF §E Cluster 2)', () => {
  // WP-1.7's full dead-capability list (tool_name_bridge.ts:410-422) — names with
  // NO registered retrieval capability. pattern_register was the W6.2/W6.3 defect;
  // resonance_register/cluster_atlas are the RC-05 defect this test guards against
  // regression on. The rest are included for completeness of the guard, even though
  // they were never actively floor-injected by this code adapter.
  const DEAD_CAPABILITIES = [
    'pattern_register', 'resonance_register', 'cluster_atlas',
    'kp_query', 'query_kp_ruling_planets', 'query_ucn_walk',
    'query_cdlm_lookup', 'query_rm_walk', 'query_jaimini_drishti',
    'timeline_query', 'query_signal_state', 'multi_school_signal_lookup',
    'jaimini_chara_dasha', 'jaimini_chara_dasha_full',
  ] as const

  it('ensureB11WholeChartReadFloor + ensureDashaContextFloor inject only resolvable tool_calls, for every QueryClass', () => {
    for (const qc of QueryClassEnum.options) {
      const p = plan(qc as QueryClass)
      const authorized: string[] = []
      ensureB11WholeChartReadFloor(p, authorized)
      ensureDashaContextFloor(p, authorized)
      for (const tc of p.tool_calls) {
        expect(
          getToolByName(tc.tool_name),
          `query_class "${qc}": floor tool_call "${tc.tool_name}" must resolve via getToolByName()`,
        ).toBeDefined()
      }
    }
  })

  it('never floor-injects a WP-1.7 dead capability, for any QueryClass', () => {
    for (const qc of QueryClassEnum.options) {
      const p = plan(qc as QueryClass)
      const authorized: string[] = []
      ensureB11WholeChartReadFloor(p, authorized)
      ensureDashaContextFloor(p, authorized)
      const names = p.tool_calls.map((t) => t.tool_name)
      for (const dead of DEAD_CAPABILITIES) {
        expect(
          names,
          `query_class "${qc}" must never floor-inject dead capability "${dead}" (WP-1.7/tool_name_bridge.ts:417 — no registered cap)`,
        ).not.toContain(dead)
      }
    }
  })

  it('discovery and remedial classes specifically resolve clean (the RC-05 live-trace acceptance bar)', () => {
    for (const qc of ['discovery', 'remedial'] as const) {
      const p = plan(qc)
      const authorized: string[] = []
      ensureB11WholeChartReadFloor(p, authorized)
      ensureDashaContextFloor(p, authorized)
      expect(p.tool_calls.length).toBeGreaterThanOrEqual(0) // no-op is valid (no L2.5 tool from THIS adapter for these classes)
      for (const tc of p.tool_calls) {
        expect(getToolByName(tc.tool_name), `${qc}: "${tc.tool_name}" must resolve`).toBeDefined()
      }
    }
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

  it('health deepdive: an L2.5 tool is present on the authorized set (RC-10: now via the compiled varga_ratification primitive, not the guarantee)', () => {
    const authorized = runFloor(tuple({ domains: ['health'], depth: 'deep' }), 'interpretive')
    // Pre-RC-10, health's floor had no L2.5-mapped primitive so the guarantee injected
    // the registry floor. RC-10 bridged bodha_signals_get → marsys://tool/L2/query_signals,
    // and health's own `varga_ratification` primitive (live_tool: bodha_signals_get) now
    // supplies this directly from the compiled floor — same invariant (≥1 L2.5 tool),
    // now satisfied by real domain-relevant data instead of generic filler.
    expect(authorized).toContain('marsys://tool/L2/query_signals')
    expect(authorized.some((t) => L2_5_TOOLS.includes(t))).toBe(true)
  })

  it('predictive holistic query still gets predictive floor + dasha floor (W6.2: pattern_register removed, query_dasha_periods not chart_facts_query)', () => {
    const authorized = runFloor(tuple({ domains: ['marriage'], depth: 'deep' }), 'predictive')
    // RC-10 (namespace-gap re-measure): marriage_deepdive's own `varga_ratification`
    // primitive (live_tool: bodha_signals_get) now resolves to a real registry L2.5
    // tool (marsys://tool/L2/query_signals) via the newly-bridged mapping — the SAME
    // "compiled floor already supplies an L2.5 tool" no-op path the career_deepdive
    // test above already exercises for cgm_graph_walk. ensureB11WholeChartReadFloor's
    // no-op condition correctly fires (B.11 is satisfied by a real, domain-relevant
    // signal query rather than the generic predictive-class filler), so the generic
    // vector_search injection no longer fires for THIS specific case — the invariant
    // (≥1 L2.5 whole-chart-read tool) still holds, just via a more precise source.
    expect(authorized.some((t) => L2_5_TOOLS.includes(t))).toBe(true)
    expect(authorized).toContain('marsys://tool/L2/query_signals')
    expect(authorized).not.toContain('pattern_register')
    expect(authorized).toContain('query_dasha_periods')
    expect(authorized).not.toContain('chart_facts_query')
  })

  it('predictive class with NO compiled L2.5 primitive still gets the generic vector_search + forward_looking floor', () => {
    // retrieval_only's floor (positions_snapshot → ganita_positions_get) has no
    // L2.5-mapped primitive, so the guarantee's generic predictive injection still
    // fires exactly as before RC-10 — the fallback path is unchanged, only the
    // "compiled floor already covers it" short-circuit widened (all four domain
    // deepdives now hit that path, since each includes `varga_ratification`).
    const authorized = runFloor(
      tuple({ intent: 'planet_strength', domains: ['general'], depth: 'shallow' }),
      'predictive',
    )
    expect(authorized).toContain('vector_search')
    expect(authorized).toContain('marsys://tool/L2/query_signals')
    expect(authorized).not.toContain('pattern_register')
    expect(authorized).toContain('query_dasha_periods')
  })

  it('missing scope_tuple falls back to legacy floor (guarantees only)', () => {
    // Simulate route path with no scope_tuple: skip compile, run guarantees only.
    const p = plan('predictive', [], ['career'])
    const authorized: string[] = []
    ensureB11WholeChartReadFloor(p, authorized)
    ensureDashaContextFloor(p, authorized)
    expect(authorized).toContain('marsys://tool/L2/query_signals')
    expect(authorized).toContain('vector_search')
    expect(authorized).toContain('query_dasha_periods')
  })
})

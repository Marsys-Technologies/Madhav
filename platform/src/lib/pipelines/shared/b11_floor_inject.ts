/**
 * b11_floor_inject — shared stage: inject the B.11 holistic-read floor into
 * a PipelinePlan's tool_calls when the planner did not already include one.
 *
 * @deprecated (W4 step 3 — floor adoption, 2026-07). SUPERSEDED. The consult route no
 * longer force-injects a hardcoded literal B.11 floor: it now COMPILES the floor from
 * the plan's deterministic scope_tuple via the Vidhi compiler and enforces the B.11 +
 * dasha invariants through `ensureB11WholeChartReadFloor` / `ensureDashaContextFloor`
 * in `@/lib/pipeline/compiled_floor_adapter`. This helper was an extracted copy of
 * route.ts's OLD inline logic and has NO production caller (only its own unit test).
 * It also drifted from route.ts (this copy emits legacy `msr_sql`/`cgm_graph_walk`
 * names; route.ts emitted the D7 registry-URI aliases). Retained, not deleted, so the
 * pipelines barrel export + existing test keep compiling; do NOT wire it into any new
 * path — use `compiled_floor_adapter` instead. Safe to remove once the G5b pipeline
 * seam lands and this barrel export is confirmed unused.
 *
 * Original note: extracted verbatim from consult/route.ts (B.11 Whole-Chart-Read
 * enforcement + Dasha context floor).
 */

import type { PipelinePlan } from '@/lib/pipeline/types'

/** The L2.5 tool names that satisfy the B.11 floor (legacy retrieve names). */
export const L2_5_TOOLS = [
  'msr_sql',
  'query_msr_aggregate',
  'pattern_register',
  'resonance_register',
  'cluster_atlas',
  'contradiction_register',
  'cgm_graph_walk',
] as const

/** What the route returns from the injection step — for tracing. */
export interface FloorInjectionResult {
  /** True if the planner did not already include an L2.5 tool. */
  injected: boolean
  /** True if the dasha context floor was also injected. */
  dashaInjected: boolean
  /** Final, unique list of authorized tool names after injection. */
  toolsAuthorized: string[]
}

export function injectB11Floor(plan: PipelinePlan): FloorInjectionResult {
  const toolsAuthorized = Array.from(new Set(plan.tool_calls.map(tc => tc.tool_name)))
  let injected = false

  if (!toolsAuthorized.some(t => (L2_5_TOOLS as readonly string[]).includes(t))) {
    injected = true
    // Predictive class: cgm_graph_walk is banned (R14c); pattern_register is
    // required (R7a). Inject msr_sql + vector_search + pattern_register so the
    // synthesis model receives the domain narrative it needs.
    if (plan.query_class === 'predictive') {
      const domainSearchQuery = (plan.domains ?? []).length > 0
        ? (plan.domains ?? []).join(' ')
        : 'relationships family marriage children'
      plan.tool_calls.push(
        { tool_name: 'msr_sql', params: { forward_looking: true }, token_budget: 600, priority: 1 as const, reason: 'B.11 predictive floor: signal foundation' },
        { tool_name: 'vector_search', params: { query_text: domainSearchQuery, doc_type: ['domain_report'], top_k: 6 }, token_budget: 500, priority: 1 as const, reason: 'B.11 predictive floor: domain narrative' },
        { tool_name: 'pattern_register', params: { forward_looking: true }, token_budget: 400, priority: 2 as const, reason: 'B.11 predictive floor: R7a requirement' },
      )
      toolsAuthorized.push('msr_sql', 'vector_search', 'pattern_register')
    } else {
      plan.tool_calls.push(
        { tool_name: 'msr_sql', params: {}, token_budget: 600, priority: 1 as const, reason: 'B.11 floor enforcement' },
        { tool_name: 'cgm_graph_walk', params: {}, token_budget: 400, priority: 2 as const, reason: 'B.11 floor enforcement' },
      )
      toolsAuthorized.push('msr_sql', 'cgm_graph_walk')
    }
  }

  // Dasha context floor: predictive and holistic queries always need the
  // canonical Vimshottari dasha sequence so synthesis can anchor phase-based
  // predictions to correct dates (data lives in chart_facts.dasha_vimshottari).
  let dashaInjected = false
  if (
    (plan.query_class === 'predictive' || plan.query_class === 'holistic') &&
    !toolsAuthorized.includes('chart_facts_query')
  ) {
    dashaInjected = true
    plan.tool_calls.push({
      tool_name: 'chart_facts_query',
      // limit:50 required — there are 50 AD records (V.001–V.050). Default limit:20
      // only covers through Mercury-Mars AD (ends 2020), cutting off the current
      // Mercury-Saturn AD and all future Ketu MD + Venus MD periods.
      params: { category: 'dasha_vimshottari', limit: 50 },
      token_budget: 600,
      priority: 1 as const,
      reason: 'dasha context floor: synthesis requires canonical MD/AD sequence for phase-anchored predictions',
    })
    toolsAuthorized.push('chart_facts_query')
  }

  return { injected, dashaInjected, toolsAuthorized }
}

/**
 * B.11 floor — the canonical Whole-Chart-Read floor enforced by the gateway.
 *
 * B.11 (PROJECT_ARCHITECTURE §H.4): every query must route through L2.5
 * Holistic Synthesis (MSR + UCN + CGM minimum) before producing its
 * domain-specific answer. The gateway enforces this structurally by:
 *   1. Declaring a fixed set of "floor tools" — these are the only tools
 *      a query may call before `b11FloorSatisfied` is set true.
 *   2. Rejecting any non-floor `invoke_tool` call with code
 *      `B11_FLOOR_MISSING` when `ctx.b11FloorSatisfied` is not true.
 *
 * The pipeline is the authority that marks the floor satisfied — it does so
 * once it has actually executed the floor tools and produced their bundles.
 * The gateway accepts this assertion; it does not re-execute MSR/UCN/CGM.
 *
 * This keeps the gateway plumbing-only while making B.11 a hard structural
 * gate rather than a soft prompt convention.
 */

/**
 * The canonical floor — names of tools that produce MSR/UCN/CDLM/CGM/RM reads.
 * These are allowed BEFORE `b11FloorSatisfied`; the moment a non-floor tool
 * is called without the flag set, the gateway rejects.
 */
export const B11_FLOOR_TOOL_NAMES: ReadonlySet<string> = new Set([
  // L2.5 holistic reads (MSR/UCN/CGM/CDLM/RM)
  'msr_sql',
  'query_msr_aggregate',
  'pattern_register',
  'resonance_register',
  'cluster_atlas',
  'contradiction_register',
  'cgm_graph_walk',
  // L1 retrieval surface that the planner's B.11 floor *also* injects under
  // predictive class (route.ts §B.11 floor enforcement, lines 472–516):
  // both contract-canonical (`query_chart_facts`) and legacy retrieve
  // (`chart_facts_query`) names are members until the alias collapse lands.
  'query_chart_facts',
  'chart_facts_query',
  'vector_search',
  // Holistic / school bundles also qualify — they wrap the floor layers.
  'holistic_bundle',
  'multi_school_bundle',
])

export function isFloorTool(name: string): boolean {
  return B11_FLOOR_TOOL_NAMES.has(name)
}

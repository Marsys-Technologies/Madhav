/**
 * compiled_floor_adapter.ts — W4 "One Planner", sequential core step 3 (floor adoption).
 *
 * Bridges the deterministic Vidhi *compiler* (`compileContract`, @/lib/vidhi/compiler)
 * to the consult route's tool-execution path. It replaces the hardcoded literal
 * "B.11 floor" tool lists that used to live inline in consult/route.ts.
 *
 * ── The two-namespace problem this file solves ──────────────────────────────────
 *
 * There are TWO distinct `ScopeTuple` shapes in the tree:
 *   1. the CLASSIFIER's tuple (@/lib/vidhi/scope_classifier) — attached to a
 *      PipelinePlan as `plan.scope_tuple` by `callPipelinePlanner`;
 *   2. the COMPILER's tuple (@/lib/vidhi/types) — what `compileContract` accepts.
 * They are deliberately different concepts (see the scope_classifier.ts header note).
 * `classifierTupleToCompilerTuple` is the mandatory, deterministic, total mapping
 * between them.
 *
 * Also: `compileContract` emits `live_tool` names in the LIVE MCP connector namespace
 * (`ganita_structural_get`, `bodha_signals_get`, …) — the compiler was authored for
 * the MCP channel (see compiler.ts / registry_data.ts headers). The consult route
 * executes retrieval-REGISTRY tool names via `getToolByName()`. Only the subset of
 * compiled primitives whose `live_tool` has a resolvable retrieval-registry equivalent
 * can execute on the web consult path; `LIVE_TOOL_TO_RETRIEVAL` is that (small,
 * explicit, test-guarded) map. Primitives with no equivalent are reported as
 * `unmappedPrimitives` rather than pushed as no-op tool names that would produce empty
 * trace steps. This is a known architecture gap documented in the W4 step-3 report.
 *
 * Two invariants the compiler does NOT express in web-executable form are preserved
 * here as explicit, orthogonal guarantees, byte-faithful to consult/route.ts's prior
 * inline logic:
 *   - `ensureB11WholeChartReadFloor` — the B.11 Whole-Chart-Read floor (≥1 L2.5 tool),
 *     including the predictive-class special-casing (vector_search + pattern_register);
 *   - `ensureDashaContextFloor` — the canonical Vimshottari dasha context floor for
 *     predictive/holistic query classes.
 */

import type { PipelinePlan, ToolCallItem } from './types'
import type { ScopeTuple as ClassifierScopeTuple } from '@/lib/vidhi/scope_classifier'
import type { IntentClass, ScopeDepth, ScopeTuple as CompilerScopeTuple } from '@/lib/vidhi/types'
import { compileContract, defaultRegistry } from '@/lib/vidhi/compiler'
import { resolveGeneratedToolUri } from '@/lib/retrieval/registry/generated_web_tool_bridge'

// ── L2.5 whole-chart-read tool names (B.11) ─────────────────────────────────────
// Kept identical to consult/route.ts's prior inline list. Old names (`msr_sql`,
// `cgm_graph_walk`) are retained alongside the D7 registry-URI aliases for backward
// compat with the lib/retrieve execution path.
export const L2_5_TOOLS: readonly string[] = [
  'msr_sql',
  'query_msr_aggregate',
  'pattern_register',
  'resonance_register',
  'cluster_atlas',
  'contradiction_register',
  'cgm_graph_walk',
  'marsys://tool/L2/query_signals',
  'marsys://tool/L2/traverse_chart_graph',
]

// ── classifier tuple → compiler tuple ───────────────────────────────────────────

const DOMAIN_DEEPDIVE: Readonly<Record<string, IntentClass>> = {
  wealth: 'wealth_deepdive',
  career: 'career_deepdive',
  health: 'health_deepdive',
  marriage: 'marriage_deepdive',
}

/**
 * Map the classifier's intent + domains + width/depth into one of the compiler's
 * eight registered `IntentClass` floor families. Deterministic and TOTAL — every
 * classifier tuple maps to a registered floor, so `compileContract` never throws on
 * an unregistered intent.
 *
 * Precedence (first match wins):
 *   1. breadth (broad width OR ≥3 domains)  → panoramic_breadth
 *   2. a domain-specific deepdive floor      → <domain>_deepdive
 *   3. explicit chart overview               → structure_read
 *   4. shallow / single-fact                 → retrieval_only
 *   5. otherwise                             → general_synthesis
 */
export function classifierIntentToCompilerIntent(tuple: ClassifierScopeTuple): IntentClass {
  if (tuple.width === 'broad' || tuple.domains.length >= 3) return 'panoramic_breadth'
  for (const d of tuple.domains) {
    const floor = DOMAIN_DEEPDIVE[d]
    if (floor) return floor
  }
  if (tuple.intent === 'chart_overview') return 'structure_read'
  if (tuple.depth === 'shallow') return 'retrieval_only'
  return 'general_synthesis'
}

const DEPTH_MAP: Readonly<Record<ClassifierScopeTuple['depth'], ScopeDepth>> = {
  shallow: 'retrieval',
  standard: 'structure',
  deep: 'deepdive',
}

/**
 * Total, deterministic mapping from the classifier's `ScopeTuple` to the compiler's
 * `ScopeTuple`. `width`, `horizon`, and `entitlement` are cosmetic on the compiler
 * side (only `intent`, `depth`, and `intervention` change the compiled contract —
 * see compiler.ts) but are mapped faithfully for auditability.
 */
export function classifierTupleToCompilerTuple(tuple: ClassifierScopeTuple): CompilerScopeTuple {
  return {
    intent: classifierIntentToCompilerIntent(tuple),
    domains: [...tuple.domains],
    width: tuple.width === 'broad' ? 'panoramic' : tuple.width === 'narrow' ? 'narrow' : 'standard',
    depth: DEPTH_MAP[tuple.depth],
    horizon:
      tuple.horizon === 'far' ? 'multi_year' : tuple.horizon === 'present' || tuple.horizon === 'near' ? 'current' : 'natal',
    intervention: tuple.intervention !== 'none',
    entitlement:
      tuple.entitlement === 'reference' ? 'public_disclosed' : tuple.entitlement === 'restricted' ? 'research' : 'native',
  }
}

// ── compiler live_tool (MCP namespace) → retrieval-registry tool name ────────────
//
// Only the compiled primitives whose live_tool has a resolvable retrieval-registry
// equivalent can execute on the web consult path. Every value here MUST resolve via
// getToolByName() — asserted by compiled_floor_adapter.test.ts against the bridge.
// The MANY floor primitives whose live_tool has NO retrieval equivalent
// (ganita_structural_get / ganita_condition_get / bodha_signals_get / …) are
// intentionally absent — they are reported as unmappedPrimitives, not pushed as
// no-op tool names. (Known gap: the compiler's floor is MCP-native; the web
// retrieval path covers only this subset. See the file header + W4 step-3 report.)
//
// W5 L1: this hand-curated map is now consulted SECOND — `resolveLiveTool()` below
// tries the GENERATED web-tool bridge first (`web_tool_bridge.generated.json`,
// built by `generate_projections.ts` from the live catalog + `canonical_faces.json`
// + `tool_name_bridge.ts`'s existing aliases). The generated bridge resolves
// 11/23 of Vidhi's distinct `live_tool` names today (up from this map's 4/23) —
// see `R1_PROJECTION_COMPILER_REPORT.md` §5 for the exact count and the still-
// unmapped names. Retained here (rather than deleted) as: (a) a documented,
// tested fallback for any name the generated bridge cannot yet resolve, and
// (b) the resolved value here is a retrieval-tool NAME (legacy namespace),
// whereas the generated bridge resolves straight to a registry URI — both are
// valid `tool_name` values now that `tool_name_bridge.ts`'s `resolveToolUri()`
// accepts literal registry URIs directly (the CR-118 fast-fail fix).
export const LIVE_TOOL_TO_RETRIEVAL: Readonly<Record<string, string>> = {
  get_cgm_subgraph: 'cgm_graph_walk', // mechanism_read → L2 CGM subgraph walk (an L2.5 tool)
  lel_query: 'lel_query', // lel_retrodiction → L5 life-event log
  ganita_yoga_firings_get: 'get_yoga_firings', // dhana_yoga_scan / nbry_scan → L1 yoga firings
  bodha_discoveries_get: 'query_discoveries', // contradiction_scan → L2 discoveries
}

/**
 * Resolve a Vidhi `live_tool` name to a web-executable `tool_name` (either a
 * legacy retrieval-tool name or a registry URI — both are valid `getToolByName()`
 * inputs, see `tool_name_bridge.ts`'s `resolveToolUri()`).
 *
 * Order: the small hand-curated `LIVE_TOOL_TO_RETRIEVAL` map first (documented,
 * test-guarded exceptions), then the generated projection (widens coverage
 * automatically as the catalog/canonical_faces.json grow — no hand-edit needed).
 */
export function resolveLiveTool(liveTool: string): string | undefined {
  return LIVE_TOOL_TO_RETRIEVAL[liveTool] ?? resolveGeneratedToolUri(liveTool)
}

const BAND_BUDGET = { acharya_floor: 600, machine_band: 400 } as const
const BAND_PRIORITY = { acharya_floor: 1, machine_band: 2 } as const

export interface CompiledFloorResult {
  /** The compiler IntentClass the plan's scope_tuple resolved to. */
  compilerIntent: IntentClass
  /** Retrieval-executable tool_calls derived from the compiled floor (dedup-ready). */
  toolCalls: ToolCallItem[]
  /** primitive_ids whose live_tool mapped to a retrieval-executable tool. */
  mappedPrimitives: string[]
  /** primitive_ids whose live_tool has no retrieval equivalent (MCP-native only). */
  unmappedPrimitives: string[]
  /** True if compileContract threw and this result is an empty (safe) fallback. */
  compileFailed: boolean
}

/**
 * Compile the B.11 floor for a plan's classifier scope_tuple and adapt it into
 * retrieval-executable `ToolCallItem`s. TOTAL: never throws out to the caller — if
 * `compileContract` throws (registry-completeness bug), returns an empty result with
 * `compileFailed: true` so the route's B.11 invariant guarantee still runs. This is
 * deliberate: force-injecting a floor that might not compile must degrade safely, not
 * crash the request.
 */
export function compileFloorForPlan(tuple: ClassifierScopeTuple, chartId: string): CompiledFloorResult {
  const compilerTuple = classifierTupleToCompilerTuple(tuple)
  let contract
  try {
    contract = compileContract(compilerTuple, defaultRegistry(), chartId)
  } catch {
    return {
      compilerIntent: compilerTuple.intent,
      toolCalls: [],
      mappedPrimitives: [],
      unmappedPrimitives: [],
      compileFailed: true,
    }
  }

  const toolCalls: ToolCallItem[] = []
  const mappedPrimitives: string[] = []
  const unmappedPrimitives: string[] = []
  const seen = new Set<string>()

  for (const item of [...contract.floor, ...contract.machine_band]) {
    const retrievalName = resolveLiveTool(item.live_tool)
    if (!retrievalName) {
      unmappedPrimitives.push(item.primitive_id)
      continue
    }
    mappedPrimitives.push(item.primitive_id)
    if (seen.has(retrievalName)) continue // one tool_call per distinct retrieval tool
    seen.add(retrievalName)
    // Strip the compiler-filled chart_id; the route injects chart_id from plan.
    const { chart_id: _chartId, ...params } = item.tool_args as Record<string, unknown>
    toolCalls.push({
      tool_name: retrievalName,
      params,
      token_budget: BAND_BUDGET[item.band],
      priority: BAND_PRIORITY[item.band],
      reason: `vidhi floor(${contract.scope_tuple.intent}): ${item.primitive_id}`,
    })
  }

  return {
    compilerIntent: compilerTuple.intent,
    toolCalls,
    mappedPrimitives,
    unmappedPrimitives,
    compileFailed: false,
  }
}

// ── B.11 whole-chart-read invariant + dasha context floor (preserved guarantees) ─
//
// These reproduce consult/route.ts's prior inline behavior EXACTLY (registry-URI tool
// names, predictive special-casing, dasha limit:50). They run as guarantees after the
// compiled floor is adopted, and as the sole floor when no scope_tuple is present. Each
// is idempotent: it no-ops when its invariant is already satisfied.

export interface FloorGuaranteeResult {
  b11Injected: boolean
  dashaInjected: boolean
}

/**
 * Guarantee ≥1 L2.5 whole-chart-read tool on the plan (B.11 / PROJECT_ARCHITECTURE
 * §H.4). No-ops if the plan's authorized tools already include an L2.5 tool (e.g. the
 * compiled floor mapped `mechanism_read` → `cgm_graph_walk`). Mutates `plan.tool_calls`
 * and `toolsAuthorized` in place; returns whether it injected.
 */
export function ensureB11WholeChartReadFloor(plan: PipelinePlan, toolsAuthorized: string[]): boolean {
  if (toolsAuthorized.some((t) => L2_5_TOOLS.includes(t))) return false

  if (plan.query_class === 'predictive') {
    // Predictive class: cgm_graph_walk is banned (R14c). Inject msr_sql + vector_search
    // so the synthesis model receives the domain narrative it needs.
    //
    // W6.2 fix-cycle (native-directed, live E2E trace 980e8181): this used to ALSO
    // inject 'pattern_register' per an "R7a requirement" — but pattern_register was
    // deliberately removed from the MCP surgical whitelist in WP-1.7 with the explicit
    // finding "no registered cap / concept never existed" (tool_name_bridge.ts:417).
    // Requiring a capability that can never resolve meant every single predictive-class
    // query on BOTH doors (consult and prashna_ask) permanently carried an unresolved-
    // tool gap since WP-1.7 landed — not a rare edge case, a guaranteed one. Removed.
    // If a real replacement for R7a's intent (pattern-grounding for predictive synthesis)
    // is built in a future wave (e.g. once the D-4b Discovery Layer's pattern registers
    // are actually served as a retrieval capability), this is the injection site to
    // re-add it — not before a real, resolvable capability exists.
    const domainSearchQuery =
      (plan.domains ?? []).length > 0 ? (plan.domains ?? []).join(' ') : 'relationships family marriage children'
    plan.tool_calls.push(
      { tool_name: 'marsys://tool/L2/query_signals', params: { forward_looking: true }, token_budget: 600, priority: 1, reason: 'B.11 predictive floor: signal foundation (registry)' },
      { tool_name: 'vector_search', params: { query_text: domainSearchQuery, doc_type: ['domain_report'], top_k: 6 }, token_budget: 500, priority: 1, reason: 'B.11 predictive floor: domain narrative' },
    )
    toolsAuthorized.push('marsys://tool/L2/query_signals', 'vector_search')
  } else {
    plan.tool_calls.push(
      { tool_name: 'marsys://tool/L2/query_signals', params: {}, token_budget: 600, priority: 1, reason: 'B.11 floor enforcement (registry)' },
      { tool_name: 'marsys://tool/L2/traverse_chart_graph', params: {}, token_budget: 400, priority: 2, reason: 'B.11 floor enforcement (registry)' },
    )
    toolsAuthorized.push('marsys://tool/L2/query_signals', 'marsys://tool/L2/traverse_chart_graph')
  }
  return true
}

/**
 * Guarantee the canonical Vimshottari dasha context floor for predictive/holistic
 * query classes. No-ops otherwise or if `query_dasha_periods` is already authorized.
 * Mutates in place; returns whether injected.
 *
 * W6.2 fix-cycle (native-directed, live E2E trace 980e8181): this used to inject
 * `chart_facts_query` with `{category:'dasha_vimshottari', limit:50}` — a genuine bug,
 * not a rare edge case. Dasha period data has never lived in `chart_facts` at all; it
 * lives in the separate `chart_dashas` table, served by `query_dasha_periods` (resolves
 * to `marsys://tool/L1/get_dashas` — tool_name_bridge.ts:86). The old injection was
 * confirmed live (both a `category:'dasha_vimshottari'` filter AND a bare `keyword:
 * 'dasha'` search against `chart_facts_query` return `returned_count:0` on the
 * canonical chart) — every single predictive/holistic query on BOTH doors has been
 * silently missing its dasha context floor since this function was written, exactly
 * the "silently absorbed empty result" failure mode B.10/§N.6 forbid. `get_dashas.ts`
 * needs no window override to get a synthesis-useful default: unfiltered, it already
 * returns a ±5-year window around "now" (verified live) — wide enough to cover any
 * currently-running MD/AD/PD and near-future transitions without needing a bespoke
 * limit.
 */
export function ensureDashaContextFloor(plan: PipelinePlan, toolsAuthorized: string[]): boolean {
  if (
    (plan.query_class === 'predictive' || plan.query_class === 'holistic') &&
    !toolsAuthorized.includes('query_dasha_periods')
  ) {
    plan.tool_calls.push({
      tool_name: 'query_dasha_periods',
      params: { system: 'vimshottari', level: 2 },
      token_budget: 600,
      priority: 1,
      reason: 'dasha context floor: synthesis requires canonical MD/AD sequence for phase-anchored predictions',
    })
    toolsAuthorized.push('query_dasha_periods')
    return true
  }
  return false
}

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
  // CR-24 (SARVA-SIDDHI, 2026-07-24): mechanism_read's live_tool was repointed from the raw
  // bodha_graph_subgraph_get (→ cgm_graph_walk) to the dedicated bodha_mechanisms_get face
  // (→ marsys://tool/L2/query_mechanisms, generated bridge). Same L2 whole-chart-read tier —
  // named-mechanism CGM subgraph motifs — so it belongs in the B.11 floor alongside its sibling.
  'marsys://tool/L2/query_mechanisms',
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
// The floor primitives whose live_tool has NO retrieval equivalent
// (ganita_structural_get / ganita_condition_get / kala_temporal_bundle, as of RC-10) are
// intentionally absent — they are reported as unmappedPrimitives, not pushed as no-op tool
// names. (Known gap, Resolver-dispositioned per RC-10: see this file's
// LIVE_TOOL_TO_RETRIEVAL comment above + NAMESPACE_COVERAGE_v2_0.md.)
//
// W5 L1: this hand-curated map is now consulted SECOND — `resolveLiveTool()` below
// tries the GENERATED web-tool bridge first (`web_tool_bridge.generated.json`,
// built by `generate_projections.ts` from the live catalog + `canonical_faces.json`
// + `tool_name_bridge.ts`'s existing aliases). Retained here (rather than deleted)
// as: (a) a documented, tested fallback for any name the generated bridge cannot yet
// resolve, and (b) the resolved value here is a retrieval-tool NAME (legacy
// namespace) OR a literal registry URI — both are valid `tool_name` values now that
// `tool_name_bridge.ts`'s `resolveToolUri()` accepts literal registry URIs directly
// (the CR-118 fast-fail fix).
//
// RC-10 (R-9, 2026-07-22, corrected 2026-07-23 on verifier REJECT) measures combined
// coverage (this hand map + the generated-bridge fallback) at 20/23 of Vidhi's distinct
// `live_tool` names — up from the W5 L1 baseline of 11/23. The remaining 3
// (`ganita_structural_get`, `ganita_condition_get`, `kala_temporal_bundle`) are
// Resolver-dispositioned below (DEFERRED), not silently dropped and not force-mapped to a
// plausible-looking but wrong URI. See
// `00_ARCHITECTURE/briefs/retrieval_residual/NAMESPACE_COVERAGE_v2_0.md` and
// `00_ARCHITECTURE/briefs/retrieval_residual/RESOLVER_RULINGS.md` (RC-10-001/002/003) for
// the full per-tool evidence table and disposition rationale.
export const LIVE_TOOL_TO_RETRIEVAL: Readonly<Record<string, string>> = {
  get_cgm_subgraph: 'cgm_graph_walk', // legacy live_tool name; kept for any stale reference
  bodha_graph_subgraph_get: 'cgm_graph_walk', // RC-14: mechanism_read's live_tool was repointed from
    // the removed legacy name get_cgm_subgraph to its canonical replacement bodha_graph_subgraph_get
    // (VIDHI_PRIMITIVES); this key keeps the mapping live under the new name — mechanism_read → L2 CGM subgraph walk (an L2.5 tool)
  lel_query: 'lel_query', // legacy live_tool name; kept for any stale reference
  mimamsa_lel_query: 'lel_query', // RC-14: lel_retrodiction's live_tool was repointed from
    // the removed legacy name lel_query to its canonical replacement mimamsa_lel_query
    // (VIDHI_PRIMITIVES); this key keeps the mapping live under the new name → L5 life-event log
  ganita_yoga_firings_get: 'get_yoga_firings', // dhana_yoga_scan / nbry_scan → L1 yoga firings
  bodha_discoveries_get: 'query_discoveries', // contradiction_scan → L2 discoveries
  // SARVA-SIDDHI W-2 P-1: standing_predictions_read (E-2) → the LIVE prospective-ledger read
  // capability (brahma_prospective_ledger, migration 458). Repointed from the mis-wired
  // phala_predictive_anchors_get (L4 phala_anchors) so the native's filed standing predictions
  // surface on the web consult path exactly as they do on the MCP connector.
  standing_predictions_read: 'marsys://tool/L4/query_prospective_ledger',

  // RC-10 (R-9, namespace-gap re-measure, 2026-07-22): 9 more of the 23 distinct
  // `live_tool` names, each verified as a genuine 1:1 concept match to an already-live
  // retrieval-registry capability (confirmed by reading the MCP tool's own handler body
  // in platform-mcp/src/tools/register_p1_*.ts — every entry below calls the exact
  // registry URI on the right via `callRegistryCapability(...)`, so this is the SAME
  // underlying data the MCP door already serves under this name, not a new/guessed
  // mapping). See NAMESPACE_COVERAGE_v2_0.md for the full per-tool evidence table.
  // (`ganita_condition_get` was REMOVED from this map on verifier REJECT, 2026-07-23 —
  // see RESOLVER_RULINGS.md RC-10-003: the MCP handler is itself a facet dispatcher over
  // get_dignity/get_avasthas/get_karakas and never calls get_condition_composite; DEFERRED
  // below alongside ganita_structural_get.)
  ganita_dasha_lord_capability_get: 'marsys://tool/L1/get_dasha_lord_capability',
  ganita_sensitive_degrees_get: 'marsys://tool/L1/get_sensitive_degrees',
  ganita_strength_get: 'marsys://tool/L1/get_strength', // shadbala / graha strength
  ganita_nakshatra_get: 'marsys://tool/L1/get_tara_chandra_bala', // MCP handler calls this exact URI (register_p1_ganita.ts §6)
  ref_doshas_get: 'marsys://tool/L0/query_dosha_catalog',
  bodha_signals_get: 'marsys://tool/L2/query_signals', // same cap msr_sql/query_msr_aggregate already resolve to
  bodha_remedies_get: 'marsys://tool/L2/query_remedies', // MCP handler calls this exact URI (register_p1_aliases.ts)
  bodha_remedies_search: 'marsys://tool/L2/query_remedies', // MCP-side documented alias of bodha_remedies_get
  kala_windows_get: 'marsys://tool/L3/query_temporal_activation', // same cap 'temporal' already resolves to

  // Genuinely un-bridged, dispositioned (not mechanical — see NAMESPACE_COVERAGE_v2_0.md):
  //   ganita_structural_get  — facet-multiplexed dispatcher (13 facets, each routing to a
  //     DIFFERENT registry URI per register_p1_ganita.ts's STRUCTURAL_FACET_URI); several
  //     Vidhi floor primitives invoke it with tool_args that carry no facet at all (e.g.
  //     `bhava_condition`), so a single static URI here would silently serve the WRONG
  //     data for some primitives — exactly the anti-laundering failure §N.6/B.10 forbid.
  //     Needs facet-aware routing in compileFloorForPlan, not a hand-map entry.
  //   ganita_condition_get   — facet-multiplexed dispatcher (3-facet: dignity/avasthas/
  //     karakas via CONDITION_FACET_URI, default facet `dignity`, register_p1_ganita.ts
  //     ~L663) — the IDENTICAL case to ganita_structural_get. It never calls
  //     get_condition_composite (get_condition_composite.ts's own header states its data is
  //     NOT what condition_get's facets read); 4 of the 6 consuming Vidhi primitives
  //     (karaka_condition, chara_karaka_read, arudha_read, karakamsa_read) target concepts
  //     absent from ga_condition_composite's columns entirely. A static URI here would
  //     silently serve the WRONG data — the same §N.6/B.10 anti-laundering failure.
  //     REJECTED at verify (RESOLVER_RULINGS.md RC-10-003); DEFERRED, needs facet/mode-aware
  //     routing in compileFloorForPlan, not a hand-map entry.
  //   kala_bundle_get (RC-14: renamed from kala_temporal_bundle) — sidecar composite with NO
  //     retrieval-registry capability at all (platform-mcp/src/server.ts's own "KEYSTONE
  //     REQUEST" comment: "has no registry primitive... REQUEST to retrieval fork: expose
  //     'kala_temporal_bundle' capability"). Requires building a new registry capability,
  //     out of a bridge-extension's scope.
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

/**
 * Token budget per compiled-floor band. Exported (not module-private) so any
 * consumer needing the same per-band budget — `plan_bridge.ts`'s
 * `fromCompiledFloorItem` is the first — REFERENCES this value instead of
 * copying it. A copied literal can drift from this source silently (§N.7
 * item 3: "no wrapper-local constant may shadow an L1-computed value... a
 * constant can drift from its source; a reference cannot" — proven true here
 * when a M4-class edit to this value passed 1613 tests against a stale copy).
 */
export const BAND_BUDGET = { acharya_floor: 600, machine_band: 400 } as const
/** Priority per compiled-floor band. Same drift-proofing rationale as BAND_BUDGET above. */
export const BAND_PRIORITY = { acharya_floor: 1, machine_band: 2 } as const

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

/**
 * tool_name_bridge.ts — Legacy tool-name → registry URI mapping + MCP surgical whitelist
 * =======================================================================================
 * D7 chat-channel migration (§3 — caller repoint; §4 — primitives_registry retirement).
 *
 * Maps every legacy `lib/retrieve` tool name to its registry capability URI.
 * Used by `getToolByName()` which replaces `getTool()` from `lib/retrieve/index`.
 *
 * Also owns the MCP surgical whitelist (SURGICAL_TOOLS, MCP_TO_RETRIEVAL_TOOL,
 * isAllowedSurgicalTool) — moved here from `lib/mcp/primitives_registry` as part
 * of D7 Step 4 retirement. primitives_registry.ts is DELETED; import from here.
 *
 * Design contract:
 *   - chart_id is NEVER defaulted here; callers must supply it explicitly.
 *   - audience_tier is STRIPPED — registry capabilities are universal-access.
 *   - If a tool name has no URI mapping, getToolByName returns undefined
 *     (same behaviour as the old getTool() for unknown names).
 */

import { getCapability } from './index'
import type { CapabilityDescriptor, CapabilityUri } from './types'
import type { ToolBundle, ToolBundleResult } from '@/lib/retrieval/shared_types'
import crypto from 'crypto'
import { resolveGeneratedToolUri } from './generated_web_tool_bridge'

/**
 * W5 L1 (CR-118 fast-fail fix): a `toolName` that is ALREADY a registry URI
 * (starts with `marsys://`) resolves directly via `getCapability()`, bypassing
 * `TOOL_NAME_TO_URI` entirely.
 *
 * Real bug this fixes: `compiled_floor_adapter.ts`'s `ensureB11WholeChartReadFloor`
 * (called from both `consult/route.ts` and the real `prashna_ask/route.ts`) pushes
 * literal registry URIs as `tool_name`
 * — e.g. `'marsys://tool/L2/query_signals'` — under the assumption that a registry
 * URI is a valid, self-resolving tool identifier. It never was: `TOOL_NAME_TO_URI`
 * only maps legacy *names* (keys) to URIs (values); a URI was never a key, so
 * `getToolByName('marsys://tool/L2/query_signals')` silently returned `undefined`
 * and consult/route.ts's tool-fetch loop (`if (!t) return null`) dropped the tool
 * with NO error and NO result — the B.11 whole-chart-read floor's own MSR-signals
 * tool (the exact capability `msr_sql` already resolves correctly under its OWN
 * name) never actually executed when injected via this path. This is the
 * `msr_sql` web-channel defect named in the W5 brief, and one instance of the
 * CR-118 fast-fail class. Fixed structurally (any URI-shaped identifier now
 * resolves) rather than by renaming the two call sites — future callers that
 * push a registry URI directly (the generated web-tool bridge below does this
 * routinely) get correct behaviour for free.
 */
function isCapabilityUri(toolName: string): boolean {
  return toolName.startsWith('marsys://')
}

// ── Tool-name → URI map ───────────────────────────────────────────────────────

/**
 * Authoritative map from legacy lib/retrieve tool names to registry URIs.
 * All entries verified against D7_CAPABILITY_URIS + L0/L1/L2 layer registrations.
 *
 * Tools NOT in RETRIEVAL_TOOLS (planner-injected strings that returned undefined
 * from getTool()): pattern_register, cgm_graph_walk,
 * resonance_register, cluster_atlas, contradiction_register, temporal, kp_query,
 * query_kp_ruling_planets, query_ucn_walk, query_cdlm_lookup, query_rm_walk,
 * query_jaimini_drishti, timeline_query, query_signal_state — these also return
 * undefined from getToolByName() (no change in behaviour).
 *
 * R5 W2 corpus lane (P7 fix, part 2 of 2): `vector_search` USED to be in the
 * above undefined-forever list too — even after the 401 auth-header bug was
 * fixed (both proxy helpers now send the correct 3-header pattern — see
 * registry_bridge.ts + register_p1_aliases.ts), the primitives route would
 * still have 500'd with "Retrieval tool not found in registry: vector_search"
 * because no URI was ever mapped for it. `vector_search` now resolves to the
 * SAME capability `classical_text_search`/`search_classical_texts`/
 * `read_classical_text` already use — query_classical_texts.ts, which is the
 * corpus's one real hybrid vector+keyword search implementation (design doc
 * §3 CORPUS idiom / instrument #13 `ref_search`). Deliberately reusing the
 * existing capability rather than standing up a second implementation.
 */
export const TOOL_NAME_TO_URI: Record<string, CapabilityUri> = {
  // L2 Bodha
  msr_sql: 'marsys://tool/L2/query_signals',
  query_msr_aggregate: 'marsys://tool/L2/query_signals',      // alias → same cap
  classical_attribution_lookup: 'marsys://tool/L2/classical_attribution_lookup',

  // L1 Gaṇita
  chart_facts_query: 'marsys://tool/L1/chart_facts_query',
  compute_natal_positions: 'marsys://tool/L1/get_positions',
  query_dasha_periods: 'marsys://tool/L1/get_dashas',
  query_special_lagnas: 'marsys://tool/L1/get_sensitive_points',
  query_varshaphala: 'marsys://tool/L1/get_tajik',
  divisional_query: 'marsys://tool/L1/get_divisionals',
  // WP-1.3(d) / F-L10-021: lel_query serves the user-authored Life Event Log
  // (life_events table, 57 rows for the native), NOT the Bodha MSR signals surface.
  // The old mapping pointed at L2/query_signals whose lel_enabled filter selects
  // lel_origin=true signals — of which there are ZERO — so lel_query returned nothing.
  lel_query: 'marsys://tool/L5/lel_query',
  // DOCTRINE-WAVES D-4b Lane B-5 (= BRIEF_D4.md v2.0 Lane C-6): mechanism_retrodiction
  // surface — LEL events joined to the classical dasha-lord/house-activation mechanism,
  // CONFIRMATION ONLY, never prediction input.
  mechanism_retrodiction_get: 'marsys://tool/L5/mechanism_retrodiction_get',
  query_panchanga: 'marsys://tool/L1/get_panchanga',

  // L0 Brahmagyan — ontology / entity resolution
  resolve_entity: 'marsys://tool/L0/resolve_entity',
  list_entities: 'marsys://tool/L0/list_entities',

  // L0 Brahmagyan — classical texts
  read_classical_text: 'marsys://tool/L0/query_classical_texts',
  search_classical_texts: 'marsys://tool/L0/query_classical_texts',
  classical_text_search: 'marsys://tool/L0/query_classical_texts',
  vector_search: 'marsys://tool/L0/query_classical_texts',       // R5 W2 (P7): corpus hybrid search
  read_chapter: 'marsys://tool/L0/read_chapter',
  list_classical_texts: 'marsys://tool/L0/list_classical_texts',
  find_verses_about: 'marsys://tool/L0/find_verses_about',

  // L0 Brahmagyan — sutravali
  query_rules: 'marsys://tool/L0/query_sutravali_rules',
  query_rules_for_planet: 'marsys://tool/L0/query_sutravali_rules_for_planet',
  read_rule: 'marsys://tool/L0/read_sutravali_rule',
  list_rules_by_text: 'marsys://tool/L0/list_sutravali_rules_by_text',

  // L0 Brahmagyan — remedies
  query_remedies: 'marsys://tool/L0/query_remedy_corpus',
  remedial_codex_query: 'marsys://tool/L0/query_remedy_corpus',
  query_remedies_for_chart: 'marsys://tool/L0/query_remedies_for_chart',
  list_remedies_by_category: 'marsys://tool/L0/list_remedies_by_category',
  read_remedy: 'marsys://tool/L0/read_remedy',
  query_tantric_remedies: 'marsys://tool/L0/query_tantric_remedies',
  query_remedies_by_planet: 'marsys://tool/L0/query_remedies_by_planet',
  query_mantras: 'marsys://tool/L0/query_mantras',

  // L0 Brahmagyan — ephemeris / transit
  query_ephemeris: 'marsys://tool/L0/query_planet_position',
  query_transit_event: 'marsys://tool/L0/query_planet_transit',

  // L3 Kāla — live compute service wrappers
  call_transit_search:    'marsys://tool/L3/call_transit_search',
  call_dasha_eligibility: 'marsys://tool/L3/call_dasha_eligibility',
  // F-11: ṢAḌ-DARŚANA W3 item 37 — paddhati convention profile (per-chart config, migrations 533/534/537)
  query_kala_paddhati_profile: 'marsys://tool/L3/query_kala_paddhati_profile',

  // L4 Phala
  query_remedy_program: 'marsys://tool/L4/query_remedy_program',
  // R5.1 C3 fix: query_muhurat previously mapped to L0/query_planet_transit — the
  // WRONG capability (it requires a `planet` param muhurta_finder never supplies,
  // and has nothing to do with electional muhurta search). Repointed to the real
  // PH-4-4 electional finder, which now reads real panchanga_daily rows (migration
  // 427_panchanga_daily_reprovision.sql) instead of always falling back to
  // hard-coded placeholder panchanga values (brahmagyan/phala/muhurta.py fix).
  query_muhurat: 'marsys://tool/L4/query_muhurat',

  // L5 Mīmāṃsā
  // R6 0b-deadtools (R-14): mimamsa_calibration_get 400'd outright — the underlying
  // retrieval-tool name 'query_calibration' had no URI mapping here, so
  // isAllowedSurgicalTool()/getToolByName() both failed closed. This is the correct,
  // schema-current L5 capability (mimamsa_calibration/reliability/multipliers/qa_eval) —
  // distinct from the legacy Python-sidecar-backed MCP tool of the same display name
  // registered in mimamsa_outcome.ts (record_outcome/query_calibration), which is fixed
  // separately for its own schema drift.
  query_calibration: 'marsys://tool/L5/query_calibration',

  // ── ṢAḌ-DARŚANA W3 items 36/41 — the muhūrta election substrate read path ────
  // Two L0 Brahmagyan readers over the global tables PR #930 landed
  // (bg_muhurta_lattice; bg_parihara_rules + bg_muhurta_activity_rules +
  // bg_muhurta_factor_census). They are pure readers: the lattice-annotation /
  // parihāra-adjudication / Pareto / gap-report ENGINE over them is single-sourced
  // in platform-mcp `lib/kala_lattice_query.ts` (ONE-ENGINE RULE — ELECT and
  // YAJÑA-SETU share it, neither owns a second copy).
  query_muhurta_lattice: 'marsys://tool/L0/query_muhurta_lattice',
  query_parihara_graph:  'marsys://tool/L0/query_parihara_graph',

  // ── WP-1.7 (LCA-1 / LCA-13) — local-bench whitelist resolution ──────────────
  // These 5 retrieval-tool names were whitelisted for MCP surgical dispatch but
  // had NO TOOL_NAME_TO_URI entry → getToolByName() returned undefined → the local
  // /api/mcp/primitives route 500'd on every call ("Retrieval tool not found in
  // registry"). Each name below resolves to a REAL registered registry capability
  // (verified against src/lib/retrieval/registry/layers/**). The OTHER 14
  // formerly-whitelisted names had no backing registry capability and were REMOVED
  // from SURGICAL_TOOLS / MCP_TO_RETRIEVAL_TOOL (see the WP-1.7 removal note below).
  // The whitelist_resolution_invariant.test.ts guard fails CI if any
  // MCP_TO_RETRIEVAL_TOOL value ever again lacks a resolvable capability.
  cgm_graph_walk: 'marsys://tool/L2/traverse_chart_graph',        // CGM subgraph walk; deployed twin get_cgm_subgraph. primitives route already wires node_id/hops → graph_seed_hints/depth for this exact name.
  contradiction_register: 'marsys://tool/L2/query_contradictions', // real L2 Bodha contradiction surface
  temporal: 'marsys://tool/L3/query_temporal_activation',          // real L3 Kāla temporal-activation capability
  query_tara_balam: 'marsys://tool/L1/get_tara_chandra_bala',      // real L1 Gaṇita tara/chandra bala baseline (one cap serves both balas)
  query_chandra_balam: 'marsys://tool/L1/get_tara_chandra_bala',   // same L1 cap — chandra bala facet

  // ── WP-1.3(a) (LCA-19) — serve the computed-but-unserved Lane-10 assets ──────
  // Each name below resolves to a NEW (or newly un-stubbed) registry capability that
  // reads a chart-scoped table which was computed and stored but had no deployed
  // serving path. Bounded serving (LIMIT + disclosed total) is enforced in each handler.
  get_medical_indications:    'marsys://tool/L1/get_medical_indications',    // F-L10-001 ga_medical
  get_vastu_directions:       'marsys://tool/L1/get_vastu_directions',       // F-L10-002 ga_vastu_planet_direction_map
  get_yoga_firings:           'marsys://tool/L1/get_yoga_firings',           // F-L10-003 ga_yoga_firings (bhanga + activation detail)
  query_cdlm_summary:         'marsys://tool/L2/query_cdlm_summary',         // F-L10-004 bodha_cdlm_chart_summary
  query_cgm_motifs:           'marsys://tool/L2/query_cgm_motifs',           // F-L10-005 bodha_cgm_motifs
  query_cgm_paths:            'marsys://tool/L2/query_cgm_paths',            // F-L10-006 bodha_cgm_paths
  query_chart_gestalt:        'marsys://tool/L2/query_chart_gestalt',        // F-L10-007 bodha_chart_gestalt
  query_dasha_dossier:        'marsys://tool/L3/query_dasha_dossier',        // F-L10-009 kala_avadhi
  query_temporal_view:        'marsys://tool/L3/query_temporal_view',        // F-L10-012 kala_darshana (un-stubbed)
  query_convergence_windows:  'marsys://tool/L3/query_convergence_windows',  // F-L10-014 kala_convergence (rigor stratum)
  query_activation_waveform:  'marsys://tool/L3/query_activation_waveform',  // F-L10-015 kala_taranga (budget: summary+drill)
  query_obstruction_periods:  'marsys://tool/L3/query_obstruction_periods',  // F-L10-018 kala_obstruction (un-stubbed)
  query_spillover_cascades:   'marsys://tool/L4/query_spillover_cascades',   // F-L10-027 phala_sankrama
  // WP-1.3j (W1-FOLLOWUP): populated-but-unserved L2 Bodha assets — real rows, no writer needed.
  query_discoveries:          'marsys://tool/L2/query_discoveries',          // F-0129..0137 bodha_discoveries
  query_pratijna:             'marsys://tool/L2/query_pratijna',             // F-0156,0176 bodha_pratijna
  query_question_lenses:      'marsys://tool/L2/query_question_lenses',      // F-0156,0176 bodha_question_lenses
  query_rm_prescriptions:     'marsys://tool/L2/query_rm_prescriptions',     // F-0161,0165,0174 bodha_rm_remedy_prescriptions
  query_rm_resonances:        'marsys://tool/L2/query_rm_resonances',        // F-0161,0165,0174 bodha_rm_resonances
  // SARVA-SIDDHI W-4 / CR-24: bodha_mechanisms first-class serving face.
  query_mechanisms:           'marsys://tool/L2/query_mechanisms',           // CR-24 bodha_mechanisms (bo_yantra_mechanism)
}

// ── ToolBundle adapter ────────────────────────────────────────────────────────

/**
 * Wrap a registry capability's handler result into the legacy ToolBundle shape.
 *
 * This is the ONLY place the ToolBundle ↔ ToolResult shape conversion lives.
 * When lib/retrieve is retired (Step 4), this adapter is removed along with it.
 *
 * Content normalisation rules:
 *   - If handler returns an object with a `results` array → use it directly (already ToolBundle-shaped).
 *   - If handler returns an object with `content` (ToolResult) → wrap in a single-item results array.
 *   - If handler returns a plain object → JSON-serialise into content.
 *
 * Error contract (T1 anti-laundering — audit §6 Cross-cutting):
 *   - A *thrown* sql/programming error from the handler is a bug, not data. It is
 *     NOT swallowed into an empty bundle; it propagates so callers' existing
 *     try/catch (consult → step_error, MCP → 500 envelope) surface it.
 *   - A handler that *returns* `{ is_error: true, ... }` is likewise surfaced as a
 *     thrown error, never laundered into a normal (empty-looking) success bundle.
 *   - A legitimate empty result (handler returns `[]` / `{results:[]}` / null with
 *     no `is_error` flag) stays a successful bundle with zero results.
 */
function resultHash(data: unknown): string {
  return 'sha256:' + crypto.createHash('sha256').update(JSON.stringify(data)).digest('hex')
}

function toToolBundleResults(content: unknown): ToolBundleResult[] {
  if (content == null) return []

  // Already an array of ToolBundleResult-shaped objects
  if (Array.isArray(content)) {
    return content.map((item: unknown) => {
      if (typeof item === 'object' && item !== null && 'content' in item) {
        return item as ToolBundleResult
      }
      return { content: typeof item === 'string' ? item : JSON.stringify(item) }
    })
  }

  // Object with results array (already ToolBundle-shaped response from a handler)
  if (typeof content === 'object' && 'results' in content) {
    const results = (content as Record<string, unknown>)['results']
    if (Array.isArray(results)) return results as ToolBundleResult[]
  }

  // Single ToolResult (content: string | object)
  if (typeof content === 'object' && 'content' in content) {
    const inner = (content as Record<string, unknown>)['content']
    const str = typeof inner === 'string' ? inner : JSON.stringify(inner)
    return [{ content: str }]
  }

  // Fallback — serialize entire object
  return [{ content: typeof content === 'string' ? content : JSON.stringify(content) }]
}

/**
 * Convert a registry CapabilityHandler result to the legacy ToolBundle shape.
 * Called by getToolByName().retrieve().
 */
async function capabilityResultToToolBundle(
  toolName: string,
  handlerPromise: Promise<unknown>,
  params: object,
  t0: number,
): Promise<ToolBundle> {
  let result: unknown
  try {
    result = await handlerPromise
  } catch (err) {
    // T1 anti-laundering: a thrown sql/programming error is a bug, NOT a legitimate
    // empty result. Re-throw (annotated) so callers' existing catch surfaces it as a
    // tool error rather than returning an indistinguishable empty success bundle.
    const msg = err instanceof Error ? err.message : String(err)
    throw new Error(`tool '${toolName}' handler threw: ${msg}`, { cause: err })
  }

  // T1 anti-laundering: a handler that *returns* an error object (is_error: true)
  // must also surface as an error, not be flattened into a normal results array
  // where an empty-but-failed result looks identical to a legitimate empty success.
  if (
    typeof result === 'object' &&
    result !== null &&
    (result as Record<string, unknown>)['is_error'] === true
  ) {
    const errContent = (result as Record<string, unknown>)['content']
    const detail =
      typeof errContent === 'string' ? errContent : JSON.stringify(errContent)
    throw new Error(`tool '${toolName}' returned an error result: ${detail}`)
  }

  const results = toToolBundleResults(result)
  return {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: toolName,
    tool_version: '1.0',
    invocation_params: params,
    results,
    served_from_cache: false,
    latency_ms: Date.now() - t0,
    result_hash: resultHash(results),
    schema_version: '1.0',
  }
}

// ── getToolByName — drop-in replacement for getTool() ──────────────────────────

/**
 * Registry-backed replacement for `getTool(name)` from `lib/retrieve/index`.
 *
 * Returns a RetrievalTool-compatible object whose `.retrieve(plan, params)` method:
 *   1. Resolves the tool name → registry URI via TOOL_NAME_TO_URI.
 *   2. Calls `capability.handler(args, { chart_id })` — no audience_tier passed.
 *   3. Wraps the ToolResult into the legacy ToolBundle shape for backward compat.
 *
 * Returns undefined (same as getTool()) if the tool name has no URI mapping.
 *
 * chart_id is extracted from plan if present. Never defaulted.
 */
export function getToolByName(toolName: string): {
  name: string
  version: string
  retrieve(plan: Record<string, unknown>, params?: Record<string, unknown>): Promise<ToolBundle>
} | undefined {
  const uri = resolveToolUri(toolName)
  if (!uri) return undefined

  const cap: CapabilityDescriptor | undefined = getCapability(uri)
  if (!cap) return undefined

  return {
    name: toolName,
    version: '1.0',
    async retrieve(plan: Record<string, unknown>, params?: Record<string, unknown>): Promise<ToolBundle> {
      const t0 = Date.now()
      // Extract chart_id from plan — never default it
      const chartId = typeof plan['chart_id'] === 'string' ? plan['chart_id'] : undefined

      // Build handler args: merge params with chart_id context (no audience_tier)
      const args: Record<string, unknown> = {
        ...(params ?? {}),
      }

      // For per_chart capabilities, chart_id is required
      if (cap.scope === 'per_chart' && chartId) {
        args['chart_id'] = chartId
      }

      // Pass plan-level hints that handlers may use (forward_looking, domains, etc.)
      // but do NOT pass audience_tier — it is stripped per DG1 ruling.
      if (typeof plan['forward_looking'] === 'boolean') {
        args['forward_looking'] = args['forward_looking'] ?? plan['forward_looking']
      }
      if (Array.isArray(plan['domains']) && !args['domains']) {
        args['domains'] = plan['domains']
      }

      return capabilityResultToToolBundle(
        toolName,
        cap.handler(args, chartId ? { chart_id: chartId } : undefined),
        params ?? {},
        t0,
      )
    },
  }
}

/**
 * Check whether a registry capability is registered for a given tool name.
 * Replaces `getTool(name) !== undefined` checks.
 */
export function hasToolByName(toolName: string): boolean {
  const uri = resolveToolUri(toolName)
  if (!uri) return false
  return getCapability(uri) !== undefined
}

/**
 * Resolve a tool name to its registry URI.
 *
 * Resolution order (W5 L1 — generated-projection bridge cutover):
 *   1. `toolName` is already a registry URI (`marsys://...`) → resolved directly
 *      (CR-118 fast-fail fix — see `isCapabilityUri` doc comment above).
 *   2. `toolName` is a hand-curated legacy alias in `TOOL_NAME_TO_URI` — these
 *      encode real migration history (D7 retirement, WP-1.x fixes, R6
 *      0b-deadtools) that cannot be mechanically re-derived from the catalog,
 *      so they take precedence over the generated projection.
 *   3. Fall back to `resolveGeneratedToolUri()` — the BUILD-TIME GENERATED
 *      projection (`platform/scripts/manifest/generate_projections.ts` →
 *      `web_tool_bridge.generated.json`) sourced from `getCatalog()` (every
 *      live capability's own `.name`) plus `canonical_faces.json`'s
 *      `deprecated_aliases`. This is what widens coverage as the catalog grows
 *      without hand-editing this file — the mechanism the W5 brief calls for
 *      ("the web channel's tool bridge becomes a generated projection of the
 *      compiled catalog... this is the mechanism that takes floor adoption
 *      from ~10%... to 100%").
 */
export function resolveToolUri(toolName: string): CapabilityUri | undefined {
  if (isCapabilityUri(toolName)) return toolName
  return TOOL_NAME_TO_URI[toolName] ?? resolveGeneratedToolUri(toolName)
}

// ── MCP Surgical Whitelist ────────────────────────────────────────────────────
//
// Moved here from lib/mcp/primitives_registry.ts (D7 Step 4 retirement).
// Single source of truth for which retrieval tools are exposed as MCP primitives.
// The dispatcher (/api/mcp/primitives/[tool]/route.ts) uses isAllowedSurgicalTool()
// to reject tool names not in this whitelist with {ok:false, error:{class:"validation"}}.
//
// MCP arch §3.7 — 14 Tier 3 primitives + 1 Tier 4 raw-asset read + TR Wave + UDA Campaign.

// WP-1.7 (LCA-1 / LCA-13) — 14 vestigial names REMOVED from this whitelist because
// they had NO backing registry capability (getToolByName undefined → local 500). Their
// concepts are either served by a canonical deployed twin or never existed:
//   multi_school_signal_lookup (legacy lib/tools impl, never bridged to the registry;
//       cross_school_lookup MCP name dropped — see follow-up F-WP17-1),
//   jaimini_chara_dasha, jaimini_chara_dasha_full (TR Wave Class B/C stubs — never built),
//   kp_query, query_kp_ruling_planets (no KP engine registered),
//   pattern_register, resonance_register, cluster_atlas (no registered cap),
//   query_ucn_walk, query_cdlm_lookup, query_rm_walk (no walk/lookup cap; UCN retired→UCD),
//   query_jaimini_drishti (no cap), timeline_query (L3 temporal is served by 'temporal'),
//   query_signal_state (query_signals is served by 'msr_sql').
// cgm_graph_walk / temporal / contradiction_register / query_tara_balam /
// query_chandra_balam were RETAINED — they now resolve (see TOOL_NAME_TO_URI WP-1.7 block).

/** The underlying retrieval tool names exposed as MCP primitives. */
export const SURGICAL_TOOLS = [
  'chart_facts_query',
  'msr_sql',
  'query_dasha_periods',
  'query_panchanga',
  'query_ephemeris',
  'query_transit_event',
  'lel_query',
  // DOCTRINE-WAVES D-4b Lane B-5: mechanism_retrodiction surface (CONFIRMATION ONLY).
  'mechanism_retrodiction_get',
  'vector_search',
  'cgm_graph_walk',
  'classical_text_search',
  // TR Wave Class A retrieval tools (engines existed pre-PR-#159)
  'query_varshaphala',
  'divisional_query',
  'remedial_codex_query',
  'query_muhurat',
  // Tara/Chandra bala — resolved via TOOL_NAME_TO_URI WP-1.7 block (get_tara_chandra_bala)
  'query_tara_balam',
  'query_chandra_balam',
  // UDA Campaign — retained portal-native tools that resolve to a real capability
  'temporal',
  'contradiction_register',
  // F-015: L0 entity resolution tools (were missing from whitelist; primitives route is POST-only)
  'resolve_entity',
  'list_entities',
  // F-004: Remedy corpus tools (were missing from whitelist; caused "not in surgical whitelist" errors)
  'query_remedies_for_chart',
  'list_remedies_by_category',
  'read_remedy',
  'query_tantric_remedies',
  'query_remedies_by_planet',
  'query_mantras',
  // F-016: L4 Phala mitigation_map primitive (query_remedy_program is the retrieval tool)
  'query_remedy_program',
  // R6 0b-deadtools (R-14): L5 Mīmāṃsā calibration scorecard (mimamsa_calibration_get alias)
  'query_calibration',
  // WP-1.3(a) (LCA-19): computed-but-unserved Lane-10 assets, now with serving paths.
  'get_medical_indications',
  'get_vastu_directions',
  'get_yoga_firings',
  'query_cdlm_summary',
  'query_cgm_motifs',
  'query_cgm_paths',
  'query_chart_gestalt',
  'query_dasha_dossier',
  'query_temporal_view',
  'query_convergence_windows',
  'query_activation_waveform',
  'query_obstruction_periods',
  'query_spillover_cascades',
  // WP-1.3j (W1-FOLLOWUP): populated-but-unserved L2 Bodha assets now with serving paths.
  'query_discoveries',
  'query_pratijna',
  'query_question_lenses',
  'query_rm_prescriptions',
  'query_rm_resonances',
  // SARVA-SIDDHI W-4 / CR-24: bodha_mechanisms first-class serving face.
  'query_mechanisms',
  // ṢAḌ-DARŚANA W3 items 36/41: muhūrta election substrate readers (L0, global).
  'query_muhurta_lattice',
  'query_parihara_graph',
  // F-02/F-07: four classical-text tools missing from MCP whitelist
  'read_chapter',
  'list_classical_texts',
  'find_verses_about',
  // F-11: ṢAḌ-DARŚANA W3 item 37 — paddhati convention profile (L3 Kāla, per-chart)
  'query_kala_paddhati_profile',
] as const

export type SurgicalToolName = (typeof SURGICAL_TOOLS)[number]

/**
 * Maps MCP-facing primitive tool names (as Claude calls them) to the underlying
 * retrieval tool names. Moved from lib/mcp/primitives_registry (D7 Step 4).
 */
export const MCP_TO_RETRIEVAL_TOOL: Record<string, SurgicalToolName> = {
  // Original 11
  query_chart_facts: 'chart_facts_query',
  query_signals: 'msr_sql',
  query_dasha_periods: 'query_dasha_periods',
  query_panchanga: 'query_panchanga',
  query_ephemeris: 'query_ephemeris',
  query_transit_event: 'query_transit_event',
  lel_query: 'lel_query',
  mechanism_retrodiction_get: 'mechanism_retrodiction_get',
  vector_search: 'vector_search',
  get_cgm_subgraph: 'cgm_graph_walk',
  // WP-1.7 (LCA-1/LCA-13): cross_school_lookup REMOVED — its target
  // multi_school_signal_lookup is a legacy lib/tools implementation never bridged
  // to a registry capability (no TOOL_NAME_TO_URI entry possible without a new cap).
  // Follow-up F-WP17-1: re-bridge by registering a registry capability wrapping
  // lib/tools/multi_school_signal_lookup.ts if the surgical primitive is wanted locally.
  read_classical_text: 'classical_text_search',
  read_chapter: 'read_chapter',
  list_classical_texts: 'list_classical_texts',
  find_verses_about: 'find_verses_about',
  search_classical_texts: 'classical_text_search',   // F-02/F-07: was missing from MCP whitelist
  // TR Wave additions (PR #159 — Class A: existing retrieval engines)
  query_varshphal: 'query_varshaphala',
  query_divisional_chart: 'divisional_query',
  query_remedial_mantras: 'remedial_codex_query',
  muhurta_finder: 'query_muhurat',
  // TR Wave Class A — retrieval-name aliases
  query_varshaphala: 'query_varshaphala',
  divisional_query: 'divisional_query',
  remedial_codex_query: 'remedial_codex_query',
  query_muhurat: 'query_muhurat',
  // Tara/Chandra bala — now resolve (TOOL_NAME_TO_URI → get_tara_chandra_bala)
  query_tara_balam: 'query_tara_balam',
  query_chandra_balam: 'query_chandra_balam',
  // WP-1.7 (LCA-1/LCA-13): jaimini_chara_dasha[_full] REMOVED — TR Wave Class B/C stubs,
  // never built, no backing capability (getToolByName was undefined → 500).
  // UDA Campaign — retained portal-native tools that resolve to a real capability:
  msr_sql: 'msr_sql',
  temporal: 'temporal',                                   // → L3/query_temporal_activation
  contradiction_register: 'contradiction_register',       // → L2/query_contradictions
  // WP-1.7 (LCA-1/LCA-13): the following 12 UDA/legacy names were REMOVED — no backing
  // registry capability, so getToolByName() returned undefined and the primitives route
  // 500'd. Removing them makes isAllowedSurgicalTool() reject the name with a clean 400
  // {class:"validation"} instead of a 500, and the deployed twin remains canonical:
  //   cross_school_lookup (multi_school_signal_lookup), kp_query, query_kp_ruling_planets,
  //   pattern_register, resonance_register, cluster_atlas, query_ucn_walk,
  //   query_cdlm_lookup, query_rm_walk, query_jaimini_drishti, timeline_query,
  //   query_signal_state.
  // F-015: L0 entity resolution tools exposed as MCP primitives (called via POST now)
  resolve_entity: 'resolve_entity',
  list_entities: 'list_entities',
  // F-004: Remedy corpus tools exposed as MCP primitives
  query_remedies: 'remedial_codex_query',
  query_remedies_for_chart: 'query_remedies_for_chart',
  list_remedies_by_category: 'list_remedies_by_category',
  read_remedy: 'read_remedy',
  query_tantric_remedies: 'query_tantric_remedies',
  query_remedies_by_planet: 'query_remedies_by_planet',
  query_mantras: 'query_mantras',
  // F-016: mitigation_map → query_remedy_program (L4 Phala phala_mitigation retrieval tool)
  mitigation_map: 'query_remedy_program',
  // R6 0b-deadtools (R-14): mimamsa_calibration_get alias → L5 query_calibration capability
  query_calibration: 'query_calibration',
  // WP-1.3(a) (LCA-19): MCP-facing names for the now-served computed-but-unserved assets.
  ganita_medical_get:          'get_medical_indications',   // F-L10-001
  ganita_vastu_get:            'get_vastu_directions',      // F-L10-002
  ganita_yoga_firings_get:     'get_yoga_firings',          // F-L10-003
  bodha_cdlm_summary_get:      'query_cdlm_summary',        // F-L10-004
  bodha_cgm_motifs_get:        'query_cgm_motifs',          // F-L10-005
  bodha_cgm_paths_get:         'query_cgm_paths',           // F-L10-006
  bodha_chart_gestalt_get:     'query_chart_gestalt',       // F-L10-007
  kala_dasha_dossier_get:      'query_dasha_dossier',       // F-L10-009
  kala_darshana_get:           'query_temporal_view',       // F-L10-012
  kala_convergence_get:        'query_convergence_windows', // F-L10-014
  kala_activation_waveform_get:'query_activation_waveform', // F-L10-015
  kala_obstruction_get:        'query_obstruction_periods', // F-L10-018
  phala_spillover_get:         'query_spillover_cascades',  // F-L10-027
  // WP-1.3j (W1-FOLLOWUP): MCP-facing names for the now-served bodha assets.
  bodha_discoveries_get:       'query_discoveries',         // F-0129..0137
  bodha_pratijna_get:          'query_pratijna',            // F-0156,0176
  bodha_question_lenses_get:   'query_question_lenses',     // F-0156,0176
  bodha_rm_prescriptions_get:  'query_rm_prescriptions',    // F-0161,0165,0174
  bodha_rm_resonances_get:     'query_rm_resonances',       // F-0161,0165,0174
  // SARVA-SIDDHI W-4 / CR-24: MCP-facing name for the bodha_mechanisms serving face.
  bodha_mechanisms_get:        'query_mechanisms',          // CR-24 bodha_mechanisms
  // ṢAḌ-DARŚANA W3 items 36/41: MCP-facing names for the muhūrta election substrate.
  // Consumed by platform-mcp's `lib/kala_lattice_query.ts` (the contender-lattice engine
  // behind kala_elect_get); global scope, so no chart authorization applies.
  query_muhurta_lattice:       'query_muhurta_lattice',     // item 36 lattice rows
  query_parihara_graph:        'query_parihara_graph',      // items 36/41 parihāra + census
  // F-11: ṢAḌ-DARŚANA W3 item 37 — paddhati profile (kala_sky_pattern.ts fetchPaddhatiProfile)
  query_kala_paddhati_profile: 'query_kala_paddhati_profile',
}

/**
 * Type guard: returns true if the given MCP tool name is in the surgical
 * primitive whitelist. Uses Object.hasOwn() to avoid prototype-pollution
 * false positives (RT-06 guard).
 */
export function isAllowedSurgicalTool(
  mcpToolName: string
): mcpToolName is keyof typeof MCP_TO_RETRIEVAL_TOOL {
  return Object.hasOwn(MCP_TO_RETRIEVAL_TOOL, mcpToolName)
}

/**
 * Returns true if the MCP tool name maps to a per_chart capability.
 * Used by the primitives route to decide whether to enforce authorizeChartAccess.
 * Returns false for global/agnostic tools and for unknown tool names.
 */
export function isPerChartPrimitive(mcpToolName: string): boolean {
  const retrievalName = MCP_TO_RETRIEVAL_TOOL[mcpToolName]
  if (!retrievalName) return false
  const uri = TOOL_NAME_TO_URI[retrievalName]
  if (!uri) return false
  const cap = getCapability(uri)
  return cap?.scope === 'per_chart'
}

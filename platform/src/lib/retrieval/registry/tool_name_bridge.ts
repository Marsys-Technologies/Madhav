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

// ── Tool-name → URI map ───────────────────────────────────────────────────────

/**
 * Authoritative map from legacy lib/retrieve tool names to registry URIs.
 * All entries verified against D7_CAPABILITY_URIS + L0/L1/L2 layer registrations.
 *
 * Tools NOT in RETRIEVAL_TOOLS (planner-injected strings that returned undefined
 * from getTool()): vector_search, pattern_register, cgm_graph_walk,
 * resonance_register, cluster_atlas, contradiction_register, temporal, kp_query,
 * query_kp_ruling_planets, query_ucn_walk, query_cdlm_lookup, query_rm_walk,
 * query_jaimini_drishti, timeline_query, query_signal_state — these also return
 * undefined from getToolByName() (no change in behaviour).
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
  lel_query: 'marsys://tool/L2/query_signals',                // lel_enabled flag path
  query_panchanga: 'marsys://tool/L1/get_panchanga',

  // L0 Brahmagyan — classical texts
  read_classical_text: 'marsys://tool/L0/query_classical_texts',
  search_classical_texts: 'marsys://tool/L0/query_classical_texts',
  classical_text_search: 'marsys://tool/L0/query_classical_texts',
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
  query_muhurat: 'marsys://tool/L0/query_planet_transit',     // nearest equivalent; sidecar path

  // L3 Kāla — live compute service wrappers
  call_transit_search:    'marsys://tool/L3/call_transit_search',
  call_dasha_eligibility: 'marsys://tool/L3/call_dasha_eligibility',
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
  const uri = TOOL_NAME_TO_URI[toolName]
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
  const uri = TOOL_NAME_TO_URI[toolName]
  if (!uri) return false
  return getCapability(uri) !== undefined
}

/**
 * Resolve a legacy tool name to its registry URI.
 * Used by the MCP primitives route (replaces MCP_TO_RETRIEVAL_TOOL lookup chain).
 */
export function resolveToolUri(toolName: string): CapabilityUri | undefined {
  return TOOL_NAME_TO_URI[toolName]
}

// ── MCP Surgical Whitelist ────────────────────────────────────────────────────
//
// Moved here from lib/mcp/primitives_registry.ts (D7 Step 4 retirement).
// Single source of truth for which retrieval tools are exposed as MCP primitives.
// The dispatcher (/api/mcp/primitives/[tool]/route.ts) uses isAllowedSurgicalTool()
// to reject tool names not in this whitelist with {ok:false, error:{class:"validation"}}.
//
// MCP arch §3.7 — 14 Tier 3 primitives + 1 Tier 4 raw-asset read + TR Wave + UDA Campaign.

/** The underlying retrieval tool names exposed as MCP primitives. */
export const SURGICAL_TOOLS = [
  'chart_facts_query',
  'msr_sql',
  'query_dasha_periods',
  'query_panchanga',
  'query_ephemeris',
  'query_transit_event',
  'lel_query',
  'vector_search',
  'cgm_graph_walk',
  'multi_school_signal_lookup',
  'classical_text_search',
  // TR Wave Class A retrieval tools (engines existed pre-PR-#159)
  'query_varshaphala',
  'divisional_query',
  'remedial_codex_query',
  'query_muhurat',
  // TR Wave Class B/C stubs (retrieval tools not yet built)
  'query_tara_balam',
  'query_chandra_balam',
  'jaimini_chara_dasha',
  'jaimini_chara_dasha_full',
  // UDA Campaign additions — 14 portal-native tools whitelisted for MCP primitive dispatch
  'msr_sql',
  'temporal',
  'kp_query',
  'query_kp_ruling_planets',
  'pattern_register',
  'resonance_register',
  'cluster_atlas',
  'contradiction_register',
  'query_ucn_walk',
  'query_cdlm_lookup',
  'query_rm_walk',
  'query_jaimini_drishti',
  'timeline_query',
  'query_signal_state',
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
  vector_search: 'vector_search',
  get_cgm_subgraph: 'cgm_graph_walk',
  cross_school_lookup: 'multi_school_signal_lookup',
  read_classical_text: 'classical_text_search',
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
  // TR Wave Class B/C stubs
  query_tara_balam: 'query_tara_balam',
  query_chandra_balam: 'query_chandra_balam',
  jaimini_chara_dasha: 'jaimini_chara_dasha',
  jaimini_chara_dasha_full: 'jaimini_chara_dasha_full',
  // UDA Campaign additions — 14 portal-native tools exposed as MCP primitives
  msr_sql: 'msr_sql',
  temporal: 'temporal',
  kp_query: 'kp_query',
  query_kp_ruling_planets: 'query_kp_ruling_planets',
  pattern_register: 'pattern_register',
  resonance_register: 'resonance_register',
  cluster_atlas: 'cluster_atlas',
  contradiction_register: 'contradiction_register',
  query_ucn_walk: 'query_ucn_walk',
  query_cdlm_lookup: 'query_cdlm_lookup',
  query_rm_walk: 'query_rm_walk',
  query_jaimini_drishti: 'query_jaimini_drishti',
  timeline_query: 'timeline_query',
  query_signal_state: 'query_signal_state',
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

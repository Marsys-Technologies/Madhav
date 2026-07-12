/**
 * P1 Phase-1 Naming Aliases — all 53 existing tools get <layer>_<topic>_<type> aliases.
 * ========================================================================================
 * Per BA-P1 brief §Step 4 (MCP_TOOL_NAMING_STANDARD §3):
 *   BOTH names call one handler. Old names are deprecated (not removed — Phase 3 removal gate).
 *   Dedup: bodha_remedies_get primary; bodha_remedies_search → alias; ref_remedies_search retained.
 *
 * DOCUMENTED DEFERRALS (6 of 6 maximum):
 *   1. recall_session     → session_recall        [internal lib/session.js — aliasable only inside session_tools.ts]
 *   2. list_my_sessions   → session_list          [internal lib/session.js]
 *   3. list_my_charts     → catalog_charts_list   [principal-bound closure; needs server-level auth]
 *   4. select_chart       → catalog_chart_select  [principal-bound closure; needs server-level auth]
 *   5. holistic_bundle_chart_facts → bodha_bundle_get  [uses callPlatformBundle with principal]
 *   6. kala_temporal_bundle → kala_bundle_get     [kala sidecar composite — multi-subsystem gather]
 *
 * The 47 aliases implemented in this file cover the remaining 47 of the 53 baseline tools.
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { describeProxyFailure } from './registry_bridge.js'
import { applyResponseBudget, autoDetectTrimmableSections, type TrimmableSection } from '../lib/response_budget.js'

// ── Infrastructure helpers ────────────────────────────────────────────────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''
const PYTHON_SIDECAR_URL = (process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001').replace(/\/$/, '')
const SIDECAR_API_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''

const AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri: 'lahiri_chitrapaksha', LAHIRI: 'lahiri_chitrapaksha', Lahiri: 'lahiri_chitrapaksha',
  lahiri_chitrapaksha: 'lahiri_chitrapaksha', true_chitra: 'lahiri_chitrapaksha',
}
function na(id?: string): string { return id ? (AYANAMSHA_ALIAS[id] ?? id) : 'lahiri_chitrapaksha' }

async function callRegistryCap(uri: string, args: Record<string, unknown>, principal: Principal): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(25_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    // R5.2 A3 (battery X-2 finding, same class as registry_bridge.ts's identical fix):
    // don't leak the raw HTTP status code into the MCP-facing error text — this helper
    // backs ganita_chart_facts_get/query_chart_facts, which the entitlement battery item
    // exercises directly.
    throw new Error(describeProxyFailure(uri, res.status, text))
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) throw new Error(`[alias] capability error: ${data.error ?? 'unknown'}`)
  return data.content
}

// R5 W2 corpus lane fix (P7 — corpus search 401, still failing after the W0a
// punch-list's registry_bridge.ts fix because THIS helper — the one every
// alias in this file calls, including ref_vector_search — was never touched).
// Root cause: this helper sent only the Layer-1 x-mcp-internal-token header;
// /api/mcp/primitives/[tool]/route.ts's Layer-2 gate requires X-MCP-User +
// X-MCP-Key-Id (X-MCP-Audience-Tier is informational only, not gated) and
// 401s any call missing them — see route.ts:91-106. The 3-header pattern was
// already fixed once in registry_bridge.ts's OWN local callPlatformPrimitive
// (that tool calls the bare `vector_search` MCP tool), but register_p1_aliases.ts
// has always had its own separate copy of this proxy helper (a second,
// never-fixed instance of the exact same bug class) — this is that instance.
// Design doc RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md §20 names this
// explicitly: "Copy the working header pattern into BOTH proxy helpers."
/**
 * R5.1 C2 item 3 (Denial ≠ empty) — mirrors registry_bridge.ts's describeProxyFailure.
 * Preserves the platform's distinct entitlement_denied signal instead of collapsing it to
 * a bare "failed (401)"; falls back to the generic message for every other error shape.
 */
export function describePrimFailure(tool: string, status: number, bodyText: string): string {
  try {
    const parsed = JSON.parse(bodyText) as { error?: { class?: string; message?: string }; denial?: { chart_id?: string; permission_required?: string } }
    if (parsed?.error?.class === 'entitlement_denied' || parsed?.denial) {
      const chartId = parsed.denial?.chart_id ?? 'unknown'
      const required = parsed.denial?.permission_required ?? 'view'
      return `[alias] ENTITLEMENT_DENIED: '${tool}' — caller lacks ${required} access to chart ${chartId} ` +
        `(distinct from an empty result — this chart exists but you are not granted). ${parsed.error?.message ?? ''}`.trim()
    }
  } catch {
    // Not JSON / not the denial shape — fall through.
  }
  return `[alias] primitive '${tool}' failed (${status})`
}

async function callPlatformPrim(
  tool: string,
  params: Record<string, unknown>,
  principal: Principal,
): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/primitives/${encodeURIComponent(tool)}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Audience-Tier': principal.role === 'super_admin' ? 'super_admin' : 'client',
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ params }),
    signal: AbortSignal.timeout(25_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(describePrimFailure(tool, res.status, text))
  }
  return res.json()
}

async function callSidecarPath(path: string, body: Record<string, unknown>): Promise<unknown> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (SIDECAR_API_KEY) headers['X-API-Key'] = SIDECAR_API_KEY
  const res = await fetch(`${PYTHON_SIDECAR_URL}${path}`, {
    method: 'POST', headers, body: JSON.stringify(body),
    signal: AbortSignal.timeout(30_000),
  })
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    throw new Error(`[alias] sidecar ${path} failed (${res.status}): ${txt.slice(0, 200)}`)
  }
  return res.json()
}

const DUAL_OUTPUT_TEXT_THRESHOLD_BYTES = 50_000

// S3 fix (R5 W0a perf lane): no pretty-print; text duplicate suppressed above
// threshold (structuredContent already carries the full payload).
//
// R6 3b-budgets (R-1/R-8): `data` here is the RAW capability/primitive/sidecar content
// (this file's aliases return `data.content` directly, unlike register_p1_ganita.ts /
// register_p1_synthesis.ts which wrap in an envelope) — so the generic auto-trim runs
// directly on `data`, keyed by an optional `toolName` (passed by every call site that goes
// through regAlias/globalAlias, and by every hand-written `server.tool` block below that
// was touched in this pass). Falls back to a generic hint when the caller omits toolName —
// still trims, just without a tool-specific recovery instrument name.
function dualOutput(data: unknown, toolName = 'unknown_tool') {
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>
    const sections = autoDetectTrimmableSections(obj, toolName)
    if (sections.length > 0) {
      const result = applyResponseBudget(obj, 40, sections)
      if (result.trim_report) obj['trim_report'] = result.trim_report
    }
  }
  const structuredContent = { type: 'object' as const, object: data }
  const json = JSON.stringify(data)
  if (Buffer.byteLength(json, 'utf8') > DUAL_OUTPUT_TEXT_THRESHOLD_BYTES) {
    return { structuredContent, content: [{ type: 'text' as const, text: '[large payload — see structuredContent]' }] }
  }
  return { structuredContent, content: [{ type: 'text' as const, text: json }] }
}
function errOut(tool: string, msg: string, extra?: Record<string, unknown>) {
  return { ...dualOutput({ ok: false, error: msg, tool, ...extra }), isError: true as const }
}

function signalsSection(): TrimmableSection<Record<string, unknown>> {
  return {
    path: 'signals', label: 'signals', minKeep: 20,
    getArray: (c) => {
      const arr = c['signals']
      return Array.isArray(arr) ? arr : undefined
    },
    setArray: (c, kept) => { c['signals'] = kept },
    recover: { instrument: 'bodha_signals_get', hint: 'call again with a smaller top_k, or paginate via offset' },
  }
}

// ── Common Zod schemas ────────────────────────────────────────────────────────

const ChartBase = {
  chart_id:     z.string().uuid().describe('Chart UUID'),
  ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
  limit:        z.number().int().min(1).max(25000).optional(),
  offset:       z.number().int().min(0).optional(),
}
const GlobalBase = {
  limit:  z.number().int().min(1).max(1000).optional(),
  offset: z.number().int().min(0).optional(),
}
const BirthBase = {
  datetime_iso:  z.string().describe("Birth datetime local ISO, e.g. '1984-02-05T10:43:00'"),
  latitude_deg:  z.number().describe('Latitude decimal degrees (N positive)'),
  longitude_deg: z.number().describe('Longitude decimal degrees (E positive)'),
  tz_offset_hours: z.number().default(5.5).describe('TZ offset hours (e.g. 5.5 for IST)'),
  ayanamsha_id: z.enum(['lahiri', 'raman', 'kp', 'true_citra']).default('lahiri'),
}

// ── D7 Registry bridge aliases (20 tools) ─────────────────────────────────────

/**
 * Map: alias_name → { uri, description_fragment }
 * All call callRegistryCap(uri, { chart_id, ayanamsha_id, limit, offset, ...extra }, principal).
 */

// Helper for simple chart-scoped registry aliases
function regAlias(
  server: McpServer,
  name: string,
  desc: string,
  uri: string,
  extraSchema: Record<string, z.ZodTypeAny> = {},
  principal: Principal,
) {
  server.tool(
    name, `[Phase-1 alias] ${desc}. Delegates to the same handler as the legacy tool name.`,
    { ...ChartBase, ...extraSchema },
    async (params) => {
      const { chart_id, ayanamsha_id, limit, offset, ...rest } = params as Record<string, unknown>
      if (!chart_id) return errOut(name, 'chart_id is required')
      try {
        const data = await callRegistryCap(uri, {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          limit: (limit as number) ?? 25000, offset: (offset as number) ?? 0, ...rest,
        }, principal)
        return dualOutput(data, name)
      } catch (err) { return errOut(name, String(err), { chart_id }) }
    }
  )
}

// Helper for global-scope (no chart_id) registry aliases
function globalAlias(
  server: McpServer,
  name: string,
  desc: string,
  uri: string,
  extraSchema: Record<string, z.ZodTypeAny> = {},
  principal: Principal,
) {
  server.tool(
    name, `[Phase-1 alias] ${desc}. Delegates to the same handler as the legacy tool name.`,
    { ...GlobalBase, ...extraSchema },
    async (params) => {
      const { limit, offset, ...rest } = params as Record<string, unknown>
      try {
        const data = await callRegistryCap(uri, {
          limit: (limit as number) ?? 100, offset: (offset as number) ?? 0, ...rest,
        }, principal)
        return dualOutput(data, name)
      } catch (err) { return errOut(name, String(err)) }
    }
  )
}

// WP-1.3 (b/c): shared faceted schema for the DB-backed dasha capability
// (marsys://tool/L1/get_dashas). Used by every LLM-facing dasha tool name so that
// system_id (F-0354) and requested windows (F-0471/0485) are honored uniformly — instead
// of a divergent, vimshottari-only, windowless PyJHora sidecar surface for some names.
const DASHA_FACET_SCHEMA: Record<string, z.ZodTypeAny> = {
  // ayanamsha_id override: no server-side default (chart_dashas carries all 5) — omitting it
  // returns one row PER ayanamsha. Pass "lahiri_chitrapaksha" for the single-row gate shape.
  ayanamsha_id: z.string().optional().describe(
    'Ayanamsha filter. NO server-side default — omitting it returns ALL 5 ayanamshas ' +
    '(one row per ayanamsha). Pass "lahiri_chitrapaksha" explicitly for the standard ' +
    'single-row current-dasha gate shape.'),
  as_of_date:    z.string().optional().describe('ISO date — the dasha running on this date ("what dasha as of X"). Echoed in facets_applied.date_filter.'),
  date_contains: z.string().optional().describe('ISO date — alias of as_of_date.'),
  date_from:     z.string().optional().describe('ISO date — exclude periods ending before this date. Echoed in facets_applied.date_filter.'),
  system:        z.string().optional().describe('Dasha system facet (default: vimshottari; "all" for every system).'),
  system_id:     z.string().optional().describe('Alias for `system` using the raw column name (F-0354). Same vocabulary; precedence system > dasha_system > system_id.'),
  dasha_system:  z.string().optional().describe('Deprecated alias for system.'),
  level:         z.union([z.string(), z.number()]).optional().describe('Exact dasha level (1=Maha..5=Prana, or the name).'),
  all_levels:    z.boolean().optional().describe('Disable the default level<=3 cap.'),
  window_start:  z.string().optional().describe('ISO date — window facet lower bound (overlap). Echoed in facets_applied.window.'),
  window_end:    z.string().optional().describe('ISO date — window facet upper bound (overlap). Echoed in facets_applied.window.'),
  lord_graha:    z.string().optional(),
  fields:        z.string().optional().describe('Projection facet: "compact" (default), "all", or a comma-separated column list.'),
}

export function registerP1AliasTools(server: McpServer, principal: Principal): void {

  // ── D7 + D8 Registry bridge aliases ──────────────────────────────────────

  // get_chart_orientation → bodha_chart_digest_get
  regAlias(server, 'bodha_chart_digest_get',
    'L2 UCD chart orientation digest (same as get_chart_orientation)',
    'marsys://tool/L2/query_ucd',
    { mode: z.enum(['summary', 'full']).optional() }, principal)

  // get_domain_reading → bodha_domain_reading_get
  regAlias(server, 'bodha_domain_reading_get',
    'L2 domain reading via Bodha synthesis (same as get_domain_reading)',
    'marsys://tool/L2/query_domain_reading',
    { domain: z.string().describe('Life domain (career, health, relationship, wealth, etc.)') }, principal)

  // get_signals → bodha_signals_get
  // R5.2 A3 (battery X-3 finding): top_k=200 (the max this schema allows) measured 234,278
  // wire bytes live — squarely the "234KB class" the R5.2 brief names, on a tool C1 never
  // touched (C1's scope was judgment_query/graha_portrait/pact_query only). Each signal
  // object is legitimately rich (citations, configuration_jsonb, dispositor context), so
  // this isn't a fabricated bloat — it's an uncapped fan-out with no budget discipline
  // anywhere in the call path. Same shared trimmer as every other budget fix this run.
  server.tool(
    'bodha_signals_get',
    '[Phase-1 alias] L2 Bodha signals ranked by relevance (same as get_signals). R5 W2: frame ' +
    '(lagna/chandra/surya/arudha/karakamsha) annotates a frame_context (never recomputes frozen ' +
    'salience); paradigm (parashari/jaimini/kp/tajika) filters to one tradition (default: all, ' +
    'unfiltered). Delegates to the same handler as the legacy tool name.',
    {
      ...ChartBase,
      domain:     z.string().optional(),
      top_k:      z.number().int().min(1).max(200).optional(),
      min_weight: z.number().min(0).max(1).optional(),
      frame:      z.enum(['lagna', 'chandra', 'surya', 'arudha', 'karakamsha']).optional(),
      paradigm:   z.enum(['parashari', 'jaimini', 'kp', 'tajika']).optional(),
    },
    async (params) => {
      const { chart_id, ayanamsha_id, limit, offset, ...rest } = params as Record<string, unknown>
      if (!chart_id) return errOut('bodha_signals_get', 'chart_id is required')
      try {
        const data = await callRegistryCap('marsys://tool/L2/query_signals', {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          limit: (limit as number) ?? 25000, offset: (offset as number) ?? 0, ...rest,
        }, principal) as Record<string, unknown>
        const inner = data['content'] as Record<string, unknown> | undefined
        if (inner) {
          const budgeted = applyResponseBudget(inner, 25, [signalsSection()])
          if (budgeted.trim_report) inner['trim_report'] = budgeted.trim_report
        }
        return dualOutput(data)
      } catch (err) { return errOut('bodha_signals_get', String(err), { chart_id }) }
    }
  )

  // traverse_graph → bodha_graph_traverse_get
  // R-18 fix: this was previously registered via the generic regAlias() helper, which forwards
  // its extraSchema keys verbatim to the primitive. The primitive (traverse_chart_graph.ts) does
  // NOT read start_node, max_depth, relation, or limit — it reads seed_node_ids, depth, edge_types,
  // and top_k_hubs (convergence-mode row cap). Those four params were therefore silently dropped
  // on every call. Rewritten as a custom handler that translates: max_depth -> depth,
  // limit -> top_k_hubs (the only row-count knob the primitive exposes; applies to convergence
  // mode), start_node -> seed_node_ids[0] (single-seed convenience), relation -> edge_types[0].
  server.tool(
    'bodha_graph_traverse_get',
    '[Phase-1 alias] L2 chart graph traversal (same as traverse_graph). R5 W2: about/about_from/about_to ' +
    'accept address expressions (e.g. "lord_of(bhava 10)") resolved via the shared address resolver; ' +
    'direction/min_strength filter traversal. Gate: a "10th-lord to Moon" path resolves in ONE call ' +
    'via mode="paths", about_from="lord_of(bhava 10)", about_to={type:"graha",graha:"Moon"}, direction="directed". ' +
    'limit caps convergence-mode hub rows (mapped to the primitive\'s top_k_hubs); max_depth caps ' +
    'neighbors-mode BFS depth (mapped to the primitive\'s depth, 1-3).',
    {
      ...ChartBase,
      mode:          z.enum(['neighbors', 'paths', 'convergence', 'contradictions']).optional(),
      start_node:    z.string().optional().describe('Single seed node UUID (neighbors mode). Mapped to seed_node_ids[0].'),
      seed_node_ids: z.array(z.string()).optional().describe('Seed node UUIDs (neighbors/paths modes).'),
      max_depth:     z.number().int().min(1).max(3).optional().describe('BFS depth for neighbors mode (1-3, default 1).'),
      relation:      z.string().optional().describe('Single edge_type filter. Mapped to edge_types[0].'),
      edge_types:    z.array(z.string()).optional(),
      about:         z.union([z.string(), z.record(z.string(), z.unknown())]).optional(),
      about_from:    z.union([z.string(), z.record(z.string(), z.unknown())]).optional(),
      about_to:      z.union([z.string(), z.record(z.string(), z.unknown())]).optional(),
      direction:     z.enum(['directed', 'both']).optional(),
      min_strength:  z.number().min(0).max(1).optional(),
    },
    async (params) => {
      const { chart_id, ayanamsha_id, limit, offset: _offset, start_node, seed_node_ids, max_depth, relation, edge_types, ...rest } =
        params as Record<string, unknown>
      void _offset // traversal has no offset concept — accepted but not applicable (not silently misapplied)
      if (!chart_id) return errOut('bodha_graph_traverse_get', 'chart_id is required')
      try {
        const resolvedSeedIds = (seed_node_ids as string[] | undefined) ?? (start_node ? [start_node as string] : undefined)
        const resolvedEdgeTypes = (edge_types as string[] | undefined) ?? (relation ? [relation as string] : undefined)
        const data = await callRegistryCap('marsys://tool/L2/traverse_chart_graph', {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          ...(resolvedSeedIds ? { seed_node_ids: resolvedSeedIds } : {}),
          ...(max_depth != null ? { depth: max_depth } : {}),
          ...(resolvedEdgeTypes ? { edge_types: resolvedEdgeTypes } : {}),
          ...(limit != null ? { top_k_hubs: limit } : {}),
          ...rest,
        }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('bodha_graph_traverse_get', String(err), { chart_id }) }
    }
  )

  // get_positions → ganita_positions_get
  regAlias(server, 'ganita_positions_get',
    'L1 graha positions (same as get_positions). R5 W2: frame (lagna/chandra/surya/arudha/' +
    'karakamsha, default lagna) re-bases house_d1 onto the requested reference sign, adding ' +
    'house_from_frame per row — e.g. frame="chandra" answers "what house is X in, from Moon" ' +
    'in this ONE call. The response\'s own `frame_note` field states exactly how many rows in ' +
    'THIS call actually carry house_from_frame (R-28: pass ayanamsha_id explicitly for full ' +
    'coverage — an unfiltered call spanning all 5 ayanamshas may only re-base a subset).',
    'marsys://tool/L1/get_positions',
    {
      frame:  z.enum(['lagna', 'chandra', 'surya', 'arudha', 'karakamsha']).optional(),
      planet: z.string().optional().describe(
        'Filter to a single graha (e.g. "Sun", "Moon", "Mars"). SC-20 fix: this alias previously ' +
        'had no planet param at all, so a caller had no way to narrow the payload.'),
    }, principal)

  // get_dashas → ganita_dashas_get
  // R5 W1 (dasha_query lane, design §18/§21/§25 E-5): facets threaded through the seam so
  // they don't die at the boundary the way as_of_date originally did (P1). Kept as a hand
  // shim (single-source codegen for this instrument is a later-wave item) but every facet
  // the handler (get_dashas.ts) now reads is declared here too.
  regAlias(server, 'ganita_dashas_get',
    'L1 dasha periods, faceted by system/level/window (same as get_dashas). ' +
    'Defaults: system=vimshottari, level<=3 (Maha/Antar/Pratyantar), window=now±5y. ' +
    'ayanamsha_id has NO default here (unlike system/level/window) — omitting it returns ' +
    'one row PER AYANAMSHA (5 rows, ~3.2KB), busting the <=1KB current-dasha gate. ' +
    'Gate target (current dasha, <=1KB, ONE call): system=vimshottari, level=1, ' +
    'as_of_date=<today>, ayanamsha_id="lahiri_chitrapaksha" — ALWAYS pass ayanamsha_id explicitly.',
    'marsys://tool/L1/get_dashas',
    DASHA_FACET_SCHEMA, principal)

  // get_temporal_windows → kala_windows_get
  // R-18 fix: the primitive (query_temporal_activation.ts) reads date_from/date_to/top_k, not
  // start_date/end_date/limit — the naming mismatch meant every call silently fell back to the
  // primitive's own defaults (today..+1y, top_k=50) regardless of what the caller passed. domain
  // is now a real filter on the primitive (joins bodha_msr_signals.domains_affected_array).
  server.tool(
    'kala_windows_get',
    '[Phase-1 alias] L3 temporal activation windows (same as get_temporal_windows).',
    {
      ...ChartBase,
      start_date: z.string().optional().describe('Start of date range (mapped to date_from).'),
      end_date:   z.string().optional().describe('End of date range (mapped to date_to).'),
      domain:     z.string().optional().describe('Filter to activations affecting this life domain.'),
    },
    async (params) => {
      const { chart_id, ayanamsha_id, limit, offset: _offset, start_date, end_date, domain } =
        params as Record<string, unknown>
      void _offset // this primitive has no offset concept
      if (!chart_id) return errOut('kala_windows_get', 'chart_id is required')
      try {
        const data = await callRegistryCap('marsys://tool/L3/query_temporal_activation', {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          ...(start_date ? { date_from: start_date } : {}),
          ...(end_date ? { date_to: end_date } : {}),
          ...(domain ? { domain } : {}),
          ...(limit != null ? { top_k: limit } : {}),
        }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('kala_windows_get', String(err), { chart_id }) }
    }
  )

  // get_projections → kala_projections_get
  regAlias(server, 'kala_projections_get',
    'L3 time-indexed projections (same as get_projections)',
    'marsys://tool/L3/query_projections',
    {
      start_date: z.string().optional(),
      end_date:   z.string().optional(),
    }, principal)

  // get_classical_citation → ref_classical_citation_get
  server.tool(
    'ref_classical_citation_get',
    '[Phase-1 alias] Retrieve classical citations from L0 (same as get_classical_citation).',
    { keyword: z.string().optional(), topic: z.string().optional(), author: z.string().optional(), ...GlobalBase },
    async ({ keyword, topic, author, limit, offset }) => {
      try {
        const data = await callRegistryCap('marsys://tool/L0/query_classical_texts', {
          keyword, topic, author, limit: limit ?? 50, offset: offset ?? 0,
        }, principal)
        return dualOutput(data, 'ref_classical_citation_get')
      } catch (err) { return errOut('ref_classical_citation_get', String(err)) }
    }
  )

  // get_remedies → bodha_remedies_get (PRIMARY alias per dedup disposition)
  regAlias(server, 'bodha_remedies_get',
    'L2 remedy recommendations via Bodha (PRIMARY Phase-1 name for get_remedies)',
    'marsys://tool/L2/query_remedies',
    { domain: z.string().optional() }, principal)

  // Also: bodha_remedies_search as secondary alias
  regAlias(server, 'bodha_remedies_search',
    'L2 remedy search via Bodha (alias of bodha_remedies_get)',
    'marsys://tool/L2/query_remedies',
    { domain: z.string().optional(), keyword: z.string().optional() }, principal)

  // get_chart_quality → bodha_quality_get
  regAlias(server, 'bodha_quality_get',
    'L2 chart quality scorecard (same as get_chart_quality)',
    'marsys://tool/L2/query_quality_scorecard', {}, principal)

  // R5.2 A2 (punch #5, orphaned C2 item 4): query_predictive_anchors's capability URI had
  // no public MCP tool wired to it — phala_anchors_get is a same-named but functionally
  // distinct sidecar-backed alias calling /api/compute/phala/event_anchors, not this
  // registry capability, so the R5.1 C2 posterior-provenance fix (base_rate_source +
  // honest cardinality-null blocks on phala_anchors rows) was correct but unreachable by
  // any live MCP tool call. Named distinctly from phala_anchors_get to avoid repeating
  // that collision.
  regAlias(server, 'phala_predictive_anchors_get',
    'L4 predictive anchors (phala_anchors/ph_nimitta) — magnitude, confidence band, karmic frame, ' +
    'malleability, and posterior_provenance (base_rate_source + honest cardinality-null where unfit) per anchor',
    'marsys://tool/L4/query_predictive_anchors',
    {
      domain: z.string().optional(),
      event_type: z.string().optional(),
      direction: z.string().optional(),
      horizon_tier: z.string().optional(),
      top_k: z.number().optional(),
    }, principal)

  // list_assets → catalog_assets_list
  server.tool(
    'catalog_assets_list',
    '[Phase-1 alias] List all registered retrieval assets (same as list_assets).',
    { layer: z.string().optional().describe('Filter by layer (L0, L1, L2, etc.)'), ...GlobalBase },
    async ({ layer, limit, offset }) => {
      try {
        const data = await callRegistryCap('marsys://resource/asset-registry/all', {
          layer, limit: limit ?? 200, offset: offset ?? 0,
        }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('catalog_assets_list', String(err)) }
    }
  )

  // ── WP-1.3(i) / LCA-11 — apex_*_assess duplicate family RETIRED (§7.3 disposition) ──
  // The four apex_marriage_assess / apex_career_assess / apex_health_assess /
  // apex_wealth_assess tools were strict near-duplicates of the canonical assess_marriage /
  // assess_career / assess_health / assess_wealth tools (registry_bridge.ts): BOTH families
  // resolved to the SAME registry URI (marsys://tool/L-DOMAIN/assess_*), presenting the
  // consumer two redundant tools per domain (LCA-11). The apex_* variants were also INFERIOR
  // — they carried no orientation_context (B.11 frame) that the canonical assess_* tools
  // pre-fetch and attach.
  //
  // Disposition: apex_*_assess RETIRED here; the underlying capability remains fully reachable
  // via the canonical assess_marriage/career/health/wealth tools (same URI, richer output).
  // NO capability is dropped — the ONLY apex_*-exclusive surface was the two tuning params
  // (max_signals_per_lens / max_contradictions), which are MIGRATED onto the canonical
  // assess_* tools in registry_bridge.ts so assess_* is now a strict superset of the retired
  // apex_* surface. See REMEDIATION_RUN_LEDGER / this run's report for the §7.3 record.

  // yoga_activation_by_dasha → kala_yoga_activation_get
  // R-18 fix: the primitive (register_d8_assess_domain.ts::yogaActivationByDashaCapability) reads
  // date_from/date_to/top_k/domain, not start_date/end_date/limit — this alias only declared
  // start_date/end_date (never mapped to the real field names) and had no domain param at all,
  // so every call silently used the primitive's defaults regardless of caller input.
  server.tool(
    'kala_yoga_activation_get',
    '[Phase-1 alias] Kāla yoga-activation-by-dasha timeline (same as yoga_activation_by_dasha).',
    {
      ...ChartBase,
      start_date:   z.string().optional().describe('Start of date window (mapped to date_from).'),
      end_date:     z.string().optional().describe('End of date window (mapped to date_to).'),
      domain:       z.string().optional().describe('Filter to yogas affecting this life domain.'),
      dasha_period: z.string().optional().describe("Dasha-antardasha label filter (e.g. 'saturn-venus')."),
      min_salience: z.number().min(0).max(1).optional(),
    },
    async (params) => {
      const { chart_id, ayanamsha_id, limit, offset: _offset, start_date, end_date, domain, dasha_period, min_salience } =
        params as Record<string, unknown>
      void _offset // this primitive has no offset concept
      if (!chart_id) return errOut('kala_yoga_activation_get', 'chart_id is required')
      try {
        const data = await callRegistryCap('marsys://tool/L-TIMING/yoga_activation_by_dasha', {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          ...(start_date ? { date_from: start_date } : {}),
          ...(end_date ? { date_to: end_date } : {}),
          ...(domain ? { domain } : {}),
          ...(dasha_period ? { dasha_period } : {}),
          ...(min_salience != null ? { min_salience } : {}),
          ...(limit != null ? { top_k: limit } : {}),
        }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('kala_yoga_activation_get', String(err), { chart_id }) }
    }
  )

  // get_cgm_subgraph → bodha_graph_subgraph_get
  // SC-21 fix: this alias was capability-degraded relative to get_cgm_subgraph (registry_bridge.ts)
  // despite its description claiming to be "the same as" — it had no mode/seed_node_ids/about/
  // min_strength, and `limit` was silently dropped (the primitive has no `limit` field; it reads
  // depth/top_k_hubs). Rewritten with full parameter parity: same param set as get_cgm_subgraph,
  // translated onto the primitive's real field names (depth, top_k_hubs, seed_node_ids).
  server.tool(
    'bodha_graph_subgraph_get',
    '[Phase-1 alias] L2 CGM subgraph extraction (same as get_cgm_subgraph) — full parameter parity: ' +
    'mode (neighbors|paths|convergence|contradictions), seed_node_ids / start_node (single-seed ' +
    'convenience), about / about_from / about_to (address-expression seeding), direction, ' +
    'min_strength, and limit (caps convergence-mode hub rows via top_k_hubs).',
    {
      ...ChartBase,
      mode:          z.enum(['neighbors', 'paths', 'convergence', 'contradictions']).optional(),
      start_node:    z.string().optional().describe('Single seed node UUID (neighbors mode). Mapped to seed_node_ids[0].'),
      seed_node_ids: z.array(z.string()).optional(),
      depth:         z.number().int().min(1).max(3).optional(),
      about:         z.union([z.string(), z.record(z.string(), z.unknown())]).optional(),
      about_from:    z.union([z.string(), z.record(z.string(), z.unknown())]).optional(),
      about_to:      z.union([z.string(), z.record(z.string(), z.unknown())]).optional(),
      direction:     z.enum(['directed', 'both']).optional(),
      min_strength:  z.number().min(0).max(1).optional(),
    },
    async (params) => {
      const { chart_id, ayanamsha_id, limit, offset: _offset, start_node, seed_node_ids, ...rest } =
        params as Record<string, unknown>
      void _offset
      if (!chart_id) return errOut('bodha_graph_subgraph_get', 'chart_id is required')
      try {
        const resolvedSeedIds = (seed_node_ids as string[] | undefined) ?? (start_node ? [start_node as string] : undefined)
        const data = await callRegistryCap('marsys://tool/L2/traverse_chart_graph', {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          ...(resolvedSeedIds ? { seed_node_ids: resolvedSeedIds } : {}),
          ...(limit != null ? { top_k_hubs: limit } : {}),
          ...rest,
        }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('bodha_graph_subgraph_get', String(err), { chart_id }) }
    }
  )

  // query_chart_facts → ganita_chart_facts_get
  // R5 W1 (lane: chart_query) fix: extraSchema previously declared fact_category/fact_id,
  // neither of which the registry handler (register_d7_channel.ts) ever read — a dead-param
  // mismatch of the same class as P1 (design §18: "aliases carry DIVERGING param names").
  // Reconciled to the real filter set the handler now implements (see query_chart_facts above
  // for the full facet description); NF-1's 404 is fixed at the shared handler, so this alias
  // is fixed for free once its own param names line up.
  regAlias(server, 'ganita_chart_facts_get',
    'L1 chart_facts EAV-crosstab query (same as query_chart_facts)',
    'marsys://tool/L1/chart_facts_query',
    {
      about: z.union([
        z.string(),
        z.object({ graha: z.string().optional(), bhava: z.number().int().min(1).max(12).optional(), house_lord: z.number().int().min(1).max(12).optional() }),
      ]).optional(),
      category:         z.string().optional(),
      planet:           z.string().optional(),
      house:            z.number().int().min(1).max(12).optional(),
      sign:             z.string().optional(),
      nakshatra:        z.string().optional(),
      divisional_chart: z.string().optional(),
      keyword:          z.string().optional(),
      shape:            z.enum(['pivoted', 'rows']).optional(),
    }, principal)

  // vector_search → ref_vector_search
  server.tool(
    'ref_vector_search',
    '[Phase-1 alias] Semantic vector search over the chart corpus (same as vector_search).',
    {
      query:        z.string().describe('Natural language search query'),
      chart_id:     z.string().uuid().optional(),
      top_k:        z.number().int().min(1).max(50).optional(),
      filter_layer: z.string().optional(),
    },
    async ({ query, chart_id, top_k, filter_layer }) => {
      try {
        const data = await callPlatformPrim('vector_search', { query, chart_id, top_k, filter_layer }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('ref_vector_search', String(err)) }
    }
  )

  // ── L0 Ephemeris aliases (5 tools) ────────────────────────────────────────

  globalAlias(server, 'ref_planet_position_get',
    'L0 planet position at a given datetime (same as query_planet_position)',
    'marsys://tool/L0/query_planet_position',
    {
      datetime_iso:    z.string().optional().describe('ISO datetime for ephemeris lookup'),
      planet:          z.string().optional(),
      ayanamsha_id:    z.string().optional(),
    }, principal)

  globalAlias(server, 'ref_planet_transit_get',
    'L0 planet transit event lookup (same as query_planet_transit)',
    'marsys://tool/L0/query_planet_transit',
    {
      planet:       z.string().optional(),
      start_date:   z.string().optional(),
      end_date:     z.string().optional(),
      ayanamsha_id: z.string().optional(),
    }, principal)

  globalAlias(server, 'ref_aspects_at_time_get',
    'L0 planetary aspects at a specific datetime (same as query_aspects_at_time)',
    'marsys://tool/L0/query_aspects_at_time',
    {
      datetime_iso: z.string().optional(),
      ayanamsha_id: z.string().optional(),
    }, principal)

  globalAlias(server, 'ref_retrograde_periods_get',
    'L0 retrograde periods for a planet in a date range (same as query_retrograde_periods)',
    'marsys://tool/L0/query_retrograde_periods',
    {
      planet:      z.string().optional(),
      start_date:  z.string().optional(),
      end_date:    z.string().optional(),
    }, principal)

  // ephemeris_cache_year → ref_ephemeris_year_get
  server.tool(
    'ref_ephemeris_year_get',
    '[Phase-1 alias] L0 ephemeris cache for a given year (same as ephemeris_cache_year).',
    { year: z.number().int().min(1900).max(2150).describe('4-digit calendar year') },
    async ({ year }) => {
      try {
        const data = await callRegistryCap(`marsys://resource/ephemeris-cache/year/${year}`, { year }, principal)
        return dualOutput(data, 'ref_ephemeris_year_get')
      } catch (err) { return errOut('ref_ephemeris_year_get', String(err), { year }) }
    }
  )

  // ── L0 Brahmagyan aliases (5 tools) ───────────────────────────────────────

  globalAlias(server, 'ref_entity_resolve',
    'Resolve a Jyotish entity name to canonical form (same as resolve_entity)',
    'marsys://tool/L0/resolve_entity',
    { name: z.string().optional().describe('Entity name to resolve') }, principal)

  globalAlias(server, 'ref_entities_list',
    'List all Jyotish canonical entities (same as list_entities)',
    'marsys://tool/L0/list_entities',
    { entity_class: z.string().optional().describe('Filter by class (graha/nakshatra/rashi/etc.)') }, principal)

  server.tool(
    'catalog_assets_all',
    '[Phase-1 alias] Full asset registry (same as asset_registry_all). Global scope.',
    { ...GlobalBase },
    async ({ limit, offset }) => {
      try {
        const data = await callRegistryCap('marsys://resource/asset-registry/all', {
          limit: limit ?? 200, offset: offset ?? 0,
        }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('catalog_assets_all', String(err)) }
    }
  )

  server.tool(
    'catalog_assets_l0',
    '[Phase-1 alias] L0 Brahmagyan asset registry (same as asset_registry_l0).',
    { ...GlobalBase },
    async ({ limit, offset }) => {
      try {
        const data = await callRegistryCap('marsys://resource/asset-registry/L0', {
          limit: limit ?? 100, offset: offset ?? 0,
        }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('catalog_assets_l0', String(err)) }
    }
  )

  server.tool(
    'util_intent_classify',
    '[Phase-1 alias] Intent classification prompt (same as intent_classify).',
    { query: z.string().describe('Query text to classify') },
    async ({ query }) => {
      try {
        const data = await callRegistryCap('marsys://prompt/intent-classify', { query }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('util_intent_classify', String(err)) }
    }
  )

  // ── L0FR Remedy aliases (7 tools — via platform primitive) ───────────────

  server.tool(
    'ref_remedies_get',
    '[Phase-1 alias] Query L0 remedy corpus (same as query_remedies).',
    {
      keyword:  z.string().optional(),
      category: z.string().optional(),
      planet:   z.string().optional(),
      ...GlobalBase,
    },
    async (params) => {
      try {
        const data = await callPlatformPrim('query_remedies', params as Record<string, unknown>, principal)
        return dualOutput(data)
      } catch (err) { return errOut('ref_remedies_get', String(err)) }
    }
  )

  server.tool(
    'ref_remedies_chart_get',
    '[Phase-1 alias] Chart-specific remedy suggestions (same as query_remedies_for_chart).',
    { affliction: z.string().describe('Planet name or domain keyword'), top_k: z.number().int().optional() },
    async ({ affliction, top_k }) => {
      try {
        const data = await callPlatformPrim('query_remedies_for_chart', { affliction, top_k }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('ref_remedies_chart_get', String(err)) }
    }
  )

  server.tool(
    'ref_remedies_by_category_list',
    '[Phase-1 alias] Remedies by category (same as list_remedies_by_category).',
    { category: z.string().describe('Remedy category (mantra/yantra/tantra/seva/gemstone/etc.)'), ...GlobalBase },
    async ({ category, limit, offset }) => {
      try {
        const data = await callPlatformPrim('list_remedies_by_category', { category, limit, offset }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('ref_remedies_by_category_list', String(err)) }
    }
  )

  server.tool(
    'ref_remedy_get',
    '[Phase-1 alias] Read a single remedy entry (same as read_remedy).',
    { remedy_id: z.string().describe('Remedy identifier') },
    async ({ remedy_id }) => {
      try {
        const data = await callPlatformPrim('read_remedy', { remedy_id }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('ref_remedy_get', String(err)) }
    }
  )

  server.tool(
    'ref_tantric_remedies_get',
    '[Phase-1 alias] Tantric remedy corpus (same as query_tantric_remedies).',
    { planet: z.string().optional(), keyword: z.string().optional(), ...GlobalBase },
    async (params) => {
      try {
        const data = await callPlatformPrim('query_tantric_remedies', params as Record<string, unknown>, principal)
        return dualOutput(data)
      } catch (err) { return errOut('ref_tantric_remedies_get', String(err)) }
    }
  )

  server.tool(
    'ref_remedies_by_planet_get',
    '[Phase-1 alias] Remedies filtered by planet (same as query_remedies_by_planet).',
    { planet: z.string().describe('Planet name (sun/moon/mars/mercury/jupiter/venus/saturn/rahu/ketu)'), ...GlobalBase },
    async ({ planet, limit, offset }) => {
      try {
        const data = await callPlatformPrim('query_remedies_by_planet', { planet, limit, offset }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('ref_remedies_by_planet_get', String(err), { planet }) }
    }
  )

  server.tool(
    'ref_mantras_get',
    '[Phase-1 alias] Mantra corpus query (same as query_mantras).',
    { planet: z.string().optional(), deity: z.string().optional(), keyword: z.string().optional(), ...GlobalBase },
    async (params) => {
      try {
        const data = await callPlatformPrim('query_mantras', params as Record<string, unknown>, principal)
        return dualOutput(data)
      } catch (err) { return errOut('ref_mantras_get', String(err)) }
    }
  )

  // Also: ref_remedies_search (dedup companion per brief disposition)
  server.tool(
    'ref_remedies_search',
    '[Phase-1 alias] Reference remedies search (dedup companion; retained per §Step 4 disposition).',
    { keyword: z.string().optional(), planet: z.string().optional(), category: z.string().optional(), ...GlobalBase },
    async (params) => {
      try {
        const data = await callPlatformPrim('query_remedies', params as Record<string, unknown>, principal)
        return dualOutput(data)
      } catch (err) { return errOut('ref_remedies_search', String(err)) }
    }
  )

  // ── L4 Phala aliases (3 via sidecar + 1 via platform primitive) ──────────

  server.tool(
    'phala_anchors_get',
    '[Phase-1 alias] L4 Phala event anchors — calibrated probabilistic event windows (same as phala_event_anchors).',
    {
      chart_id:   z.string().uuid().describe('Chart UUID'),
      date_range: z.object({
        start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
        end:   z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
      }).optional(),
      min_confidence: z.number().min(0).max(1).optional(),
    },
    async ({ chart_id, date_range, min_confidence }) => {
      if (!chart_id) return errOut('phala_anchors_get', 'chart_id is required')
      try {
        const data = await callSidecarPath('/api/compute/phala/event_anchors', {
          chart_id, date_range, min_confidence,
        })
        return dualOutput(data, 'phala_anchors_get')
      } catch (err) { return errOut('phala_anchors_get', String(err), { chart_id }) }
    }
  )

  server.tool(
    'phala_mitigation_get',
    '[Phase-1 alias] L4 mitigation map — dosha/challenge mitigation paths (same as mitigation_map).',
    { chart_id: z.string().uuid().describe('Chart UUID'), domain: z.string().optional() },
    async ({ chart_id, domain }) => {
      if (!chart_id) return errOut('phala_mitigation_get', 'chart_id is required')
      try {
        const data = await callPlatformPrim('mitigation_map', { chart_id, domain }, principal)
        return dualOutput(data, 'phala_mitigation_get')
      } catch (err) { return errOut('phala_mitigation_get', String(err), { chart_id }) }
    }
  )

  server.tool(
    'kala_muhurta_get',
    '[Phase-1 alias] Muhurta (auspicious timing) finder (same as muhurta_finder).',
    {
      chart_id:      z.string().uuid().describe('Chart UUID'),
      start_date:    z.string().optional().describe('Search window start (YYYY-MM-DD). Default: today.'),
      end_date:      z.string().optional().describe('Search window end (YYYY-MM-DD). Default: start_date + 30 days.'),
      activity_type: z.string().optional()
        .describe('Activity: marriage|travel|business|medical|education|property|general. Default: general.'),
    },
    async ({ chart_id, start_date, end_date, activity_type }) => {
      if (!chart_id) return errOut('kala_muhurta_get', 'chart_id is required')
      // R5.1 C3 fix: this alias previously called a non-existent sidecar path
      // ('/api/compute/muhurat', body shape {start_date,end_date,activity_type}) —
      // always a 404. Repointed to the real PH-4-4 endpoint
      // (brahmagyan/phala/muhurta.py) with its actual request contract
      // (chart_id, action_type, date_range:{start,end}).
      const start = start_date ?? new Date().toISOString().slice(0, 10)
      const end = end_date ?? new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10)
      const action_type = activity_type ?? 'general'
      try {
        const data = await callSidecarPath('/api/compute/phala/muhurta_finder', {
          chart_id,
          action_type,
          date_range: { start, end },
        })
        return dualOutput(data)
      } catch (err) { return errOut('kala_muhurta_get', String(err), { chart_id }) }
    }
  )

  server.tool(
    'phala_outlook_get',
    '[Phase-1 alias] L4 Phala composite predictive outlook (same as phala_outlook).',
    {
      chart_id:       z.string().uuid().describe('Chart UUID'),
      horizon_months: z.number().int().min(1).max(120).optional().describe('Forecast horizon in months (default: 12)'),
    },
    async ({ chart_id, horizon_months }) => {
      if (!chart_id) return errOut('phala_outlook_get', 'chart_id is required')
      try {
        const data = await callSidecarPath('/api/compute/phala/outlook', {
          chart_id, horizon_months: horizon_months ?? 12,
        })
        return dualOutput(data)
      } catch (err) { return errOut('phala_outlook_get', String(err), { chart_id }) }
    }
  )

  // ── L5 Mīmāṃsā aliases (3 tools — via platform primitive) ───────────────

  server.tool(
    'mimamsa_lel_query',
    '[Phase-1 alias] Mīmāṃsā LEL intake / life-event query (same as lel_query).',
    {
      chart_id: z.string().uuid().optional(),
      query:    z.string().optional().describe('Natural language life-event query'),
      ...GlobalBase,
    },
    async (params) => {
      try {
        const data = await callPlatformPrim('lel_query', params as Record<string, unknown>, principal)
        return dualOutput(data, 'mimamsa_lel_query')
      } catch (err) { return errOut('mimamsa_lel_query', String(err)) }
    }
  )

  server.tool(
    'mimamsa_outcome_record',
    '[Phase-1 alias] Record an outcome against a prediction (same as record_outcome).',
    {
      chart_id:    z.string().uuid(),
      prediction_id: z.string().optional(),
      outcome:     z.string().describe('Actual outcome description'),
      verdict:     z.enum(['confirmed', 'partial', 'denied']).optional(),
    },
    async (params) => {
      try {
        const data = await callPlatformPrim('record_outcome', params as Record<string, unknown>, principal)
        return dualOutput(data)
      } catch (err) { return errOut('mimamsa_outcome_record', String(err)) }
    }
  )

  server.tool(
    'mimamsa_calibration_get',
    '[Phase-1 alias] Query calibration stats for a chart (same as query_calibration).',
    {
      chart_id: z.string().uuid().describe('Chart UUID'),
      domain:   z.string().optional(),
      ...GlobalBase,
    },
    async ({ chart_id, domain, limit, offset }) => {
      try {
        const data = await callPlatformPrim('query_calibration', { chart_id, domain, limit, offset }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('mimamsa_calibration_get', String(err), { chart_id }) }
    }
  )

  // ── L1 Stream G PyJHora natal aliases (3 tools) ───────────────────────────

  server.tool(
    'ganita_natal_positions_compute',
    '[Phase-1 alias] Compute natal graha positions via PyJHora sidecar (same as compute_natal_positions).',
    BirthBase,
    async (params) => {
      try {
        const data = await callSidecarPath('/api/pyhora/compute', params as Record<string, unknown>)
        return dualOutput(data)
      } catch (err) { return errOut('ganita_natal_positions_compute', String(err)) }
    }
  )

  // WP-1.3 (b/c): ganita_dasha_periods_get + query_dasha_periods REPOINTED from the
  // vimshottari-only PyJHora sidecar to the DB-backed faceted capability (get_dashas), so
  // the audit-named dasha tools honor system_id (F-0354: ~437k non-vimshottari rows/chart
  // were dark) and requested windows (F-0471/0485: a fixed today-centered decade made
  // past/future timing unanswerable). Both now share the identical faceted schema +
  // handler as ganita_dashas_get — one authoritative dasha surface, no divergent duplicate.
  regAlias(server, 'ganita_dasha_periods_get',
    'L1 dasha periods, faceted by system/level/window (same as get_dashas / ganita_dashas_get). ' +
    'Honors system_id (all 8 systems: vimshottari, vimshottari_kp, yogini, ashtottari, ' +
    'chara_karaka, kalachakra, mudda, naisargika) and requested date windows. ' +
    'Defaults: system=vimshottari, level<=3, window=now±5y. ayanamsha_id has NO default — ' +
    'pass "lahiri_chitrapaksha" for the single-row current-dasha gate shape.',
    'marsys://tool/L1/get_dashas',
    DASHA_FACET_SCHEMA, principal)

  regAlias(server, 'query_dasha_periods',
    'L1 dasha periods, faceted by system/level/window (DB-backed, chart_id required). ' +
    'Honors system_id (all 8 systems) and requested date windows (as_of_date / window_start / ' +
    'window_end), echoing the applied filter back in facets_applied. Defaults: system=vimshottari, ' +
    'level<=3, window=now±5y. ayanamsha_id has NO default — pass "lahiri_chitrapaksha" for the ' +
    'single-row current-dasha gate shape.',
    'marsys://tool/L1/get_dashas',
    DASHA_FACET_SCHEMA, principal)

  server.tool(
    'ganita_special_lagnas_get',
    '[Phase-1 alias] Compute special lagnas + upagrahas via PyJHora sidecar (same as query_special_lagnas).',
    BirthBase,
    async (params) => {
      try {
        const data = await callSidecarPath('/api/pyhora/compute', params as Record<string, unknown>)
        return dualOutput(data)
      } catch (err) { return errOut('ganita_special_lagnas_get', String(err)) }
    }
  )
}

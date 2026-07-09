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
  if (!res.ok) throw new Error(`[alias] capability ${uri} failed (${res.status})`)
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
function dualOutput(data: unknown) {
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
        return dualOutput(data)
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
        return dualOutput(data)
      } catch (err) { return errOut(name, String(err)) }
    }
  )
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
  regAlias(server, 'bodha_signals_get',
    'L2 Bodha signals ranked by relevance (same as get_signals). R5 W2: frame (lagna/chandra/' +
    'surya/arudha/karakamsha) annotates a frame_context (never recomputes frozen salience); ' +
    'paradigm (parashari/jaimini/kp/tajika) filters to one tradition (default: all, unfiltered).',
    'marsys://tool/L2/query_signals',
    {
      domain:     z.string().optional(),
      top_k:      z.number().int().min(1).max(200).optional(),
      min_weight: z.number().min(0).max(1).optional(),
      frame:      z.enum(['lagna', 'chandra', 'surya', 'arudha', 'karakamsha']).optional(),
      paradigm:   z.enum(['parashari', 'jaimini', 'kp', 'tajika']).optional(),
    }, principal)

  // traverse_graph → bodha_graph_traverse_get
  regAlias(server, 'bodha_graph_traverse_get',
    'L2 chart graph traversal (same as traverse_graph). R5 W2: about/about_from/about_to accept ' +
    'address expressions (e.g. "lord_of(bhava 10)") resolved via the shared address resolver; ' +
    'direction/min_strength filter traversal. Gate: a "10th-lord to Moon" path resolves in ONE call ' +
    'via mode="paths", about_from="lord_of(bhava 10)", about_to={type:"graha",graha:"Moon"}, direction="directed".',
    'marsys://tool/L2/traverse_chart_graph',
    {
      mode:        z.enum(['neighbors', 'paths', 'cluster', 'convergence', 'contradictions']).optional(),
      start_node:  z.string().optional(),
      max_depth:   z.number().int().min(1).max(5).optional(),
      relation:    z.string().optional(),
      about:       z.union([z.string(), z.record(z.string(), z.unknown())]).optional(),
      about_from:  z.union([z.string(), z.record(z.string(), z.unknown())]).optional(),
      about_to:    z.union([z.string(), z.record(z.string(), z.unknown())]).optional(),
      direction:   z.enum(['directed', 'both']).optional(),
      min_strength: z.number().min(0).max(1).optional(),
    }, principal)

  // get_positions → ganita_positions_get
  regAlias(server, 'ganita_positions_get',
    'L1 graha positions (same as get_positions). R5 W2: frame (lagna/chandra/surya/arudha/' +
    'karakamsha, default lagna) re-bases house_d1 onto the requested reference sign, adding ' +
    'house_from_frame per row — e.g. frame="chandra" answers "what house is X in, from Moon" ' +
    'in this ONE call.',
    'marsys://tool/L1/get_positions',
    {
      frame: z.enum(['lagna', 'chandra', 'surya', 'arudha', 'karakamsha']).optional(),
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
    {
      // Override the shared ChartBase.ayanamsha_id description for this tool specifically:
      // ChartBase's generic "(default: 'lahiri_chitrapaksha')" wording is TRUE for
      // chart_facts_query but FALSE here — get_dashas.ts applies no ayanamsha filter unless
      // the caller supplies one (R5 W1 verifier finding; JL-010 doc fix).
      ayanamsha_id:  z.string().optional().describe(
        'Ayanamsha filter. NO server-side default — omitting it returns ALL 5 ayanamshas ' +
        '(one row per ayanamsha). Pass "lahiri_chitrapaksha" explicitly for the standard ' +
        'single-row current-dasha gate shape.'),
      as_of_date:    z.string().optional(),
      date_contains: z.string().optional(),
      date_from:     z.string().optional(),
      system:        z.string().optional().describe('Dasha system facet (default: vimshottari; "all" for every system).'),
      dasha_system:  z.string().optional().describe('Deprecated alias for system.'),
      level:         z.union([z.string(), z.number()]).optional().describe('Exact dasha level (1=Maha..5=Prana, or the name).'),
      all_levels:    z.boolean().optional().describe('Disable the default level<=3 cap.'),
      window_start:  z.string().optional(),
      window_end:    z.string().optional(),
      lord_graha:    z.string().optional(),
      fields:        z.string().optional().describe('Projection facet: "compact" (default), "all", or a comma-separated column list.'),
    }, principal)

  // get_temporal_windows → kala_windows_get
  regAlias(server, 'kala_windows_get',
    'L3 temporal activation windows (same as get_temporal_windows)',
    'marsys://tool/L3/query_temporal_activation',
    {
      start_date: z.string().optional(),
      end_date:   z.string().optional(),
      domain:     z.string().optional(),
    }, principal)

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
        return dualOutput(data)
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

  // assess_marriage → apex_marriage_assess
  regAlias(server, 'apex_marriage_assess',
    'Apex domain assess: marriage/relationship (same as assess_marriage)',
    'marsys://tool/L-DOMAIN/assess_marriage',
    {
      max_signals_per_lens:  z.number().int().min(1).max(50).optional(),
      max_contradictions:    z.number().int().min(1).max(100).optional(),
    }, principal)

  // assess_career → apex_career_assess
  regAlias(server, 'apex_career_assess',
    'Apex domain assess: career/profession (same as assess_career)',
    'marsys://tool/L-DOMAIN/assess_career',
    {
      max_signals_per_lens:  z.number().int().min(1).max(50).optional(),
      max_contradictions:    z.number().int().min(1).max(100).optional(),
    }, principal)

  // assess_health → apex_health_assess
  regAlias(server, 'apex_health_assess',
    'Apex domain assess: health/longevity (same as assess_health)',
    'marsys://tool/L-DOMAIN/assess_health',
    {
      max_signals_per_lens:  z.number().int().min(1).max(50).optional(),
      max_contradictions:    z.number().int().min(1).max(100).optional(),
    }, principal)

  // assess_wealth → apex_wealth_assess
  regAlias(server, 'apex_wealth_assess',
    'Apex domain assess: wealth/finance (same as assess_wealth)',
    'marsys://tool/L-DOMAIN/assess_wealth',
    {
      max_signals_per_lens:  z.number().int().min(1).max(50).optional(),
      max_contradictions:    z.number().int().min(1).max(100).optional(),
    }, principal)

  // yoga_activation_by_dasha → kala_yoga_activation_get
  regAlias(server, 'kala_yoga_activation_get',
    'Kāla yoga-activation-by-dasha timeline (same as yoga_activation_by_dasha)',
    'marsys://tool/L-TIMING/yoga_activation_by_dasha',
    {
      start_date: z.string().optional(),
      end_date:   z.string().optional(),
    }, principal)

  // get_cgm_subgraph → bodha_graph_subgraph_get
  regAlias(server, 'bodha_graph_subgraph_get',
    'L2 CGM subgraph extraction (same as get_cgm_subgraph)',
    'marsys://tool/L2/traverse_chart_graph',
    {
      start_node: z.string().optional(),
      subgraph:   z.boolean().optional().default(true),
    }, principal)

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
        return dualOutput(data)
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
        return dualOutput(data)
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
        return dualOutput(data)
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
        return dualOutput(data)
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

  server.tool(
    'ganita_dasha_periods_get',
    '[Phase-1 alias] Compute Vimshottari dasha chain via PyJHora sidecar (same as query_dasha_periods).',
    BirthBase,
    async (params) => {
      try {
        const data = await callSidecarPath('/api/pyhora/compute', params as Record<string, unknown>)
        return dualOutput(data)
      } catch (err) { return errOut('ganita_dasha_periods_get', String(err)) }
    }
  )

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

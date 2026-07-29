/**
 * P1 Phase-1 Naming Aliases — all 53 existing tools get <layer>_<topic>_<type> aliases.
 * ========================================================================================
 * Per BA-P1 brief §Step 4 (MCP_TOOL_NAMING_STANDARD §3):
 *   BOTH names call one handler. Old names are deprecated (not removed — Phase 3 removal gate).
 *   Dedup: bodha_remedies_get primary; bodha_remedies_search → alias; ref_remedies_search retained.
 *
 * DOCUMENTED DEFERRALS — RESOLVED at the RC-14 breaking flip (2026-07-23). All 6 were
 * RENAMED IN PLACE at their source registrations (old name gone, new canonical name live);
 * the old names moved into canonical_faces.json's deprecated_aliases for web-channel replay:
 *   1. recall_session     → session_recall        [session_tools.ts]
 *   2. list_my_sessions   → session_list          [session_tools.ts]
 *   3. list_my_charts     → catalog_charts_list   [chart_selection.ts]
 *   4. select_chart       → catalog_chart_select  [chart_selection.ts]
 *   5. holistic_bundle_chart_facts → bodha_bundle_get  [retrieval/holistic_bundle.ts]
 *   6. kala_temporal_bundle → kala_bundle_get     [retrieval/kala_temporal.ts]
 *
 * RC-14 ALSO removed the 43 legacy P1 short names (this file's canonical faces are KEPT;
 * the legacy duplicates are no-op'd by lib/deprecated_tool_gate.ts). This file registers
 * canonical layer_noun_verb faces — it is NOT removed.
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import {
  describeProxyFailure, resolveChartFactsAyanamsha,
  READING_DEPTH_ZOD, guardDeepDiveNotLossy, DeepDiveLossyFormError, type ReadingDepth,
} from './registry_bridge.js'
import { autoDetectTrimmableSections, finalizeMcpBudget, type TrimmableSection } from '../lib/response_budget.js'
import { classifyScope } from './intent_scope_classifier.js'

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

// W4-loop-1 (E-5 group1): the L0 ephemeris ref_* aliases used to proxy through
// callRegistryCap → /api/retrieval/capability, which reached the sidecar with the
// wrong/missing sidecar credential (401 "Invalid API key") and, for
// ref_planet_position_get, dropped `date` entirely (sidecar 500 date "undefined").
// Their canonical twins in l0_ephemeris.ts (query_planet_position /
// query_planet_transit / query_aspects_at_time / query_retrograde_periods /
// ephemeris_cache_year) call the sidecar DIRECTLY via a GET with the x-api-key
// header and work. Mirror that exact data path here (GET + x-api-key), not the
// registry proxy.
async function callSidecarGet(path: string): Promise<unknown> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (SIDECAR_API_KEY) headers['x-api-key'] = SIDECAR_API_KEY
  const res = await fetch(`${PYTHON_SIDECAR_URL}${path}`, {
    method: 'GET', headers, signal: AbortSignal.timeout(30_000),
  })
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    throw new Error(`[alias] sidecar GET ${path} failed (${res.status}): ${txt.slice(0, 200)}`)
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
//
// D-1.6 S-5 (R-1/R-8/CR-49 residual — phala_mitigation_get measured 99.9KB live despite this
// function's budgeting): the prior version called `applyResponseBudget` directly and SKIPPED
// budgeting entirely when `sections.length === 0` — which happens whenever the real bulk lives
// inside a JSON-encoded STRING nested inside a small (<=10 item) array (the surgical-primitives
// ToolBundle shape `{result:{results:[{content:"<json string>"}]}}`, R-29's double-encoding
// pattern), because autoDetectTrimmableSections only declares a section for arrays it can see
// AND that are longer than 10 — a 1-item bundle array never qualifies, and the array-based
// trimmer has no way to shrink a giant string. Routing through `finalizeMcpBudget` instead
// (same self-verifying entry point registry_bridge.ts's assess_*/traverse_graph/judgment_query
// already use) adds its last-resort bounded-depth long-string truncation fallback, which DOES
// reach that shape — this is a strict superset of the prior behavior (array trimming still runs
// first; string truncation only engages if arrays alone can't close the gap).
function dualOutput(data: unknown, toolName = 'unknown_tool') {
  let finalData: unknown = data
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>
    const sections = autoDetectTrimmableSections(obj, toolName)
    finalData = finalizeMcpBudget(obj, { maxKb: 40, sections })
  }
  const structuredContent = { type: 'object' as const, object: finalData }
  const json = JSON.stringify(finalData)
  if (Buffer.byteLength(json, 'utf8') > DUAL_OUTPUT_TEXT_THRESHOLD_BYTES) {
    return { structuredContent, content: [{ type: 'text' as const, text: '[large payload — see structuredContent]' }] }
  }
  return { structuredContent, content: [{ type: 'text' as const, text: json }] }
}
function errOut(tool: string, msg: string, extra?: Record<string, unknown>) {
  return { ...dualOutput({ ok: false, error: msg, tool, ...extra }), isError: true as const }
}

// ── EL-41 / B-1: per-requested-category receipt ─────────────────────────────────
// Every multi-category tool must report what happened to EACH requested category — never
// let one silently vanish from the response shape, even when its result is genuinely empty.
//
// Shape is the FROZEN C2 contract (~/elev-v2-shared/contracts/C2_PER_CATEGORY_RECEIPT_v1_0.md),
// not an ad-hoc one — γ builds against this exact shape. `receipt_state` is C8's closed,
// mechanically-derived enum (CONFIRMED|CATALOG_ONLY|DARK|MIXED); C8 §2 says the (0,0,0) triple
// is omitted as "never touched" — but every category THIS handler was explicitly asked for is,
// by construction, touched. A requested category with no real rows and no catalog-only match is
// therefore recorded as `dark_count: 1` (an obligation this response should have covered per the
// caller's own request, and didn't) rather than as a bare (0,0,0) — this keeps the EL-41 "never
// silently vanish" guarantee compatible with C8's closed enum instead of inventing a 5th state.
type CategoryReceiptState = 'CONFIRMED' | 'CATALOG_ONLY' | 'DARK' | 'MIXED'
interface CategoryReceipt {
  fact_category: string
  confirmed_count: number
  catalog_only_count: number
  dark_count: number
  receipt_state: CategoryReceiptState
  note?: string
}
function deriveReceiptState(confirmed: number, catalogOnly: number, dark: number): CategoryReceiptState {
  const nonZero = [confirmed > 0, catalogOnly > 0, dark > 0].filter(Boolean).length
  if (nonZero > 1) return 'MIXED'
  if (confirmed > 0) return 'CONFIRMED'
  if (catalogOnly > 0) return 'CATALOG_ONLY'
  return 'DARK'
}

/**
 * Defensive unwrap for callRegistryCap's return value. /api/retrieval/capability's handler
 * contract is `{ content: <realPayload>, is_error: boolean }` (see register_p1_ganita.ts's
 * documented A4 fix for the identical bug class — callRegistryCap in THIS file returns
 * `res.json().content`, which is that whole `{content, is_error}` object one level too
 * shallow, not the real payload) — but callers historically treated it as already-unwrapped.
 * Handles both shapes so a receipt/count built from `data` never silently reads past the
 * real payload into `undefined`.
 */
function unwrapCapabilityPayload(data: unknown): Record<string, unknown> {
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>
    if ('is_error' in obj && 'content' in obj && obj['content'] && typeof obj['content'] === 'object') {
      return obj['content'] as Record<string, unknown>
    }
    return obj
  }
  return {}
}

function extractRowsForReceipt(data: unknown): Record<string, unknown>[] {
  const payload = unwrapCapabilityPayload(data)
  return Array.isArray(payload['rows']) ? payload['rows'] as Record<string, unknown>[] : []
}

/** Builds a CategoryReceipt entry (frozen C2 shape) for every REQUESTED alias — never omits one,
 * even if empty (see the `dark_count: 1` note on the type above for why "empty" is never (0,0,0)). */
function buildCategoryReceipts(
  requestedAliases: string[],
  aliasMap: Record<string, string[]>,
  rows: Record<string, unknown>[],
): CategoryReceipt[] {
  const countByRealCategory = new Map<string, number>()
  for (const r of rows) {
    const cat = r['fact_category']
    if (typeof cat === 'string') countByRealCategory.set(cat, (countByRealCategory.get(cat) ?? 0) + 1)
  }
  return requestedAliases.map((alias): CategoryReceipt => {
    const realCats = aliasMap[alias]
    if (!realCats || realCats.length === 0) {
      const confirmed = 0, catalogOnly = 0, dark = 1
      return {
        fact_category: alias, confirmed_count: confirmed, catalog_only_count: catalogOnly, dark_count: dark,
        receipt_state: deriveReceiptState(confirmed, catalogOnly, dark),
        note: `"${alias}" has no known backing fact_category mapping — this alias is not wired to any stored data.`,
      }
    }
    const count = realCats.reduce((sum, c) => sum + (countByRealCategory.get(c) ?? 0), 0)
    if (count > 0) {
      return {
        fact_category: alias, confirmed_count: count, catalog_only_count: 0, dark_count: 0,
        receipt_state: deriveReceiptState(count, 0, 0),
      }
    }
    const confirmed = 0, catalogOnly = 0, dark = 1
    return {
      fact_category: alias, confirmed_count: confirmed, catalog_only_count: catalogOnly, dark_count: dark,
      receipt_state: deriveReceiptState(confirmed, catalogOnly, dark),
      note: `No ${realCats.join('/')} rows exist for this chart/ayanamsha — genuinely empty, not dropped.`,
    }
  })
}

// EL-41/B-1 (ganita_special_lagnas_get): public alias name → real backing chart_facts
// fact_category set. Live-verified against chart 482012f1 — see the tool registration's
// comment for the full root-cause writeup (only 'special_lagna' happened to match verbatim).
const SPECIAL_LAGNA_CATEGORY_MAP: Record<string, string[]> = {
  special_lagna: ['special_lagna'],
  upagraha: ['upagraha_position', 'sun_derived_upagraha'],
  saham: ['saham_position'],
  sensitive_point: ['sensitive_point_gulika_mandi', 'sensitive_degree_check', 'nakshatra_pada_sensitive'],
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
//
// `opts.paramAliases`: CR-42 fix — maps an alias-only param name (e.g. `planet`, the name
// LLM callers naturally reach for) onto the underlying capability's native param name
// (e.g. `graha`) before the call. Without this, a caller-supplied `planet` value would
// either be stripped by the zod schema (if not declared at all) or passed through under
// the WRONG key name that the capability's handler never reads — both are silent
// filter-fallthrough. If both the alias name and the native name are supplied, the native
// name wins (caller explicitly used the capability's own vocabulary).
function regAlias(
  server: McpServer,
  name: string,
  desc: string,
  uri: string,
  extraSchema: Record<string, z.ZodTypeAny> = {},
  principal: Principal,
  opts?: { paramAliases?: Record<string, string> },
) {
  server.tool(
    name, `[Phase-1 alias] ${desc}. Delegates to the same handler as the legacy tool name.`,
    { ...ChartBase, ...extraSchema },
    async (params) => {
      const { chart_id, ayanamsha_id, limit, offset, ...rest } = params as Record<string, unknown>
      if (!chart_id) return errOut(name, 'chart_id is required')
      try {
        const resolvedRest: Record<string, unknown> = { ...rest }
        if (opts?.paramAliases) {
          for (const [aliasKey, nativeKey] of Object.entries(opts.paramAliases)) {
            if (resolvedRest[aliasKey] !== undefined) {
              if (resolvedRest[nativeKey] === undefined) resolvedRest[nativeKey] = resolvedRest[aliasKey]
              delete resolvedRest[aliasKey]
            }
          }
        }
        const data = await callRegistryCap(uri, {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          limit: (limit as number) ?? 25000, offset: (offset as number) ?? 0, ...resolvedRest,
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
  //
  // SAMAPANA Track B item 4a (correctness fix, independent of the footgun question below):
  // `mode` was a DEAD parameter. This tool used to be registered via the generic `regAlias`
  // helper, which spreads every extra param straight through under its own key — `mode` rode
  // through under the literal key "mode", but query_ucd.ts's handler only ever reads
  // `response_format` (defaulting to 'summary' when that key is absent/invalid). No
  // `paramAliases` entry mapped mode → response_format (contrast bodha_remedies_get's
  // `planet` → `graha` mapping below), so `bodha_chart_digest_get(mode:'full')` always
  // silently served response_format:'summary' server-side — unfixable by the caller via the
  // documented param. This is a bespoke registration (not `regAlias`) because it also needs
  // the reading_depth deep-dive guard (item 3) and the footgun fix's contract-side forcing
  // (item 4b), neither of which `regAlias`'s generic plumbing supports.
  //
  // Item 4 footgun disposition: per the brief, the PREFERRED fix is contract-side (less
  // blast radius) — the deep-dive contract's mandatory first call always passes 'full'
  // rather than flipping this tool's own default. That is what `reading_depth` does below.
  // The default itself is left at 'summary' (footgun still live for a caller who omits BOTH
  // `mode` and `reading_depth`) — documented here per the brief's explicit instruction to
  // record the footgun-nature even when choosing the contract-side fix.
  server.tool(
    'bodha_chart_digest_get',
    '[Phase-1 alias] L2 UCD chart orientation digest (same as get_chart_orientation). ' +
    'Delegates to the same handler as the legacy tool name. FOOTGUN NOTICE: `mode` defaults ' +
    "to 'summary' (top-10 signals) — this is the MANDATORY first call of every reading (B.11), " +
    "so an unqualified call opens every reading with a terse digest unless overridden. Pass " +
    "reading_depth:'deep_dive' (forces mode:'full' regardless of what you pass for `mode`) for " +
    "a beyond-acharya-grade deep dive, or mode:'full' directly for a one-off.",
    {
      ...ChartBase,
      mode: z.enum(['summary', 'full']).optional().describe(
        "Output verbosity, mapped onto the underlying query_ucd 'response_format'. 'summary' " +
        "(default if reading_depth is not 'deep_dive'): top-10 signals — a lossy reduction, " +
        "not a mere byte-ceiling knob. 'full': uncapped top_signals (up to top_k_signals, " +
        "forced to 100 under reading_depth:'deep_dive')."
      ),
      reading_depth: READING_DEPTH_ZOD,
    },
    async (params) => {
      const { chart_id, ayanamsha_id, limit, offset, mode, reading_depth, ...rest } = params as Record<string, unknown>
      if (!chart_id) return errOut('bodha_chart_digest_get', 'chart_id is required')
      try {
        const rd = reading_depth as ReadingDepth | undefined
        // Item 3 guard: a deep dive can never be silently routed through the lossy 'summary'
        // form — refuse the self-contradictory combination instead of picking a side.
        guardDeepDiveNotLossy(rd, 'mode', mode as string | undefined, ['summary'])
        // Item 4b: reading_depth:'deep_dive' forces the full digest even if the caller never
        // touches `mode` at all.
        const response_format = rd === 'deep_dive' ? 'full' : (mode as string | undefined ?? 'summary')
        const data = await callRegistryCap('marsys://tool/L2/query_ucd', {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          limit: (limit as number) ?? 25000, offset: (offset as number) ?? 0,
          ...rest, response_format,
          ...(rd === 'deep_dive' ? { top_k_signals: 100 } : {}),
        }, principal)
        return dualOutput(data, 'bodha_chart_digest_get')
      } catch (err) {
        if (err instanceof DeepDiveLossyFormError) return errOut('bodha_chart_digest_get', err.message)
        return errOut('bodha_chart_digest_get', String(err), { chart_id })
      }
    }
  )

  // get_domain_reading → bodha_domain_reading_get
  regAlias(server, 'bodha_domain_reading_get',
    'L2 domain reading via Bodha synthesis (same as get_domain_reading). D-1.5b: the ' +
    'question-lens family is paginated (lens_limit/lens_offset, default 60/page) — see ' +
    'response.lens_pagination.total for the true family size.',
    'marsys://tool/L2/query_domain_reading',
    {
      domain: z.string().describe('Life domain (career, health, relationship, wealth, etc.)'),
      max_signal_refs: z.number().int().min(1).max(2000).optional(),
      response_format: z.enum(['default', 'full']).optional(),
      lens_limit: z.number().int().min(1).max(200).optional()
        .describe('D-1.5b response budget: max question-lens rows to return (default 60).'),
      lens_offset: z.number().int().min(0).optional()
        .describe('D-1.5b response budget: pagination offset into the question-lens family (default 0).'),
      max_signals_per_lens: z.number().int().min(1).max(100).optional()
        .describe('D-1.5b B-7 response budget: max ranked_signals served INSIDE each lens ' +
          '(default 25, max 100). The stored lens holds hundreds–thousands of rows; serving it ' +
          'unbounded blew this response past 900KB. See per-lens ranked_signals_total for the ' +
          'true family size; response_format=full raises the cap to 200/lens.'),
    }, principal)

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
      // §N.6 serving-reach (Gate B / B2_sudarshana): filter to one signal_type_class. This
      // flows verbatim through `...rest` to query_signals, which applies it in the WHERE clause
      // BEFORE the salience LIMIT/candidate-pool cap — so a class-scoped query returns ALL rows
      // of that class regardless of their global salience rank. Without this facet on the alias
      // schema, the MCP SDK strips the param and legitimately low-salience structural corroboration
      // classes (sudarshana_agreement et al., ~rank 8k-9k of ~9.9k per ayanamsha) were unreachable
      // through this surface by ANY domain/top_k/offset combination. Free string (no enum): an
      // incomplete enum is exactly what hid these classes from callers.
      signal_type_class: z.string().optional()
        .describe('Filter to one bodha_msr_signals.signal_type_class (e.g. sudarshana_agreement, ' +
          'yoga, dosha, karaka_alignment, composite_state). Applied pre-salience-cap, so it reaches ' +
          'low-salience corroboration classes a chart-wide salience page never surfaces.'),
    },
    async (params) => {
      const { chart_id, ayanamsha_id, limit, offset, min_weight, ...rest } = params as Record<string, unknown>
      if (!chart_id) return errOut('bodha_signals_get', 'chart_id is required')
      try {
        // D15b-F3 (R-18 param no-op audit): this schema documents `min_weight`, but the
        // downstream capability (query_signals.ts) only ever reads `args['min_salience']` —
        // `min_weight` was forwarded verbatim via `...rest` and silently ignored on every
        // call (a documented param that filters nothing). Alias it onto `min_salience`
        // before forwarding; an explicit `min_salience` in the caller's own params (if ever
        // added) still wins since it would already be a rest key.
        const data = await callRegistryCap('marsys://tool/L2/query_signals', {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          limit: (limit as number) ?? 25000, offset: (offset as number) ?? 0,
          ...(min_weight != null && rest['min_salience'] == null ? { min_salience: min_weight } : {}),
          ...rest,
        }, principal) as Record<string, unknown>
        const inner = data['content'] as Record<string, unknown> | undefined
        if (inner) {
          // Lane 5 (§N.6 (iii) layered envelope): a small verdict ahead of the (budgeted,
          // potentially large) row list — tier distribution + top subjects, computed from
          // signals ALREADY fetched in this same response (zero new query, B.10). Built
          // BEFORE the trimmer runs so the verdict reflects the untrimmed served set.
          const rows = Array.isArray(inner['signals']) ? inner['signals'] as Record<string, unknown>[] : []
          const tierCounts: Record<string, number> = {}
          const subjectCounts: Record<string, number> = {}
          for (const r of rows) {
            const tier = typeof r['signature_tier'] === 'string' ? r['signature_tier'] as string : 'unknown'
            tierCounts[tier] = (tierCounts[tier] ?? 0) + 1
            const facts = Array.isArray(r['constituent_facts_array']) ? r['constituent_facts_array'] as string[] : []
            for (const f of facts.slice(0, 1)) { subjectCounts[f] = (subjectCounts[f] ?? 0) + 1 }
          }
          const topSubjects = Object.entries(subjectCounts).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([k]) => k)
          inner['verdict_summary'] = {
            served_count: rows.length,
            tier_distribution: tierCounts,
            top_subjects_by_frequency: topSubjects,
            note: 'Small verdict over THIS response\'s own served rows (§N.6 (iii)) — not a re-query.',
          }
          // W3-L5 (budget unification, W-8): migrated off bare applyResponseBudget onto the
          // self-verifying finalizeMcpBudget entry point (this file's own dualOutput below
          // applies a second, file-wide auto-detect pass at 40KB as a backstop — the two are
          // not redundant: this narrower 25KB pre-trim on `inner` alone leaves headroom for
          // verdict_summary computed just above).
          finalizeMcpBudget(inner, { maxKb: 25, sections: [signalsSection()] })
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
  // EL-41/B-1 sweep item: broken out of the generic regAlias into a bespoke handler so an
  // EXPLICIT `categories` request gets a `category_receipts` entry per requested category
  // (never silently absent, even when genuinely empty) — same discipline as
  // ganita_special_lagnas_get and phala_predictive_anchors_get above. Unlike special-lagnas,
  // these category names already match get_positions.ts's real fact_category values verbatim
  // (no alias-mapping bug here) — this is the "an empty category must say so" half of
  // EL-41/B-1, not a naming fix. Only fires when `categories` is explicitly passed — the
  // CR-50 default page (no categories, no include_upagrahas) isn't a multi-category request.
  server.tool(
    'ganita_positions_get',
    'L1 graha positions (same as get_positions). R5 W2: frame (lagna/chandra/surya/arudha/' +
    'karakamsha, default lagna) re-bases house_d1 onto the requested reference sign, adding ' +
    'house_from_frame per row — e.g. frame="chandra" answers "what house is X in, from Moon" ' +
    'in this ONE call. The response\'s own `frame_note` field states exactly how many rows in ' +
    'THIS call actually carry house_from_frame (R-28: pass ayanamsha_id explicitly for full ' +
    'coverage — an unfiltered call spanning all 5 ayanamshas may only re-base a subset). ' +
    'CR-50: the default page serves ONLY the 9 classical grahas + Lagna — pass ' +
    'include_upagrahas=true to also fetch upagrahas/aprakasha bodies (served after, never ' +
    'interleaved into the default page).',
    {
      ...ChartBase,
      frame:  z.enum(['lagna', 'chandra', 'surya', 'arudha', 'karakamsha']).optional(),
      planet: z.string().optional().describe(
        'Filter to a single graha (e.g. "Sun", "Moon", "Mars"). SC-20 fix: this alias previously ' +
        'had no planet param at all, so a caller had no way to narrow the payload.'),
      include_upagrahas: z.boolean().optional().describe(
        'CR-50: when true, also serves upagraha_position/aprakasha_position rows AFTER the 9 ' +
        'grahas + Lagna. Default false — the default page is grahas + Lagna only.'),
      categories: z.array(z.enum(['graha_position', 'upagraha_position', 'aprakasha_position'])).optional()
        .describe('Explicit category list — overrides the CR-50 default and include_upagrahas entirely. ' +
          'When passed, the response carries a `category_receipts` entry for EVERY requested category ' +
          '(EL-41/B-1) — never silently absent even if a category is genuinely empty for this chart.'),
    },
    async (params) => {
      const { chart_id, ayanamsha_id, limit, offset, ...rest } = params as Record<string, unknown>
      if (!chart_id) return errOut('ganita_positions_get', 'chart_id is required')
      try {
        const requestedCategories = rest['categories'] as string[] | undefined
        const data = await callRegistryCap('marsys://tool/L1/get_positions', {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          limit: (limit as number) ?? 25000, offset: (offset as number) ?? 0, ...rest,
        }, principal)
        const payload = unwrapCapabilityPayload(data)
        if (requestedCategories && requestedCategories.length > 0) {
          const rows = Array.isArray(payload['rows']) ? payload['rows'] as Record<string, unknown>[] : []
          // Identity map: these category names already equal their own real fact_category
          // (verified against get_positions.ts's SQL) — no alias translation needed here.
          const identityMap = Object.fromEntries(requestedCategories.map(c => [c, [c]]))
          payload['category_receipts'] = buildCategoryReceipts(requestedCategories, identityMap, rows)
        }
        return dualOutput(payload, 'ganita_positions_get')
      } catch (err) { return errOut('ganita_positions_get', String(err), { chart_id }) }
    }
  )

  // ── W4-loop-1 (E-6 group4): fronting tools for computed-but-unserved assets ──────
  // Registry capabilities existed (or were added this pass) but had NO LLM-facing MCP tool.

  // ga_medical → ganita_medical_get (registry cap marsys://tool/L1/get_medical_indications)
  regAlias(server, 'ganita_medical_get',
    'L1 classical medical (Vaidya-phala) indications for a chart (ga_medical). NOT a diagnosis — ' +
    'per-graha dosha/organ watch-indications with classical citations.',
    'marsys://tool/L1/get_medical_indications',
    {
      graha:           z.string().optional().describe('Filter by graha (e.g. Sun, Moon, Mars).'),
      indication_tier: z.string().optional().describe('Filter by indication tier.'),
    }, principal)

  // ga_vastu → ganita_vastu_get (registry cap marsys://tool/L1/get_vastu_directions)
  regAlias(server, 'ganita_vastu_get',
    'L1 Vāstu graha→direction map for a chart (ga_vastu_planet_direction_map).',
    'marsys://tool/L1/get_vastu_directions',
    {
      graha:           z.string().optional().describe('Filter by graha.'),
      direction:       z.string().optional().describe('Filter by direction (e.g. East, North).'),
      indication_tier: z.string().optional().describe('Filter by indication tier.'),
    }, principal)

  // ga_ayurdaya → ganita_ayurdaya_get (longevity bands — answers "how long / longevity band")
  regAlias(server, 'ganita_ayurdaya_get',
    'L1 classical longevity (Āyurdāya) computations for a chart (Piṇḍāyu/Aṃśāyu/Naisargikāyu — ' +
    'total_years + band alpayu/madhyayu/purnayu). NOT a death prediction.',
    'marsys://tool/L1/get_ayurdaya',
    { method: z.string().optional().describe('Filter by method fact_subject (AMSAYU, PINDAYU, NISARGAYU).') },
    principal)

  // ga_sensitive_degree → ganita_sensitive_degrees_get
  // MC-029 (Śodhana Builder T6 "YOGI-BINDU"): also serves the Yogi/Avayogi/Duplicate-Yogi/
  // Sahayogi Tajika construct (fact_category=sensitive_point_yogi) — same tool, one more
  // served category, distinguishable via the fact_category field on each returned row.
  regAlias(server, 'ganita_sensitive_degrees_get',
    'L1 sensitive-degree checks for a chart (gaṇḍānta/sandhi/mṛtyu-bhāga/pushkara etc.), ' +
    'plus the Yogi/Avayogi/Duplicate-Yogi/Sahayogi Tajika construct (subjects YOGI/AVAYOGI/' +
    'DUPLICATE_YOGI/SAHAYOGI — Yogi Sphuta = Sun+Moon+93°20\', its nakshatra lord = Yogi ' +
    'Graha; Avayogi = Yogi+186°40\', its nakshatra lord = Avayogi Graha; Duplicate-Yogi/' +
    'Sahayogi = the rasi lord of the Yogi Sphuta\'s own sign).',
    'marsys://tool/L1/get_sensitive_degrees',
    {
      subject:    z.string().optional().describe('Filter by fact_subject (graha code e.g. SUN, VEN, or a Yogi-system subject YOGI/AVAYOGI/DUPLICATE_YOGI/SAHAYOGI).'),
      check_type: z.string().optional().describe('Filter by fact_key (specific check).'),
    }, principal)

  // Doctrine Campaign D-1 Night-1, Lane 5: ga_vichara ("judged structure", Lane 2's new
  // asset) → ganita_vichara_get (registry cap marsys://tool/L1/get_vichara). Born
  // §N.6-conformant — the registry handler itself already ships a layered
  // {verdict, digest, rows} response, loud facet rejection, and an honest empty_reason
  // (including "asset not built yet" while Lane 2 is unmerged) — this alias just fronts it.
  regAlias(server, 'ganita_vichara_get',
    'L1 ga_vichara ("judged structure") — the judgment layer on top of ga_structural: ' +
    'valence_pass (functional-lordship valence, e.g. 8L-Mars→H2 strong_malefic), ' +
    'varga_ratification (ratification_factor ∈ [0.6,1.4] per domain×subject), ' +
    'varga_ratification_divergence (a varga flipping D1\'s dignity direction — rankable ' +
    'evidence), varga_consistency (continuous vargottama-generalized index, 0..1), ' +
    'leverage_index (domain_load_bearing_weight ÷ capability, dasha-runway-weighted — ' +
    'the number remedy/intervention-timing ranks on). Every row carries ' +
    'constituent_fact_ids resolving back to chart_facts (§N.5). Response is a layered ' +
    'envelope: verdict (family counts) + digest (per-family summary) + paginated rows. ' +
    'If ga_vichara has not been built for this chart yet, returns an honest empty_reason ' +
    '(not an error).',
    'marsys://tool/L1/get_vichara',
    {
      family: z.enum([
        'valence_pass', 'varga_ratification', 'varga_ratification_divergence',
        'varga_consistency', 'leverage_index',
      ]).optional().describe('Filter to one vichara_family. Unknown values are rejected loudly, never silently ignored.'),
      domain: z.enum(['wealth', 'career', 'marriage', 'health', 'general']).optional()
        .describe('Filter by domain (only meaningful for varga_ratification/varga_ratification_divergence/leverage_index).'),
      subject: z.string().optional().describe('Filter by subject (graha/lord/karaka code, e.g. VENUS or venus — case-insensitive).'),
    }, principal)

  // ga_yoga_firings → ganita_yoga_firings_get (registry cap marsys://tool/L1/get_yoga_firings).
  // Doctrine Campaign D-1 Night-1, Lane 5 (§N.6 CR-76 avoidance): ga_yoga_firings was a
  // computed asset (~50-56 rows/chart, now carrying Lane 3's grounds_jsonb ledger) with NO
  // deployed MCP tool serving it — the same dark-asset failure class this lane exists to
  // prevent recurring. Default fired=true keeps catalog-only rows from ever rendering as a
  // finding (CR-72/CR-43) unless the caller explicitly asks for all/non-fired rows.
  regAlias(server, 'ganita_yoga_firings_get',
    'L1 detailed Nābhasa/yoga firing rows for a chart (ga_yoga_firings) — per-yoga strength ' +
    'scoring, bhaṅga/cancellation, partial-formation %, dāśā-activation windows, and (when ' +
    'present) Lane 3\'s grounds_jsonb verdict ledger. Default fired=true (catalog-only rows ' +
    'never served as findings — CR-72/CR-43); pass all=true or fired=false to see them.',
    'marsys://tool/L1/get_yoga_firings',
    {
      fired:             z.boolean().optional().describe('Filter by fired status (default: true).'),
      all:               z.boolean().optional().describe('If true, ignore the fired filter (serve fired + non-fired).'),
      bhanga_active:     z.boolean().optional().describe('Filter to firings with an active bhaṅga (cancellation) rule.'),
      is_partial:        z.boolean().optional().describe('Filter to partially-formed yogas.'),
      yoga_canonical_id: z.string().optional().describe('Filter to a specific yoga by canonical id.'),
    }, principal)

  // Doctrine Campaign D-3 (Kāla Taraṅga), Lane T-1: sign-keyed Aṣṭakavarga (D-1.5b Lane B-2
  // ashtakavarga_bindu_sign / ashtakavarga_kakshya_boundary chart_facts) → transit-gating
  // (SAV/BAV damp/amplify per sign) + dated kakṣyā sub-windows (registry cap
  // marsys://tool/L1/get_av_transit_gating). No default mode/planet/dates for
  // kakshya_windows — CR-87: nothing here silently falls back onto a cached chart/planet/date.
  regAlias(server, 'ganita_av_transit_gating_get',
    'D-3 Kāla Taraṅga: sign-keyed Aṣṭakavarga transit gating + kakṣyā sub-windows for a ' +
    'chart. mode="sav_bav_gating" (default) serves SAV/BAV bindu counts per sign classified ' +
    'damping/amplifying/neutral against the classical mean (~28.08 bindus/sign) — used to ' +
    'damp or amplify a timing window when a transiting planet crosses that sign. Filter by ' +
    'sign_number, house (resolved via the chart LAGNA), or graha (BAV only). mode=' +
    '"kakshya_windows" (requires planet, target_sign, start_date, end_date — no defaults) ' +
    'returns dated ~3.75-degree kakṣyā sub-arcs the planet crosses in that sidereal sign ' +
    'across the date range, each tagged with its classical kakṣyā lord and real entry/exit ' +
    'dates derived from the planet\'s actual transit speed (not a fixed day-count).',
    'marsys://tool/L1/get_av_transit_gating',
    {
      mode:        z.enum(['sav_bav_gating', 'kakshya_windows']).optional(),
      sign_number: z.number().int().min(1).max(12).optional().describe('sav_bav_gating: filter to one sidereal sign.'),
      house:       z.number().int().min(1).max(12).optional().describe('sav_bav_gating: filter by house (resolved via LAGNA).'),
      graha:       z.string().optional().describe('sav_bav_gating: filter BAV to one graha.'),
      planet:      z.string().optional().describe('kakshya_windows (required): transiting planet, e.g. "Saturn".'),
      target_sign: z.number().int().min(1).max(12).optional().describe('kakshya_windows (required): target sidereal sign 1-12.'),
      start_date:  z.string().optional().describe('kakshya_windows (required): YYYY-MM-DD.'),
      end_date:    z.string().optional().describe('kakshya_windows (required): YYYY-MM-DD.'),
    }, principal)

  // ka_tulana → kala_priority_ranking_get (registry cap marsys://tool/L3/call_priority_ranking)
  // MC-024 (ŚODHANA T4): added domain/domains filter (previously undeclared here — silently
  // dropped at the zod boundary even though the capability now honors it) and disclosure of
  // the neutral-dignity down-rank the underlying capability applies (a "dignity state =
  // neutral" descriptor row is rarely a genuine priority signal — down-ranked, not dropped).
  regAlias(server, 'kala_priority_ranking_get',
    'L3 priority-ranked signals for a chart in a period (ka_tulana service) — ranks active ' +
    'signals by salience × activation_strength × convergence. Which signals deserve attention ' +
    'in a time window. Neutral-dignity descriptor rows ("dignity state = neutral") are down-' +
    'ranked (priority_score x0.3, flagged via neutral_dignity_downranked per row) rather than ' +
    'treated as genuine priority findings — see neutral_dignity_downranked_count. Filter by ' +
    'domain/domains (career/character/health/relationship/spirituality/wealth) to scope to a ' +
    'life domain. [ṢAḌ-DARŚANA W0.4] Superseded by kala_priority_get (VIEW 5 PRIORITIZE), ' +
    'which wraps this SAME capability on the elevated kala_* envelope (argument-shaped ' +
    'reading, tri-plane pointers into EXPLAIN/AHEAD/ELECT, coverage, freshness, ' +
    'calibration_maturity) — prefer kala_priority_get for new callers. This alias remains ' +
    'live, not retired.',
    'marsys://tool/L3/call_priority_ranking',
    {
      date_from: z.string().optional().describe('Start of evaluation period (YYYY-MM-DD).'),
      date_to:   z.string().optional().describe('End of evaluation period (YYYY-MM-DD).'),
      top_k:     z.number().int().min(1).max(100).optional().describe('Max signals (default 20).'),
      domain:    z.string().optional().describe(
        'Filter to ONE life domain (e.g. "wealth", "career", "health", "relationship", ' +
        '"spirituality", "character"), matched case-insensitively. Takes precedence over `domains`.'),
      domains:   z.array(z.string()).optional().describe(
        'Filter to ANY of these life domains (OR/overlap match), case-insensitive. Ignored if `domain` is also given.'),
    }, principal)

  // bg_sign_medical → ref_sign_medical_get (global reference)
  globalAlias(server, 'ref_sign_medical_get',
    'L0 rāśi→medical reference (bg_sign_medical): sign→body_part/organ_systems/element/dosha (Kālapuruṣa).',
    'marsys://tool/L0/query_sign_medical',
    {
      sign_number: z.number().int().min(1).max(12).optional().describe('Filter by sign number (1=Aries..12=Pisces).'),
      sign_name:   z.string().optional().describe('Filter by sign name (case-insensitive).'),
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
    '[Phase-1 alias] L3 temporal activation windows (same as get_temporal_windows). ' +
    '[ṢAḌ-DARŚANA W0.4 deprecation notice — not retired, still live]: for "what is active ' +
    'now" / "what is coming" queries, prefer kala_now_get (current state) or ' +
    'kala_ahead_get (forward-dated windows + projections) — both re-present this same ' +
    'substrate on the elevated argument-shaped envelope (question_frame, tri_plane ' +
    'pointers, 3-state coverage). This tool remains the raw low-level primitive.',
    {
      ...ChartBase,
      start_date: z.string().optional().describe('Start of date range (mapped to date_from).'),
      end_date:   z.string().optional().describe('End of date range (mapped to date_to).'),
      as_of:      z.string().optional().describe('Point-in-time date (mapped to as_of) — only windows active as of this date; overrides start_date/end_date.'),
      domain:     z.string().optional().describe('Filter to activations affecting this life domain.'),
    },
    async (params) => {
      const { chart_id, ayanamsha_id, limit, offset: _offset, start_date, end_date, as_of, domain } =
        params as Record<string, unknown>
      void _offset // this primitive has no offset concept
      if (!chart_id) return errOut('kala_windows_get', 'chart_id is required')
      try {
        const data = await callRegistryCap('marsys://tool/L3/query_temporal_activation', {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          ...(start_date ? { date_from: start_date } : {}),
          ...(end_date ? { date_to: end_date } : {}),
          ...(as_of ? { as_of } : {}),
          ...(domain ? { domain } : {}),
          ...(limit != null ? { top_k: limit } : {}),
        }, principal)
        // SATYA-ŚEṢA W3 (2026-07-25): this call was missing dualOutput's second
        // (toolName) argument, so autoDetectTrimmableSections's recover_via
        // pointer (surfaced on every trimmed response's drill_pointers) named
        // the tool 'unknown_tool' instead of 'kala_windows_get' — a caller
        // trying to page through a trimmed result had no honest instrument
        // name to call back with.
        return dualOutput(data, 'kala_windows_get')
      } catch (err) { return errOut('kala_windows_get', String(err), { chart_id }) }
    }
  )

  // get_projections → kala_projections_get
  // CR-6 (S-4): this alias used to declare start_date/end_date, which the underlying
  // primitive (query_projections.ts) has NEVER understood (it reads horizon_years /
  // domain / limit — no date_from/date_to concept at all) — those two params were a
  // total silent no-op. Worse, domain and max_projections (which the primitive AND
  // get_projections DO honor) were absent from the schema entirely, so a caller
  // passing them had them silently stripped before the handler ever ran. Rewritten
  // as a direct mirror of get_projections (registry_bridge.ts) rather than the
  // generic regAlias() shape, including its client-side max_projections cap (F-008).
  server.tool(
    'kala_projections_get',
    '[Phase-1 alias] L3 time-indexed probabilistic projections (same as get_projections). ' +
    '[ṢAḌ-DARŚANA W0.4 deprecation notice — not retired, still live]: for "what is coming" ' +
    'queries, prefer kala_ahead_get, which re-presents this same kala_bhavishya substrate ' +
    '(probability_tier included) on the elevated argument-shaped envelope (question_frame, ' +
    'tri_plane pointers, 3-state coverage, falsifier). Per SHAD_DARSHANA_BRIEF_v2_0.md §7 ' +
    'rail, kala_ahead_get is the intended AHEAD-view replacement; this tool remains the raw ' +
    'low-level primitive.',
    {
      ...ChartBase,
      domain: z.string().optional().describe('Domain to project (e.g. career, relationship).'),
      horizon_years: z.number().int().min(1).max(20).optional().describe('Projection horizon in years (default: 5).'),
      max_projections: z.number().int().min(1).max(200).optional().describe(
        'Max projections to return (default: 20; the primitive is otherwise unbounded).'
      ),
    },
    async (params) => {
      const { chart_id, ayanamsha_id, domain, horizon_years, max_projections } =
        params as Record<string, unknown>
      if (!chart_id) return errOut('kala_projections_get', 'chart_id is required')
      try {
        const data = await callRegistryCap('marsys://tool/L3/query_projections', {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          ...(domain ? { domain } : {}),
          horizon_years: (horizon_years as number | undefined) ?? 5,
        }, principal)
        const projData = data as Record<string, unknown>
        const projections = (projData['projections'] as unknown[]) ?? []
        const cap = (max_projections as number | undefined) ?? 20
        const boundedProjections = projections.slice(0, cap)
        return dualOutput({
          ...projData,
          projections: boundedProjections,
          projections_total: projections.length,
          projections_returned: boundedProjections.length,
        }, 'kala_projections_get')
      } catch (err) { return errOut('kala_projections_get', String(err), { chart_id }) }
    }
  )

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
  //
  // CR-42/R-19/R-20 fix (D-1.6 S-1): `graha`/`planet` were NOT in this alias's zod schema —
  // the MCP SDK strips any param an LLM caller sends that isn't declared in the tool's
  // input shape, so a `planet="Saturn"` filter was silently discarded before the request
  // body was even built (never reached `...rest`, never reached the underlying
  // L2/query_remedies capability's `graha` filter at all). A Saturn-scoped remedy query
  // therefore served ALL grahas' resonances/prescriptions unfiltered — the exact "Saturn
  // query must never serve Jupiter remedies" failure mode this fix closes. `planet` is
  // accepted as an alias of the capability's native `graha` param name.
  // PARISHODHANA B1 (R-29/EL-51 follow-up): `fields` was not declared on this alias's
  // zod schema — same silent-param-strip failure mode CR-42 fixed for graha/planet
  // above. The underlying L2/query_remedies capability's `fields='all'` recovery path
  // (its own drill_pointers advertise it, and it's the documented way to reach
  // associated_*_array / estimated_cost_inr_range_jsonb / the raw prescription_detail_jsonb)
  // was therefore unreachable through this MCP tool — always silently forced to
  // 'compact' regardless of what a caller passed. Now declared and forwarded.
  regAlias(server, 'bodha_remedies_get',
    'L2 remedy recommendations via Bodha (PRIMARY Phase-1 name for get_remedies)',
    'marsys://tool/L2/query_remedies',
    {
      domain: z.string().optional(),
      graha: z.string().optional().describe('Filter by target graha (e.g. Saturn, Venus) — case-insensitive.'),
      planet: z.string().optional().describe('Alias of `graha`.'),
      tradition: z.string().optional(),
      fields: z.enum(['compact', 'all']).optional().describe(
        "'compact' (default) narrates + drops always-null/redundant columns; 'all' returns full raw rows."),
    }, principal, { paramAliases: { planet: 'graha' } })

  // Also: bodha_remedies_search as secondary alias
  regAlias(server, 'bodha_remedies_search',
    'L2 remedy search via Bodha (alias of bodha_remedies_get)',
    'marsys://tool/L2/query_remedies',
    {
      domain: z.string().optional(),
      keyword: z.string().optional(),
      graha: z.string().optional().describe('Filter by target graha (e.g. Saturn, Venus) — case-insensitive.'),
      planet: z.string().optional().describe('Alias of `graha`.'),
      tradition: z.string().optional(),
      fields: z.enum(['compact', 'all']).optional().describe(
        "'compact' (default) narrates + drops always-null/redundant columns; 'all' returns full raw rows."),
    }, principal, { paramAliases: { planet: 'graha' } })

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
  //
  // EL-41/B-1 fix: this WAS a generic `regAlias(...)` registration, which forwards
  // callRegistryCap's return value verbatim into dualOutput. query_predictive_anchors.ts
  // (the underlying L4 capability) ALREADY computes an honest `empty_reason`/`known_gap`
  // block whenever `anchors` comes back empty (§N.6 Serving Density Principle — see that
  // file's own comment) — but callRegistryCap's return value is one level too shallow
  // (`{content: <realPayload>, is_error}`, the SAME unwrap-depth bug register_p1_ganita.ts's
  // A4 comment documents, never fixed in this file — see unwrapCapabilityPayload above), so
  // `empty_reason`/`known_gap` were buried under an extra `.content` a caller reading the
  // top-level response would never find: "returns empty with NO empty_reason/known_gap field
  // in some request shapes" (every request shape that returns zero anchors). Broken out into
  // a bespoke handler (instead of the shared regAlias) so this ONE tool can unwrap correctly
  // without touching regAlias's ~40 other callers.
  server.tool(
    'phala_predictive_anchors_get',
    'L4 predictive anchors (phala_anchors/ph_nimitta) — magnitude, confidence band, karmic frame, ' +
    'malleability, and posterior_provenance (base_rate_source + honest cardinality-null where unfit) per ' +
    'anchor. When the result is empty, `empty_reason` + `known_gap` (e.g. CR-66) always explain why ' +
    '(genuine zero-anchor build vs. a filter miss vs. an unreachable backing table) — never a bare empty array.',
    {
      ...ChartBase,
      domain: z.string().optional(),
      event_type: z.string().optional(),
      direction: z.string().optional(),
      horizon_tier: z.string().optional(),
      top_k: z.number().optional(),
    },
    async (params) => {
      const p = params as Record<string, unknown>
      const chartId = p['chart_id'] as string | undefined
      if (!chartId) return errOut('phala_predictive_anchors_get', 'chart_id is required')
      try {
        const data = await callRegistryCap('marsys://tool/L4/query_predictive_anchors', {
          chart_id: chartId,
          ayanamsha_id: na(p['ayanamsha_id'] as string | undefined),
          domain: p['domain'], event_type: p['event_type'], direction: p['direction'],
          horizon_tier: p['horizon_tier'], top_k: p['top_k'],
        }, principal)
        const payload = unwrapCapabilityPayload(data)
        // Defensive floor: guarantee empty_reason/known_gap are NEVER silently absent when
        // anchors is empty, even if the underlying capability's own disclosure changes shape
        // in the future — this tool's whole point is that this field must always be reachable.
        const anchors = Array.isArray(payload['anchors']) ? payload['anchors'] : []
        if (anchors.length === 0 && payload['empty_reason'] == null) {
          payload['empty_reason'] = 'phala_predictive_anchors_get returned zero anchors and the ' +
            'backing capability supplied no reason — treat as an honest empty pending investigation, ' +
            'not a confirmed zero-prediction result.'
          payload['known_gap'] = payload['known_gap'] ?? null
        }
        return dualOutput(payload, 'phala_predictive_anchors_get')
      } catch (err) { return errOut('phala_predictive_anchors_get', String(err), { chart_id: chartId }) }
    }
  )

  // SARVA-SIDDHI W-2 P-1 (2026-07-24) — standing_predictions_read: the READ side of the LIVE
  // prospective ledger (brahma_prospective_ledger, migration 458 — D-4a Lane A-4). This is the
  // live_tool the Vidhi E-2 primitive `standing_predictions_read` was repointed to (it had been
  // mis-wired to phala_predictive_anchors_get, an L4 phala_anchors surface — the PRE_DARPANA_
  // READINESS B-2 FAIL). Returns the OPEN filed, falsifiable standing predictions for the chart,
  // domain-layered (§N.6): the requested domain's material cluster leads (wealth ⊇ {wealth,
  // residence}), non-matching open predictions returned under other_domain_predictions (never
  // dropped — B.10), explicit empty_reason on an empty result. Confirmation/disclosure ONLY —
  // §11: predictions exist by explicit filing only; this surface never files or calibrates.
  regAlias(server, 'standing_predictions_read',
    'Standing prospective-ledger read (brahma_prospective_ledger) — the OPEN filed, falsifiable ' +
    'predictions for the chart: claim, event_class, temporal shape + window/milestones, confidence, ' +
    'a MANDATORY falsifier, generator_class and source_citation. Domain-layered (wealth clusters ' +
    '{wealth, residence}); non-matching open predictions returned under other_domain_predictions. ' +
    'Confirmation/disclosure only — never a filing or calibration write (§11).',
    'marsys://tool/L4/query_prospective_ledger',
    {
      domain: z.string().optional().describe('Question domain (wealth clusters {wealth, residence}).'),
      status: z.string().optional().describe('Lifecycle filter (open | matched | confirmed | falsified | withdrawn). Default: open.'),
    }, principal)

  // list_assets → catalog_assets_list
  // W5 L8 ("listCapabilities filters" / W-13): same additional filters as list_assets
  // (registry_bridge.ts) and asset_registry_all.ts's own handler — asset_type,
  // catalog_status, scope, is_active, has_writer. All optional, AND-combined.
  server.tool(
    'catalog_assets_list',
    '[Phase-1 alias] List all registered retrieval assets (same as list_assets).',
    {
      layer: z.string().optional().describe('Filter by layer (L0, L1, L2, etc.)'),
      asset_type: z.enum(['data', 'service']).optional().describe('Filter by asset_type: data or service'),
      catalog_status: z.enum(['CURRENT', 'DRAFT']).optional().describe('Filter by catalog_status: CURRENT or DRAFT'),
      scope: z.enum(['global', 'per_chart']).optional().describe('Filter by scope: global or per_chart'),
      is_active: z.boolean().optional().describe('Filter to active (true) or inactive (false) assets'),
      has_writer: z.boolean().optional().describe('Filter to assets with (true) or without (false) a registered writer'),
      ...GlobalBase,
    },
    async ({ layer, asset_type, catalog_status, scope, is_active, has_writer, limit, offset }) => {
      try {
        const data = await callRegistryCap('marsys://resource/asset-registry/all', {
          layer, asset_type, catalog_status, scope, is_active, has_writer,
          limit: limit ?? 200, offset: offset ?? 0,
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

  // CR-24 completion fix (mechanism_read conformance): the planner primitive `mechanism_read`
  // (registry_data.ts) was repointed from `bodha_graph_subgraph_get` to `bodha_mechanisms_get`
  // at the CR-24 merge, but that change only updated the planner-side registry/tests — it never
  // registered the corresponding MCP tool, so `bodha_mechanisms_get` did not exist as a callable
  // surface (unlike sibling faces bodha_graph_subgraph_get / bodha_signals_get, each of which has
  // its own server.tool registration). The capability itself was never missing: bo_yantra_mechanism
  // (writer) populates bodha_mechanisms, and query_mechanisms.ts (L2_bodha registry capability)
  // already reads it — this wires that existing capability up as a first-class live tool.
  // get_mechanisms → bodha_mechanisms_get
  server.tool(
    'bodha_mechanisms_get',
    'L2 named, valenced Mechanism (Yantra) objects from bodha_mechanisms — the first-class ' +
    'CGM-subgraph mechanisms the bo_yantra_mechanism writer builds (convergent_dispositor_chain, ' +
    'dispositor_cycle, house_lordship_cycle, yoga_cluster, mutual_reception, parivartana_chain, ' +
    'stellium, mutual_aspect, mutual_aspect_triangle, graha_bhava_affliction). Each row: ' +
    'mechanism_name, mechanism_class, valence (benefic|malefic|mixed|neutral), member_node_ids / ' +
    'member_edge_ids composition, edge_strength_avg/min/max (DR-7 edge_strength_v1 provenance), ' +
    'centrality_summary, and a grounding citation. Filters: ayanamsha_id, mechanism_class, valence, ' +
    'chain_circuit_only (isolates the convergent_dispositor_chain/dispositor_cycle/house_lordship_cycle ' +
    'family, served first). Per-class and per-valence facet counts over the full match set are always ' +
    'returned. Bounded (LIMIT <=50) with a disclosed total, offset pagination, and an honest ' +
    'empty_reason when a chart carries no mechanisms.',
    {
      ...ChartBase,
      mechanism_class:    z.string().optional().describe('Filter by a single mechanism_class. Omit for all.'),
      valence:            z.enum(['benefic', 'malefic', 'mixed', 'neutral']).optional(),
      chain_circuit_only: z.boolean().optional().describe(
        'When true, return only the CR-24 chain/circuit family (convergent_dispositor_chain, ' +
        'dispositor_cycle, house_lordship_cycle). Default false.'),
    },
    async (params) => {
      const { chart_id, ayanamsha_id, limit, offset, mechanism_class, valence, chain_circuit_only } =
        params as Record<string, unknown>
      if (!chart_id) return errOut('bodha_mechanisms_get', 'chart_id is required')
      try {
        const data = await callRegistryCap('marsys://tool/L2/query_mechanisms', {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          ...(mechanism_class ? { mechanism_class } : {}),
          ...(valence ? { valence } : {}),
          ...(chain_circuit_only != null ? { chain_circuit_only } : {}),
          ...(limit != null ? { limit } : {}),
          ...(offset != null ? { offset } : {}),
        }, principal)
        return dualOutput(data, 'bodha_mechanisms_get')
      } catch (err) { return errOut('bodha_mechanisms_get', String(err), { chart_id }) }
    }
  )

  // query_chart_facts → ganita_chart_facts_get
  // R5 W1 (lane: chart_query) fix: extraSchema previously declared fact_category/fact_id,
  // neither of which the registry handler (register_d7_channel.ts) ever read — a dead-param
  // mismatch of the same class as P1 (design §18: "aliases carry DIVERGING param names").
  // Reconciled to the real filter set the handler now implements (see query_chart_facts above
  // for the full facet description); NF-1's 404 is fixed at the shared handler, so this alias
  // is fixed for free once its own param names line up.
  // WP-1.3(f)/LCA-3: hand-written (not regAlias) so this alias reaches all 6 stored ayanamshas.
  // regAlias routes ayanamsha through the shared `na()` helper, which collapses
  // true_chitra -> lahiri_chitrapaksha and would hide true_chitra's dataset here exactly as it
  // did on the primary query_chart_facts tool. Uses resolveChartFactsAyanamsha (the same
  // query_chart_facts-scoped resolver as registry_bridge.ts) and forwards fact_subject +
  // pagination so this alias is at full parity with query_chart_facts.
  server.tool(
    'ganita_chart_facts_get',
    '[Phase-1 alias] L1 chart_facts EAV-crosstab query (same as query_chart_facts). Reaches all 6 stored ayanamshas (lahiri_chitrapaksha [default], krishnamurti, raman, surya_siddhanta_classical, true_chitra, INVARIANT); discloses pagination (total + more_available) over the 5,566 subjects.',
    {
      chart_id:         z.string().uuid().describe('Chart UUID'),
      ayanamsha_id:     z.string().optional().describe("Ayanamsha (default 'lahiri_chitrapaksha'); any of the 6 stored ayanamshas reachable."),
      about: z.union([
        z.string(),
        z.object({ graha: z.string().optional(), bhava: z.number().int().min(1).max(12).optional(), house_lord: z.number().int().min(1).max(12).optional() }),
      ]).optional(),
      category:         z.string().optional(),
      planet:           z.string().optional(),
      house:            z.number().int().min(1).max(12).optional(),
      sign:             z.string().optional(),
      nakshatra:        z.string().optional(),
      // r18-intentional-passthrough: divisional_chart
      // (R-18 param no-op audit: forwarded verbatim via `...rest` below to chart_facts_query,
      // which reads it directly — live-verified S-12 CLOSED_WITH_EVIDENCE, BIND_D-1.6 S-7:
      // ganita_chart_facts_get(divisional_chart=D2|D9) serves the divisional_facts section.)
      divisional_chart: z.string().optional().describe('Divisional chart code (e.g. "D9", "D2"). Also returns that varga\'s chart_divisionals-native EAV facts (per-varga sign/house, hora class incl. surya_hora/chandra_hora + hora_d2_house, varga dignity, house lords/occupants) in a separate `divisional_facts` section.'),
      keyword:          z.string().optional(),
      fact_subject:     z.string().optional().describe('Exact fact_subject filter (e.g. "LAGNA", "SUN", "D9_JUP"). Comma-separated for multiple.'),
      shape:            z.enum(['pivoted', 'rows']).optional(),
      limit:            z.number().int().min(1).max(1000).optional(),
      offset:           z.number().int().min(0).optional(),
    },
    async (params) => {
      const { chart_id, ayanamsha_id, ...rest } = params as Record<string, unknown>
      if (!chart_id) return errOut('ganita_chart_facts_get', 'chart_id is required')
      try {
        const data = await callRegistryCap('marsys://tool/L1/chart_facts_query', {
          chart_id,
          ayanamsha_id: resolveChartFactsAyanamsha(ayanamsha_id as string | undefined),
          ...rest,
        }, principal)
        return dualOutput(data, 'ganita_chart_facts_get')
      } catch (err) { return errOut('ganita_chart_facts_get', String(err), { chart_id }) }
    }
  )

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
  // W4-loop-1 (E-5 group1): all five now mirror their working l0_ephemeris.ts twins
  // (direct sidecar GET with x-api-key), not the registry proxy that 401'd/500'd.

  server.tool(
    'ref_planet_position_get',
    '[Phase-1 alias] L0 planet position at a given date (same as query_planet_position).',
    {
      date:         z.string().optional().describe('Date in YYYY-MM-DD format (1900-2150).'),
      datetime_iso: z.string().optional().describe('Alias of `date` — the date portion (YYYY-MM-DD) is used.'),
      planet:       z.string().optional().describe('Optional graha (Sun..Ketu). Omit for all 9 bodies.'),
    },
    async ({ date, datetime_iso, planet }) => {
      try {
        const d = (date ?? datetime_iso ?? '').slice(0, 10)
        if (!d) return errOut('ref_planet_position_get', 'date (YYYY-MM-DD) is required')
        const qs = new URLSearchParams({ date: d })
        if (planet) qs.set('planet', planet)
        const data = await callSidecarGet(`/brahmagyan/ephemeris/planet_position?${qs}`)
        return dualOutput(data, 'ref_planet_position_get')
      } catch (err) { return errOut('ref_planet_position_get', String(err)) }
    }
  )

  server.tool(
    'ref_planet_transit_get',
    '[Phase-1 alias] L0 planet transit series across a date window (same as query_planet_transit).',
    {
      planet:      z.string().describe('Planet to query (Sun..Saturn/Rahu/Ketu).'),
      start_date:  z.string().describe('Start date YYYY-MM-DD.'),
      end_date:    z.string().describe('End date YYYY-MM-DD.'),
      sign_number: z.number().int().min(1).max(12).optional().describe('Optional tropical sign filter (1=Aries..12=Pisces).'),
    },
    async ({ planet, start_date, end_date, sign_number }) => {
      try {
        const qs = new URLSearchParams({ planet, start_date, end_date })
        if (sign_number !== undefined) qs.set('sign_number', String(sign_number))
        const data = await callSidecarGet(`/brahmagyan/ephemeris/planet_transit?${qs}`)
        return dualOutput(data, 'ref_planet_transit_get')
      } catch (err) { return errOut('ref_planet_transit_get', String(err)) }
    }
  )

  server.tool(
    'ref_aspects_at_time_get',
    '[Phase-1 alias] L0 planetary aspects on a specific date (same as query_aspects_at_time).',
    {
      date:         z.string().optional().describe('Date YYYY-MM-DD.'),
      datetime_iso: z.string().optional().describe('Alias of `date` — the date portion (YYYY-MM-DD) is used.'),
      orb_degrees:  z.number().min(0.1).max(10.0).optional().describe('Orb tolerance in degrees (default 1.0).'),
    },
    async ({ date, datetime_iso, orb_degrees }) => {
      try {
        const d = (date ?? datetime_iso ?? '').slice(0, 10)
        if (!d) return errOut('ref_aspects_at_time_get', 'date (YYYY-MM-DD) is required')
        const qs = new URLSearchParams({ date: d, orb_degrees: String(orb_degrees ?? 1.0) })
        const data = await callSidecarGet(`/brahmagyan/ephemeris/aspects?${qs}`)
        return dualOutput(data, 'ref_aspects_at_time_get')
      } catch (err) { return errOut('ref_aspects_at_time_get', String(err)) }
    }
  )

  server.tool(
    'ref_retrograde_periods_get',
    '[Phase-1 alias] L0 retrograde station events for a planet in a date range (same as query_retrograde_periods).',
    {
      planet:     z.string().describe('Planet (Mercury/Venus/Mars/Jupiter/Saturn).'),
      start_date: z.string().describe('Start date YYYY-MM-DD.'),
      end_date:   z.string().describe('End date YYYY-MM-DD.'),
    },
    async ({ planet, start_date, end_date }) => {
      try {
        const qs = new URLSearchParams({ planet, start_date, end_date })
        const data = await callSidecarGet(`/brahmagyan/ephemeris/retrograde_periods?${qs}`)
        return dualOutput(data, 'ref_retrograde_periods_get')
      } catch (err) { return errOut('ref_retrograde_periods_get', String(err)) }
    }
  )

  // ephemeris_cache_year → ref_ephemeris_year_get
  server.tool(
    'ref_ephemeris_year_get',
    '[Phase-1 alias] L0 ephemeris cache for a given year (same as ephemeris_cache_year).',
    { year: z.number().int().min(1900).max(2150).describe('4-digit calendar year') },
    async ({ year }) => {
      try {
        const data = await callSidecarGet(
          `/brahmagyan/ephemeris/all_bodies_range?start_date=${year}-01-01&end_date=${year}-12-31`)
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

  // W5 L8 ("listCapabilities filters" / W-13): same additional filters as
  // catalog_assets_list/list_assets, forwarded to the same underlying resource handler.
  server.tool(
    'catalog_assets_all',
    '[Phase-1 alias] Full asset registry (same as asset_registry_all). Global scope. ' +
    'Optional filters: layer, asset_type, catalog_status, scope, is_active, has_writer.',
    {
      layer: z.string().optional().describe('Filter by layer (L0, L1, L2, etc.)'),
      asset_type: z.enum(['data', 'service']).optional().describe('Filter by asset_type: data or service'),
      catalog_status: z.enum(['CURRENT', 'DRAFT']).optional().describe('Filter by catalog_status: CURRENT or DRAFT'),
      scope: z.enum(['global', 'per_chart']).optional().describe('Filter by scope: global or per_chart'),
      is_active: z.boolean().optional().describe('Filter to active (true) or inactive (false) assets'),
      has_writer: z.boolean().optional().describe('Filter to assets with (true) or without (false) a registered writer'),
      ...GlobalBase,
    },
    async ({ layer, asset_type, catalog_status, scope, is_active, has_writer, limit, offset }) => {
      try {
        const data = await callRegistryCap('marsys://resource/asset-registry/all', {
          layer, asset_type, catalog_status, scope, is_active, has_writer,
          limit: limit ?? 200, offset: offset ?? 0,
        }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('catalog_assets_all', String(err)) }
    }
  )

  server.tool(
    'catalog_assets_l0',
    '[Phase-1 alias] L0 Brahmagyan asset registry (same as asset_registry_l0). ' +
    'Optional filters: asset_type, catalog_status, scope, is_active, has_writer.',
    {
      asset_type: z.enum(['data', 'service']).optional().describe('Filter by asset_type: data or service'),
      catalog_status: z.enum(['CURRENT', 'DRAFT']).optional().describe('Filter by catalog_status: CURRENT or DRAFT'),
      scope: z.enum(['global', 'per_chart']).optional().describe('Filter by scope: global or per_chart'),
      is_active: z.boolean().optional().describe('Filter to active (true) or inactive (false) assets'),
      has_writer: z.boolean().optional().describe('Filter to assets with (true) or without (false) a registered writer'),
      ...GlobalBase,
    },
    async ({ asset_type, catalog_status, scope, is_active, has_writer, limit, offset }) => {
      try {
        const data = await callRegistryCap('marsys://resource/asset-registry/L0', {
          asset_type, catalog_status, scope, is_active, has_writer,
          limit: limit ?? 100, offset: offset ?? 0,
        }, principal)
        return dualOutput(data)
      } catch (err) { return errOut('catalog_assets_l0', String(err)) }
    }
  )

  server.tool(
    'util_intent_classify',
    '[Phase-1 alias] Deterministic Vidhi scope-tuple classifier (same as intent_classify). ' +
    'CR-28 / DR-8: returns {scope_tuple, confidence, method:"deterministic_rules", matched_rules, ' +
    'fallback_prompt, fallback_recommended, usage} — not a rendered prompt. Both twins share ONE ' +
    'classifier module so they never diverge.',
    { query: z.string().describe('Query text to classify') },
    async ({ query }) => {
      try {
        // DR-8 (DIS.021): deterministic classification runs locally (no server-side LLM, no proxy
        // to the marsys://prompt/intent-classify prompt) — same pure module as intent_classify.
        const result = classifyScope(query)
        return dualOutput(result, 'util_intent_classify')
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
  //
  // CR-42 residue (D-1.5b item 3): this schema always declared a `keyword` param, but the
  // underlying `query_remedies` primitive (platform/src/lib/retrieve/remedy_tools.ts) only
  // ever reads planet/domain/category/top_k off its params — `keyword` was silently dropped,
  // a search-in-name-only. CR-42's established discipline elsewhere in this codebase is:
  // either genuinely honor the param, or explicitly reject/flag when it can't. Genuinely
  // honoring it (rather than rejecting) is the more useful fix here, since the corpus text
  // fields ARE available on every returned row — this pools a bounded candidate set from the
  // primitive, applies a real case-insensitive substring search across the corpus's text
  // fields, and discloses the honest scope of that search (candidate_pool_size) so a caller
  // never mistakes a bounded-pool search for a full-corpus one.
  const REMEDY_SEARCH_FIELDS = [
    'prescription_text', 'mantra_text', 'mantra_sanskrit', 'mantra_transliteration',
    'deity', 'category', 'source_citation', 'classical_attestation_text', 'planet', 'domain',
  ]
  server.tool(
    'ref_remedies_search',
    '[Phase-1 alias] Reference remedies search (dedup companion; retained per §Step 4 disposition). ' +
    'CR-42 fix: `keyword` is now GENUINELY applied as a case-insensitive substring search across ' +
    `${REMEDY_SEARCH_FIELDS.join('/')} — the underlying query_remedies primitive has no native ` +
    'keyword filter, so this pools a bounded candidate set and searches it client-side; see the ' +
    'response\'s `keyword_search` receipt for the honest scope (candidate_pool_size) actually covered.',
    { keyword: z.string().optional(), planet: z.string().optional(), category: z.string().optional(), ...GlobalBase },
    async (params) => {
      try {
        const { keyword, limit, offset, ...rest } = params as Record<string, unknown>
        void offset // query_remedies has no offset concept (top_k only) — accepted for schema parity, unused.
        const kw = typeof keyword === 'string' ? keyword.trim() : ''
        const desiredLimit = typeof limit === 'number' && limit > 0 ? limit : 10

        if (!kw) {
          // No keyword requested — planet/category are genuinely honored natively by the
          // primitive; behave exactly as before, just mapping limit -> top_k honestly.
          const data = await callPlatformPrim('query_remedies', { ...rest, top_k: desiredLimit }, principal)
          return dualOutput(data)
        }

        const POOL_SIZE = Math.min(Math.max(desiredLimit * 10, 100), 500)
        const data = await callPlatformPrim('query_remedies', { ...rest, top_k: POOL_SIZE }, principal) as
          { result?: { results?: { content: string; source_canonical_id?: string; source_version?: string; confidence?: number }[] } }
        const pool = data?.result?.results ?? []
        const kwLower = kw.toLowerCase()
        const matched = pool.filter(r => {
          let row: Record<string, unknown>
          try { row = JSON.parse(r.content) } catch { return false }
          return REMEDY_SEARCH_FIELDS.some(f => {
            const v = row[f]
            return typeof v === 'string' && v.toLowerCase().includes(kwLower)
          })
        })
        const served = matched.slice(0, desiredLimit)

        return dualOutput({
          ...data,
          result: { ...(data?.result ?? {}), results: served },
          keyword_search: {
            applied: true,
            keyword: kw,
            fields_searched: REMEDY_SEARCH_FIELDS,
            candidate_pool_size: pool.length,
            matched_count: matched.length,
            served_count: served.length,
            note: 'CR-42: query_remedies has no native keyword filter — this is a genuine ' +
              `client-side substring search over a BOUNDED candidate pool (top_k=${POOL_SIZE}), ` +
              'NOT a full-corpus search. Remedies outside the pool are not searched; narrow with ' +
              'planet/category to shrink the pool the keyword search actually covers, or raise ' +
              '`limit` to widen it (pool = limit × 10, capped at 500).',
          },
        })
      } catch (err) { return errOut('ref_remedies_search', String(err)) }
    }
  )

  // ── L4 Phala aliases (3 via sidecar + 1 via platform primitive) ──────────

  server.tool(
    'phala_anchors_get',
    // O-7 (D-1.6 Lane S-6): description previously said "(same as phala_event_anchors)" —
    // no tool by that name is registered; the primitive's actual TOOL_NAME is
    // 'event_anchors' (phala_event_anchors.ts:227). This stale reference made the
    // alias<->primitive pair undiscoverable/unverifiable by the O-7 conformance check
    // (platform/scripts/audit/alias_conformance_check.ts) — corrected to the real name.
    '[Phase-1 alias] L4 Phala event anchors — calibrated probabilistic event windows (same as event_anchors).',
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
    '[Phase-1 alias] [DEPRECATED — superseded by kala_elect_get, ṢAḌ-DARŚANA v2 W0.4: the ' +
    'elevated ELECT view over this same muhurta_finder substrate, with argument-shaped ' +
    'reading, tāra-bala/target-graha dissent, tri-plane pointers, and honest coverage. ' +
    'This alias remains live — not retired — per the campaign\'s strangler-fig discipline.] ' +
    'Muhurta (auspicious timing) finder (same as muhurta_finder).',
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
        // RC-04 drill-crawl (2026-07-23): dualOutput(data) with no toolName arg was
        // defaulting recover_via.instrument to the literal placeholder 'unknown_tool' in
        // this tool's trim_report/drill_pointers whenever a section was auto-trimmed
        // (live-reproduced: mitigations 100→10, auspicious_windows 30→15, both pointing
        // callers at 'unknown_tool'). Passing the real tool name here matches the sibling
        // call sites in this file (e.g. mimamsa_lel_query below) that already do this.
        return dualOutput(data, 'phala_outlook_get')
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
      // r18-intentional-passthrough: prediction_id, outcome, verdict
      // (R-18 param no-op audit: the entire `params` object — every declared key, not a
      // filtered subset — is forwarded verbatim to callPlatformPrim('record_outcome', ...)
      // below; there is no per-key handling to audit because nothing here filters anything.)
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

  // CR-16 (D-2 V-3, ledger row 26): special-lagna access was birth-data-ONLY — a caller holding a
  // built chart_id had no path to that chart's STORED special-lagna facts and was forced to
  // re-supply raw birth data for a sidecar recompute (which also bypasses entitlement + the L1
  // canonical values §N.5). Now chart_id is a first-class alternative input: when supplied, the
  // stored special_lagna/upagraha/saham facts are served from chart_facts via the entitlement-gated
  // registry capability marsys://tool/L1/get_sensitive_points (categories filter) — the same
  // canonical rows the rest of the estate reads. Birth-data path retained for un-built charts.
  //
  // EL-41 / B-1 fix: the public `categories` enum here ('special_lagna'/'upagraha'/'saham'/
  // 'sensitive_point') are ALIAS names, not literal chart_facts.fact_category values — only
  // 'special_lagna' happens to match exactly. get_sensitive_points.ts filters
  // `fact_category = ANY($2)` on whatever is passed VERBATIM, so 'upagraha', 'saham', and
  // 'sensitive_point' matched ZERO real rows (live-verified against 482012f1: real categories
  // are 'upagraha_position'/'sun_derived_upagraha', 'saham_position', and
  // 'sensitive_point_gulika_mandi'/'sensitive_degree_check'/'nakshatra_pada_sensitive'
  // respectively) — a requested category silently vanishing from the response with no signal
  // at all. SPECIAL_LAGNA_CATEGORY_MAP below maps each public alias to its real backing
  // fact_category set so data actually returns, and every REQUESTED alias gets an entry in
  // `category_receipts` (never silently absent, even when genuinely empty).
  server.tool(
    'ganita_special_lagnas_get',
    '[Phase-1 alias] Special lagnas + upagrahas. TWO input modes: (1) chart_id — serves the ' +
    "chart's STORED special_lagna/upagraha/saham facts (chart_facts, §N.5 canonical, entitlement-" +
    'gated) — preferred for a built chart; (2) birth data (datetime_iso/latitude_deg/…) — a ' +
    'PyJHora sidecar recompute for an un-built chart. Supersedes query_special_lagnas ' +
    '(birth-data only). CR-16.',
    {
      chart_id: z.string().uuid().optional().describe(
        'Built chart UUID — serves stored special-lagna facts (preferred). If omitted, birth data is required.'),
      categories: z.array(z.enum(['special_lagna', 'upagraha', 'saham', 'sensitive_point']))
        .optional().describe('chart_id mode: which stored fact_categories to return (default special_lagna + upagraha).'),
      ...BirthBase,
      datetime_iso:  z.string().optional().describe("Birth datetime local ISO (birth-data mode). Not needed when chart_id is given."),
      latitude_deg:  z.number().optional().describe('Latitude decimal degrees (birth-data mode).'),
      longitude_deg: z.number().optional().describe('Longitude decimal degrees (birth-data mode).'),
    },
    async (params) => {
      const p = params as Record<string, unknown>
      const chartId = p['chart_id'] as string | undefined
      try {
        if (chartId) {
          // Chart-keyed path: stored special-lagna facts via the entitlement-gated capability.
          const requestedAliases = (p['categories'] as string[] | undefined) ?? ['special_lagna', 'upagraha']
          // EL-41/B-1: expand each public alias to its REAL backing fact_category set so
          // 'upagraha'/'saham'/'sensitive_point' actually retrieve data instead of matching
          // nothing (see comment above the tool registration).
          const realCategories = [...new Set(
            requestedAliases.flatMap(a => SPECIAL_LAGNA_CATEGORY_MAP[a] ?? []),
          )]
          const data = await callRegistryCap('marsys://tool/L1/get_sensitive_points', {
            chart_id: chartId,
            ayanamsha_id: na(p['ayanamsha_id'] as string | undefined),
            categories: realCategories,
            limit: (p['limit'] as number) ?? 25000,
            offset: (p['offset'] as number) ?? 0,
          }, principal)
          const payload = unwrapCapabilityPayload(data)
          const rows = extractRowsForReceipt(data)
          const category_receipts = buildCategoryReceipts(
            requestedAliases, SPECIAL_LAGNA_CATEGORY_MAP, rows,
          )
          return dualOutput({ ...payload, category_receipts }, 'ganita_special_lagnas_get')
        }
        if (!p['datetime_iso']) {
          return errOut('ganita_special_lagnas_get',
            'Provide either chart_id (stored facts, preferred) or birth data (datetime_iso/latitude_deg/longitude_deg).')
        }
        const data = await callSidecarPath('/api/pyhora/compute', p)
        return dualOutput(data)
      } catch (err) { return errOut('ganita_special_lagnas_get', String(err), chartId ? { chart_id: chartId } : undefined) }
    }
  )
}

/**
 * D7 — Registry-backed MCP Tool Bridge
 * =====================================
 * Exposes the new registry capabilities as MCP tools on the server.
 * Called from server.ts during tool registration.
 *
 * This is the "by-construction-no-drift" connection:
 *   registry.getCapability(uri).handler === the function both channels call
 *
 * All new consolidated MCP tools delegate to the same CapabilityDescriptor.handler
 * that the chat channel calls via getCapability(uri). Same handler → drift impossible.
 *
 * D7 consolidated tool surface (§2.1 of brief) — ~12 workflow-shaped tools:
 *   get_chart_orientation  → marsys://tool/L2/query_ucd
 *   get_domain_reading     → marsys://tool/L2/query_domain_reading
 *   get_signals            → marsys://tool/L2/query_signals
 *   traverse_graph         → marsys://tool/L2/traverse_chart_graph
 *   get_positions          → marsys://tool/L1/get_positions
 *   get_dashas             → marsys://tool/L1/get_dashas
 *   get_temporal_windows   → marsys://tool/L3/query_temporal_activation
 *   get_projections        → marsys://tool/L3/query_projections
 *   get_classical_citation → marsys://tool/L0/query_classical_texts
 *   get_remedies           → marsys://tool/L2/query_remedies
 *   get_chart_quality      → marsys://tool/L2/query_quality_scorecard
 *   list_assets            → marsys://resource/asset-registry/all
 *
 * Provider-spec obligations (RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC §B.i):
 *   - outputSchema + structuredContent + text fallback (dual output)
 *   - cursor pagination on list/search tools
 *   - response_format / verbosity enum on umbrella tools
 *   - UUIDs resolved to names in output
 *   - tool names: snake_case, no hyphens, ≤64 chars
 *   - transport: Streamable HTTP only (matches server.ts)
 *
 * chart_agnostic_gate: all per_chart tools require chart_id; error if missing.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
// R5 W1 (design §E-6 + brief §Lane signals_query/synthesis_query): wires get_signals
// (signals_query) and get_chart_orientation (synthesis_query) onto the W0b generated
// contract path — the SAME buildRetrievalEnvelope + response_format negotiation
// pattern register_p1_ganita.ts's ganita_yogas_get established. Imports the GENERATED
// module (not a hand-mirror) — see scripts/generate_envelope.ts / src/generated/envelope.ts.
import {
  buildRetrievalEnvelope,
  resolveEnvelopeFormat,
  judgmentFlag,
  redactProvenanceTables,
  type EnvelopeFormat,
  type ChartHeader,
  type DrillPointerType,
  type CoverageStamp,
  type PactStage,
  type TrimReportEntry,
  type JudgmentFlagEntry,
} from '../generated/envelope.js'
// R5.1 C1 (MCP-consume hardening): the shared, reusable response-size trimmer for the
// three instruments whose full-detail payload (up to ~86KB) is unusable over a real MCP
// channel — judgment_query, graha_portrait, pact_query. See response_budget.ts's header
// for why this is structure-aware (shrinks named arrays) rather than a byte-truncation.
import { finalizeMcpBudget, autoDetectTrimmableSections, type TrimmableSection, assembleSaraContent, type SaraKernel, type DrillPointerLike } from '../lib/response_budget.js'
// Elevation Campaign v2.1 · Stream α (SATYA) — flagship completeness wiring.
// γ built `dossier` (the Ω5 gather-then-compose engine) but a naive uninstructed agent asking
// "how is my wealth?" reaches for the obviously-named `assess_wealth`, gets the shallow default
// bundle, and never discovers dossier — scoring ~15% against the domain concept set. Fix (option
// (b)(i)): the assess_* entrypoints now internally invoke the SAME dossier assembly logic
// (runDossier is a PURE function over embedded slice bundles — zero I/O, no HTTP round-trip to
// self) and merge its 100%-accounted completeness map into their OWN response, so the tool a
// naive caller actually reaches for is now backed by the complete domain accounting, not a
// shallow slice. No computation is reimplemented (B.10) — dossier is a deterministic join of the
// Total Concept Inventory × completeness accounting.
import { runDossier, type DossierPage } from './dossier.js'
// ṢAḌ-DARŚANA (SHAD_DARSHANA_BRIEF_v2_0.md §2 file map) — the nine kala_* view/capability
// facades over the elevated kala envelope. Consolidated (post-Night-2 hygiene fix) into ONE
// dedicated, kala-owned aggregator — see kala_views/register_all.ts's docstring for why: this
// file's own registration surface serves every campaign's tools, so a hand-edited per-tool
// import+call block here was a chronic multi-lane merge-conflict hot spot. The "one canonical
// registration per tool, asserted by test" guarantee (brief §2) is unchanged — each tool's
// server.tool() call is still reached from exactly one place, now inside register_all.ts.
import { registerAllKalaViews } from './kala_views/register_all.js'
import { resolveChartFactsAyanamsha } from '../lib/ayanamsha.js'
export { resolveChartFactsAyanamsha } from '../lib/ayanamsha.js'

// ── Platform URL (for proxy calls to the platform API) ───────────────────────

const PLATFORM_URL = (
  process.env['PLATFORM_URL'] ?? 'http://localhost:3000'
).replace(/\/$/, '')

// Service-to-service token — must match MCP_INTERNAL_TOKEN on amjis-web.
// Required by /api/retrieval/capability (F1 gate, M0.5).
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

function normalizeAyanamsha(id?: string): string {
  return resolveChartFactsAyanamsha(id)
}

// This shared resolver preserves every stored school, including true_chitra.

// ── Platform primitive caller ─────────────────────────────────────────────────

/**
 * Call a platform primitive via /api/mcp/primitives/{tool}.
 * Used for tools (e.g. vector_search) that are not in the registry.
 *
 * R5 W0a punch-list fix (P7 — corpus search 401). Root cause per
 * RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md §20: this helper sent only
 * X-MCP-Internal-Token, but /api/mcp/primitives/[tool]/route.ts's Layer 2 gate
 * requires X-MCP-User + X-MCP-Key-Id (X-MCP-Audience-Tier is informational).
 * The working 3-header pattern already existed in resources/capabilities.ts —
 * copied here per the design doc's named fix class.
 */
/**
 * R5.1 C2 item 3 (Denial ≠ empty): when the platform route already built a distinct
 * `entitlement_denied` McpErrorEnvelope (denial block present), preserve that signal in the
 * thrown error's message instead of collapsing it to a generic "failed (401): <truncated
 * text>" — the whole point of the distinct envelope is lost if the MCP-facing error message
 * can't be told apart from any other 401. Falls back to the generic message for every other
 * error shape (never assumes denial when the body doesn't say so).
 */
export function describeProxyFailure(tool: string, status: number, bodyText: string): string {
  try {
    const parsed = JSON.parse(bodyText) as { error?: { class?: string; message?: string }; denial?: { chart_id?: string; permission_required?: string } }
    if (parsed?.error?.class === 'entitlement_denied' || parsed?.denial) {
      const chartId = parsed.denial?.chart_id ?? 'unknown'
      const required = parsed.denial?.permission_required ?? 'view'
      return `[registry_bridge] ENTITLEMENT_DENIED: '${tool}' — caller lacks ${required} access to chart ${chartId} ` +
        `(distinct from an empty result — this chart exists but you are not granted). ${parsed.error?.message ?? ''}`.trim()
    }
  } catch {
    // Not JSON / not the denial shape — fall through to the generic message below.
  }
  return `[registry_bridge] primitive call '${tool}' failed (${status}): ${bodyText.slice(0, 200)}`
}

async function callPlatformPrimitive(
  tool: string,
  params: Record<string, unknown>,
  principal: Principal,
): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/primitives/${tool}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Audience-Tier': principal.role === 'super_admin' ? 'super_admin' : 'client',
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ params }),
    signal: AbortSignal.timeout(20_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(describeProxyFailure(tool, res.status, text))
  }
  return res.json()
}

/**
 * R-29 fix: the `/api/mcp/primitives/[tool]` route serves a `ToolBundle` whose
 * `results[].content` field is CONTRACTUALLY a string (shared_types.ts `ToolBundleResult.
 * content: string` — a wide, estate-used contract not changed here). For structured-content
 * tools (vector_search's hybrid search rows), `toToolBundleResults()` (tool_name_bridge.ts)
 * populates that string via `JSON.stringify(content)` — so the payload the MCP client
 * receives is JSON-double-encoded: an outer JSON envelope whose `result.results[].content`
 * is itself a JSON string that must be parsed AGAIN client-side (measured +5-6s latency,
 * register R-29). Since this is the client-facing boundary (not the shared ToolBundle
 * contract), parse each such string back into structured JSON here before handing the
 * response to `dualOutput` — plain-text (non-JSON) content is left untouched.
 */
function unwrapDoubleEncodedToolBundleResults(data: unknown): unknown {
  if (!data || typeof data !== 'object') return data
  const root = data as Record<string, unknown>
  const result = root['result'] as Record<string, unknown> | undefined
  const results = result?.['results']
  if (!Array.isArray(results)) return data
  const unwrapped = results.map((r) => {
    if (r && typeof r === 'object' && typeof (r as Record<string, unknown>)['content'] === 'string') {
      const raw = (r as Record<string, unknown>)['content'] as string
      try {
        return { ...(r as Record<string, unknown>), content: JSON.parse(raw) }
      } catch {
        return r // not JSON — genuinely plain text, leave as-is
      }
    }
    return r
  })
  return { ...root, result: { ...result, results: unwrapped } }
}

// ── DB proxy helper ───────────────────────────────────────────────────────────

/**
 * Minimal DB proxy: calls platform API which holds the actual PG connection.
 * The MCP server does not hold a direct DB connection.
 */
async function platformQuery(
  sql: string,
  params: unknown[]
): Promise<{ rows: Record<string, unknown>[] }> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql, params }),
    signal: AbortSignal.timeout(15_000),
  })
  if (!res.ok) {
    throw new Error(`[registry_bridge] platform DB query failed: ${res.status}`)
  }
  return res.json() as Promise<{ rows: Record<string, unknown>[] }>
}

/**
 * Build a SynergyContext for capability handlers.
 */
function buildCtx(chartId?: string) {
  return {
    db: { query: platformQuery },
    chart_id: chartId,
    lel_enabled: false,
  }
}

// ── Unified envelope helper (R5 W1 — mirrors register_p1_ganita.ts's envelope()) ──

// Three-arg call sites are UNCHANGED (format defaults to 'legacy', v3Extras undefined) —
// they get the exact legacy shape. Call sites opting into 'v3' pass format='v3' +
// v3Extras; those extras are silently ignored under 'legacy' (additive-only, brief §6.3).
function envelope(
  content: unknown,
  toolName: string,
  pagination?: { offset: number; limit: number; total: number | null },
  format: EnvelopeFormat = 'legacy',
  v3Extras?: {
    chart_header?: ChartHeader | null
    verdict?: unknown
    ranking_basis?: Record<string, unknown> | null
    grounding?: { fact_ids: string[]; citations: string[]; grounding_score: number | null }
    drill_pointers?: { instrument: string; hint: string; pointer_type?: DrillPointerType; pact_stage?: PactStage }[]
    judgment_flags?: JudgmentFlagEntry[]
    as_of_date?: string
    coverage?: CoverageStamp | null
    trim_report?: TrimReportEntry[] | null
  },
  // Entitlement gate (finding: "provenance.tables / source_table expose raw internal
  // schema names regardless of entitlement") — pass `false` for an ordinary end-user
  // caller (not native/debug-tier) to strip raw provenance.tables/source_table schema
  // detail from `content` (buildRetrievalEnvelope → redactProvenanceTables). Omitted
  // (default) preserves today's byte-identical content for every existing call site.
  entitled?: boolean,
) {
  return buildRetrievalEnvelope(
    {
      tool: toolName,
      content,
      pagination,
      chart_header: v3Extras?.chart_header,
      verdict: v3Extras?.verdict,
      ranking_basis: v3Extras?.ranking_basis,
      grounding: v3Extras?.grounding,
      drill_pointers: v3Extras?.drill_pointers,
      judgment_flags: v3Extras?.judgment_flags,
      as_of_date: v3Extras?.as_of_date,
      coverage: v3Extras?.coverage,
      trim_report: v3Extras?.trim_report,
      entitled,
    },
    format,
  )
}

// ── R5.1 C1 — MCP-channel response-budget application ────────────────────────

/** Response size ceilings (brief §C1): the wire budget for a fully-assembled MCP tool
 *  response (envelope + orientation_context together — the whole structuredContent
 *  object), not just the inner `content` block. */
const MCP_RESPONSE_BUDGET_KB = {
  judgment_query: 12,
  graha_portrait: 12,
  pact_query: 8,
  // R6 3b-budgets (Ring-2 gap fix, R-1/R-8): assess_marriage/career/health/wealth are
  // reconciled multi-source bundles (domain reading + temporal activation + contradictions +
  // composite signals) — richer than the three single-purpose instruments above, so a wider
  // ceiling than 8-12KB is appropriate, but 40KB is still a two-orders-of-magnitude cut from
  // the register's measured 1.04MB assess_career payload.
  assess_marriage: 40,
  assess_career: 40,
  assess_health: 40,
  assess_wealth: 40,
  // D-1.6 Lane S-5 (R-1/R-8/CR-49 residuals): traverse_graph/get_cgm_subgraph measured 99KB,
  // get_projections 70KB on the live connector (BIND_D-1.6 S-7 probe) — all over the 64KB
  // Gate Ś default-page ceiling. 55KB leaves headroom under that ceiling for the dualOutput
  // wrapper's own overhead (same SAFETY_MARGIN_BYTES rationale as judgment_query/graha_portrait
  // above), while still serving a genuinely useful default page (these are graph-shaped
  // responses — nodes/edges/projections are the actionable payload, not decorative).
  traverse_graph: 55,
  get_cgm_subgraph: 55,
  get_projections: 55,
  // W3-L5 (budget unification, R-2 item 5 / W-8): the remaining 15 registry_bridge.ts tools
  // that previously called plain `dualOutput` with NO response-budget pass at all — part of
  // the ~36-of-~115 unclamped surface (GT-48). 40KB matches the assess_* ceiling above: wide
  // enough for genuinely useful default pages, still a real cut from unbounded.
  get_chart_orientation: 40,
  get_domain_reading: 40,
  get_signals: 40,
  get_positions: 40,
  get_dashas: 40,
  get_temporal_windows: 40,
  get_classical_citation: 40,
  get_remedies: 40,
  get_chart_quality: 40,
  list_assets: 40,
  yoga_activation_by_dasha: 40,
  query_chart_facts: 40,
  chart_snapshot: 40,
  get_graha_yuddha: 40,
  vector_search: 40,
  // W5 Lane L4 (tool-search metadata): a search-result page over ~120 catalog
  // entries is small (name/description/keywords per hit, capped at 100 hits) —
  // 24KB comfortably covers a full 100-result page without ever needing a trim.
  tool_search: 24,
} as const

// ── W3 "One Envelope" — verbosity knob (plan §7 item 6 / master brief §E W3) ──────────
//
// `verbosity: 'concise' | 'detailed'` is an ADDITIVE, optional request-level knob wired
// onto every MCP_RESPONSE_BUDGET_KB-governed tool above. 'detailed' (or omitted) keeps
// today's behavior byte-for-byte (base maxKb, unchanged). 'concise' tightens the ceiling
// this specific call is trimmed against — the caller asking for a leaner page, not a
// server-side policy change to every other caller's default.
//
// C-4 GUARD (CLAUDE.md §N.6 "Serving Density Principle" / response_budget.ts's
// `TrimmableSection.hardFloor`): tightening `maxKb` must NEVER be allowed to reintroduce
// the exact regression class the D-1.5a wave gate caught — a generic trim pass zeroing a
// section that is genuinely populated with confirmed findings (judgment_query's
// bearing_yogas/bearing_afflictions/affliction_mechanisms sections below all declare
// `hardFloor: true`). This function does NOT touch that guarantee at all: `hardFloor`
// is enforced inside `applyResponseBudget`'s PASS 2 regardless of what `maxKb` value is
// passed in — a tighter `maxKb` only means PASS 2 (the hard-cap fallback) is reached
// sooner, not that hardFloor sections are floored past their declared `minKeep`. See
// `platform-mcp/src/__tests__/verbosity_hard_floor.test.ts` for a reproduction of the
// exact D-1.5a scenario (a genuinely-populated bearing_yogas-shaped section) proving this
// holds under a concise-tightened budget, not just the existing declared-budget case.
const CONCISE_MIN_KB = 4
export type Verbosity = 'concise' | 'detailed' | 'exhaustive'
export function resolveVerbosityMaxKb(baseKb: number, verbosity: Verbosity | undefined): number {
  if (verbosity !== 'concise') return baseKb
  return Math.max(Math.round(baseKb * 0.5), CONCISE_MIN_KB)
}
// SAMAPANA Track B (brief §2 item 1): 'exhaustive' is a new named maximal tier, added
// alongside 'concise'/'detailed' — NOT a replacement or a re-numbering of either. It shares
// 'detailed's ceiling exactly: `resolveVerbosityMaxKb`'s `verbosity !== 'concise'` branch
// already returns `baseKb` unchanged for any value other than 'concise', so 'exhaustive'
// needs no new branch there to get "detailed's ceiling, never shrunk" — this is verified by
// samapana_trackb_exhaustive.test.ts, not merely assumed. What 'exhaustive' ADDS beyond that
// (unique to this tier) is forcing every B.11 orientation pre-fetch this call makes
// (fetchOrientationContext below) to its own full form — response_format:'full' instead of
// the terse 10-signal 'digest' — so a caller asking for the maximal tier actually receives
// the maximal signal set, not just a wider byte ceiling around the same terse digest.
// Back-compat is absolute: 'detailed' and omitted verbosity are UNCHANGED by this addition —
// only the new 'exhaustive' branch (both here and in fetchOrientationContext) is added.
const VERBOSITY_ZOD = z.enum(['concise', 'detailed', 'exhaustive']).optional().describe(
  "Response-size knob (W3 + SAMAPANA Track B): 'concise' tightens this call's response-" +
  "budget ceiling (response_budget.ts) to roughly half its normal size — trimmable/catalog-" +
  "style sections shrink first; confirmed-finding sections marked hardFloor (e.g. judgment_" +
  "query's bearing_yogas) never drop below their declared floor, concise or not. 'detailed' " +
  "(default if omitted) keeps the normal, wider ceiling. 'exhaustive' keeps that SAME ceiling " +
  "(never narrower than 'detailed') AND additionally forces this call's mandatory B.11 " +
  "orientation pre-fetch to its full form (response_format:'full', not the default 10-signal " +
  "digest) — the maximal tier for a beyond-acharya-grade deep dive. Prefer reading_depth:" +
  "'deep_dive' on assess_* tools to set this (and the matching internal full-form calls) in " +
  "one flag instead of by hand."
)

// ── SAMAPANA Track B item 2 — the reading_depth:'deep_dive' contract ───────────────────
//
// A single named contract a caller sets ONCE on the natural entry point (assess_wealth/
// assess_career/assess_marriage/assess_health, and bodha_chart_digest_get for the digest
// call directly) instead of setting verbosity + response_format + digest mode by hand on
// every sub-call. 'deep_dive' deterministically resolves to verbosity:'exhaustive' — see
// `resolveEffectiveVerbosity` below, which every reading_depth-bearing tool handler calls.
export type ReadingDepth = 'standard' | 'deep_dive'
export const READING_DEPTH_ZOD = z.enum(['standard', 'deep_dive']).optional().describe(
  "Reading-depth contract (SAMAPANA Track B): 'deep_dive' deterministically forces " +
  "verbosity:'exhaustive' (this call's widest — i.e. 'detailed' — byte ceiling) AND the " +
  "mandatory B.11 orientation pre-fetch to its full form (response_format:'full', top_k_" +
  "signals:100 — not the default 10-signal digest) — a single flag standing in for setting " +
  "verbosity + the digest mode by hand. Never silently downgraded by a stray verbosity:" +
  "'concise'/'detailed' also present on the same call — deep_dive always wins. 'standard' " +
  "(default if omitted) keeps today's behavior byte-for-byte. Cannot be combined with a " +
  "lossy summary/compact response_format on the same call — see guardDeepDiveNotLossy."
)

/** reading_depth:'deep_dive' deterministically forces the effective verbosity to 'exhaustive'
 *  regardless of whatever the caller also passed for `verbosity` on the same call — a deep
 *  dive is never silently downgraded by a stray verbosity:'concise'/'detailed' left over from
 *  a copy-pasted prior call. 'standard' (or omitted reading_depth) leaves `verbosity` as-is,
 *  so back-compat for callers that never touch reading_depth is absolute. */
export function resolveEffectiveVerbosity(
  verbosity: Verbosity | undefined,
  reading_depth: ReadingDepth | undefined,
): Verbosity | undefined {
  return reading_depth === 'deep_dive' ? 'exhaustive' : verbosity
}

// ── SAMAPANA Track B item 3 — hard-guard against ANY lossy summary form under a deep dive ──
//
// No MC-004/MC-006-style "guaranteed-fits" reading_depth:'compact' projection exists in this
// build (that is Track C's OPTIONAL item) — but the *general* shape of "a lossy summary/
// digest projection" already exists TODAY on query_ucd/get_chart_orientation/
// bodha_chart_digest_get: response_format:'summary' caps top_signals at 10, 'digest' caps it
// at 0. `guardDeepDiveNotLossy` is the one bind point every current AND future lossy form
// must be checked against before applying its reduction: if a caller sets reading_depth:
// 'deep_dive' AND ALSO explicitly requests one of the named lossy `formValue`s on the SAME
// call, that is a self-contradictory request — REFUSE it (throw), never silently pick one
// side. (Omitting the lossy-form param entirely under deep_dive is fine — every deep_dive
// call site in this file defaults that param to 'full' when reading_depth is 'deep_dive' and
// the caller left it unset, so this guard only ever fires on an explicit contradiction.) A
// future Track C summary form binds to this SAME function rather than inventing its own gate.
export class DeepDiveLossyFormError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'DeepDiveLossyFormError'
  }
}
export function guardDeepDiveNotLossy(
  reading_depth: ReadingDepth | undefined,
  formParamName: string,
  formValue: string | undefined,
  lossyValues: readonly string[],
): void {
  if (reading_depth === 'deep_dive' && formValue !== undefined && lossyValues.includes(formValue)) {
    throw new DeepDiveLossyFormError(
      `reading_depth:'deep_dive' cannot be combined with ${formParamName}:'${formValue}' — a deep ` +
      `dive must never be silently routed through a lossy summary/compact form (SAMAPANA Track B ` +
      `item 3). Omit ${formParamName} (defaults to the full form under deep_dive) or pass 'full'.`
    )
  }
}

// ── C1 — budget_kb request-side override (contract C1) ────────────────────────
//
// `budget_kb` is an ADDITIVE, optional request-level knob: the caller's own ceiling on the
// wire size of THIS response, in KB. Its ONLY server-side effect is to tighten (never widen)
// the ceiling the existing applyResponseBudget/finalizeMcpBudget trim is measured against —
// no new trimming algorithm, no per-tool default change.
//
//   maxKb = budget_kb ? min(budget_kb, STATIC_DEFAULT) : STATIC_DEFAULT
//
// A budget_kb LOWER than the tool's static default is honored (tighter budget); a HIGHER one
// is clamped to the static default — the server ceiling is a hard cap, not a suggestion.
// Composes with `verbosity`: 'concise' still halves the static default; the final ceiling is
// the tighter of (verbosity-resolved default) and (budget_kb clamped to the static default),
// so neither knob can be used to WIDEN past the static ceiling and either can tighten.
const BUDGET_KB_ZOD = z.number().min(1).max(64).optional().describe(
  "C1 response-budget override (KB, 1–64). Omit to use this tool's server default. A value " +
  "BELOW the default tightens the response (fewer/leaner rows survive); a value ABOVE the " +
  "default is clamped to the default (the server ceiling is a hard cap). When a response is " +
  "actually trimmed, `budget_kb_applied` (the ceiling used) — and `budget_kb_requested` if " +
  "you supplied one — are echoed back on the envelope."
)

/**
 * Resolve the effective wire-budget ceiling for a tool call from (a) the tool's static
 * default ceiling, (b) an optional caller-supplied `budget_kb`, and (c) an optional
 * `verbosity` knob. `budget_kb` clamps to the static default (hard cap); the final result is
 * the tighter of the verbosity-resolved default and the clamped request. This is the single
 * shared resolution mechanism the C1 contract asks for — every call site funnels through it.
 */
function resolveMaxKb(
  toolName: keyof typeof MCP_RESPONSE_BUDGET_KB,
  budgetKb: number | undefined,
  verbosity?: Verbosity,
): number {
  const staticDefault = MCP_RESPONSE_BUDGET_KB[toolName]
  const afterVerbosity = resolveVerbosityMaxKb(staticDefault, verbosity)
  if (budgetKb === undefined) return afterVerbosity
  // Clamp the request to the static ceiling first (hard cap), then take the tighter of that
  // and the verbosity-resolved default so a below-4 budget_kb is honored even under 'concise'
  // (whose CONCISE_MIN_KB floor otherwise applies only to the default, not the caller cap).
  return Math.min(afterVerbosity, budgetKb, staticDefault)
}

/**
 * A trimmable section targeting the B.11 orientation preamble's `entity_profiles` digest —
 * prepended to every B.11-orienting tool response (get_chart_orientation's own digest output,
 * pre-fetched alongside each instrument). This is GENERIC framing (a digest of essentially
 * every other entity in the chart), not the point of an entity-scoped call, and is fully
 * recoverable from get_chart_orientation — so it is the FIRST thing a budget trim sacrifices:
 * `minKeep: 0` (droppable to nothing) and NO `hardFloor` (PASS 2 may zero it entirely). This
 * inverts the pre-EL-36 priority, under which the entity-specific payload arrays (which DO
 * carry the answer) were floored to 0 while this generic preamble survived.
 *
 * EL-36 path fix: `callRegistryCapability` returns the double-wrapped capability shape
 * `{ content: <payload>, is_error }` (see its stub in the r5w3 portrait test and
 * `fetchOrientationContext`), so the live array lives at `orientation_context.content.
 * entity_profiles`, NOT the top-level `orientation_context.entity_profiles` this section
 * used to point at — a silent no-op that was a direct cause of the "generic preamble
 * survives" half of EL-36. The getter/setter below tolerate BOTH nesting levels so the
 * section keeps biting regardless of whether a caller passes the wrapped or unwrapped shape.
 */
function orientationEntityProfilesSection(): TrimmableSection<Record<string, unknown>> {
  const locate = (root: Record<string, unknown>): { holder: Record<string, unknown>; arr: unknown[] } | undefined => {
    const oc = root['orientation_context'] as Record<string, unknown> | undefined
    if (!oc) return undefined
    const inner = oc['content'] as Record<string, unknown> | undefined
    if (inner && Array.isArray(inner['entity_profiles'])) return { holder: inner, arr: inner['entity_profiles'] as unknown[] }
    if (Array.isArray(oc['entity_profiles'])) return { holder: oc, arr: oc['entity_profiles'] as unknown[] }
    return undefined
  }
  return {
    path: 'orientation_context.content.entity_profiles',
    getArray: (root) => locate(root)?.arr,
    setArray: (root, kept) => {
      const found = locate(root)
      if (found) found.holder['entity_profiles'] = kept
    },
    minKeep: 0,
    recover: { instrument: 'bodha_chart_digest_get', hint: 'full entity_profiles digest (this entity-scoped call dropped the generic orientation preamble to protect the entity-specific payload — recover the full holistic digest here).' },
    label: 'orientation_context.entity_profiles (generic preamble — first-sacrificed)',
  }
}

/**
 * Apply the shared response-budget trimmer to a fully-assembled MCP response object
 * (`{ orientation_context, orientation_ok, ...envelope-fields }`). Thin wrapper over
 * `finalizeMcpBudget` (response_budget.ts) — the self-verifying entry point that measures
 * the ACTUAL final object (trim_report + merged drill_pointers included), not just the
 * pre-attachment data-section trim, and degrades trim_report itself if attaching it
 * reopens the gap. See that function's doc-comment for the full R5.1 C1 hard-cap
 * rationale (a live independent verifier caught the original, simpler version of this
 * wrapper attaching trim_report/drill_pointers AFTER the budget check, un-measured).
 */
function applyMcpBudget<T extends Record<string, unknown>>(
  response: T,
  maxKb: number,
  sections: TrimmableSection<T>[],
  budgetKbRequested?: number,
): T {
  const allSections = [...sections, orientationEntityProfilesSection() as unknown as TrimmableSection<T>]
  return finalizeMcpBudget(response, { maxKb, sections: allSections, budgetKbRequested })
}

/**
 * R6 3b-budgets (Ring-2 gap fix, R-1/R-8): `assess_marriage`/`assess_career`/`assess_health`/
 * `assess_wealth` are registered HERE, directly in this file — they call this file's own
 * plain `dualOutput` (line ~301), NOT register_p1_aliases.ts's dualOutput. The auto-budget
 * mechanism wired into register_p1_aliases.ts / register_p1_ganita.ts / register_p1_synthesis.ts
 * never touched these 4 primary tool names — the register's own 1.04MB assess_career
 * measurement names THESE tool names, not their `apex_*` alias variants. This is the missing
 * TS-level backstop: same `autoDetectTrimmableSections` mechanism those files use, combined
 * with this file's own `orientationEntityProfilesSection` (every assess_* response carries
 * `orientation_context` too) and run through the same self-verifying `finalizeMcpBudget`
 * entry point `applyMcpBudget` above already uses — not a second, divergent mechanism.
 *
 * Double-application note: this is the ONLY place `assess_career` (etc.) is registered as an
 * MCP tool — register_p1_aliases.ts's `apex_career_assess` is a SEPARATE tool name that
 * independently fetches its own copy of the capability response and applies its own budget
 * once; neither call path invokes the other's handler or dualOutput, so there is no scenario
 * where one response passes through two budget applications. Re-running `applyResponseBudget`
 * on an already-under-budget object is also a documented no-op (estimateBytes short-circuits
 * before any section is touched) — so even a hypothetical future call chain that composed
 * these two functions would be safe, just redundant.
 */
function applyMcpBudgetAuto<T extends Record<string, unknown>>(
  response: T,
  maxKb: number,
  toolName: string,
  budgetKbRequested?: number,
): T {
  const autoSections = autoDetectTrimmableSections(response, toolName)
  const allSections = [...autoSections, orientationEntityProfilesSection() as unknown as TrimmableSection<T>]
  return finalizeMcpBudget(response, { maxKb, sections: allSections, budgetKbRequested })
}

// ── Flagship completeness: fold dossier's 100%-accounted territory into assess_* ──────────────
//
// γ's diagnosis (verbatim): a genuinely fresh, uninstructed agent asking "How is my wealth?"
// calls `assess_wealth` (the obviously-named tool), gets the shallow default bundle, and never
// discovers `dossier` — scoring ~15% against the domain concept set. The behaviourally-effective
// fix is option (b)(i): route the obvious entrypoint THROUGH dossier's completeness so its OWN
// response carries the same complete accounting dossier would, not a shallow slice.
//
// `runDossier` is a PURE function over compiled slice bundles (no DB, no HTTP) — safe to call
// inline and cheap to page. We page it internally at the ceiling budget, accumulate the WHOLE
// concept slice's coverage into a compact per-serving-tool map, and attach:
//   • `domain_completeness` — the 100% accounting (denominator + per-state tally + coverage map
//     of every serving_tool that carries this domain's concepts, with counts and drill args),
//     plus the post-gate composition_scaffold when the slice is fully accounted; and
//   • a hard, un-missable `judgment_flags` steer + `completeness_directive` string that a
//     continuing agent cannot read past without knowing the complete territory exists and how to
//     hydrate it row-by-row (the `dossier` paging call).
// No astrological value is computed here (B.10): this is a re-serving of dossier's deterministic
// accounting join. If no precompiled slice exists for (domain, chart) the helper returns null and
// assess_* is unchanged — never a fabricated map.

interface CoverageMapEntry {
  serving_tool: string
  concept_count: number
  unit_count: number
  states: Record<string, number>
  example_args?: Record<string, unknown>
}

const DOSSIER_COVERAGE_MAP_MAX_TOOLS = 60

/** Hard ceiling on coverage-walk iterations. Hitting it means the walk was TRUNCATED — the slice
 *  never reported itself done — not that the walk finished. */
const DOSSIER_PAGE_WALK_MAX = 64

/** Why a coverage walk stopped before the slice's own paging reported `more_available: false`.
 *  `null` means it ended naturally, and only then is the cumulative tally a COMPLETE measurement. */
type CoverageWalkTermination =
  | 'page_fetch_threw'
  | 'page_fetch_not_ok'
  | 'page_guard_limit_reached'
  | 'cursor_missing_while_more_available'

/** Page the dossier engine to 100% (pure, embedded slices) and assemble a compact completeness
 *  block. Returns null when no slice is precompiled for (domain, chart) — assess_* then unchanged.
 *
 *  SAMĀPTI F-19 (§N.8): `fully_accounted` asserts "this domain slice is completely accounted for."
 *  It used to be computed as `cov.accounted === cov.slice_size` over the LAST page reached, with no
 *  term for whether the walk actually FINISHED — so it measured "did pagination stop", which every
 *  terminating loop satisfies. The sharp edge was the mid-walk `!page.ok` branch: `runDossier`'s
 *  error shape carries a zeroed `coverage_so_far` (`accounted: 0`, `slice_size: 0`), and the loop
 *  adopted that page before testing `ok`, so a FAILED walk compared `0 === 0` and reported
 *  `fully_accounted: true` on assess_wealth / assess_career / judgment_query.
 *
 *  Now: a not-ok page is never adopted as the coverage source, every early exit is recorded, and a
 *  truncated walk yields `fully_accounted: null` (UNKNOWN — we stopped measuring) reported
 *  distinctly from `false` (we measured, and the slice is genuinely under-accounted). */
export function assembleDomainCompleteness(domain: string, chart_id: string): Record<string, unknown> | null {
  let page: DossierPage
  try {
    page = runDossier({ domain, chart_id, budget_kb: 64 })
  } catch {
    return null
  }
  if (!page.ok) return null

  const perTool = new Map<string, CoverageMapEntry>()
  const accumulate = (p: DossierPage): void => {
    for (const chunk of p.page_units) {
      const conceptSum = chunk.concept_counts.reduce((a, b) => a + b, 0)
      const existing = perTool.get(chunk.serving_tool) ?? {
        serving_tool: chunk.serving_tool,
        concept_count: 0,
        unit_count: 0,
        states: {},
        ...(chunk.values.length > 0
          ? { example_args: { chart_id, ...(chunk.serving_arg_key && chunk.serving_arg_key !== '@' ? { [chunk.serving_arg_key]: chunk.values[0] } : {}) } }
          : {}),
      }
      existing.concept_count += conceptSum
      existing.unit_count += chunk.values.length
      existing.states[chunk.state] = (existing.states[chunk.state] ?? 0) + conceptSum
      perTool.set(chunk.serving_tool, existing)
    }
  }

  accumulate(page)
  let pagesWalked = 1
  let truncated: CoverageWalkTermination | null = null
  while (page.more_available && page.cursor && pagesWalked <= DOSSIER_PAGE_WALK_MAX) {
    let next: DossierPage
    try {
      next = runDossier({ domain, chart_id, budget_kb: 64, cursor: page.cursor })
    } catch {
      truncated = 'page_fetch_threw'
      break
    }
    // F-19: a not-ok page carries a ZEROED coverage_so_far (accounted 0, slice_size 0). Adopting
    // it as `page` — as this loop used to, by assigning before testing `ok` — is what let a failed
    // walk compare 0 === 0 and report FULL accounting. Never adopt a not-ok page.
    if (!next.ok) {
      truncated = 'page_fetch_not_ok'
      break
    }
    page = next
    pagesWalked += 1
    accumulate(page)
  }
  // Fell out of the loop with pages still outstanding ⇒ the walk was truncated, not finished.
  // (`more_available` without a `cursor` is a dossier invariant break — treated as truncation
  // because it is likewise a walk we could not complete, never as a completed measurement.)
  if (truncated === null && page.more_available) {
    truncated = page.cursor ? 'page_guard_limit_reached' : 'cursor_missing_while_more_available'
  }

  // `page` is now the last page the walk SUCCESSFULLY reached — its coverage_so_far is the
  // cumulative tally to that point, and its synthesis_gate is that page's own (correctly
  // conjunctive) gate. Whether the walk reached the end is a SEPARATE fact, held in `truncated`.
  const cov = page.coverage_so_far
  const allTools = Array.from(perTool.values()).sort((a, b) => b.concept_count - a.concept_count)
  const coverage_map = allTools.slice(0, DOSSIER_COVERAGE_MAP_MAX_TOOLS)

  // F-19 / §N.8 — two INDEPENDENT facts, reported as two fields, never collapsed into one bool:
  //   `coverage_walk`     — did we finish MEASURING? (complete | truncated | empty_slice)
  //   `fully_accounted`   — is the slice accounted for? true | false | null(=unknown)
  // `accounted === slice_size` only measures the second claim when the first is 'complete'. A
  // truncated walk yields null (we stopped counting), NOT false (we counted, and it came up short)
  // and never true. A zero denominator is a vacuous 0 === 0, so it is null too — an empty slice is
  // an accounting gap, not a fully-accounted territory.
  const walkFinished = truncated === null
  const denominatorUsable = cov.slice_size > 0
  const fully_accounted: boolean | null =
    walkFinished && denominatorUsable ? cov.accounted === cov.slice_size : null
  const coverage_walk: 'complete' | 'truncated' | 'empty_slice' =
    !walkFinished ? 'truncated' : denominatorUsable ? 'complete' : 'empty_slice'
  const walkComplete = coverage_walk === 'complete'
  const trulyFullyAccounted = fully_accounted === true

  return {
    source: 'dossier (Ω5 gather-then-compose engine)',
    domain,
    chart_id,
    slice_size: cov.slice_size,
    accounted: cov.accounted,
    pct: cov.pct,
    fully_accounted,
    coverage_walk,
    pages_walked: pagesWalked,
    ...(walkComplete
      ? {}
      : {
          coverage_walk_reason: truncated ?? 'slice_size_zero',
          coverage_walk_note:
            'INCOMPLETE MEASUREMENT: ' +
            (coverage_walk === 'truncated'
              ? 'the dossier coverage walk stopped before the slice reported itself done, so ' +
                `\`accounted\`/\`pct\` above are a PARTIAL tally over ${pagesWalked} page(s)`
              : 'the slice reported a zero denominator, so `accounted === slice_size` would be a ' +
                'vacuous 0 === 0 rather than an accounting') +
            ' and `fully_accounted` is null — UNKNOWN, not false and never true. Do not treat ' +
            'this domain as fully accounted; page ' +
            `dossier(domain="${domain}", chart_id="${chart_id}") directly to establish coverage.`,
        }),
    synthesis_gate: page.synthesis_gate,
    coverage_by_state: {
      served: cov.served,
      empty_for_this_chart: cov.empty_for_this_chart,
      not_computed_globally: cov.not_computed_globally,
      superseded_by_aggregate: cov.superseded_by_aggregate,
      excluded_by_named_rule: cov.excluded_by_named_rule,
    },
    chain_pattern_units: cov.chain_pattern_units_seen,
    distinct_serving_tools: allTools.length,
    coverage_map,
    ...(coverage_map.length < allTools.length
      ? { coverage_map_truncated: true, coverage_map_note: `Showing the ${coverage_map.length} highest-concept serving tools of ${allTools.length}; page dossier for the complete per-tool map.` }
      : {}),
    ...(page.composition_scaffold ? { composition_scaffold: page.composition_scaffold } : {}),
    full_hydration: {
      tool: 'dossier',
      args: { domain, chart_id, budget_kb: 64 },
      // F-19: this note used to hardcode "100%" regardless of the computed coverage. It now states
      // what the walk actually established.
      note: (trulyFullyAccounted
        ? 'This block accounts for 100% of the domain concept slice by serving-tool and state — ' +
          'the complete territory, not a shallow default. '
        : `This block accounts for ${cov.accounted}/${cov.slice_size} (${cov.pct}%) of the domain ` +
          'concept slice by serving-tool and state — a PARTIAL accounting, not the complete ' +
          'territory. ') +
        'To HYDRATE the actual rows for any unit, ' +
        'call its serving_tool with {chart_id, ...args}; to walk the whole slice row-by-row with a ' +
        'structural synthesis gate, call `dossier` and follow `cursor` until synthesis_gate=OPEN, ' +
        'then compose the reading over the WHOLE slice.',
    },
    note: (trulyFullyAccounted
      ? 'Complete-accounting domain territory, sourced from the dossier engine (a deterministic ' +
        'join of the Total Concept Inventory × completeness accounting — no computation ' +
        'reimplemented, B.10). The reconciled assessment below is BOUNDED by this: every concept ' +
        'this domain carries is accounted here (by state, with its live serving handle), so a ' +
        'reader holds the whole territory before composing, never a ~15% default slice.'
      : 'PARTIAL-accounting domain territory, sourced from the dossier engine (a deterministic ' +
        'join of the Total Concept Inventory × completeness accounting — no computation ' +
        'reimplemented, B.10). ' +
        (walkComplete
          ? `The walk completed but the slice accounts for only ${cov.accounted}/${cov.slice_size} ` +
            'of its own concepts — a build gap in the slice itself. '
          : 'The coverage walk did not finish, so what is accounted below is what was reached, ' +
            'not what exists. ') +
        'Do NOT read this block as the whole territory; see `coverage_walk` / `fully_accounted`.'),
  }
}

/** Attach the dossier completeness block + an un-missable steer onto an assess_* response,
 *  mutating it in place. No-op when no slice is precompiled for (domain, chart). */
export function attachDomainCompleteness(response: Record<string, unknown>, domain: string, chart_id: string): void {
  const completeness = assembleDomainCompleteness(domain, chart_id)
  if (!completeness) return
  response['domain_completeness'] = completeness
  const pct = (completeness['pct'] as number | undefined) ?? 0
  const sliceSize = (completeness['slice_size'] as number | undefined) ?? 0
  // F-19: the steer must not assert "the full slice" when the accounting could not establish it.
  const fullyAccounted = completeness['fully_accounted'] === true
  const walkReason = String(completeness['coverage_walk_reason'] ?? 'unknown')
  response['completeness_directive'] = fullyAccounted
    ? `COMPLETE ACCOUNTING ATTACHED: this response is backed by the full ${domain} concept slice ` +
      `(${sliceSize} concepts, ${pct}% accounted) via domain_completeness — read that map before ` +
      `concluding. For a row-by-row hydrated reading of the whole territory, call ` +
      `dossier(domain="${domain}", chart_id="${chart_id}") and page to synthesis_gate=OPEN.`
    : `INCOMPLETE ACCOUNTING ATTACHED: the ${domain} concept-slice accounting did NOT establish ` +
      `full coverage (${pct}% of ${sliceSize} concepts reached; coverage_walk=` +
      `${String(completeness['coverage_walk'])}, reason=${walkReason}). domain_completeness is a ` +
      `PARTIAL map — do not read it as the whole territory. Call ` +
      `dossier(domain="${domain}", chart_id="${chart_id}") and page to synthesis_gate=OPEN to ` +
      `establish coverage before composing.`
  // Un-missable structured flag (string entry — a valid JudgmentFlagEntry; renders via
  // judgmentFlagText). Prepended so it is the first flag a reader encounters.
  const existingFlags = Array.isArray(response['judgment_flags'])
    ? (response['judgment_flags'] as unknown[])
    : []
  response['judgment_flags'] = [
    fullyAccounted
      ? `complete_domain_accounting_attached: the full ${domain} concept slice (${sliceSize} concepts, ` +
        `${pct}% accounted) is attached as domain_completeness. This assessment is a reconciled ` +
        `HEADLINE over that complete territory — do not treat it as the whole reading. Call ` +
        `dossier(domain="${domain}", chart_id) to page the full slice row-by-row.`
      : `domain_accounting_incomplete: the ${domain} concept-slice accounting is PARTIAL ` +
        `(${pct}% of ${sliceSize} concepts; coverage_walk=${String(completeness['coverage_walk'])}, ` +
        `reason=${walkReason}). fully_accounted is null — UNKNOWN, not confirmed. The attached ` +
        `domain_completeness map is what was reached, not what exists; call ` +
        `dossier(domain="${domain}", chart_id) to establish the real territory.`,
    ...existingFlags,
  ]
}

/** Compact completeness POINTER (no per-tool coverage_map / scaffold) for tight-budget surfaces
 *  like judgment_query (12KB). Same 100% accounting summary + the dossier hydration call, sized to
 *  fit alongside an existing envelope. Returns null when no flagship slice exists for (domain, chart). */
export function buildDomainCompletenessPointer(domain: unknown, chart_id: string): Record<string, unknown> | null {
  if (typeof domain !== 'string' || !domain) return null
  const full = assembleDomainCompleteness(domain, chart_id)
  if (!full) return null
  // F-19: the pointer must carry the SAME honest signal as the full block — a compact surface is
  // not a licence to flatten `true | false | null` back into a bare boolean, nor to keep asserting
  // "100% accounted" in prose when the walk never established it.
  const fullyAccounted = full['fully_accounted'] === true
  return {
    source: full['source'],
    domain,
    slice_size: full['slice_size'],
    accounted: full['accounted'],
    pct: full['pct'],
    fully_accounted: full['fully_accounted'],
    coverage_walk: full['coverage_walk'],
    ...(full['coverage_walk_reason'] !== undefined
      ? { coverage_walk_reason: full['coverage_walk_reason'] }
      : {}),
    synthesis_gate: full['synthesis_gate'],
    coverage_by_state: full['coverage_by_state'],
    distinct_serving_tools: full['distinct_serving_tools'],
    full_hydration: full['full_hydration'],
    note: fullyAccounted
      ? `A COMPLETE ${domain} reading (all ${String(full['slice_size'])} domain concepts, 100% ` +
        `accounted) is available via dossier(domain="${domain}", chart_id) — this judgment is a ` +
        `bhava/domain-scoped verdict, not the whole-territory sweep.`
      : `INCOMPLETE accounting for ${domain}: only ${String(full['accounted'])}/` +
        `${String(full['slice_size'])} concepts (${String(full['pct'])}%) were accounted ` +
        `(coverage_walk=${String(full['coverage_walk'])}), so fully_accounted is null — UNKNOWN, ` +
        `not confirmed. Call dossier(domain="${domain}", chart_id) to establish the territory; ` +
        `this judgment remains a bhava/domain-scoped verdict either way.`,
  }
}

/** PARIŚODHANA R-10 fix: join the already-computed L1 `ga_vichara` leverage_index family
 *  (chart_vichara, served live via `marsys://tool/L1/get_vichara` / ganita_vichara_get) into
 *  an assess_* response, mutating in place. Confirmed live (chart 482012f1-…): 7 real,
 *  populated rows (one per graha) existed for domain="wealth" via ganita_vichara_get, but the
 *  field was completely ABSENT — not null — from assess_wealth's response shape. Pure
 *  serving-layer wiring; no new computation (B.10) and no restatement of the L1 value (§N.5)
 *  — every emitted row is a read-only projection of the vichara row's own fields
 *  (value_num/value_jsonb/constituent_fact_ids/formula_version/source_citation), so a caller
 *  can always resolve back to chart_vichara/chart_facts via the same ids the row already
 *  carries. Never throws: a failed join degrades to an honest empty array + reason, never a
 *  fabricated substitute. */
export async function attachLeverageIndex(
  response: Record<string, unknown>, domain: string, chart_id: string, ayanamsha_id: string, principal: Principal,
): Promise<void> {
  const drillPointer = `ganita_vichara_get(chart_id, family="leverage_index", domain="${domain}")`
  try {
    const payload = await callRegistryCapability(
      'marsys://tool/L1/get_vichara',
      { chart_id, ayanamsha_id, family: 'leverage_index', domain },
      chart_id, principal,
    )
    const inner = unwrapCapabilityContent(payload) as Record<string, unknown> | undefined
    const rawRows = inner && Array.isArray(inner['rows']) ? inner['rows'] as Record<string, unknown>[] : []
    response['leverage_index_by_graha'] = rawRows.map((r) => {
      const j = (r['value_jsonb'] as Record<string, unknown> | undefined) ?? {}
      return {
        subject: r['subject'],
        leverage_index: r['value_num'],
        capability: j['capability'],
        dignity_score: j['dignity_score'],
        domain_load_bearing_weight: j['domain_load_bearing_weight'],
        dasha_runway_weight: j['dasha_runway_weight'],
        years_to_start: j['years_to_start'],
        constituent_fact_ids: r['constituent_fact_ids'],
        formula_version: r['formula_version'],
        source_citation: r['source_citation'],
      }
    })
    response['leverage_index_note'] =
      `leverage_index (domain_load_bearing_weight ÷ capability, dasha-runway-weighted — the ` +
      `number remedy/intervention-timing ranks on) sourced read-only from L1 ga_vichara ` +
      `(chart_vichara, §N.5 — never restated/recomputed here). Full per-row breakdown + ` +
      `constituent_fact_ids: call ${drillPointer}.`
    if (rawRows.length === 0) {
      response['leverage_index_empty_reason'] = typeof inner?.['empty_reason'] === 'string'
        ? inner['empty_reason']
        : `No leverage_index rows for domain="${domain}" on this chart — call ${drillPointer} for the live honest-empty diagnostic.`
    }
  } catch (err) {
    // Never fabricate a value on failure — degrade to an honest, clearly-labeled gap instead.
    response['leverage_index_by_graha'] = []
    response['leverage_index_empty_reason'] =
      `leverage_index join failed (${err instanceof Error ? err.message : String(err)}) — call ${drillPointer} directly.`
  }
}

// ── W7 — Substance-inline domain reading (SATYA-ŚEṢA W7 addendum) ──────────────────────────
//
// The Offer Law (SATYA_SHESHA_W7_ADDENDUM_v1_0.md §1, proven live by the sealed evaluator
// harness): #782's fix above (attachDomainCompleteness) folds dossier's 100%-accounted
// completeness RECEIPT into assess_wealth/assess_career — but a receipt is a pointer, and a
// naive consumer reads a pointer and does not follow it (sealed-harness score stayed flat at
// 2-3/13 with the receipt attached, live-measured). W7 fixes this by composing the acharya's
// OPENING READING — one to three dense, fact_id-grounded sentences per top-tier concept
// family — directly INTO assess_wealth/assess_career's own response (`reading`), so the tool
// a naive caller actually reaches for already carries the substance, not just an accounting
// of where the substance lives.
//
// No new astrological computation happens here (B.10): every sentence is a deterministic
// template over data already fetched by this same call (`data`, already assembled above) plus
// a small number of additional READS of already-registered, already-computed L1/L2
// capabilities (net_argala_per_varga, bodha_mechanisms, bo_upaya remedies, special_lagna,
// bhava_arudha, karakamsa_position, nakshatra_cross_ayanamsha) — never a re-derivation, and
// every family's fact_ids resolve back to real chart_facts/bodha_* rows (§N.5).
//
// Family list per domain mirrors that domain's TCI top tier — wealth's 13 and career's 12
// families below are the same shape SEALED_EVALUATOR_HARNESS_v1_0.md §3's required_concepts
// lists were frozen FROM (they coincide by construction, not because this code reads the
// harness — this file never imports or inspects the harness or its grading list, so a future
// harness edit cannot change what this digest serves, and vice versa; W7 addendum §2's
// integrity constraint). The mechanism generalizes to any domain by adding one more row to
// DOMAIN_READING_FAMILIES + its companion config maps below — nothing here is wealth/career-
// hardcoded logic, only wealth/career-specific DATA POINTERS (exactly like DOMAIN_DIRECT_VARGAS
// in the platform-side register_d8_assess_domain.ts this mirrors).

export interface ReadingFamilyEntry {
  family: string
  label: string
  // MC-017 fix (SHODHANA follow-up, Dvārapāla-authorized): the prior single token
  // `not_computed_at_l1` was ambiguous — it read as "the underlying astrological computation
  // was never done at L1" when in every site below it actually meant "this reading-digest's
  // curated/assessor-level block wasn't populated on this call," while the raw positions/facts
  // usually DO exist elsewhere (chart_facts / chart_divisionals / bodha_mechanisms / bodha_upaya).
  // Split into two distinct, verified states so a caller never over-reads an absence:
  //   - 'domain_block_not_served': the classical concept IS computed somewhere in the system
  //     (an L1 chart_facts category, an L1 chart_divisionals varga, or an L2 bodha_* table/
  //     capability all exist for it) — this specific reading-digest fetch just didn't surface
  //     it (query-param mismatch, call failure, or a not-yet-populated per-varga block).
  //   - 'not_computed_globally': the concept was genuinely never computed at any level (no raw
  //     data either) — mirrors MC-009's `not_computed_globally` convention for L2 mechanism
  //     classes (dispositor_cycle/house_lordship_cycle/mutual_reception/parivartana_chain/
  //     stellium/yoga_cluster) and must never be conflated with it.
  status: 'served' | 'partial' | 'empty_for_this_chart' | 'domain_block_not_served' | 'not_computed_globally'
  sentences: string[]
  fact_ids: string[]
}

const WEALTH_READING_FAMILIES = [
  'per_varga_ashtakavarga', 'divisional_D2', 'divisional_D11', 'indu_lagna',
  'argala_house_2', 'argala_house_11', 'full_dispositor_closure',
  'all_chart_mechanisms_and_chains', 'special_lagnas', 'cross_ayanamsha_agreement',
  'timing_windows', 'remedies', 'contradictions_with_adjudication',
] as const

const CAREER_READING_FAMILIES = [
  'per_varga_ashtakavarga', 'divisional_D10', 'divisional_D9', 'karakamsha_or_swamsha',
  'argala_house_10', 'full_dispositor_closure',
  'all_chart_mechanisms_and_chains', 'special_lagnas', 'cross_ayanamsha_agreement',
  'timing_windows', 'remedies', 'contradictions_with_adjudication',
] as const

const DOMAIN_READING_FAMILIES: Record<string, readonly string[]> = {
  wealth: WEALTH_READING_FAMILIES,
  career: CAREER_READING_FAMILIES,
}
// The domain's classical-wealth/career vargas — same pairing register_d8_assess_domain.ts's
// DOMAIN_DIRECT_VARGAS uses, read back here from `data.varga_analysis` (already fetched).
const DOMAIN_READING_VARGAS: Record<string, [string, string]> = { wealth: ['D2', 'D11'], career: ['D10', 'D9'] }
const DOMAIN_READING_HOUSES: Record<string, number[]> = { wealth: [2, 11], career: [10] }
const DOMAIN_READING_KARAKA_CODE: Record<string, string> = { wealth: 'JUP', career: 'SAT' }
const DOMAIN_READING_KARAKA_LABEL: Record<string, string> = { wealth: 'Jupiter', career: 'Saturn' }

function titleCaseUnderscored(s: string): string {
  return s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

interface ChartFactsRow {
  fact_id?: unknown
  fact_category?: unknown
  fact_subject?: unknown
  fact_key?: unknown
  fact_value_num?: unknown
  fact_value_text?: unknown
  fact_value_jsonb?: unknown
}

/** TRACK A / SAMĀPANA §1 root-cause fix (real, confirmed root cause — NOT the routing/auth
 *  divergence originally suspected in PŪRṆA-VIRĀMA §4/§9.1; that hypothesis is REFUTED by direct
 *  evidence below):
 *
 *  Every registry `CapabilityDescriptor.handler` (query_mechanisms.ts, chart_facts_query in
 *  register_d7_channel.ts, query_remedies, etc.) returns a `{ content: X, is_error: boolean }`
 *  ToolResult-shaped wrapper — confirmed by reading query_mechanisms.ts's own `return { content:
 *  {...}, is_error: false }` and chart_facts_query's identical pattern. `/api/retrieval/capability`
 *  (route.ts) does `const content = await getOrComputeCapability(..., () => capability.handler(...))`
 *  then `NextResponse.json({ ok: true, content })` — so the HTTP JSON body's `content` field IS
 *  that whole `{ content, is_error }` wrapper, not the inner payload. `callRegistryCapability`
 *  (below) returns `data.content` verbatim, so every `fetchReadingSupplements` result
 *  (argala/mechanisms/remedies/specialLagna/arudha/karakamsa/crossAyanamsha) arrives here as the
 *  DOUBLY-WRAPPED `{ content: { rows / narration / prescriptions / ... }, is_error }` shape.
 *  `resolveChartHeader` (further down this file) already unwraps this correctly via
 *  `raw?.['content']`; `buildDomainReading`'s own `sourceData = data['content'] ?? data` fixed the
 *  SAME class of bug for the assess_wealth/assess_career payload itself (PŪRṆA-VIRĀMA close-out).
 *  But the family readers below (`rowsOf`, `readMechanismsFamily`, `readDispositorClosureFamily`,
 *  `readRemediesFamily`) never got that fix — they read `rows`/`narration`/`prescriptions` directly
 *  off the WRAPPER, one level too shallow, so they always found `undefined` and reported an honest
 *  (but false) empty/gap. No thrown error, no auth/entitlement denial, no cache poisoning, no
 *  ayanamsha-alias divergence (that one IS real but separate — see readCrossAyanamshaFamily) — just
 *  this shape mismatch. Live-verified (Track A, 2026-07-27): calling the SAME capability with the
 *  SAME args via its standalone MCP tool (bodha_mechanisms_get, ganita_chart_facts_get,
 *  bodha_remedies_get) returns rich real data for this chart, proving the internal HTTP round-trip
 *  itself is not the defect — only this file's own unwrapping of its response was. */
function unwrapCapabilityContent(payload: unknown): unknown {
  if (!payload || typeof payload !== 'object') return payload
  const p = payload as Record<string, unknown>
  if (typeof p['__fetch_error'] === 'string') return payload // safeCall's thrown-error diagnostic stub — not a wrapper
  if ('content' in p && typeof p['is_error'] === 'boolean') return p['content'] ?? payload
  return payload
}

function rowsOf(payload: unknown): ChartFactsRow[] {
  const inner = unwrapCapabilityContent(payload)
  if (!inner || typeof inner !== 'object') return []
  const rows = (inner as Record<string, unknown>)['rows']
  return Array.isArray(rows) ? (rows as ChartFactsRow[]) : []
}

/** Diagnostic (PŪRṆA-VIRĀMA): if a supplement call threw (tagged by safeCall's catch), surface
 *  the real error inline instead of letting it read identically to a genuine computed-empty. */
function diagSuffix(payload: unknown): string {
  if (!payload || typeof payload !== 'object') return ''
  const p = payload as Record<string, unknown>
  if (typeof p['__fetch_error'] !== 'string') return ''
  return ` [DIAG fetch_error: ${p['__fetch_error']} | uri=${String(p['__fetch_uri'])} args=${JSON.stringify(p['__fetch_args'])}]`
}

/** Additional read-only capability calls the digest needs beyond what assess_wealth/career
 *  already fetched (W7.2): argala on the domain's houses, chart-wide mechanisms/chains,
 *  remedies, special lagnas + Arudha Lagna, karakamsa (career only), cross-ayanamsha
 *  nakshatra-consistency. Every call reads an existing L1/L2 capability's already-computed
 *  rows — never a new computation (B.10). A failed call degrades to `null`, never a fabricated
 *  substitute — the corresponding family then reports an honest gap instead of substance. */
async function fetchReadingSupplements(
  domain: string, chart_id: string, ayanamsha_id: string, principal: Principal,
): Promise<{
  argala: unknown; mechanisms: unknown; remedies: unknown
  specialLagna: unknown; arudha: unknown; karakamsa: unknown; crossAyanamsha: unknown
}> {
  const houses = DOMAIN_READING_HOUSES[domain] ?? []
  // Diagnostic (PŪRṆA-VIRĀMA): distinguish "the call threw" from "the call succeeded with a
  // genuinely empty result" — the two were previously conflated into the same `null`, which
  // hid a real live-probed gap (5/13 families empty post-#799) behind an ambiguous "call failed
  // or returned nothing" message. A thrown error now carries its real message through to the
  // family sentence instead of being silently swallowed (B.10: never let a fetch failure look
  // identical to an honest computed-empty).
  const safeCall = async (uri: string, args: Record<string, unknown>): Promise<unknown> => {
    try {
      return await callRegistryCapability(uri, { chart_id, ayanamsha_id, ...args }, chart_id, principal)
    } catch (err) {
      return { __fetch_error: err instanceof Error ? err.message : String(err), __fetch_uri: uri, __fetch_args: args }
    }
  }

  const [argala, mechanisms, remedies, specialLagna, arudha, karakamsa, crossAyanamsha] = await Promise.all([
    houses.length > 0
      ? safeCall('marsys://tool/L1/chart_facts_query', {
          category: 'net_argala_per_varga',
          fact_subject: houses.map((h) => `D1_HOUSE_${h}`).join(','),
          shape: 'rows',
        })
      : Promise.resolve(null),
    safeCall('marsys://tool/L2/query_mechanisms', { limit: 50 }),
    safeCall('marsys://tool/L2/query_remedies', { domain }),
    safeCall('marsys://tool/L1/chart_facts_query', { category: 'special_lagna', shape: 'rows', limit: 200 }),
    safeCall('marsys://tool/L1/chart_facts_query', { category: 'bhava_arudha', shape: 'rows', limit: 200 }),
    domain === 'career'
      ? safeCall('marsys://tool/L1/chart_facts_query', { category: 'karakamsa_position', shape: 'rows', limit: 200 })
      : Promise.resolve(null),
    // MC-017-documented second bug (distinct from the content-unwrap fix above): ga_nakshatra.py's
    // cross_ayanamsha pass writes nakshatra_cross_ayanamsha rows under ayanamsha_id='INVARIANT'
    // (by design — the cross-ayanamsha agreement value is the same across all 5 sidereal
    // ayanamshas, so it is stored once, invariantly), never under the domain's own ayanamsha_id
    // (e.g. lahiri_chitrapaksha). The outer `ayanamsha_id` in safeCall's spread was shadowing this
    // with the domain's ayanamsha, filtering out every row. Overriding it here to 'INVARIANT'
    // reaches the actual stored rows — readCrossAyanamshaFamily's own comment already named this
    // exact mismatch; this wires the fix through.
    safeCall('marsys://tool/L1/chart_facts_query', { category: 'nakshatra_cross_ayanamsha', shape: 'rows', limit: 200, ayanamsha_id: 'INVARIANT' }),
  ])
  return { argala, mechanisms, remedies, specialLagna, arudha, karakamsa, crossAyanamsha }
}

/** varga substance already present in `data.varga_analysis` (buildVargaAnalysisDirect, EL-45)
 *  — per_varga_ashtakavarga / divisional_D2 / divisional_D11 / divisional_D10 / divisional_D9
 *  families read this, never re-fetch it (D1 of the addendum: this substance was ALREADY
 *  served, just never foregrounded into a family-level sentence). */
function readVargaFamily(vargaAnalysis: Record<string, unknown> | undefined, varga: string, purpose: string): ReadingFamilyEntry {
  const perVarga = (vargaAnalysis?.['per_varga'] as Record<string, unknown> | undefined)?.[varga] as Record<string, unknown> | undefined
  if (!perVarga) {
    // MC-017: verified this is a serving gap, not a computation gap — ${varga}'s positions are
    // standard L1/L1.5 output (ga_vargas_writer + ga_structural_writer materialize all 30 vargas,
    // including this one, into chart_divisionals; buildVargaAnalysisDirect then reads
    // graha_dignity_per_varga/ashtakavarga_pinda_sarva_per_varga FROM those rows) — the raw
    // divisional positions exist even when this call's per_varga block came back empty.
    return { family: `divisional_${varga}`, label: `Divisional chart ${varga}`, status: 'domain_block_not_served', sentences: [
      `${varga} (${purpose}) is not in this call's varga_analysis — ${vargaAnalysis?.['note'] ? String(vargaAnalysis['note']) : 'no direct-consumption block returned'} ` +
        `(raw ${varga} positions exist in chart_divisionals/chart_facts graha_dignity_per_varga — see chart_facts_query with divisional_chart="${varga}").`,
    ], fact_ids: [] }
  }
  const dignityRows = Array.isArray(perVarga['graha_dignity']) ? perVarga['graha_dignity'] as Record<string, unknown>[] : []
  const factIds = dignityRows.map((r) => String(r['fact_id'] ?? '')).filter(Boolean)
  const notable = dignityRows.filter((r) => typeof r['dignity'] === 'string' && ['exalted', 'own_sign', 'debilitated', 'moolatrikona'].includes(String(r['dignity'])))
  const sentences: string[] = []
  if (dignityRows.length > 0) {
    const sample = (notable.length > 0 ? notable : dignityRows).slice(0, 4)
      .map((r) => `${r['graha']} ${r['dignity']}${r['house_display'] ? ` in ${r['house_display']}` : ''}`)
    sentences.push(`${varga} (${purpose}): ${sample.join(', ')}${dignityRows.length > sample.length ? ` (+${dignityRows.length - sample.length} more grahas placed)` : ''}.`)
  }
  const avAvailable = perVarga['ashtakavarga_available'] === true
  const avRows = Array.isArray(perVarga['ashtakavarga_pinda_sarva']) ? perVarga['ashtakavarga_pinda_sarva'] as Record<string, unknown>[] : []
  if (avAvailable && avRows.length > 0) {
    const top = [...avRows].sort((a, b) => Number(b['pinda_sarva'] ?? 0) - Number(a['pinda_sarva'] ?? 0)).slice(0, 3)
      .map((r) => `${r['graha']} ${r['pinda_sarva']}`)
    sentences.push(`Per-varga Ashṭakavarga piṇḍa (${varga}): ${top.join(', ')}.`)
    for (const r of avRows) { const fid = r['fact_id']; if (typeof fid === 'string') factIds.push(fid) }
  } else if (perVarga['empty_reason']) {
    sentences.push(String(perVarga['empty_reason']))
  }
  return {
    family: `divisional_${varga}`,
    label: `Divisional chart ${varga} (${purpose})`,
    status: sentences.length > 0 ? 'served' : 'empty_for_this_chart',
    sentences: sentences.length > 0 ? sentences : [`No ${varga} placements returned for this chart.`],
    fact_ids: Array.from(new Set(factIds)),
  }
}

function readAshtakavargaFamily(vargaAnalysis: Record<string, unknown> | undefined, vargas: [string, string]): ReadingFamilyEntry {
  const perVarga = vargaAnalysis?.['per_varga'] as Record<string, unknown> | undefined
  const sentences: string[] = []
  const factIds: string[] = []
  for (const v of vargas) {
    const block = perVarga?.[v] as Record<string, unknown> | undefined
    const avRows = Array.isArray(block?.['ashtakavarga_pinda_sarva']) ? block!['ashtakavarga_pinda_sarva'] as Record<string, unknown>[] : []
    if (block?.['ashtakavarga_available'] === true && avRows.length > 0) {
      const top = [...avRows].sort((a, b) => Number(b['pinda_sarva'] ?? 0) - Number(a['pinda_sarva'] ?? 0)).slice(0, 3)
        .map((r) => `${r['graha']} ${r['pinda_sarva']}`)
      sentences.push(`${v} piṇḍa sarva — ${top.join(', ')}.`)
      for (const r of avRows) { const fid = r['fact_id']; if (typeof fid === 'string') factIds.push(fid) }
    } else if (block?.['empty_reason']) {
      sentences.push(`${v}: ${String(block['empty_reason'])}`)
    }
  }
  return {
    family: 'per_varga_ashtakavarga',
    label: 'Per-varga Ashṭakavarga (piṇḍa sarva)',
    status: factIds.length > 0 ? 'served' : 'empty_for_this_chart',
    sentences: sentences.length > 0 ? sentences : ['No per-varga Ashṭakavarga rows returned for this chart\'s domain vargas.'],
    fact_ids: Array.from(new Set(factIds)),
  }
}

function readInduLagnaFamily(vargaAnalysis: Record<string, unknown> | undefined): ReadingFamilyEntry {
  const indu = vargaAnalysis?.['indu_lagna'] as Record<string, unknown> | undefined
  if (!indu) {
    return { family: 'indu_lagna', label: 'Indu Lagna (Jaimini wealth-strength lagna)', status: 'empty_for_this_chart', sentences: ['Indu Lagna was not returned for this chart/ayanamsha.'], fact_ids: [] }
  }
  return {
    family: 'indu_lagna',
    label: 'Indu Lagna (Jaimini wealth-strength lagna)',
    status: 'served',
    sentences: [
      `Indu Lagna falls in ${String(indu['sign'] ?? '?')} (lord ${String(indu['sign_lord'] ?? '?')}, D1 house ${String(indu['house_d1'] ?? '?')}, nakshatra ${String(indu['nakshatra'] ?? '?')}) — the dedicated Jaimini wealth-strength point, distinct from the 2nd/11th house-and-lord reading.`,
    ],
    fact_ids: (indu['fact_ids'] as string[] | undefined) ?? [],
  }
}

function readKarakamshaFamily(karakamsaPayload: unknown): ReadingFamilyEntry {
  const rows = rowsOf(karakamsaPayload)
  const byKey = new Map<string, ChartFactsRow>()
  for (const r of rows) { if (String(r.fact_subject) === 'KARAKAMSA') byKey.set(String(r.fact_key), r) }
  const sign = byKey.get('sign')
  const ak = byKey.get('atmakaraka_graha')
  if (!sign && !ak) {
    // MC-017: verified serving gap, not absence — karakamsa_position is written by
    // ga_sensitive_writer (L1, category 18) from the Atmakaraka's D9 sign, and the raw
    // ingredients (Atmakaraka determination + D9 navamsa positions for every graha) are
    // standard chart_facts/chart_divisionals output for any built chart; a missing
    // karakamsa_position row for this specific ayanamsha_id is a data-plane/query gap, not
    // proof the underlying computation never happened.
    return { family: 'karakamsha_or_swamsha', label: 'Karakāṁśa (Jaimini)', status: 'domain_block_not_served', sentences: ['karakamsa_position carries no KARAKAMSA rows for this chart/ayanamsha (raw Ātmakāraka + D9 navāṃśa positions exist in chart_facts/chart_divisionals — see chart_facts_query category="karaka_chara_position" or divisional_chart="D9").'], fact_ids: [] }
  }
  const factIds = [sign, ak].filter((r): r is ChartFactsRow => !!r).map((r) => String(r.fact_id ?? '')).filter(Boolean)
  return {
    family: 'karakamsha_or_swamsha',
    label: 'Karakāṁśa (Jaimini)',
    status: 'served',
    sentences: [
      `Karakāṁśa (D9 sign of the Ātmakāraka) falls in ${String(sign?.fact_value_text ?? '?')}` +
        `${ak ? `, Ātmakāraka is ${String(ak.fact_value_text ?? '?')}` : ''} — the Jaimini soul-significator's` +
        ' navāṃśa placement, read alongside the D10/10th-lord career signature above.',
    ],
    fact_ids: Array.from(new Set(factIds)),
  }
}

function readArgalaFamily(domain: string, argalaPayload: unknown, house: number): ReadingFamilyEntry {
  const family = `argala_house_${house}`
  const rows = rowsOf(argalaPayload)
  const row = rows.find((r) => String(r.fact_subject) === `D1_HOUSE_${house}`)
  if (!row) {
    // MC-017: verified serving gap, not absence — net_argala_per_varga is written by
    // ga_structural_writer for ALL_30_VARGAS (including D1) per house, so D1 house argala is
    // standard L1 output for any built chart; a missing D1_HOUSE_${house} row here reflects
    // this call/ayanamsha not surfacing it, never that the underlying house/lord positions
    // (which exist as basic chart_facts) were never computed.
    return { family, label: `Net argala on house ${house}`, status: 'domain_block_not_served', sentences: [`net_argala_per_varga carries no D1_HOUSE_${house} row for this chart (raw house/lord positions exist in chart_facts — see chart_facts_query category="net_argala_per_varga").${diagSuffix(argalaPayload)}`], fact_ids: [] }
  }
  const net = Number(row.fact_value_num ?? 0)
  const reading = net > 0
    ? `net supportive (argala outweighs virodha-argala — interventions on this house's results are more helped than blocked)`
    : net < 0
    ? `net obstructed (virodha-argala outweighs argala — interventions on this house's results are more blocked than helped)`
    : `exactly balanced (argala and virodha-argala cancel)`
  return {
    family, label: `Net argala on house ${house}`, status: 'served',
    sentences: [`House ${house} carries a net argala score of ${net} — ${reading} (whole-sign, D1, all contributing offsets from BPHS's argala/virodha-argala rule).`],
    fact_ids: [String(row.fact_id ?? '')].filter(Boolean),
  }
}

function readSpecialLagnaFamily(specialPayload: unknown, arudhaPayload: unknown): ReadingFamilyEntry {
  const rows = rowsOf(specialPayload)
  const bySubject = new Map<string, Map<string, ChartFactsRow>>()
  for (const r of rows) {
    const subj = String(r.fact_subject)
    if (!bySubject.has(subj)) bySubject.set(subj, new Map())
    bySubject.get(subj)!.set(String(r.fact_key), r)
  }
  const factIds: string[] = []
  const parts: string[] = []
  for (const subj of ['BHAVA_LAGNA', 'GHATI_LAGNA', 'HORA_LAGNA', 'SREE_LAGNA', 'VARNADA_LAGNA']) {
    const keys = bySubject.get(subj)
    const sign = keys?.get('sign')
    if (sign?.fact_value_text) {
      parts.push(`${titleCaseUnderscored(subj)} in ${String(sign.fact_value_text)}`)
      factIds.push(String(sign.fact_id ?? ''))
    }
  }
  const arudhaRows = rowsOf(arudhaPayload)
  const al = arudhaRows.find((r) => String(r.fact_subject).includes('HOUSE_1') || String(r.fact_subject) === 'AL1' || String(r.fact_subject) === 'ARUDHA_LAGNA')
  if (al) {
    const signVal = al.fact_value_text ?? (al.fact_value_jsonb as Record<string, unknown> | null)?.['sign']
    if (signVal) { parts.push(`Ārūḍha Lagna (AL) in ${String(signVal)}`); factIds.push(String(al.fact_id ?? '')) }
  }
  return {
    family: 'special_lagnas',
    label: 'Special lagnas (Bhava/Ghati/Hora/Sree/Varnada) + Ārūḍha Lagna',
    status: parts.length > 0 ? 'served' : 'empty_for_this_chart',
    sentences: parts.length > 0 ? [`${parts.join('; ')}.`] : [`No special-lagna rows returned for this chart/ayanamsha.${diagSuffix(specialPayload)} [rows_len=${rows.length}]`],
    fact_ids: Array.from(new Set(factIds.filter(Boolean))),
  }
}

function readCrossAyanamshaFamily(domain: string, crossAyanamshaPayload: unknown): ReadingFamilyEntry {
  const rows = rowsOf(crossAyanamshaPayload)
  const karakaCode = DOMAIN_READING_KARAKA_CODE[domain]
  const karakaLabel = DOMAIN_READING_KARAKA_LABEL[domain]
  const byKarakaKey = new Map<string, ChartFactsRow>()
  const byLagnaKey = new Map<string, ChartFactsRow>()
  for (const r of rows) {
    const subj = String(r.fact_subject)
    if (subj === karakaCode) byKarakaKey.set(String(r.fact_key), r)
    if (subj === 'LAGNA') byLagnaKey.set(String(r.fact_key), r)
  }
  const karakaConsistency = byKarakaKey.get('nak_5ay_consistency')
  const lagnaConsistency = byLagnaKey.get('nak_5ay_consistency')
  if (!karakaConsistency && !lagnaConsistency) {
    // MC-017: verified serving gap, not absence — ga_nakshatra.py's cross_ayanamsha pass writes
    // nakshatra_cross_ayanamsha rows with ayanamsha_id='INVARIANT' (by design: the value is the
    // SAME across all 5 sidereal ayanamshas, so it is stored once, invariantly), but this
    // supplement fetch queries chart_facts_query with the domain's actual ayanamsha_id
    // (e.g. lahiri_chitrapaksha) — a mismatched filter that returns zero rows even though the
    // rows exist. The raw per-ayanamsha nakshatra positions this is derived from are themselves
    // ordinary chart_facts output too.
    return { family: 'cross_ayanamsha_agreement', label: 'Cross-ayanaṃśa agreement', status: 'domain_block_not_served', sentences: [`nakshatra_cross_ayanamsha carries no rows for the domain kāraka or Lagna on this chart (the rows are stored under ayanamsha_id="INVARIANT", not this call's ayanamsha_id — see chart_facts_query category="nakshatra_cross_ayanamsha" ayanamsha_id="INVARIANT").${diagSuffix(crossAyanamshaPayload)}`], fact_ids: [] }
  }
  const sentences: string[] = []
  const factIds: string[] = []
  if (karakaConsistency) {
    sentences.push(`${karakaLabel} (${domain} kāraka) holds the SAME nakṣatra in ${String(karakaConsistency.fact_value_text)} of the 5 sidereal ayanaṃśas this chart carries — its dignity/house reading above is cross-ayanaṃśa stable to that degree, not an artifact of one ayanaṃśa choice.`)
    factIds.push(String(karakaConsistency.fact_id ?? ''))
  }
  if (lagnaConsistency) {
    sentences.push(`Lagna's nakṣatra agrees across ${String(lagnaConsistency.fact_value_text)} of 5 ayanaṃśas (its RAŚI/sign is Aries in all 5 per the chart's FORENSIC anchor — sign-level agreement is a coarser, stronger invariant than the finer nakṣatra-level consistency reported here).`)
    factIds.push(String(lagnaConsistency.fact_id ?? ''))
  }
  return { family: 'cross_ayanamsha_agreement', label: 'Cross-ayanaṃśa agreement', status: 'served', sentences, fact_ids: Array.from(new Set(factIds.filter(Boolean))) }
}

function readMechanismsFamily(mechanismsPayload: unknown): ReadingFamilyEntry {
  const unwrapped = unwrapCapabilityContent(mechanismsPayload)
  if (!unwrapped || typeof unwrapped !== 'object') {
    // MC-017: verified serving gap, not absence — marsys://tool/L2/query_mechanisms is a real,
    // wired capability over the bodha_mechanisms table (also independently servable via
    // bodha_mechanisms_get), built for any chart that ran the L2 Bodha campaign. A failed/empty
    // call here means THIS fetch didn't reach the data, not that mechanisms were never computed.
    return { family: 'all_chart_mechanisms_and_chains', label: 'L2 mechanisms (dispositor chains/cycles, yoga clusters)', status: 'domain_block_not_served', sentences: [`query_mechanisms call failed or returned nothing for this chart (bodha_mechanisms data may still exist — see bodha_mechanisms_get).${diagSuffix(mechanismsPayload)}`], fact_ids: [] }
  }
  const content = unwrapped as Record<string, unknown>
  const rows = Array.isArray(content['rows']) ? content['rows'] as Record<string, unknown>[] : []
  if (rows.length === 0) {
    return { family: 'all_chart_mechanisms_and_chains', label: 'L2 mechanisms (dispositor chains/cycles, yoga clusters)', status: 'empty_for_this_chart', sentences: [`${String(content['empty_reason'] ?? 'No bodha_mechanisms rows for this chart.')}${diagSuffix(mechanismsPayload)} [rows_len=${rows.length} total_matching=${String(content['total_matching'])}]`], fact_ids: [] }
  }
  const totalMatching = Number(content['total_matching'] ?? rows.length)
  const chainCircuitCount = Number(content['chain_circuit_count'] ?? 0)
  const top = rows.slice(0, 3).map((r) => {
    const members = Array.isArray(r['member_node_ids_array']) ? (r['member_node_ids_array'] as unknown[]).length : null
    return `${r['mechanism_name']} (${r['mechanism_class']}, ${r['valence']}${members != null ? `, ${members}-node` : ''})`
  })
  return {
    family: 'all_chart_mechanisms_and_chains',
    label: 'L2 mechanisms (dispositor chains/cycles, yoga clusters)',
    status: 'served',
    sentences: [
      `${totalMatching} named L2 mechanism(s) fire on this chart (${chainCircuitCount} chain/circuit-class — convergent dispositor chains, dispositor cycles, house-lordship cycles). Leading: ${top.join('; ')}${totalMatching > top.length ? `, +${totalMatching - top.length} more (bodha_mechanisms_get for the full set)` : ''}.`,
    ],
    fact_ids: [],
  }
}

/** full_dispositor_closure reuses the SAME mechanisms rows as all_chart_mechanisms_and_chains
 *  (chain_circuit-class rows ARE the traced dispositor closures — a convergent_dispositor_chain
 *  or dispositor_cycle IS a closure), but reports on the chain/circuit subset specifically so
 *  the two families are never byte-identical (density principle §N.6: each layer earns its own
 *  sentence over the SAME underlying data when the concepts are genuinely distinct facets of it). */
function readDispositorClosureFamily(mechanismsPayload: unknown): ReadingFamilyEntry {
  const unwrapped = unwrapCapabilityContent(mechanismsPayload)
  if (!unwrapped || typeof unwrapped !== 'object') {
    // MC-017: same verified serving gap as readMechanismsFamily above — query_mechanisms is a
    // real capability over bodha_mechanisms (also servable via bodha_mechanisms_get); a
    // failed/empty call here is not proof dispositor closures were never computed.
    return { family: 'full_dispositor_closure', label: 'Dispositor chain/cycle closure', status: 'domain_block_not_served', sentences: [`query_mechanisms call failed or returned nothing for this chart (bodha_mechanisms data may still exist — see bodha_mechanisms_get).${diagSuffix(mechanismsPayload)}`], fact_ids: [] }
  }
  const content = unwrapped as Record<string, unknown>
  const rows = Array.isArray(content['rows']) ? content['rows'] as Record<string, unknown>[] : []
  const chains = rows.filter((r) => ['convergent_dispositor_chain', 'dispositor_cycle', 'house_lordship_cycle'].includes(String(r['mechanism_class'])))
  if (chains.length === 0) {
    return { family: 'full_dispositor_closure', label: 'Dispositor chain/cycle closure', status: 'empty_for_this_chart', sentences: ['No convergent_dispositor_chain / dispositor_cycle / house_lordship_cycle mechanism fires on this chart — dispositors do not close into a traced cycle here (a genuine finding, not a serving gap).'], fact_ids: [] }
  }
  const first = chains[0]!
  const members = Array.isArray(first['member_node_ids_array']) ? (first['member_node_ids_array'] as unknown[]).length : null
  return {
    family: 'full_dispositor_closure',
    label: 'Dispositor chain/cycle closure',
    status: 'served',
    sentences: [
      `${chains.length} dispositor chain/cycle structure(s) close on this chart. Highest-ranked: "${first['mechanism_name']}" (${first['mechanism_class']}, valence ${first['valence']}${members != null ? `, traces through ${members} node(s)` : ''}) — this is the traced dispositor CLOSURE, distinct from any single planet's individual sign-lordship placement.`,
    ],
    fact_ids: [],
  }
}

function readRemediesFamily(remediesPayload: unknown): ReadingFamilyEntry {
  const unwrapped = unwrapCapabilityContent(remediesPayload)
  if (!unwrapped || typeof unwrapped !== 'object') {
    // MC-017: verified serving gap, not absence — marsys://tool/L2/query_remedies is a real,
    // wired capability over the bodha_upaya (bo_upaya) table, also independently servable via
    // bodha_remedies_get, for any chart that ran the L2 Bodha campaign. A failed/empty call
    // here means this fetch didn't reach the data, not that remedies were never computed.
    return { family: 'remedies', label: 'Remedy priority (bo_upaya)', status: 'domain_block_not_served', sentences: [`query_remedies call failed or returned nothing for this chart (bodha_upaya data may still exist — see bodha_remedies_get).${diagSuffix(remediesPayload)}`], fact_ids: [] }
  }
  const content = unwrapped as Record<string, unknown>
  const narration = content['narration'] as Record<string, unknown> | undefined
  const lead = typeof narration?.['lead'] === 'string' ? narration['lead'] as string : null
  const prescriptions = Array.isArray(content['prescriptions']) ? content['prescriptions'] as Record<string, unknown>[] : []
  if (!lead && prescriptions.length === 0) {
    return { family: 'remedies', label: 'Remedy priority (bo_upaya)', status: 'empty_for_this_chart', sentences: [`No bo_upaya resonance/prescription rows for this chart — an honest empty, not a stub.${diagSuffix(remediesPayload)}`], fact_ids: [] }
  }
  const sentences: string[] = []
  if (lead) sentences.push(lead)
  const topPrescription = prescriptions[0]
  if (topPrescription) {
    sentences.push(`Top prescription for ${String(topPrescription['target_graha'])}: ${String(topPrescription['remedy_label_human'])} (${String(topPrescription['remedy_category'])}, ${String(topPrescription['tradition'])} tradition, classical strength ${String(topPrescription['classical_strength_rating'])}).`)
  }
  return { family: 'remedies', label: 'Remedy priority (bo_upaya)', status: 'served', sentences, fact_ids: [] }
}

function readTimingWindowsFamily(activatingDasha: Record<string, unknown> | undefined): ReadingFamilyEntry {
  const activations = Array.isArray(activatingDasha?.['activations']) ? activatingDasha!['activations'] as Record<string, unknown>[] : []
  if (activations.length === 0) {
    return { family: 'timing_windows', label: 'Activating dasha timing windows', status: 'empty_for_this_chart', sentences: [String(activatingDasha?.['partial_failure'] ?? 'No activating dasha windows returned for this call\'s date range.')], fact_ids: [] }
  }
  const first = activations[0]!
  return {
    family: 'timing_windows', label: 'Activating dasha timing windows', status: 'served',
    sentences: [`${activations.length} activation window(s) in range; nearest: ${JSON.stringify(first).slice(0, 220)}.`],
    fact_ids: [],
  }
}

function readContradictionsFamily(contradictions: Record<string, unknown> | undefined): ReadingFamilyEntry {
  const items = Array.isArray(contradictions?.['items']) ? contradictions!['items'] as Record<string, unknown>[] : []
  const totalCount = Number(contradictions?.['total_count'] ?? items.length)
  if (items.length === 0) {
    return {
      family: 'contradictions_with_adjudication', label: 'Domain contradictions + adjudication', status: 'empty_for_this_chart',
      // SHABDA-SHUDDHI Lane L5 Fix 6: bodha_contradictions covers only ~3 of 13 canonical domains;
      // when items.length === 0, this is NOT a confirmed clean bill — it is a gap in adjudication
      // coverage. Replacing the false "correct negative / internally consistent" claim with an
      // honest not_adjudicated signal, following kala_lattice_query.ts:364-376 pattern.
      sentences: [totalCount === 0
        ? 'No contradictions tagged to this domain in bodha_contradictions — not_adjudicated: the contradiction corpus does not yet cover this domain, so absence of a tag is a coverage gap, not a confirmed clean reading.'
        : `${totalCount} chart-wide contradiction(s) exist but none tag this domain — not_adjudicated: domain-specific contradiction coverage may be incomplete.`],
      fact_ids: [],
    }
  }
  const first = items[0]!
  const adjudication = first['adjudication'] ?? first['resolution_hint'] ?? first['adjudication_note']
  return {
    family: 'contradictions_with_adjudication', label: 'Domain contradictions + adjudication', status: 'served',
    sentences: [`${totalCount} contradiction(s) tag this domain. Leading tension: ${String(first['tension_label'] ?? first['label'] ?? first['description'] ?? JSON.stringify(first).slice(0, 160))}${adjudication ? ` — adjudication: ${String(adjudication)}` : ' — no automated adjudication hint; needs acharya-level resolution.'}`],
    fact_ids: [],
  }
}

/** Assemble the substance-inline `reading` digest (W7.1-W7.3) for assess_wealth/career.
 *  Never throws — a family whose data source fails degrades to an honest gap entry, never a
 *  dropped family and never fabricated substance (B.10). */
export async function buildDomainReading(
  domain: string, chart_id: string, ayanamsha_id: string, data: Record<string, unknown>, principal: Principal,
): Promise<{ reading: ReadingFamilyEntry[]; families_served: number; families_total: number }> {
  const families = DOMAIN_READING_FAMILIES[domain]
  if (!families) return { reading: [], families_served: 0, families_total: 0 }

  // Bug fix (PŪRṆA-VIRĀMA close-out, live-probe-discovered): the L-DOMAIN/assess_wealth and
  // L-DOMAIN/assess_career capabilities (register_d8_assess_domain.ts) return their payload
  // wrapped as `{ content: { varga_analysis, activating_dasha, contradictions, ... } }` — the
  // same envelope assess_wealth/assess_career spread onto `response` one level up in
  // registry_bridge.ts (`{ orientation_context, orientation_ok, ...data }`, where `data` IS
  // that `{ content: {...} }` object). So on the live wire, the substance this function needs
  // lives at `data.content.varga_analysis` etc., never at `data.varga_analysis` directly — the
  // original W7 build read the wrong depth and always found `undefined`, so every family
  // degraded to `not_computed_at_l1`/`empty_for_this_chart` regardless of what was actually
  // served. `w7_substance_inline.test.ts`'s fixtures called `buildDomainReading` with a flat
  // (uncontented) `data` object, which is why the unit tests passed against this bug. Falling
  // back to `data` itself keeps those flat-fixture unit tests valid while fixing the real shape.
  const sourceData = (data['content'] as Record<string, unknown> | undefined) ?? data
  const vargaAnalysis = sourceData['varga_analysis'] as Record<string, unknown> | undefined
  const vargas = DOMAIN_READING_VARGAS[domain] ?? ['D1', 'D1']
  const houses = DOMAIN_READING_HOUSES[domain] ?? []

  const supplements = await fetchReadingSupplements(domain, chart_id, ayanamsha_id, principal)

  const byFamily = new Map<string, ReadingFamilyEntry>()
  const add = (entry: ReadingFamilyEntry): void => { byFamily.set(entry.family, entry) }

  add(readAshtakavargaFamily(vargaAnalysis, vargas))
  add(readVargaFamily(vargaAnalysis, vargas[0], domain === 'wealth' ? 'Horā — liquid wealth' : 'Dasamsa — career/status'))
  add(readVargaFamily(vargaAnalysis, vargas[1], domain === 'wealth' ? 'Rudrāṃśa — gains/income' : 'Navamsa — dharma/marriage cross-check'))
  if (domain === 'wealth') add(readInduLagnaFamily(vargaAnalysis))
  if (domain === 'career') add(readKarakamshaFamily(supplements.karakamsa))
  for (const h of houses) add(readArgalaFamily(domain, supplements.argala, h))
  add(readDispositorClosureFamily(supplements.mechanisms))
  add(readMechanismsFamily(supplements.mechanisms))
  add(readSpecialLagnaFamily(supplements.specialLagna, supplements.arudha))
  add(readCrossAyanamshaFamily(domain, supplements.crossAyanamsha))
  add(readTimingWindowsFamily(sourceData['activating_dasha'] as Record<string, unknown> | undefined))
  add(readRemediesFamily(supplements.remedies))
  add(readContradictionsFamily(sourceData['contradictions'] as Record<string, unknown> | undefined))

  // MC-017: this defensive fallback fires only if a family name in DOMAIN_READING_FAMILIES has
  // no matching `add()` call above (currently none — every wealth/career family is wired; this
  // guards future family-list drift). Labeled 'domain_block_not_served' rather than
  // 'not_computed_globally' because this branch cannot verify system-wide absence — it only
  // knows THIS reading digest has no reader wired for the family; the underlying concept may
  // well have L1/L2 data reachable via chart_facts_query/dossier. Claiming the stronger
  // 'not_computed_globally' would require confirming no raw data exists anywhere, which a
  // generic wiring-gap catch cannot do.
  const reading = families.map((f) => byFamily.get(f) ?? {
    family: f, label: titleCaseUnderscored(f), status: 'domain_block_not_served' as const,
    sentences: [`${f} has no wired data source in this build's reading digest — served as an honest gap, not fabricated (raw L1/L2 data for this concept, if any, may still be reachable via chart_facts_query/dossier).`], fact_ids: [],
  })
  const families_served = reading.filter((r) => r.status === 'served').length
  return { reading, families_served, families_total: families.length }
}

/** Attach the substance-inline reading digest to an assess_* response (W7.1-W7.3), mutating
 *  in place, and correct the gate-semantics inversion (W7.3): `domain_completeness`'s raw
 *  `synthesis_gate` describes the DOSSIER's own server-side bookkeeping (100% of the ~13,820-
 *  concept slice accounted) — it is NOT a signal that THIS response delivered that slice to
 *  the caller, and D2's diagnosis was exactly a naive consumer misreading OPEN there as
 *  absolution. This response DOES deliver the flagship family digest inline (that is what W7
 *  is), so the honest, response-scoped status is `reading_digest_status`, reported separately
 *  from the untouched full-slice bookkeeping gate (renamed `slice_accounting_gate` here so the
 *  two can never be conflated by field name alone). */
export async function attachDomainReading(
  response: Record<string, unknown>, domain: string, chart_id: string, ayanamsha_id: string, principal: Principal,
): Promise<void> {
  const { reading, families_served, families_total } = await buildDomainReading(domain, chart_id, ayanamsha_id, response, principal)
  if (families_total === 0) return
  response['reading'] = reading

  const completeness = response['domain_completeness'] as Record<string, unknown> | undefined
  if (completeness) {
    // W7.3: never let the full-slice bookkeeping gate masquerade as "this response is fully
    // hydrated" — rename it and attach the response-scoped digest status alongside it.
    if ('synthesis_gate' in completeness) {
      completeness['slice_accounting_gate'] = completeness['synthesis_gate']
      delete completeness['synthesis_gate']
    }
    completeness['reading_digest_status'] =
      `${families_served}/${families_total} families summarized inline (see \`reading\`) · ` +
      `full_hydration: available via dossier(domain="${domain}", chart_id="${chart_id}") ` +
      `(${String(completeness['slice_size'] ?? '?')} concepts).`
  }
  response['completeness_directive'] =
    `SUBSTANCE-INLINE: this response's \`reading\` field carries ${families_served}/${families_total} ` +
    `${domain} concept families as grounded sentences (fact_id-cited) — read it directly, it IS the ` +
    `opening reading, not a pointer to one. For the full ${String(completeness?.['slice_size'] ?? '')}-concept ` +
    `territory (every unit, not just the flagship families), call dossier(domain="${domain}", chart_id="${chart_id}").`
}

/**
 * R-21 fix — "receipt integrity": a served "✓" / boolean-true / string-affirmative receipt
 * mark (judgment_query's `receipt.varga_confirmed`, graha_portrait's `verdict.completeness`)
 * is computed from the CAPABILITY's own untrimmed output, before `applyMcpBudget` runs. If
 * the response-budget trimmer then floors the backing array down to kept_count 0 (the R5.1
 * C1 hard-cap PASS 2 can override every section's declared minKeep), the wire response ends
 * up with a "✓" receipt mark next to a genuinely empty array — the exact defect the register
 * names (varga_confirmed:"D10✓" next to varga_confirmation.rows:[]; completeness sections
 * marked ✓ for a section trimmed to empty).
 *
 * This reconciles AFTER trimming: for every declared `path` in the trim report whose
 * `kept_count` is 0 (fully trimmed away), downgrade the corresponding receipt key from an
 * affirmative mark to an honest `trimmed_to_empty` value naming the recover instrument —
 * never silently leave a "✓" next to zero surviving rows.
 */
function reconcileReceiptWithTrimReport(
  receipt: Record<string, unknown>,
  keyToSectionPaths: Record<string, string[]>,
  trimReport: TrimReportEntry[] | null | undefined,
): void {
  if (!trimReport || trimReport.length === 0) return
  const trimmedToZero = new Map(
    trimReport.filter(e => e.kept_count === 0).map(e => [e.path, e]),
  )
  for (const [key, paths] of Object.entries(keyToSectionPaths)) {
    const matchedEntries = paths.map(p => trimmedToZero.get(p)).filter((e): e is TrimReportEntry => Boolean(e))
    // Only downgrade when EVERY declared backing path for this key is confirmed trimmed to
    // zero (a partial trim of one of several backing arrays doesn't necessarily zero the
    // parent's pre-trim count) AND at least one such path was actually in the trim report.
    if (matchedEntries.length === 0 || matchedEntries.length !== paths.length) continue
    const prior = receipt[key]
    const isAffirmative = prior === '✓' || prior === true || (typeof prior === 'string' && prior.endsWith('✓'))
    if (!isAffirmative) continue
    const recoverInstrument = matchedEntries[0]?.recover_via.instrument ?? 'see recover_via'
    receipt[key] = `trimmed_to_empty (was "${prior}" pre-trim; 0 rows survived response-budget ` +
      `trimming — recover full detail via ${recoverInstrument})`
  }
}

// WP-S4-fix2 (Gate Ś #10 — receipt-honesty violation): `reconcileReceiptWithTrimReport` above
// only downgrades a receipt key when the response-budget trimmer's own trim_report confirms a
// backing path was cut to zero. That leaves a gap: a section can be genuinely empty (never had
// data, not a trim casualty — e.g. the `kala_activations` timing hook when nothing forward-dated
// exists) and the trim_report has no entry for it at all, so `reconcileReceiptWithTrimReport`
// silently skips it and an affirmative pre-trim `timing_anchored: true` (stamped honestly at
// write time against DIFFERENT backing data, e.g. real chart_dashas mahadasha windows) ships
// unreconciled against a served payload whose timing_hooks arrays are ALL empty. This is the
// exact "✓-with-empty-evidence" class the density-principle doctrine (CLAUDE.md §N.6 point 3)
// and B.10 forbid. Fix: after applyMcpBudget, definitively re-derive `timing_anchored` from what
// SURVIVED onto the wire — never from the pre-trim intent — and force it false (with a flag) if
// every constituent timing array is empty in the actually-served content, regardless of why.
function enforceTimingAnchoredHonesty(
  receipt: Record<string, unknown>,
  servedContent: Record<string, unknown> | undefined,
  judgmentFlags: JudgmentFlagEntry[],
): void {
  const timing = (servedContent?.['checklist'] as Record<string, unknown> | undefined)
    ?.['timing_hooks'] as Record<string, unknown> | undefined
  const current = timing?.['current']
  const hasCurrent = Array.isArray(current) && current.length > 0
  const windowsByGraha = timing?.['mahadasha_windows_by_graha'] as Record<string, unknown> | undefined
  const hasWindows = windowsByGraha
    ? Object.values(windowsByGraha).some(w => Array.isArray(w) && w.length > 0)
    : false
  const activations = timing?.['kala_activations']
  const hasActivations = Array.isArray(activations) && activations.length > 0
  const servedTimingAnchored = hasCurrent || hasWindows || hasActivations

  const priorAffirmative = receipt['timing_anchored'] === true ||
    (typeof receipt['timing_anchored'] === 'string' && receipt['timing_anchored'] !== 'false')
  if (!servedTimingAnchored && priorAffirmative) {
    receipt['timing_anchored'] = false
    judgmentFlags.push(judgmentFlag(
      'timing_anchored_forced_false',
      'the served timing_hooks (current/mahadasha_windows_by_graha/' +
      'kala_activations) are all empty on the wire — receipt.timing_anchored downgraded from an ' +
      'affirmative pre-trim/pre-serve value rather than shipping a "✓-with-empty-evidence" receipt ' +
      '(Gate Ś #10; CLAUDE.md §N.6 point 3 / B.10).',
    ))
  }
}

// PARIŚODHANA Phase B1 fix (CR-2/CR-63/R-38 — receipt-honesty violation, live-confirmed
// 2026-07-27 on chart 482012f1-710e-4a25-994a-93821f5871aa across wealth/career/marriage):
// `enforceTimingAnchoredHonesty` above closes the gap for `timing_anchored` — but its
// SIBLING receipt field, `varga_confirmed`, has no equivalent guard. `reconcileReceiptWithTrimReport`
// (the R-21 fix) only downgrades `varga_confirmed` when the FINAL `budgeted.trim_report`
// still names `content.checklist.varga_confirmation.rows` with `kept_count: 0` — but
// `finalizeMcpBudget`'s own post-attachment degrade step (response_budget.ts's
// "re-measure the WHOLE object" pass) can collapse the ENTIRE trim_report array down to a
// single one-line `(trim_report)` summary entry when attaching the full report would
// reopen the byte-budget gap. That is exactly what happens on every judgment_query call at
// its default 12KB ceiling (confirmed live: trim_report collapses from 8 real entries to 1
// summary entry) — erasing the per-path record `reconcileReceiptWithTrimReport` depends on
// to catch this case. The result: a `varga_confirmed:"D2✓"` / `"D10✓"` / `"D9✓"` receipt
// mark survives unreconciled next to a genuinely-empty served `checklist.varga_confirmation.rows`,
// reproducing on every domain regardless of dignity strength (CR-2/CR-63/R-38). Fix:
// re-derive `varga_confirmed` from what actually SURVIVED onto the wire — never from the
// trim_report's own (possibly-collapsed) bookkeeping — same discipline as
// enforceTimingAnchoredHonesty, so it is immune to whatever caused the emptiness (real
// budget trim, trim_report collapse, or rows that were already empty pre-trim).
function enforceVargaConfirmedHonesty(
  receipt: Record<string, unknown>,
  servedContent: Record<string, unknown> | undefined,
  judgmentFlags: JudgmentFlagEntry[],
): void {
  const checklist = servedContent?.['checklist'] as Record<string, unknown> | undefined
  const vargaConfirmation = checklist?.['varga_confirmation'] as Record<string, unknown> | undefined
  const rows = vargaConfirmation?.['rows']
  const servedVargaConfirmed = Array.isArray(rows) && rows.length > 0

  const priorMark = receipt['varga_confirmed']
  const priorAffirmative = priorMark === true ||
    (typeof priorMark === 'string' && priorMark.includes('✓'))
  if (!servedVargaConfirmed && priorAffirmative) {
    const varga = typeof vargaConfirmation?.['varga'] === 'string' ? vargaConfirmation['varga'] as string : null
    receipt['varga_confirmed'] = false
    judgmentFlags.push(judgmentFlag(
      'varga_confirmed_forced_false',
      'the served checklist.varga_confirmation.rows are empty on the wire' +
      (varga ? ` (operative varga ${varga})` : '') + ' — receipt.varga_confirmed downgraded from ' +
      `"${String(priorMark)}" rather than shipping a "✓-with-empty-evidence" receipt ` +
      '(CR-2/CR-63/R-38; CLAUDE.md §N.6 point 3 / B.10).',
    ))
  }
}

// ── Dual output helper ────────────────────────────────────────────────────────

// S3 fix (R5 W0a perf lane, design §21 serialization tax — measured 2.4x):
// above this size, skip the redundant text-duplicate serialization. Below it,
// dual output is still built but WITHOUT pretty-printing (indent:2 was a
// measured 20-30% byte inflation for zero client benefit — structuredContent
// already carries the full typed payload).
const DUAL_OUTPUT_TEXT_THRESHOLD_BYTES = 50_000

/**
 * Build MCP tool response with both structuredContent and text fallback.
 * Provider-spec obligation: dual output per MCP spec.
 *
 * R5 W0a punch-list (P3 fix class): dropped the `null, 2` pretty-print indent —
 * pure serialization padding, no information content.
 * S3 (R5 W0a perf lane): compact JSON.stringify, not indent:2; above the size
 * threshold the text fallback is replaced with a pointer to structuredContent
 * instead of re-serializing the full payload a second time on the wire. See
 * JL-003 for the 50KB threshold ruling.
 */
function dualOutput(data: unknown): {
  structuredContent?: { type: 'object'; object: unknown }
  content: Array<{ type: 'text'; text: string }>
} {
  const structuredContent = { type: 'object' as const, object: data }
  const json = JSON.stringify(data)
  if (Buffer.byteLength(json, 'utf8') > DUAL_OUTPUT_TEXT_THRESHOLD_BYTES) {
    return {
      structuredContent,
      content: [{
        type: 'text' as const,
        text: '[large payload — see structuredContent; text duplicate suppressed per S3 serialization-tax fix]',
      }],
    }
  }
  return {
    structuredContent,
    content: [{ type: 'text' as const, text: json }],
  }
}

/**
 * R5.1 C1 fix (live-verifier finding #3): `dualOutput`'s 50KB text-duplication threshold
 * (S3/JL-003) means every judgment_query/graha_portrait/pact_query response under 50KB —
 * i.e. EVERY one of them, since they're now budget-capped at 8-12KB — still got the FULL
 * structuredContent duplicated again as `content[0].text`, roughly DOUBLING real wire
 * bytes (confirmed live: 22,841 + 22,814 ≈ 47,789 bytes for one judgment_query call).
 *
 * The brief's size ceilings ("≤12KB judgment/portrait, ≤8KB pact") are read as what an
 * MCP client actually receives on the wire, not just the structuredContent's own byte
 * count — so for these three budget-governed tools specifically, the text duplicate is
 * ALWAYS suppressed in favor of the same short structuredContent-pointer message
 * `dualOutput` already uses above its general 50KB threshold. This does NOT touch
 * `dualOutput`/`DUAL_OUTPUT_TEXT_THRESHOLD_BYTES` itself — every other MCP tool in this
 * file keeps the general S3 threshold/behavior unchanged; this is a narrower, explicit
 * choice for the three tools whose whole point this phase is to keep small.
 */
function dualOutputBudgeted(data: unknown): {
  structuredContent?: { type: 'object'; object: unknown }
  content: Array<{ type: 'text'; text: string }>
} {
  return {
    structuredContent: { type: 'object' as const, object: data },
    content: [{
      type: 'text' as const,
      text: '[budget-capped response — see structuredContent; text duplicate suppressed for this instrument per R5.1 C1]',
    }],
  }
}

// ── Error output ──────────────────────────────────────────────────────────────

// ── R-5 fix: typed error envelope, never leak raw SQL/driver detail ──────────
//
// Denial ≠ empty ≠ internal error (register R-5): a caught error's `String(err)` may be a
// deliberately-authored, safe validation/denial message ("chart_id is required",
// "ENTITLEMENT_DENIED: ...") OR a raw driver/SQL error ('column "salience_score" does not
// exist', a stack frame, a connection string). The former is safe to echo verbatim; the
// latter must NEVER reach the client — it leaks internal schema/implementation detail and
// gives callers no stable, typed thing to branch on. classifyErrorMessage() distinguishes
// the three classes; errorOutput() logs the raw detail server-side only when it collapses
// an internal-looking message to the generic safe one.
type McpErrorClass = 'validation' | 'permission_denied' | 'internal_error'

function classifyErrorMessage(message: string): { error_class: McpErrorClass; safe_message: string } {
  if (/ENTITLEMENT_DENIED|AUTHZ_DENIED|lacks .* access/i.test(message)) {
    return { error_class: 'permission_denied', safe_message: message }
  }
  if (/ is required($|[^a-zA-Z])|^either `|^Unknown facet|^Unsupported /i.test(message)) {
    return { error_class: 'validation', safe_message: message }
  }
  const looksInternal =
    /column ".*" does not exist|relation ".*" does not exist|syntax error at or near|ECONNREFUSED|invalid input syntax|PostgresError|\bat \S+\.(ts|js):\d+|\.node_modules[\\/]/i.test(message)
  if (looksInternal) {
    return {
      error_class: 'internal_error',
      safe_message: 'An internal error occurred while serving this request. The specific ' +
        'cause has been logged server-side and is not exposed to the client (never leak raw ' +
        'SQL/driver detail — R-5).',
    }
  }
  return { error_class: 'internal_error', safe_message: message }
}

function errorOutput(tool: string, message: string, extra?: Record<string, unknown>) {
  const { error_class, safe_message } = classifyErrorMessage(message)
  if (error_class === 'internal_error' && safe_message !== message) {
    console.error(`[${tool}] internal_error (raw, server-only, never sent to client): ${message}`)
  }
  const data = { ok: false, error: { class: error_class, message: safe_message }, tool, ...extra }
  return { ...dualOutput(data), isError: true as const }
}

// ── Registry capability caller ────────────────────────────────────────────────

/**
 * Call a registry capability via the platform's /api/retrieval/capability endpoint.
 *
 * The MCP server is a separate Node package (platform-mcp) and cannot import
 * the Next.js platform's TypeScript modules directly. Instead, it calls the
 * platform's HTTP API, which holds the live registry and DB connection.
 *
 * Endpoint: POST /api/retrieval/capability
 * Body: { uri, args }
 * Response: { ok: boolean, content: unknown, error?: string }
 */
async function callRegistryCapability(
  uri: string,
  args: Record<string, unknown>,
  _chartId: string | undefined,   // chart_id is already in args; kept for call-site clarity
  principal: Principal,
): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(20_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    // R5.2 A3 (battery X-2 finding): the previous generic message embedded the raw HTTP
    // status code as literal text ("capability call failed (401): ...") — the battery's own
    // "no_raw_401_403_text" assertion correctly flags that as a leak of transport-layer
    // detail into the MCP-facing error text. describeProxyFailure already produces the
    // clean, denial-specific message for the entitlement case (and a generic-but-status-
    // code-free message otherwise) — callPlatformPrimitive already used it; this call site
    // never did. Same fix, same file, finally applied uniformly.
    throw new Error(describeProxyFailure(uri, res.status, text))
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) {
    throw new Error(`[registry_bridge] capability error: ${data.error ?? 'unknown'}`)
  }
  return data.content
}

// ── chart_header resolution (W3-L1, GT-47 / W-9 — fail-loud, not silent-null) ────────
//
// W3-L1 honesty flag emitted whenever chart_header resolution fails or comes back
// error-shaped. Stable string, mirrors platform/src/lib/retrieval/chart_header.ts's
// CHART_HEADER_UNRESOLVED_FLAG (this process cannot import that file directly — see
// envelope.ts's PROCESS-BOUNDARY NOTE — so the flag string is independently declared
// here, kept byte-identical). The forthcoming flags-closed-enum migration (W3-L2)
// folds this string into its enum verbatim.
export const CHART_HEADER_UNRESOLVED_FLAG = 'chart_header_unresolved'

/**
 * Resolve the chart_header block for a v3 envelope, honestly.
 *
 * Fixes TWO distinct failure modes that both used to go silent:
 *   1. The `marsys://tool/L1/get_chart_header` capability call itself throwing
 *      (network error, entitlement denial, etc.) — every call site previously caught
 *      this and set `chart_header = null` with no signal.
 *   2. `callRegistryCapability` returning the capability's raw ToolResult
 *      (`{ content: ChartHeader, is_error: boolean }`) UNCAST — every call site was
 *      assigning that whole wrapper object to `chart_header` via `as ChartHeader`
 *      instead of unwrapping `.content` (the same unwrap `get_signals`/`get_domain_reading`
 *      already do via `wrapper['content']`). Live-verified: a real v3 `get_chart_orientation`
 *      call was serving `chart_header: { content: {...the real header...}, is_error: false }`
 *      — every consumer reading `chart_header.lagna_sign` etc. got `undefined` even though
 *      the header had resolved successfully underneath the wrapper.
 * Both failure modes now return the SAME honest shape: `chart_header: null` PLUS the
 * `chart_header_unresolved` flag, so a caller can never mistake "unresolved" for
 * "genuinely has no data" (never a silent null — B.10-adjacent).
 */
export async function resolveChartHeader(
  chart_id: string,
  ayanamsha_id: string | undefined,
  principal: Principal,
): Promise<{ chart_header: ChartHeader | null; flags: string[] }> {
  try {
    const raw = await callRegistryCapability(
      'marsys://tool/L1/get_chart_header', { chart_id, ayanamsha_id }, chart_id, principal,
    ) as Record<string, unknown> | null
    const isError = Boolean(raw?.['is_error'])
    const inner = (raw?.['content'] as ChartHeader | null | undefined) ?? null
    // The L1 capability (get_chart_header.ts) surfaces a DB-level resolution failure via
    // `metadata.flags` even when `is_error` stays false (the header remains best-effort
    // content) — propagate that flag rather than treating a nulled-fields header as silently
    // fine.
    const metadataFlags = (raw?.['metadata'] as Record<string, unknown> | undefined)?.['flags']
    const upstreamFlags = Array.isArray(metadataFlags)
      ? metadataFlags.filter((f): f is string => typeof f === 'string')
      : []
    if (isError || !inner) {
      return { chart_header: null, flags: [CHART_HEADER_UNRESOLVED_FLAG] }
    }
    return { chart_header: inner, flags: upstreamFlags }
  } catch {
    return { chart_header: null, flags: [CHART_HEADER_UNRESOLVED_FLAG] }
  }
}

// ── B.11 orient-before-domain enforcement ─────────────────────────────────────

/**
 * B.11 Whole-Chart-Read Protocol (PROJECT_ARCHITECTURE §H.4):
 * Every domain-specific query must be preceded by an orientation digest
 * from the L2 UCD (query_ucd / get_chart_orientation). In the MCP channel,
 * which is stateless per-request and has no shared session state, we enforce
 * this STRUCTURALLY: each non-floor domain tool handler fetches the UCD
 * before doing its domain work and includes the result as `orientation_context`
 * in the output. This means orient-before-domain is guaranteed by construction —
 * the tool itself ensures orientation has happened, not a soft prompt convention.
 *
 * Floor tools (get_chart_orientation itself, get_classical_citation, list_assets)
 * are exempt — they ARE the floor or are chart-agnostic.
 *
 * If the UCD call fails (e.g. no bodha data yet), we return a graceful-empty
 * stub so the domain tool can still serve — a failed orientation is non-blocking
 * but annotated in the response.
 */
// SAMAPANA Track B item 1: pure helper so the 'exhaustive'-forces-full-digest decision is
// unit-testable without mocking network I/O (see samapana_trackb_exhaustive.test.ts). Every
// verbosity OTHER than 'exhaustive' (including 'concise'/'detailed'/undefined) keeps today's
// exact digest shape — top_k_signals:10, response_format:'digest' — byte-for-byte unchanged.
export function resolveOrientationFetchParams(
  verbosity: Verbosity | undefined,
): { top_k_signals: number; response_format: 'digest' | 'full' } {
  if (verbosity === 'exhaustive') return { top_k_signals: 100, response_format: 'full' }
  return { top_k_signals: 10, response_format: 'digest' }
}

/**
 * SAMĀPTI A7-N8-AUDIT F-22 — the B.11 enforcement signal, made into a real assertion.
 *
 * BEFORE: `orientation_ok` was set to the literal `true` on the sole basis that the
 * `query_ucd` call did not THROW. Three independent ways that produced a false green:
 *
 *   1. `query_ucd`'s own handler (`platform/src/lib/retrieval/registry/layers/L2_bodha/
 *      query_ucd.ts`) catches every error it raises and RETURNS `{ content: { error },
 *      is_error: true }` — it does not throw. So the ordinary DB-failure path never
 *      reached the `catch` below, and an error payload read `orientation_ok: true`.
 *   2. An unbuilt / partially-built chart returns HTTP 200 with `digest` empty,
 *      `entity_profiles: []` and `convergence_domains: []` — no holistic context at all —
 *      and still read `orientation_ok: true`.
 *   3. Nothing checked that the payload was even ABOUT the requested chart.
 *
 * AFTER: `orientation_ok` asserts what its name claims — that holistic context is actually
 * present for THIS chart. The repair pattern is `resolveChartHeader` in this same file
 * (unwrap, check `is_error`, check the inner payload, emit an honest flag), applied to the
 * signal B.11 rests on. Never blocking: a failed/hollow orientation still serves the domain
 * tool, and the payload is passed through untouched (B.10 — nothing is dropped); only the
 * boolean tells the truth, plus an added `b11_note` naming the reason.
 *
 * Note on the substance test: this call site requests `response_format: 'digest'`, which
 * returns `top_signals: []` BY DESIGN, so an empty `top_signals` is never on its own
 * evidence of a hollow orientation. Substance is therefore read from the surfaces `digest`
 * actually populates — `entity_profiles`, `convergence_domains`, and the digest counts.
 */
export interface OrientationAssessment {
  ok: boolean
  /** `null` iff ok; otherwise names exactly what failed. Never a silent false. */
  reason: string | null
}

export function assessOrientationPayload(payload: unknown, chart_id: string): OrientationAssessment {
  if (payload == null || typeof payload !== 'object') {
    return { ok: false, reason: 'UCD orientation returned no payload object.' }
  }
  const wrapper = payload as Record<string, unknown>

  // query_ucd returns its errors in-band as { content: { error }, is_error: true } — it
  // does not throw — so this, not the try/catch, is the branch that actually fires.
  if (wrapper['is_error'] === true) {
    const innerErr = (wrapper['content'] as Record<string, unknown> | undefined)?.['error']
    return { ok: false, reason: `UCD orientation returned an error payload: ${String(innerErr ?? 'unspecified')}` }
  }

  // `callRegistryCapability` returns the DOUBLE-WRAPPED capability shape
  // (`{ content, is_error }`) — see the EL-36 note at the top of this file and the
  // identical `content ?? wrapper` unwrap `get_domain_reading` already performs. The
  // fallback to `wrapper` covers a already-unwrapped payload rather than mis-grading it.
  const inner = (wrapper['content'] as Record<string, unknown> | undefined) ?? wrapper
  if (inner == null || typeof inner !== 'object') {
    return { ok: false, reason: 'UCD orientation payload carried no content block.' }
  }
  if (inner['error'] != null) {
    return { ok: false, reason: `UCD orientation content reported an error: ${String(inner['error'])}` }
  }

  // Identity: the orientation must be about the chart we asked about. (The platform side
  // enforces the same invariant via `orientationEchoMatches`; this process cannot import
  // that module across the package boundary — see envelope.ts's PROCESS-BOUNDARY NOTE — so
  // the check is independently restated here rather than assumed.)
  const echoed = inner['chart_id']
  if (typeof echoed === 'string' && echoed !== chart_id) {
    return { ok: false, reason: `UCD orientation echoed chart_id ${echoed}, not the requested ${chart_id}.` }
  }

  // Substance: is there any holistic context in here at all?
  const entityProfiles = inner['entity_profiles']
  const convergence   = inner['convergence_domains']
  const digest        = (inner['digest'] as Record<string, unknown> | undefined) ?? {}
  const msrCount      = Number(digest['msr_signal_count'] ?? 0)
  const hasSubstance =
    (Array.isArray(entityProfiles) && entityProfiles.length > 0) ||
    (Array.isArray(convergence) && convergence.length > 0) ||
    (Number.isFinite(msrCount) && msrCount > 0)

  if (!hasSubstance) {
    return {
      ok: false,
      reason:
        'UCD orientation is empty for this chart — no entity_profiles, no convergence_domains, ' +
        'and msr_signal_count is 0/absent. The chart is unbuilt or only partially built at L2, ' +
        'so the B.11 whole-chart-read floor was NOT actually satisfied by this call.',
    }
  }

  return { ok: true, reason: null }
}

async function fetchOrientationContext(
  chart_id: string,
  ayanamsha_id: string | undefined,
  principal: Principal,
  verbosity?: Verbosity,
): Promise<{ orientation_context: unknown; orientation_ok: boolean }> {
  try {
    const { top_k_signals, response_format } = resolveOrientationFetchParams(verbosity)
    const ucdData = await callRegistryCapability(
      'marsys://tool/L2/query_ucd',
      { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), top_k_signals, response_format },
      chart_id, principal,
    )
    // F-22: the boolean now reflects an assessment of the payload, not merely the absence
    // of a thrown exception.
    const assessment = assessOrientationPayload(ucdData, chart_id)
    if (assessment.ok) return { orientation_context: ucdData, orientation_ok: true }
    // Non-blocking and non-destructive: the real payload is preserved verbatim alongside
    // an honest note, so nothing is dropped (B.10) and no caller can read the hollow case
    // as a satisfied B.11 floor.
    return {
      orientation_context: {
        ...(ucdData as Record<string, unknown>),
        b11_note: `UCD orientation did not establish holistic context. ${assessment.reason}`,
      },
      orientation_ok: false,
    }
  } catch (err) {
    // Non-blocking: domain tool still runs; orientation failure is annotated
    return {
      orientation_context: {
        b11_note: 'UCD orientation pre-fetch failed (graceful-empty). Domain tool executed without holistic context.',
        error: String(err),
      },
      orientation_ok: false,
    }
  }
}

// ── Tool registrations ────────────────────────────────────────────────────────

/**
 * Register all D7 consolidated MCP tools on the server.
 *
 * All per_chart tools: chart_id is REQUIRED — no default fallback.
 * chart_agnostic_gate RULE-1: per_chart scope → chart_id in required_inputs.
 *
 * B.11 enforcement: all per_chart domain tools call fetchOrientationContext()
 * before executing their domain query. The UCD result is included in the
 * response as `orientation_context` so the LLM always has holistic context.
 */
export function registerRegistryBridgeTools(server: McpServer, principal: Principal): void {

  // ── get_chart_orientation (L-ORIENT umbrella — synthesis_query, design §5 #7) ──
  // marsys://tool/L2/query_ucd
  server.tool(
    'get_chart_orientation',
    'Mandatory first call for any chart reading. Retrieves the L2 Bodha synthesis layer\'s Unified Chart Digest (UCD) — the holistic portrait of the chart distilled from 573 MSR signals, the CDLM domain activation grid, the CGM causal graph, and the Life Event Log. In classical Jyotish, an acharya reads the whole chart before any domain. This tool enforces that discipline: it surfaces the Lagna lord condition, Moon nakshatra character, dominant cross-domain themes, and active contradictions. entity_profiles (design §E-6) are hierarchically-aggregated composite-ranked signal groups — one row per graha, not twenty atomic signals — computed by the SAME ranking pipeline get_signals uses. Call this before get_domain_reading, get_signals, or any other per-chart tool — the B.11 Whole-Chart-Read Protocol requires it. envelope_format=\'v3\' (opt-in; default \'legacy\') returns the R5 unified envelope alongside the existing response_format verbosity control.',
    {
      chart_id: z.string().uuid().describe(
        'UUID of the chart to read. Required — no default chart.'
      ),
      ayanamsha_id: z.string().optional().describe(
        "Ayanamsha for signals (default: 'LAHIRI')"
      ),
      top_k_signals: z.number().int().min(1).max(100).optional().describe(
        'Number of top MSR signals to return (default: 20)'
      ),
      top_k_entities: z.number().int().min(1).max(30).optional().describe(
        'Number of hierarchically-aggregated entity profiles to return (default: 10).'
      ),
      response_format: z.enum(['full', 'summary', 'digest']).optional().describe(
        'Output verbosity: full (all fields), summary (key fields), digest (counts + entity_profiles only, no atomic signals). Default: summary.'
      ),
      envelope_format: z.enum(['legacy', 'v3']).optional()
        .describe("Envelope shape: 'legacy' (default, unchanged) or 'v3' (populated verdict/grounding/ranking_basis/drill_pointers/chart_header — opt-in until the R5 W4 battery flips the default). Distinct from response_format, which governs digest verbosity."),
      reading_depth: READING_DEPTH_ZOD,
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, top_k_signals, top_k_entities, response_format, envelope_format, reading_depth, budget_kb }) => {
      if (!chart_id) return errorOutput('get_chart_orientation', 'chart_id is required')
      try {
        // SAMAPANA Track B item 3: a deep dive can never be silently routed through the
        // lossy 'summary'/'digest' projections (today's real lossy forms on this tool) —
        // refuse the self-contradictory combination rather than silently picking a side.
        guardDeepDiveNotLossy(reading_depth, 'response_format', response_format, ['summary', 'digest'])
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        // SAMAPANA Track B item 4b (footgun fix, contract-side): reading_depth:'deep_dive'
        // forces the full digest even if the caller never touches response_format at all —
        // the deep-dive contract's mandatory first call always gets the full signal set, not
        // the default top-10 'summary'. Back-compat: reading_depth omitted/'standard' leaves
        // this branch untouched — `fmt` resolves exactly as it did before this change.
        const fmt = response_format ?? (reading_depth === 'deep_dive' ? 'full' : 'summary')
        const format = resolveEnvelopeFormat(envelope_format)
        const raw = await callRegistryCapability(
          'marsys://tool/L2/query_ucd',
          { chart_id, ayanamsha_id: resolvedAyanamsha,
            top_k_signals: top_k_signals ?? (reading_depth === 'deep_dive' ? 100 : 20),
            top_k_entities: top_k_entities ?? 10, response_format: fmt },
          chart_id, principal
        )
        // R5 W1 fix: callRegistryCapability returns the capability handler's raw return
        // value ({ content, is_error }) — this call site was reading fields directly off
        // that wrapper (responseData['chart_id'] etc), which are actually one level
        // deeper under `.content`, and always resolved to undefined. Unwrap here (matches
        // get_domain_reading's established pattern) before any field access.
        const wrapper = raw as Record<string, unknown>
        const responseData = (wrapper['content'] as Record<string, unknown>) ?? wrapper

        // F-026: response_format bounding is now genuinely applied server-side
        // (query_ucd.ts) too; this MCP-layer bounding remains as defense-in-depth /
        // backward-compat for callers relying on the exact prior shape.
        let bounded: Record<string, unknown>
        if (fmt === 'digest') {
          bounded = {
            chart_id: responseData['chart_id'],
            ayanamsha_id: responseData['ayanamsha_id'],
            digest: responseData['digest'],
            entity_profiles: responseData['entity_profiles'],
            convergence_domains: responseData['convergence_domains'],
            provenance: responseData['provenance'],
            response_format: 'digest',
          }
        } else if (fmt === 'summary') {
          const signals = (responseData['top_signals'] as unknown[]) ?? []
          bounded = { ...responseData, top_signals: signals.slice(0, 10), response_format: 'summary' }
        } else {
          const signals = (responseData['top_signals'] as unknown[]) ?? []
          bounded = { ...responseData, top_signals: signals.slice(0, 100), response_format: 'full' }
        }

        if (format !== 'v3') {
          return dualOutputBudgeted(applyMcpBudgetAuto(envelope(bounded, 'get_chart_orientation') as unknown as Record<string, unknown>, resolveMaxKb('get_chart_orientation', budget_kb), 'get_chart_orientation', budget_kb))
        }

        // ── v3 population (design §10/§E-6) ──────────────────────────────────
        const entityProfiles = (responseData['entity_profiles'] as Record<string, unknown>[]) ?? []
        const rankingBasis = (responseData['ranking_basis'] as Record<string, unknown> | null) ?? null
        const digestBlock = (responseData['digest'] as Record<string, unknown>) ?? {}

        const verdict = {
          entity_profile_count: entityProfiles.length,
          msr_signal_count: digestBlock['msr_signal_count'] ?? null,
          contradiction_count: digestBlock['contradiction_count'] ?? null,
          weakest_graha: digestBlock['weakest_graha'] ?? null,
          top_priority_class: digestBlock['top_priority_class'] ?? null,
          note: 'entity_profile_count/msr_signal_count are chart-wide aggregates already computed by this response — not recomputed here.',
        }

        const citations = Array.from(new Set(
          ((responseData['top_signals'] as Record<string, unknown>[]) ?? [])
            .map(s => s['citation_human']).filter((v): v is string => typeof v === 'string' && v.length > 0)
        ))
        // WP-1.2(a) (LCA-14, §N.5): populate envelope grounding.fact_ids from the
        // resolvable L1 fact_ids the query_ucd handler already surfaced (content.grounding
        // + entity_profiles[].fact_ids). These are the exact ids verified present in
        // chart_facts by the handler — never fabricated (B.10). Falls back to the union of
        // entity_profiles[].fact_ids when a handler predates the grounding block.
        const handlerGrounding = responseData['grounding'] as Record<string, unknown> | undefined
        const groundingFactIds = new Set<string>()
        const handlerFactIds = handlerGrounding?.['fact_ids']
        if (Array.isArray(handlerFactIds)) {
          for (const fid of handlerFactIds) if (typeof fid === 'string' && fid) groundingFactIds.add(fid)
        }
        if (groundingFactIds.size === 0) {
          for (const p of entityProfiles) {
            const pf = (p as Record<string, unknown>)['fact_ids']
            if (Array.isArray(pf)) for (const fid of pf) if (typeof fid === 'string' && fid) groundingFactIds.add(fid)
          }
        }
        const grounding = { fact_ids: Array.from(groundingFactIds), citations, grounding_score: null }

        const judgment_flags: JudgmentFlagEntry[] = []
        if (entityProfiles.length === 0) judgment_flags.push(judgmentFlag('zero_entity_profiles'))

        // Typed per design §28.4 (R5 W3 Phase B) — additive `pointer_type` alongside the
        // pre-existing {instrument, hint} shape. Neither pointer here is a named classical
        // move (this is the domain-agnostic orient surface, not a bhava-judgment recipe),
        // so both are honestly 'other' rather than force-fit into the classical vocabulary.
        const drill_pointers: { instrument: string; hint: string; pointer_type: DrillPointerType }[] = [
          { instrument: 'bodha_signals_get', hint: 'atomic composite-ranked signal drill for any entity_profiles.top_signal_ids.', pointer_type: 'other' },
          { instrument: 'bodha_domain_reading_get', hint: 'domain-conditioned reading for a specific life domain.', pointer_type: 'other' },
        ]

        const { chart_header, flags: chartHeaderFlags } = await resolveChartHeader(chart_id, resolvedAyanamsha, principal)
        judgment_flags.push(...chartHeaderFlags)

        // D5 coverage receipt: digest.msr_signal_count is a chart-wide aggregate already
        // computed by vw_chart_digest (query_ucd.ts) — no extra query needed. `served` is
        // the atomic top_signals count actually returned in THIS response after the
        // response_format bound (digest=0, summary<=10, full<=100).
        const servedTopSignals = (bounded['top_signals'] as unknown[] | undefined)?.length ?? 0
        const msrSignalCountRaw = digestBlock['msr_signal_count']
        const coverage: CoverageStamp = {
          family: 'msr_signals',
          served: servedTopSignals,
          total: typeof msrSignalCountRaw === 'number' ? msrSignalCountRaw
            : (typeof msrSignalCountRaw === 'string' && msrSignalCountRaw !== '' ? Number(msrSignalCountRaw) : null),
        }

        return dualOutputBudgeted(applyMcpBudgetAuto(
          envelope(bounded, 'get_chart_orientation', undefined, 'v3',
            { chart_header, verdict, ranking_basis: rankingBasis, grounding, drill_pointers, judgment_flags, coverage }) as unknown as Record<string, unknown>,
          resolveMaxKb('get_chart_orientation', budget_kb), 'get_chart_orientation', budget_kb,
        ))
      } catch (err) {
        return errorOutput('get_chart_orientation', String(err), { chart_id })
      }
    }
  )

  // ── get_domain_reading (L-DOMAIN drill) ──────────────────────────────────
  // marsys://tool/L2/query_domain_reading
  server.tool(
    'get_domain_reading',
    'Retrieves the L2 Bodha domain activation reading for a specific life domain (career, relationship, health, wealth, spirituality, character). In Jyotish, each domain (bhava) is governed by a karaka planet and a set of signifying houses — career by the 10th lord and its dispositor chain; relationship by the 7th lord and Venus; health by the Lagna lord and the 6th/8th. This tool surfaces which MSR signals are active in the named domain, ranked by computed_salience, with their constituent L1 facts and classical derivation chain. Always returns an orientation_context from the L2 UCD as the holistic frame (B.11 by construction).',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      domain: z.string().describe(
        'Life domain to drill: career, relationship, character, spirituality, wealth, health, or other domain name.'
      ),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      cursor: z.string().optional().describe('Pagination cursor (from previous response.next_cursor)'),
      max_lenses: z.number().int().min(1).max(12).optional().describe(
        'Max question lenses to return (default: 3 for token safety; pass 12 for full payload).'
      ),
      max_signals_per_lens: z.number().int().min(1).max(100).optional().describe(
        'Max signals per lens (default: 20).'
      ),
      max_signal_refs: z.number().int().min(1).max(2000).optional().describe(
        'Max signal IDs in signal_id_refs (default 200; capped at 2000).'
      ),
      response_format: z.enum(['default', 'full']).optional().describe(
        "Payload verbosity. 'default': token-safe (shared_signal_ids_array omitted, signal_id_refs ≤200). 'full': includes arrays (signal_id_refs ≤2000)."
      ),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, domain, ayanamsha_id, cursor, max_lenses, max_signals_per_lens, max_signal_refs, response_format, budget_kb }) => {
      if (!chart_id) return errorOutput('get_domain_reading', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before domain drill.
        // S1 fix (R5 W0a perf lane): orientation fetch and the domain query are
        // independent HTTP calls (both hit the platform API) — parallelize
        // rather than serially awaiting each (measured ~458ms/call added by
        // the serial UCD pre-fetch; this is the biggest median win in §21).
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal),
          callRegistryCapability(
            'marsys://tool/L2/query_domain_reading',
            { chart_id, domain, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), cursor,
              ...(response_format ? { response_format } : {}),
              ...(max_signal_refs != null ? { max_signal_refs } : {}) },
            chart_id, principal
          ),
        ])
        // F-021R: Bound the response — default 3 lenses × 20 signals (was 17MB / 90k signal objects)
        // callRegistryCapability returns data.content from the HTTP response, where
        // the handler itself wraps in { content: {...}, is_error: false }. So the
        // actual payload is one level deeper: data → { content: { question_lenses } }.
        const domainWrapper = data as Record<string, unknown>
        const inner = (domainWrapper['content'] as Record<string, unknown>) ?? domainWrapper
        const lenses = (inner['question_lenses'] as unknown[]) ?? []
        const maxLenses = max_lenses ?? 3
        const maxSig = max_signals_per_lens ?? 20
        const lensesToBound = lenses.slice(0, maxLenses)
        const boundedLenses = lensesToBound.map((lens) => {
          const l = lens as Record<string, unknown>
          // all_relevant_ranked_jsonb is stored as { total_count, ranked_signals: [...] }
          // (a JSONB object, not a flat array). Slice ranked_signals and preserve total_count.
          const arj = l['all_relevant_ranked_jsonb']
          let boundedArj: unknown
          let totalSignals = 0
          if (arj && typeof arj === 'object' && !Array.isArray(arj)) {
            const arjObj = arj as Record<string, unknown>
            const ranked = Array.isArray(arjObj['ranked_signals'])
              ? (arjObj['ranked_signals'] as unknown[])
              : []
            totalSignals = ranked.length
            boundedArj = { ...arjObj, ranked_signals: ranked.slice(0, maxSig), total_count: ranked.length }
          } else if (Array.isArray(arj)) {
            // Flat array fallback (schema v1 compat)
            totalSignals = (arj as unknown[]).length
            boundedArj = (arj as unknown[]).slice(0, maxSig)
          } else {
            boundedArj = arj
          }
          // F-023: template_element_ids_jsonb may contain duplicate refs — dedup
          const templateIds = Array.isArray(l['template_element_ids_jsonb'])
            ? (l['template_element_ids_jsonb'] as string[])
            : []
          const uniqueTemplateIds = [...new Set(templateIds)]
          return {
            ...l,
            all_relevant_ranked_jsonb: boundedArj,
            all_relevant_total: totalSignals,
            template_element_ids_jsonb: uniqueTemplateIds,
          }
        })
        return dualOutputBudgeted(applyMcpBudgetAuto({
          orientation_context,
          orientation_ok,
          ...inner,
          question_lenses: boundedLenses,
          lenses_total: lenses.length,
          lenses_returned: boundedLenses.length,
          token_safety_note: `Bounded to ${maxLenses} lenses × ${maxSig} signals. Pass max_lenses=12 + max_signals_per_lens=100 for full payload.`,
        }, resolveMaxKb('get_domain_reading', budget_kb), 'get_domain_reading', budget_kb))
      } catch (err) {
        return errorOutput('get_domain_reading', String(err), { chart_id, domain })
      }
    }
  )

  // ── get_signals (L-SIGNAL ranked signals — signals_query, design §5 #5) ──
  // marsys://tool/L2/query_signals
  server.tool(
    'get_signals',
    'Retrieves ranked MSR (Multi-Signal Repository) signals for a chart — the 573-signal corpus of astrological patterns derived from L1 Gaṇita facts. Each signal encodes a classical Jyotish observation (yoga, placement, aspect, nakshatra condition) with its constituent L1 fact_ids, a computed_salience score reflecting how prominently it operates in this chart, and the domain tags it activates. Use min_salience to focus on high-confidence signals (≥0.7 = strong; ≥0.5 = moderate). The signal layer is the analytical backbone: get_domain_reading and get_chart_orientation both synthesize from this corpus. Query directly when you need raw signal evidence for a specific claim. response_format=\'v3\' (opt-in; default \'legacy\') returns the R5 unified envelope: populated verdict (signal counts + composite-ranking mode), grounding (signal_id/citation coverage in this page), ranking_basis (the actual composite-4D scoring basis when domain was specified), drill_pointers (get_chart_orientation for the entity-level digest, traverse_graph for causal context), judgment_flags, and chart_header.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      domain: z.string().optional().describe('Filter by domain (e.g. career, health)'),
      min_salience: z.number().min(0).max(1).optional().describe(
        'Minimum computed_salience threshold (0–1). Ranked by computed_salience DESC — NOT signature_tier.'
      ),
      limit: z.number().int().min(1).max(200).optional().describe('Max signals (default: 50)'),
      // R5 W1 fix: this facet was declared but silently ignored — the call below forwarded
      // it as `limit`, but query_signals.ts's handler only reads `top_k`/`offset` (design
      // §18's "diverging param names" premise finding: top_k vs limit). cursor is now
      // translated to a numeric offset instead of being dropped on the floor (E-5).
      cursor: z.string().optional().describe('Pagination cursor — a stringified offset (e.g. "50"). Use next_cursor from a prior response.'),
      lel_enabled: z.boolean().optional().describe(
        'Include lel_origin=true signals (Life Event Log calibration). Default: false.'
      ),
      response_format: z.enum(['legacy', 'v3']).optional()
        .describe("Envelope shape: 'legacy' (default, unchanged) or 'v3' (populated verdict/grounding/ranking_basis/drill_pointers/chart_header — opt-in until the R5 W4 battery flips the default)."),
      frame: z.enum(['lagna', 'chandra', 'surya', 'arudha', 'karakamsha']).optional().describe(
        "R5 W2: annotates a frame_context (each graha's house counted from this reference sign) alongside the unchanged, unfiltered signal rows. Default: lagna."
      ),
      paradigm: z.enum(['parashari', 'jaimini', 'kp', 'tajika']).optional().describe(
        'R5 W2: filters to one signal_tradition. Default: unfiltered (every tradition, each individually tagged) — required for whole-chart-read (B.11) discipline.'
      ),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, domain, min_salience, limit, cursor, lel_enabled, response_format, frame, paradigm, budget_kb }) => {
      if (!chart_id) return errorOutput('get_signals', 'chart_id is required')
      try {
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        const format = resolveEnvelopeFormat(response_format)
        const resolvedLimit = limit ?? 50
        const resolvedOffset = cursor && /^\d+$/.test(cursor) ? Number(cursor) : 0

        // B.11: fetch holistic orientation before signal drill (S1: parallelized)
        const [{ orientation_context, orientation_ok }, raw] = await Promise.all([
          fetchOrientationContext(chart_id, resolvedAyanamsha, principal),
          callRegistryCapability(
            'marsys://tool/L2/query_signals',
            { chart_id, ayanamsha_id: resolvedAyanamsha, domain, min_salience,
              top_k: resolvedLimit, offset: resolvedOffset, lel_enabled: lel_enabled ?? false,
              frame, paradigm },
            chart_id, principal
          ),
        ])
        // callRegistryCapability returns the capability handler's raw return value
        // ({ content, is_error }) — unwrap `.content` for the real payload (matches
        // get_domain_reading's unwrap pattern; get_signals previously skipped this step).
        const wrapper = raw as Record<string, unknown>
        const inner = (wrapper['content'] as Record<string, unknown>) ?? wrapper

        if (format !== 'v3') {
          return dualOutputBudgeted(applyMcpBudgetAuto({
            orientation_context, orientation_ok,
            ...envelope(inner, 'get_signals', { offset: resolvedOffset, limit: resolvedLimit, total: null }),
          }, resolveMaxKb('get_signals', budget_kb), 'get_signals', budget_kb))
        }

        // ── v3 population (design §10/§E-6) ──────────────────────────────────
        const signals = (inner['signals'] as Record<string, unknown>[]) ?? []
        const returned_count = Number(inner['returned_count'] ?? signals.length)
        const truncated = Boolean(inner['truncated'])
        // D5 coverage receipt: query_signals.ts now computes a genuine COUNT(*) against the
        // SAME base filters (domain/source_subsystem/signal_type_class/paradigm/min_salience/
        // lel_enabled) this page was drawn from — never a guess.
        const totalMatchingFilters = typeof inner['total_matching_filters'] === 'number'
          ? (inner['total_matching_filters'] as number)
          : null

        const fact_ids = Array.from(new Set(
          signals.flatMap(s => ((s['constituent_facts_array'] as string[] | null) ?? []))
        )).filter(Boolean)
        const citations = Array.from(new Set(
          signals.map(s => s['citation_human']).filter((v): v is string => typeof v === 'string' && v.length > 0)
        ))
        const verifiedCount = signals.filter(s => {
          const st = s['verification_pass_status']
          return st === 'two_pass_verified' || st === 'pass'
        }).length
        const grounding = {
          fact_ids, citations,
          grounding_score: signals.length > 0 ? Math.round((verifiedCount / signals.length) * 1000) / 1000 : null,
        }

        const rankingBasis = (inner['ranking_basis'] as Record<string, unknown> | null) ?? null
        const verdict = {
          returned_count,
          truncated,
          domain: domain ?? null,
          ranking_mode: rankingBasis?.['mode'] ?? 'salience_fallback',
          note: 'Counts are of SIGNALS SERVED IN THIS PAGE only — pass a higher limit/cursor for more.',
        }

        const judgment_flags: JudgmentFlagEntry[] = []
        if (returned_count === 0) judgment_flags.push(judgmentFlag('zero_rows_returned'))
        if (truncated) judgment_flags.push(judgmentFlag('response_size_truncated'))

        // Typed per design §28.4 (R5 W3 Phase B) — additive; see get_chart_orientation's
        // sibling comment above for why the orient-view pointer is 'other'. The graph
        // traversal pointer genuinely IS a dispositor/causal-chain move.
        const drill_pointers: { instrument: string; hint: string; pointer_type: DrillPointerType }[] = [
          { instrument: 'bodha_chart_digest_get', hint: 'entity_profiles for the hierarchically-aggregated, same-pipeline orient view (design §E-6).', pointer_type: 'other' },
          { instrument: 'bodha_graph_subgraph_get', hint: 'traverse causal context from these signal_ids.', pointer_type: 'dispositor_chain' },
        ]

        const { chart_header, flags: chartHeaderFlags } = await resolveChartHeader(chart_id, resolvedAyanamsha, principal)
        judgment_flags.push(...chartHeaderFlags)

        const filterLabel = [
          domain ? `domain=${domain}` : null,
          paradigm ? `paradigm=${paradigm}` : null,
        ].filter(Boolean).join(',')
        const coverage: CoverageStamp = {
          family: `msr_signals${filterLabel ? `[${filterLabel}]` : ''}`,
          served: signals.length,
          total: totalMatchingFilters,
        }

        return dualOutputBudgeted(applyMcpBudgetAuto({
          orientation_context, orientation_ok,
          ...envelope(inner, 'get_signals', { offset: resolvedOffset, limit: resolvedLimit, total: totalMatchingFilters },
            'v3', { chart_header, verdict, ranking_basis: rankingBasis, grounding, drill_pointers, judgment_flags, coverage }),
        }, resolveMaxKb('get_signals', budget_kb), 'get_signals', budget_kb))
      } catch (err) {
        return errorOutput('get_signals', String(err), { chart_id })
      }
    }
  )

  // ── traverse_graph (CGM graph traversal) ─────────────────────────────────
  // marsys://tool/L2/traverse_chart_graph
  server.tool(
    'traverse_graph',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      seed_signal_ids: z.array(z.string()).min(1).optional().describe(
        'Seed signal UUIDs to start traversal from (use signal_id values from get_signals). ' +
        'Alternative to about/about_from/about_to for address-seeded traversal (R5 W2).'
      ),
      mode: z.enum(['neighbors', 'paths', 'cluster']).optional().describe(
        'Traversal mode: neighbors (adjacent nodes), paths (shortest paths between seeds), cluster (community). Default: neighbors.'
      ),
      depth: z.number().int().min(1).max(3).optional().describe('Traversal depth (default: 2, max: 3)'),
      about: z.union([z.string(), z.record(z.string(), z.unknown())]).optional().describe(
        'R5 W2: address expression (AddressExpression object or DSL string, e.g. "lord_of(bhava 10)") ' +
        'seeding neighbors mode — resolved via the shared address resolver.'
      ),
      about_from: z.union([z.string(), z.record(z.string(), z.unknown())]).optional().describe(
        'R5 W2: address expression for the paths-mode start node, e.g. "lord_of(bhava 10)".'
      ),
      about_to: z.union([z.string(), z.record(z.string(), z.unknown())]).optional().describe(
        'R5 W2: address expression for the paths-mode end node, e.g. {type:"graha", graha:"Moon"}.'
      ),
      direction: z.enum(['directed', 'both']).optional().describe(
        'R5 W2: directed follows real from_node_id→to_node_id edges only; both treats edges as undirected. Default: both.'
      ),
      min_strength: z.number().min(0).max(1).optional().describe(
        'R5 W2: filter traversal/edges to computed_strength >= this floor.'
      ),
      verbosity: VERBOSITY_ZOD,
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, seed_signal_ids, mode, depth, about, about_from, about_to, direction, min_strength, verbosity, budget_kb }) => {
      if (!chart_id) return errorOutput('traverse_graph', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before graph traversal (S1: parallelized)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, undefined, principal, verbosity),
          callRegistryCapability(
            'marsys://tool/L2/traverse_chart_graph',
            {
              chart_id,
              seed_signal_ids,
              mode: mode ?? 'neighbors',
              depth: depth ?? 2,
              about,
              about_from,
              about_to,
              direction,
              min_strength,
            },
            chart_id, principal
          ),
        ])
        // D-1.6 S-5 (R-1/R-8/CR-49 residual): live probe measured 99KB at depth=1 default,
        // well over the 64KB Gate Ś ceiling — this response was never budget-wrapped. Same
        // applyMcpBudgetAuto + dualOutputBudgeted mechanism already used for assess_*/
        // judgment_query (response_budget.ts) — generic array-section auto-detection plus
        // the self-verifying finalizeMcpBudget re-measure and string-truncation fallback.
        const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
        return dualOutputBudgeted(applyMcpBudgetAuto(response, resolveMaxKb('traverse_graph', budget_kb, verbosity), 'traverse_graph', budget_kb))
      } catch (err) {
        return errorOutput('traverse_graph', String(err), { chart_id })
      }
    }
  )

  // ── get_positions (L1 Gaṇita graha positions) ────────────────────────────
  // marsys://tool/L1/get_positions
  server.tool(
    'get_positions',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      planet: z.string().optional().describe('Optional: filter by planet name (e.g. Sun, Moon, Mars)'),
      frame: z.enum(['lagna', 'chandra', 'surya', 'arudha', 'karakamsha']).optional().describe(
        "R5 W2: re-bases house_d1 onto this reference sign (adds house_from_frame per row). Default: lagna."
      ),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, planet, frame, budget_kb }) => {
      if (!chart_id) return errorOutput('get_positions', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L1/get_positions',
          { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), planet, frame },
          chart_id, principal
        )
        return dualOutputBudgeted(applyMcpBudgetAuto(data as Record<string, unknown>, resolveMaxKb('get_positions', budget_kb), 'get_positions', budget_kb))
      } catch (err) {
        return errorOutput('get_positions', String(err), { chart_id })
      }
    }
  )

  // ── get_dashas (L1 Vimshottari dasha chain) ──────────────────────────────
  // marsys://tool/L1/get_dashas
  server.tool(
    'get_dashas',
    'Retrieves the dasha (planetary period) chain from L1 Gaṇita. Default system: VIMSHOTTARI — the 120-year Parashara sequence (Sun 6 yr, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19, Mercury 17, Ketu 7, Venus 20), subdivided into antardasha and pratyantardasha. Other systems available: YOGINI, ASHTOTTARI, CHARA, NARAYANA, SHOOLA, KALACHAKRA. The running period lord colors all life events during its tenure: its natal placement, lordship, aspects received, and conjunctions determine what it delivers. Use this to identify which lords are active now and in the near future, then cross-reference with get_temporal_windows and get_signals to see which yogas those lords activate. Pass date_from=birth_date to exclude pre-birth rows (the dasha running at birth may have started before the birth date).',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      system_id: z.string().optional().describe(
        "Dasha system to retrieve (default: 'VIMSHOTTARI'). Options: VIMSHOTTARI | YOGINI | ASHTOTTARI | CHARA | NARAYANA | SHOOLA | KALACHAKRA."
      ),
      date_from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe(
        "ISO date YYYY-MM-DD. Filters to dashas whose end_date >= this date, excluding rows that ended before this point. Pass the chart's birth date (e.g. '1984-02-05') to exclude pre-birth rows."
      ),
      limit: z.number().int().min(1).max(200).optional().describe('Max dasha rows (default: 50)'),
      cursor: z.string().optional().describe('Pagination cursor'),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, system_id, date_from, limit, cursor, budget_kb }) => {
      if (!chart_id) return errorOutput('get_dashas', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L1/get_dashas',
          {
            chart_id,
            ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
            dasha_system: system_id ?? 'VIMSHOTTARI',
            ...(date_from ? { date_from } : {}),
            limit: limit ?? 50,
            cursor,
          },
          chart_id, principal
        )
        return dualOutputBudgeted(applyMcpBudgetAuto(data as Record<string, unknown>, resolveMaxKb('get_dashas', budget_kb), 'get_dashas', budget_kb))
      } catch (err) {
        return errorOutput('get_dashas', String(err), { chart_id })
      }
    }
  )

  // ── get_temporal_windows (L3 temporal activation + convergence) ──────────
  // marsys://tool/L3/query_temporal_activation + query_convergence_windows
  server.tool(
    'get_temporal_windows',
    'Retrieves the L3 Kāla temporal activation layer for a date range — identifying which Jyotish periods (Vimshottari dasha, antardasha, pratyantardasha) are running, which MSR signals are activated by those period lords, and where convergence windows occur (multiple activation streams peaking simultaneously). In classical Jyotish, timing is the hardest discipline: a powerful yoga (structural combination) only gives its results when its constituent lords run their period. This tool applies that temporal gate — distinguishing signals that are structurally present from those that are temporally ripe. Returns orientation_context (B.11) alongside temporal data.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      date_from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe('Start date YYYY-MM-DD'),
      date_to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe('End date YYYY-MM-DD'),
      as_of: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe(
        'Point-in-time date YYYY-MM-DD — returns only windows active AS OF this date; overrides date_from/date_to.'
      ),
      include_convergence: z.boolean().optional().describe('Include convergence windows (default: true)'),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, date_from, date_to, as_of, include_convergence, budget_kb }) => {
      if (!chart_id) return errorOutput('get_temporal_windows', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before temporal domain query (S1: parallelized)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal),
          callRegistryCapability(
            'marsys://tool/L3/query_temporal_activation',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), date_from, date_to, ...(as_of ? { as_of } : {}), include_convergence: include_convergence ?? true },
            chart_id, principal
          ),
        ])
        return dualOutputBudgeted(applyMcpBudgetAuto({ orientation_context, orientation_ok, ...data as Record<string, unknown> }, resolveMaxKb('get_temporal_windows', budget_kb), 'get_temporal_windows', budget_kb))
      } catch (err) {
        return errorOutput('get_temporal_windows', String(err), { chart_id })
      }
    }
  )

  // ── get_projections (L3 probabilistic projections) ───────────────────────
  // marsys://tool/L3/query_projections
  server.tool(
    'get_projections',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      domain: z.string().optional().describe('Domain to project (e.g. career, relationship)'),
      horizon_years: z.number().int().min(1).max(20).optional().describe('Projection horizon in years (default: 5)'),
      max_projections: z.number().int().min(1).max(200).optional().describe(
        'Max projections to return (default: 20; was unbounded at 117KB+).'
      ),
      verbosity: VERBOSITY_ZOD,
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, domain, horizon_years, max_projections, verbosity, budget_kb }) => {
      if (!chart_id) return errorOutput('get_projections', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before predictive projection (S1: parallelized)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal, verbosity),
          callRegistryCapability(
            'marsys://tool/L3/query_projections',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), domain, horizon_years: horizon_years ?? 5 },
            chart_id, principal
          ),
        ])
        // F-008: Cap projections array — was 117KB unbounded
        const projData = data as Record<string, unknown>
        const projections = (projData['projections'] as unknown[]) ?? []
        const cap = max_projections ?? 20
        const boundedProjections = projections.slice(0, cap)
        // D-1.6 S-5 (R-1/R-8/CR-49 residual): live probe measured 70KB even with the
        // `projections` array already capped by max_projections — other fields in the
        // response (e.g. per-projection detail objects, nested breakdowns) still pushed it
        // over the 64KB Gate Ś ceiling. Wrap the whole assembled response through the same
        // budget mechanism as traverse_graph/assess_* rather than relying solely on the
        // hand-rolled projections cap above.
        const response = {
          orientation_context,
          orientation_ok,
          ...projData,
          projections: boundedProjections,
          projections_total: projections.length,
          projections_returned: boundedProjections.length,
        }
        return dualOutputBudgeted(applyMcpBudgetAuto(response, resolveMaxKb('get_projections', budget_kb, verbosity), 'get_projections', budget_kb))
      } catch (err) {
        return errorOutput('get_projections', String(err), { chart_id })
      }
    }
  )

  // ── get_classical_citation (L0 classical text retrieval) ─────────────────
  // marsys://tool/L0/query_classical_texts
  // Global scope — no chart_id required
  server.tool(
    'get_classical_citation',
    {
      query: z.string().describe('Topic or verse to search for in classical Jyotish texts.'),
      text_ids: z.array(z.string()).optional().describe('Optional: limit to specific text IDs'),
      limit: z.number().int().min(1).max(20).optional().describe('Max results (default: 5)'),
      cursor: z.string().optional().describe('Pagination cursor'),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ query, text_ids, limit, cursor, budget_kb }) => {
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L0/query_classical_texts',
          { query, text_ids, limit: limit ?? 5, cursor }, undefined, principal,
        )
        return dualOutputBudgeted(applyMcpBudgetAuto(data as Record<string, unknown>, resolveMaxKb('get_classical_citation', budget_kb), 'get_classical_citation', budget_kb))
      } catch (err) {
        return errorOutput('get_classical_citation', String(err))
      }
    }
  )

  // ── get_remedies (L2 remedy prescriptions) ───────────────────────────────
  // marsys://tool/L2/query_remedies
  server.tool(
    'get_remedies',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      domain: z.string().optional().describe('Filter remedies by life domain'),
      remedy_type: z.string().optional().describe('Filter by type: mantra, gemstone, ritual, upaya'),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, domain, remedy_type, budget_kb }) => {
      if (!chart_id) return errorOutput('get_remedies', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before remedy prescription (S1: parallelized)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, undefined, principal),
          callRegistryCapability(
            'marsys://tool/L2/query_remedies',
            { chart_id, domain, remedy_type },
            chart_id, principal
          ),
        ])
        return dualOutputBudgeted(applyMcpBudgetAuto({ orientation_context, orientation_ok, ...data as Record<string, unknown> }, resolveMaxKb('get_remedies', budget_kb), 'get_remedies', budget_kb))
      } catch (err) {
        return errorOutput('get_remedies', String(err), { chart_id })
      }
    }
  )

  // ── get_chart_quality (calibration + trust) ───────────────────────────────
  // marsys://tool/L2/query_quality_scorecard
  server.tool(
    'get_chart_quality',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, budget_kb }) => {
      if (!chart_id) return errorOutput('get_chart_quality', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before quality/calibration surface (S1: parallelized)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, undefined, principal),
          callRegistryCapability(
            'marsys://tool/L2/query_quality_scorecard',
            { chart_id },
            chart_id, principal
          ),
        ])
        return dualOutputBudgeted(applyMcpBudgetAuto({ orientation_context, orientation_ok, ...data as Record<string, unknown> }, resolveMaxKb('get_chart_quality', budget_kb), 'get_chart_quality', budget_kb))
      } catch (err) {
        return errorOutput('get_chart_quality', String(err), { chart_id })
      }
    }
  )

  // ── list_assets (asset catalog) ───────────────────────────────────────────
  // marsys://resource/asset-registry/all
  // Global scope — no chart_id required
  // W5 L8 ("listCapabilities filters" / W-13): added asset_type/catalog_status/scope/
  // is_active/has_writer filters, forwarded to the same asset_registry_all.ts handler
  // that already implements them (AND-combined; all optional, backward compatible).
  server.tool(
    'list_assets',
    {
      layer: z.string().optional().describe('Filter by layer: L0, L1, L2, L3, L4, L5'),
      asset_type: z.enum(['data', 'service']).optional().describe('Filter by asset_type: data or service'),
      catalog_status: z.enum(['CURRENT', 'DRAFT']).optional().describe('Filter by catalog_status: CURRENT or DRAFT'),
      scope: z.enum(['global', 'per_chart']).optional().describe('Filter by scope: global or per_chart'),
      is_active: z.boolean().optional().describe('Filter to active (true) or inactive (false) assets'),
      has_writer: z.boolean().optional().describe('Filter to assets with (true) or without (false) a registered writer'),
      limit: z.number().int().min(1).max(200).optional().describe('Max assets (default: 81)'),
      cursor: z.string().optional().describe('Pagination cursor'),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ layer, asset_type, catalog_status, scope, is_active, has_writer, limit, cursor, budget_kb }) => {
      try {
        // list_assets → platform cockpit registry (direct HTTP; no @/ import possible)
        const data = await callRegistryCapability(
          'marsys://resource/asset-registry/all',
          { layer, asset_type, catalog_status, scope, is_active, has_writer, limit: limit ?? 81, cursor }, undefined, principal
        )
        return dualOutputBudgeted(applyMcpBudgetAuto({ ...(data as Record<string, unknown>), pagination: { cursor, limit } }, resolveMaxKb('list_assets', budget_kb), 'list_assets', budget_kb))
      } catch (err) {
        return errorOutput('list_assets', String(err))
      }
    }
  )

  // ── tool_search (W5 Lane L4 — "tool-search metadata") ────────────────────
  // marsys://tool/L0/tool_search — global scope, no chart_id required.
  // Keyword search over the FULL ~120-capability catalog (name/description/
  // layer/domain-tag/keyword match), so a caller can discover a capability by
  // describing what it needs instead of already knowing the exact tool name.
  // See platform/src/lib/retrieval/registry/tool_search.ts for the shared
  // derivation this delegates to (same function backs the generated
  // tool_search_index.generated.json census artifact — zero drift).
  server.tool(
    'tool_search',
    'Keyword search over the full MARSYS tool/resource/prompt catalog (~120 capabilities ' +
      'across L0-L5). Returns matching tool names, descriptions, and layer/domain tags — NOT ' +
      'the full catalog. Use this before assuming a needed capability does not exist, or when ' +
      'the exact tool name is unknown (e.g. query="dasha activation", "muhurta", "yoga ' +
      'firings", "remedies"). Case-insensitive keyword/substring match — not fuzzy or semantic ' +
      'search; a query with no overlap returns an honest empty result, never a fabricated guess.',
    {
      query: z.string().describe('Keyword(s) describing the capability you need (e.g. "dasha", "muhurta timing", "remedy for saturn").'),
      limit: z.number().int().min(1).max(100).optional().describe('Max matching tools to return (default 20, max 100).'),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ query, limit, budget_kb }) => {
      if (!query || !query.trim()) return errorOutput('tool_search', 'query is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L0/tool_search', { query, limit }, undefined, principal
        )
        return dualOutputBudgeted(applyMcpBudgetAuto(data as Record<string, unknown>, resolveMaxKb('tool_search', budget_kb), 'tool_search', budget_kb))
      } catch (err) {
        return errorOutput('tool_search', String(err), { query })
      }
    }
  )

  /**
   * A-09 (F-56/F-111): Sāra composition for assess_* tools. Replaces the object-blind
   * applyMcpBudgetAuto path. verdict_skeleton (~43KB) and activating_dasha (~62KB) are
   * OBJECTS invisible to autoDetectTrimmableSections — they now land in the evidence layer
   * and are cleanly excluded when budget is tight rather than silently surviving trim passes.
   */
  function buildAssessResponse(
    response: Record<string, unknown>,
    toolName: keyof typeof MCP_RESPONSE_BUDGET_KB,
    budget_kb: number | undefined,
    effectiveVerbosity: Verbosity | undefined,
  ) {
    const effectiveBudgetKb = resolveMaxKb(toolName, budget_kb, effectiveVerbosity)

    const kernel: SaraKernel = {
      verdict: (response['verdict'] as string) ?? '',
      flags: (response['judgment_flags'] as JudgmentFlagEntry[]) ?? [],
      promise: null,
      pointers: [
        { instrument: 'get_domain_reading', hint: 'marsys://tool/L2/get_domain_reading' } as DrillPointerLike,
        { instrument: 'query_temporal_activation', hint: 'marsys://tool/L3/query_temporal_activation' } as DrillPointerLike,
        { instrument: 'query_contradictions', hint: 'marsys://tool/L2/query_contradictions' } as DrillPointerLike,
      ],
    }

    // Grounding: essential structured context with bounded arrays.
    // Excludes verdict_skeleton and activating_dasha — the two large objects (F-56/F-111)
    // that were invisible to the auto-trimmer.
    const grounding: Record<string, unknown> = {
      orientation_context: response['orientation_context'],
      orientation_ok: response['orientation_ok'],
      domain: response['domain'],
      chart_id: response['chart_id'],
      ayanamsha_id: response['ayanamsha_id'],
      reading_checklist: response['reading_checklist'],
      step_results: response['step_results'],
      gochara_sweep: response['gochara_sweep'],
      contradictions: response['contradictions'],
      house_analysis: response['house_analysis'],
      citations: response['citations'],
      provenance: response['provenance'],
      yoga_fact_ids: response['yoga_fact_ids'],
    }
    // assess_career/wealth: reading + completeness injected by attachDomainReading/Completeness
    if (response['reading'] !== undefined) grounding['reading'] = response['reading']
    if (response['completeness'] !== undefined) grounding['completeness'] = response['completeness']
    // assess_wealth: leverage_index injected by attachLeverageIndex
    if (response['leverage_index'] !== undefined) grounding['leverage_index'] = response['leverage_index']

    // Evidence: the two large objects (F-56/F-111) + remaining heavy data.
    // Excluded at the 40KB configured budget; available for deep_dive/exhaustive.
    const evidence = {
      verdict_skeleton: response['verdict_skeleton'],
      activating_dasha: response['activating_dasha'],
      karaka_analysis: response['karaka_analysis'],
      varga_analysis: response['varga_analysis'],
      sensitive_degree_firings: response['sensitive_degree_firings'],
      kp_cusp_chain: response['kp_cusp_chain'],
      ranking_basis: response['ranking_basis'],
    }

    const counts: Record<string, number> = {
      contradictions: Array.isArray(response['contradictions'])
        ? (response['contradictions'] as unknown[]).length : 0,
      yoga_fact_ids: Array.isArray(response['yoga_fact_ids'])
        ? (response['yoga_fact_ids'] as unknown[]).length : 0,
      reading_families: Array.isArray(response['reading'])
        ? (response['reading'] as unknown[]).length : 0,
    }

    return assembleSaraContent({ kernel, grounding, evidence, budget_kb: effectiveBudgetKb, counts })
  }

  // ── D8 APEX TOOLS ─────────────────────────────────────────────────────────
  // assess_marriage / assess_career / assess_health / assess_wealth
  // yoga_activation_by_dasha
  // get_cgm_subgraph / query_chart_facts / vector_search

  // ── assess_marriage (D8 L-DOMAIN reconciled bundle) ──────────────────────
  server.tool(
    'assess_marriage',
    'Reconciled marriage/relationship assessment for a chart. Orchestrates the 7th lord + Venus kāraka + D9 + bhāvat-bhāva analysis across the Bodha synthesis layer (L2), Kāla temporal activation (L3), and the contradiction surface. Returns convergences, tensions, activating dasha window, and classical citations for the relationship domain. judgment_flags marks inferences requiring acharya validation. chart_id is required — never defaulted. (Canonical assessment tool — the former apex_marriage_assess alias was retired per WP-1.3(i)/LCA-11; its tuning params are folded in below.)',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      max_signals_per_lens: z.number().int().min(1).max(50).optional().describe('Max ranked signals per question lens (default 10, max 50). Drill via get_domain_reading for full lists.'),
      max_contradictions: z.number().int().min(1).max(100).optional().describe('Max contradictions in the bundle (default 15, max 100). Remainder via query_contradictions.'),
      verbosity: VERBOSITY_ZOD,
      reading_depth: READING_DEPTH_ZOD,
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, max_signals_per_lens, max_contradictions, verbosity, reading_depth, budget_kb }) => {
      if (!chart_id) return errorOutput('assess_marriage', 'chart_id is required')
      try {
        // SAMAPANA Track B item 2: reading_depth:'deep_dive' deterministically forces the
        // effective verbosity to 'exhaustive' — never silently downgraded by a stray verbosity
        // also present on this call.
        const effectiveVerbosity = resolveEffectiveVerbosity(verbosity, reading_depth)
        // S1 fix: orientation + domain assessment parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal, effectiveVerbosity),
          callRegistryCapability(
            'marsys://tool/L-DOMAIN/assess_marriage',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
              ...(max_signals_per_lens != null ? { max_signals_per_lens } : {}),
              ...(max_contradictions != null ? { max_contradictions } : {}) },
            chart_id, principal
          ),
        ])
        const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
        return dualOutputBudgeted(buildAssessResponse(response, 'assess_marriage', budget_kb, effectiveVerbosity))
      } catch (err) {
        return errorOutput('assess_marriage', String(err), { chart_id })
      }
    }
  )

  // ── assess_career (D8 L-DOMAIN reconciled bundle) ────────────────────────
  server.tool(
    'assess_career',
    'Reconciled career/vocation assessment for a chart. Orchestrates the 10th lord + Saturn kāraka + D10 + yoga detection + activating dasha window. Calls Bodha domain reading (L2), Kāla temporal activation (L3), and the contradiction surface. Returns convergences, tensions, and judgment_flags for inferences requiring acharya validation. chart_id is required — never defaulted. (Canonical assessment tool — the former apex_career_assess alias was retired per WP-1.3(i)/LCA-11; its tuning params are folded in below.)',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      max_signals_per_lens: z.number().int().min(1).max(50).optional().describe('Max ranked signals per question lens (default 10, max 50). Drill via get_domain_reading for full lists.'),
      max_contradictions: z.number().int().min(1).max(100).optional().describe('Max contradictions in the bundle (default 15, max 100). Remainder via query_contradictions.'),
      verbosity: VERBOSITY_ZOD,
      reading_depth: READING_DEPTH_ZOD,
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, max_signals_per_lens, max_contradictions, verbosity, reading_depth, budget_kb }) => {
      if (!chart_id) return errorOutput('assess_career', 'chart_id is required')
      try {
        // SAMAPANA Track B item 2: reading_depth:'deep_dive' deterministically forces the
        // effective verbosity to 'exhaustive' — never silently downgraded by a stray verbosity
        // also present on this call.
        const effectiveVerbosity = resolveEffectiveVerbosity(verbosity, reading_depth)
        // S1 fix: orientation + domain assessment parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal, effectiveVerbosity),
          callRegistryCapability(
            'marsys://tool/L-DOMAIN/assess_career',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
              ...(max_signals_per_lens != null ? { max_signals_per_lens } : {}),
              ...(max_contradictions != null ? { max_contradictions } : {}) },
            chart_id, principal
          ),
        ])
        const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
        // Elevation α: back the naive-caller entrypoint with dossier's 100%-accounted territory.
        attachDomainCompleteness(response, 'career', chart_id)
        // SATYA-ŚEṢA W7: serve the reading itself, inline, not just a pointer to one.
        await attachDomainReading(response, 'career', chart_id, normalizeAyanamsha(ayanamsha_id), principal)
        return dualOutputBudgeted(buildAssessResponse(response, 'assess_career', budget_kb, effectiveVerbosity))
      } catch (err) {
        return errorOutput('assess_career', String(err), { chart_id })
      }
    }
  )

  // ── assess_health (D8 L-DOMAIN reconciled bundle) ────────────────────────
  server.tool(
    'assess_health',
    'Reconciled health/vitality assessment for a chart. Orchestrates the 1st + 6th + 8th lords + Sun kāraka + afflictions + D1/D6 analysis. Calls Bodha domain reading (L2), Kāla temporal activation (L3), and the contradiction surface. Returns convergences, tensions, and judgment_flags for inferences requiring acharya validation. chart_id is required — never defaulted. (Canonical assessment tool — the former apex_health_assess alias was retired per WP-1.3(i)/LCA-11; its tuning params are folded in below.)',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      max_signals_per_lens: z.number().int().min(1).max(50).optional().describe('Max ranked signals per question lens (default 10, max 50). Drill via get_domain_reading for full lists.'),
      max_contradictions: z.number().int().min(1).max(100).optional().describe('Max contradictions in the bundle (default 15, max 100). Remainder via query_contradictions.'),
      verbosity: VERBOSITY_ZOD,
      reading_depth: READING_DEPTH_ZOD,
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, max_signals_per_lens, max_contradictions, verbosity, reading_depth, budget_kb }) => {
      if (!chart_id) return errorOutput('assess_health', 'chart_id is required')
      try {
        // SAMAPANA Track B item 2: reading_depth:'deep_dive' deterministically forces the
        // effective verbosity to 'exhaustive' — never silently downgraded by a stray verbosity
        // also present on this call.
        const effectiveVerbosity = resolveEffectiveVerbosity(verbosity, reading_depth)
        // S1 fix: orientation + domain assessment parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal, effectiveVerbosity),
          callRegistryCapability(
            'marsys://tool/L-DOMAIN/assess_health',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
              ...(max_signals_per_lens != null ? { max_signals_per_lens } : {}),
              ...(max_contradictions != null ? { max_contradictions } : {}) },
            chart_id, principal
          ),
        ])
        const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
        return dualOutputBudgeted(buildAssessResponse(response, 'assess_health', budget_kb, effectiveVerbosity))
      } catch (err) {
        return errorOutput('assess_health', String(err), { chart_id })
      }
    }
  )

  // ── assess_wealth (D8 L-DOMAIN reconciled bundle) ────────────────────────
  server.tool(
    'assess_wealth',
    'Reconciled wealth/prosperity assessment for a chart. Orchestrates the 2nd + 11th lords + Jupiter kāraka + dasha activation window + classical citations. Calls Bodha domain reading (L2), Kāla temporal activation (L3), and the contradiction surface. Returns convergences, tensions, and judgment_flags for inferences requiring acharya validation. chart_id is required — never defaulted. (Canonical assessment tool — the former apex_wealth_assess alias was retired per WP-1.3(i)/LCA-11; its tuning params are folded in below.)',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      max_signals_per_lens: z.number().int().min(1).max(50).optional().describe('Max ranked signals per question lens (default 10, max 50). Drill via get_domain_reading for full lists.'),
      max_contradictions: z.number().int().min(1).max(100).optional().describe('Max contradictions in the bundle (default 15, max 100). Remainder via query_contradictions.'),
      verbosity: VERBOSITY_ZOD,
      reading_depth: READING_DEPTH_ZOD,
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, max_signals_per_lens, max_contradictions, verbosity, reading_depth, budget_kb }) => {
      if (!chart_id) return errorOutput('assess_wealth', 'chart_id is required')
      try {
        // SAMAPANA Track B item 2: reading_depth:'deep_dive' deterministically forces the
        // effective verbosity to 'exhaustive' — never silently downgraded by a stray verbosity
        // also present on this call.
        const effectiveVerbosity = resolveEffectiveVerbosity(verbosity, reading_depth)
        // S1 fix: orientation + domain assessment parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal, effectiveVerbosity),
          callRegistryCapability(
            'marsys://tool/L-DOMAIN/assess_wealth',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
              ...(max_signals_per_lens != null ? { max_signals_per_lens } : {}),
              ...(max_contradictions != null ? { max_contradictions } : {}) },
            chart_id, principal
          ),
        ])
        const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
        // Elevation α: back the naive-caller entrypoint with dossier's 100%-accounted territory.
        attachDomainCompleteness(response, 'wealth', chart_id)
        // SATYA-ŚEṢA W7: serve the reading itself, inline, not just a pointer to one.
        await attachDomainReading(response, 'wealth', chart_id, normalizeAyanamsha(ayanamsha_id), principal)
        // PARIŚODHANA R-10: join the already-computed L1 ga_vichara leverage_index family in —
        // it was fully computed (7 rows/chart) but completely absent from this response shape.
        await attachLeverageIndex(response, 'wealth', chart_id, normalizeAyanamsha(ayanamsha_id), principal)
        return dualOutputBudgeted(buildAssessResponse(response, 'assess_wealth', budget_kb, effectiveVerbosity))
      } catch (err) {
        return errorOutput('assess_wealth', String(err), { chart_id })
      }
    }
  )

  // ── yoga_activation_by_dasha (D8 L-TIMING bridge) ────────────────────────
  server.tool(
    'yoga_activation_by_dasha',
    'Bridges the L2 Bodha yoga-signal catalog and the L3 Kāla timing activation surface. Returns yoga signals (signal_type_class=yoga) active within the given dasha window, ranked by salience × dasha_alignment_score. Each result includes activation_start, activation_end, active_dasha_periods_jsonb, and constituent_fact_ids for drill-down. Use to answer "which yogas are ripening now?" chart_id is required — never defaulted.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      dasha_period: z.string().optional().describe(
        "Dasha-antardasha label to filter by (e.g. 'saturn-venus'). Case-insensitive substring match against active_dasha_periods_jsonb."
      ),
      date_from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe('Start of window (YYYY-MM-DD). Default: today.'),
      date_to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe('End of window (YYYY-MM-DD). Default: 3 years from today.'),
      top_k: z.number().int().min(1).max(200).optional().describe('Max activated yogas to return (default: 30).'),
      min_salience: z.number().min(0).max(1).optional().describe('Minimum salience threshold (0–1, default: 0).'),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, dasha_period, date_from, date_to, top_k, min_salience, budget_kb }) => {
      if (!chart_id) return errorOutput('yoga_activation_by_dasha', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L-TIMING/yoga_activation_by_dasha',
          {
            chart_id,
            ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
            ...(dasha_period ? { dasha_period } : {}),
            ...(date_from ? { date_from } : {}),
            ...(date_to ? { date_to } : {}),
            ...(top_k != null ? { top_k } : {}),
            ...(min_salience != null ? { min_salience } : {}),
          },
          chart_id, principal
        )
        return dualOutputBudgeted(applyMcpBudgetAuto(data as Record<string, unknown>, resolveMaxKb('yoga_activation_by_dasha', budget_kb), 'yoga_activation_by_dasha', budget_kb))
      } catch (err) {
        return errorOutput('yoga_activation_by_dasha', String(err), { chart_id })
      }
    }
  )

  // ── get_cgm_subgraph (CGM graph: per-chart subgraph traversal) ────────────
  // marsys://tool/L2/traverse_chart_graph
  // Apex alias: expose traverse_chart_graph as get_cgm_subgraph for D8 surface.
  server.tool(
    'get_cgm_subgraph',
    'Traverses the Causal Graph Model (CGM) for a chart — the bodha_cgm_nodes + bodha_cgm_edges graph built from L2 Bodha signals. Four modes: neighbors (BFS from seed node_ids), paths (shortest path between two nodes), convergence (top hub nodes by in-degree), contradictions (nodes with conflicting signal valence). Use to explore causal chains, find convergence hubs, or surface contradictions in the chart\'s signal graph. chart_id is required — never defaulted.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      mode: z.enum(['neighbors', 'paths', 'convergence', 'contradictions']).optional().describe(
        'Traversal mode (default: neighbors).'
      ),
      seed_node_ids: z.array(z.string().uuid()).optional().describe(
        'Seed node UUIDs (from bodha_cgm_nodes) for neighbors/paths modes.'
      ),
      depth: z.number().int().min(1).max(3).optional().describe('BFS depth for neighbors mode (1–3, default 1).'),
      seed_node: z.string().uuid().optional().describe('Source node UUID for paths mode.'),
      target_node: z.string().uuid().optional().describe('Target node UUID for paths mode.'),
      query_text: z.string().optional().describe('Semantic seed: finds top-3 similar nodes and runs BFS from them.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      about: z.union([z.string(), z.record(z.string(), z.unknown())]).optional().describe(
        'R5 W2: address expression (e.g. "lord_of(bhava 10)") seeding neighbors mode — resolved via the shared address resolver.'
      ),
      about_from: z.union([z.string(), z.record(z.string(), z.unknown())]).optional().describe(
        'R5 W2: address expression for the paths-mode start node, e.g. "lord_of(bhava 10)".'
      ),
      about_to: z.union([z.string(), z.record(z.string(), z.unknown())]).optional().describe(
        'R5 W2: address expression for the paths-mode end node, e.g. {type:"graha", graha:"Moon"}.'
      ),
      direction: z.enum(['directed', 'both']).optional().describe(
        'R5 W2: directed follows real from_node_id→to_node_id edges only; both treats edges as undirected. Default: both.'
      ),
      min_strength: z.number().min(0).max(1).optional().describe(
        'R5 W2: filter traversal/edges to computed_strength >= this floor.'
      ),
      verbosity: VERBOSITY_ZOD,
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, mode, seed_node_ids, depth, seed_node, target_node, query_text, ayanamsha_id, about, about_from, about_to, direction, min_strength, verbosity, budget_kb }) => {
      if (!chart_id) return errorOutput('get_cgm_subgraph', 'chart_id is required')
      try {
        // S1 fix: orientation + graph traversal parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal, verbosity),
          callRegistryCapability(
            'marsys://tool/L2/traverse_chart_graph',
            {
              chart_id,
              ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
              mode: mode ?? 'neighbors',
              ...(seed_node_ids ? { seed_node_ids } : {}),
              ...(depth != null ? { depth } : {}),
              ...(seed_node ? { seed_node } : {}),
              ...(target_node ? { target_node } : {}),
              ...(query_text ? { query_text } : {}),
              ...(about ? { about } : {}),
              ...(about_from ? { about_from } : {}),
              ...(about_to ? { about_to } : {}),
              ...(direction ? { direction } : {}),
              ...(min_strength != null ? { min_strength } : {}),
            },
            chart_id, principal
          ),
        ])
        // D-1.6 S-5 (R-1/R-8/CR-49 residual): live probe measured 99.7KB default page — over
        // the 64KB Gate Ś ceiling. Same generic auto-budget mechanism as traverse_graph.
        const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
        return dualOutputBudgeted(applyMcpBudgetAuto(response, resolveMaxKb('get_cgm_subgraph', budget_kb, verbosity), 'get_cgm_subgraph', budget_kb))
      } catch (err) {
        return errorOutput('get_cgm_subgraph', String(err), { chart_id })
      }
    }
  )

  // ── query_chart_facts (L1 chart_facts EAV-crosstab lookup) ────────────────
  // marsys://tool/L1/chart_facts_query  (D7 gap-fill / B.11 floor tool)
  //
  // R5 W1 (lane: chart_query) fix: this tool 404'd unconditionally in prod (R5_RUN_LEDGER
  // NF-1) because the registry-side handler called a Python sidecar route that does not
  // exist. The handler was rewritten to query chart_facts directly (see
  // register_d7_channel.ts) — this shim now also: (a) adds `about` (design §27.1 universal
  // address facet — "lagna", {graha}, {bhava}, {house_lord}) and `shape` (pivoted/rows,
  // design §1/§18 EAV-crosstab mandate); (b) drops `as_of_date`/`from_date`/`to_date` —
  // chart_facts has no validity_start/validity_end columns, so these params could never
  // have done anything (a dead-param bug of the same class as P1's as_of_date, fixed here
  // by removing the illusion of the filter rather than silently ignoring it). See
  // R5_JUDGMENT_LEDGER for the ruling on both changes.
  server.tool(
    'query_chart_facts',
    'EAV-crosstab lookup over the chart_facts table (27,554 rows per chart, single ayanamsha per call). Covers planet positions, dignities, strengths, house placements, divisional charts, yogas, doshas, and more. Default shape="pivoted" returns ONE wide row per fact_subject (e.g. lagna -> {sign, sign_lord, house_d1, pada, longitude_sidereal}) instead of raw EAV rows — shape="rows" returns the flat form. The `about` facet lets you address the chart astrologically instead of guessing categories: about="lagna", about={graha:"Saturn"}, about={bhava:10} (the house itself), about={house_lord:10} (resolves the Nth house rashi from the lagna + classical BPHS rulership and returns the resolved lord graha\'s facts — the resolution chain is served back in `about_resolution`). Returns fact_id references for downstream drill. B.11-floor-injected. chart_id is required — never defaulted.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe(
        "Ayanamsha to query. Any of the 6 stored ayanamshas is reachable: 'lahiri_chitrapaksha' " +
        "(default), 'krishnamurti' (alias 'kp'), 'raman', 'surya_siddhanta_classical', " +
        "'true_chitra' (alias 'true_citra'), 'INVARIANT'. One ayanamsha per call."
      ),
      about: z.union([
        z.string(),
        z.object({ graha: z.string().optional(), bhava: z.number().int().min(1).max(12).optional(), house_lord: z.number().int().min(1).max(12).optional() }),
      ]).optional().describe('Astrological address facet: "lagna", a graha name, {graha}, {bhava:N}, or {house_lord:N}.'),
      category: z.string().optional().describe(
        'Fact category filter (e.g. "graha_position", "graha_dignity_per_varga", "yoga_label", "house_bhava_bala_total"). Comma-separated for multiple.'
      ),
      planet: z.string().optional().describe('Graha name filter (e.g. "Sun", "Moon", "Saturn", "Rahu", "Ketu").'),
      house: z.number().int().min(1).max(12).optional().describe('Bhava number (1–12) filter.'),
      sign: z.string().optional().describe('Rashi name filter (e.g. "Aries", "Scorpio").'),
      nakshatra: z.string().optional().describe('Nakshatra name filter.'),
      divisional_chart: z.string().optional().describe('Divisional chart code filter (e.g. "D9", "D10", "D2"). Also returns that varga\'s chart_divisionals-native EAV facts (per-varga sign/house, hora class incl. surya_hora/chandra_hora + hora_d2_house, varga dignity, house lords/occupants) in a separate `divisional_facts` section — data not stored in chart_facts.'),
      keyword: z.string().optional().describe('Free-text keyword search over fact_key/fact_value_text.'),
      fact_subject: z.string().optional().describe('Exact fact_subject filter (e.g. "LAGNA", "SUN", "D9_JUP", "HOUSE_10"). Comma-separated for multiple.'),
      shape: z.enum(['pivoted', 'rows']).optional().describe('"pivoted" (default, one wide row per subject) or "rows" (flat EAV rows).'),
      limit: z.number().int().min(1).max(1000).optional().describe('Max subjects/rows to return (default: 100, max: 1000).'),
      offset: z.number().int().min(0).optional().describe('Pagination offset — rows (shape="rows") or subjects (shape="pivoted") to skip before the next `limit` (default: 0).'),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, about, category, planet, house, sign, nakshatra, divisional_chart, keyword, fact_subject, shape, limit, offset, budget_kb }) => {
      if (!chart_id) return errorOutput('query_chart_facts', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L1/chart_facts_query',
          {
            chart_id,
            // WP-1.3(f)/LCA-3: query_chart_facts-scoped resolver so all 6 stored ayanamshas
            // (incl. true_chitra) are reachable — the shared normalizeAyanamsha collapses
            // true_chitra -> lahiri, hiding a full dataset.
            ayanamsha_id: resolveChartFactsAyanamsha(ayanamsha_id),
            ...(about !== undefined ? { about } : {}),
            ...(category ? { category } : {}),
            ...(planet ? { planet } : {}),
            ...(house != null ? { house } : {}),
            ...(sign ? { sign } : {}),
            ...(nakshatra ? { nakshatra } : {}),
            ...(divisional_chart ? { divisional_chart } : {}),
            ...(keyword ? { keyword } : {}),
            ...(fact_subject ? { fact_subject } : {}),
            ...(shape ? { shape } : {}),
            ...(limit != null ? { limit } : {}),
            ...(offset != null ? { offset } : {}),
          },
          chart_id, principal
        )
        return dualOutputBudgeted(applyMcpBudgetAuto(data as Record<string, unknown>, resolveMaxKb('query_chart_facts', budget_kb), 'query_chart_facts', budget_kb))
      } catch (err) {
        return errorOutput('query_chart_facts', String(err), { chart_id })
      }
    }
  )

  // ── chart_snapshot (R5.1 C2 item 7 — compact chat-renderable D1/D9 grid) ──
  // marsys://tool/L1/chart_snapshot — "the 'show me the chart' answer": 12-rashi text grid,
  // occupants w/ degrees, Lagna marked, <=2KB. D9 (navamsa) only on explicit include_navamsa=true.
  server.tool(
    'chart_snapshot',
    'The compact "show me the chart" answer: a 12-rashi D1 (rashi chart) text grid — every graha\'s sign + degree-in-sign, Lagna sign clearly marked — sized for direct display in a chat client (hard-capped at 2KB). Pass include_navamsa=true to ALSO get the D9 (navamsa) grid in the same response — D9 is never included by default. Pass vargas:["D2","D10",...] to ADDITIVELY assemble any number of further divisional-chart grids server-side (EL-48) — served in `additional_vargas`, alongside the unchanged D1(+D9) grid/text shape; a requested varga this chart has no data for is named honestly in `unresolved_vargas`. Renders already-computed chart_divisionals positions; no new computation. chart_id is required.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      include_navamsa: z.boolean().optional().describe('Also include the D9 (navamsa) grid. Default: false (D1 only).'),
      vargas: z.array(z.string()).optional().describe('Additional varga codes to assemble (e.g. ["D2","D10","D11"]), additive to D1 (and D9 if include_navamsa is set) — served in `additional_vargas`, never replacing the D1/D9 default. Standard codes: D1-D10, D12, D16, D20, D24, D27, D30, D40, D45, D60.'),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, include_navamsa, vargas, budget_kb }) => {
      if (!chart_id) return errorOutput('chart_snapshot', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L1/chart_snapshot',
          {
            chart_id,
            ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
            ...(include_navamsa != null ? { include_navamsa } : {}),
            ...(vargas && vargas.length > 0 ? { vargas } : {}),
          },
          chart_id, principal
        )
        return dualOutputBudgeted(applyMcpBudgetAuto(data as Record<string, unknown>, resolveMaxKb('chart_snapshot', budget_kb), 'chart_snapshot', budget_kb))
      } catch (err) {
        return errorOutput('chart_snapshot', String(err), { chart_id })
      }
    }
  )

  // ── get_graha_yuddha (R5.1 C2 item 6 — JL-027 Option A serve-time overlay) ─
  // marsys://tool/L1/get_graha_yuddha — graha yuddha (planetary war) winner by northern
  // ecliptic latitude (BPHS Option A), overlaid at serve time on the chart_facts floor.
  // See get_graha_yuddha.ts header for full citation + doctrine (canonical-or-floor).
  server.tool(
    'get_graha_yuddha',
    'Graha yuddha (planetary war): tara-graha pairs (Mars/Mercury/Jupiter/Venus/Saturn) within 1 degree orb in the same sign, and their winner per JL-027 Option A (Parasari northern-latitude rule — Venus always wins; else the more-northern ecliptic latitude wins), computed at serve time from already-computed ephemeris data joined against the chart\'s birth date. chart_facts.graha_yuddha itself remains floored (winner=NULL) at rest; this tool overlays the ratified, cited winner without writing back to chart data. Where the pair is not tara-graha-eligible or ephemeris data is unavailable for the birth date, the floor is returned unchanged — the retired uncited longitude-proxy method is never substituted. chart_id is required.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe('Filter by ayanamsha. Omit for all ayanamshas present.'),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, budget_kb }) => {
      if (!chart_id) return errorOutput('get_graha_yuddha', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L1/get_graha_yuddha',
          {
            chart_id,
            ...(ayanamsha_id ? { ayanamsha_id: normalizeAyanamsha(ayanamsha_id) } : {}),
          },
          chart_id, principal
        )
        return dualOutputBudgeted(applyMcpBudgetAuto(data as Record<string, unknown>, resolveMaxKb('get_graha_yuddha', budget_kb), 'get_graha_yuddha', budget_kb))
      } catch (err) {
        return errorOutput('get_graha_yuddha', String(err), { chart_id })
      }
    }
  )

  // ── vector_search (semantic retrieval — chart-agnostic) ───────────────────
  // Not in the registry; calls platform primitive directly.
  server.tool(
    'vector_search',
    'Semantic vector search over the MARSYS document corpus (domain reports, signal narratives, classical text excerpts, life event annotations). Returns the top-k most semantically similar documents to the query. Chart-agnostic — no chart_id required. Use to find relevant astrological literature, prior domain reports, or signal descriptions matching a natural-language query.',
    {
      query_text: z.string().describe('Natural-language query for semantic retrieval. Required.'),
      top_k: z.number().int().min(1).max(50).optional().describe('Number of results to return (default: 10).'),
      doc_type: z.array(z.string()).optional().describe(
        'Document type filter (e.g. ["domain_report"], ["signal_narrative"], ["classical_text"]). Omit for all types.'
      ),
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ query_text, top_k, doc_type, budget_kb }) => {
      if (!query_text) return errorOutput('vector_search', 'query_text is required')
      try {
        const data = await callPlatformPrimitive('vector_search', {
          query_text,
          top_k: top_k ?? 10,
          ...(doc_type ? { doc_type } : {}),
        }, principal)
        return dualOutputBudgeted(applyMcpBudgetAuto(unwrapDoubleEncodedToolBundleResults(data) as Record<string, unknown>, resolveMaxKb('vector_search', budget_kb), 'vector_search', budget_kb))
      } catch (err) {
        return errorOutput('vector_search', String(err))
      }
    }
  )

  // ── judgment_query (R5 W3, design §28.1) ──────────────────────────────────
  // marsys://tool/L-JUDGMENT/judgment_query — the bhava-adhyaya classical checklist
  // recipe as one instrument, generalizing the assess_marriage/assess_career/
  // assess_health/assess_wealth domain tools (design §29 fold-in). The redundant
  // apex_*_assess aliases were retired per WP-1.3(i)/LCA-11; the canonical assess_*
  // tools remain fully answerable (same capability, richer output).
  server.tool(
    'judgment_query',
    'THE classical bhava-adhyaya judgment recipe as ONE instrument (design §28.1) — the acharya\'s ' +
    'own working method for any bhava-question ("how is the marriage?", "how is my career?", or a ' +
    'bare house number), not hardcoded to marriage. Pass `domain` (marriage/relationship/career/' +
    'wealth/health/progeny/education/spirituality — resolved via the shastra map, design §28.5) or ' +
    'a bare `bhava` (1-12). Returns the COMPLETE classical checklist in ONE call: bhava condition ' +
    '(sign + occupants + aspecting grahas) · bhāveśa (lord) condition + placement + dignity + ' +
    'strength · kāraka condition (e.g. Venus for marriage) · judged from BOTH lagna AND chandra ' +
    '(Sudarshana discipline) · operative-varga confirmation (e.g. D9 for marriage) · bearing yogas/' +
    'doshas · timing hooks (current + upcoming dasha windows for the lord/karaka) · a deterministic ' +
    'promise-register verdict (never an LLM judgment or a probability) · a classical-units ' +
    'completeness RECEIPT (design §28.6): {bhava, bhavesha, karaka, from_moon, varga_confirmed, ' +
    'yogas_checked, bhanga_checked, timing_anchored}. Generalizes assess_marriage/' +
    'assess_career/assess_health/assess_wealth (the redundant apex_*_assess aliases were ' +
    'retired per WP-1.3(i)/LCA-11); this is the richer, shastra-shaped successor. response_format=\'v3\' (opt-in; ' +
    'default \'legacy\') returns the R5 unified envelope.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      domain: z.string().optional().describe(
        'Life-domain name (shastra map, design §28.5): marriage/relationship/partnership ' +
        '(bhava 7, Venus, D9), career/vocation (bhava 10, Sun+Mercury+Saturn, D10), wealth/finance ' +
        '(bhava 2, Jupiter, D2), health/vitality (bhava 1, Sun, D6), progeny/children (bhava 5, ' +
        'Jupiter, D7), education (bhava 4, Mercury+Jupiter, D24), spirituality (bhava 9, ' +
        'Jupiter+Ketu, D20). Takes precedence over `bhava` if both given.'
      ),
      bhava: z.number().int().min(1).max(12).optional().describe(
        'Bhava (house) number 1-12, for a judgment question the shastra map does not name a ' +
        'domain for. Required if `domain` is omitted.'
      ),
      response_format: z.enum(['legacy', 'v3']).optional().describe(
        "Envelope shape: 'legacy' (default, unchanged) or 'v3' (populated verdict/grounding/" +
        "drill_pointers/chart_header — opt-in until the R5 W4 battery flips the default)."
      ),
      max_signals: z.number().int().min(1).max(50).optional().describe(
        'Max yoga/dosha signals to include in the bearing-yogas check (default: 15, max: 50).'
      ),
      verbosity: VERBOSITY_ZOD,
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, domain, bhava, response_format, max_signals, verbosity, budget_kb }) => {
      if (!chart_id) return errorOutput('judgment_query', 'chart_id is required')
      if (!domain && bhava === undefined) {
        return errorOutput('judgment_query', 'either `domain` or `bhava` is required')
      }
      try {
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        // R5.1 C1: 'v3' is now the MCP-channel DEFAULT for this instrument (an explicit
        // response_format:'legacy' remains the escape hatch to the pre-C1 hollow envelope).
        const format = resolveEnvelopeFormat(response_format ?? 'v3')
        // Entitlement gate (finding: "provenance.tables / source_table expose raw internal
        // schema names regardless of entitlement") — only a native/debug-tier principal
        // (super_admin, same role check the X-MCP-Audience-Tier header above already uses)
        // sees raw DB table names in a `provenance` block; an ordinary end-user-facing call
        // gets the same content with those two fields stripped (redactProvenanceTables).
        const entitled = principal.role === 'super_admin'

        // B.11: fetch holistic orientation alongside the judgment recipe (S1: parallelized)
        const [{ orientation_context: rawOrientationContext, orientation_ok }, raw] = await Promise.all([
          fetchOrientationContext(chart_id, resolvedAyanamsha, principal, verbosity),
          callRegistryCapability(
            'marsys://tool/L-JUDGMENT/judgment_query',
            { chart_id, ayanamsha_id: resolvedAyanamsha, domain, bhava, max_signals },
            chart_id, principal
          ),
        ])
        // orientation_context carries query_ucd's raw content verbatim (including its
        // content.provenance.tables block, e.g. ['vw_chart_digest', 'bodha_msr_signals',
        // 'bodha_convergence']) — it rides in as a SIBLING field, not through envelope()'s
        // `content`, so it needs its own gate call (envelope()'s `entitled` param below only
        // covers judgment_query's own `inner` content).
        const orientation_context = redactProvenanceTables(rawOrientationContext, entitled)
        const wrapper = raw as Record<string, unknown>
        const inner = (wrapper['content'] as Record<string, unknown>) ?? wrapper

        // R5.1 C1 — the trimmable sections of judgment_query's own content shape (see
        // register_d9_judgment.ts's handler return for the shape these paths address).
        // bearing_yogas (up to max_signals, default 15/max 50 signal objects) is the
        // dominant lever; the rest are cheap defense-in-depth floors.
        const judgmentSections: TrimmableSection<Record<string, unknown>>[] = [
          {
            path: 'content.checklist.bearing_yogas',
            getArray: (root) => {
              const checklist = (root['content'] as Record<string, unknown> | undefined)?.['checklist'] as Record<string, unknown> | undefined
              const arr = checklist?.['bearing_yogas']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const checklist = (root['content'] as Record<string, unknown> | undefined)?.['checklist'] as Record<string, unknown> | undefined
              if (checklist) checklist['bearing_yogas'] = kept
            },
            minKeep: 3,
            recover: { instrument: 'bodha_signals_get', hint: 'full yoga+dosha+karaka_alignment signal set beyond the lean slice kept here — pass domain + a higher top_k. (SC-18: was "query_signals", a non-existent MCP tool name).' },
            label: 'checklist.bearing_yogas',
            // D-1.5a wave gate finding: this is the firings-authoritative verdict-moving
            // signal (A3/R-3) — a fired Dhana/Raja/NBRY yoga must actually be visible in the
            // served response, not just move the (invisible) composite score internally.
            // hardFloor protects its minKeep=3 from PASS 2's hard-cap override, which was
            // silently zeroing it precisely because the fix made it non-empty for the first
            // time (see response_budget.ts's TrimmableSection.hardFloor doc).
            hardFloor: true,
          },
          {
            // DR-9 Part B (native-ratified): the THREAT layer's own §N.6 hardFloor —
            // symmetric to bearing_yogas. The whole point of the partitioned serve is
            // that a budget trim can NEVER zero the adverse layer while the supporting
            // layer survives (that asymmetry is how the estate showed all-benefic).
            path: 'content.checklist.bearing_afflictions',
            getArray: (root) => {
              const checklist = (root['content'] as Record<string, unknown> | undefined)?.['checklist'] as Record<string, unknown> | undefined
              const arr = checklist?.['bearing_afflictions']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const checklist = (root['content'] as Record<string, unknown> | undefined)?.['checklist'] as Record<string, unknown> | undefined
              if (checklist) checklist['bearing_afflictions'] = kept
            },
            minKeep: 3,
            recover: { instrument: 'bodha_signals_get', hint: 'full adverse-valence (malefic/mixed) signal set for this domain beyond the lean threat-layer slice kept here — pass domain + a higher top_k.' },
            label: 'checklist.bearing_afflictions',
            hardFloor: true,
          },
          {
            // affliction mechanisms (graha-to-house tenancy afflictions, e.g.
            // Rahu-occupies-dhana) — the mechanism-level threat layer, also floored.
            path: 'content.checklist.affliction_mechanisms',
            getArray: (root) => {
              const checklist = (root['content'] as Record<string, unknown> | undefined)?.['checklist'] as Record<string, unknown> | undefined
              const arr = checklist?.['affliction_mechanisms']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const checklist = (root['content'] as Record<string, unknown> | undefined)?.['checklist'] as Record<string, unknown> | undefined
              if (checklist) checklist['affliction_mechanisms'] = kept
            },
            minKeep: 2,
            recover: { instrument: 'bodha_discoveries_get', hint: 'full graha_bhava_affliction + adverse mechanism set beyond the slice kept here.' },
            label: 'checklist.affliction_mechanisms',
            hardFloor: true,
          },
          {
            path: 'content.checklist.varga_confirmation.rows',
            getArray: (root) => {
              const vc = ((root['content'] as Record<string, unknown> | undefined)?.['checklist'] as Record<string, unknown> | undefined)?.['varga_confirmation'] as Record<string, unknown> | undefined
              const arr = vc?.['rows']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const vc = ((root['content'] as Record<string, unknown> | undefined)?.['checklist'] as Record<string, unknown> | undefined)?.['varga_confirmation'] as Record<string, unknown> | undefined
              if (vc) vc['rows'] = kept
            },
            minKeep: 4,
            recover: { instrument: 'ganita_chart_facts_get', hint: 'full operative-varga placements for every graha (this call confirmed only bhāveśa/kāraka). (SC-18: was "get_divisionals", a non-existent MCP tool name; pass divisional_chart=<varga>).' },
            label: 'checklist.varga_confirmation.rows',
          },
          {
            path: 'content.fact_id_refs',
            getArray: (root) => {
              const arr = (root['content'] as Record<string, unknown> | undefined)?.['fact_id_refs']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const content = root['content'] as Record<string, unknown> | undefined
              if (content) content['fact_id_refs'] = kept
            },
            minKeep: 20,
            recover: { instrument: 'judgment_query', hint: 'full fact_id_refs list (this response kept a lean slice; grounding.fact_ids in the envelope still reflects the full set).' },
            label: 'content.fact_id_refs',
          },
          {
            // R5.1 C1 fix (live-verifier finding #1): checklist.timing_hooks was NOT
            // declared as trimmable at all — live measurement showed it alone at
            // ~5.2-5.5KB for career/native, the dominant remaining lever after
            // bearing_yogas/varga_confirmation. `current` is a flat array (get_dashas'
            // ≤5-row snapshot) — trim it directly.
            path: 'content.checklist.timing_hooks.current',
            getArray: (root) => {
              const timing = ((root['content'] as Record<string, unknown> | undefined)?.['checklist'] as Record<string, unknown> | undefined)?.['timing_hooks'] as Record<string, unknown> | undefined
              const arr = timing?.['current']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const timing = ((root['content'] as Record<string, unknown> | undefined)?.['checklist'] as Record<string, unknown> | undefined)?.['timing_hooks'] as Record<string, unknown> | undefined
              if (timing) timing['current'] = kept
            },
            minKeep: 3,
            hardFloor: true, // F-51: answer-bearing timing — PASS 2 must not zero this while catalog rows survive
            recover: { instrument: 'ganita_dashas_get', hint: 'full current-period rows across all dasha levels (this call kept a lean slice).' },
            label: 'checklist.timing_hooks.current',
          },
          {
            // `mahadasha_windows_by_graha` is a Record<graha, rows[]> — NOT a single array —
            // so this section flattens it to a { graha, row } array for measurement/cutting,
            // then regroups by graha in setArray. Trims total window-rows across ALL grahas
            // combined (not per-graha), which is what actually drives the byte count.
            path: 'content.checklist.timing_hooks.mahadasha_windows_by_graha',
            getArray: (root) => {
              const timing = ((root['content'] as Record<string, unknown> | undefined)?.['checklist'] as Record<string, unknown> | undefined)?.['timing_hooks'] as Record<string, unknown> | undefined
              const windows = timing?.['mahadasha_windows_by_graha'] as Record<string, unknown[]> | undefined
              if (!windows) return undefined
              const flat: { graha: string; row: unknown }[] = []
              for (const [graha, rows] of Object.entries(windows)) {
                if (Array.isArray(rows)) for (const row of rows) flat.push({ graha, row })
              }
              return flat.length > 0 ? flat : undefined
            },
            setArray: (root, kept) => {
              const timing = ((root['content'] as Record<string, unknown> | undefined)?.['checklist'] as Record<string, unknown> | undefined)?.['timing_hooks'] as Record<string, unknown> | undefined
              if (!timing) return
              const regrouped: Record<string, unknown[]> = {}
              for (const item of kept as { graha: string; row: unknown }[]) {
                if (!regrouped[item.graha]) regrouped[item.graha] = []
                regrouped[item.graha]!.push(item.row)
              }
              timing['mahadasha_windows_by_graha'] = regrouped
            },
            minKeep: 4,
            hardFloor: true, // F-51: answer-bearing timing — PASS 2 must not zero this while catalog rows survive
            recover: { instrument: 'ganita_dashas_get', hint: 'full multi-level dasha timeline for the bhāveśa/kāraka(s) (this call kept a lean slice of mahadasha windows only).' },
            label: 'checklist.timing_hooks.mahadasha_windows_by_graha',
          },
        ]

        // Elevation α: for a flagship domain question, steer to dossier's complete-accounting
        // sweep (compact pointer — judgment_query's 12KB budget can't hold the full map).
        const completenessPointer = buildDomainCompletenessPointer(domain, chart_id)

        if (format !== 'v3') {
          const legacyResponse: Record<string, unknown> = { orientation_context, orientation_ok, ...envelope(inner, 'judgment_query', undefined, 'legacy', undefined, entitled) }
          if (completenessPointer) legacyResponse['domain_completeness_pointer'] = completenessPointer
          return dualOutputBudgeted(applyMcpBudget(legacyResponse, resolveMaxKb('judgment_query', budget_kb, verbosity), judgmentSections, budget_kb))
        }

        // ── v3 population (design §10/§28.6) ──────────────────────────────────
        const receipt = (inner['receipt'] as Record<string, unknown>) ?? {}
        const verdictBlock = (inner['verdict'] as Record<string, unknown>) ?? {}
        const factIdRefs = (inner['fact_id_refs'] as string[]) ?? []
        const grounding = { fact_ids: factIdRefs, citations: [], grounding_score: null }

        const verdict = {
          ...verdictBlock,
          receipt,
          note: 'Deterministic classical-checklist verdict + completeness receipt (design §28.6) — see `receipt` for which checklist items were actually checked this call.',
        }

        const judgment_flags = (inner['judgment_flags'] as JudgmentFlagEntry[]) ?? []
        const drill_pointers = (inner['drill_pointers'] as { instrument: string; hint: string; pointer_type?: DrillPointerType }[]) ?? []

        const { chart_header, flags: chartHeaderFlags } = await resolveChartHeader(chart_id, resolvedAyanamsha, principal)
        judgment_flags.push(...chartHeaderFlags)

        // Elevation α: un-missable steer to the complete-accounting dossier sweep for a flagship
        // domain question. Kept OUT of drill_pointers (that array carries a closed §28.4
        // pointer_type vocabulary with exact-shape tests) — the steer rides as a string
        // judgment_flag plus the dedicated `domain_completeness_pointer` envelope field.
        if (completenessPointer) {
          judgment_flags.unshift(
            `complete_domain_accounting_available: dossier(domain="${String(domain)}", chart_id) serves ` +
              `all ${String(completenessPointer['slice_size'])} ${String(domain)} concepts at 100% accounting ` +
              `(see domain_completeness_pointer). This judgment is a domain-scoped verdict, not the whole reading.`,
          )
        }

        const v3Response = {
          orientation_context, orientation_ok,
          ...envelope(inner, 'judgment_query', undefined, 'v3', {
            chart_header, verdict, grounding, drill_pointers, judgment_flags,
          }, entitled),
          ...(completenessPointer ? { domain_completeness_pointer: completenessPointer } : {}),
        }
        const budgeted = applyMcpBudget(v3Response, resolveMaxKb('judgment_query', budget_kb, verbosity), judgmentSections, budget_kb)
        // R-21 fix: `receipt.varga_confirmed`/`receipt.timing_anchored` were stamped from the
        // PRE-TRIM capability output (register_d9_judgment.ts) — reconcile against what
        // actually survived applyMcpBudget so e.g. varga_confirmed:"D10✓" is never served
        // next to a `checklist.varga_confirmation.rows` that trimmed to empty.
        reconcileReceiptWithTrimReport(receipt, {
          varga_confirmed: ['content.checklist.varga_confirmation.rows'],
          timing_anchored: ['content.checklist.timing_hooks.current', 'content.checklist.timing_hooks.mahadasha_windows_by_graha'],
        }, budgeted['trim_report'] as TrimReportEntry[] | null | undefined)
        // WP-S4-fix2 (Gate Ś #10): definitive post-trim honesty guard — see
        // enforceTimingAnchoredHonesty's docstring. Runs AFTER the path-matched reconcile above
        // so it catches the case that reconcile's trim_report-path matching cannot: a timing
        // array that was already empty pre-trim (never appears in trim_report at all) rather
        // than one the budget trimmer cut to zero.
        enforceTimingAnchoredHonesty(
          receipt,
          budgeted['content'] as Record<string, unknown> | undefined,
          budgeted['judgment_flags'] as JudgmentFlagEntry[] | undefined ?? [],
        )
        // PARIŚODHANA Phase B1 (CR-2/CR-63/R-38): the varga_confirmed sibling of the
        // timing_anchored guard above — see enforceVargaConfirmedHonesty's docstring.
        enforceVargaConfirmedHonesty(
          receipt,
          budgeted['content'] as Record<string, unknown> | undefined,
          budgeted['judgment_flags'] as JudgmentFlagEntry[] | undefined ?? [],
        )
        return dualOutputBudgeted(budgeted)
      } catch (err) {
        return errorOutput('judgment_query', String(err), { chart_id })
      }
    }
  )

  // ── graha_portrait narration (R5.3 B2 — Pratinidhi-R ruling) ──────────────────
  // Assembles verdict.narration PROSE from facts `inner` already carries (pre-trim —
  // narration is built before applyMcpBudget runs, so it can safely cite any row even
  // if that row is later trimmed off the wire in `content`; grounding.fact_ids below is
  // expanded with every fact_id this narration cites so the citation still resolves).
  // NO new astrological derivation of chart values: the two classical lookup tables
  // below (sign→lord rulership, shadbala required-rupas thresholds) are the SAME fixed,
  // published-constant values ga_structural_writer.py / ga_strength_writer.py already
  // embed server-side — reused here for prose framing, never re-derived per chart.
  const ZODIAC_SIGNS_ORDER = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
  ] as const
  const SIGN_LORD: Record<string, string> = {
    Aries: 'Mars', Taurus: 'Venus', Gemini: 'Mercury', Cancer: 'Moon', Leo: 'Sun',
    Virgo: 'Mercury', Libra: 'Venus', Scorpio: 'Mars', Sagittarius: 'Jupiter',
    Capricorn: 'Saturn', Aquarius: 'Saturn', Pisces: 'Jupiter',
  }
  const DUSTHANA_HOUSES = new Set([6, 8, 12])
  const ORDINAL_WORDS = [
    '0th', '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th', '12th',
  ]
  const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
  const NATIVE_BIRTH_YEAR = 1984
  const DIGNITY_LABEL: Record<string, string> = {
    debilitated: 'debilitated (neecha)', exalted: 'exalted', own: 'own sign', neutral: 'neutral',
  }

  type PortraitRow = Record<string, unknown>
  const ordinalWord = (n: number): string => ORDINAL_WORDS[n] ?? `${n}th`
  const rowsOf = (inner: Record<string, unknown>, section: string, field: string): PortraitRow[] => {
    const s = inner[section] as Record<string, unknown> | undefined
    const arr = s?.[field]
    return Array.isArray(arr) ? (arr as PortraitRow[]) : []
  }
  const factIdOf = (row: PortraitRow | undefined): string | null => {
    const v = row?.['fact_id']
    return typeof v === 'string' ? v : null
  }
  const jsonbOf = (row: PortraitRow | undefined): Record<string, unknown> => {
    const v = row?.['fact_value_jsonb']
    return (v && typeof v === 'object') ? v as Record<string, unknown> : {}
  }
  const textOf = (row: PortraitRow | undefined): string | null => {
    const v = row?.['fact_value_text']
    return typeof v === 'string' ? v : null
  }
  const numOf = (row: PortraitRow | undefined): number | null => {
    const v = row?.['fact_value_num']
    if (typeof v === 'number') return v
    if (typeof v === 'string' && v.trim() !== '' && !Number.isNaN(Number(v))) return Number(v)
    return null
  }
  const dignityTier = (state: string | null): 'strong' | 'weak' | 'mid' | 'unknown' => {
    if (state === 'exalted' || state === 'own') return 'strong'
    if (state === 'debilitated') return 'weak'
    if (state === 'neutral') return 'mid'
    return 'unknown'
  }
  const housesRuledFromLagna = (grahaName: string, lagnaSign: string): number[] => {
    const startIdx = ZODIAC_SIGNS_ORDER.indexOf(lagnaSign as typeof ZODIAC_SIGNS_ORDER[number])
    if (startIdx < 0) return []
    const houses: number[] = []
    for (let h = 1; h <= 12; h++) {
      const sign = ZODIAC_SIGNS_ORDER[(startIdx + h - 1) % 12]
      if (sign && SIGN_LORD[sign] === grahaName) houses.push(h)
    }
    return houses
  }
  /** Deletes `citation_ref` (internal MCP-lineage debug string, never a classical
   *  citation — see Pratinidhi-R ruling) from every row this narration reads, freeing
   *  budget headroom for the added prose. Only ever applied to the v3 response path. */
  const stripCitationRefDeep = (node: unknown): void => {
    if (node === null || typeof node !== 'object') return
    if (Array.isArray(node)) { for (const v of node) stripCitationRefDeep(v); return }
    const obj = node as Record<string, unknown>
    if ('citation_ref' in obj) delete obj['citation_ref']
    for (const v of Object.values(obj)) stripCitationRefDeep(v)
  }

  async function buildGrahaPortraitNarration(
    chartId: string, grahaName: string, lagnaSign: string | null, inner: Record<string, unknown>,
    principal: Principal,
  ): Promise<{ narration: string; extraFactIds: string[] }> {
    const sentences: string[] = []
    const extraFactIds: string[] = []

    // ── functional role (lordship houses from lagna + already-computed functional class) ──
    const functionalRows = rowsOf(inner, 'functional_nature', 'rows')
    const bphsRow = functionalRows.find(r => r['fact_key'] === 'bphs_canonical')
    const functionalClass = textOf(bphsRow)
    if (lagnaSign) {
      const houses = housesRuledFromLagna(grahaName, lagnaSign)
      if (houses.length > 0) {
        const houseList = houses.map(ordinalWord).join(' + ')
        const yk = functionalClass === 'yoga_karaka'
        sentences.push(
          `${grahaName} = ${houseList} lord for ${lagnaSign} lagna` +
          (functionalClass ? ` (${yk ? 'yogakaraka' : functionalClass.replace(/_/g, ' ')})` : '') + '.',
        )
        const fid = factIdOf(bphsRow); if (fid) extraFactIds.push(fid)
      }
    }

    // ── dignity: D1 vs D9 promise-vs-delivery tension ────────────────────────
    const dignityRows = rowsOf(inner, 'dignity', 'operative_varga_rows')
    const byVarga = new Map<string, PortraitRow>()
    for (const r of dignityRows) {
      const varga = jsonbOf(r)['varga']
      if (typeof varga === 'string') byVarga.set(varga, r)
    }
    const d1 = byVarga.get('D1')
    const d9 = byVarga.get('D9')
    const describeVargaRow = (r: PortraitRow): string => {
      const state = textOf(r) ?? 'unknown'
      const j = jsonbOf(r)
      const sign = typeof j['sign'] === 'string' ? j['sign'] as string : '?'
      const houseRaw = j['house']
      const house = typeof houseRaw === 'number' ? houseRaw : (typeof houseRaw === 'string' ? Number(houseRaw) : null)
      const label = DIGNITY_LABEL[state] ?? state
      return `${label} (${sign}${house != null && Number.isFinite(house) ? `, ${ordinalWord(house)} house` : ''})`
    }

    if (d1) {
      const fid = factIdOf(d1); if (fid) extraFactIds.push(fid)
      const state = textOf(d1)
      const confirmPrefix = dignityTier(state) === 'strong' ? 'Confirmed: ' : ''
      sentences.push(`${confirmPrefix}${grahaName} is ${describeVargaRow(d1)} in D1.`)

      if (d9) {
        const fid9 = factIdOf(d9); if (fid9) extraFactIds.push(fid9)
        const t1 = dignityTier(state)
        const t9 = dignityTier(textOf(d9))
        let connector = 'and'
        if (t1 === 'strong' && t9 === 'weak') connector = 'but'
        else if (t1 === 'weak' && t9 === 'strong') connector = 'though redeemed —'
        sentences.push(
          `In D9: ${describeVargaRow(d9)} — ${connector} ${
            t1 !== t9
              ? (t1 === 'strong' ? 'natal strength undercut by navamsha stress' : 'natal weakness tempered by navamsha support')
              : 'a consistent read across D1 and D9'
          }.`,
        )
      }

      // ── dusthana-house counterweight (dignity vs house-utility tension) ────
      const d1HouseRaw = jsonbOf(d1)['house']
      const d1House = typeof d1HouseRaw === 'number' ? d1HouseRaw : null
      if (d1House != null && DUSTHANA_HOUSES.has(d1House) && dignityTier(state) === 'strong') {
        const houseName = d1House === 12 ? '12th house (dusthana: loss/expenditure/bed-pleasures)'
          : d1House === 8 ? '8th house (dusthana: transformation/longevity stress)'
          : '6th house (dusthana: conflict/service/debt)'
        sentences.push(
          `But this dignity sits in the ${houseName} — dignity does not sit in an unconditionally ` +
          `strength-giving house; this tempers any "guarantees" framing.`,
        )
      }

      // ── neecha-bhanga honesty check (only when D1 is debilitated) ───────────
      if (state === 'debilitated') {
        const sign = jsonbOf(d1)['sign']
        const dispositor = typeof sign === 'string' ? SIGN_LORD[sign] : undefined
        if (dispositor) {
          const cgm = inner['cgm_neighborhood'] as Record<string, unknown> | undefined
          const nodes = ((cgm?.['nodes']) ?? []) as PortraitRow[]
          const dispositorNode = nodes.find(n =>
            n['node_type'] === 'graha' &&
            typeof n['node_subject'] === 'string' &&
            (n['node_subject'] as string).toUpperCase() === dispositor.toUpperCase(),
          )
          if (dispositorNode) {
            const dState = dispositorNode['dignity_state']
            const strong = dState === 'exalted' || dState === 'own'
            sentences.push(
              `Neecha-bhanga checked via the fetched dispositor-chain data: dispositor ${dispositor}'s ` +
              `dignity here is ${String(dState ?? 'unknown')} — ${strong
                ? 'the strong-dispositor cancellation condition IS met (treat as a candidate bhanga, not a full multi-condition confirmation — other classical conditions like kendra placement aren\'t covered by this depth-1 neighborhood).'
                : 'the strong-dispositor cancellation condition is NOT met from this data; no cancellation confirmed here — a full multi-condition audit needs deeper dispositor-chain traversal.'}`,
            )
          } else if (nodes.length === 0) {
            // EL-07 Absence Protocol: distinguish "the neighborhood query itself returned
            // nothing" (a genuine grounding gap worth naming explicitly) from the dispositor
            // simply not being among an otherwise-populated node set (the branch below).
            sentences.push(
              `Neecha-bhanga could not be checked against dispositor-chain data: this portrait's ` +
              `cgm_neighborhood.nodes returned 0 rows for ${grahaName} — no cancellation condition ` +
              `evaluated (not a claim that ${dispositor} lacks cancellation, only that this depth-1 ` +
              `neighborhood query had nothing to check it against); traverse_graph can re-query directly.`,
            )
          } else {
            sentences.push(
              `Neecha-bhanga checked against the dispositor-chain data this portrait retrieves: dispositor ` +
              `${dispositor} is not among the ${nodes.length} node(s) present in the depth-1 cgm_neighborhood ` +
              `returned here — no cancellation condition met in what's available; a full multi-condition audit ` +
              `needs deeper dispositor-chain traversal (see drill_pointers).`,
            )
          }
        }
      }
    } else if (d9) {
      const fid9 = factIdOf(d9); if (fid9) extraFactIds.push(fid9)
      sentences.push(`In D9: ${describeVargaRow(d9)}.`)
    }

    // ── shadbala ───────────────────────────────────────────────────────────
    // ŚUDDHA-VĀCA P0-1..4 fix (lane:serve-shadbala — the native's originating complaint):
    // graha_shadbala_total carries TWO fact_key variants for the same (chart_id,
    // ayanamsha_id, fact_subject) — 'ratio' (L1 achieved/required, ~0.8-1.7) and 'rupa'
    // (raw achieved, ~4.6-8.5). The prior code selected whichever row `.find()` landed on
    // first (no fact_key pin — D1_MISSELECT) and printed it labeled "rupas" regardless of
    // which one it actually was, against a hardcoded SHADBALA_REQUIRED_RUPAS constant
    // (D3_HARDCODED_DRIFT) — producing "1.69 rupas vs 5.00 required — grade: weak (deficit)"
    // for Sun, the chart's single strongest planet. Fix: pin fact_key='rupa' for the
    // achieved value, and REFERENCE (never re-derive, §N.5) the graha's own L1
    // `required_rupa` fact — stored under ayanamsha_id='INVARIANT' since it does not vary
    // by ayanamsha, confirmed live for chart 482012f1.
    const strengthRows = rowsOf(inner, 'strength', 'rows')
    const totalRow = strengthRows.find(r => r['fact_category'] === 'graha_shadbala_total' && r['fact_key'] === 'rupa')
    if (totalRow) {
      const fid = factIdOf(totalRow); if (fid) extraFactIds.push(fid)
      const rupas = numOf(totalRow)
      if (rupas != null) {
        let required: number | null = null
        let requiredFid: string | null = null
        try {
          const requiredPayload = await callRegistryCapability(
            'marsys://tool/L1/chart_facts_query',
            {
              chart_id: chartId, ayanamsha_id: 'INVARIANT', category: 'graha_shadbala_total',
              planet: grahaName, fact_key: 'required_rupa', shape: 'rows',
            },
            chartId, principal,
          )
          const unwrapped = (requiredPayload && typeof requiredPayload === 'object' &&
            'content' in (requiredPayload as Record<string, unknown>) &&
            typeof (requiredPayload as Record<string, unknown>)['is_error'] === 'boolean')
            ? (requiredPayload as Record<string, unknown>)['content']
            : requiredPayload
          const requiredRows = Array.isArray((unwrapped as Record<string, unknown> | undefined)?.['rows'])
            ? (unwrapped as Record<string, unknown>)['rows'] as PortraitRow[]
            : []
          const requiredRow = requiredRows[0]
          required = requiredRow ? numOf(requiredRow) : null
          requiredFid = requiredRow ? factIdOf(requiredRow) : null
        } catch {
          required = null
        }
        if (required != null) {
          if (requiredFid) extraFactIds.push(requiredFid)
          const surplus = rupas - required
          const grade = surplus >= 0 ? 'strong (surplus)' : 'weak (deficit)'
          sentences.push(
            `Shadbala: ${rupas.toFixed(2)} rupas vs ${required.toFixed(2)} required — grade: ${grade} ` +
            `(${surplus >= 0 ? '+' : ''}${surplus.toFixed(2)} rupas).`,
          )
        } else {
          // §N.7.6 — an honest null beats an invented judgment: no fallback threshold,
          // no fabricated grade, when the L1 required_rupa fact can't be reached.
          sentences.push(`Shadbala: ${rupas.toFixed(2)} rupas total (required-rupa threshold unavailable from L1 this call — no grade assigned).`)
        }
      }
    }

    // ── avasthas (up to 2 systems, D1-preferred) ──────────────────────────────
    const avasthaRows = rowsOf(inner, 'avasthas', 'rows')
    const avasthaD1 = avasthaRows.filter(r => r['fact_key'] === 'D1')
    const avasthaPool = avasthaD1.length > 0 ? avasthaD1 : avasthaRows
    const seenSystems = new Set<string>()
    const avasthaClauses: string[] = []
    for (const r of avasthaPool) {
      const category = typeof r['fact_category'] === 'string' ? r['fact_category'] as string : ''
      const system = category.replace('graha_avastha_', '').replace('_per_varga', '')
      if (!system || seenSystems.has(system)) continue
      const state = textOf(r)
      if (!state) continue
      seenSystems.add(system)
      avasthaClauses.push(`${system} avastha: ${state}`)
      const fid = factIdOf(r); if (fid) extraFactIds.push(fid)
      if (avasthaClauses.length >= 2) break
    }
    if (avasthaClauses.length > 0) sentences.push(`Avasthas — ${avasthaClauses.join('; ')}.`)

    // ── yogas / configurations ─────────────────────────────────────────────
    const yogas = (inner['yogas'] as Record<string, unknown> | undefined) ?? {}
    const parivartana = (yogas['parivartana_exchanges'] as PortraitRow[] | undefined) ?? []
    if (parivartana.length > 0) {
      const p = parivartana[0]
      const headline = p && typeof p['signal_headline_text'] === 'string' ? p['signal_headline_text'] as string : null
      const sid = p?.['signal_id']
      sentences.push(
        `Yoga/configuration: parivartana exchange — ${headline ?? 'structural sign exchange'}` +
        `${sid ? ` (signal_id ${String(sid)})` : ''}.`,
      )
    } else {
      const catalogCount =
        ((yogas['catalog_yoga_matches'] as unknown[] | undefined)?.length ?? 0) +
        ((yogas['catalog_dosha_matches'] as unknown[] | undefined)?.length ?? 0)
      if (catalogCount > 0) {
        sentences.push(
          `Yogas: no confirmed parivartana exchange for ${grahaName}; ${catalogCount} catalog yoga/dosha ` +
          `candidate row(s) mention this graha but are requires_pass catalog matches, not confirmed firings (JL-004).`,
        )
      } else {
        sentences.push(
          `Yogas: no parivartana exchange and no catalog yoga/dosha candidates for ${grahaName} in this chart ` +
          `— yoga_fires/dosha_fires are honestly 0 rows for this build (JL-004: a requires_pass catalog, not ` +
          `confirmed firings).`,
        )
      }
    }

    // ── dashas (current/next Mahadasha, with age for the documented native chart only) ──
    const dashaRows = rowsOf(inner, 'dashas', 'rows')
    if (dashaRows.length > 0) {
      const today = new Date().toISOString().slice(0, 10)
      const withDates = dashaRows
        .map(r => ({ row: r, start: r['start_date'], end: r['end_date'] }))
        .filter((x): x is { row: PortraitRow; start: string; end: string } =>
          typeof x.start === 'string' && typeof x.end === 'string')
        .sort((a, b) => a.start.localeCompare(b.start))
      const current = withDates.find(x => x.start <= today && x.end >= today)
      const next = withDates.find(x => x.start > today)
      const ageSuffix = (dateStr: string): string => {
        if (chartId !== NATIVE_CHART_ID) return ''
        const year = Number(dateStr.slice(0, 4))
        return Number.isFinite(year) ? ` (age ${year - NATIVE_BIRTH_YEAR})` : ''
      }
      if (current) {
        sentences.push(`Current ${grahaName} Mahadasha: ${current.start} → ${current.end}${ageSuffix(current.start)}.`)
        const fid = factIdOf(current.row); if (fid) extraFactIds.push(fid)
      }
      if (next) {
        sentences.push(`Next ${grahaName} Mahadasha: ${next.start} → ${next.end}${ageSuffix(next.start)}.`)
        const fid = factIdOf(next.row); if (fid) extraFactIds.push(fid)
      } else if (!current && withDates.length > 0) {
        const past = withDates[withDates.length - 1]
        if (past) {
          sentences.push(`Most recent ${grahaName} Mahadasha (past): ${past.start} → ${past.end}${ageSuffix(past.start)}.`)
          const fid = factIdOf(past.row); if (fid) extraFactIds.push(fid)
        }
      }
    }

    // ── CGM neighborhood (optional, cheap) ────────────────────────────────
    const cgm = inner['cgm_neighborhood'] as Record<string, unknown> | undefined
    const cgmEdges = ((cgm?.['edges']) ?? []) as PortraitRow[]
    if (cgmEdges.length > 0) {
      const top = cgmEdges.slice(0, 3).map(e => String(e['relationship_basis'] ?? e['edge_type'] ?? 'edge'))
      sentences.push(`CGM neighborhood: ${cgmEdges.length} edge(s), top relations — ${top.join(', ')}.`)
    }

    // ── standing disclosures (always true; cheap) ─────────────────────────
    sentences.push(
      'Single-tradition read: dignity/strength above are BPHS/classical-dignity based only ' +
      '(JL-004 caveat) — not cross-checked against Jaimini/KP.',
    )
    sentences.push(
      `Scope: graha_portrait assesses ${grahaName} alone — any bhava-level claim (e.g. marriage promise via ` +
      `the 7th house, career via the 10th) needs judgment_query for the complete promise-register verdict.`,
    )

    return { narration: sentences.join(' '), extraFactIds: Array.from(new Set(extraFactIds)) }
  }

  // ── graha_portrait (R5 W3, design §28.2 — the mirror recipe for graha-questions) ──
  // marsys://tool/L2/graha_portrait
  //
  // MANDATORY W2-lesson check (per the R5 run brief): every param the capability
  // accepts (chart_id, graha, ayanamsha_id, operative_vargas, include) is declared
  // in this Zod schema AND explicitly threaded through the callRegistryCapability
  // args object below — none spread blindly. Verified by grep against
  // graha_portrait.ts's input_schema (see W3 report).
  server.tool(
    'graha_portrait',
    'The mirror recipe for graha-questions (design §28.2) — "how is my Saturn?" as ONE call. Returns a complete portrait of a single graha: current position (sign/house/nakshatra/pada), dignity chain across the operative vargas (D1/D9/D10/D60 highlighted; full varga list included), shadbala decomposition (6 components + total + vimsopaka + ishta/kashta), avasthas (baladi/jagrad/deepta/lajjitadi/sayanadi), yogas/configurations it participates in (parivartana exchanges served as real chart-specific data; yoga_fires/dosha_fires honestly reported empty-with-reason per JL-004 — they are a requires_pass catalog, not confirmed firings), its dasha periods across the lifetime (Mahadasha-level, past AND next, not clipped to the ±5y default window), its CGM neighborhood (direct graph neighbors + edges from traverse_chart_graph), and its functional nature for this lagna (benefic/malefic/yoga-karaka classification). Every section is a synthesis over already-built L1/L2 tools — not a new data source. Use `include` to narrow to a subset of sections for a cheaper call.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      graha: z.string().describe('The graha to portray — English name, Sanskrit name, 2-letter shorthand, or fact_subject code (e.g. "Saturn", "shani", "sa", "SAT"). Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      operative_vargas: z.array(z.string()).optional().describe('Which vargas to call out as "operative" in the dignity chain (default: D1, D9, D10, D60). The full dignity row set across ALL vargas is always included regardless of this list.'),
      include: z.array(z.enum(['position', 'dignity', 'functional_nature', 'strength', 'avasthas', 'special_states', 'yogas', 'dashas', 'cgm_neighborhood'])).optional().describe('Subset of sections to compute (default: all). R-6 fix: functional_nature (served under the dignity call, now independently requestable) and special_states (alias for avasthas — the classical name for the baladi/jagrad/deepta/lajjitadi/sayanadi system) are now valid options; previously the former was unenumerated and the latter errored as invalid.'),
      response_format: z.enum(['legacy', 'v3']).optional().describe("Envelope shape: 'legacy' (default, unchanged — the raw portrait object) or 'v3' (adds populated verdict/grounding/drill_pointers/judgment_flags/chart_header per the R5 unified envelope)."),
      verbosity: VERBOSITY_ZOD,
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, graha, ayanamsha_id, operative_vargas, include, response_format, verbosity, budget_kb }) => {
      if (!chart_id) return errorOutput('graha_portrait', 'chart_id is required')
      if (!graha) return errorOutput('graha_portrait', 'graha is required')
      try {
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        // R5.1 C1: 'v3' is now the MCP-channel DEFAULT for this instrument (an explicit
        // response_format:'legacy' remains the escape hatch to the pre-C1 hollow envelope).
        const format = resolveEnvelopeFormat(response_format ?? 'v3')

        // B.11: fetch holistic orientation before this entity-level drill.
        const [{ orientation_context, orientation_ok }, raw] = await Promise.all([
          fetchOrientationContext(chart_id, resolvedAyanamsha, principal, verbosity),
          callRegistryCapability(
            'marsys://tool/L2/graha_portrait',
            {
              chart_id, graha, ayanamsha_id: resolvedAyanamsha,
              ...(operative_vargas ? { operative_vargas } : {}),
              ...(include ? { include } : {}),
            },
            chart_id, principal,
          ),
        ])
        const wrapper = raw as Record<string, unknown>
        const inner = (wrapper['content'] as Record<string, unknown>) ?? wrapper

        // R5.1 C1 — graha_portrait's dominant size levers (register_d9.../graha_portrait.ts
        // handler shape): dignity.all_varga_rows is a near-duplicate SUPERSET of
        // dignity.operative_varga_rows (which is left untouched — the "operative vargas"
        // highlight survives any trim), so it floors to 0 first; strength/avasthas/yogas/
        // cgm arrays keep a small lean slice rather than being fully dropped.
        const portraitSections: TrimmableSection<Record<string, unknown>>[] = [
          {
            path: 'content.dignity.all_varga_rows',
            getArray: (root) => {
              const dignity = (root['content'] as Record<string, unknown> | undefined)?.['dignity'] as Record<string, unknown> | undefined
              const arr = dignity?.['all_varga_rows']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const dignity = (root['content'] as Record<string, unknown> | undefined)?.['dignity'] as Record<string, unknown> | undefined
              if (dignity) dignity['all_varga_rows'] = kept
            },
            minKeep: 0,
            recover: { instrument: 'ganita_condition_get', hint: 'full dignity_state rows across every varga (this response kept only operative_vargas — D1/D9/D10/D60 by default). (SC-18: was "get_dignity", a non-existent MCP tool name; use facet="dignity").' },
            label: 'dignity.all_varga_rows',
          },
          {
            path: 'content.dignity.other_rows',
            getArray: (root) => {
              const dignity = (root['content'] as Record<string, unknown> | undefined)?.['dignity'] as Record<string, unknown> | undefined
              const arr = dignity?.['other_rows']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const dignity = (root['content'] as Record<string, unknown> | undefined)?.['dignity'] as Record<string, unknown> | undefined
              if (dignity) dignity['other_rows'] = kept
            },
            minKeep: 0,
            recover: { instrument: 'ganita_condition_get', hint: 'full non-dignity/non-functional_class rows for this graha. (SC-18: was "get_dignity", a non-existent MCP tool name; use facet="dignity").' },
            label: 'dignity.other_rows',
          },
          {
            // Last-resort lever: the operative_vargas highlight (D1/D9/D10/D60 by default)
            // is what a "how is my Saturn" mirror-recipe answer needs most — kept at a
            // floor of 2 rather than fully dropped, but eligible to shrink if a
            // well-connected graha's cgm_neighborhood/strength alone can't close the gap.
            path: 'content.dignity.operative_varga_rows',
            getArray: (root) => {
              const dignity = (root['content'] as Record<string, unknown> | undefined)?.['dignity'] as Record<string, unknown> | undefined
              const arr = dignity?.['operative_varga_rows']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const dignity = (root['content'] as Record<string, unknown> | undefined)?.['dignity'] as Record<string, unknown> | undefined
              if (dignity) dignity['operative_varga_rows'] = kept
            },
            minKeep: 2,
            recover: { instrument: 'ganita_condition_get', hint: 'full operative-varga dignity rows (D1/D9/D10/D60) — this response kept a lean slice. (SC-18: was "get_dignity", a non-existent MCP tool name; use facet="dignity").' },
            label: 'dignity.operative_varga_rows',
            // EL-36: the operative-varga dignity highlight IS the "how is my Saturn" answer —
            // hardFloor so PASS 2 can never zero it (the generic orientation preamble goes first).
            hardFloor: true,
          },
          {
            path: 'content.strength.rows',
            getArray: (root) => {
              const strength = (root['content'] as Record<string, unknown> | undefined)?.['strength'] as Record<string, unknown> | undefined
              const arr = strength?.['rows']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const strength = (root['content'] as Record<string, unknown> | undefined)?.['strength'] as Record<string, unknown> | undefined
              if (strength) strength['rows'] = kept
            },
            minKeep: 4,
            recover: { instrument: 'ganita_strength_get', hint: 'full shadbala decomposition (this response kept a lean slice of the 6-component + vimsopaka + ishta/kashta breakdown). (SC-18: was "get_strength", a non-existent MCP tool name).' },
            label: 'strength.rows',
            hardFloor: true, // EL-36: confirmed shadbala — protected from PASS 2 zeroing.
          },
          {
            path: 'content.avasthas.rows',
            getArray: (root) => {
              const avasthas = (root['content'] as Record<string, unknown> | undefined)?.['avasthas'] as Record<string, unknown> | undefined
              const arr = avasthas?.['rows']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const avasthas = (root['content'] as Record<string, unknown> | undefined)?.['avasthas'] as Record<string, unknown> | undefined
              if (avasthas) avasthas['rows'] = kept
            },
            minKeep: 3,
            recover: { instrument: 'ganita_condition_get', hint: 'full avastha rows across all five systems (baladi/jagrad/deepta/lajjitadi/sayanadi). (SC-18: was "get_avasthas", a non-existent MCP tool name; use facet="avasthas").' },
            label: 'avasthas.rows',
            hardFloor: true, // EL-36: confirmed deterministic avasthas — protected from PASS 2 zeroing.
          },
          {
            path: 'content.yogas.catalog_yoga_matches',
            getArray: (root) => {
              const yogas = (root['content'] as Record<string, unknown> | undefined)?.['yogas'] as Record<string, unknown> | undefined
              const arr = yogas?.['catalog_yoga_matches']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const yogas = (root['content'] as Record<string, unknown> | undefined)?.['yogas'] as Record<string, unknown> | undefined
              if (yogas) yogas['catalog_yoga_matches'] = kept
            },
            minKeep: 3,
            recover: { instrument: 'bodha_signals_get', hint: 'full signal_type_class=yoga MSR matches for this graha.' },
            label: 'yogas.catalog_yoga_matches',
          },
          {
            path: 'content.yogas.catalog_dosha_matches',
            getArray: (root) => {
              const yogas = (root['content'] as Record<string, unknown> | undefined)?.['yogas'] as Record<string, unknown> | undefined
              const arr = yogas?.['catalog_dosha_matches']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const yogas = (root['content'] as Record<string, unknown> | undefined)?.['yogas'] as Record<string, unknown> | undefined
              if (yogas) yogas['catalog_dosha_matches'] = kept
            },
            minKeep: 3,
            recover: { instrument: 'bodha_signals_get', hint: 'full signal_type_class=dosha MSR matches for this graha.' },
            label: 'yogas.catalog_dosha_matches',
          },
          {
            // R5.1 C1 fix (live-verifier finding #1): the THIRD array inside content.yogas —
            // parivartana_exchanges — was the one missed the first time (catalog_yoga_matches
            // and catalog_dosha_matches were already declared above). Live measurement showed
            // the whole content.yogas block at 10,784 bytes untrimmed for Saturn/native —
            // bigger than the entire 12KB ceiling on its own.
            path: 'content.yogas.parivartana_exchanges',
            getArray: (root) => {
              const yogas = (root['content'] as Record<string, unknown> | undefined)?.['yogas'] as Record<string, unknown> | undefined
              const arr = yogas?.['parivartana_exchanges']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const yogas = (root['content'] as Record<string, unknown> | undefined)?.['yogas'] as Record<string, unknown> | undefined
              if (yogas) yogas['parivartana_exchanges'] = kept
            },
            minKeep: 3,
            recover: { instrument: 'bodha_signals_get', hint: 'full signal_type_class=parivartana MSR matches for this graha (structural exchange yogas).' },
            label: 'yogas.parivartana_exchanges',
            // EL-36 + §N.6: parivartana exchanges are served as REAL chart-specific data
            // (confirmed, not requires_pass catalog labels) — hardFloor. The catalog_yoga_/
            // catalog_dosha_matches arrays above are lower-density catalog labels and stay
            // floorable-to-zero (trimmed before this confirmed section).
            hardFloor: true,
          },
          {
            path: 'content.cgm_neighborhood.edges',
            getArray: (root) => {
              const cgm = (root['content'] as Record<string, unknown> | undefined)?.['cgm_neighborhood'] as Record<string, unknown> | undefined
              const arr = cgm?.['edges']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const cgm = (root['content'] as Record<string, unknown> | undefined)?.['cgm_neighborhood'] as Record<string, unknown> | undefined
              if (cgm) cgm['edges'] = kept
            },
            minKeep: 3,
            recover: { instrument: 'bodha_graph_traverse_get', hint: 'full CGM edge set (this response kept a lean slice of the depth-1 neighborhood).' },
            label: 'cgm_neighborhood.edges',
            hardFloor: true, // EL-36: confirmed CGM structure — protected from PASS 2 zeroing.
          },
          {
            path: 'content.cgm_neighborhood.nodes',
            getArray: (root) => {
              const cgm = (root['content'] as Record<string, unknown> | undefined)?.['cgm_neighborhood'] as Record<string, unknown> | undefined
              const arr = cgm?.['nodes']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const cgm = (root['content'] as Record<string, unknown> | undefined)?.['cgm_neighborhood'] as Record<string, unknown> | undefined
              if (cgm) cgm['nodes'] = kept
            },
            minKeep: 3,
            recover: { instrument: 'bodha_graph_traverse_get', hint: 'full CGM node set (this response kept a lean slice of the depth-1 neighborhood).' },
            label: 'cgm_neighborhood.nodes',
            hardFloor: true, // EL-36: confirmed CGM structure — protected from PASS 2 zeroing.
          },
          {
            // R5.1 C1 fix: even with every data section above floored to 0, live
            // measurement showed graha_portrait still ~270-300 bytes over the 12KB
            // ceiling — this small provenance array (8 tool URIs, purely documentation,
            // not classical/astrological content) was the remaining lever.
            path: 'content.provenance.synthesis_of',
            getArray: (root) => {
              const provenance = (root['content'] as Record<string, unknown> | undefined)?.['provenance'] as Record<string, unknown> | undefined
              const arr = provenance?.['synthesis_of']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const provenance = (root['content'] as Record<string, unknown> | undefined)?.['provenance'] as Record<string, unknown> | undefined
              if (provenance) provenance['synthesis_of'] = kept
            },
            minKeep: 0,
            recover: { instrument: 'graha_portrait', hint: 'full provenance.synthesis_of tool-URI list (documentation only, not chart data).' },
            label: 'provenance.synthesis_of',
          },
          {
            // R5.1 C1 fix: live cross-chart verification (Venus/Abhinandan) found
            // position.rows alone at 3636 bytes — NOT declared trimmable at all in the
            // first pass (the native/Saturn case happened to have only 1 row here, which
            // is why this gap wasn't caught testing that chart alone — a genuine
            // per-chart data-shape difference, not a bug in the trim logic itself).
            path: 'content.position.rows',
            getArray: (root) => {
              const position = (root['content'] as Record<string, unknown> | undefined)?.['position'] as Record<string, unknown> | undefined
              const arr = position?.['rows']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const position = (root['content'] as Record<string, unknown> | undefined)?.['position'] as Record<string, unknown> | undefined
              if (position) position['rows'] = kept
            },
            minKeep: 1,
            recover: { instrument: 'ganita_positions_get', hint: 'full position rows for this graha across every category.' },
            label: 'position.rows',
            hardFloor: true, // EL-36: the graha's position is the irreducible core of the portrait.
          },
          {
            path: 'content.functional_nature.rows',
            getArray: (root) => {
              const fn = (root['content'] as Record<string, unknown> | undefined)?.['functional_nature'] as Record<string, unknown> | undefined
              const arr = fn?.['rows']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const fn = (root['content'] as Record<string, unknown> | undefined)?.['functional_nature'] as Record<string, unknown> | undefined
              if (fn) fn['rows'] = kept
            },
            minKeep: 1,
            recover: { instrument: 'ganita_condition_get', hint: 'full functional-class rows for this graha across ascendant variants. (SC-18: was "get_dignity", a non-existent MCP tool name; use facet="dignity").' },
            label: 'functional_nature.rows',
            hardFloor: true, // EL-36: benefic/malefic/yoga-karaka classification — confirmed core.
          },
          {
            path: 'content.dashas.rows',
            getArray: (root) => {
              const dashas = (root['content'] as Record<string, unknown> | undefined)?.['dashas'] as Record<string, unknown> | undefined
              const arr = dashas?.['rows']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const dashas = (root['content'] as Record<string, unknown> | undefined)?.['dashas'] as Record<string, unknown> | undefined
              if (dashas) dashas['rows'] = kept
            },
            minKeep: 2,
            recover: { instrument: 'ganita_dashas_get', hint: 'full Mahadasha-level dasha periods for this graha (1900-2100 window kept only a lean slice).' },
            label: 'dashas.rows',
            hardFloor: true, // EL-36: confirmed Mahadasha windows — protected from PASS 2 zeroing.
          },
        ]

        if (format !== 'v3') {
          const legacyResponse = { orientation_context, orientation_ok, ...envelope(inner, 'graha_portrait') }
          const legacyBudgeted = applyMcpBudget(legacyResponse, resolveMaxKb('graha_portrait', budget_kb, verbosity), portraitSections, budget_kb)
          // EL-36 residual (R-21 receipt integrity, extended to the legacy escape hatch):
          // the v3 path below reconciles `completeness` against what actually survived
          // applyMcpBudget's trim; the legacy shape carries the SAME `content.completeness`
          // object (envelope()'s legacy branch wraps `inner` as `content` verbatim — see
          // buildRetrievalEnvelope/redactProvenanceTables, which returns the same reference
          // when entitled) so the identical reconciliation applies cleanly here too, reading
          // post-trim state from `legacyBudgeted` (never the pre-trim `inner`) so a section
          // PASS 2 floored to 0 never ships next to a stale "✓". No numeric receipt
          // (verdict.sections_populated / grounding.grounding_score) exists on the legacy
          // shape to re-derive — those are v3-only fields — so this is the complete legacy
          // reconciliation, not a partial one.
          const legacyContent = (legacyBudgeted as Record<string, unknown>)['content'] as Record<string, unknown> | undefined
          const legacyCompleteness = legacyContent?.['completeness'] as Record<string, unknown> | undefined
          if (legacyCompleteness) {
            reconcileReceiptWithTrimReport(legacyCompleteness, {
              dignity: ['content.dignity.all_varga_rows', 'content.dignity.other_rows', 'content.dignity.operative_varga_rows'],
              functional_nature: ['content.functional_nature.rows'],
              strength: ['content.strength.rows'],
              avasthas: ['content.avasthas.rows'],
              yogas: ['content.yogas.catalog_yoga_matches', 'content.yogas.catalog_dosha_matches', 'content.yogas.parivartana_exchanges'],
              dashas: ['content.dashas.rows'],
              position: ['content.position.rows'],
              cgm_neighborhood: ['content.cgm_neighborhood.edges', 'content.cgm_neighborhood.nodes'],
            }, legacyBudgeted['trim_report'] as TrimReportEntry[] | null | undefined)
          }
          return dualOutputBudgeted(legacyBudgeted)
        }

        // ── v3 population ─────────────────────────────────────────────────
        const completeness = (inner['completeness'] as Record<string, string> | undefined) ?? {}
        const errors = (inner['errors'] as Record<string, string> | undefined) ?? undefined
        const sectionsPopulated = Object.values(completeness).filter(v => v === '✓').length
        const sectionsRequested = Object.values(completeness).filter(v => v !== 'not_requested').length

        const positionRows = ((inner['position'] as Record<string, unknown> | undefined)?.['rows'] as Record<string, unknown>[] | undefined) ?? []
        const fact_ids = Array.from(new Set(positionRows.map(r => r['fact_id']).filter((v): v is string => typeof v === 'string')))

        const { chart_header, flags: chartHeaderFlags } = await resolveChartHeader(chart_id, resolvedAyanamsha, principal)

        // Pratinidhi-R ruling (R5.3 B2): the narration MUST be built from `inner` —
        // the UNTRIMMED capability output — BEFORE applyMcpBudget runs below, so it can
        // safely cite any fetched row even if that row is later trimmed off the wire.
        const grahaNameResolved = typeof inner['graha'] === 'string' ? inner['graha'] as string : graha
        const { narration, extraFactIds } = await buildGrahaPortraitNarration(
          chart_id, grahaNameResolved, chart_header?.lagna_sign ?? null, inner, principal,
        )
        // New budget headroom (Pratinidhi-R ruling): citation_ref is internal MCP-lineage
        // provenance, never a classical citation — strip it from every row now that
        // narration (which reads fact_id/fact_value_text/fact_value_jsonb, never
        // citation_ref) has already been built from the untouched `inner`.
        stripCitationRefDeep(inner)

        const fact_ids_grounded = Array.from(new Set([...fact_ids, ...extraFactIds]))
        const grounding = {
          fact_ids: fact_ids_grounded, citations: [],
          grounding_score: sectionsRequested > 0 ? Math.round((sectionsPopulated / sectionsRequested) * 1000) / 1000 : null,
        }

        const verdict = {
          graha: inner['graha'] ?? graha,
          graha_code: inner['graha_code'] ?? null,
          completeness,
          sections_populated: sectionsPopulated,
          sections_requested: sectionsRequested,
          narration,
          note: 'completeness uses the design §28.6 classical-units receipt vocabulary (✓ / zero_rows / error / not_requested) per section. narration is assembled from the sections already fetched by this same call (see grounding.fact_ids for the specific L1/L2 facts it cites) — never a new chart computation.',
        }

        const judgment_flags: JudgmentFlagEntry[] = [...chartHeaderFlags]
        if (errors && Object.keys(errors).length > 0) judgment_flags.push(judgmentFlag('partial_portrait_section_errors'))
        if (completeness['yogas'] === 'zero_rows') judgment_flags.push(judgmentFlag('no_parivartana_or_catalog_matches_for_graha'))
        if (completeness['dashas'] === 'zero_rows') judgment_flags.push(judgmentFlag('no_mahadasha_periods_for_graha'))

        // Typed per design §28.4 (R5 W3 Phase B) — additive `pointer_type` alongside the
        // pre-existing {instrument, hint} shape.
        const drill_pointers: { instrument: string; hint: string; pointer_type: DrillPointerType }[] = [
          { instrument: 'ganita_dashas_get', hint: 'Antardasha-level (level=2+) detail for this graha\'s Mahadasha periods, narrower window.', pointer_type: 'dasha_of_promise' },
          { instrument: 'bodha_graph_traverse_get', hint: 'deeper CGM traversal (depth>1, paths mode) from this graha\'s neighborhood.', pointer_type: 'dispositor_chain' },
          { instrument: 'bodha_signals_get', hint: 'raw MSR signal evidence for any yoga/dosha match surfaced here.', pointer_type: 'karaka_condition' },
          { instrument: 'judgment_query', hint: 'the complete bhava-level (7th-house marriage, 10th-house career, etc.) promise-register verdict — this entity-scoped call cannot fully adjudicate bhava claims on its own.', pointer_type: 'karaka_condition' },
        ]

        const v3Response = {
          orientation_context, orientation_ok,
          ...envelope(inner, 'graha_portrait', undefined, 'v3', { chart_header, verdict, grounding, drill_pointers, judgment_flags }),
        }
        const budgeted = applyMcpBudget(v3Response, resolveMaxKb('graha_portrait', budget_kb, verbosity), portraitSections, budget_kb)
        // R-21 fix: `completeness` was stamped '✓'/'zero_rows'/'error' from the PRE-TRIM
        // capability output; reconcile against what actually survived applyMcpBudget so a
        // section trimmed all the way to 0 rows is never served with a stale '✓'.
        reconcileReceiptWithTrimReport(completeness, {
          dignity: ['content.dignity.all_varga_rows', 'content.dignity.other_rows', 'content.dignity.operative_varga_rows'],
          functional_nature: ['content.functional_nature.rows'],
          strength: ['content.strength.rows'],
          avasthas: ['content.avasthas.rows'],
          yogas: ['content.yogas.catalog_yoga_matches', 'content.yogas.catalog_dosha_matches', 'content.yogas.parivartana_exchanges'],
          dashas: ['content.dashas.rows'],
          position: ['content.position.rows'],
          cgm_neighborhood: ['content.cgm_neighborhood.edges', 'content.cgm_neighborhood.nodes'],
        }, budgeted['trim_report'] as TrimReportEntry[] | null | undefined)
        // EL-36 receipt truth: reconcileReceiptWithTrimReport may have downgraded one or more
        // `completeness` marks from '✓' to a 'trimmed_to_empty …' string. The NUMERIC receipt
        // (verdict.sections_populated + grounding.grounding_score) was computed PRE-trim and
        // would now over-report sections that did not survive onto the wire — re-derive both
        // from the reconciled `completeness` so the counts and the marks agree. verdict is
        // stored by reference in the envelope (buildRetrievalEnvelope) so mutating it here lands
        // on the wire; grounding is rebuilt into a fresh object by the envelope, so its score is
        // written through `budgeted.grounding`. (This can only ever lower the count — a genuine
        // survivor keeps its '✓'.)
        const populatedAfterTrim = Object.values(completeness).filter(v => v === '✓').length
        if (populatedAfterTrim !== sectionsPopulated) {
          verdict.sections_populated = populatedAfterTrim
          const groundingBlock = (budgeted as Record<string, unknown>)['grounding'] as { grounding_score: number | null } | undefined
          if (groundingBlock) {
            groundingBlock.grounding_score = sectionsRequested > 0
              ? Math.round((populatedAfterTrim / sectionsRequested) * 1000) / 1000
              : null
          }
        }
        return dualOutputBudgeted(budgeted)
      } catch (err) {
        return errorOutput('graha_portrait', String(err), { chart_id, graha })
      }
    }
  )

  // ── pact_query (R5 W4, design §26/§28.3 — the PACT protocol as one chained ──
  // investigation) — marsys://tool/L-PACT/pact_query
  //
  // MANDATORY W2-lesson check (per the R5 run brief standing requirement): every
  // param the capability accepts (chart_id, ayanamsha_id, domain, bhava, as_of_date,
  // max_signals) is declared in this Zod schema AND explicitly threaded through the
  // callRegistryCapability args object below — none spread blindly. Verified against
  // register_d10_pact.ts's input_schema before wiring this call.
  server.tool(
    'pact_query',
    'THE PACT PROTOCOL (design §26/§28.3) as one chained investigation for event/timing ' +
    'questions — the classical predictive grammar "promise in the rashi → confirmation in ' +
    'the varga → activation in the dasha → trigger in the transit", walked stage by stage. ' +
    'HALTS HONESTLY the moment a stage is classically denied rather than fabricating the ' +
    'stages after it (B.10) — pact_status reports denied_at_promise / denied_at_confirmation / ' +
    'denied_at_activation / chain_pending_activation / chain_incomplete_infra / chain_complete. ' +
    '`chain_incomplete_infra` means all four stages were attempted but TRIGGER could not be ' +
    'evaluated (ephemeris sidecar unreachable/empty) — an infrastructure gap, distinct from ' +
    '`chain_complete` (all four stages ran AND TRIGGER data was actually fetched) and distinct ' +
    'from any classical denial. Stage 1 PROMISE runs ' +
    'judgment_query\'s full checklist verdict (design §28.1). Stage 2 CONFIRMATION checks the ' +
    'promise-carrying bhāveśa/kāraka\'s dignity IN the operative varga (e.g. D9 for marriage). ' +
    'Stage 3 ACTIVATION locates which Vimshottari mahadasha carries that lord/kāraka: active ' +
    'now, upcoming (pending — NOT a denial), or none found (denied). Stage 4 TRIGGER, only ' +
    'reached when ACTIVATION is active now, fetches the transiting tropical position for the ' +
    'activating graha(s) as an honest PARTIAL gate check (full sidereal vedha/aspect gating is ' +
    'a documented data-plane gap, reported not fabricated). Pass `domain` or `bhava` exactly ' +
    'as judgment_query accepts. response_format=\'v3\' (opt-in; default \'legacy\') returns the ' +
    'R5 unified envelope with typed drill_pointers carrying `pact_stage` metadata. ' +
    '[ṢAḌ-DARŚANA W0.4] Superseded by kala_explain_get (VIEW 6 EXPLAIN), which wraps this ' +
    'SAME capability on the elevated kala_* envelope (argument-shaped reading naming the ' +
    'weakest link, tri-plane pointers into UPĀYA/ELECT/AHEAD, coverage, freshness, ' +
    'calibration_maturity) — prefer kala_explain_get for new callers. This tool remains live, ' +
    'not retired.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      domain: z.string().optional().describe(
        'Life-domain name, resolved via judgment_query\'s shastra map (design §28.5): ' +
        'marriage/relationship/partnership, career/vocation, wealth/finance, health/vitality, ' +
        'progeny/children, education, spirituality. Takes precedence over `bhava` if both given.'
      ),
      bhava: z.number().int().min(1).max(12).optional().describe(
        'Bhava (house) number 1-12, same semantics as judgment_query. Required if `domain` is omitted.'
      ),
      as_of_date: z.string().optional().describe(
        'Date (YYYY-MM-DD) to evaluate ACTIVATION/TRIGGER as-of. Default: today.'
      ),
      response_format: z.enum(['legacy', 'v3']).optional().describe(
        "Envelope shape: 'legacy' (default, unchanged) or 'v3' (populated verdict/grounding/" +
        "drill_pointers/chart_header — opt-in until the R5 W4 battery flips the default)."
      ),
      max_signals: z.number().int().min(1).max(50).optional().describe(
        'Forwarded to judgment_query for the PROMISE stage (default: 15, max: 50).'
      ),
      verbosity: VERBOSITY_ZOD,
      budget_kb: BUDGET_KB_ZOD,
    },
    async ({ chart_id, ayanamsha_id, domain, bhava, as_of_date, response_format, max_signals, verbosity, budget_kb }) => {
      if (!chart_id) return errorOutput('pact_query', 'chart_id is required')
      if (!domain && bhava === undefined) {
        return errorOutput('pact_query', 'either `domain` or `bhava` is required')
      }
      try {
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        // R5.1 C1: 'v3' is now the MCP-channel DEFAULT for this instrument (an explicit
        // response_format:'legacy' remains the escape hatch to the pre-C1 hollow envelope).
        const format = resolveEnvelopeFormat(response_format ?? 'v3')

        // B.11: fetch holistic orientation alongside the PACT chain (S1: parallelized)
        const [{ orientation_context, orientation_ok }, raw] = await Promise.all([
          fetchOrientationContext(chart_id, resolvedAyanamsha, principal, verbosity),
          callRegistryCapability(
            'marsys://tool/L-PACT/pact_query',
            { chart_id, ayanamsha_id: resolvedAyanamsha, domain, bhava, as_of_date, max_signals },
            chart_id, principal
          ),
        ])
        const wrapper = raw as Record<string, unknown>
        const inner = (wrapper['content'] as Record<string, unknown>) ?? wrapper

        // R5.1 C1 — pact_query is already lean by construction (register_d10_pact.ts
        // deliberately does NOT re-embed judgment_query's full checklist — see that
        // file's header). The remaining levers: a stage-scoped array field (TRIGGER's
        // transiting_positions / CONFIRMATION's dignities / ACTIVATION's active_periods)
        // and the accumulated fact_id_refs. `findStageArraySection` targets exactly ONE
        // named field on exactly ONE named stage inside content.stages[] — never a
        // parallel resolver, purely a view into what pact_query already computed.
        const findStageArraySection = (
          stageName: string, field: string, minKeep: number, recover: { instrument: string; hint: string },
        ): TrimmableSection<Record<string, unknown>> => ({
          path: `content.stages[stage=${stageName}].${field}`,
          getArray: (root) => {
            const stagesArr = (root['content'] as Record<string, unknown> | undefined)?.['stages']
            if (!Array.isArray(stagesArr)) return undefined
            const stage = (stagesArr as Record<string, unknown>[]).find(s => s['stage'] === stageName)
            const arr = stage?.[field]
            return Array.isArray(arr) ? arr : undefined
          },
          setArray: (root, kept) => {
            const stagesArr = (root['content'] as Record<string, unknown> | undefined)?.['stages']
            if (!Array.isArray(stagesArr)) return
            const stage = (stagesArr as Record<string, unknown>[]).find(s => s['stage'] === stageName)
            if (stage) stage[field] = kept
          },
          minKeep,
          recover,
          label: `stages[${stageName}].${field}`,
        })
        const pactSections: TrimmableSection<Record<string, unknown>>[] = [
          findStageArraySection('TRIGGER', 'transiting_positions', 1, { instrument: 'ref_planet_transit_get', hint: 'full transit series across the activation window (this call fetched only the single as_of_date snapshot).' }),
          findStageArraySection('CONFIRMATION', 'dignities', 2, { instrument: 'ganita_condition_get', hint: 'full dignity rows for the promise-carrying graha(s) in the operative varga. (SC-18: was "get_dignity", a non-existent MCP tool name; use facet="dignity").' }),
          findStageArraySection('ACTIVATION', 'active_periods', 2, { instrument: 'ganita_dashas_get', hint: 'full dasha timeline for the promise-carrying graha(s).' }),
          {
            path: 'content.fact_id_refs',
            getArray: (root) => {
              const arr = (root['content'] as Record<string, unknown> | undefined)?.['fact_id_refs']
              return Array.isArray(arr) ? arr : undefined
            },
            setArray: (root, kept) => {
              const content = root['content'] as Record<string, unknown> | undefined
              if (content) content['fact_id_refs'] = kept
            },
            minKeep: 20,
            recover: { instrument: 'pact_query', hint: 'full fact_id_refs list (this response kept a lean slice; grounding.fact_ids in the envelope still reflects the full set).' },
            label: 'content.fact_id_refs',
          },
        ]

        if (format !== 'v3') {
          const legacyResponse = { orientation_context, orientation_ok, ...envelope(inner, 'pact_query') }
          return dualOutputBudgeted(applyMcpBudget(legacyResponse, resolveMaxKb('pact_query', budget_kb, verbosity), pactSections, budget_kb))
        }

        // ── v3 population ──────────────────────────────────────────────────
        const factIdRefs = (inner['fact_id_refs'] as string[]) ?? []
        const grounding = { fact_ids: factIdRefs, citations: [], grounding_score: null }
        const stages = (inner['stages'] as Record<string, unknown>[]) ?? []
        const pactStatus = inner['pact_status'] as string | undefined

        // R-22 fix: echo the REQUESTED as_of_date (falling back to the resolved/defaulted value the
        // capability actually evaluated against), not envelope()'s own new-Date()-at-response-time
        // default. Declared here (ahead of the verdict) because CR-15's MD derivation keys on it.
        const resolvedAsOfDate = (inner['as_of_date'] as string | undefined) ?? as_of_date

        // CR-15 (D-2 V-3, ledger row 27): NAME the true running Mahādaśā lord. The PACT chain's
        // ACTIVATION stage locates which dasha carries the promise but the served verdict never
        // named the CURRENT MD lord — a caller could not tell whose period is actually running.
        // Derive it deterministically from the level-1 Vimśottarī spine (get_dashas), §N.5 canonical
        // values, relative to the same as_of_date the chain evaluated. This is a view over data the
        // estate already computes — no re-derivation of the dasha itself.
        let mahadasha: {
          current_lord: string | null; current_from: string | null; current_to: string | null
          next_lord: string | null; next_from: string | null; as_of: string | null
          note: string
        } | null = null
        try {
          const asOf = resolvedAsOfDate ?? new Date().toISOString().slice(0, 10)
          const mdRaw = await callRegistryCapability(
            'marsys://tool/L1/get_dashas',
            { chart_id, ayanamsha_id: resolvedAyanamsha, system: 'vimshottari', level: 1, all_levels: false, fields: 'compact' },
            chart_id, principal,
          ) as Record<string, unknown>
          const mdContent = (mdRaw?.['content'] as Record<string, unknown>) ?? mdRaw
          const mdRows = (Array.isArray(mdContent?.['rows']) ? mdContent['rows'] : []) as Record<string, unknown>[]
          const l1 = mdRows
            .filter(r => Number(r['level_n']) === 1 && r['start_date'] && r['end_date'])
            .sort((a, b) => String(a['start_date']).localeCompare(String(b['start_date'])))
          const curIdx = l1.findIndex(r => String(r['start_date']) <= asOf && asOf < String(r['end_date']))
          const cur = curIdx >= 0 ? l1[curIdx] : undefined
          if (cur) {
            const nxt = l1[curIdx + 1]
            mahadasha = {
              current_lord: (cur['lord_graha'] as string) ?? null,
              current_from: (cur['start_date'] as string) ?? null,
              current_to: (cur['end_date'] as string) ?? null,
              next_lord: (nxt?.['lord_graha'] as string) ?? null,
              next_from: (nxt?.['start_date'] as string) ?? null,
              as_of: asOf,
              note: 'Running Vimśottarī Mahādaśā lord as of as_of_date (level-1 spine, §N.5 canonical). ' +
                'The PACT ACTIVATION stage tells you whether the promise-carrying graha is favored by THIS period.',
            }
          }
        } catch {
          mahadasha = null // MD naming is enrichment — a failure here must not break the chain.
        }

        const verdict = {
          pact_status: pactStatus,
          stages_completed: stages.length,
          stages: stages.map(s => ({ stage: s['stage'], status: s['status'] })),
          mahadasha, // CR-15: the named running MD lord (+ next), or null if underivable.
          note: 'Chain-honesty verdict (design §30 W4 acceptance): a denied stage halts the chain — ' +
            'stages_completed < 4 with pact_status starting "denied_at_" is a CORRECT honest halt, ' +
            'not a failure. pact_status="chain_complete" means all four stages ran, TRIGGER data ' +
            'was actually fetched, and fact_id_refs are cited. R-22: "chain_incomplete_infra" means ' +
            'all four stages were ATTEMPTED (stages_completed may read 4) but TRIGGER could not be ' +
            'evaluated (ephemeris sidecar unreachable/empty) — do not read stages_completed alone ' +
            'as proof of a passed chain; always check pact_status.',
        }

        const judgment_flags = (inner['judgment_flags'] as JudgmentFlagEntry[]) ?? []
        const drill_pointers = (inner['drill_pointers'] as { instrument: string; hint: string; pointer_type?: DrillPointerType; pact_stage?: PactStage }[]) ?? []

        const { chart_header, flags: chartHeaderFlags } = await resolveChartHeader(chart_id, resolvedAyanamsha, principal)
        judgment_flags.push(...chartHeaderFlags)

        const v3Response = {
          orientation_context, orientation_ok,
          ...envelope(inner, 'pact_query', undefined, 'v3', {
            chart_header, verdict, grounding, drill_pointers, judgment_flags,
            as_of_date: resolvedAsOfDate,
          }),
        }
        return dualOutputBudgeted(applyMcpBudget(v3Response, resolveMaxKb('pact_query', budget_kb, verbosity), pactSections, budget_kb))
      } catch (err) {
        return errorOutput('pact_query', String(err), { chart_id })
      }
    }
  )

  // ── ṢAḌ-DARŚANA — all nine kala_* view/capability facades (brief §2 file map) ────
  // Consolidated into ONE call (post-Night-2 hygiene fix; see kala_views/register_all.ts's
  // docstring). "One canonical registration per tool, asserted by test" (brief §2) still
  // holds — each tool's server.tool() call is reached from exactly one place, now inside
  // register_all.ts rather than scattered across this shared, multi-campaign file.
  registerAllKalaViews(server, principal)
}

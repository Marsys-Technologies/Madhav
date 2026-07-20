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
import { finalizeMcpBudget, autoDetectTrimmableSections, type TrimmableSection } from '../lib/response_budget.js'

// ── Platform URL (for proxy calls to the platform API) ───────────────────────

const PLATFORM_URL = (
  process.env['PLATFORM_URL'] ?? 'http://localhost:3000'
).replace(/\/$/, '')

// Service-to-service token — must match MCP_INTERNAL_TOKEN on amjis-web.
// Required by /api/retrieval/capability (F1 gate, M0.5).
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Ayanamsha normalization (F-006/F-011/F-031) ───────────────────────────────
// Signals are stored under 'lahiri_chitrapaksha'. Tools historically defaulted
// to 'LAHIRI' causing a join mismatch → 0 rows. This map aliases all known
// spellings to the canonical stored id so default + explicit calls both work.
const AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri:               'lahiri_chitrapaksha',
  lahiri_chitrapaksha:  'lahiri_chitrapaksha',
  lahiri_chitra:        'lahiri_chitrapaksha',
  true_chitra:          'lahiri_chitrapaksha',
  true_citra:           'lahiri_chitrapaksha',
  LAHIRI:               'lahiri_chitrapaksha',
  Lahiri:               'lahiri_chitrapaksha',
}
const DEFAULT_AYANAMSHA = 'lahiri_chitrapaksha'

function normalizeAyanamsha(id?: string): string {
  if (!id) return DEFAULT_AYANAMSHA
  return AYANAMSHA_ALIAS[id] ?? id
}

// WP-1.3(f) / LCA-3 (ayanamsha reachability). chart_facts stores SIX distinct ayanamsha_id
// values — five sidereal (lahiri_chitrapaksha, krishnamurti, raman, surya_siddhanta_classical,
// true_chitra) plus INVARIANT (ayanamsha-independent facts). The shared `normalizeAyanamsha`
// above COLLAPSES `true_chitra`/`true_citra` -> `lahiri_chitrapaksha` (AYANAMSHA_ALIAS), which
// made true_chitra's own 27,112-row dataset UNREACHABLE via query_chart_facts (the tool
// effectively served ≤5 of 6 ayanamshas, and the two Chitra-family names both bound to lahiri).
// This resolver is SCOPED to query_chart_facts (it must not change the shared normalizer used
// by the dasha/signals tools, which are a parallel lane): it maps convenience aliases to the
// canonical id WITHOUT collapsing any two distinct stored ayanamshas together, so every one of
// the 6 is reachable. Unknown ids pass through unchanged (the handler then returns an honest
// empty result rather than silently querying lahiri).
const CHART_FACTS_AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri:                    'lahiri_chitrapaksha',
  lahiri_chitra:             'lahiri_chitrapaksha',
  lahiri_chitrapaksha:       'lahiri_chitrapaksha',
  kp:                        'krishnamurti',
  krishnamurti:              'krishnamurti',
  raman:                     'raman',
  surya_siddhanta:           'surya_siddhanta_classical',
  surya_siddhanta_classical: 'surya_siddhanta_classical',
  true_chitra:               'true_chitra',
  true_citra:                'true_chitra',
  chitra:                    'true_chitra',
  invariant:                 'INVARIANT',
}
export function resolveChartFactsAyanamsha(id?: string): string {
  if (!id) return DEFAULT_AYANAMSHA
  return CHART_FACTS_AYANAMSHA_ALIAS[id] ?? CHART_FACTS_AYANAMSHA_ALIAS[id.toLowerCase()] ?? id
}

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
} as const

/**
 * A trimmable section targeting `orientation_context.entity_profiles` — shared by every
 * B.11-orienting tool response (get_chart_orientation's own digest output, pre-fetched
 * alongside each of these three instruments). Kept small (floor 3) since orientation is a
 * frame, not the point of these calls — get_chart_orientation itself remains the full-
 * detail path.
 */
function orientationEntityProfilesSection(): TrimmableSection<Record<string, unknown>> {
  return {
    path: 'orientation_context.entity_profiles',
    getArray: (root) => {
      const oc = root['orientation_context'] as Record<string, unknown> | undefined
      const arr = oc?.['entity_profiles']
      return Array.isArray(arr) ? arr : undefined
    },
    setArray: (root, kept) => {
      const oc = root['orientation_context'] as Record<string, unknown> | undefined
      if (oc) oc['entity_profiles'] = kept
    },
    minKeep: 3,
    recover: { instrument: 'get_chart_orientation', hint: 'full entity_profiles digest (this call kept only a lean slice to fit the MCP response budget).' },
    label: 'orientation_context.entity_profiles',
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
): T {
  const allSections = [...sections, orientationEntityProfilesSection() as unknown as TrimmableSection<T>]
  return finalizeMcpBudget(response, { maxKb, sections: allSections })
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
): T {
  const autoSections = autoDetectTrimmableSections(response, toolName)
  const allSections = [...autoSections, orientationEntityProfilesSection() as unknown as TrimmableSection<T>]
  return finalizeMcpBudget(response, { maxKb, sections: allSections })
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
async function fetchOrientationContext(
  chart_id: string,
  ayanamsha_id: string | undefined,
  principal: Principal,
): Promise<{ orientation_context: unknown; orientation_ok: boolean }> {
  try {
    const ucdData = await callRegistryCapability(
      'marsys://tool/L2/query_ucd',
      { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), top_k_signals: 10, response_format: 'digest' },
      chart_id, principal,
    )
    return { orientation_context: ucdData, orientation_ok: true }
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
    },
    async ({ chart_id, ayanamsha_id, top_k_signals, top_k_entities, response_format, envelope_format }) => {
      if (!chart_id) return errorOutput('get_chart_orientation', 'chart_id is required')
      try {
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        const fmt = response_format ?? 'summary'
        const format = resolveEnvelopeFormat(envelope_format)
        const raw = await callRegistryCapability(
          'marsys://tool/L2/query_ucd',
          { chart_id, ayanamsha_id: resolvedAyanamsha, top_k_signals: top_k_signals ?? 20,
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
          return dualOutput(envelope(bounded, 'get_chart_orientation'))
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
          { instrument: 'get_signals', hint: 'atomic composite-ranked signal drill for any entity_profiles.top_signal_ids.', pointer_type: 'other' },
          { instrument: 'get_domain_reading', hint: 'domain-conditioned reading for a specific life domain.', pointer_type: 'other' },
        ]

        let chart_header: ChartHeader | null = null
        try {
          chart_header = await callRegistryCapability(
            'marsys://tool/L1/get_chart_header', { chart_id, ayanamsha_id: resolvedAyanamsha }, chart_id, principal
          ) as ChartHeader
        } catch {
          chart_header = null
        }

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

        return dualOutput(
          envelope(bounded, 'get_chart_orientation', undefined, 'v3',
            { chart_header, verdict, ranking_basis: rankingBasis, grounding, drill_pointers, judgment_flags, coverage })
        )
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
    },
    async ({ chart_id, domain, ayanamsha_id, cursor, max_lenses, max_signals_per_lens, max_signal_refs, response_format }) => {
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
        return dualOutput({
          orientation_context,
          orientation_ok,
          ...inner,
          question_lenses: boundedLenses,
          lenses_total: lenses.length,
          lenses_returned: boundedLenses.length,
          token_safety_note: `Bounded to ${maxLenses} lenses × ${maxSig} signals. Pass max_lenses=12 + max_signals_per_lens=100 for full payload.`,
        })
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
    },
    async ({ chart_id, ayanamsha_id, domain, min_salience, limit, cursor, lel_enabled, response_format, frame, paradigm }) => {
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
          return dualOutput({
            orientation_context, orientation_ok,
            ...envelope(inner, 'get_signals', { offset: resolvedOffset, limit: resolvedLimit, total: null }),
          })
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
          { instrument: 'get_chart_orientation', hint: 'entity_profiles for the hierarchically-aggregated, same-pipeline orient view (design §E-6).', pointer_type: 'other' },
          { instrument: 'get_cgm_subgraph', hint: 'traverse causal context from these signal_ids.', pointer_type: 'dispositor_chain' },
        ]

        let chart_header: ChartHeader | null = null
        try {
          chart_header = await callRegistryCapability(
            'marsys://tool/L1/get_chart_header', { chart_id, ayanamsha_id: resolvedAyanamsha }, chart_id, principal
          ) as ChartHeader
        } catch {
          chart_header = null // frame-safety header is best-effort; never fails the instrument
        }

        const filterLabel = [
          domain ? `domain=${domain}` : null,
          paradigm ? `paradigm=${paradigm}` : null,
        ].filter(Boolean).join(',')
        const coverage: CoverageStamp = {
          family: `msr_signals${filterLabel ? `[${filterLabel}]` : ''}`,
          served: signals.length,
          total: totalMatchingFilters,
        }

        return dualOutput({
          orientation_context, orientation_ok,
          ...envelope(inner, 'get_signals', { offset: resolvedOffset, limit: resolvedLimit, total: totalMatchingFilters },
            'v3', { chart_header, verdict, ranking_basis: rankingBasis, grounding, drill_pointers, judgment_flags, coverage }),
        })
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
    },
    async ({ chart_id, seed_signal_ids, mode, depth, about, about_from, about_to, direction, min_strength }) => {
      if (!chart_id) return errorOutput('traverse_graph', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before graph traversal (S1: parallelized)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, undefined, principal),
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
        return dualOutputBudgeted(applyMcpBudgetAuto(response, MCP_RESPONSE_BUDGET_KB.traverse_graph, 'traverse_graph'))
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
    },
    async ({ chart_id, ayanamsha_id, planet, frame }) => {
      if (!chart_id) return errorOutput('get_positions', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L1/get_positions',
          { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), planet, frame },
          chart_id, principal
        )
        return dualOutput(data)
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
    },
    async ({ chart_id, ayanamsha_id, system_id, date_from, limit, cursor }) => {
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
        return dualOutput(data)
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
    },
    async ({ chart_id, ayanamsha_id, date_from, date_to, as_of, include_convergence }) => {
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
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
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
    },
    async ({ chart_id, ayanamsha_id, domain, horizon_years, max_projections }) => {
      if (!chart_id) return errorOutput('get_projections', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before predictive projection (S1: parallelized)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal),
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
        return dualOutputBudgeted(applyMcpBudgetAuto(response, MCP_RESPONSE_BUDGET_KB.get_projections, 'get_projections'))
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
    },
    async ({ query, text_ids, limit, cursor }) => {
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L0/query_classical_texts',
          { query, text_ids, limit: limit ?? 5, cursor }, undefined, principal,
        )
        return dualOutput(data)
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
    },
    async ({ chart_id, domain, remedy_type }) => {
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
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
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
    },
    async ({ chart_id }) => {
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
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
      } catch (err) {
        return errorOutput('get_chart_quality', String(err), { chart_id })
      }
    }
  )

  // ── list_assets (asset catalog) ───────────────────────────────────────────
  // marsys://resource/asset-registry/all
  // Global scope — no chart_id required
  server.tool(
    'list_assets',
    {
      layer: z.string().optional().describe('Filter by layer: L0, L1, L2, L3, L4, L5'),
      limit: z.number().int().min(1).max(200).optional().describe('Max assets (default: 81)'),
      cursor: z.string().optional().describe('Pagination cursor'),
    },
    async ({ layer, limit, cursor }) => {
      try {
        // list_assets → platform cockpit registry (direct HTTP; no @/ import possible)
        const data = await callRegistryCapability(
          'marsys://resource/asset-registry/all',
          { layer, limit: limit ?? 81, cursor }, undefined, principal
        )
        return dualOutput({ ...(data as Record<string, unknown>), pagination: { cursor, limit } })
      } catch (err) {
        return errorOutput('list_assets', String(err))
      }
    }
  )

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
    },
    async ({ chart_id, ayanamsha_id, max_signals_per_lens, max_contradictions }) => {
      if (!chart_id) return errorOutput('assess_marriage', 'chart_id is required')
      try {
        // S1 fix: orientation + domain assessment parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal),
          callRegistryCapability(
            'marsys://tool/L-DOMAIN/assess_marriage',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
              ...(max_signals_per_lens != null ? { max_signals_per_lens } : {}),
              ...(max_contradictions != null ? { max_contradictions } : {}) },
            chart_id, principal
          ),
        ])
        const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
        return dualOutputBudgeted(applyMcpBudgetAuto(response, MCP_RESPONSE_BUDGET_KB.assess_marriage, 'assess_marriage'))
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
    },
    async ({ chart_id, ayanamsha_id, max_signals_per_lens, max_contradictions }) => {
      if (!chart_id) return errorOutput('assess_career', 'chart_id is required')
      try {
        // S1 fix: orientation + domain assessment parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal),
          callRegistryCapability(
            'marsys://tool/L-DOMAIN/assess_career',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
              ...(max_signals_per_lens != null ? { max_signals_per_lens } : {}),
              ...(max_contradictions != null ? { max_contradictions } : {}) },
            chart_id, principal
          ),
        ])
        const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
        return dualOutputBudgeted(applyMcpBudgetAuto(response, MCP_RESPONSE_BUDGET_KB.assess_career, 'assess_career'))
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
    },
    async ({ chart_id, ayanamsha_id, max_signals_per_lens, max_contradictions }) => {
      if (!chart_id) return errorOutput('assess_health', 'chart_id is required')
      try {
        // S1 fix: orientation + domain assessment parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal),
          callRegistryCapability(
            'marsys://tool/L-DOMAIN/assess_health',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
              ...(max_signals_per_lens != null ? { max_signals_per_lens } : {}),
              ...(max_contradictions != null ? { max_contradictions } : {}) },
            chart_id, principal
          ),
        ])
        const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
        return dualOutputBudgeted(applyMcpBudgetAuto(response, MCP_RESPONSE_BUDGET_KB.assess_health, 'assess_health'))
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
    },
    async ({ chart_id, ayanamsha_id, max_signals_per_lens, max_contradictions }) => {
      if (!chart_id) return errorOutput('assess_wealth', 'chart_id is required')
      try {
        // S1 fix: orientation + domain assessment parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal),
          callRegistryCapability(
            'marsys://tool/L-DOMAIN/assess_wealth',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
              ...(max_signals_per_lens != null ? { max_signals_per_lens } : {}),
              ...(max_contradictions != null ? { max_contradictions } : {}) },
            chart_id, principal
          ),
        ])
        const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
        return dualOutputBudgeted(applyMcpBudgetAuto(response, MCP_RESPONSE_BUDGET_KB.assess_wealth, 'assess_wealth'))
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
    },
    async ({ chart_id, ayanamsha_id, dasha_period, date_from, date_to, top_k, min_salience }) => {
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
        return dualOutput(data)
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
    },
    async ({ chart_id, mode, seed_node_ids, depth, seed_node, target_node, query_text, ayanamsha_id, about, about_from, about_to, direction, min_strength }) => {
      if (!chart_id) return errorOutput('get_cgm_subgraph', 'chart_id is required')
      try {
        // S1 fix: orientation + graph traversal parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal),
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
        return dualOutputBudgeted(applyMcpBudgetAuto(response, MCP_RESPONSE_BUDGET_KB.get_cgm_subgraph, 'get_cgm_subgraph'))
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
    },
    async ({ chart_id, ayanamsha_id, about, category, planet, house, sign, nakshatra, divisional_chart, keyword, fact_subject, shape, limit, offset }) => {
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
        return dualOutput(data)
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
    'The compact "show me the chart" answer: a 12-rashi D1 (rashi chart) text grid — every graha\'s sign + degree-in-sign, Lagna sign clearly marked — sized for direct display in a chat client (hard-capped at 2KB). Pass include_navamsa=true to ALSO get the D9 (navamsa) grid in the same response — D9 is never included by default. Renders already-computed chart_divisionals positions; no new computation. chart_id is required.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      include_navamsa: z.boolean().optional().describe('Also include the D9 (navamsa) grid. Default: false (D1 only).'),
    },
    async ({ chart_id, ayanamsha_id, include_navamsa }) => {
      if (!chart_id) return errorOutput('chart_snapshot', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L1/chart_snapshot',
          {
            chart_id,
            ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
            ...(include_navamsa != null ? { include_navamsa } : {}),
          },
          chart_id, principal
        )
        return dualOutput(data)
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
    },
    async ({ chart_id, ayanamsha_id }) => {
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
        return dualOutput(data)
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
    },
    async ({ query_text, top_k, doc_type }) => {
      if (!query_text) return errorOutput('vector_search', 'query_text is required')
      try {
        const data = await callPlatformPrimitive('vector_search', {
          query_text,
          top_k: top_k ?? 10,
          ...(doc_type ? { doc_type } : {}),
        }, principal)
        return dualOutput(unwrapDoubleEncodedToolBundleResults(data))
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
    },
    async ({ chart_id, ayanamsha_id, domain, bhava, response_format, max_signals }) => {
      if (!chart_id) return errorOutput('judgment_query', 'chart_id is required')
      if (!domain && bhava === undefined) {
        return errorOutput('judgment_query', 'either `domain` or `bhava` is required')
      }
      try {
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        // R5.1 C1: 'v3' is now the MCP-channel DEFAULT for this instrument (an explicit
        // response_format:'legacy' remains the escape hatch to the pre-C1 hollow envelope).
        const format = resolveEnvelopeFormat(response_format ?? 'v3')

        // B.11: fetch holistic orientation alongside the judgment recipe (S1: parallelized)
        const [{ orientation_context, orientation_ok }, raw] = await Promise.all([
          fetchOrientationContext(chart_id, resolvedAyanamsha, principal),
          callRegistryCapability(
            'marsys://tool/L-JUDGMENT/judgment_query',
            { chart_id, ayanamsha_id: resolvedAyanamsha, domain, bhava, max_signals },
            chart_id, principal
          ),
        ])
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
            recover: { instrument: 'get_signals', hint: 'full yoga+dosha+karaka_alignment signal set beyond the lean slice kept here — pass domain + a higher top_k. (SC-18: was "query_signals", a non-existent MCP tool name).' },
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
            recover: { instrument: 'get_signals', hint: 'full adverse-valence (malefic/mixed) signal set for this domain beyond the lean threat-layer slice kept here — pass domain + a higher top_k.' },
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
            recover: { instrument: 'get_dashas', hint: 'full current-period rows across all dasha levels (this call kept a lean slice).' },
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
            recover: { instrument: 'get_dashas', hint: 'full multi-level dasha timeline for the bhāveśa/kāraka(s) (this call kept a lean slice of mahadasha windows only).' },
            label: 'checklist.timing_hooks.mahadasha_windows_by_graha',
          },
        ]

        if (format !== 'v3') {
          const legacyResponse = { orientation_context, orientation_ok, ...envelope(inner, 'judgment_query') }
          return dualOutputBudgeted(applyMcpBudget(legacyResponse, MCP_RESPONSE_BUDGET_KB.judgment_query, judgmentSections))
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

        let chart_header: ChartHeader | null = null
        try {
          chart_header = await callRegistryCapability(
            'marsys://tool/L1/get_chart_header', { chart_id, ayanamsha_id: resolvedAyanamsha }, chart_id, principal
          ) as ChartHeader
        } catch {
          chart_header = null
        }

        const v3Response = {
          orientation_context, orientation_ok,
          ...envelope(inner, 'judgment_query', undefined, 'v3', {
            chart_header, verdict, grounding, drill_pointers, judgment_flags,
          }),
        }
        const budgeted = applyMcpBudget(v3Response, MCP_RESPONSE_BUDGET_KB.judgment_query, judgmentSections)
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
  const SHADBALA_REQUIRED_RUPAS: Record<string, number> = {
    Sun: 5.0, Moon: 6.0, Mars: 5.0, Mercury: 7.0, Jupiter: 6.5, Venus: 5.5, Saturn: 5.0,
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

  function buildGrahaPortraitNarration(
    chartId: string, grahaName: string, lagnaSign: string | null, inner: Record<string, unknown>,
  ): { narration: string; extraFactIds: string[] } {
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
          } else {
            sentences.push(
              `Neecha-bhanga checked against the dispositor-chain data this portrait retrieves: dispositor ` +
              `${dispositor} is not present in the depth-1 cgm_neighborhood returned here — no cancellation ` +
              `condition met in what's available; a full multi-condition audit needs deeper dispositor-chain ` +
              `traversal (see drill_pointers).`,
            )
          }
        }
      }
    } else if (d9) {
      const fid9 = factIdOf(d9); if (fid9) extraFactIds.push(fid9)
      sentences.push(`In D9: ${describeVargaRow(d9)}.`)
    }

    // ── shadbala ───────────────────────────────────────────────────────────
    const strengthRows = rowsOf(inner, 'strength', 'rows')
    const totalRow = strengthRows.find(r => r['fact_category'] === 'graha_shadbala_total')
    if (totalRow) {
      const fid = factIdOf(totalRow); if (fid) extraFactIds.push(fid)
      const rupas = numOf(totalRow)
      const required = SHADBALA_REQUIRED_RUPAS[grahaName]
      if (rupas != null) {
        if (required != null) {
          const surplus = rupas - required
          const grade = surplus >= 0 ? 'strong (surplus)' : 'weak (deficit)'
          sentences.push(
            `Shadbala: ${rupas.toFixed(2)} rupas vs ${required.toFixed(2)} required — grade: ${grade} ` +
            `(${surplus >= 0 ? '+' : ''}${surplus.toFixed(2)} rupas).`,
          )
        } else {
          sentences.push(`Shadbala: ${rupas.toFixed(2)} rupas total.`)
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
    },
    async ({ chart_id, graha, ayanamsha_id, operative_vargas, include, response_format }) => {
      if (!chart_id) return errorOutput('graha_portrait', 'chart_id is required')
      if (!graha) return errorOutput('graha_portrait', 'graha is required')
      try {
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        // R5.1 C1: 'v3' is now the MCP-channel DEFAULT for this instrument (an explicit
        // response_format:'legacy' remains the escape hatch to the pre-C1 hollow envelope).
        const format = resolveEnvelopeFormat(response_format ?? 'v3')

        // B.11: fetch holistic orientation before this entity-level drill.
        const [{ orientation_context, orientation_ok }, raw] = await Promise.all([
          fetchOrientationContext(chart_id, resolvedAyanamsha, principal),
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
            recover: { instrument: 'get_signals', hint: 'full signal_type_class=yoga MSR matches for this graha.' },
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
            recover: { instrument: 'get_signals', hint: 'full signal_type_class=dosha MSR matches for this graha.' },
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
            recover: { instrument: 'get_signals', hint: 'full signal_type_class=parivartana MSR matches for this graha (structural exchange yogas).' },
            label: 'yogas.parivartana_exchanges',
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
            recover: { instrument: 'traverse_graph', hint: 'full CGM edge set (this response kept a lean slice of the depth-1 neighborhood).' },
            label: 'cgm_neighborhood.edges',
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
            recover: { instrument: 'traverse_graph', hint: 'full CGM node set (this response kept a lean slice of the depth-1 neighborhood).' },
            label: 'cgm_neighborhood.nodes',
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
            recover: { instrument: 'get_positions', hint: 'full position rows for this graha across every category.' },
            label: 'position.rows',
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
            recover: { instrument: 'get_dashas', hint: 'full Mahadasha-level dasha periods for this graha (1900-2100 window kept only a lean slice).' },
            label: 'dashas.rows',
          },
        ]

        if (format !== 'v3') {
          const legacyResponse = { orientation_context, orientation_ok, ...envelope(inner, 'graha_portrait') }
          return dualOutputBudgeted(applyMcpBudget(legacyResponse, MCP_RESPONSE_BUDGET_KB.graha_portrait, portraitSections))
        }

        // ── v3 population ─────────────────────────────────────────────────
        const completeness = (inner['completeness'] as Record<string, string> | undefined) ?? {}
        const errors = (inner['errors'] as Record<string, string> | undefined) ?? undefined
        const sectionsPopulated = Object.values(completeness).filter(v => v === '✓').length
        const sectionsRequested = Object.values(completeness).filter(v => v !== 'not_requested').length

        const positionRows = ((inner['position'] as Record<string, unknown> | undefined)?.['rows'] as Record<string, unknown>[] | undefined) ?? []
        const fact_ids = Array.from(new Set(positionRows.map(r => r['fact_id']).filter((v): v is string => typeof v === 'string')))

        let chart_header: ChartHeader | null = null
        try {
          chart_header = await callRegistryCapability(
            'marsys://tool/L1/get_chart_header', { chart_id, ayanamsha_id: resolvedAyanamsha }, chart_id, principal,
          ) as ChartHeader
        } catch {
          chart_header = null
        }

        // Pratinidhi-R ruling (R5.3 B2): the narration MUST be built from `inner` —
        // the UNTRIMMED capability output — BEFORE applyMcpBudget runs below, so it can
        // safely cite any fetched row even if that row is later trimmed off the wire.
        const grahaNameResolved = typeof inner['graha'] === 'string' ? inner['graha'] as string : graha
        const { narration, extraFactIds } = buildGrahaPortraitNarration(
          chart_id, grahaNameResolved, chart_header?.lagna_sign ?? null, inner,
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

        const judgment_flags: JudgmentFlagEntry[] = []
        if (errors && Object.keys(errors).length > 0) judgment_flags.push(judgmentFlag('partial_portrait_section_errors'))
        if (completeness['yogas'] === 'zero_rows') judgment_flags.push(judgmentFlag('no_parivartana_or_catalog_matches_for_graha'))
        if (completeness['dashas'] === 'zero_rows') judgment_flags.push(judgmentFlag('no_mahadasha_periods_for_graha'))

        // Typed per design §28.4 (R5 W3 Phase B) — additive `pointer_type` alongside the
        // pre-existing {instrument, hint} shape.
        const drill_pointers: { instrument: string; hint: string; pointer_type: DrillPointerType }[] = [
          { instrument: 'get_dashas', hint: 'Antardasha-level (level=2+) detail for this graha\'s Mahadasha periods, narrower window.', pointer_type: 'dasha_of_promise' },
          { instrument: 'traverse_graph', hint: 'deeper CGM traversal (depth>1, paths mode) from this graha\'s neighborhood.', pointer_type: 'dispositor_chain' },
          { instrument: 'get_signals', hint: 'raw MSR signal evidence for any yoga/dosha match surfaced here.', pointer_type: 'karaka_condition' },
          { instrument: 'judgment_query', hint: 'the complete bhava-level (7th-house marriage, 10th-house career, etc.) promise-register verdict — this entity-scoped call cannot fully adjudicate bhava claims on its own.', pointer_type: 'karaka_condition' },
        ]

        const v3Response = {
          orientation_context, orientation_ok,
          ...envelope(inner, 'graha_portrait', undefined, 'v3', { chart_header, verdict, grounding, drill_pointers, judgment_flags }),
        }
        const budgeted = applyMcpBudget(v3Response, MCP_RESPONSE_BUDGET_KB.graha_portrait, portraitSections)
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
    'R5 unified envelope with typed drill_pointers carrying `pact_stage` metadata.',
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
    },
    async ({ chart_id, ayanamsha_id, domain, bhava, as_of_date, response_format, max_signals }) => {
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
          fetchOrientationContext(chart_id, resolvedAyanamsha, principal),
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
          findStageArraySection('TRIGGER', 'transiting_positions', 1, { instrument: 'query_planet_transit', hint: 'full transit series across the activation window (this call fetched only the single as_of_date snapshot).' }),
          findStageArraySection('CONFIRMATION', 'dignities', 2, { instrument: 'ganita_condition_get', hint: 'full dignity rows for the promise-carrying graha(s) in the operative varga. (SC-18: was "get_dignity", a non-existent MCP tool name; use facet="dignity").' }),
          findStageArraySection('ACTIVATION', 'active_periods', 2, { instrument: 'get_dashas', hint: 'full dasha timeline for the promise-carrying graha(s).' }),
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
          return dualOutputBudgeted(applyMcpBudget(legacyResponse, MCP_RESPONSE_BUDGET_KB.pact_query, pactSections))
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

        let chart_header: ChartHeader | null = null
        try {
          chart_header = await callRegistryCapability(
            'marsys://tool/L1/get_chart_header', { chart_id, ayanamsha_id: resolvedAyanamsha }, chart_id, principal
          ) as ChartHeader
        } catch {
          chart_header = null
        }

        const v3Response = {
          orientation_context, orientation_ok,
          ...envelope(inner, 'pact_query', undefined, 'v3', {
            chart_header, verdict, grounding, drill_pointers, judgment_flags,
            as_of_date: resolvedAsOfDate,
          }),
        }
        return dualOutputBudgeted(applyMcpBudget(v3Response, MCP_RESPONSE_BUDGET_KB.pact_query, pactSections))
      } catch (err) {
        return errorOutput('pact_query', String(err), { chart_id })
      }
    }
  )
}

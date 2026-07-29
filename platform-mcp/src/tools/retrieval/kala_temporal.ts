/**
 * retrieval/kala_temporal.ts — BRAHMA-KA-3-COMPOSITE: kala.temporal composite L3 tool
 *
 * Composite MCP tool that wraps the L3 Kāla assets:
 *   KA-3-1 kala.timeline   — per-dasha-period dossier rows (kala_avadhi, via query_dasha_dossier)
 *   KA-3-2 kala.convergence — convergence windows (kala_convergence, via query_convergence_windows)
 *   KA-3-3 kala.obstruction — obstruction periods (kala_obstruction, via query_obstruction_periods)
 *   KA-3-5 kala.snapshot    — point-in-time current Kala state, composed from the above plus
 *                             kala_darshana (via query_temporal_view) for kala_readiness
 *
 * CR-40/T-1 (D-1.6 Lane S-6, 2026-07-16): this tool previously called four Python-sidecar
 * HTTP endpoints (`/kala/timeline`, `/kala/convergence`, `/kala/obstructions`, `/kala/snapshot`)
 * that were NEVER MOUNTED on the sidecar — `platform/python-sidecar/main.py` has no `/kala`
 * prefix router and never has (confirmed: every `app.include_router` call inspected, no
 * `kala.py`/`convergence.py`/`obstruction.py` router file exists anywhere under
 * `platform/python-sidecar/routers/`). So this was never an auth/key-wiring gap — the
 * sidecar's `verify_api_key` dependency was never even reached, since the routes 404'd. Every
 * call silently degraded to the empty fallback template, so `sidecar_available` was
 * permanently false. The real L3 Kāla data already exists in Postgres (kala_avadhi,
 * kala_convergence, kala_obstruction, kala_darshana — populated by the ka_* orchestrator
 * writers) and is already served correctly through the retrieval registry by sibling tools
 * (kala_life_arc_get and the capabilities under
 * platform/src/lib/retrieval/registry/layers/L3_kala/). This composite now calls those SAME
 * registry capabilities via callRegistryCapability — the identical DB-primary proxy path every
 * other BA-P1/D7 tool uses — instead of the non-existent sidecar HTTP surface.
 * `sidecar_available` is kept as the field name for backward/gate compatibility (Gate Ś §13
 * checks it) but now means "L3 Kāla backing data reachable from Postgres via the registry"
 * rather than "Python sidecar reachable".
 *
 * Input:
 *   {
 *     chart_id: string,               // UUID (required — chart_agnostic_gate RULE-1/4)
 *     date_range?: { start: string, end: string }  // YYYY-MM-DD (optional)
 *     include_snapshot?: boolean,     // include kala.snapshot for today (default true)
 *   }
 *
 * Output:
 *   {
 *     timeline_excerpt:    [...],  // vimshottari dasha-period dossier rows (kala_avadhi)
 *                                   // overlapping date_range, levels 1-3
 *     convergence_windows: [...],  // convergence windows overlapping date_range
 *     obstructions:        [...],  // top obstruction rows by severity_score — kala_obstruction
 *                                   // carries no per-row date range, so this array is NOT
 *                                   // filtered by date_range (disclosed in provenance_envelope)
 *     snapshot:            {...},  // current Kala state (if include_snapshot)
 *     provenance_envelope: {...}
 *   }
 *
 * Wiring: registerKalaTemporalRetrievalTool(server, principal) in server.ts — principal is now
 * required (CR-40/T-1 fix) so callRegistryCapability can satisfy /api/retrieval/capability's
 * per-call chart-entitlement gate (X-MCP-User / X-MCP-Key-Id), same as every other BA-P1 tool.
 * Note: kala_temporal.ts (in parent dir) registers the standalone `temporal` tool.
 *       This file registers `kala_temporal_bundle` for the retrieval/ layer.
 *
 * chart_id: required from caller — no default chart (chart_agnostic_gate RULE-1/4)
 *
 * BRAHMA-KA-3-COMPOSITE / l3-kala
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../../types.js'
import { describeProxyFailure } from '../registry_bridge.js'
import { budgetMcpContent } from '../../lib/response_budget.js'

// ── Constants ─────────────────────────────────────────────────────────────────

const SOURCE_CITATION = 'kala_avadhi / kala_convergence / kala_obstruction / kala_darshana (L3 Kāla, orchestrator-built) via Brahma retrieval registry'
// REMEDIATION D7: NATIVE_CHART_ID default removed. chart_id is now REQUIRED.
// chart_agnostic_gate RULE-1/RULE-4: no default on chart_id.
const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''
// DEFAULT_SNAPSHOT_DATE: today's date (ISO), computed at runtime.
// chart_agnostic_gate: no hardcoded native-specific date.
const DEFAULT_SNAPSHOT_DATE = new Date().toISOString().slice(0, 10)

// ── Registry capability caller (CR-40/T-1: replaces the dead sidecar-fetch path) ─────────────
// Same pattern as register_p1_synthesis.ts / register_p1_reference.ts: proxy through
// /api/retrieval/capability so the in-process registry (platform/src/lib/retrieval/registry)
// does the actual DB read.
async function callRegistryCapability(
  uri: string,
  args: Record<string, unknown>,
  principal: Principal
): Promise<{ content: unknown; ok: boolean; error?: string }> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(15_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(describeProxyFailure(uri, res.status, text))
  }
  const data = (await res.json()) as { ok: boolean; content?: unknown; error?: string }
  return { content: data.content, ok: data.ok, error: data.error }
}

/** Fetch a capability and pull out its row array. Never throws — a transport/proxy
 *  failure or a malformed envelope both resolve to `{ rows: [], ok: false }` so the caller
 *  can distinguish "capability unreachable" from "capability reached, zero real rows".
 *
 *  CR-93/94 double-unwrap fix (same root cause already documented/fixed in
 *  register_p1_ganita.ts's callRegistryCapability and register_p2_dasha_lord.ts's):
 *  /api/retrieval/capability responds `{ ok: true, content: await capability.handler(args) }`,
 *  and every CapabilityDescriptor handler (registry/types.ts contract) itself returns
 *  `{ content: <realPayload>, is_error: boolean }`. So the `content` this function receives
 *  from callRegistryCapability is really `{ content: { rows: [...], ... }, is_error: false }` —
 *  one level deeper than a bare `.rows` read expects. Live-confirmed on chart 482012f1
 *  (1,571 kala_avadhi rows / full vimshottari coverage 1949-2100): every fetchCapabilityRows
 *  call in this file was reading `content.rows` (undefined) instead of
 *  `content.content.rows`, so kala_temporal_bundle silently reported timeline_count: 0 for
 *  every date range while still marking sidecar_available/ok as successful. Defensive: only
 *  unwraps one level deeper when the shape actually matches the handler-result contract (has
 *  an `is_error` key) — never mis-unwraps a legitimately content-shaped payload that happens
 *  to lack that key.
 *
 *  CR-111 fix (D-4a Lane A-0): the double-unwrap above fixed `query_dasha_dossier` (whose
 *  handler names its array field `rows` — see query_dasha_dossier.ts), but
 *  `query_convergence_windows` names its field `convergence_windows` and
 *  `query_obstruction_periods` names its field `obstructions` (neither is called `rows` —
 *  see each capability's own `content: {...}` shape). A hardcoded `.rows` read therefore
 *  always resolved to `undefined` → `[]` for those two capabilities specifically, while
 *  `ok` stayed `true` (the round-trip genuinely succeeded) — so kala_temporal_bundle
 *  reported honest-looking `convergence_count: 0` / `obstruction_count: 0` even when the
 *  backing tables held real, dated rows for the exact requested range (live-confirmed:
 *  chart 482012f1, kala_convergence holds 1,685 rows overlapping 2026-01-01..2027-12-31
 *  incl. the 2027-10-20→11-01 TRIGGER-refined peak, yet the bundle served zero). Fix: an
 *  explicit `fieldName` parameter — defaults to `'rows'` for existing callers (timeline,
 *  MD/AD/PD dasha-dossier snapshot lookups), passed as `'convergence_windows'` /
 *  `'obstructions'` for those two capabilities specifically. No change to any scoring,
 *  weighting, or threshold — this is purely which JSON key gets read. */
async function fetchCapabilityRows<T>(
  uri: string,
  args: Record<string, unknown>,
  principal: Principal,
  fieldName: string = 'rows'
): Promise<{ rows: T[]; ok: boolean }> {
  try {
    const { content, ok } = await callRegistryCapability(uri, args, principal)
    if (!ok || !content || typeof content !== 'object') return { rows: [], ok: false }
    const inner =
      !Array.isArray(content) && 'is_error' in (content as Record<string, unknown>)
        ? (content as { content?: unknown }).content
        : content
    if (!inner || typeof inner !== 'object') return { rows: [], ok: true }
    const rows = (inner as Record<string, unknown>)[fieldName]
    return { rows: Array.isArray(rows) ? (rows as T[]) : [], ok: true }
  } catch {
    return { rows: [], ok: false }
  }
}

// ── Types ─────────────────────────────────────────────────────────────────────
// CR-40/T-1: row shapes now mirror the real kala_avadhi / kala_convergence /
// kala_obstruction / kala_darshana columns (see query_dasha_dossier.ts,
// query_convergence_windows.ts, query_obstruction_periods.ts, query_temporal_view.ts)
// rather than the old Python-sidecar contract these tables never actually served.

export interface TimelineRow {
  avadhi_id: string
  system_id: string
  level_n: number
  lord_graha: string
  period_start: string
  period_end: string
  dossier: unknown
  quality: unknown
  [key: string]: unknown
}

export interface ConvergenceWindow {
  convergence_id: number
  window_start: string
  window_end: string
  peak_date: string
  convergence_score: number
  confidence_score: number
  confidence_label: string
  domain: string | null
  constituent_factors: unknown
  source_citation: string
  [key: string]: unknown
}

export interface ObstructionEntry {
  id: number
  convergence_id: number | null
  obstruction_type: string
  severity: string
  severity_score: number
  override_score: number | null
  obstruction_detail: unknown
  source_citation: string
  [key: string]: unknown
}

export interface KalaSnapshot {
  chart_id: string
  snapshot_date: string
  active_dasha: {
    md_lord: string | null
    ad_lord: string | null
    ad_start: string | null
    ad_end: string | null
    days_elapsed: number | null
    days_remaining: number | null
  } | null
  active_pratyantardasha: {
    pd_lord: string
    pd_start: string
    pd_end: string
    days_elapsed: number
    days_remaining: number
  } | null
  transit_state: { transits: unknown[]; source: string }
  active_convergences: ConvergenceWindow[]
  active_obstructions: unknown[]
  kala_readiness: { score: number | null; interpretation: string; breakdown: unknown | null }
  kala_summary: string
  provenance_envelope: Record<string, unknown>
}

export interface KalaTemporalBundle {
  timeline_excerpt: TimelineRow[]
  convergence_windows: ConvergenceWindow[]
  obstructions: ObstructionEntry[]
  snapshot: KalaSnapshot | null
  provenance_envelope: {
    source: string
    assets: string[]
    chart_id: string
    date_range: { start: string; end: string }
    computed_at: string
    source_citation: string
    timeline_count: number
    convergence_count: number
    obstruction_count: number
    snapshot_included: boolean
    sidecar_available: boolean
    obstructions_not_date_filtered: boolean
  }
}

function daysBetween(a: string, b: string): number {
  const msPerDay = 24 * 60 * 60 * 1000
  return Math.round((new Date(b).getTime() - new Date(a).getTime()) / msPerDay)
}

// ── Core: computeKalaTemporalBundle ──────────────────────────────────────────

/**
 * Compute the composite L3 Kāla bundle for a chart and date range.
 *
 * CR-40/T-1: primary (and only) path is the retrieval registry's DB-backed L3 Kāla
 * capabilities (kala_avadhi / kala_convergence / kala_obstruction / kala_darshana),
 * proxied via callRegistryCapability — same path every other BA-P1/D7 tool uses. The
 * dead Python-sidecar HTTP path (routes that were never mounted) has been removed.
 */
export async function computeKalaTemporalBundle(
  chartId: string,
  dateRange: { start: string; end: string },
  includeSnapshot: boolean,
  principal: Principal
): Promise<KalaTemporalBundle> {
  const { start, end } = dateRange
  const computedAt = new Date().toISOString()

  const [timelineResp, convResp, obsResp] = await Promise.all([
    fetchCapabilityRows<TimelineRow>(
      'marsys://tool/L3/query_dasha_dossier',
      { chart_id: chartId, system_id: 'vimshottari', date_from: start, date_to: end, limit: 50 },
      principal
    ),
    fetchCapabilityRows<ConvergenceWindow>(
      'marsys://tool/L3/query_convergence_windows',
      { chart_id: chartId, date_from: start, date_to: end, top_k: 50 },
      principal,
      'convergence_windows'
    ),
    fetchCapabilityRows<ObstructionEntry>(
      'marsys://tool/L3/query_obstruction_periods',
      { chart_id: chartId, limit: 50 },
      principal,
      'obstructions'
    ),
  ])

  const timeline = timelineResp.rows
  const convergenceWindows = convResp.rows
  const obstructions = obsResp.rows
  // "Backing data available" = the registry proxy round-tripped successfully for every
  // sub-asset (an empty array from a reachable capability still counts as available —
  // B.10: an honest empty result must stay distinguishable from an unreachable one).
  const dataAvailable = timelineResp.ok && convResp.ok && obsResp.ok

  let snapshot: KalaSnapshot | null = null
  if (includeSnapshot) {
    const today = DEFAULT_SNAPSHOT_DATE
    const [mdResp, adResp, pdResp, darshanaResp] = await Promise.all([
      fetchCapabilityRows<TimelineRow>(
        'marsys://tool/L3/query_dasha_dossier',
        { chart_id: chartId, system_id: 'vimshottari', level_n: 1, active_on: today, limit: 1 },
        principal
      ),
      fetchCapabilityRows<TimelineRow>(
        'marsys://tool/L3/query_dasha_dossier',
        { chart_id: chartId, system_id: 'vimshottari', level_n: 2, active_on: today, limit: 1 },
        principal
      ),
      fetchCapabilityRows<TimelineRow>(
        'marsys://tool/L3/query_dasha_dossier',
        { chart_id: chartId, system_id: 'vimshottari', level_n: 3, active_on: today, limit: 1 },
        principal
      ),
      fetchCapabilityRows<{
        effective_score: number; net_label: string; window_start: string; window_end: string
        obstruction_summary: unknown; narrative: unknown
      }>(
        'marsys://tool/L3/query_temporal_view',
        { chart_id: chartId, active_on: today, limit: 1 },
        principal
      ),
    ])

    const md = mdResp.rows[0]
    const ad = adResp.rows[0]
    const pd = pdResp.rows[0]
    const darshana = darshanaResp.rows[0]

    const activeDasha = ad
      ? {
          md_lord: md?.lord_graha ?? null,
          ad_lord: ad.lord_graha,
          ad_start: ad.period_start,
          ad_end: ad.period_end,
          days_elapsed: daysBetween(ad.period_start, today),
          days_remaining: daysBetween(today, ad.period_end),
        }
      : null

    const activePratyantardasha = pd
      ? {
          pd_lord: pd.lord_graha,
          pd_start: pd.period_start,
          pd_end: pd.period_end,
          days_elapsed: daysBetween(pd.period_start, today),
          days_remaining: daysBetween(today, pd.period_end),
        }
      : null

    const snapshotDataAvailable = mdResp.ok && adResp.ok && pdResp.ok && darshanaResp.ok

    snapshot = {
      chart_id: chartId,
      snapshot_date: today,
      active_dasha: activeDasha,
      active_pratyantardasha: activePratyantardasha,
      transit_state: {
        transits: [],
        source: snapshotDataAvailable
          ? 'not computed by kala_temporal_bundle — call ref_planet_transit_get / query_planet_transit for live transit positions'
          : 'L3 Kāla registry unreachable this call — no transit data',
      },
      // Convergence/obstruction windows active today, from the already-fetched arrays
      // (query_convergence_windows overlap semantics: window_end >= date_from AND
      // window_start <= date_to). kala_obstruction carries no date range at all (see
      // module docstring), so "active_obstructions" is honestly sourced from the
      // kala_darshana confluence row for today (its obstruction_summary jsonb), not a
      // date-filtered slice of the raw obstruction table.
      active_convergences: convergenceWindows.filter(
        (w) => w.window_start <= today && w.window_end >= today
      ),
      active_obstructions: darshana?.obstruction_summary
        ? [darshana.obstruction_summary]
        : [],
      kala_readiness: darshana
        ? {
            score: darshana.effective_score,
            interpretation: darshana.net_label,
            breakdown: darshana.narrative ?? null,
          }
        : {
            score: null,
            interpretation: snapshotDataAvailable
              ? 'No kala_darshana confluence row active for today — chart has no computed windows covering the current date.'
              : 'L3 Kāla registry unreachable this call — kala_readiness cannot be computed.',
            breakdown: null,
          },
      kala_summary: darshana
        ? `Kāla-Darshana confluence active today: net_label=${darshana.net_label}, effective_score=${darshana.effective_score}.`
        : (snapshotDataAvailable
            ? 'No active Kāla-Darshana confluence window for today.'
            : 'L3 Kāla registry unreachable — snapshot could not be computed.'),
      provenance_envelope: {
        asset: 'kala.snapshot',
        unit: 'KA-3-5',
        chart_id: chartId,
        source_citation: SOURCE_CITATION,
        layer: 'L3 Kāla',
        snapshot_date: today,
        mode: snapshotDataAvailable ? 'live' : 'unreachable',
        tables: ['kala_avadhi', 'kala_darshana'],
      },
    }
  }

  return {
    timeline_excerpt: timeline,
    convergence_windows: convergenceWindows,
    obstructions,
    snapshot: includeSnapshot ? snapshot : null,
    provenance_envelope: {
      source: 'kala.temporal_bundle',
      assets: ['kala.timeline', 'kala.convergence', 'kala.obstruction', 'kala.snapshot'],
      chart_id: chartId,
      date_range: { start, end },
      computed_at: computedAt,
      source_citation: SOURCE_CITATION,
      timeline_count: timeline.length,
      convergence_count: convergenceWindows.length,
      obstruction_count: obstructions.length,
      snapshot_included: includeSnapshot,
      sidecar_available: dataAvailable,
      obstructions_not_date_filtered: true,
    },
  }
}

// ── Input schema ──────────────────────────────────────────────────────────────

// REMEDIATION D7: chart_id is now REQUIRED (no .default(), no ?? NATIVE_CHART_ID).
// chart_agnostic_gate RULE-1: per_chart scope → chart_id in required_inputs.
// chart_agnostic_gate RULE-3: native identifiers removed from description.
// chart_agnostic_gate RULE-4: no default on chart_id field.
// chart_agnostic_gate RULE-5: no native UUID in chart_id description.
const InputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart to compute Kāla temporal bundle for. Required — no default chart.'
    ),

  date_range: z
    .object({
      start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('Start date YYYY-MM-DD'),
      end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('End date YYYY-MM-DD'),
    })
    .optional()
    .describe(
      'Date range for the temporal bundle (default: 6 months before + after current date). ' +
        'For a full life arc, pass the chart subject\'s birth year through 2040-12-31.'
    ),

  include_snapshot: z
    .boolean()
    .default(true)
    .describe(
      'Include the point-in-time kala.snapshot for the current date. ' +
        'Default true — always include for current Kala state.'
    ),
})

// ── Tool description ──────────────────────────────────────────────────────────

const TOOL_NAME = 'kala_bundle_get'

// REMEDIATION D7 (RULE-3): native identifiers removed from LLM-visible description.
// CR-40/T-1: description updated — source is now the L3 Kāla registry capabilities
// (Postgres-backed), not the Python sidecar (which never had these routes mounted).
const TOOL_DESCRIPTION = `\
What it does: Returns the composite L3 Kāla temporal bundle — the L3 Kāla assets in one \
call for a given chart UUID, sourced from the retrieval registry (kala_avadhi / \
kala_convergence / kala_obstruction / kala_darshana — Postgres-backed, orchestrator-built):
  • kala.timeline    (KA-3-1) — vimshottari dasha-period dossier rows (levels 1-3) in date_range
  • kala.convergence (KA-3-2) — convergence windows overlapping date_range
  • kala.obstruction (KA-3-3) — top obstruction rows by severity (NOT date-filtered — the
    underlying table carries no per-row date range; disclosed via
    provenance_envelope.obstructions_not_date_filtered)
  • kala.snapshot    (KA-3-5) — current Kala state (MD/AD/PD dasha + kala_readiness score from
    the active kala_darshana confluence window, if any)

Output shape:
  {
    timeline_excerpt:    [...],  // dasha-period dossier rows (kala_avadhi)
    convergence_windows: [...],  // convergence windows (kala_convergence)
    obstructions:        [...],  // obstruction rows (kala_obstruction; not date-filtered)
    snapshot:            {...},  // current Kala state (kala_readiness.score, or null if no
                                  // confluence window is active today — an honest gap, not a
                                  // fabricated score)
    provenance_envelope: {...}
  }

When to use: Use for any temporal or predictive query about a chart (<chart_uuid>). \
Pair with holistic_bundle for the full picture — holistic_bundle provides the L2 natal \
signal layer; kala_temporal_bundle provides the L3 temporal animation layer.

[ṢAḌ-DARŚANA W0.4 deprecation notice — not retired, still live]: for the kala.snapshot \
piece specifically ("what is my temporal state right now"), prefer kala_now_get, which \
re-presents the same MD/AD/PD + kala_darshana confluence state on the elevated \
argument-shaped envelope (question_frame, tri_plane pointers, 3-state coverage). This \
tool remains the composite (timeline + convergence + obstruction + snapshot in one call).

Requires: chart_id (UUID) — must be provided by caller. No default chart.

BRAHMA-KA-3-COMPOSITE | kala.temporal_bundle retrieval tool.`

// ── Tool registration ─────────────────────────────────────────────────────────

/**
 * Register the kala_temporal_bundle retrieval tool on an McpServer instance.
 *
 * Called from server.ts during the BRAHMA L3 Kāla registration phase.
 *
 * CR-40/T-1: `principal` is now required — computeKalaTemporalBundle proxies through
 * /api/retrieval/capability, which needs X-MCP-User/X-MCP-Key-Id (same as every other
 * BA-P1 tool's callRegistryCapability call).
 *
 * Example:
 *   import { registerKalaTemporalRetrievalTool } from './tools/retrieval/kala_temporal.js'
 *   registerKalaTemporalRetrievalTool(server, principal)
 */
export function registerKalaTemporalRetrievalTool(server: McpServer, principal: Principal): void {
  server.tool(TOOL_NAME, TOOL_DESCRIPTION, InputSchema.shape, async (params) => {
    const input = InputSchema.parse(params)

    // Default date range: 6 months before + 6 months after today (chart-agnostic).
    // Computed at request time so the window always centers on the current date.
    const todayMs = Date.now()
    const sixMonthsMs = 6 * 30 * 24 * 60 * 60 * 1000
    const dateRange = input.date_range ?? {
      start: new Date(todayMs - sixMonthsMs).toISOString().slice(0, 10),
      end:   new Date(todayMs + sixMonthsMs).toISOString().slice(0, 10),
    }

    try {
      const result = await computeKalaTemporalBundle(
        input.chart_id,
        dateRange,
        input.include_snapshot,
        principal
      )
      const budgeted = budgetMcpContent(result, TOOL_NAME)

      // SATYA-ŚEṢA W3 (2026-07-25): this call previously pretty-printed with
      // `JSON.stringify(budgeted, null, 2)` — `budgetMcpContent`'s own internal
      // measurement (response_budget.ts's `estimateBytes`) always uses COMPACT
      // JSON.stringify (no indent) to decide whether/how much to trim, so a
      // response that measured "under the 40KB ceiling" internally could still
      // be served far over it once the 2-space indentation was added back on
      // the wire (live-measured: a 37.7KB compact payload became 53.1KB
      // pretty-printed — 41% larger, enough on its own to blow the ceiling
      // this call believed it had already enforced). Every sibling tool in
      // this file/family (dualOutput, register_gochara_windows.ts) serves
      // compact JSON; this now matches.
      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(budgeted),
          },
        ],
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(
              {
                error: true,
                tool: TOOL_NAME,
                message,
                chart_id: input.chart_id,
                date_range: dateRange,
                provenance_envelope: {
                  source: 'kala.temporal_bundle',
                  source_citation: SOURCE_CITATION,
                  computed_at: new Date().toISOString(),
                },
              },
              null,
              2
            ),
          },
        ],
        isError: true,
      }
    }
  })
}

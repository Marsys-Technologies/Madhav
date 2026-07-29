/**
 * tools/kala_views/now.ts — ṢAḌ-DARŚANA W0.4 (SHAD_DARSHANA_BRIEF_v2_0.md §0.4 · §2 file map
 * · §3 W0.4 "Eight facades over EXISTING substrate").
 * ==========================================================================
 * `kala_now_get` — VIEW 1: NOW ("What is my temporal state?"), per
 * KALA_SIX_VIEWS_DESIGN_v1_0.md §1.
 *
 * THIN FACADE — this file computes NOTHING new. It calls the SAME two registry
 * capabilities the existing `kala_windows_get` (register_p1_aliases.ts, →
 * `marsys://tool/L3/query_temporal_activation`) and the snapshot half of `kala_bundle_get`
 * (tools/retrieval/kala_temporal.ts, → `marsys://tool/L3/query_temporal_view`) already call,
 * and re-presents their EXISTING rows through the elevated envelope (`lib/kala_envelope.ts`)
 * + the shared prose engine (`lib/argument_composer.ts`). No new join, no new field, no new
 * computation — every claim in the composed reading traces to a field the underlying
 * capability already returns (§N.5 / B.10).
 *
 * Design authority: KALA_SIX_VIEWS_DESIGN_v1_0.md §1 (NOW content + clarity contract),
 * KALA_SUPREME_ELEVATION_v1_0.md (v1.2) §5 (envelope E3/E4/E5), §11 (item 43 tri-plane).
 *
 * What is genuinely NOT computed here yet (honestly disclosed via `coverage`, never
 * silently dropped): daśā-sandhi bands, per-ingress transit moorti, dual-reference
 * (Moon+lagna) gochara — all named W1/W3 build items in the brief, not this facade's job.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../../types.js'
import {
  makeKalaEnvelope,
  noLelCalibrationMaturity,
  buildKalaFreshness,
  buildFieldSnapshotIdStub,
  pointerTo,
  isNoLever,
  computedCoverage,
  honestEmptyCoverage,
  notInCorpusCoverage,
  type ArgumentReading,
  type ArgumentEvidence,
  type ArgumentVerdict,
  type QuestionFrame,
  type TriPlanePointers,
  type DrillPointerLike,
  type KalaCoverageEntry,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'
import { autoDetectTrimmableSections, finalizeMcpBudget } from '../../lib/response_budget.js'

// ── Infrastructure (self-contained proxy helper — mirrors the established per-file
// pattern in register_p1_aliases.ts / tools/retrieval/kala_temporal.ts / registry_bridge.ts;
// this file does not import their module-local helpers to avoid coupling this new lane's
// facade to files owned/being edited by sibling lanes in the same campaign) ─────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

const AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri: 'lahiri_chitrapaksha', LAHIRI: 'lahiri_chitrapaksha', Lahiri: 'lahiri_chitrapaksha',
  lahiri_chitrapaksha: 'lahiri_chitrapaksha', true_chitra: 'lahiri_chitrapaksha',
}
function normalizeAyanamsha(id?: string): string {
  return id ? (AYANAMSHA_ALIAS[id] ?? id) : 'lahiri_chitrapaksha'
}

/**
 * Calls a registry capability via /api/retrieval/capability. NEVER throws — a transport
 * failure or malformed envelope both resolve to `{ content: null, ok: false }` so the
 * caller can serve an honest `honest_empty` coverage entry instead of crashing the whole
 * facade over one degraded sub-call (mirrors tools/retrieval/kala_temporal.ts's
 * `fetchCapabilityRows` resilience contract).
 *
 * Defensive double-unwrap: /api/retrieval/capability responds `{ ok, content: <result> }`,
 * and every CapabilityDescriptor handler itself returns `{ content: <payload>, is_error }`.
 * This only unwraps the second layer when the shape actually matches that contract (has an
 * `is_error` key) — never mis-unwraps a legitimately content-shaped payload lacking one.
 */
async function callRegistryCapability(
  uri: string,
  args: Record<string, unknown>,
  principal: Principal,
): Promise<{ content: Record<string, unknown> | null; ok: boolean }> {
  try {
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
    if (!res.ok) return { content: null, ok: false }
    const data = (await res.json()) as { ok: boolean; content?: unknown }
    if (!data.ok) return { content: null, ok: false }
    const outer = data.content
    if (outer && typeof outer === 'object' && !Array.isArray(outer) && 'is_error' in (outer as Record<string, unknown>)) {
      const wrapper = outer as { content?: unknown; is_error?: boolean }
      const inner = wrapper.content
      return {
        content: inner && typeof inner === 'object' ? (inner as Record<string, unknown>) : null,
        ok: wrapper.is_error !== true,
      }
    }
    return { content: outer && typeof outer === 'object' ? (outer as Record<string, unknown>) : null, ok: true }
  } catch {
    return { content: null, ok: false }
  }
}

function dualOutput(data: unknown, toolName = 'kala_now_get') {
  let finalData: unknown = data
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>
    const sections = autoDetectTrimmableSections(obj, toolName)
    finalData = finalizeMcpBudget(obj, { maxKb: 40, sections })
  }
  const structuredContent = { type: 'object' as const, object: finalData }
  const json = JSON.stringify(finalData)
  return { structuredContent, content: [{ type: 'text' as const, text: json }] }
}

function errOut(tool: string, msg: string, extra?: Record<string, unknown>) {
  return { ...dualOutput({ ok: false, error: msg, tool, ...extra }, tool), isError: true as const }
}

// ── Window-family shape (query_temporal_activation's `window_families` /
// `forward_windows` rows — read verbatim, never re-derived) ────────────────────────

interface WindowFamily {
  window_start: string | null
  window_end: string | null
  window_peak?: string | null
  member_count: number
  member_signal_ids?: string[]
  signature_classes?: string[]
  domains?: string[]
  max_orb_strength?: number
  [key: string]: unknown
}

interface DarshanaRow {
  effective_score: number | null
  net_label: string | null
  window_start?: string | null
  window_end?: string | null
  obstruction_summary?: unknown
  narrative?: unknown
  [key: string]: unknown
}

// ── The reading (template-over-computed-data — B.10; no generative call) ───────────

function buildNowReading(params: {
  asOfDate: string
  windowFamilies: WindowFamily[]
  darshana: DarshanaRow | null
  windowsOk: boolean
  darshanaOk: boolean
}): ArgumentReading {
  const { asOfDate, windowFamilies, darshana, windowsOk, darshanaOk } = params
  const top = windowFamilies[0]

  const thesisParts: string[] = []
  if (!windowsOk) {
    thesisParts.push(
      `Temporal activation windows could not be reached for ${asOfDate} — serving what is available.`,
    )
  } else if (windowFamilies.length === 0) {
    thesisParts.push(`No temporal activation window is active for this chart as of ${asOfDate}.`)
  } else {
    const label = (top?.signature_classes ?? []).join('/') || 'unlabeled'
    const orb = typeof top?.max_orb_strength === 'number' ? top.max_orb_strength.toFixed(2) : 'n/a'
    thesisParts.push(
      `${windowFamilies.length} temporal activation window(s) active as of ${asOfDate}; strongest: ` +
        `${label} (orb strength ${orb}, ${top?.member_count ?? 0} contributing signal(s)).`,
    )
  }
  if (darshanaOk && darshana) {
    thesisParts.push(
      `Kāla-Darshana confluence: ${darshana.net_label ?? 'unlabeled'} (effective_score ${darshana.effective_score ?? 'n/a'}).`,
    )
  } else if (darshanaOk && !darshana) {
    thesisParts.push('No Kāla-Darshana confluence window is active today.')
  }

  const evidence: ArgumentEvidence[] = windowFamilies.slice(0, 3).map((f) => ({
    claim:
      `${(f.signature_classes ?? []).join('/') || 'activation'} window ` +
      `${f.window_start ?? '?'}..${f.window_end ?? '?'}` +
      (f.domains && f.domains.length > 0 ? ` touching ${f.domains.join(', ')}` : ''),
    fact_ids: f.member_signal_ids ?? [],
  }))

  const verdict: ArgumentVerdict = {
    statement:
      darshanaOk && darshana
        ? `Kāla state: ${darshana.net_label ?? 'unlabeled'}.`
        : windowFamilies.length > 0
          ? `${windowFamilies.length} structural activation window(s) currently bear on this chart.`
          : 'No structural activation currently bears on this chart.',
    tier: 'structural_prior',
  }

  return {
    thesis: thesisParts.join(' ') || `No temporal state could be assembled for ${asOfDate}.`,
    evidence,
    dissent: [],
    verdict,
    falsifier: null,
  }
}

// ── Core compute (exported for tests — mirrors computeKalaTemporalBundle's shape) ──

export interface KalaNowResult {
  tool: 'kala_now_get'
  chart_id: string
  as_of_date: string
  reading: ArgumentReading
  reading_prose: string
  question_frame: QuestionFrame | null
  field_snapshot_id: string
  tri_plane: TriPlanePointers
  coverage: KalaCoverageEntry[]
  freshness: ReturnType<typeof buildKalaFreshness>
  calibration_maturity: ReturnType<typeof noLelCalibrationMaturity>
  windows: WindowFamily[]
  darshana: DarshanaRow | null
  drill_pointers: DrillPointerLike[]
  provenance_envelope: {
    source: string
    assets: string[]
    chart_id: string
    as_of_date: string
    computed_at: string
    source_citation: string
    windows_reachable: boolean
    darshana_reachable: boolean
  }
}

const SOURCE_CITATION =
  'kala_activation / kala_activation_predicates / kala_bhavishya (forward-window fallback) / ' +
  'kala_darshana (L3 Kāla, orchestrator-built) via Brahma retrieval registry — same substrate ' +
  'as kala_windows_get / kala_bundle_get, re-presented on the ṢAḌ-DARŚANA elevated envelope.'

export async function computeKalaNow(
  chartId: string,
  args: { ayanamsha_id?: string; as_of?: string; question_frame?: QuestionFrame | null },
  principal: Principal,
): Promise<KalaNowResult> {
  const ayanamshaId = normalizeAyanamsha(args.ayanamsha_id)
  const asOfDate = args.as_of ?? new Date().toISOString().slice(0, 10)

  const [windowsResp, darshanaResp] = await Promise.all([
    callRegistryCapability(
      'marsys://tool/L3/query_temporal_activation',
      { chart_id: chartId, ayanamsha_id: ayanamshaId, as_of: asOfDate, top_k: 20 },
      principal,
    ),
    callRegistryCapability(
      'marsys://tool/L3/query_temporal_view',
      { chart_id: chartId, active_on: asOfDate, limit: 1 },
      principal,
    ),
  ])

  const windowsOk = windowsResp.ok
  const rawFamilies = (windowsResp.content?.['window_families'] as WindowFamily[] | undefined) ?? []
  // query_temporal_activation itself falls back to kala_bhavishya `forward_windows` when
  // `activations`/`window_families` are empty (its own honest-empty discipline) — re-present
  // whichever the capability actually populated, never re-deriving the choice ourselves.
  const rawForward = (windowsResp.content?.['forward_windows'] as WindowFamily[] | undefined) ?? []
  const windowFamilies = rawFamilies.length > 0 ? rawFamilies : rawForward

  const darshanaOk = darshanaResp.ok
  const darshanaRows = (darshanaResp.content?.['rows'] as DarshanaRow[] | undefined) ?? []
  const darshana = darshanaRows[0] ?? null

  const reading = buildNowReading({ asOfDate, windowFamilies, darshana, windowsOk, darshanaOk })
  const composed = composeArgument(reading)

  const triPlane: TriPlanePointers = {
    // NOW IS the interpretation plane — null is the contractually-legal value here
    // (kala_envelope.ts: "null only legal when this object IS the interpretation plane").
    interpretation_ref: null,
    prediction_ref: pointerTo(
      'kala_ahead_get',
      'Forward-dated windows and probabilistic projections building on this NOW state',
    ),
    intervention_ref: pointerTo(
      'kala_elect_get',
      'Election windows for undertakings, informed by this NOW state',
    ),
  }

  const coverage: KalaCoverageEntry[] = [
    windowsOk
      ? computedCoverage('temporal_activation_windows')
      : honestEmptyCoverage('temporal_activation_windows', 'L3 Kāla registry unreachable this call.'),
    darshanaOk
      ? computedCoverage('kala_darshana_confluence')
      : honestEmptyCoverage('kala_darshana_confluence', 'L3 Kāla registry unreachable this call.'),
    notInCorpusCoverage(
      'dasha_sandhi_bands',
      'Junction-turbulence flags not yet computed for any chart — SHAD_DARSHANA_BRIEF_v2_0.md item 1 (wave W3).',
    ),
    notInCorpusCoverage(
      'transit_moorti',
      'Per-ingress moorti-nirṇaya not yet computed — SHAD_DARSHANA_BRIEF_v2_0.md item 4 (wave W3).',
    ),
    notInCorpusCoverage(
      'dual_reference_gochara',
      'Moon+lagna dual-reference gochara serving not yet joined into this view — SHAD_DARSHANA_BRIEF_v2_0.md item 8 (wave W1).',
    ),
  ]

  const drillPointers: DrillPointerLike[] = [triPlane.prediction_ref, triPlane.intervention_ref].filter(
    (p): p is DrillPointerLike => p != null && !isNoLever(p),
  )

  const envelope = makeKalaEnvelope({
    reading,
    questionFrame: args.question_frame ?? null,
    fieldSnapshotId: buildFieldSnapshotIdStub({ chart_id: chartId, ayanamsha_id: ayanamshaId, as_of: asOfDate }),
    triPlane,
    coverage,
    freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: null }),
    calibrationMaturity: noLelCalibrationMaturity(),
  })

  return {
    tool: 'kala_now_get',
    chart_id: chartId,
    as_of_date: asOfDate,
    ...envelope,
    reading_prose: composed.full_text,
    windows: windowFamilies,
    darshana,
    drill_pointers: drillPointers,
    provenance_envelope: {
      source: 'kala_now_get',
      assets: ['kala_activation (ka_kalasutra)', 'kala_bhavishya (forward-window fallback)', 'kala_darshana'],
      chart_id: chartId,
      as_of_date: asOfDate,
      computed_at: new Date().toISOString(),
      source_citation: SOURCE_CITATION,
      windows_reachable: windowsOk,
      darshana_reachable: darshanaOk,
    },
  }
}

// ── Input schema + registration ─────────────────────────────────────────────────

const QuestionFrameSchema = z
  .object({
    domain: z.string().optional(),
    entity: z.string().optional(),
    horizon: z.string().optional(),
    intent_verb: z.string().optional(),
    stakes: z.string().optional(),
    comparison_target: z.string().optional(),
  })
  .optional()
  .describe(
    'Optional question-frame (Elevation §5 E4): the caller\'s specific angle on this chart\'s ' +
      'NOW state — domain/entity/horizon/intent_verb/stakes/comparison_target. The chart is ' +
      'always implicit (chart_id); this is the only per-question input. W0: accepted and echoed ' +
      'verbatim in the response — full relevance-scoring/reading-conditioning on this param is a ' +
      'later-wave elevation (E4 full).',
  )

const InputSchema = z.object({
  chart_id: z.string().uuid().describe('UUID of the chart. Required — no default chart.'),
  ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')."),
  as_of: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/)
    .optional()
    .describe('Point-in-time date YYYY-MM-DD to read as "now" (default: today).'),
  question_frame: QuestionFrameSchema,
})

const TOOL_NAME = 'kala_now_get'

const TOOL_DESCRIPTION = `\
What is my temporal state right now? Returns the current layered Kāla clock state for a \
chart — active temporal-activation windows (kala_activation, orb-strength ranked) and the \
current Kāla-Darshana confluence (kala_darshana: effective_score + net_label) — composed \
into an argument-shaped reading (thesis → evidence → verdict) on the ṢAḌ-DARŚANA elevated \
envelope (question_frame, field_snapshot_id, tri_plane pointers, 3-state coverage, \
freshness attestation, calibration_maturity).

THIN FACADE (W0): re-presents the SAME substrate kala_windows_get and kala_bundle_get's \
snapshot already serve — no new computation. Honestly discloses (via \`coverage\`) which \
richer NOW concepts (daśā-sandhi bands, per-ingress transit moorti, dual-reference gochara) \
are not yet joined into this view.

Output includes: reading (structured argument) + reading_prose (composed text) + windows + \
darshana + tri_plane (→ kala_ahead_get for what's coming, → kala_elect_get for when to act) \
+ coverage + drill_pointers.

Requires: chart_id (UUID). Successor to kala_windows_get for "what is my state now" queries \
— kala_windows_get remains live (not retired).`

export function registerKalaNowGetTool(server: McpServer, principal: Principal): void {
  server.tool(TOOL_NAME, TOOL_DESCRIPTION, InputSchema.shape, async (params) => {
    const input = InputSchema.parse(params)
    if (!input.chart_id) return errOut(TOOL_NAME, 'chart_id is required')
    try {
      const result = await computeKalaNow(
        input.chart_id,
        { ayanamsha_id: input.ayanamsha_id, as_of: input.as_of, question_frame: input.question_frame ?? null },
        principal,
      )
      return dualOutput(result, TOOL_NAME)
    } catch (err) {
      return errOut(TOOL_NAME, err instanceof Error ? err.message : String(err), { chart_id: input.chart_id })
    }
  })
}

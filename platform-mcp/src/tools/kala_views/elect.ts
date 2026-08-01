/**
 * kala_views/elect.ts — ṢAḌ-DARŚANA v2 W0.4 (SHAD_DARSHANA_BRIEF_v2_0.md §0.4 · §2 file map).
 * ==========================================================================
 * VIEW 3 — ELECT (`kala_elect_get`) — "When should I act?"
 *
 * A THIN FACADE (W0 depth — no new computation) over the EXISTING muhūrta substrate:
 * `handleMuhurtaFinder` (`../muhurta_finder.js`, asset PH-4-4), which already computes
 * panchāṅga × daśā × transit × signal-activation scored windows, tāra-bala vetoes,
 * target-graha transit gating, and a horā ladder. This file adds NOTHING astrological —
 * it composes that already-computed data into the elevated `kala_envelope.ts` shape
 * (argument-shaped reading, question_frame, field_snapshot_id stub, tri-plane pointers,
 * 3-state coverage, freshness, calibration_maturity) via `argument_composer.ts`.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════
 * THE MODE-3 ROUTING RULE (KALA_SUPREME_ELEVATION_v1_0.md §8, binding; SHAD_DARSHANA_BRIEF
 * _v2_0.md §7 "MODE-3 ROUTING RULE"): **`kala_elect_get` is the SOLE server of Mode 3**
 * (ACTIVITY ELECTION — given an undertaking, return the ranked act-time slate). This tool
 * IS that server: an undertaking-shaped call (`undertaking` param set) lands here and is
 * answered — at W0 depth, with the existing muhūrta score/veto stack, honestly incomplete
 * on the ritual-pairing half (item 38's W4 half — see the `ritual_pairing` coverage entry
 * below, `not_in_corpus` until W4). `kala_ritual_get` (a separate lane's W0 stub) serves
 * Modes 1–2 only and redirects a Mode-3-shaped call here with `wrong_view` — this file does
 * not implement that redirect (not this lane's file), it only needs to be a valid,
 * answering landing target, which it is.
 * ══════════════════════════════════════════════════════════════════════════════════════
 *
 * WHAT THIS FILE IS NOT (W0/W1 scope discipline):
 *   - It does NOT implement the contender lattice / parihāra adjudication engine (item 36,
 *     W3) — that full election-doctrine engine (`lib/kala_lattice_query.ts`) is a later
 *     wave, built by a different session. This facade reports that gap honestly via
 *     `not_in_corpus` coverage, never by fabricating a judgment ledger.
 *   - It does NOT compute muhūrta-lagna, Sarvatobhadra vedha, or Kota-Chakra — all W3 items.
 *   - It does NOT pair the elected act-time with a preparatory ritual (item 38's W4 half).
 *
 * W1 ADDITIONS (item 38-lite + ELECT frontier v0, SHAD_DARSHANA_BRIEF_v2_0.md §3 W1):
 * every candidate now also carries `grading_tier`/`grading_tier_label` — a thin, SERVING-
 * LAYER normalization of the already-computed score/veto into the gold/silver/bronze
 * vocabulary the design doc's own gap-report example uses (see `lib/kala_grading.ts` for
 * the documented lite-v0 threshold convention) — and the response carries a top-level
 * `frontier` statement (best candidate + whether a gold-tier exists in this horizon). Both
 * are thin re-labelings of data this facade already had; neither invents new astrological
 * judgment or evaluates doṣas/parihāras (that is still item 36, W3).
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'
import { handleMuhurtaFinder, MuhurtaFinderInputSchema, type MuhurtaFinderResult, type MuhurtaWindow, type HoraSlot } from '../muhurta_finder.js'
import {
  makeKalaEnvelope,
  buildFieldSnapshotIdStub,
  pointerTo,
  noLeverPointer,
  computedCoverage,
  honestEmptyCoverage,
  notInCorpusCoverage,
  buildKalaFreshness,
  noLelCalibrationMaturity,
  kalaEvidenceTrimmableSection,
  type ArgumentReading,
  type ArgumentEvidence,
  type ArgumentDissent,
  type KalaCoverageEntry,
  type QuestionFrame,
  type KalaEnvelope,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'
import { finalizeMcpBudget, type TrimmableSection } from '../../lib/response_budget.js'
import { gradeCandidate, buildFrontierStatement, type CandidateGradingTier, type FrontierStatement } from '../../lib/kala_grading.js'

// ── Input schema ─────────────────────────────────────────────────────────────────────

// Reuses the EXACT action_type enum muhurta_finder.ts already validates against (no drift
// between "undertaking" here and "action_type" there — same closed vocabulary, B.10-clean).
const UNDERTAKING_ENUM = MuhurtaFinderInputSchema.shape.action_type

export const KalaElectInputShape = {
  chart_id: z.string().uuid().describe('Chart UUID. Required — no default chart.'),
  undertaking: UNDERTAKING_ENUM.default('general').describe(
    'The undertaking to elect a time for. This is the Mode-3 (ACTIVITY ELECTION) subject — ' +
    'marriage|travel|business|medical|education|property|general|spiritual_initiation|' +
    'remedial_ritual|japa_start. Same closed vocabulary muhurta_finder validates against.'
  ),
  date_range: z.object({
    start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('ISO date YYYY-MM-DD'),
    end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('ISO date YYYY-MM-DD'),
  }).optional().describe('Search range. Default: today .. today+90d. Max 90 days (48h blocks).'),
  min_score: z.number().min(0).max(1).optional().describe('Minimum auspiciousness_score [0,1]. Default 0.0.'),
  limit: z.number().int().min(1).max(45).optional().describe('Max candidate windows to return. Default 5.'),
  native_janma_nakshatra: z.string().optional().describe(
    "The native's janma (birth) nakshatra, to join tāra-bala personal-star vetoes. " +
    'Omit → tāra-bala reported honestly unavailable (never fabricated).'
  ),
  target_graha: z.enum(['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']).optional()
    .describe('When the election is tied to a specific graha, check its transit dignity during each window.'),
  question_frame: z.object({
    domain: z.string().optional(),
    entity: z.string().optional(),
    horizon: z.string().optional(),
    intent_verb: z.string().optional(),
    stakes: z.string().optional(),
    comparison_target: z.string().optional(),
  }).optional().describe('E4 (Elevation §5) — the caller-supplied question frame. The chart is always implicit.'),
  budget_kb: z.number().min(1).max(200).optional().describe('Response size ceiling in KB. Default 40.'),
}

const KalaElectZod = z.object(KalaElectInputShape)
export type KalaElectInput = z.infer<typeof KalaElectZod>

// ── Response shape (envelope + ELECT-specific candidate slate) ─────────────────────────

export interface KalaElectCandidate {
  start: string
  end: string
  score: number
  hard_flag: boolean
  disqualified: boolean
  rank_penalty_reason: string[]
  drivers: string[]
  source_citation: string
  // Item 38-lite (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1) — a thin serving-layer normalization
  // of the ALREADY-COMPUTED score/veto into the gold/silver/bronze vocabulary
  // KALA_SUPREME_ELEVATION_v1_0.md §9's own gap-report example uses. See lib/kala_grading.ts
  // for the documented lite-v0 threshold convention; W3 item 36 supersedes this with the
  // full doṣa/parihāra-aware contender-lattice grade.
  grading_tier: CandidateGradingTier
  grading_tier_label: string
  // Honesty-inversion fix (PARĪKṢAKA live-production acceptance pass, pre-existing since
  // commit 2cba21c5 / PR #940): `coverage` has always asserted `hora_ladder: computed` —
  // the data genuinely IS computed by muhurta_finder.ts's enrichWindowsLaneF (every window
  // gains a horā ladder unconditionally, ~line 776) — but this facade never projected it
  // onto the served candidate, so the claim was unbacked by any actual field in the
  // response. Fix option (a): serve the already-computed ladder verbatim (thin-facade
  // discipline — no new computation, same as every other candidate field here).
  hora_ladder: HoraSlot[]
}

export interface KalaElectResponse extends KalaEnvelope<ArgumentReading> {
  tool: 'kala_elect_get'
  chart_id: string
  undertaking: string
  query_window: { start: string; end: string } | null
  candidates: KalaElectCandidate[]
  candidate_count: number
  gap_report: string | null
  // ELECT frontier statement v0 (KALA_SUPREME_ELEVATION_v1_0.md §6 "ELECT → the frontier,
  // not just the slate"; SHAD_DARSHANA_BRIEF_v2_0.md §3 W1 "ELECT frontier statement v0").
  // A modest first version — the full W3 gap-report engine (next-occurrence search beyond
  // the horizon, Pareto near-frontier band) is a later wave; see lib/kala_grading.ts.
  frontier: FrontierStatement
  composed_text: string
  empty_reason?: string
}

function defaultDateRange(): { start: string; end: string } {
  const start = new Date().toISOString().slice(0, 10)
  const end = new Date(Date.now() + 90 * 86_400_000).toISOString().slice(0, 10)
  return { start, end }
}

function windowDrivers(w: MuhurtaWindow): string[] {
  const drivers: string[] = []
  const f = w.factors
  if (f) {
    if (f.panchanga_quality >= 0.6) drivers.push(`panchanga_quality=${f.panchanga_quality.toFixed(2)}`)
    if (f.dasha_quality >= 0.6) drivers.push(`dasha_quality=${f.dasha_quality.toFixed(2)} (${f.dasha_details?.md_lord}/${f.dasha_details?.ad_lord})`)
    if (f.transit_quality >= 0.6) drivers.push(`transit_quality=${f.transit_quality.toFixed(2)}`)
    if (f.signal_activation >= 0.6) drivers.push(`signal_activation=${f.signal_activation.toFixed(2)}`)
  }
  if (w.tara_bala?.favorable) drivers.push(`tara_bala=${w.tara_bala.tara_name} (favorable)`)
  return drivers
}

/** Builds the argument-shaped reading (E3) from the already-computed muhurta_finder result.
 *  Pure composition — no new astrological computation. */
function buildArgumentReading(
  undertaking: string,
  result: MuhurtaFinderResult,
): ArgumentReading {
  const windows = result.windows ?? []
  const live = windows.filter((w) => !w.disqualified)
  const top = live[0]

  const evidence: ArgumentEvidence[] = live.slice(0, 3).map((w) => ({
    claim: `${w.start} → ${w.end}: score ${w.score.toFixed(2)} (${w.source_citation})`,
    // No L1 fact_ids resolvable from muhurta_finder's response shape at this facade
    // depth (§N.5 — never fabricated); the window's own source_citation carries the
    // classical grounding instead, stated in the claim text above.
    fact_ids: [],
    strength: w.score >= 0.7 ? 'strong' : w.score >= 0.5 ? 'moderate' : 'weak',
  }))

  const dissent: ArgumentDissent[] = windows
    .filter((w) => w.hard_flag || w.disqualified)
    .slice(0, 3)
    .map((w) => ({
      claim: `${w.start} → ${w.end} ${w.disqualified ? 'disqualified' : 'flagged'}: ${(w.rank_penalty_reason ?? []).join('; ') || 'personal-star or target-graha veto'}`,
      fact_ids: [],
      source: w.tara_bala ? 'tara_bala (nava-tara personal star)' : (w.target_graha_check ? 'target_graha transit gate' : 'muhurta veto'),
    }))

  const thesis = top
    ? `For ${undertaking}, the strongest available window in the searched horizon is ${top.start} → ${top.end} (score ${top.score.toFixed(2)} of 1.0), among ${live.length} qualifying candidate${live.length === 1 ? '' : 's'}.`
    : windows.length > 0
      ? `For ${undertaking}, every candidate window in the searched horizon carries a hard veto (personal star or target-graha) — no clean election exists in this range.`
      : `For ${undertaking}, no candidate windows were computed in the searched horizon (${result.empty_reason ?? 'see empty_reason'}).`

  const verdict = top
    ? { statement: `Elect ${top.start} → ${top.end} for ${undertaking}, or wait for the next comparably-scored window if this range is inconvenient.` as string, tier: 'structural_prior' as const }
    : { statement: `No electable window found for ${undertaking} in this horizon — widen the date range or reconsider the undertaking's constraints.`, tier: 'structural_prior' as const }

  const falsifier = top
    ? { statement: `if ${undertaking} is not undertaken by ${top.end}, this specific elected window closes`, resolves_by: top.end.slice(0, 10) }
    : null

  return { thesis, evidence, dissent, verdict, falsifier }
}

function buildCoverage(result: MuhurtaFinderResult): KalaCoverageEntry[] {
  const coverage: KalaCoverageEntry[] = [computedCoverage('panchanga_dasha_transit_muhurta_scoring')]

  const laneF = result.lane_f
  if (laneF) {
    coverage.push(
      laneF.tara_bala_status === 'applied'
        ? computedCoverage('tara_bala_personal_star_veto')
        : honestEmptyCoverage('tara_bala_personal_star_veto', laneF.tara_bala_note ?? 'native_janma_nakshatra not supplied')
    )
    if (laneF.target_graha_status === 'applied') {
      coverage.push(computedCoverage('target_graha_transit_gate'))
    } else if (laneF.target_graha_status === 'pending_c5_service') {
      coverage.push(notInCorpusCoverage('target_graha_transit_gate', laneF.target_graha_note ?? 'β C5 sidereal transit-dignity service is DRAFT'))
    } else {
      coverage.push(honestEmptyCoverage('target_graha_transit_gate', 'target_graha not requested for this call'))
    }
    // Honesty-inversion fix (defect 1, PARĪKṢAKA live-production pass): this used to push
    // `computed` unconditionally the instant `laneF` existed, with no check that any window
    // actually carried a ladder — and, separately, the served candidate never carried the
    // field at all (see KalaElectCandidate.hora_ladder above). Both are fixed now: the field
    // is genuinely projected onto every candidate, and this check confirms the projection
    // actually produced something before claiming `computed` — an honest_empty fallback for
    // the (currently theoretical, since enrichWindowsLaneF always populates it) case where a
    // future change makes the ladder computation itself yield zero slots.
    const hasHoraLadder = (result.windows ?? []).some((w) => (w.hora_ladder?.length ?? 0) > 0)
    coverage.push(
      hasHoraLadder
        ? computedCoverage('hora_ladder')
        : honestEmptyCoverage(
            'hora_ladder',
            'no candidate window in this horizon carries a horā ladder (either no windows were computed, or the ladder computation yielded zero slots for every window)',
          )
    )
  }

  // Item 38-lite + ELECT frontier v0 (wave W1) — thin serving-layer normalization over the
  // already-computed score/veto stack; see lib/kala_grading.ts for the documented convention.
  coverage.push(computedCoverage('candidate_grading_lite'))
  coverage.push(computedCoverage('elect_frontier_v0'))

  // Honest W0/W1 gaps — the full election-doctrine engine (item 36/41, W3) does not exist yet.
  coverage.push(notInCorpusCoverage(
    'contender_lattice_parihara_adjudication',
    'the full contender lattice + parihāra graph + Pareto survival engine (item 36, ' +
    'KALA_SUPREME_ELEVATION_v1_0.md §9) lands at W3; this facade serves the existing ' +
    'muhurta_finder score/veto stack only — no doṣa→parihāra judgment ledger yet. ' +
    'candidate_grading_lite (above) is a thin single-scalar tier label, not this engine.',
  ))
  coverage.push(notInCorpusCoverage(
    'muhurta_lagna_strength',
    'instant-lagna computation + strength check (item 7) not yet built; candidates are not ' +
    'refined to intra-day muhurta-lagna precision.',
  ))
  coverage.push(notInCorpusCoverage(
    'ritual_pairing',
    'Mode-3 ritual pairing (item 38\'s W4 half, Elevation §8) — the preparatory rite + its ' +
    'own best time served alongside the act-time slate as one answer — is not yet wired; ' +
    'this response serves the act-time slate only.',
  ))

  return coverage
}

export async function handleKalaElectGet(
  input: KalaElectInput,
  principal: Principal,
): Promise<{ response?: KalaElectResponse; error?: { message: string; extra?: Record<string, unknown> } }> {
  const dateRange = input.date_range ?? defaultDateRange()

  const finderInput = MuhurtaFinderInputSchema.parse({
    chart_id: input.chart_id,
    action_type: input.undertaking,
    date_range: dateRange,
    ...(input.min_score !== undefined ? { min_score: input.min_score } : {}),
    limit: input.limit ?? 5,
    ...(input.native_janma_nakshatra ? { native_janma_nakshatra: input.native_janma_nakshatra } : {}),
    ...(input.target_graha ? { target_graha: input.target_graha } : {}),
  })

  const raw = await handleMuhurtaFinder(finderInput, principal) as {
    structuredContent?: { object: unknown }
    content?: { type: string; text?: string }[]
    isError?: boolean
  }
  if (raw.isError) {
    // handleMuhurtaFinder has two distinct error shapes: the AUTHZ_DENIED early-return
    // (content-only, no structuredContent) and errorOutput()'s structuredContent.object.error
    // (platform call failures). Check both rather than assuming the richer shape.
    const obj = raw.structuredContent?.object as { error?: string } | undefined
    const textMessage = raw.content?.[0]?.text
    return {
      error: {
        message: obj?.error ?? textMessage ?? 'muhurta_finder call failed',
        extra: { chart_id: input.chart_id },
      },
    }
  }

  const result = raw.structuredContent?.object as MuhurtaFinderResult
  const reading = buildArgumentReading(input.undertaking, result)
  const coverage = buildCoverage(result)
  const composed = composeArgument(reading)

  const questionFrame: QuestionFrame | null = input.question_frame ?? null

  const envelope = makeKalaEnvelope<ArgumentReading>({
    reading,
    questionFrame,
    fieldSnapshotId: buildFieldSnapshotIdStub({
      ph_muhurta_queried_at: result.provenance_envelope?.queried_at ?? null,
    }),
    triPlane: {
      // ELECT is itself an interpretation of the chart's dasha/transit/panchanga stack —
      // it is not the interpretation plane, so it points there.
      interpretation_ref: pointerTo('get_domain_reading', 'the domain reading behind why this undertaking\'s window scores as it does for this chart'),
      prediction_ref: pointerTo('kala_bundle_get', 'the forward temporal field this election sits inside'),
      // ND-1 (ṢAḌ-DARŚANA W1 verify-reopen, 2026-07-30): was a bare `null`. See ahead.ts's
      // prediction_ref for the full rationale — the campaign's own tri_plane_no_dead_end_gate.ts
      // already grades a bare null `WARN` ("not independently verifiable at v0"); an honest,
      // self-describing `no_lever` states the same fact in the shape the contract provides.
      intervention_ref: noLeverPointer(
        'kala_elect_get IS the intervention plane — the election candidates in this response '
          + 'ARE the intervention lever, so there is no further intervention surface to '
          + 'traverse to. Not a missing pointer: a terminal by construction. (The '
          + 'UPĀYA/YAJÑA-tier levers, kala_upaya_get / kala_ritual_get, are W0 stubs whose '
          + 'real engines land at wave W4 — pointing at them today would be a live pointer '
          + 'to content that does not exist yet.)',
      ),
    },
    coverage,
    freshness: buildKalaFreshness({
      ephemerisVersion: null,
      sweepBuildDate: null,
      fieldHash: null,
    }),
    calibrationMaturity: noLelCalibrationMaturity(),
  })

  const candidates: KalaElectCandidate[] = (result.windows ?? []).map((w) => {
    const grade = gradeCandidate({ score: w.score, disqualified: w.disqualified ?? false })
    return {
      start: w.start,
      end: w.end,
      score: w.score,
      hard_flag: w.hard_flag ?? false,
      disqualified: w.disqualified ?? false,
      rank_penalty_reason: w.rank_penalty_reason ?? [],
      drivers: windowDrivers(w),
      source_citation: w.source_citation,
      grading_tier: grade.tier,
      grading_tier_label: grade.tier_label,
      hora_ladder: w.hora_ladder ?? [],
    }
  })

  const gapReport = candidates.length === 0
    ? (result.empty_reason ?? `no candidate windows computed for ${input.undertaking} in ${dateRange.start}..${dateRange.end}`)
    : (candidates.every((c) => c.disqualified)
      ? 'every candidate in this horizon carries a hard veto — widen the date range or supply native_janma_nakshatra/target_graha context to re-check'
      : null)

  // ELECT frontier statement v0 (item 38-lite's sibling deliverable, E6) — built from the
  // SAME already-graded candidates, never a second scoring pass.
  const frontier = buildFrontierStatement(
    candidates.map((c) => ({ start: c.start, end: c.end, score: c.score, disqualified: c.disqualified })),
    input.undertaking,
    dateRange,
    result.empty_reason ?? null,
  )

  const response: KalaElectResponse = {
    ...envelope,
    tool: 'kala_elect_get',
    chart_id: input.chart_id,
    undertaking: input.undertaking,
    query_window: result.query_window ?? dateRange,
    candidates,
    candidate_count: candidates.length,
    gap_report: gapReport,
    frontier,
    composed_text: composed.full_text,
    ...(result.empty_reason ? { empty_reason: result.empty_reason } : {}),
  }

  const sections: TrimmableSection<KalaElectResponse>[] = [
    kalaEvidenceTrimmableSection<KalaElectResponse>({ instrument: 'kala_elect_get', hint: 'call again with a narrower date_range for full evidence' }),
    {
      path: 'candidates',
      label: 'candidate windows',
      minKeep: 1,
      getArray: (c) => c.candidates,
      setArray: (c, kept) => { c.candidates = kept as KalaElectCandidate[] },
      recover: { instrument: 'kala_elect_get', hint: 'call again with a smaller limit or narrower date_range' },
    },
  ]

  const budgeted = finalizeMcpBudget(response as unknown as Record<string, unknown>, {
    maxKb: input.budget_kb ?? 40,
    sections: sections as unknown as TrimmableSection<Record<string, unknown>>[],
    budgetKbRequested: input.budget_kb,
  }) as unknown as KalaElectResponse

  return { response: budgeted }
}

// ── MCP registration ────────────────────────────────────────────────────────────────
// ONE canonical registration site for kala_elect_get (SHAD_DARSHANA_BRIEF_v2_0.md §2 file
// map). Mirrors the sibling kala_views registrations (priority.ts's
// registerKalaPriorityTool, etc.) — registry_bridge.ts imports and calls this function.

function dualOutput(data: unknown): { structuredContent: { type: 'object'; object: unknown }; content: [{ type: 'text'; text: string }] } {
  return { structuredContent: { type: 'object', object: data }, content: [{ type: 'text', text: JSON.stringify(data) }] }
}

function errorOutput(tool: string, message: string, extra?: Record<string, unknown>) {
  return { ...dualOutput({ ok: false, error: message, tool, ...extra }), isError: true as const }
}

export function registerKalaElectTool(server: McpServer, principal: Principal): void {
  server.tool(
    'kala_elect_get',
    'ELECT — "When should I act?" The sole server of YAJÑA-SETU Mode 3 (ACTIVITY ELECTION, ' +
    'KALA_SUPREME_ELEVATION_v1_0.md §8): given an undertaking (marriage, travel, business, ' +
    'medical, education, property, spiritual_initiation, remedial_ritual, japa_start, or ' +
    'general) and a date range, returns a ranked slate of candidate act-time windows with ' +
    'per-candidate scoring (panchāṅga × daśā × transit × signal-activation), a gold/silver/' +
    'bronze/marginal grading_tier per candidate (item 38-lite — thin serving-layer ' +
    'normalization, see coverage.candidate_grading_lite), personal-star (tāra-bala) and ' +
    'target-graha vetoes, a top-level frontier statement (best candidate + whether a ' +
    'gold-tier exists in this horizon), and an honest gap report when no clean election ' +
    'exists in the searched horizon. A ritual/yajña question with no named undertaking ' +
    'routes to kala_ritual_get instead (Modes 1-2) — this tool never accepts a bare sky-' +
    'pattern or opportunity-scan query. W1 depth: the full contender-lattice + parihāra ' +
    'adjudication engine (item 36) and ritual pairing (item 38\'s W4 half) are not yet wired ' +
    '— reported honestly via this response\'s coverage block, never silently omitted.',
    KalaElectInputShape,
    async (args) => {
      const parsed = args as KalaElectInput
      if (!parsed.chart_id) return errorOutput('kala_elect_get', 'chart_id is required')
      try {
        const { response, error } = await handleKalaElectGet(parsed, principal)
        if (error) return errorOutput('kala_elect_get', error.message, error.extra)
        return dualOutput(response)
      } catch (err) {
        return errorOutput('kala_elect_get', String(err), { chart_id: parsed.chart_id })
      }
    },
  )
}

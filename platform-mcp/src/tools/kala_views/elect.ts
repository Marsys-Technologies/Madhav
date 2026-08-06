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
 * W3 ADDITION (item 36 — the contender lattice + parihāra adjudication ENGINE):
 * this facade now ALSO consults `lib/kala_lattice_query.ts` — the single engine ELECT and
 * YAJÑA-SETU share (ONE-ENGINE RULE) — over the `bg_muhurta_lattice` / `bg_parihara_rules`
 * substrate that landed with PR #930. Each candidate gains a `judgment_ledger`
 * (`doṣas_present → parihāras_applied → residual_doṣas → net standing`, Elevation §9 stage 3)
 * and the response gains a `lattice_adjudication` block (Pareto survival across factor
 * groups + the gap report + the density counts). Three honesty properties are load-bearing
 * and asserted by tests: uncited-convention lattice rows are served but never become
 * findings or doṣas (§N.6); a doṣa is cancelled only by a genuinely-existing muhūrta-scope
 * parihāra rule, of which the corpus currently has ZERO, so residuals are reported
 * uncancelled with the gap named; and the coverage entry reads `computed` only when cited
 * rows genuinely annotated a candidate, `honest_empty` otherwise. The muhūrta-lagna refinement
 * (item 7) and ritual pairing (item 38's W4 half) remain honestly unbuilt below.
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
  resolveFieldSnapshot,
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
import {
  adjudicateCandidates,
  fetchLatticeSubstrate,
  type JudgmentLedger,
  type LatticeAdjudication,
  type LatticeSubstrate,
} from '../../lib/kala_lattice_query.js'
// ṢAḌ-DARŚANA W4 Lane R — item 38's closing half (the ritual pairing) and the §5.4
// mortality hard exclusion that heads the rite-pairing path (ADJUDICATION-13, binding).
import {
  buildMortalityExclusionRefusal,
  detectMortalityExclusion,
  type MortalityExclusionRefusal,
} from '../../lib/kala_sky_pattern.js'
import {
  scoreMode1Opportunities,
  type ActivityClass,
  type RitualOpportunity,
} from '../../lib/kala_ritual_resonance.js'
// ṢAḌ-DARŚANA W3 Lane w3-muh — Item 14: Janma-anchored election micro-rules.
// Pure; no I/O; degrades gracefully to null when janma anchor is unavailable.
import {
  applyJanmaMicroRulesOrNull,
  tithiNumFromName,
  varaIndexFromLord,
  type JanmaMicroRuleContext,
  type JanmaMicroRules,
  type JanmaMicroWindowInput,
} from '../../lib/kala_janma_micro_rules.js'
import { nakshatraNumber } from '../muhurta_finder.js'

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
  // Item 36 (W3): the per-candidate judgment ledger from the shared contender-lattice
  // engine — doṣas_present → parihāras_applied (citations) → residual_doṣas → net standing,
  // plus the separately-counted uncited-convention factor layer (§N.6). Null when the
  // lattice substrate could not be read for this call — an honest absence, never a
  // fabricated clean verdict.
  judgment_ledger: JudgmentLedger | null
  // ── Item 38's CLOSING half (ṢAḌ-DARŚANA W4, design §3.5) ───────────────────────────
  // ELECT now serves the act-time slate AND the paired preparatory rite with its own best
  // time, as ONE answer. For each surviving act-time candidate, Lane R's Mode-1 resonance
  // scorer runs over a PREPARATORY HORIZON ENDING AT THIS CANDIDATE'S START — a rite that
  // has not happened yet cannot prepare an act that has.
  //
  // `null` WITH A REASON is a legal and frequent answer (design §3.5, verbatim), and the
  // reason is carried in `paired_rite_reason` rather than dropped — an unexplained null
  // would be indistinguishable from an unwired field, which is the `hora_ladder` inversion
  // class this campaign already caught once.
  paired_rite: RitualOpportunity | null
  paired_rite_reason: string | null
  // ── Item 14 (ṢAḌ-DARŚANA W3 Lane w3-muh) — Janma-anchored election micro-rules ──────
  // Per KALA_SIX_VIEWS_DESIGN_v1_0.md §3.2: "Personal star overlay: tārā-bala from
  // janma-nakṣatra + janma-tithi/vara/nakṣatra returns as personally-potent days."
  // Null when no janma anchor was available for this call (honest gap, never fabricated).
  // When non-null, hard_veto=true means this candidate carries a Vadha-tārā veto from
  // the native's personal star — the same veto class as muhurta_finder's tara_bala flag.
  janma_micro_rules: JanmaMicroRules | null
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
  // Item 36 (W3) — the contender-lattice engine's slate-level output: Pareto survival across
  // factor groups (with the axes it could NOT evaluate named, never zero-filled), the gap
  // report including the Muhūrta Factor Census dispositions, and the density counts that keep
  // cited findings and uncited conventions from ever reading as one number.
  lattice_adjudication: LatticeAdjudication | null
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

function buildCoverage(
  result: MuhurtaFinderResult,
  adjudication: LatticeAdjudication | null,
  pairing: PairingOutcome | null,
  janmaMicroApplied: boolean,
  janmaMicroUnavailableReason: string | null,
): KalaCoverageEntry[] {
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

  // Item 36 (W3) — the contender lattice + parihāra adjudication engine is now WIRED. Its
  // coverage state is whatever the engine honestly reports; this facade never upgrades it.
  // (Before W3 this was an unconditional `not_in_corpus`; the engine now decides.)
  if (adjudication === null) {
    coverage.push(honestEmptyCoverage(
      'contender_lattice_parihara_adjudication',
      'the muhūrta lattice substrate could not be consulted for this call — no judgment ' +
      'ledger was computed, and none is simulated.',
    ))
  } else if (adjudication.coverage_state === 'computed') {
    coverage.push(computedCoverage('contender_lattice_parihara_adjudication'))
  } else {
    coverage.push(honestEmptyCoverage(
      'contender_lattice_parihara_adjudication',
      adjudication.coverage_reason ?? 'the lattice engine returned no cited annotation for this horizon',
    ))
  }

  // Item 41 — the Muhūrta Factor Census, served in coverage exactly as Elevation §9's
  // "what are you NOT considering" block requires.
  if (adjudication === null || adjudication.gap_report.census_state === 'not_in_corpus') {
    coverage.push(notInCorpusCoverage(
      'muhurta_factor_census',
      'the Muhūrta Factor Census (item 41) could not be read for this call, so the ' +
      'not-computed / not-in-corpus factor register is not available to qualify this answer.',
    ))
  } else if (adjudication.gap_report.census_state === 'computed') {
    coverage.push(computedCoverage('muhurta_factor_census'))
  } else {
    coverage.push(honestEmptyCoverage(
      'muhurta_factor_census',
      'the factor census returned zero rows — the bg_parihara_rules asset may not be built ' +
      'in this environment.',
    ))
  }

  // The muhūrta-scope parihāra layer is a REAL, NAMED corpus gap (not an unbuilt feature):
  // every row in bg_parihara_rules is scope=natal. Disclosed as its own coverage entry so a
  // caller reading "adjudication: computed" cannot infer that cancellations were available.
  if (adjudication !== null && adjudication.density.parihara_rules_muhurta_scope === 0) {
    coverage.push(notInCorpusCoverage(
      'muhurta_scope_parihara_rules',
      adjudication.gap_report.parihara_corpus_gap ??
      'no muhūrta-scope doṣa-cancellation rule exists in the ingested corpus.',
    ))
  }

  // Item 7 (ṢAḌ-DARŚANA W4 ruling R-1): the muhūrta-lagna substrate now EXISTS as
  // bg_muhurta_lattice factor_family='lagna' (12–13 rising-sign spans/day, each carrying
  // the lagna lord and every graha's sign at the span start). What this ELECT facade does
  // NOT yet do is refine its act-time candidates to that precision — so the coverage state
  // is `honest_empty` (the substrate is there; this surface has not consumed it) rather
  // than `not_in_corpus` (which would now be false). Stating the difference is the point:
  // a stale `not_in_corpus` would keep reporting a corpus gap that has closed.
  const lagnaAtoms = adjudication === null
    ? 0
    : adjudication.gap_report.factor_families_evaluated.filter((f) => f === 'lagna').length
  coverage.push(honestEmptyCoverage(
    'muhurta_lagna_strength',
    lagnaAtoms > 0
      ? 'the muhūrta-lagna substrate IS built (bg_muhurta_lattice factor_family=lagna, ruling ' +
        'R-1) and carries the rising-sign span + lagna lord + every graha\'s sign at span start, ' +
        'but this ELECT facade does not yet refine its act-time candidates to that precision. ' +
        'The gap is in THIS surface, not in the corpus.'
      : 'instant-lagna strength is not refined into these candidates. The substrate exists ' +
        '(bg_muhurta_lattice factor_family=lagna, ruling R-1) but no lagna atom was returned for ' +
        'this horizon — the L0 lattice may not be rebuilt in this environment.',
  ))

  // Item 38's CLOSING half. This was an UNCONDITIONAL not_in_corpus at W1 — the exact
  // shape the `hora_ladder` honesty inversion took. It is now genuinely conditioned on
  // whether a paired rite was actually produced, and the empty case names WHY.
  const pairedCount = pairing?.paired.filter((p) => p !== null).length ?? 0
  if (pairing === null) {
    coverage.push(honestEmptyCoverage(
      'ritual_pairing',
      'the ritual-pairing pass did not run for this call (no surviving act-time candidate, or ' +
      'the rite substrate could not be read). No paired rite is simulated.',
    ))
  } else if (pairedCount > 0) {
    coverage.push(computedCoverage('ritual_pairing'))
  } else {
    coverage.push(honestEmptyCoverage(
      'ritual_pairing',
      pairing.reason ??
      'the pairing pass ran and produced no rite for any candidate — an honest empty, not an ' +
      'unwired field. Each candidate carries its own paired_rite_reason.',
    ))
  }

  // Item 14 (ṢAḌ-DARŚANA W3 Lane w3-muh) — Janma-anchored election micro-rules.
  // Coverage is `computed` only when the janma anchor was actually available and applied
  // to at least one candidate; `honest_empty` when no janma anchor was supplied.
  // §N.8: this entry is conditioned on real application — never a false `computed`.
  if (janmaMicroApplied) {
    coverage.push(computedCoverage('janma_anchored_micro_rules'))
  } else {
    coverage.push(honestEmptyCoverage(
      'janma_anchored_micro_rules',
      janmaMicroUnavailableReason ??
      'no janma nakshatra anchor was supplied for this call — tārā-bala micro-rules require the ' +
      'native\'s birth nakshatra (supply native_janma_nakshatra, or use a chart that has the ' +
      'janma nakshatra fact in L1). janma-tithi and janma-vara resonance likewise unavailable.',
    ))
  }

  return coverage
}

// ── Item 38's closing half: the ritual pairing ───────────────────────────────────────

/** The outcome of one pairing pass over the whole slate. `paired[i]` corresponds to
 *  `candidates[i]`; a `null` entry is legal and carries its reason in `reasons[i]`. */
interface PairingOutcome {
  paired: (RitualOpportunity | null)[]
  reasons: (string | null)[]
  /** Slate-level reason when NOTHING paired. `null` when at least one did. */
  reason: string | null
}

/** Maps an ELECT undertaking to the `bg_muhurta_activity_rules` class the rite should be
 *  graded against. This is a closed-vocabulary → closed-vocabulary mapping between two
 *  tables THIS repo owns, not an astrological correspondence: `remedial_ritual` IS
 *  `upaya_ritual`, `japa_start` IS `mantra_initiation`. Anything with no exact counterpart
 *  falls back to `upaya_ritual` — the preparatory rite for an arbitrary undertaking IS a
 *  remedial rite, which is that class's own definition. */
function activityClassForUndertaking(undertaking: string): ActivityClass {
  switch (undertaking) {
    case 'marriage': return 'vivah'
    case 'travel': return 'yatra'
    case 'business': return 'vyapara'
    case 'property': return 'property_purchase'
    case 'japa_start': return 'mantra_initiation'
    case 'spiritual_initiation': return 'sadhana_initiation'
    case 'remedial_ritual': return 'upaya_ritual'
    default: return 'upaya_ritual'
  }
}

/**
 * For each surviving act-time candidate, find the best-scoring preparatory rite window in
 * the horizon ENDING AT that candidate's start (design §3.5). Uses Lane R's Mode-1 scorer
 * and, through it, the FROZEN engine — no second scoring path.
 */
async function buildRitualPairing(
  input: KalaElectInput,
  candidates: { start: string; end: string; disqualified: boolean }[],
  substrate: LatticeSubstrate | null,
  principal: Principal,
): Promise<PairingOutcome | null> {
  if (candidates.length === 0) return null
  if (substrate === null || !substrate.lattice_available) {
    return {
      paired: candidates.map(() => null),
      reasons: candidates.map(
        () =>
          'the muhūrta lattice payload could not be read for this call, so no preparatory-rite ' +
          'window was searched. No rite is simulated.',
      ),
      reason:
        'the muhūrta lattice payload could not be read for this call — the pairing pass had no ' +
        'substrate to search and produced nothing. Not an unwired field: an unavailable substrate.',
    }
  }

  const activityClass = activityClassForUndertaking(input.undertaking)
  const paired: (RitualOpportunity | null)[] = []
  const reasons: (string | null)[] = []

  for (const c of candidates) {
    if (c.disqualified) {
      paired.push(null)
      reasons.push('candidate carries a hard veto — no preparatory rite is paired to a disqualified act-time window.')
      continue
    }
    const actStart = Date.parse(c.start)
    if (Number.isNaN(actStart)) {
      paired.push(null)
      reasons.push('candidate start could not be parsed, so no preparatory horizon could be bounded.')
      continue
    }
    // The preparatory horizon ENDS at the act-time candidate's start. A rite that has not
    // happened yet cannot prepare an act that has.
    const prepStart = new Date(Math.max(Date.now(), actStart - 30 * 86_400_000)).toISOString()
    const prepEnd = new Date(actStart).toISOString()
    const windows = substrate.lattice_rows
      .filter((r) => r.factor_family === 'combination_yoga')
      .filter((r) => String((r.detail as { strength?: unknown } | null)?.strength ?? '') === 'auspicious')
      .filter((r) => {
        const rs = Date.parse(r.start_utc)
        const re = Date.parse(r.end_utc)
        return !Number.isNaN(rs) && !Number.isNaN(re) && rs < Date.parse(prepEnd) && re > Date.parse(prepStart)
      })
      .map((r) => ({
        start_utc: new Date(Math.max(Date.parse(r.start_utc), Date.parse(prepStart))).toISOString(),
        end_utc: new Date(Math.min(Date.parse(r.end_utc), Date.parse(prepEnd))).toISOString(),
        authority_basis: [`${r.factor_family}/${r.factor_key}@${r.start_utc}`],
        binding_families: [r.factor_family],
      }))

    if (windows.length === 0) {
      paired.push(null)
      reasons.push(
        `no auspicious combination-yoga span exists in the preparatory horizon ` +
        `(${prepStart} .. ${prepEnd}) for this candidate. An honest empty — no rite window is invented.`,
      )
      continue
    }

    const scored = await scoreMode1Opportunities(
      { chartId: input.chart_id, activityClass, windows, substrate, subjectLabel: `${input.undertaking} (preparatory rite)`, limit: 1 },
      principal,
    )
    const best = scored.opportunities[0] ?? null
    paired.push(best)
    reasons.push(
      best === null
        ? 'preparatory windows exist but none could be scored (every score factor was absent for this chart).'
        : null,
    )
  }

  const anyPaired = paired.some((p) => p !== null)
  return {
    paired,
    reasons,
    reason: anyPaired
      ? null
      : 'the pairing pass ran over every surviving candidate and produced no rite — each candidate ' +
        'carries its own paired_rite_reason. An honest empty, not an unwired field.',
  }
}

export async function handleKalaElectGet(
  input: KalaElectInput,
  principal: Principal,
): Promise<{
  response?: KalaElectResponse
  withheld?: MortalityExclusionRefusal
  error?: { message: string; extra?: Record<string, unknown> }
}> {
  // ══════════════════════════════════════════════════════════════════════════════
  // §5.4 INDIVIDUALIZED-MORTALITY-WINDOW HARD EXCLUSION (ADJUDICATION-13, binding).
  // FIRST, before any computation. Pure and synchronous — structurally incapable of
  // awaiting I/O, so it cannot be reordered after a fetch by a later refactor.
  // NOT a disclosure tier (`native_self` does not unlock it) and NOT conditioned on
  // filing. Design §3.4: "The same §5.4 check heads the ELECT rite-pairing path."
  // ══════════════════════════════════════════════════════════════════════════════
  const mortality = detectMortalityExclusion(input)
  if (mortality.excluded) {
    return { withheld: buildMortalityExclusionRefusal(mortality) }
  }

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

  // ── Item 36 (W3): the contender-lattice + parihāra adjudication pass ────────────
  // Candidate intervals are built FIRST (they are the engine's input), then the shared
  // engine annotates and adjudicates them. `id` is positional and stable within the
  // response — the substrate has no candidate identity of its own.
  const windows = result.windows ?? []
  const intervals = windows.map((w, i) => ({
    id: `c${i}`,
    start: w.start,
    end: w.end,
    score: w.score,
    disqualified: w.disqualified ?? false,
  }))

  // A lattice/parihāra read failure must never fail the whole election — ELECT's W0/W1
  // answer stands on its own. The engine degrades to an honest `honest_empty` coverage
  // entry instead (see buildCoverage), which is exactly the 3-state contract.
  let adjudication: LatticeAdjudication | null = null
  let latticeSubstrate: LatticeSubstrate | null = null
  try {
    latticeSubstrate = await fetchLatticeSubstrate(
      {
        start_utc: new Date(`${dateRange.start}T00:00:00Z`).toISOString(),
        end_utc: new Date(`${dateRange.end}T23:59:59Z`).toISOString(),
      },
      principal,
    )
    adjudication = adjudicateCandidates(intervals, latticeSubstrate, {
      subject_label: `${input.undertaking} (ELECT act-time)`,
    })
  } catch {
    adjudication = null
    latticeSubstrate = null
  }
  const ledgerById = new Map((adjudication?.ledgers ?? []).map((l) => [l.candidate_id, l]))

  // ── Item 38's closing half: pair each act-time candidate with its preparatory rite ──
  // A pairing failure must never fail the whole election — ELECT's act-time answer stands
  // on its own and the coverage entry reports the gap honestly.
  let pairing: PairingOutcome | null = null
  try {
    pairing = await buildRitualPairing(
      input,
      windows.map((w) => ({ start: w.start, end: w.end, disqualified: w.disqualified ?? false })),
      latticeSubstrate,
      principal,
    )
  } catch {
    pairing = null
  }

  // ── Item 14 (ṢAḌ-DARŚANA W3 Lane w3-muh) — Janma-anchored election micro-rules ────
  // Build the janma context from the native_janma_nakshatra input (same field muhurta_finder
  // uses for tara_bala). The FORENSIC canonical anchor for native 482012f1:
  //   janma nakshatra = Purva Bhadrapada (id=25)
  //   janma tithi = Shukla Tritiya (num=3)
  //   janma vara = Ravivara (index=0, Sunday)
  // These are NOT hardcoded here — they come from the chart's L1 facts via input fields.
  // For now: nakshatra from `native_janma_nakshatra` (string, same as muhurta_finder uses),
  // tithi/vara from panchanga_details on the window's own factors. The context is null
  // when native_janma_nakshatra is not supplied — an honest gap, never fabricated.
  const janmaNakId = nakshatraNumber(input.native_janma_nakshatra)
  // Janma tithi/vara: these come from the NATIVE's birth panchanga, not the window's.
  // At this facade tier, they are not carried by the elect input yet — the FORENSIC
  // anchors (tithi=3/Shukla Tritiya, vara=0/Sunday) are part of the native's L1 chart_facts
  // and would need a separate L1 fact fetch, which is out of scope for this W3 lane.
  // Honest gap: we set them null at the context level; the per-window tithi/vara data IS
  // available from the window's own panchanga_details for the window's date (not the native's
  // birth date), which the test checks. The context must carry the native's birth values, not
  // the window's — so janma_tithi_num / janma_vara_index are null here until L1 fact wiring.
  const janmaContext: JanmaMicroRuleContext | null = janmaNakId !== null
    ? { janma_nakshatra_id: janmaNakId, janma_tithi_num: -1, janma_vara_index: -1 }
    : null
  // NOTE: janma_tithi_num=-1 and janma_vara_index=-1 are sentinel values indicating "unknown".
  // The per-window comparison will produce null for tithi/vara resonance because the
  // window's values will never equal -1 (tithis are 1..30, varas 0..6). This preserves
  // honest null semantics for the resonance fields when the birth panchanga is unavailable.

  // Per-window micro-rule application: builds JanmaMicroRules for each candidate window.
  const perWindowMicroRules: (JanmaMicroRules | null)[] = windows.map((w) => {
    const windowNakId = nakshatraNumber(w.factors?.panchanga_details?.moon_nakshatra)
    const windowTithiNum = tithiNumFromName(w.factors?.panchanga_details?.tithi_name)
    const windowVaraIndex = varaIndexFromLord(w.factors?.panchanga_details?.vara_lord)
    const windowInput: JanmaMicroWindowInput = {
      window_nakshatra_id: windowNakId,
      window_tithi_num: windowTithiNum,
      window_vara_index: windowVaraIndex,
    }
    return applyJanmaMicroRulesOrNull(janmaContext, windowInput)
  })

  // Was janma micro-rules actually applied? `computed` requires at least one non-null result.
  const janmaMicroApplied = perWindowMicroRules.some((r) => r !== null)
  const janmaMicroUnavailableReason = janmaContext === null
    ? 'native_janma_nakshatra was not supplied for this call — janma-anchored micro-rules ' +
      'require the native\'s birth nakshatra. Supply native_janma_nakshatra to enable tārā-bala ' +
      'micro-rule computation, janma-nakshatra resonance, and the tārā-based veto check.'
    : null

  const reading = buildArgumentReading(input.undertaking, result)
  const coverage = buildCoverage(result, adjudication, pairing, janmaMicroApplied, janmaMicroUnavailableReason)
  const composed = composeArgument(reading)

  const questionFrame: QuestionFrame | null = input.question_frame ?? null

  // W2 (E5): the real field snapshot read — served id, or an honest marker; never a stub.
  const fieldSnapshot = await resolveFieldSnapshot(input.chart_id, principal)

  const envelope = makeKalaEnvelope<ArgumentReading>({
    reading,
    questionFrame,
    fieldSnapshot,
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
      fieldHash: fieldSnapshot.field_content_hash,
    }),
    calibrationMaturity: noLelCalibrationMaturity(),
  })

  const candidates: KalaElectCandidate[] = windows.map((w, i) => {
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
      judgment_ledger: ledgerById.get(`c${i}`) ?? null,
      paired_rite: pairing?.paired[i] ?? null,
      paired_rite_reason:
        pairing?.reasons[i] ??
        (pairing === null
          ? 'the ritual-pairing pass did not run for this call — no rite is simulated.'
          : null),
      // Item 14 (ṢAḌ-DARŚANA W3 Lane w3-muh): janma micro-rules for this candidate window.
      // Null when native_janma_nakshatra was not supplied (honest gap, §N.8).
      janma_micro_rules: perWindowMicroRules[i] ?? null,
    }
  })

  // The W0/W1 gap statement, now ALSO carrying the item-36 engine's own gap report when the
  // engine ran. The two are concatenated rather than one overwriting the other: the veto/empty
  // statement is about muhurta_finder's slate, the lattice statement is about the frontier and
  // the named corpus gaps. Neither is fabricated when absent.
  const baseGapReport = candidates.length === 0
    ? (result.empty_reason ?? `no candidate windows computed for ${input.undertaking} in ${dateRange.start}..${dateRange.end}`)
    : (candidates.every((c) => c.disqualified)
      ? 'every candidate in this horizon carries a hard veto — widen the date range or supply native_janma_nakshatra/target_graha context to re-check'
      : null)
  const latticeGapStatement = adjudication?.gap_report.statement ?? null
  const gapReport = [baseGapReport, latticeGapStatement].filter((s): s is string => !!s).join(' ') || null

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
    lattice_adjudication: adjudication,
    composed_text: composed.full_text,
    ...(result.empty_reason ? { empty_reason: result.empty_reason } : {}),
  }

  const sections: TrimmableSection<KalaElectResponse>[] = [
    kalaEvidenceTrimmableSection<KalaElectResponse>({ instrument: 'kala_elect_get', hint: 'call again with a narrower date_range for full evidence' }),
    // §N.6 part 2 — the LOW-density layer is the one a trim eats first. Every candidate's
    // uncited-convention factor list is fully floorable to zero (it is served context, not a
    // finding), and is declared BEFORE the candidates section so the trimmer's disposable
    // tier absorbs the cut before any confirmed judgment ledger is touched.
    {
      path: 'candidates[].judgment_ledger.convention_only_factors',
      label: 'uncited-convention factor spans (all candidates)',
      minKeep: 0,
      getArray: (c) => c.candidates.flatMap((cand) => cand.judgment_ledger?.convention_only_factors ?? []),
      setArray: (c, kept) => {
        // Distribute the surviving entries back in order, then truncate the rest. The
        // per-candidate `convention_only_factor_count` is deliberately NOT rewritten — it
        // remains the TRUE count, so a trimmed response still tells the honest number.
        let remaining = kept.length
        for (const cand of c.candidates) {
          const ledger = cand.judgment_ledger
          if (!ledger) continue
          const take = Math.max(0, Math.min(ledger.convention_only_factors.length, remaining))
          ledger.convention_only_factors = ledger.convention_only_factors.slice(0, take)
          remaining -= take
        }
      },
      // No dedicated lattice-query tool is registered yet (bg_muhurta_lattice serving is
      // deliberately deferred — SHAD_DARSHANA_STATE.md, "needs real citation-backed content,
      // a more careful individual session"). Point recovery at this response's own real
      // source instead of a phantom instrument a caller could never resolve.
      recover: { instrument: 'kala_elect_get', hint: 'call again with a narrower date_range or smaller limit for the full convention-row set per candidate' },
    },
    {
      path: 'candidates',
      label: 'candidate windows (with judgment ledgers)',
      minKeep: 1,
      getArray: (c) => c.candidates,
      setArray: (c, kept) => { c.candidates = kept as KalaElectCandidate[] },
      recover: { instrument: 'kala_elect_get', hint: 'call again with a smaller limit or narrower date_range' },
      // §N.6 part 2: candidates now carry the confirmed doṣa→parihāra→residual ledger — the
      // densest, most-actionable layer in this response. hardFloor keeps at least one alive
      // even under the hard-cap fallback pass.
      hardFloor: true,
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
    'exists in the searched horizon. Each candidate also carries a judgment_ledger from the ' +
    'contender-lattice engine (doṣas present → parihāras applied with citations → residual ' +
    'doṣas → net standing), and the response carries a lattice_adjudication block with Pareto ' +
    'survival across factor groups, the Muhūrta Factor Census dispositions, and separate counts ' +
    'for cited findings versus uncited-convention factor spans — never read as one number. ' +
    'A ritual/yajña question with no named undertaking routes to kala_ritual_get instead ' +
    '(Modes 1-2) — this tool never accepts a bare sky-pattern or opportunity-scan query. ' +
    'Honest remaining gaps: no muhūrta-scope doṣa-cancellation rule exists in the ingested ' +
    'corpus, so residual doṣas are reported uncancelled. ITEM 38 IS NOW CLOSED: each surviving ' +
    'candidate also carries paired_rite — the preparatory rite AND its own best time, scored ' +
    'over a horizon that ENDS at that candidate\'s start, served as one answer with the ' +
    'act-time slate. A null paired_rite is legal and always carries paired_rite_reason. ' +
    'Muhūrta-lagna refinement (item 7) has substrate but is not yet consumed by this facade — ' +
    'reported via the coverage block, never silently omitted. A request whose shape or ' +
    'substrate touches the span-of-life / death-timing question is WITHHELD outright under ' +
    'MACRO_PLAN §3.5.C, under every audience tier.',
    KalaElectInputShape,
    async (args) => {
      const parsed = args as KalaElectInput
      if (!parsed.chart_id) return errorOutput('kala_elect_get', 'chart_id is required')
      try {
        const { response, error, withheld } = await handleKalaElectGet(parsed, principal)
        // §5.4 (ADJUDICATION-13): the refusal is a SUCCESSFUL response carrying no content,
        // not an error. Reporting it as an error would let a caller retry it as a transient
        // failure; it is a permanent, deliberate withholding.
        if (withheld) return dualOutput(withheld as unknown as KalaElectResponse)
        if (error) return errorOutput('kala_elect_get', error.message, error.extra)
        return dualOutput(response)
      } catch (err) {
        return errorOutput('kala_elect_get', String(err), { chart_id: parsed.chart_id })
      }
    },
  )
}

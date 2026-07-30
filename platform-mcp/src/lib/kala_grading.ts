/**
 * kala_grading.ts — ṢAḌ-DARŚANA W1 item 38-lite (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1
 * "38-lite (grading-engine facade unifying ELECT candidate output)"; §2 file map names
 * this exact path — `lib/kala_grading.ts` — as "the candidate grading engine (score
 * vector → tier → ledgers)", the FULL version of which is item 36/38's W3 job
 * (KALA_SUPREME_ELEVATION_v1_0.md §9 "THE CONTENDER ALGORITHM" — Pareto survival across
 * factor GROUPS, the doṣa→parihāra judgment ledger, the gap report). This file is the
 * W1-LITE first version: a thin SERVING-LAYER normalization, not a new judgment engine.
 * ==========================================================================
 * WHAT THIS FILE DOES: labels an already-scored ELECT candidate (score ∈ [0,1],
 * `disqualified`/`hard_flag` — all computed upstream by `muhurta_finder.ts`/PH-4-4) with a
 * tier drawn from the SAME gold/silver vocabulary KALA_SUPREME_ELEVATION_v1_0.md §9's own
 * gap-report example already uses ("9 Aug (gold — two of four ideals, no residual doṣa),
 * 21 Aug (silver — bhadrā present but cancelled by Abhijit...)"). It does NOT compute a new
 * score, does NOT evaluate doṣas/parihāras (that requires the item 36 lattice, not built
 * yet), and does NOT rank across factor GROUPS (Pareto survival) — it is a single-scalar
 * tiering of the score the substrate already produced, thin by design.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════
 * DOCUMENTED CONVENTION (explicit, per the brief's "state it explicitly" requirement for
 * every lite placeholder in this wave): the tier thresholds below (0.75/0.55/0.35) are a
 * CONSERVATIVE, DOCUMENTED DEFAULT chosen for this lite facade — they are NOT derived from
 * the corpus or from any calibrated distribution (no reference cohort exists yet, item 22,
 * W2). They exist only to give ELECT's already-computed score a human-legible label using
 * the vocabulary the design doc itself reaches for. W3's real contender-lattice grading
 * engine (item 36) supersedes this file's tiering with a doṣa/parihāra-aware, multi-axis
 * Pareto-survival grade — this file's job ends there; it does not pre-empt that design.
 *
 * WHAT THIS FILE IS NOT (W1-lite scope discipline):
 *   - It does NOT implement the contender lattice, parihāra graph, or Pareto survival
 *     (item 36, W3) — `lib/kala_lattice_query.ts` in the brief's file map is that engine.
 *   - It does NOT invent a new astrological judgment (B.10) — every input to `gradeCandidate`
 *     is a value the caller already computed; this file only labels it.
 */

export type CandidateGradingTier = 'gold' | 'silver' | 'bronze' | 'marginal' | 'disqualified'

export interface CandidateGrade {
  tier: CandidateGradingTier
  tier_label: string
  basis: string
  convention_id: 'lite_v0_score_threshold'
}

export interface GradableCandidate {
  score: number
  disqualified: boolean
}

interface TierThreshold {
  tier: Exclude<CandidateGradingTier, 'disqualified'>
  min: number
  label: string
}

/** The lite-v0 threshold table — see the documented-convention note above. Ordered
 *  highest-first; the first threshold the candidate's score clears wins. */
const TIER_THRESHOLDS: readonly TierThreshold[] = [
  { tier: 'gold', min: 0.75, label: 'Gold — strong convergence across the already-scored factors' },
  { tier: 'silver', min: 0.55, label: 'Silver — solid but not ideal' },
  { tier: 'bronze', min: 0.35, label: 'Bronze — usable, meaningfully weaker than the top candidates' },
  { tier: 'marginal', min: 0, label: 'Marginal — weak convergence; consider widening the search' },
]

/**
 * Grades one already-scored candidate. Pure function — no network, no new astrological
 * computation. `disqualified` (a hard tāra-bala/target-graha veto, already computed
 * upstream) always wins over the score: a disqualified candidate is never labeled gold.
 */
export function gradeCandidate(candidate: GradableCandidate): CandidateGrade {
  if (candidate.disqualified) {
    return {
      tier: 'disqualified',
      tier_label: 'Disqualified — a hard veto (personal-star tāra-bala or target-graha transit) applies',
      basis: 'disqualified flag, already computed upstream by muhurta_finder — never re-derived here',
      convention_id: 'lite_v0_score_threshold',
    }
  }
  const clamped = Number.isFinite(candidate.score) ? Math.max(0, Math.min(1, candidate.score)) : 0
  const matched = TIER_THRESHOLDS.find((t) => clamped >= t.min) ?? TIER_THRESHOLDS[TIER_THRESHOLDS.length - 1]!
  return {
    tier: matched.tier,
    tier_label: matched.label,
    basis: `auspiciousness_score=${clamped.toFixed(2)} vs lite-v0 threshold table (documented placeholder — not corpus-calibrated; W3 item 36 supersedes)`,
    convention_id: 'lite_v0_score_threshold',
  }
}

// ── Frontier statement (E6 — KALA_SUPREME_ELEVATION_v1_0.md §6 "ELECT → the frontier, not
// just the slate"; SHAD_DARSHANA_BRIEF_v2_0.md §3 W1 "ELECT frontier statement v0") ──────
// v0 scope: summarize the best-available candidate and whether a higher tier exists in the
// searched horizon — NOT the full W3 gap-report engine (next-occurrence search beyond the
// horizon, doṣa/parihāra ledgers, Pareto near-frontier band). Honest-empty when nothing
// qualifies, per the absence-of-expected discipline used elsewhere in this campaign.

export interface FrontierCandidateSummary {
  start: string
  end: string
  score: number
  tier: CandidateGradingTier
  tier_label: string
}

export interface FrontierStatement {
  statement: string
  candidate_count: number
  best: FrontierCandidateSummary | null
  best_tier: CandidateGradingTier | null
  gold_tier_present: boolean
  convention_id: 'lite_v0_frontier'
}

export interface FrontierCandidateInput {
  start: string
  end: string
  score: number
  disqualified: boolean
}

/**
 * Builds the v0 frontier statement from an already-graded candidate list (this file's own
 * `gradeCandidate` output joined back onto each candidate). Never fabricates a "next
 * occurrence beyond the horizon" date — that requires the W3 gap-report engine's search;
 * v0 states honestly that it does not have that answer yet rather than inventing one.
 */
export function buildFrontierStatement(
  candidates: FrontierCandidateInput[],
  undertaking: string,
  dateRange: { start: string; end: string },
  emptyReason: string | null,
): FrontierStatement {
  const live = candidates.filter((c) => !c.disqualified)
  if (live.length === 0) {
    const reason = emptyReason ?? `no candidate windows computed for ${undertaking} in ${dateRange.start}..${dateRange.end}`
    return {
      statement:
        `No candidates for ${undertaking} in the searched horizon (${dateRange.start}..${dateRange.end}): ${reason}. ` +
        'The next occurrence beyond this horizon is not yet computed at this build tier — the full ' +
        'frontier/gap-report search (item 36, W3) will answer that; widen date_range to check manually.',
      candidate_count: 0,
      best: null,
      best_tier: null,
      gold_tier_present: false,
      convention_id: 'lite_v0_frontier',
    }
  }
  const graded = live
    .map((c) => ({ ...c, grade: gradeCandidate({ score: c.score, disqualified: c.disqualified }) }))
    .sort((a, b) => b.score - a.score)
  const best = graded[0]!
  const goldPresent = graded.some((c) => c.grade.tier === 'gold')
  const bestSummary: FrontierCandidateSummary = {
    start: best.start, end: best.end, score: best.score, tier: best.grade.tier, tier_label: best.grade.tier_label,
  }
  const statement = goldPresent
    ? `${live.length} candidate${live.length === 1 ? '' : 's'} found for ${undertaking} in ${dateRange.start}..${dateRange.end}; ` +
      `best is ${best.start} → ${best.end} (${best.grade.tier}, score ${best.score.toFixed(2)}).`
    : `${live.length} candidate${live.length === 1 ? '' : 's'} found for ${undertaking} in ${dateRange.start}..${dateRange.end}, ` +
      `none reaching gold tier; the best available is ${best.start} → ${best.end} (${best.grade.tier}, score ${best.score.toFixed(2)}). ` +
      'A higher-tier opportunity may exist beyond this horizon — widen date_range to check (the full ' +
      'frontier/gap-report engine with next-occurrence search lands at W3, item 36).'
  return {
    statement,
    candidate_count: live.length,
    best: bestSummary,
    best_tier: best.grade.tier,
    gold_tier_present: goldPresent,
    convention_id: 'lite_v0_frontier',
  }
}

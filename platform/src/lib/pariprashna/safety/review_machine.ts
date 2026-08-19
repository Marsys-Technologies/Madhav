/**
 * Paripraśna safety — THE HS-3/HS-4 REVIEW STATE MACHINE (lane G1-A).
 *
 * SAFETY_PRIVACY_TENANCY §2 HS-3, quoted because every clause of it is load-
 * bearing: "(1) the reading is composed and SEALED-PENDING (persisted, not
 * streamed beyond an acknowledgment); (2) TWO INDEPENDENT adversarial review
 * passes run against the sealed reading (DISTINCT models/contexts, prompted to
 * refute grounding, calibration language, and framing), verdicts recorded on
 * the receipt; (3) the SIGN-OFF AFFORDANCE (native) releases it — a SEPARATE
 * act, informed by the two passes."
 *
 * MP §3.5.C is the authority above it, and it names the two controls as
 * distinct: "double red-team AND explicit native sign-off". The architecture
 * repeats the emphasis: "two distinct controls, never collapsed". This module
 * is where "never collapsed" is made structural — `signOff` REFUSES on a
 * review that has not reached `adversarial_passes_complete`, and there is no
 * argument, flag, or role that lets a caller skip it.
 *
 * ── WHAT "INDEPENDENT" IS CHECKED TO MEAN ────────────────────────────────────
 * Two passes from the same model in the same context are one pass recorded
 * twice. `recordAdversarialPass` rejects a second pass whose
 * (reviewer_model_id, reviewer_context_id) pair equals the first's. That is a
 * REAL detector behind the word "independent" (§N.8) — a weak one (it cannot
 * detect two nominally different models that are the same weights behind
 * different names) and it says so rather than claiming more.
 *
 * ── NCD-4 ────────────────────────────────────────────────────────────────────
 * `interstitial_shown` is a distinct terminal state, reachable ONLY from
 * `openReview` and ONLY for a proven-`native_self` subject on an HS-3 class.
 * NCD-10 scopes the relaxation precisely — "native-self interstitial for
 * health-crisis/mental-health readings; cohort subjects unaffected — full
 * seal" — so HS-4 mortality windows do NOT get the interstitial even for the
 * native. `interstitialApplies` encodes exactly that scope and nothing wider.
 */

import type {
  AdversarialPass,
  AdversarialVerdict,
  SafetyClass,
  SafetyReviewRecord,
  SafetyReviewState,
} from './types'

/** Legal transitions. Anything not listed here is refused by `assertTransition`. */
const TRANSITIONS: Record<SafetyReviewState, SafetyReviewState[]> = {
  seal_pending: ['adversarial_pass_1_recorded', 'withheld'],
  adversarial_pass_1_recorded: ['adversarial_passes_complete', 'withheld'],
  adversarial_passes_complete: ['released', 'withheld'],
  released: [],
  withheld: [],
  interstitial_shown: [],
}

export class SafetyReviewTransitionError extends Error {
  readonly code = 'SAFETY_REVIEW_ILLEGAL_TRANSITION'
  constructor(from: SafetyReviewState, to: SafetyReviewState, why: string) {
    super(`SAFETY_REVIEW_ILLEGAL_TRANSITION: ${from} -> ${to}: ${why}`)
    this.name = 'SafetyReviewTransitionError'
  }
}

export function isLegalTransition(from: SafetyReviewState, to: SafetyReviewState): boolean {
  return (TRANSITIONS[from] ?? []).includes(to)
}

/**
 * NCD-4 / NCD-10 scope, exactly.
 *
 * TRUE only when: the subject is a PROVEN `native_self` (a null subject_kind is
 * not proof — the consent lane returns null when its own enforcement is off,
 * and "we didn't check" must not buy the relaxation), AND every detected class
 * is an HS-3 class. One HS-4 mortality class anywhere in the set takes the
 * whole turn back to the full seal path.
 */
export function interstitialApplies(args: {
  subjectKind: 'native_self' | 'cohort' | 'test' | null
  classes: readonly SafetyClass[]
}): boolean {
  if (args.subjectKind !== 'native_self') return false
  const hs3 = args.classes.filter((c) => c === 'hs3_health_crisis' || c === 'hs3_mental_health')
  if (hs3.length === 0) return false
  return args.classes.every((c) => c === 'hs3_health_crisis' || c === 'hs3_mental_health')
}

export interface OpenReviewArgs {
  reviewId: string
  chartId: string
  turnId: string
  classes: SafetyClass[]
  subjectKind: 'native_self' | 'cohort' | 'test' | null
  /** True to take the NCD-4 branch. The caller must have used `interstitialApplies`. */
  interstitial: boolean
  now?: Date
}

export function openReview(args: OpenReviewArgs): SafetyReviewRecord {
  const now = (args.now ?? new Date()).toISOString()
  if (args.interstitial && !interstitialApplies({ subjectKind: args.subjectKind, classes: args.classes })) {
    // Refuse to open an interstitial review outside NCD-10's scope. A caller
    // that gets this wrong gets an exception, not a quietly-widened relaxation.
    throw new SafetyReviewTransitionError(
      'seal_pending',
      'interstitial_shown',
      'NCD-4/NCD-10 scope: interstitial requires a proven native_self subject and HS-3-only classes',
    )
  }
  return {
    review_id: args.reviewId,
    chart_id: args.chartId,
    turn_id: args.turnId,
    state: args.interstitial ? 'interstitial_shown' : 'seal_pending',
    classes: [...args.classes],
    subject_kind: args.subjectKind,
    passes: [],
    signed_off_by: null,
    signed_off_at: null,
    withheld_reason: null,
    opened_at: now,
  }
}

export interface RecordPassArgs {
  reviewerModelId: string
  reviewerContextId: string
  verdict: AdversarialVerdict
  findings: string[]
  now?: Date
}

/**
 * Record one adversarial pass. Pure — returns the next record; persistence is
 * the caller's job (`db.ts`), so the machine is testable with no database.
 */
export function recordAdversarialPass(
  review: SafetyReviewRecord,
  args: RecordPassArgs,
): SafetyReviewRecord {
  if (review.state !== 'seal_pending' && review.state !== 'adversarial_pass_1_recorded') {
    throw new SafetyReviewTransitionError(
      review.state,
      'adversarial_pass_1_recorded',
      'adversarial passes may only be recorded on a sealed review',
    )
  }
  const ordinal: 1 | 2 = review.passes.length === 0 ? 1 : 2
  if (review.passes.length >= 2) {
    throw new SafetyReviewTransitionError(
      review.state,
      'adversarial_passes_complete',
      'both adversarial passes are already recorded',
    )
  }
  const first = review.passes[0]
  if (
    first &&
    first.reviewer_model_id === args.reviewerModelId &&
    first.reviewer_context_id === args.reviewerContextId
  ) {
    // The detector behind the word "independent". Weak but real: it cannot see
    // through two aliases of one model, and this lane does not claim it can.
    throw new SafetyReviewTransitionError(
      review.state,
      'adversarial_passes_complete',
      'the second pass must be INDEPENDENT: distinct (reviewer_model_id, reviewer_context_id) from the first',
    )
  }
  const pass: AdversarialPass = {
    pass_ordinal: ordinal,
    reviewer_model_id: args.reviewerModelId,
    reviewer_context_id: args.reviewerContextId,
    verdict: args.verdict,
    findings: [...args.findings],
    recorded_at: (args.now ?? new Date()).toISOString(),
  }
  const passes = [...review.passes, pass]
  const nextState: SafetyReviewState =
    passes.length === 2 ? 'adversarial_passes_complete' : 'adversarial_pass_1_recorded'
  assertTransition(review.state, nextState)
  return { ...review, passes, state: nextState }
}

export interface SignOffArgs {
  signedOffBy: string
  now?: Date
}

/**
 * The SEPARATE act (step 3). Refuses unless BOTH passes are in.
 *
 * Also refuses when either pass returned `refuted`: a sign-off that can release
 * a reading two adversarial passes said was wrong would make the passes
 * decorative. Releasing over a `refuted` verdict is possible only by recording
 * a withhold and opening a NEW review — i.e. by re-doing the work, which is the
 * point.
 */
export function signOff(review: SafetyReviewRecord, args: SignOffArgs): SafetyReviewRecord {
  if (review.state !== 'adversarial_passes_complete') {
    throw new SafetyReviewTransitionError(
      review.state,
      'released',
      'sign-off is a SEPARATE control and cannot substitute for the two adversarial passes (MP §3.5.C: "double red-team AND explicit native sign-off")',
    )
  }
  if (review.passes.some((p) => p.verdict === 'refuted')) {
    throw new SafetyReviewTransitionError(
      review.state,
      'released',
      'an adversarial pass returned `refuted`; a refuted reading is withheld, not signed off',
    )
  }
  if (!args.signedOffBy) {
    throw new SafetyReviewTransitionError(review.state, 'released', 'sign-off requires an identified signer')
  }
  assertTransition(review.state, 'released')
  const now = (args.now ?? new Date()).toISOString()
  return { ...review, state: 'released', signed_off_by: args.signedOffBy, signed_off_at: now }
}

export function withhold(review: SafetyReviewRecord, reason: string): SafetyReviewRecord {
  assertTransition(review.state, 'withheld')
  return { ...review, state: 'withheld', withheld_reason: reason }
}

/** A released review is the ONLY state on which sealed content may be served. */
export function isReleasable(review: SafetyReviewRecord): boolean {
  return review.state === 'released' || review.state === 'interstitial_shown'
}

function assertTransition(from: SafetyReviewState, to: SafetyReviewState): void {
  if (!isLegalTransition(from, to)) {
    throw new SafetyReviewTransitionError(from, to, 'not a legal transition')
  }
}

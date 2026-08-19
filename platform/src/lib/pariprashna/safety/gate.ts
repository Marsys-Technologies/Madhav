/**
 * Paripraśna — THE SafetyPolicyGate (lane G1-A, PPR-12).
 *
 * The port the architecture's §3 chain names between entitlement and planning:
 *
 *   NormalizedQuery → EntitlementDecision → **SafetyPolicyDecision**
 *     → ScopeTuple → plan …
 *
 * and the one `pipeline/safety_gate.ts` declared as "PORT NOT YET IMPLEMENTED"
 * with the insertion point named. This is the implementation; that file's
 * `classifyTurnSafety` call is the wiring.
 *
 * ── ORDERING, AND WHY IT IS THIS ORDERING ────────────────────────────────────
 * The gate runs AFTER consent resolution and BEFORE the plan stage.
 *   · after consent — a subject must be consented before their question is even
 *     classified, and the gate NEEDS `subject_kind` for the NCD-4 branch;
 *   · before planning — PPR-12 and §3 both: "a blocked class must never build a
 *     retrieval plan". The HS-2 path in particular short-circuits with nothing
 *     retrieved, so there is nothing to leak.
 *
 * ── THE DECISION IS WRITTEN ON EVERY TURN ────────────────────────────────────
 * Including turns where nothing fired. A safety table containing only the turns
 * that fired cannot answer "out of how many?", and every rate this domain cares
 * about needs that denominator. G3-A (receipt emission) reads this object as
 * the receipt's `safety_decision` field.
 *
 * ── FLAG-OFF IS A ZERO-COST NO-OP ────────────────────────────────────────────
 * With `PARIPRASHNA_SAFETY_GATE_ENABLED` OFF (the default), `classifyTurnSafety`
 * returns a decision with `enforced: false` and action `proceed` BEFORE running
 * a single pattern and before touching the database. `enforced: false` means
 * "no safety question was asked on this turn" — it is NOT "asked and found
 * nothing", and the field exists precisely so a receipt can tell those apart
 * (§N.8).
 */

import { randomUUID } from 'node:crypto'

import { classifyQuery, reclassifyWithPlan, type ClassificationResult } from './classifier'
import { isSafetyGateEnabled } from './flag'
import { llmAssistRan } from './llm_assist'
import { notificationRequired, recordCohortNativeNotification } from './notification'
import { interstitialApplies, openReview } from './review_machine'
import { persistNewReview } from './review_db'
import { appendSafetyDecision } from './audit'
import { capabilitiesExcludedFor } from './sensitive_capabilities'
import {
  SAFETY_CLASSES,
  maxSeverity,
  type SafetyAction,
  type SafetyClass,
  type SafetyDb,
  type SafetyDecision,
  type SafetySeverity,
} from './types'

export type SubjectKind = 'native_self' | 'cohort' | 'test' | null

/**
 * Map a detected class set to the action.
 *
 * Precedence is by consequence severity, not by class number:
 *   HS-2  → hard_stop            (no plan, fixed response)
 *   HS-4  → seal_pending_signoff (ALWAYS — NCD-10 scopes the relaxation to
 *                                 health-crisis/mental-health only, so a
 *                                 mortality window does not get the
 *                                 interstitial even for the native)
 *   HS-3  → interstitial when NCD-4 applies, else seal_pending_signoff
 *   HS-1  → reframe (it always co-occurs with HS-4 via the classifier's
 *                    implication rule, so in practice HS-1 lands on the seal
 *                    path; `reframe` is its floor, not its ceiling)
 *   none  → proceed
 */
export function resolveAction(args: {
  classes: readonly SafetyClass[]
  subjectKind: SubjectKind
}): { action: SafetyAction; ncd4: boolean } {
  const { classes, subjectKind } = args
  if (classes.includes('hs2_suicide_adjacent')) return { action: 'hard_stop', ncd4: false }

  const ncd4 = interstitialApplies({ subjectKind, classes })
  if (classes.includes('hs4_mortality_window')) {
    return { action: 'seal_pending_signoff', ncd4: false }
  }
  if (classes.includes('hs3_health_crisis') || classes.includes('hs3_mental_health')) {
    return ncd4 ? { action: 'interstitial', ncd4: true } : { action: 'seal_pending_signoff', ncd4: false }
  }
  if (classes.includes('hs1_date_of_death')) return { action: 'reframe', ncd4: false }
  return { action: 'proceed', ncd4: false }
}

export interface ClassifyTurnSafetyArgs {
  turnId: string
  chartId: string
  queryText: string
  /** From the consent lane's decision. `null` when consent enforcement is OFF. */
  subjectKind: SubjectKind
  /** Injectable for tests. Omitted → the production pool. */
  db?: SafetyDb
  now?: Date
  /** Injectable id source so tests get deterministic ids. */
  newId?: () => string
}

/**
 * Classify one turn and record the decision.
 *
 * Never throws. A gate that can throw is a gate that can take a turn down, and
 * a fault in the AUDIT path must not become a fault in the SAFETY path — so a
 * failed write is reported as `audit_written: false` and the decision stands.
 * A fault in CLASSIFICATION is different and is handled differently: it fails
 * closed to `seal_pending_signoff`, because a classifier that could not decide
 * has not decided the query is safe.
 */
export async function classifyTurnSafety(args: ClassifyTurnSafetyArgs): Promise<SafetyDecision> {
  const now = args.now ?? new Date()
  const newId = args.newId ?? (() => randomUUID())
  const base = {
    decision_id: newId(),
    turn_id: args.turnId,
    chart_id: args.chartId,
    subject_kind: args.subjectKind,
    llm_assist_ran: llmAssistRan(),
    decided_at: now.toISOString(),
  }

  // ── The flag gate. Nothing below runs in production today. ────────────────
  if (!isSafetyGateEnabled()) {
    return {
      ...base,
      enforced: false,
      classes_detected: [],
      severity: 'none',
      action: 'proceed',
      ncd4_interstitial_applies: false,
      detections: [],
      evasion_markers: [],
      excluded_capabilities: [],
      review_id: null,
      audit_written: false,
    }
  }

  let classification: ClassificationResult
  try {
    classification = classifyQuery({ queryText: args.queryText })
  } catch (err) {
    // FAIL CLOSED. A classifier that crashed did not clear the query.
    console.error('[pariprashna/safety] classifier fault — failing closed:', err)
    const decision: SafetyDecision = {
      ...base,
      enforced: true,
      classes_detected: [],
      severity: 'review_required',
      action: 'seal_pending_signoff',
      ncd4_interstitial_applies: false,
      detections: [
        {
          cls: 'hs4_mortality_window',
          severity: 'review_required',
          detector: 'gate',
          rule: 'classifier_fault_fail_closed',
          matched_span_hash: '',
          surface: 'query',
        },
      ],
      evasion_markers: [],
      excluded_capabilities: capabilitiesExcludedFor(['hs4_mortality_window']),
      review_id: null,
      audit_written: false,
    }
    return finalize(decision, args, now, newId)
  }

  const { action, ncd4 } = resolveAction({
    classes: classification.classes,
    subjectKind: args.subjectKind,
  })

  const decision: SafetyDecision = {
    ...base,
    enforced: true,
    classes_detected: [...classification.classes],
    severity: classification.severity,
    action,
    ncd4_interstitial_applies: ncd4,
    detections: classification.detections,
    evasion_markers: classification.evasion_markers,
    excluded_capabilities: capabilitiesExcludedFor(classification.classes),
    review_id: null,
    audit_written: false,
  }

  return finalize(decision, args, now, newId)
}

/**
 * Does this action REQUIRE a review record to exist?
 *
 * One predicate, named once, used by both the pre-plan and the post-plan path
 * and mirrored by the DB CHECK constraint
 * `pariprashna_safety_decisions_seal_requires_review_chk` (migration 577).
 * Keeping it in one place is the point: the hardening round found that the two
 * paths had DIFFERENT answers to this question, and only one of them was right.
 */
export function actionRequiresReview(action: SafetyAction): boolean {
  return action === 'seal_pending_signoff' || action === 'interstitial'
}

/**
 * Open the review record an action requires, and put its id on the decision.
 *
 * ── WHY THIS IS ITS OWN FUNCTION (hardening round, C-6) ──────────────────────
 * It used to be inline in `finalize`, which meant `reclassifyAfterPlan` — the
 * OTHER path that can land on `seal_pending_signoff` — did not run it. A turn
 * that classified clean before planning and escalated after it therefore
 * produced: no review row, `review_id: null` on the decision, and a reader
 * shown the acknowledgment that says "the review has been opened. Nothing has
 * been discarded" — a false statement about a sealed reading that nothing was
 * tracking. There is no FK on `review_id`, so nothing could detect it either.
 *
 * Both paths now call this, and the DB CHECK added alongside it makes the class
 * of bug unrepresentable rather than merely fixed.
 */
async function openReviewForDecision(
  decision: SafetyDecision,
  db: SafetyDb,
  now: Date,
  newId: () => string,
): Promise<SafetyDecision> {
  if (!actionRequiresReview(decision.action)) return decision
  // Already carries one (e.g. a post-plan escalation on a turn that had
  // already sealed pre-plan) — never open a second review for one turn.
  if (decision.review_id) return decision

  const reviewId = newId()
  const open = (interstitial: boolean): ReturnType<typeof openReview> =>
    openReview({
      reviewId,
      chartId: decision.chart_id,
      turnId: decision.turn_id,
      classes: decision.classes_detected,
      subjectKind: decision.subject_kind,
      interstitial,
      now,
    })

  let out = decision
  let review: ReturnType<typeof openReview>
  try {
    review = open(decision.action === 'interstitial')
  } catch (err) {
    // `openReview` refuses an out-of-scope interstitial (NCD-4/NCD-10). Fall
    // back to the SEAL path — the fail-closed direction, never to `proceed`.
    //
    // Note what changed here in the hardening round: the fallback used to also
    // set `review_id: null`, which left a `seal_pending_signoff` decision with
    // no review at all — the same defect C-6 is about, reached by a different
    // route. It now RE-OPENS as a non-interstitial review, so the seal it fell
    // back to is a seal something is actually tracking.
    console.error('[pariprashna/safety] interstitial refused — re-opening as a seal review:', err)
    out = { ...out, action: 'seal_pending_signoff', ncd4_interstitial_applies: false }
    review = open(false)
  }

  const persisted = await persistNewReview(db, review)
  // The review id goes on the decision whether or not the row landed: the id is
  // what the acknowledgment quotes back, and a decision claiming
  // `review_id: null` while the reader was told a review was opened would be
  // the worse inconsistency. Persistence failure surfaces via `audit_written`
  // and the server log.
  if (!persisted) {
    console.error('[pariprashna/safety] review row did not persist for turn', out.turn_id)
  }
  return { ...out, review_id: reviewId }
}

/** Open the review (when the action needs one), write the audit row, notify. */
async function finalize(
  decision: SafetyDecision,
  args: ClassifyTurnSafetyArgs,
  now: Date,
  newId: () => string,
): Promise<SafetyDecision> {
  const db = args.db ?? (await import('./db')).defaultSafetyDb()
  return recordDecision(await openReviewForDecision(decision, db, now, newId), db, now, newId)
}

/**
 * Append the audit row and record any notification obligation.
 *
 * Shared by the pre-plan and post-plan paths so the two cannot diverge on what
 * a decision's persistence consists of — which is exactly how C-6 happened.
 */
async function recordDecision(
  decision: SafetyDecision,
  db: SafetyDb,
  now: Date,
  newId: () => string,
): Promise<SafetyDecision> {
  const written = await appendSafetyDecision(db, decision)
  const out = { ...decision, audit_written: written }

  const notify = notificationRequired({ subjectKind: out.subject_kind, classes: out.classes_detected })
  if (notify.required) {
    // Idempotent per turn: the obligation table is `UNIQUE (turn_id)` with
    // `ON CONFLICT DO NOTHING`, so a post-plan escalation that re-reaches this
    // line does not double-record an obligation the pre-plan pass already took.
    await recordCohortNativeNotification(db, {
      notificationId: newId(),
      chartId: out.chart_id,
      turnId: out.turn_id,
      decisionId: out.decision_id,
      reason: notify.reason,
      now,
    })
  }

  return out
}

/**
 * The post-plan re-classification (PPR-12's plan-time enforcement point).
 *
 * Called by the plan stage with the produced plan's domains and authorized
 * capabilities. Returns an UPDATED decision whose class set and severity are
 * >= the pre-plan decision's — never smaller. A plan that reveals a health
 * domain the question's wording hid escalates the turn; a plan that reveals
 * nothing leaves the decision exactly as it was.
 *
 * This does NOT re-write the audit row. The pre-plan decision is a fact about
 * what the gate knew before planning; a second row (`seq+1`) records what it
 * knew after. Editing the first would make the chain a story rather than a log.
 */
export async function reclassifyAfterPlan(args: {
  decision: SafetyDecision
  queryText: string
  domains: readonly string[]
  capabilities: readonly string[]
  db?: SafetyDb
  now?: Date
  newId?: () => string
}): Promise<SafetyDecision> {
  if (!args.decision.enforced) return args.decision
  const now = args.now ?? new Date()
  const newId = args.newId ?? (() => randomUUID())

  const prior: ClassificationResult = {
    detections: args.decision.detections,
    evasion_markers: args.decision.evasion_markers,
    classes: args.decision.classes_detected,
    severity: args.decision.severity,
    // The pre-plan pass's normalized text is not persisted on the decision (it
    // is C1), so the post-plan pass re-derives from `queryText` where it needs
    // to. This placeholder is never read: `reclassifyWithPlan` returns the
    // PRIOR result's `normalized` field untouched, and the caller ignores it.
    normalized: { normalized: '', squashed: '', normalizedAll: [], squashedAll: [], literal: '' },
  }
  const rawMerged = reclassifyWithPlan(prior, {
    queryText: args.queryText,
    domains: args.domains,
    capabilities: args.capabilities,
  })

  // ── THE MONOTONICITY FLOOR, ENFORCED AT RUNTIME (hardening round, C-4) ─────
  //
  // `reclassifyWithPlan`'s union and `strongerAction` below are two INDEPENDENT
  // guards against de-escalation, and the hardening round's mutation testing
  // found that either could be deleted alone with the whole suite still green:
  // removing the classifier's carry-forward left `action` correct (because
  // `strongerAction` covered it) while silently dropping `hs2_suicide_adjacent`
  // from `classes_detected` and demoting `severity` from `hard_stop` to
  // `review_required` — in the HASH-CHAINED audit row, undetectably.
  //
  // Tests that kill each guard independently now exist. This is the second
  // half of that fix and the more important one: a guard whose only enforcement
  // is a test can be regressed by anyone who changes the test. `mergeFloor`
  // re-imposes the floor HERE, on the value that is about to be persisted, so
  // the audit row cannot record a de-escalation regardless of what any upstream
  // merge did. It is the §N.8 move — a real detector, on the actual claim,
  // rather than a convention two other places happen to honor.
  const merged = mergeFloor(prior, rawMerged)

  const sameClasses =
    merged.classes.length === args.decision.classes_detected.length &&
    merged.classes.every((c) => args.decision.classes_detected.includes(c))
  if (sameClasses && merged.severity === args.decision.severity) return args.decision

  const { action, ncd4 } = resolveAction({
    classes: merged.classes,
    subjectKind: args.decision.subject_kind,
  })
  const escalated: SafetyDecision = {
    ...args.decision,
    decision_id: newId(),
    classes_detected: [...merged.classes],
    severity: merged.severity,
    // Never de-escalate: take the stronger of the two actions.
    action: strongerAction(args.decision.action, action),
    ncd4_interstitial_applies: ncd4 && args.decision.action !== 'seal_pending_signoff',
    detections: merged.detections,
    excluded_capabilities: capabilitiesExcludedFor(merged.classes),
    decided_at: now.toISOString(),
    audit_written: false,
  }
  const db = args.db ?? (await import('./db')).defaultSafetyDb()
  // C-6: a post-plan escalation into the seal/interstitial path opens its
  // review here, exactly as the pre-plan path does. This call is what makes the
  // acknowledgment ("the review has been opened") true on this path, and what
  // lets the DB CHECK requiring `review_id` on a sealed decision hold.
  return recordDecision(await openReviewForDecision(escalated, db, now, newId), db, now, newId)
}

/**
 * Re-impose the prior classification as a FLOOR on a merged one.
 *
 * Pure, total, and idempotent. Returns a result whose class set is a superset
 * of `prior`'s and whose severity is `>=` prior's — carrying forward, verbatim,
 * any detection the merge dropped. If the merge was already monotone (the
 * normal case, and what `reclassifyWithPlan` is written to do) this returns it
 * untouched, so the guard is invisible until something upstream breaks.
 *
 * A dropped detection is logged: silently repairing a de-escalation would make
 * this the same kind of unearned green signal it exists to prevent.
 */
export function mergeFloor(
  prior: ClassificationResult,
  merged: ClassificationResult,
): ClassificationResult {
  const missing = prior.detections.filter(
    (p) => !merged.detections.some((m) => m.rule === p.rule && m.cls === p.cls && m.detector === p.detector),
  )
  const severityFloored = maxSeverity(merged.severity, prior.severity)
  if (missing.length === 0 && severityFloored === merged.severity) return merged

  console.error(
    '[pariprashna/safety] MONOTONICITY VIOLATION in the post-plan merge — ' +
      `${missing.length} detection(s) dropped, severity ${merged.severity} < ${prior.severity}. ` +
      'Carrying the prior classification forward; this is a bug in reclassifyWithPlan.',
  )
  const detections = [...merged.detections, ...missing]
  return {
    detections,
    evasion_markers: merged.evasion_markers.length ? merged.evasion_markers : prior.evasion_markers,
    classes: SAFETY_CLASSES.filter((c) => detections.some((d) => d.cls === c)),
    severity: detections.reduce<SafetySeverity>((acc, d) => maxSeverity(acc, d.severity), severityFloored),
    normalized: merged.normalized,
  }
}

function strongerAction(a: SafetyAction, b: SafetyAction): SafetyAction {
  const rank: Record<SafetyAction, number> = {
    proceed: 0,
    reframe: 1,
    interstitial: 2,
    seal_pending_signoff: 3,
    hard_stop: 4,
  }
  return rank[a] >= rank[b] ? a : b
}

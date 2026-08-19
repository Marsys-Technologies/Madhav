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
import type { SafetyAction, SafetyClass, SafetyDb, SafetyDecision } from './types'

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

/** Open the review (when the action needs one), write the audit row, notify. */
async function finalize(
  decision: SafetyDecision,
  args: ClassifyTurnSafetyArgs,
  now: Date,
  newId: () => string,
): Promise<SafetyDecision> {
  const db = args.db ?? (await import('./db')).defaultSafetyDb()
  let out = decision

  if (out.action === 'seal_pending_signoff' || out.action === 'interstitial') {
    const reviewId = newId()
    try {
      const review = openReview({
        reviewId,
        chartId: out.chart_id,
        turnId: out.turn_id,
        classes: out.classes_detected,
        subjectKind: out.subject_kind,
        interstitial: out.action === 'interstitial',
        now,
      })
      const persisted = await persistNewReview(db, review)
      // The review id goes on the decision whether or not the row landed: the
      // id is what the acknowledgment quotes back, and a decision claiming
      // `review_id: null` while the reader was told a review was opened would
      // be the worse inconsistency. Persistence failure surfaces via
      // `audit_written` and the server log.
      out = { ...out, review_id: reviewId }
      if (!persisted) {
        console.error('[pariprashna/safety] review row did not persist for turn', out.turn_id)
      }
    } catch (err) {
      // openReview refuses an out-of-scope interstitial. Falling back to the
      // SEAL path is the fail-closed direction — never to `proceed`.
      console.error('[pariprashna/safety] review open refused — falling back to seal:', err)
      out = { ...out, action: 'seal_pending_signoff', ncd4_interstitial_applies: false, review_id: null }
    }
  }

  const written = await appendSafetyDecision(db, out)
  out = { ...out, audit_written: written }

  const notify = notificationRequired({ subjectKind: out.subject_kind, classes: out.classes_detected })
  if (notify.required) {
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
    normalized: { normalized: '', squashed: '', literal: '' },
  }
  const merged = reclassifyWithPlan(prior, {
    queryText: args.queryText,
    domains: args.domains,
    capabilities: args.capabilities,
  })

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
  const written = await appendSafetyDecision(db, escalated)
  return { ...escalated, audit_written: written }
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

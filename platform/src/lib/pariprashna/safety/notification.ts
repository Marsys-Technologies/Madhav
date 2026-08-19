/**
 * Paripraśna safety — HS-2 COHORT-NATIVE NOTIFICATION (lane G1-A).
 *
 * SAFETY_PRIVACY_TENANCY §2 HS-2, the clause after the fixed response: "audit
 * row; NATIVE NOTIFIED FOR COHORT SUBJECTS — and that notification pathway is
 * itself disclosed in the §3.5.D consent document (a subject's crisis query
 * reaching the researcher is a disclosure the subject must have accepted in
 * advance)."
 *
 * ── THE SCOPE RULE, WHICH IS NARROWER THAN "NOTIFY ON HS-2" ──────────────────
 * The obligation is for COHORT subjects. It is not for `native_self`: the
 * native asking the instrument a crisis question and the instrument then
 * "notifying the native" is a loop, not a safeguard. `notificationRequired`
 * encodes exactly that, and returns `false` with a stated reason rather than a
 * bare boolean, so a caller logging the decision logs WHY.
 *
 * A null `subject_kind` (consent enforcement OFF, so nobody checked) does NOT
 * buy the native_self exemption — it FAILS TOWARD notification, since an
 * unrecorded obligation is worse than a redundant one.
 *
 * ── WHAT IS BUILT, AND THE HONEST HOLE ───────────────────────────────────────
 * BUILT: the obligation row, its append-only table, and the query a delivery
 * job would drain.
 * NOT BUILT: delivery. This codebase has NO notification transport — no email
 * sender, no push channel, no operator inbox that a library call can reach.
 * Inventing one inside a safety lane would be the wrong place for it, and
 * writing `delivered: true` against a transport that does not exist is the §N.8
 * defect this project has a named principle about. So the row is written in
 * state `pending`, `pendingNotifications()` is the drain, and the gap is
 * REPORTED rather than papered over: today an HS-2 event on a cohort chart
 * leaves a durable, queryable obligation that nothing yet delivers.
 */

import type { SafetyDb } from './types'
import { isSafetyGateEnabled } from './flag'

export type NotificationState = 'pending' | 'delivered' | 'failed'

export interface NotificationRequirement {
  required: boolean
  reason:
    | 'cohort_subject_crisis_query'
    | 'subject_kind_unknown_fails_toward_notification'
    | 'native_self_no_third_party_to_notify'
    | 'test_subject'
    | 'no_hs2_class'
}

export function notificationRequired(args: {
  subjectKind: 'native_self' | 'cohort' | 'test' | null
  classes: readonly string[]
}): NotificationRequirement {
  if (!args.classes.includes('hs2_suicide_adjacent')) {
    return { required: false, reason: 'no_hs2_class' }
  }
  if (args.subjectKind === 'cohort') {
    return { required: true, reason: 'cohort_subject_crisis_query' }
  }
  if (args.subjectKind === 'native_self') {
    return { required: false, reason: 'native_self_no_third_party_to_notify' }
  }
  if (args.subjectKind === 'test') {
    return { required: false, reason: 'test_subject' }
  }
  return { required: true, reason: 'subject_kind_unknown_fails_toward_notification' }
}

export interface RecordNotificationArgs {
  notificationId: string
  chartId: string
  turnId: string
  decisionId: string
  reason: NotificationRequirement['reason']
  now?: Date
}

/**
 * Record the obligation. Returns whether the row landed — never assumed.
 *
 * Note what the row does NOT carry: the question. §5's safe-logging rule holds
 * here more than anywhere. A researcher reading this table learns that a
 * crisis-class query occurred on a chart at a time, and must go through the
 * consented access path for anything more.
 */
export async function recordCohortNativeNotification(
  db: SafetyDb,
  args: RecordNotificationArgs,
): Promise<boolean> {
  if (!isSafetyGateEnabled()) return false
  try {
    await db.query(
      `INSERT INTO pariprashna_safety_notifications (
         notification_id, chart_id, turn_id, decision_id, reason, state, recorded_at
       ) VALUES ($1,$2,$3,$4,$5,'pending',$6)
       ON CONFLICT (turn_id) DO NOTHING`,
      [
        args.notificationId,
        args.chartId,
        args.turnId,
        args.decisionId,
        args.reason,
        (args.now ?? new Date()).toISOString(),
      ],
    )
    return true
  } catch (err) {
    console.error('[pariprashna/safety] cohort-native notification write failed:', err)
    return false
  }
}

export interface NotificationRow {
  notification_id: string
  chart_id: string
  turn_id: string
  decision_id: string
  reason: string
  state: NotificationState
  recorded_at: string
  delivered_at: string | null
}

/** The drain a delivery job would read. There is no such job yet — see header. */
export async function pendingNotifications(db: SafetyDb, limit = 100): Promise<NotificationRow[]> {
  const { rows } = await db.query<NotificationRow>(
    `SELECT notification_id, chart_id, turn_id, decision_id, reason, state,
            recorded_at::text AS recorded_at, delivered_at::text AS delivered_at
       FROM pariprashna_safety_notifications
      WHERE state = 'pending' ORDER BY recorded_at ASC LIMIT $1`,
    [limit],
  )
  return rows
}

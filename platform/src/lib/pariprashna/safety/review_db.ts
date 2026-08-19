/**
 * Paripraśna safety — persistence for the HS-3/HS-4 review records.
 *
 * `review_machine.ts` is the pure state machine; this is the only file that
 * knows it lives in a table. Keeping the split means every transition rule is
 * unit-tested with no database, and the DB layer's job is reduced to "write
 * what the machine returned" — it cannot invent a transition of its own,
 * because it never computes one.
 *
 * `pariprashna_safety_reviews` is append-only on its EVENT table and mutable
 * on its current-state row, the same pattern G1-B used for
 * `chart_subject_consent` + `chart_subject_consent_events`: the current state
 * is convenient, the history is the record.
 */

import type { SafetyDb, SafetyQueryable, SafetyReviewRecord, SafetyReviewState } from './types'

export async function persistNewReview(db: SafetyDb, review: SafetyReviewRecord): Promise<boolean> {
  try {
    await db.withTransaction(async (tx: SafetyQueryable) => {
      await tx.query(
        `INSERT INTO pariprashna_safety_reviews (
           review_id, chart_id, turn_id, state, classes, subject_kind, opened_at
         ) VALUES ($1,$2,$3,$4,$5,$6,$7)
         ON CONFLICT (review_id) DO NOTHING`,
        [
          review.review_id,
          review.chart_id,
          review.turn_id,
          review.state,
          review.classes,
          review.subject_kind,
          review.opened_at,
        ],
      )
      await appendReviewEvent(tx, review.review_id, null, review.state, 'opened', {
        classes: review.classes,
        subject_kind: review.subject_kind,
      })
    })
    return true
  } catch (err) {
    console.error('[pariprashna/safety] review persist failed:', err)
    return false
  }
}

export async function persistReviewTransition(
  db: SafetyDb,
  before: SafetyReviewRecord,
  after: SafetyReviewRecord,
  actor: string,
): Promise<void> {
  await db.withTransaction(async (tx: SafetyQueryable) => {
    // Compare-and-set on the PREVIOUS state: two concurrent sign-offs cannot
    // both land, and a transition computed against stale state fails loudly
    // rather than overwriting whatever is there now.
    const { rows } = await tx.query<{ review_id: string }>(
      `UPDATE pariprashna_safety_reviews
          SET state = $3, signed_off_by = $4, signed_off_at = $5, withheld_reason = $6
        WHERE review_id = $1 AND state = $2
        RETURNING review_id`,
      [
        after.review_id,
        before.state,
        after.state,
        after.signed_off_by,
        after.signed_off_at,
        after.withheld_reason,
      ],
    )
    if (rows.length !== 1) {
      throw new Error(
        `SAFETY_REVIEW_STALE_TRANSITION: review ${after.review_id} was not in state ` +
          `"${before.state}" when the transition to "${after.state}" was applied`,
      )
    }
    const newPass = after.passes[after.passes.length - 1]
    if (after.passes.length > before.passes.length && newPass) {
      await tx.query(
        `INSERT INTO pariprashna_safety_review_passes (
           review_id, pass_ordinal, reviewer_model_id, reviewer_context_id, verdict,
           findings, recorded_at
         ) VALUES ($1,$2,$3,$4,$5,$6,$7)`,
        [
          after.review_id,
          newPass.pass_ordinal,
          newPass.reviewer_model_id,
          newPass.reviewer_context_id,
          newPass.verdict,
          newPass.findings,
          newPass.recorded_at,
        ],
      )
    }
    await appendReviewEvent(tx, after.review_id, before.state, after.state, actor, {
      passes: after.passes.length,
      signed_off_by: after.signed_off_by,
      withheld_reason: after.withheld_reason,
    })
  })
}

async function appendReviewEvent(
  tx: SafetyQueryable,
  reviewId: string,
  fromState: SafetyReviewState | null,
  toState: SafetyReviewState,
  actor: string,
  payload: Record<string, unknown>,
): Promise<void> {
  await tx.query(
    `INSERT INTO pariprashna_safety_review_events (review_id, from_state, to_state, actor, payload)
     VALUES ($1,$2,$3,$4,$5::jsonb)`,
    [reviewId, fromState, toState, actor, JSON.stringify(payload)],
  )
}

export async function loadReview(db: SafetyDb, reviewId: string): Promise<SafetyReviewRecord | null> {
  const { rows } = await db.query<{
    review_id: string
    chart_id: string
    turn_id: string
    state: SafetyReviewState
    classes: string[]
    subject_kind: 'native_self' | 'cohort' | 'test' | null
    signed_off_by: string | null
    signed_off_at: string | null
    withheld_reason: string | null
    opened_at: string
  }>(
    `SELECT review_id, chart_id, turn_id, state, classes, subject_kind, signed_off_by,
            signed_off_at::text AS signed_off_at, withheld_reason, opened_at::text AS opened_at
       FROM pariprashna_safety_reviews WHERE review_id = $1`,
    [reviewId],
  )
  const r = rows[0]
  if (!r) return null
  const { rows: passRows } = await db.query<{
    pass_ordinal: number
    reviewer_model_id: string
    reviewer_context_id: string
    verdict: string
    findings: string[]
    recorded_at: string
  }>(
    `SELECT pass_ordinal, reviewer_model_id, reviewer_context_id, verdict, findings,
            recorded_at::text AS recorded_at
       FROM pariprashna_safety_review_passes WHERE review_id = $1 ORDER BY pass_ordinal ASC`,
    [reviewId],
  )
  return {
    review_id: r.review_id,
    chart_id: r.chart_id,
    turn_id: r.turn_id,
    state: r.state,
    classes: r.classes as SafetyReviewRecord['classes'],
    subject_kind: r.subject_kind,
    passes: passRows.map((p) => ({
      pass_ordinal: p.pass_ordinal as 1 | 2,
      reviewer_model_id: p.reviewer_model_id,
      reviewer_context_id: p.reviewer_context_id,
      verdict: p.verdict as SafetyReviewRecord['passes'][number]['verdict'],
      findings: p.findings ?? [],
      recorded_at: p.recorded_at,
    })),
    signed_off_by: r.signed_off_by,
    signed_off_at: r.signed_off_at,
    withheld_reason: r.withheld_reason,
    opened_at: r.opened_at,
  }
}

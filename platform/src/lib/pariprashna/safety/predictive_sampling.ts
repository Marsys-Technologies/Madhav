/**
 * Paripraśna safety — HS-6, PREDICTIVE-OUTPUT SAMPLING INTO THE §IS.8 CADENCE.
 *
 * SAFETY_PRIVACY_TENANCY §2 HS-6: "Served readings whose receipts carry
 * `prediction_candidates` are sampled into the standing red-team cadence
 * (§IS.8 — every third session / phase close): the sample's receipts + prose
 * are reviewed adversarially, and findings enter the normal fix-log. This is
 * the runtime hook that makes 'every predictive output is subject to the
 * red-team cadence' a detector-backed claim rather than prose."
 *
 * ── WHAT §IS.8 ACTUALLY IS, STATED BEFORE BUILDING AGAINST IT ────────────────
 * §IS.8 (MACRO_PLAN v2.0) is a GOVERNANCE cadence, not a piece of software:
 * "Red-team passes are mandatory at three cadences: (a) every third session by
 * default; (b) every macro-phase close before the SESSION_LOG seal; (c) every
 * 12 months for MP itself." There is no scheduler, no queue, no runner — the
 * cadence is discharged by a human-run session that writes a RED_TEAM artifact.
 *
 * So this module does NOT pretend to "wire predictive outputs into the §IS.8
 * mechanism", because there is no mechanism to wire into. What it builds is the
 * half that was genuinely missing: a SAMPLE POOL that a red-team session can
 * draw from, and a record of which draws were reviewed. Before this, a red-team
 * session asking "which predictive readings should I review?" had no answer
 * except "look through the conversations" — which is why MP §3.5.A.5's claim
 * was prose.
 *
 * The honest boundary: this makes the cadence's INPUT real and auditable. It
 * does not and cannot make the cadence itself run. `pendingSampleCount()` is
 * the detector that lets a session-close checklist assert the obligation was
 * discharged — and read false when it was not.
 */

import type { SafetyDb } from './types'
import { isSafetyGateEnabled } from './flag'

export type SampleState = 'pending_review' | 'reviewed' | 'excluded'

export interface RecordPredictiveSampleArgs {
  sampleId: string
  chartId: string
  turnId: string
  /** How many prediction candidates the receipt carried. Never zero here. */
  predictionCandidateCount: number
  /** The receipt hash, so the reviewer can pull the exact reading. */
  receiptHash: string | null
  /** Safety classes on the turn, so a reviewer can prioritize. */
  safetyClasses: string[]
  now?: Date
}

/**
 * Record one served predictive reading into the sample pool.
 *
 * Called from the persistence stage when the turn's detected prediction
 * candidates are non-empty. Best-effort and NON-FATAL: a sampling failure must
 * never cost a reader their reading. It returns a boolean rather than throwing,
 * and the caller logs it — a swallowed `true` would be the §N.8 defect.
 *
 * A no-op when the flag is OFF, and it returns `false` in that case, which
 * correctly reads as "nothing was sampled" rather than "sampled successfully".
 */
export async function recordPredictiveSample(
  db: SafetyDb,
  args: RecordPredictiveSampleArgs,
): Promise<boolean> {
  if (!isSafetyGateEnabled()) return false
  if (args.predictionCandidateCount <= 0) return false
  try {
    await db.query(
      `INSERT INTO pariprashna_predictive_samples (
         sample_id, chart_id, turn_id, prediction_candidate_count, receipt_hash,
         safety_classes, state, sampled_at
       ) VALUES ($1,$2,$3,$4,$5,$6,'pending_review',$7)
       ON CONFLICT (turn_id) DO NOTHING`,
      [
        args.sampleId,
        args.chartId,
        args.turnId,
        args.predictionCandidateCount,
        args.receiptHash,
        args.safetyClasses,
        (args.now ?? new Date()).toISOString(),
      ],
    )
    return true
  } catch (err) {
    console.error('[pariprashna/safety] predictive sample write failed (non-fatal):', err)
    return false
  }
}

export interface PredictiveSampleRow {
  sample_id: string
  chart_id: string
  turn_id: string
  prediction_candidate_count: number
  receipt_hash: string | null
  safety_classes: string[]
  state: SampleState
  sampled_at: string
  reviewed_at: string | null
  red_team_artifact_ref: string | null
}

/**
 * The draw a red-team session makes. Oldest-first so the pool drains rather
 * than accumulating a permanently-unreviewed tail.
 */
export async function drawPendingSamples(
  db: SafetyDb,
  limit: number,
): Promise<PredictiveSampleRow[]> {
  const { rows } = await db.query<PredictiveSampleRow>(
    `SELECT sample_id, chart_id, turn_id, prediction_candidate_count, receipt_hash,
            safety_classes, state, sampled_at::text AS sampled_at,
            reviewed_at::text AS reviewed_at, red_team_artifact_ref
       FROM pariprashna_predictive_samples
      WHERE state = 'pending_review'
      ORDER BY sampled_at ASC
      LIMIT $1`,
    [limit],
  )
  return rows
}

/**
 * Close the loop: mark a drawn sample reviewed, naming the artifact that
 * reviewed it.
 *
 * `redTeamArtifactRef` is REQUIRED. A sample marked reviewed with no artifact
 * behind it is a green signal with no detector — the exact thing §N.8 forbids.
 */
export async function markSampleReviewed(
  db: SafetyDb,
  sampleId: string,
  redTeamArtifactRef: string,
  now?: Date,
): Promise<boolean> {
  if (!isSafetyGateEnabled()) return false
  if (!redTeamArtifactRef?.trim()) {
    throw new Error(
      'SAMPLE_REVIEW_REQUIRES_ARTIFACT: a sample marked reviewed must name the red-team ' +
        'artifact that reviewed it (§N.8 — a status with no detector behind it is null, not green)',
    )
  }
  const { rows } = await db.query<{ sample_id: string }>(
    `UPDATE pariprashna_predictive_samples
        SET state = 'reviewed', reviewed_at = $2, red_team_artifact_ref = $3
      WHERE sample_id = $1 AND state = 'pending_review'
      RETURNING sample_id`,
    [sampleId, (now ?? new Date()).toISOString(), redTeamArtifactRef],
  )
  return rows.length === 1
}

/**
 * The §IS.8 obligation detector.
 *
 * A session-close checklist can ask this and get a number that is FALSE when
 * the obligation was not discharged. That is what turns "every predictive
 * output is subject to the red-team cadence" from a sentence into a claim with
 * a way to be wrong.
 */
export async function pendingSampleCount(db: SafetyDb): Promise<number> {
  const { rows } = await db.query<{ n: string }>(
    `SELECT count(*)::text AS n FROM pariprashna_predictive_samples WHERE state = 'pending_review'`,
  )
  return Number(rows[0]?.n ?? 0)
}

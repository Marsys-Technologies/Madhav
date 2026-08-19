/**
 * Paripraśna consent — THE EXCLUDED-SUBJECT REGISTER (§3.5.F, carried).
 *
 * "Exclusions (minors, consent-incapacity) are LOGGED — no corpus produced, no
 * analysis performed — in their own register, so the exclusion discipline is
 * itself auditable."
 *
 * Shape decision: a TABLE, not a view over `chart_subject_consent`. A view could
 * only ever project exclusions that are already recorded as consent columns —
 * and the two most important exclusion reasons are precisely the ones that have
 * NO consent row to project from (`no_consent_row`) or that are computed at
 * serve time from a different table entirely (`minor`, from `charts.birth_date`).
 * A view would silently show an empty register for the exact cases §3.5.F exists
 * to make auditable.
 *
 * The register does NOT accrete one row per served request: a partial unique
 * index on `(chart_id, exclusion_reason) WHERE cleared_at IS NULL` keeps one
 * OPEN row per reason, and re-detection refreshes `detected_at` + `evidence`.
 * An exclusion that later stops applying (a minor turns 18) is CLEARED, never
 * deleted — the register is a history, not a current-state cache.
 */

import type { ConsentQueryable, ExclusionReason, ExclusionRow } from './types'

export interface RegisterExclusionInput {
  chartId: string
  reason: ExclusionReason
  /** The specific code path that produced this exclusion. Never a generic label. */
  detector: string
  subjectAgeYears?: number | null
  evidence?: Record<string, unknown>
}

/**
 * Log (or refresh) an open exclusion. Idempotent per (chart, reason).
 * Returns the register row as stored.
 */
export async function registerExclusion(
  db: ConsentQueryable,
  input: RegisterExclusionInput,
): Promise<ExclusionRow> {
  const { rows } = await db.query<ExclusionRow>(
    `INSERT INTO chart_subject_exclusions
       (chart_id, exclusion_reason, detector, subject_age_years, evidence)
     VALUES ($1, $2, $3, $4, $5::jsonb)
     ON CONFLICT (chart_id, exclusion_reason) WHERE cleared_at IS NULL
     DO UPDATE SET detector          = EXCLUDED.detector,
                   subject_age_years = EXCLUDED.subject_age_years,
                   evidence          = EXCLUDED.evidence,
                   detected_at       = now()
     RETURNING *`,
    [
      input.chartId,
      input.reason,
      input.detector,
      input.subjectAgeYears ?? null,
      JSON.stringify(input.evidence ?? {}),
    ],
  )
  return rows[0]
}

/**
 * Clear an open exclusion (e.g. a minor subject who has since turned 18).
 * A no-op when no open row exists — clearing something that was never excluded
 * is not an error, and inventing one would make callers guard pointlessly.
 */
export async function clearExclusion(
  db: ConsentQueryable,
  chartId: string,
  reason: ExclusionReason,
  clearedReason: string,
): Promise<number> {
  const { rows } = await db.query<{ exclusion_id: number }>(
    `UPDATE chart_subject_exclusions
        SET cleared_at = now(), cleared_reason = $3
      WHERE chart_id = $1 AND exclusion_reason = $2 AND cleared_at IS NULL
      RETURNING exclusion_id`,
    [chartId, reason, clearedReason],
  )
  return rows.length
}

/** Every open exclusion for one chart. */
export async function listOpenExclusions(
  db: ConsentQueryable,
  chartId: string,
): Promise<ExclusionRow[]> {
  const { rows } = await db.query<ExclusionRow>(
    `SELECT * FROM chart_subject_exclusions
      WHERE chart_id = $1 AND cleared_at IS NULL
      ORDER BY exclusion_reason`,
    [chartId],
  )
  return rows
}

/** The whole register for one chart, open and cleared, newest first. */
export async function listExclusionHistory(
  db: ConsentQueryable,
  chartId: string,
): Promise<ExclusionRow[]> {
  const { rows } = await db.query<ExclusionRow>(
    `SELECT * FROM chart_subject_exclusions
      WHERE chart_id = $1
      ORDER BY detected_at DESC, exclusion_id DESC`,
    [chartId],
  )
  return rows
}

/**
 * The register as a whole — every currently-excluded subject. This is the
 * surface an audit reads to answer "who is the instrument refusing to serve,
 * and why?" without having to re-derive it from serving logs.
 */
export async function listExcludedSubjects(db: ConsentQueryable): Promise<ExclusionRow[]> {
  const { rows } = await db.query<ExclusionRow>(
    `SELECT * FROM chart_subject_exclusions
      WHERE cleared_at IS NULL
      ORDER BY detected_at DESC, exclusion_id DESC`,
  )
  return rows
}

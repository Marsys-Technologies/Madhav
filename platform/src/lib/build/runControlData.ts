import 'server-only'
import { query } from '@/lib/db/client'

/** Existing super-admin run control statements. Authorization, HTTP/error mapping
 * and resume dispatch stay with the callers; no transaction or job is opened here.
 */

export function requestBuildRunPause(id: string) {
  return query<{ id: string; state: string }>(
      `UPDATE build_runs
       SET pause_requested_at = NOW()
       WHERE id=$1 AND state = 'running'
       RETURNING id, state`,
      [id]
    )
}

export function requestBuildRunStop(id: string) {
  return query<{ id: string }>(
      `WITH requested AS (
         UPDATE build_runs
         SET stop_requested_at = NOW(),
             ended_at = CASE WHEN state IN ('planned','paused') THEN NOW() ELSE ended_at END,
             state = CASE WHEN state IN ('planned','paused') THEN 'stopped' ELSE state END
         WHERE id=$1 AND state IN ('planned','running','paused')
         RETURNING id, state
       ), aborted AS (
         UPDATE build_run_assets b
         SET state = 'aborted', ended_at = NOW(), error = 'Stopped before this asset started.'
         FROM requested r
         WHERE b.run_id = r.id AND r.state = 'stopped' AND b.state = 'queued'
         RETURNING 1
       )
       SELECT id FROM requested`,
      [id]
    )
}

export function claimPausedBuildRun(id: string) {
  return query<{ id: string; resume_requested_at: string }>(
      `UPDATE build_runs
       SET state = 'planned', pause_requested_at = NULL, resume_requested_at = NOW()
       WHERE id=$1 AND state = 'paused'
         AND plan_manifest IS NOT NULL AND plan_manifest_digest IS NOT NULL
       RETURNING id, resume_requested_at::text AS resume_requested_at`,
      [id]
    )
}

export function readBuildRunResumeState(id: string) {
  return query<{ state: string; has_manifest: boolean }>(
        `SELECT state,
                (plan_manifest IS NOT NULL AND plan_manifest_digest IS NOT NULL) AS has_manifest
           FROM build_runs WHERE id=$1`,
        [id]
      )
}

export function restorePausedBuildRunAfterDispatchFailure(detail: string, id: string, requestedAt: string) {
  return query(
        `UPDATE build_runs
         SET state = 'paused', pause_requested_at = NOW(), last_error = $1
         WHERE id=$2 AND state = 'planned' AND resume_requested_at = $3::timestamptz`,
        [detail, id, requestedAt]
      )
}

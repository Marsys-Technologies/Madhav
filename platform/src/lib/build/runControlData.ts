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
      `UPDATE build_runs
       SET stop_requested_at = NOW(),
           state = CASE WHEN state = 'planned' THEN 'stopped' ELSE state END
       WHERE id=$1 AND state IN ('planned','running','paused')
       RETURNING id`,
      [id]
    )
}

export function claimPausedBuildRun(id: string) {
  return query<{ id: string; action?: string }>(
      `UPDATE build_runs
       SET state = 'planned', pause_requested_at = NULL
       WHERE id=$1 AND state = 'paused'
         AND plan_manifest IS NOT NULL AND plan_manifest_digest IS NOT NULL
       RETURNING id, action`,
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

export function restorePausedBuildRunAfterDispatchFailure(detail: string, id: string) {
  return query(
        `UPDATE build_runs
         SET state = 'paused', pause_requested_at = NOW(), last_error = $1
         WHERE id=$2 AND state = 'planned'`,
        [detail, id]
      )
}

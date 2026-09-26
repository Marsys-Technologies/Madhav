/**
 * terminalizeFailedRun.ts — Packet A2 ("Always record why it failed").
 *
 * Shared helper for the "dispatch a run, then invokeRunJob throws" idiom, which
 * was copy-pasted across four TypeScript call sites (platform/src/app/api/cockpit/
 * watchdog/route.ts, platform/src/app/api/cockpit/runs/route.ts x2, platform/src/
 * lib/build/recalibrationEnqueue.ts). All four wrote the caught error's message to
 * build_runs.last_error, then aborted the run's still-queued build_run_assets rows
 * with NO error text at all — even though the exact message was already computed
 * and sitting in scope one line above. That silent gap accounted for 295 of 301
 * (98%) of all empty-error build_run_assets records measured before this fix
 * (00_ARCHITECTURE/briefs/nirmana/engine/measurements/A2_before_20260926T120820Z.json).
 *
 * Mirrors the reference-good pattern already in this repo on the Python side —
 * `_terminalize_preflight_failure`
 * (platform/python-sidecar/pipeline/orchestrator/runner.py:325-337) — which writes
 * the same message to both tables in one CTE. This is the TypeScript-side
 * equivalent for the "run never got a chance to dispatch" case.
 *
 * `message` must be non-empty, attributable text: the caught exception's own
 * `.message`, or a literal describing which reaper/dispatcher fired. If a caller
 * passes empty/whitespace text (e.g. an exception whose `.message` is `''`), this
 * helper writes a distinguishable, honestly-labeled fallback instead of storing an
 * empty string — never a vague "unknown error" that would be indistinguishable
 * from the defect this packet fixes. See CLAUDE.md §N.7 item 6 / §N.8.
 */
import { query } from '@/lib/db/client'

export const TERMINALIZE_EMPTY_MESSAGE_FALLBACK =
  'dispatch failed: caller supplied no error message (exception had an empty .message)'

/**
 * Fail a specific, already-known run (by id) and abort its still-queued
 * build_run_assets rows in one atomic statement, propagating the same
 * attributable text to both build_runs.last_error and build_run_assets.error.
 *
 * Idempotent by construction: the inner CTE only matches build_runs rows not
 * already 'failed'/'completed'/'stopped' at a terminal state that would make a
 * re-application meaningless, and the build_run_assets UPDATE only matches rows
 * still 'queued' — re-running this for the same runId after it already applied
 * is a no-op (nothing left to match).
 */
export async function terminalizeFailedRun(runId: string, message: string): Promise<void> {
  const errorText = message && message.trim().length > 0 ? message : TERMINALIZE_EMPTY_MESSAGE_FALLBACK

  await query(
    `WITH failed_run AS (
       UPDATE build_runs
       SET state = 'failed', ended_at = NOW(), last_error = $1
       WHERE id = $2
         AND state NOT IN ('completed', 'failed', 'stopped')
       RETURNING id
     )
     UPDATE build_run_assets
     SET state = 'aborted', ended_at = NOW(), error = $1
     WHERE run_id IN (SELECT id FROM failed_run)
       AND state = 'queued'`,
    [errorText, runId]
  )
}

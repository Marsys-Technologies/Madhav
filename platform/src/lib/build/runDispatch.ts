import 'server-only'
import { query } from '@/lib/db/client'
import { invokeRunJob } from '@/lib/build/jobInvoker'

/**
 * Post-commit dispatch of a prepared run (Jātaka chart workspace, Task 5).
 *
 * Job invocation can never be rolled back, so it always happens after the
 * preparation transaction commits. On failure the run is marked failed and its
 * queued assets aborted so nothing orphans as 'planned'. The chart-correction
 * path passes `failurePrefix: 'JOB_DISPATCH_FAILED'`, which the shared readiness
 * authority reads as Needs rebuild; the cockpit keeps its raw error text.
 */
export type DispatchResult =
  | { ok: true; executionName: string }
  | { ok: false; code: 'JOB_DISPATCH_FAILED'; message: string }

export async function dispatchPreparedRun(
  runId: string,
  options: { failurePrefix?: string } = {},
): Promise<DispatchResult> {
  try {
    const invocation = await invokeRunJob(runId)
    return { ok: true, executionName: invocation?.executionName ?? '' }
  } catch (error) {
    const message = (error as Error)?.message ?? String(error)
    const lastError = options.failurePrefix ? `${options.failurePrefix}: ${message}` : message
    try {
      await query(`UPDATE build_runs SET state='failed', ended_at=NOW(), last_error=$1 WHERE id=$2`, [lastError, runId])
      await query(`UPDATE build_run_assets SET state='aborted' WHERE run_id=$1 AND state='queued'`, [runId])
    } catch (recordError) {
      // The watchdog's undispatched-run reaper still fails an orphaned 'planned' run;
      // the caller is told the truth about the dispatch either way.
      console.error('[build/runDispatch] could not record dispatch failure:', (recordError as Error)?.message)
    }
    return { ok: false, code: 'JOB_DISPATCH_FAILED', message }
  }
}

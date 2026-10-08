import 'server-only'
import { invokeRunJob } from '@/lib/build/jobInvoker'
import { terminalizeFailedRun } from '@/lib/build/terminalizeFailedRun'

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
  options: { failurePrefix?: string; forceExecute?: boolean } = {},
): Promise<DispatchResult> {
  try {
    const invocation = options.forceExecute
      ? await invokeRunJob(runId, { forceExecute: true })
      : await invokeRunJob(runId)
    return { ok: true, executionName: invocation?.executionName ?? '' }
  } catch (error) {
    const message = (error as Error)?.message ?? String(error)
    const lastError = options.failurePrefix ? `${options.failurePrefix}: ${message}` : message
    try {
      // A2: one statement, the same attributable text on both build_runs.last_error and the
      // aborted build_run_assets.error (previously the assets were aborted with no error text).
      await terminalizeFailedRun(runId, lastError)
    } catch (recordError) {
      // The watchdog's undispatched-run reaper still fails an orphaned 'planned' run;
      // the caller is told the truth about the dispatch either way.
      console.error('[build/runDispatch] could not record dispatch failure:', (recordError as Error)?.message)
    }
    return { ok: false, code: 'JOB_DISPATCH_FAILED', message }
  }
}

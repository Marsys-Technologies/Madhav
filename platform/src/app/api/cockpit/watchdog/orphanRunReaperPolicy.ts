// Pure mirror of clause 1's SQL decision boundary (route.ts, the orphan-run reaper),
// extracted purely so the boundary can be exercised directly in a unit test without a
// live Postgres — the same reason classifyStuckCandidate.ts is a sibling module (see
// its own file-header comment) and the reason the Python orchestrator side of this
// same incident used an equivalent hand-rolled mirror in
// platform/python-sidecar/tests/test_watchdog_heartbeat_fix.py
// (`_watchdog_clause2_would_reap`).
//
// This function is NOT called by route.ts — clause 1 is a single set-based
// UPDATE ... WHERE ... NOT EXISTS statement evaluated by Postgres over the whole
// build_runs/asset_throughput/build_substep_progress state, not a per-row JS
// decision route.ts could invoke. Keeping this mirror in lock-step with route.ts's
// actual SQL is a manual discipline: any change to clause 1's thresholds or
// evidence sources in route.ts must be mirrored here (and vice versa), and the
// route.test.ts SQL-text assertions exist specifically to catch drift between the
// two (see "clause 1 SQL text matches the reaper-policy mirror" test).
//
// INCIDENT (2026-07-31/08-01): clause 1 originally consulted asset_throughput.
// last_built_at ALONE, with a 10-minute window. A heavy writer's substep cadence
// (~5-6.5 min, ~7 min worst case for ka_gochara_sweep) left too little margin,
// and a run was falsely killed while its container was alive and progressing
// (build_substep_progress showed fresh commits the reaper never consulted). Fixed
// by (a) widening the window to 15 minutes and (b) treating a recent
// build_substep_progress commit for the chart as independent, corroborating
// evidence of life — either signal being recent is sufficient to spare the run.

export const ORPHAN_RUN_MIN_AGE_MINUTES = 30
export const ORPHAN_RUN_EVIDENCE_WINDOW_MINUTES = 15

export interface OrphanRunReaperInput {
  /** build_runs.state */
  runState: string
  /** build_runs.started_at */
  startedAt: Date
  /** MAX(asset_throughput.last_built_at) across all rows for this run's chart_id, or null if none. */
  latestAssetThroughputAt: Date | null
  /** MAX(build_substep_progress.completed_at) across all rows for this run's chart_id, or null if none. */
  latestSubstepProgressAt: Date | null
}

/**
 * Mirrors route.ts clause 1: true iff this run WOULD be reaped (marked 'failed').
 *
 * A run is reaped only when ALL of:
 *   - state = 'running'
 *   - started_at is older than ORPHAN_RUN_MIN_AGE_MINUTES
 *   - NEITHER asset_throughput NOR build_substep_progress shows activity within
 *     ORPHAN_RUN_EVIDENCE_WINDOW_MINUTES for the run's chart
 */
export function wouldReapOrphanRun(input: OrphanRunReaperInput, now: Date): boolean {
  if (input.runState !== 'running') return false

  const ageMs = now.getTime() - input.startedAt.getTime()
  const minAgeMs = ORPHAN_RUN_MIN_AGE_MINUTES * 60_000
  if (ageMs <= minAgeMs) return false

  const evidenceWindowMs = ORPHAN_RUN_EVIDENCE_WINDOW_MINUTES * 60_000
  const cutoff = now.getTime() - evidenceWindowMs

  const hasRecentThroughput =
    input.latestAssetThroughputAt != null && input.latestAssetThroughputAt.getTime() > cutoff
  const hasRecentSubstepProgress =
    input.latestSubstepProgressAt != null && input.latestSubstepProgressAt.getTime() > cutoff

  return !hasRecentThroughput && !hasRecentSubstepProgress
}

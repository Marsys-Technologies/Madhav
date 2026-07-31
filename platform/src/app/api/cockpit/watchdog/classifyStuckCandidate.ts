// Extracted from route.ts so it can be unit-tested without a database (Next's
// build-time route-shape check forbids a route.ts from exporting anything other
// than GET/POST/route-config — the same reason cockpit/stats/deriveState.ts is a
// sibling module rather than inline).
//
// SAMĀPTI B-WATCHDOG-LIT · DVA Ruling 10 · finding F3.
//
// This is the watchdog's stuck-'building'-asset promotion predicate. It decides
// what a heartbeat that has gone stale (>15 min) actually means for one asset.
//
// The defect this closes: the predicate used to be "rows present ⇒ 'lit'". For a
// writer with a real substep plan that is wrong, because such a writer commits
// per substep (asset_runner.py `_drive_substeps` — one commit and one heartbeat
// per substep), so rows exist from substep 1 onward. A 303-substep sweep that
// died at substep 78 has rows present and a stale heartbeat, and was therefore
// promoted to 'lit' — falsely reporting a 26%-built asset as complete and
// unblocking every downstream dependant on it.
//
// Why this module cannot simply check completeness: the size of a writer's plan
// is never persisted. `build_substep_progress` (migration 436) records only the
// substeps that DID commit; the plan total exists solely as `len(substeps)`
// inside the Python orchestrator process and in a transient SSE event. The
// Python path proves completeness by re-invoking the writer's own
// `plan_substeps(ctx)` (asset_runner.py:596-630), which this out-of-band
// TypeScript reaper has no way to call. Deriving a total from anything available
// here would be a fabricated computation (CLAUDE.md §B.10).
//
// So completeness is UNPROVABLE from here for plan-bearing writers, and the rule
// is that unproven is not proven. The result is strictly more conservative than
// the predicate it replaces: every input that now yields 'withhold-incomplete'
// previously yielded 'rescue-lit', and no input yields 'rescue-lit' that did not
// before. It can only ever promote fewer assets, never more.

export type StuckCandidateVerdict =
  // Data confirmed present and no substep plan to finish → the original D-3
  // Part B rescue: a slow-but-succeeding write whose own state flip raced a
  // crash. Promote to 'lit'.
  | 'rescue-lit'
  // Data confirmed present, but the asset has a substep plan whose completion
  // cannot be established here. Record 'incomplete' (migration 474) — honest,
  // and deliberately outside the ('lit','service_ok') dependency-satisfied
  // allowlist, so downstream stays blocked until a rebuild finishes the plan.
  | 'withhold-incomplete'
  // No data confirmed present. Unchanged behaviour: a genuine stuck writer.
  | 'error'

export interface StuckCandidate {
  // asset_registry.has_substeps. true = the writer declares a real substep plan.
  // false/NULL = a light writer with no plan; nothing to prove complete.
  has_substeps: boolean | null
  // asset_registry.target_floor. 0 is the explicit declaration that zero rows is
  // this asset's correct complete state (CLAUDE.md §N.4).
  target_floor: number | null
}

/**
 * @param candidate  registry metadata for the stuck asset
 * @param actualRows rows counted via asset_registry.count_sql, or null when the
 *                   asset declares no count_sql or the probe threw. null means
 *                   "unknown", which is never treated as evidence of completion.
 */
export function classifyStuckCandidate(
  candidate: StuckCandidate,
  actualRows: number | null
): StuckCandidateVerdict {
  // Same "zero_rows_is_complete" rule as the Python writer path (§N.4): rows
  // present, OR target_floor=0 declaring 0 rows as the correct complete state.
  const dataConfirmedComplete =
    actualRows != null && (actualRows > 0 || candidate.target_floor === 0)

  if (!dataConfirmedComplete) return 'error'
  if (candidate.has_substeps === true) return 'withhold-incomplete'
  return 'rescue-lit'
}

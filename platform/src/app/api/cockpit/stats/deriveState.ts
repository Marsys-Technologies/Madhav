// Extracted from route.ts (not a Next.js route file itself, so it can be unit-tested and
// export more than GET/POST/route-config — Next's build-time route-shape check forbids any
// other export from a route.ts file, which is why this logic cannot live there directly).

export type AssetState = 'lit' | 'building' | 'stale' | 'dormant' | 'error' | 'partial' | 'incomplete' | 'not_migrated' | 'service_ok'

// Badge-honesty defect (pre-D-4b readiness pass, native-flagged, 2026-07-21): a HEAVY
// (has_substeps=true) writer whose build hit its own writer_timeout_seconds mid-materialization
// is marked asset_throughput.state='error' by the orchestrator (platform/python-sidecar/pipeline/
// orchestrator/runner.py::_mark_asset_blocked) — the SAME surfaced state as a genuinely broken
// writer (a real exception, a schema mismatch, a permanently-failing query). The two are NOT the
// same operator situation: one is "safely resumable, just not finished yet" (the substep-
// resumption ledger, build_substep_progress, already supports picking up exactly where a prior
// dispatch left off — see ka_gochara_sweep.writer's own `plan_substeps`); the other needs
// engineering attention. `deriveState` now distinguishes them when substep-ledger evidence is
// available: any committed-substep count > 0 for a `has_substeps` asset in the `error` state
// downgrades the badge to `partial` (never silently reported as `lit`/`stale`/`dormant`, and
// never conflated with a genuinely broken `error`).
//
// ── SAMĀPTI B-COCKPIT-INCOMPLETE (DVA Ruling 24, 2026-07-30) ──────────────────────────
// The `partial` mechanism above is keyed on `error` being NON-NULL. That made a
// DIAGNOSTIC STRING the sole load-bearing signal for a SEMANTIC state, and it was
// already broken in production: the Python orchestrator's own 'incomplete' write path
// (`asset_runner.py::_run_data_writer`, the SATYA-DĪPA no-op-completion rejection, and
// migration 474 which added the state) sets `state = 'incomplete', rows_written = <rows
// present>, last_error = NULL` in a single UPDATE. With `error` NULL, control fell
// straight through the `if (error)` block to `if (actualRows > 0) return 'lit'` — so a
// Python-produced `incomplete` asset, which by construction has rows present, rendered
// as a green LIT badge in the cockpit while `asset_throughput.state` honestly said
// 'incomplete'. That is a falsely-lit operator surface and it directly falsifies the
// convergence check "no asset lit with an incomplete substep plan".
//
// The fix is a FIRST-CLASS `incomplete` branch keyed on `asset_throughput.state` — the
// authoritative state column — placed ahead of BOTH the `error` block and the
// `actualRows > 0` fallthrough. Consequences, deliberately:
//   * The same stored state now always produces the same badge. The TypeScript watchdog
//     path writes 'incomplete' WITH a last_error string (deliberately, as belt-and-
//     braces); the Python path writes it with last_error NULL. Before this branch those
//     two produced 'partial' and 'lit' respectively — two different badges for one
//     stored state, decided by whether a message happened to be attached. Now both
//     produce 'incomplete', and the `error`-keyed `partial` path is belt-and-braces
//     rather than the sole mechanism, exactly as Ruling 24 requires.
//   * No future "clear the stale error message" commit can silently re-light an
//     incomplete asset. That commit has, in effect, already been written once.
//
// Why the branch keys on the state column and NOT on a computed substep ratio: the
// substep plan's TOTAL is never persisted anywhere. `build_substep_progress` (migration
// 436) records only which substeps DID commit; the total lives in-process in
// `_drive_substeps` and in a transient SSE frame. Deriving "incomplete" from
// `substepsCommitted` alone would require inventing a denominator — a fabricated
// computation (CLAUDE.md §B.10). The writers themselves already do the completeness
// arithmetic (`plan_substeps(ctx)` returning zero remaining) and persist the ANSWER as
// `asset_throughput.state`. Reading that answer IS deriving from substep completeness;
// re-deriving it here from an incomplete input would not be.
export function deriveState(
  asset: { is_active?: boolean; target_floor?: number | null; asset_type?: string | null; asset_kind?: string | null; has_substeps?: boolean },
  actualRows: number | null,
  error: string | null,
  throughputState: string | null,
  substepsCommitted: number | null = null
): AssetState {
  // Service assets have no count_sql/target_table by design — they are healthy
  // when registered + CURRENT. They must never fall through to the data-asset
  // dormant/error logic below. Check both asset_type (L1/L2 legacy) and
  // asset_kind (L3+ canonical) so new-layer service registrations are caught.
  if (asset.asset_type === 'service' || asset.asset_kind === 'service') return 'service_ok'
  if (asset.is_active === false) return 'not_migrated'
  // SAMĀPTI B-COCKPIT-INCOMPLETE (DVA Ruling 24): first-class, and FIRST — ahead of the
  // `error` block and the `actualRows > 0` fallthrough alike. 'incomplete' (migration 474)
  // means "ran; some data IS present from committed substeps; the writer's own substep plan
  // reports work still remaining". Rows being present is precisely what makes this state
  // dangerous, not what makes it safe: it is the reason the fallthrough used to light it.
  // It is NOT in the ('lit','service_ok') dependency-satisfied allowlist, so the backend
  // correctly keeps downstream dependants blocked — the cockpit must not contradict that.
  // Deliberately independent of `error`: whether a diagnostic string is attached does not
  // change what the asset IS.
  if (throughputState === 'incomplete') return 'incomplete'
  if (error) {
    if (asset.has_substeps && substepsCommitted != null && substepsCommitted > 0) return 'partial'
    return 'error'
  }
  // 'building' must precede the actualRows check: the fast-path sets actual_rows=rows_written
  // which climbs from 0 during a build. Without this guard the bar would flip to 'lit' at the
  // first committed batch even though the asset is still actively building.
  if (throughputState === 'building') return 'building'
  // §N.4: count_sql is authoritative for data presence. Rows present = lit,
  // regardless of throughput state or target_floor. Floors are aspirational,
  // NOT gates — an asset with rows > 0 and no active zero-row build is lit.
  // An orphaned record or cascade-stale flag does NOT override real data confirmed by count_sql.
  if (actualRows != null && actualRows > 0) return 'lit'
  // §N.4: target_floor=0 declares that 0 rows IS the correct complete state for this asset
  // (e.g. ga_prashna on natal charts — writer ran, evaluated, found no prashna question).
  // When throughput confirms completion and 0 rows is by design, honour it as lit.
  if (throughputState === 'lit' && actualRows === 0 && asset.target_floor === 0) return 'lit'
  // No rows at all: fall back to throughput state for in-progress vs stale vs dormant.
  // A writer that ran but produced 0 rows and target_floor > 0 (e.g. mi_jivanaghatana
  // with no life_events) should show as 'dormant' not 'lit'.
  if (throughputState === 'lit' && actualRows !== 0) return 'lit'
  if (throughputState === 'stale') return 'stale'
  return 'dormant'
}

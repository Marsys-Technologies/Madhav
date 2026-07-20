// Extracted from route.ts (not a Next.js route file itself, so it can be unit-tested and
// export more than GET/POST/route-config — Next's build-time route-shape check forbids any
// other export from a route.ts file, which is why this logic cannot live there directly).

export type AssetState = 'lit' | 'building' | 'stale' | 'dormant' | 'error' | 'partial' | 'not_migrated' | 'service_ok'

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

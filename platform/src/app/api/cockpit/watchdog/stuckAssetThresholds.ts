// Per-asset stuck-asset staleness thresholds for the watchdog (HYG-REAPER-LONG-SUBSTEP).
//
// Sibling module, not route.ts: a Next.js route file may export only route
// handlers/config (same reason as classifyStuckCandidate.ts / watchdogMessages.ts).
//
// WHY: both reaper clauses in route.ts treat "no asset_throughput.last_built_at
// advance for 15 min" as proof a build is dead. That window is right for every asset
// whose substep (or whole write) finishes well inside it, but the heartbeat is stamped
// once per substep commit, and a substep is ONE multi-minute transaction (PostgreSQL
// NOW() is the transaction START time — see route.ts file header). A healthy substep
// longer than the window is therefore reaped mid-flight: the stuck path writes
// asset_throughput + build_run_assets to error/incomplete under a live writer.
// MEASURED (J-3c, EXEC-J3C-REPROJECT-1): ka_gochara_v5 substep 34 (verify:bereavement)
// took 1,086.8 s (18.1 min) on a healthy run — above the 900 s window.
//
// ROUTE (OWNER-FROZEN-EDIT-CONDITIONAL-20261018: registry-threshold route first, no
// FROZEN edit): the watchdog, not the orchestrator, learns that some assets legitimately
// go quiet longer. Nothing in `_drive_substeps` / the writers changes.
//
// SOURCE OF THE OVERRIDES — (I) INTERPRETATION: the natural home is an
// `asset_registry` column, but that needs an additive migration and no migration number
// was allocated to this item (MIGRATION_ALLOCATION.json). The overrides are therefore a
// reviewed constant keyed by `asset_registry.asset_id`. The SQL consumes them as bound
// parameters in one shape (`unnest($ids::text[], $secs::int[])`), so moving the source to
// a registry column later swaps this table for a join without touching the clauses.
//
// SEMANTICS: the effective threshold is GREATEST(default, override). An override can only
// LENGTHEN an asset's grace; it can never shorten the 15-min default, and an asset with
// no entry behaves exactly as before. A truly dead writer still stops heartbeating and is
// reaped once it is stale beyond ITS threshold (a genuine hang is delayed, not exempted).

/** The 15-minute window every asset without an override keeps (route.ts clauses 1 and 2). */
export const DEFAULT_STUCK_ASSET_THRESHOLD_SECONDS = 900

/**
 * asset_id → seconds of heartbeat silence tolerated before the asset is judged stuck.
 *
 * ka_gochara_v5: 3,600 s. Longest measured healthy substep is 1,086.8 s (J-3c substep 34);
 * the SR-J3-REAPER-PAUSE stall rule uses max(45 min, 3 x longest real substep) = 54.4 min
 * for the same purpose, so 60 min (3.3 x measured, rounded up) clears that and leaves
 * headroom for a heavier chart (the J-4e/f century build) without disabling hang detection.
 */
export const STUCK_ASSET_THRESHOLD_OVERRIDES_SECONDS: Readonly<Record<string, number>> = {
  ka_gochara_v5: 3600,
}

/** Effective stuck threshold in seconds for one asset: GREATEST(default, override). */
export function stuckThresholdSeconds(
  assetId: string,
  overrides: Readonly<Record<string, number>> = STUCK_ASSET_THRESHOLD_OVERRIDES_SECONDS
): number {
  const override = Object.prototype.hasOwnProperty.call(overrides, assetId) ? overrides[assetId] : 0
  return Math.max(DEFAULT_STUCK_ASSET_THRESHOLD_SECONDS, override)
}

/** Bound parameters (asset ids, seconds) for the SQL fragments below. Only real extensions. */
export function stuckThresholdOverrideParams(
  overrides: Readonly<Record<string, number>> = STUCK_ASSET_THRESHOLD_OVERRIDES_SECONDS
): [string[], number[]] {
  const entries = Object.entries(overrides).filter(
    ([, s]) => Number.isInteger(s) && s > DEFAULT_STUCK_ASSET_THRESHOLD_SECONDS
  )
  return [entries.map(([id]) => id), entries.map(([, s]) => s)]
}

/**
 * SQL boolean: the `assetCol`/`heartbeatCol` row has been silent longer than its
 * per-asset override (TRUE when the asset has no override, so the unchanged 15-minute
 * clause alone decides). `idsParam` / `secsParam` are `$n` placeholders bound to
 * stuckThresholdOverrideParams().
 */
export function staleBeyondOverrideSql(
  assetCol: string,
  heartbeatCol: string,
  idsParam: string,
  secsParam: string
): string {
  return `NOT EXISTS (
         SELECT 1 FROM unnest(${idsParam}::text[], ${secsParam}::int[]) AS o(asset_id, secs)
         WHERE o.asset_id = ${assetCol}
           AND ${heartbeatCol} >= NOW() - make_interval(secs => o.secs)
       )`
}

/**
 * SQL boolean for clause 1 (orphan run): the chart has an in-flight ('building') asset
 * whose heartbeat is still inside ITS override window — independent evidence of life,
 * additive to the unchanged 15-minute asset_throughput / build_substep_progress checks.
 * Only assets with an override can match, so default assets behave exactly as before.
 */
export function aliveWithinOverrideSql(chartCol: string, idsParam: string, secsParam: string): string {
  return `EXISTS (
           SELECT 1
           FROM asset_throughput ovr
           JOIN unnest(${idsParam}::text[], ${secsParam}::int[]) AS o(asset_id, secs)
             ON o.asset_id = ovr.asset_id
           WHERE ovr.chart_id = ${chartCol}
             AND ovr.state = 'building'
             AND ovr.last_built_at >= NOW() - make_interval(secs => o.secs)
         )`
}

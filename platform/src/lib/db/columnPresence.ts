// Packet B1 — C-1 (review B1_review_20260926T182200Z.md, BLOCKS THE DEPLOY).
//
// Shared, process-lifetime cache for "does this column exist in THIS environment
// yet". Extracted out of any single route.ts because more than one route needs the
// same answer (cockpit/stats and cockpit/runs/active both select
// build_run_assets.blocked_by_asset_id) and a route.ts file may only export
// GET/POST/route-config (Next's build-time route-shape check forbids any other
// export from a route.ts file — the same reason deriveState.ts was pulled out of
// stats/route.ts).
//
// Mirrors asset_runner.py's `_duration_columns_present` pattern (migration 1094's
// own graceful-degradation precedent): probe ONCE per process via
// information_schema.columns, cache the boolean, never re-probe per request. A
// route that selects a column before its migration has applied in this environment
// must degrade to omitting that column — never throw and let an outer catch turn
// the whole response into a silent, HTTP-200 blank.
import { query } from '@/lib/db/client'

const _cache = new Map<string, boolean>()

/**
 * Returns whether `column` exists on `table` in the `public` schema, probing once
 * per (table, column) pair for the lifetime of this process and caching the result.
 *
 * `table`/`column` must be trusted, compile-time-known identifiers (never
 * user input) — they are interpolated as bound query parameters here (not string-
 * concatenated into SQL), so this is safe regardless, but the cache key assumes a
 * small, fixed set of callers, not an unbounded one.
 */
export async function columnPresent(table: string, column: string): Promise<boolean> {
  const key = `${table}.${column}`
  const cached = _cache.get(key)
  if (cached !== undefined) return cached
  const { rows } = await query<{ present: number }>(
    `SELECT 1 AS present FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = $1 AND column_name = $2`,
    [table, column]
  )
  const present = rows.length > 0
  _cache.set(key, present)
  if (!present) {
    console.warn(
      `[columnPresence] ${key} is ABSENT in this environment — every request this ` +
      'process serves will degrade gracefully by omitting it, until this process is ' +
      'restarted after the owning migration applies.'
    )
  }
  return present
}

/** Packet B1: build_run_assets.blocked_by_asset_id (migration 1095). */
export function blockedByAssetIdColumnPresent(): Promise<boolean> {
  return columnPresent('build_run_assets', 'blocked_by_asset_id')
}

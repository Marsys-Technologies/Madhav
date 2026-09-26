// Packet B2 ("the DAG-derived downstream count") — mirrors columnPresence.ts's
// process-lifetime cache pattern (itself mirroring asset_runner.py's
// `_duration_columns_present`, migration 1094's graceful-degradation precedent),
// applied to a RELATION instead of a column: does vw_asset_downstream_dependents
// exist in THIS environment yet (migration 1096 may not have reached it).
//
// A route that queries a view before its migration has applied must degrade to
// omitting that value — never throw and turn the whole response into a silent,
// HTTP-200 blank, and never fabricate a 0 standing in for "not yet computed"
// (§N.8 — an absent-or-zero figure must render honestly as ABSENT, not as a
// confident number; see stats/route.ts's own comment on downstream_dependent_count
// and AssetRow.tsx's rendering of it).
import { query } from '@/lib/db/client'

const _cache = new Map<string, boolean>()

/**
 * Returns whether `view` exists in the `public` schema, probing once per view for
 * the lifetime of this process and caching the result.
 */
export async function viewPresent(view: string): Promise<boolean> {
  const cached = _cache.get(view)
  if (cached !== undefined) return cached
  const { rows } = await query<{ present: number }>(
    `SELECT 1 AS present FROM information_schema.views
      WHERE table_schema = 'public' AND table_name = $1`,
    [view]
  )
  const present = rows.length > 0
  _cache.set(view, present)
  if (!present) {
    console.warn(
      `[viewPresence] ${view} is ABSENT in this environment — every request this ` +
      'process serves will degrade gracefully by omitting it, until this process is ' +
      'restarted after the owning migration applies.'
    )
  }
  return present
}

/** Packet B2: vw_asset_downstream_dependents (migration 1096). */
export function downstreamDependentsViewPresent(): Promise<boolean> {
  return viewPresent('vw_asset_downstream_dependents')
}

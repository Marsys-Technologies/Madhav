/**
 * authorizeChartAccess — Unit 2c (Stream B) one authorization brain.
 *
 * Replaces the inline `chart.client_id !== user.uid` check in the consult/consume
 * route and is the single per-chart authz gate routed through by every web + MCP
 * read path.
 *
 * Rules (in order):
 *   0. role 'inactive' (profile not active) → 'deny'
 *   1. super_admin, IF chart_id exists → 'all'
 *   2. principal.uid === charts.owner_id → 'all'
 *   3. chart_grants row matches (chartId, principal.uid) → 'view'
 *   4. else → 'deny' (also covers: chart_id does not exist, any role)
 *
 * 'view' grants Profile/Consult/Panchang read-only — Build/edit/delete reject.
 * Caller is responsible for mapping the returned Permission to HTTP status + UI.
 */

export type Principal = {
  uid: string
  /**
   * 'inactive' is NOT a privilege level: it marks a principal whose profile is not
   * active (disabled / pending / missing), as resolved by `resolveMcpPrincipalRole`.
   * It always yields 'deny' (Rule 0), whatever the chart.
   */
  role: 'guest' | 'super_admin' | 'inactive'
}

export type Permission = 'all' | 'view' | 'deny'

import type { QueryResultRow } from 'pg'

/**
 * Minimal DB surface this brain needs. Production passes the pg `query` from
 * `@/lib/db/client`; tests pass a mock. Keeping it structural avoids importing
 * `server-only` into the unit test path.
 */
export interface DbLike {
  query<T extends QueryResultRow = QueryResultRow>(
    sql: string,
    params?: unknown[]
  ): Promise<{ rows: T[] }>
}

export interface AuthorizeArgs {
  principal: Principal
  chartId: string
  db: DbLike
}

export async function authorizeChartAccess(
  args: AuthorizeArgs
): Promise<Permission> {
  const { principal, chartId, db } = args

  // Rule 0: an inactive principal gets nothing, and no DB read is spent on it.
  if (principal.role === 'inactive') return 'deny'

  // Rule 1: super_admin sees everything — but only for a chart_id that
  // actually exists. Defense-in-depth: without this check a super_admin
  // request for a bogus/deleted chart_id would get a silent 'all' grant
  // that only fails (or worse, doesn't fail) further downstream, instead
  // of the clean not-found every other role already gets via Rule 4.
  if (principal.role === 'super_admin') {
    const existsRes = await db.query<{ owner_id: string | null }>(
      'SELECT owner_id FROM charts WHERE id=$1',
      [chartId]
    )
    return existsRes.rows[0] ? 'all' : 'deny'
  }

  // Rule 2: owner_id match → full access.
  const ownerRes = await db.query<{ owner_id: string | null }>(
    'SELECT owner_id FROM charts WHERE id=$1',
    [chartId]
  )
  const ownerRow = ownerRes.rows[0]
  if (ownerRow && ownerRow.owner_id && ownerRow.owner_id === principal.uid) {
    return 'all'
  }

  // Rule 3: chart_grants → view-only.
  const grantRes = await db.query<{ permission: string }>(
    'SELECT permission FROM chart_grants WHERE chart_id=$1 AND principal_id=$2 LIMIT 1',
    [chartId, principal.uid]
  )
  if (grantRes.rows[0]) {
    // Today permission column is constrained to 'view'; tomorrow may widen.
    return grantRes.rows[0].permission === 'view' ? 'view' : 'deny'
  }

  // Rule 4: deny.
  return 'deny'
}

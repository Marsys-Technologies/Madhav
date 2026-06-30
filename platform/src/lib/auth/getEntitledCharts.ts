/**
 * getEntitledCharts — retrieve all charts a principal is entitled to see.
 *
 * Logic:
 *   - super_admin: returns ALL charts in the system
 *   - guest: returns charts where owner_id = uid UNION charts granted via chart_grants
 *
 * Returns an array of EntitledChart objects, sorted by display_name.
 * Used by M2 list_my_charts tool (via /api/mcp/my/charts).
 *
 * M1 identity entitlement (MCP elevation arc, 2026-07-01).
 */

import type { QueryResultRow } from 'pg'

export interface EntitledChart {
  id: string
  display_name: string
}

/**
 * Minimal DB surface. Production passes the pg `query` from `@/lib/db/client`;
 * tests pass a mock. Structural typing avoids importing `server-only` into test paths.
 */
export interface DbLike {
  query<T extends QueryResultRow = QueryResultRow>(
    sql: string,
    params?: unknown[]
  ): Promise<{ rows: T[] }>
}

/**
 * Retrieve entitled charts for the given principal.
 *
 * @param uid   The user's UID (from mcp_api_keys → profiles).
 * @param role  Resolved role: 'guest' | 'super_admin'.
 * @param db    DB accessor — never committed by this function.
 * @returns     Array of { id, display_name } sorted by display_name.
 */
export async function getEntitledCharts(
  uid: string,
  role: 'guest' | 'super_admin',
  db: DbLike
): Promise<EntitledChart[]> {
  let rows: Array<{ id: string; display_name: string }>

  if (role === 'super_admin') {
    // super_admin sees every chart
    const res = await db.query<{ id: string; display_name: string }>(
      `SELECT id, COALESCE(preferred_name, subject_name, name) AS display_name
       FROM charts
       ORDER BY COALESCE(preferred_name, subject_name, name)`
    )
    rows = res.rows
  } else {
    // guest: owned charts UNION granted charts (dedup by id)
    const res = await db.query<{ id: string; display_name: string }>(
      `SELECT DISTINCT c.id,
              COALESCE(c.preferred_name, c.subject_name, c.name) AS display_name
       FROM charts c
       WHERE c.owner_id = $1
       UNION
       SELECT DISTINCT c.id,
              COALESCE(c.preferred_name, c.subject_name, c.name) AS display_name
       FROM charts c
       JOIN chart_grants g ON g.chart_id = c.id
       WHERE g.principal_id = $1
       ORDER BY display_name`,
      [uid]
    )
    rows = res.rows
  }

  return rows.map((r) => ({ id: r.id, display_name: r.display_name }))
}

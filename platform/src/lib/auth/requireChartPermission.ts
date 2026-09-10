/**
 * requireChartPermission — the route-level adapter over `authorizeChartAccess`.
 *
 * `authorizeChartAccess` is the one authorization brain (see its own docstring for
 * the rule order). It is deliberately structural: it takes a `DbLike` so it can be
 * unit-tested without dragging `server-only` into the test path. That leaves every
 * API route repeating the same three things — read the caller's role, wrap
 * `@/lib/db/client`'s `query` into a `DbLike`, and map the resulting `Permission`
 * onto an HTTP status.
 *
 * P2-B-001 (GET /api/charts/[id]) and P2-B-007 (cockpit Clear preview+execute)
 * each open-coded that block. P2-B-008 had to add it to six more cockpit routes,
 * at which point eight hand-written copies of a security check is itself the risk:
 * one transcription slip (a `!==` for a `===`, a forgotten `super_admin` mapping,
 * a 200-instead-of-403) is a silent cross-tenant hole that no type error catches.
 * This helper is that block, written once.
 *
 * Two access levels, matching the distinction the Clear routes established:
 *
 *   'write' — requires `permission === 'all'` (owner or super_admin). Use for
 *             anything destructive or state-changing. A `chart_grants` 'view'
 *             grantee must NOT pass: a read grant is not a delete grant. This
 *             mirrors the Nirmāṇa page guard, which already gates the cockpit UI
 *             on `canBuild === (permission === 'all')`.
 *   'read'  — requires `permission !== 'deny'`. Use for read-only disclosure of
 *             chart-scoped data, which is exactly what a 'view' grant is for.
 *
 * Returns `null` when access is granted, or a ready-to-return 403 `NextResponse`
 * when it is not — so the call site reads:
 *
 *     const denied = await requireChartPermission({ uid, role, chartId, access: 'write' })
 *     if (denied) return denied
 *
 * Note the deliberate response shape: a bare `{ error: 'Forbidden', code:
 * 'FORBIDDEN_CHART' }` with no detail. A non-existent chart_id and an existent
 * one the caller cannot reach are reported identically, so the endpoint cannot be
 * used to enumerate which chart_ids exist.
 */
import { NextResponse } from 'next/server'
import type { QueryResultRow } from 'pg'
import { query } from '@/lib/db/client'
import { authorizeChartAccess, type DbLike, type Permission } from '@/lib/auth/authorizeChartAccess'

export type ChartAccessLevel = 'read' | 'write'

/**
 * The `DbLike` view onto the production pool. Kept as a module-level constant so
 * every caller shares one adapter rather than re-wrapping `query` per request.
 */
const db: DbLike = {
  async query<T extends QueryResultRow = QueryResultRow>(sql: string, params?: unknown[]) {
    const result = await query<T>(sql, params)
    return { rows: result.rows }
  },
}

/**
 * Reads the caller's platform role. Anything that is not exactly 'super_admin'
 * is treated as 'guest' — `authorizeChartAccess`'s `Principal` admits only those
 * two, and defaulting the unknown case DOWN (to the least privilege) is the only
 * safe direction.
 */
export async function getPrincipalRole(uid: string): Promise<'guest' | 'super_admin'> {
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [uid])
  return rows[0]?.role === 'super_admin' ? 'super_admin' : 'guest'
}

export interface RequireChartPermissionArgs {
  uid: string
  /**
   * Pass the already-resolved role when the route computed it for its own reasons
   * (several cockpit routes need `isSuperAdmin` for scope filtering anyway), to
   * avoid a duplicate `profiles` round-trip. Omit it and the helper reads it.
   */
  role?: 'guest' | 'super_admin'
  chartId: string
  access: ChartAccessLevel
}

/**
 * Resolves the caller's permission on `chartId` and returns a 403 response if the
 * requested access level is not met, or `null` if it is.
 */
export async function requireChartPermission(
  args: RequireChartPermissionArgs
): Promise<NextResponse | null> {
  const { uid, chartId, access } = args
  const role = args.role ?? (await getPrincipalRole(uid))

  const permission: Permission = await authorizeChartAccess({
    principal: { uid, role },
    chartId,
    db,
  })

  const ok = access === 'write' ? permission === 'all' : permission !== 'deny'
  if (ok) return null

  return NextResponse.json({ error: 'Forbidden', code: 'FORBIDDEN_CHART' }, { status: 403 })
}

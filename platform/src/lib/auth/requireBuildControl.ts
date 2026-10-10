/**
 * requireBuildControl — who may STOP or SKIP a build (SS N-373 / PR-S1, item 3).
 *
 * `POST /api/build/stop`, `/api/build/asset/stop` and `/api/build/asset/skip` used
 * to check only "is anyone logged in" and then wrote `stop_requested` /
 * `build_checkpoints` rows for ANY caller-supplied `build_id`: a guest could stop
 * or skip another tenant's build (SESSION_GATE_AUDIT MEDIUM).
 *
 * Rule: the caller must be the OWNER of the chart the build belongs to (write
 * access, `requireChartPermission(..., 'write')`: a read-only `chart_grants`
 * grantee does not pass), or a super_admin. The request carries only a
 * `build_id`, so the chart is resolved SERVER-SIDE from it — a client-supplied
 * `chart_id` would be attacker-chosen and is never trusted:
 *
 *   - `build_runs.id`            (current build model, uuid)
 *   - `build_events.build_id`    (legacy per-build event rows; text, carries chart_id)
 *
 * A build that resolves to NO chart (unknown id, decommissioned tables, or a DB
 * error while resolving) is not tied to a chart, so it is super_admin only. That
 * is deliberately fail-CLOSED: a non-admin is never allowed by a lookup failure.
 * A build that resolves to several charts needs write access on every one.
 *
 * Returns `null` when the caller may proceed, or a ready-to-return 403.
 */
import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { getPrincipalRole, requireChartPermission } from '@/lib/auth/requireChartPermission'

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

async function chartIdsFor(sql: string, buildId: string, source: string): Promise<string[]> {
  try {
    const { rows } = await query<{ chart_id: string | null }>(sql, [buildId])
    return rows.map((r) => r.chart_id).filter((c): c is string => typeof c === 'string' && c.length > 0)
  } catch (err) {
    // Missing table / transient error: this source resolves nothing. The caller
    // treats "no chart" as super_admin-only, so this can only DENY, never allow.
    console.error(`[requireBuildControl] ${source} lookup failed`, err)
    return []
  }
}

/** The distinct chart ids a build belongs to, from every source that knows. */
export async function resolveBuildChartIds(buildId: string): Promise<string[]> {
  const ids = new Set<string>()
  if (UUID_RE.test(buildId)) {
    for (const id of await chartIdsFor('SELECT chart_id FROM build_runs WHERE id = $1::uuid', buildId, 'build_runs')) ids.add(id)
  }
  for (const id of await chartIdsFor('SELECT DISTINCT chart_id FROM build_events WHERE build_id = $1', buildId, 'build_events')) ids.add(id)
  return [...ids]
}

export async function requireBuildControl(args: {
  uid: string
  buildId: string
}): Promise<NextResponse | null> {
  const { uid, buildId } = args
  const role = await getPrincipalRole(uid)
  if (role === 'super_admin') return null

  const chartIds = await resolveBuildChartIds(buildId)
  if (chartIds.length === 0) {
    return NextResponse.json({ error: 'Forbidden', code: 'FORBIDDEN_BUILD' }, { status: 403 })
  }
  for (const chartId of chartIds) {
    const denied = await requireChartPermission({ uid, role, chartId, access: 'write' })
    if (denied) return denied
  }
  return null
}

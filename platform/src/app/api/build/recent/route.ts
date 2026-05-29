/**
 * GET /api/build/recent
 *
 * Returns builds completed (status = 'complete' | 'failed') in the last 24 hours
 * that the user has not yet seen — for post-visit toast notifications.
 *
 * Behaviour:
 *   1. Auth: 401 if unauthenticated.
 *   2. Scope:
 *        - Regular user: builds where triggered_by_uid = user.uid
 *        - super_admin: ALL recent builds across all users
 *   3. Terminal statuses: 'complete' | 'failed'
 *   4. Window: finished_at (or failed_at) >= NOW() - INTERVAL '24 hours'
 *   5. Notification deduplication:
 *        - If notification_views table exists: exclude builds where a
 *          notification_views row (build_id, user_uid) already exists.
 *        - If notification_views table does NOT exist: return all
 *          completed/failed builds in the last 24 h (degrade gracefully).
 *   6. Joins charts for chart_name.
 *   7. Returns [] if none (not 404).
 *   8. Sorted by finished_at DESC.
 *   9. Cache-Control: no-store (notifications must be fresh).
 *
 * [BUILD-ORCH-D-04] /api/build/recent unseen completed builds.
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

// ─── Terminal statuses ────────────────────────────────────────────────────────

const TERMINAL_STATUSES = ['complete', 'failed'] as const
type TerminalStatus = (typeof TERMINAL_STATUSES)[number]

// ─── Response shape ───────────────────────────────────────────────────────────

interface RecentBuildItem {
  build_id: string
  chart_id: string
  chart_name: string | null
  status: TerminalStatus
  finished_at: string
  ayanamshas: string[]
  error_summary: string | null
}

// ─── DB row type ──────────────────────────────────────────────────────────────

interface BuildRow {
  build_id: string
  chart_id: string
  chart_name: string | null
  status: TerminalStatus
  finished_at: string
  ayanamshas: string[] | null
  error_summary: string | null
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Probe whether notification_views exists in the public schema.
 * Returns true if the table is present, false otherwise.
 */
async function notificationViewsExists(): Promise<boolean> {
  try {
    const result = await query<{ exists: boolean }>(
      `SELECT EXISTS (
         SELECT 1 FROM information_schema.tables
         WHERE table_schema = 'public'
           AND table_name   = 'notification_views'
       ) AS exists`,
      [],
    )
    return result.rows[0]?.exists === true
  } catch {
    return false
  }
}

// ─── Handler ──────────────────────────────────────────────────────────────────

export async function GET(_request: Request): Promise<Response> {
  // ── Auth ────────────────────────────────────────────────────────────────────
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  // ── Fetch user role ──────────────────────────────────────────────────────────
  const profileResult = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [user.uid],
  )
  const rawRole = profileResult.rows[0]?.role ?? ''
  const isSuperAdmin = rawRole === 'super_admin'

  // ── Check notification_views availability ────────────────────────────────────
  const hasNotificationViews = await notificationViewsExists()

  // ── Build query ──────────────────────────────────────────────────────────────
  // finished_at is set for 'complete' builds; failed_at is set for 'failed' builds.
  // We use COALESCE(finished_at, failed_at) as the canonical finish timestamp so
  // both terminal statuses are handled uniformly.

  const statusList = TERMINAL_STATUSES.join("','")

  // Notification-views exclusion clause (only when the table exists)
  const nvExclude = hasNotificationViews
    ? `AND NOT EXISTS (
         SELECT 1 FROM notification_views nv
         WHERE nv.build_id = b.build_id
           AND nv.user_uid = $${isSuperAdmin ? '1' : '2'}
       )`
    : ''

  // For super_admin the uid param appears only inside the NV clause (if any).
  // For regular users the uid param appears in the WHERE + optionally in NV clause.
  // We need consistent $N numbering:
  //   - guest, no NV:   params = [uid]   → $1 = uid
  //   - guest, NV:      params = [uid, uid] → $1 = uid (WHERE), $2 = uid (NV)
  //   - super_admin, no NV: params = []
  //   - super_admin, NV:    params = [uid]  → $1 = uid (NV)

  let sql: string
  let params: string[]

  if (isSuperAdmin) {
    sql = `
      SELECT
        b.build_id,
        b.chart_id,
        c.name                                          AS chart_name,
        b.status,
        COALESCE(b.finished_at, b.failed_at)::text      AS finished_at,
        b.ayanamshas,
        b.error_summary
      FROM builds b
      LEFT JOIN charts c ON c.chart_id = b.chart_id
      WHERE b.status IN ('${statusList}')
        AND COALESCE(b.finished_at, b.failed_at) >= NOW() - INTERVAL '24 hours'
        ${nvExclude}
      ORDER BY COALESCE(b.finished_at, b.failed_at) DESC
    `
    params = hasNotificationViews ? [user.uid] : []
  } else {
    sql = `
      SELECT
        b.build_id,
        b.chart_id,
        c.name                                          AS chart_name,
        b.status,
        COALESCE(b.finished_at, b.failed_at)::text      AS finished_at,
        b.ayanamshas,
        b.error_summary
      FROM builds b
      LEFT JOIN charts c ON c.chart_id = b.chart_id
      WHERE b.status IN ('${statusList}')
        AND b.triggered_by_uid = $1
        AND COALESCE(b.finished_at, b.failed_at) >= NOW() - INTERVAL '24 hours'
        ${hasNotificationViews ? nvExclude.replace('$2', '$2') : ''}
      ORDER BY COALESCE(b.finished_at, b.failed_at) DESC
    `
    params = hasNotificationViews ? [user.uid, user.uid] : [user.uid]
  }

  const result = await query<BuildRow>(sql, params)

  // ── Shape response ───────────────────────────────────────────────────────────
  const items: RecentBuildItem[] = result.rows.map((row) => ({
    build_id: row.build_id,
    chart_id: row.chart_id,
    chart_name: row.chart_name ?? null,
    status: row.status,
    finished_at: row.finished_at,
    ayanamshas: Array.isArray(row.ayanamshas) ? row.ayanamshas : [],
    error_summary: row.error_summary ?? null,
  }))

  return NextResponse.json(items, {
    status: 200,
    headers: {
      'Cache-Control': 'no-store',
    },
  })
}

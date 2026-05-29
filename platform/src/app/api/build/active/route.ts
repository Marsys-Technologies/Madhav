/**
 * GET /api/build/active
 *
 * Returns all in-progress builds for the authenticated user.
 *
 * Behaviour:
 *   1. Auth: 401 if unauthenticated.
 *   2. Scope:
 *        - Regular user: builds where triggered_by_uid = user.uid
 *        - super_admin: ALL active builds across all users
 *   3. Active statuses: 'queued' | 'running' | 'cancelling'
 *   4. For each build, computes steps_complete + steps_total from build_steps,
 *      derives progress_pct, and joins charts table for chart_name.
 *   5. Returns sorted by queued_at DESC.
 *   6. Returns empty array [] if no active builds (not 404).
 *   7. Cache-Control: max-age=5 (5-second browser/CDN cache).
 *
 * [BUILD-ORCH-D-03] /api/build/active in-progress builds list.
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

// ─── Active statuses ─────────────────────────────────────────────────────────

const ACTIVE_STATUSES = ['queued', 'running', 'cancelling'] as const
type ActiveStatus = (typeof ACTIVE_STATUSES)[number]

// ─── Response shape ──────────────────────────────────────────────────────────

interface ActiveBuildItem {
  build_id: string
  chart_id: string
  chart_name: string | null
  ayanamshas: string[]
  status: ActiveStatus
  queued_at: string
  started_at: string | null
  steps_complete: number
  steps_total: number
  progress_pct: number
}

// ─── DB row types ─────────────────────────────────────────────────────────────

interface BuildRow {
  build_id: string
  chart_id: string
  chart_name: string | null
  ayanamshas: string[] | null
  status: ActiveStatus
  queued_at: string
  started_at: string | null
  steps_complete: number | string
  steps_total: number | string
}

// ─── Handler ─────────────────────────────────────────────────────────────────

export async function GET(_request: Request): Promise<Response> {
  // ── Auth ───────────────────────────────────────────────────────────────────
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  // ── Fetch user role ────────────────────────────────────────────────────────
  const profileResult = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [user.uid],
  )
  const rawRole = profileResult.rows[0]?.role ?? ''
  const isSuperAdmin = rawRole === 'super_admin'

  // ── Query active builds ────────────────────────────────────────────────────
  // Join charts for chart_name; aggregate build_steps for progress.
  // Super admin sees ALL active builds; regular user sees only their own.
  const statusList = ACTIVE_STATUSES.join("','")

  const sql = isSuperAdmin
    ? `
        SELECT
          b.build_id,
          b.chart_id,
          c.name                                        AS chart_name,
          b.ayanamshas,
          b.status,
          b.queued_at,
          b.started_at,
          COUNT(bs.step_id) FILTER (WHERE bs.status = 'complete')  AS steps_complete,
          COUNT(bs.step_id)                                          AS steps_total
        FROM builds b
        LEFT JOIN charts c ON c.chart_id = b.chart_id
        LEFT JOIN build_steps bs ON bs.build_id = b.build_id
        WHERE b.status IN ('${statusList}')
        GROUP BY b.build_id, b.chart_id, c.name, b.ayanamshas, b.status, b.queued_at, b.started_at
        ORDER BY b.queued_at DESC
      `
    : `
        SELECT
          b.build_id,
          b.chart_id,
          c.name                                        AS chart_name,
          b.ayanamshas,
          b.status,
          b.queued_at,
          b.started_at,
          COUNT(bs.step_id) FILTER (WHERE bs.status = 'complete')  AS steps_complete,
          COUNT(bs.step_id)                                          AS steps_total
        FROM builds b
        LEFT JOIN charts c ON c.chart_id = b.chart_id
        LEFT JOIN build_steps bs ON bs.build_id = b.build_id
        WHERE b.status IN ('${statusList}')
          AND b.triggered_by_uid = $1
        GROUP BY b.build_id, b.chart_id, c.name, b.ayanamshas, b.status, b.queued_at, b.started_at
        ORDER BY b.queued_at DESC
      `

  const result = await query<BuildRow>(sql, isSuperAdmin ? [] : [user.uid])

  // ── Shape response ─────────────────────────────────────────────────────────
  const items: ActiveBuildItem[] = result.rows.map((row) => {
    const stepsComplete = Number(row.steps_complete) || 0
    const stepsTotal = Number(row.steps_total) || 0
    const progressPct = stepsTotal > 0 ? (stepsComplete / stepsTotal) * 100 : 0

    return {
      build_id: row.build_id,
      chart_id: row.chart_id,
      chart_name: row.chart_name ?? null,
      ayanamshas: Array.isArray(row.ayanamshas) ? row.ayanamshas : [],
      status: row.status,
      queued_at: row.queued_at,
      started_at: row.started_at ?? null,
      steps_complete: stepsComplete,
      steps_total: stepsTotal,
      progress_pct: progressPct,
    }
  })

  return NextResponse.json(items, {
    status: 200,
    headers: {
      'Cache-Control': 'max-age=5',
    },
  })
}

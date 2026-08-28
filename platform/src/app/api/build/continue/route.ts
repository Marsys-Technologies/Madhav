/**
 * POST /api/build/continue
 * Resumes the most recent build for the given chart_id.
 * [PHASE-C-07]
 */
import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { requireChartPermission } from '@/lib/auth/requireChartPermission'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const { chart_id } = await req.json().catch(() => ({}))
  if (!chart_id) return NextResponse.json({ error: 'chart_id required' }, { status: 400 })

  // V3-E-011: this route checked only "is anyone logged in" and then
  // trusted the caller-supplied chart_id — any authenticated user could
  // resume/continue another tenant's build and INSERT build_events rows
  // for it, a cross-tenant WRITE. Resuming a build is state-changing, so
  // 'write' (owner or super_admin only) is required — a chart_grants
  // 'view' grantee must not be able to trigger a build resume, matching
  // the B-008 precedent for the cockpit refresh/runs POST routes.
  const denied = await requireChartPermission({ uid: user.uid, chartId: chart_id, access: 'write' })
  if (denied) return denied

  // Get latest build
  const { rows } = await query<{ build_id: string }>(
    `SELECT id AS build_id FROM builds WHERE chart_id = $1 ORDER BY created_at DESC LIMIT 1`,
    [chart_id],
  )
  const build_id = rows[0]?.build_id
  if (!build_id) return NextResponse.json({ error: 'no prior build found' }, { status: 404 })

  await query(
    `INSERT INTO build_events (build_id, chart_id, event_type, payload, created_at)
     VALUES ($1, $2, 'resume_requested', '{}', NOW())`,
    [build_id, chart_id],
  )

  return NextResponse.json({ ok: true, build_id })
}

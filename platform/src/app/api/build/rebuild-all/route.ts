/**
 * POST /api/build/rebuild-all
 * Enqueues a full chart rebuild.
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

  // V3-E-010: this route used to check only "is there a logged-in user" and
  // then INSERT a build_events row for whatever chart_id the caller supplied —
  // a cross-tenant write. Same root cause as B-001/B-007/B-008. 'write' level
  // (permission === 'all'): triggering a full-chart rebuild is a state-changing
  // action, so a chart_grants 'view' grantee must not pass.
  const denied = await requireChartPermission({ uid: user.uid, chartId: chart_id, access: 'write' })
  if (denied) return denied

  const { rows } = await query<{ build_id: string }>(
    `INSERT INTO build_events (build_id, chart_id, event_type, payload, created_at)
     VALUES (gen_random_uuid(), $1, 'rebuild_all_requested', '{}', NOW())
     RETURNING build_id`,
    [chart_id],
  )

  return NextResponse.json({ ok: true, build_id: rows[0]?.build_id })
}

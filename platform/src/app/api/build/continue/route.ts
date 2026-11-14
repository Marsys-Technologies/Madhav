/**
 * Retired legacy POST interface. Current builds use the Cockpit run contract.
 * Keep session/input/write-permission refusals before disclosing retirement;
 * never translate a legacy build identity into a new run or dispatch a job.
 */
import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { requireChartPermission } from '@/lib/auth/requireChartPermission'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const { chart_id } = (await req.json().catch(() => ({}))) ?? {}
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

  return NextResponse.json(
    {
      error: 'Decommissioned. Use the current Cockpit controls and POST /api/cockpit/runs. Legacy build IDs cannot be resumed here.',
      code: 'ENDPOINT_GONE',
    },
    { status: 410 },
  )
}

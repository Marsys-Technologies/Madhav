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

  const body = await req.json().catch(() => null)
  const { asset_id, build_id, chart_id } = body ?? {}
  if (!asset_id || !build_id || !chart_id) {
    return NextResponse.json({ error: 'asset_id, build_id, chart_id required' }, { status: 400 })
  }

  // V3-E-010: this route used to check only "is there a logged-in user" and
  // then INSERT a build_events row for whatever chart_id the caller supplied —
  // a cross-tenant write. Same root cause as B-001/B-007/B-008. 'write' level
  // (permission === 'all'): triggering a single-asset rebuild is a
  // state-changing action, so a chart_grants 'view' grantee must not pass.
  const denied = await requireChartPermission({ uid: user.uid, chartId: chart_id, access: 'write' })
  if (denied) return denied

  return NextResponse.json(
    {
      error: 'Decommissioned. Use the current Cockpit controls and POST /api/cockpit/runs for a new asset-scoped run.',
      code: 'ENDPOINT_GONE',
    },
    { status: 410 },
  )
}

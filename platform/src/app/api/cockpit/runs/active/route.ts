import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { requireChartPermission } from '@/lib/auth/requireChartPermission'
import { readActiveBuildRun } from '@/lib/build/activeRunData'
import { getChartReadinessMap } from '@/lib/charts/readiness'

export const maxDuration = 8

export async function GET(req: NextRequest) {
  // Read-only endpoint — any authenticated user may poll the active run for
  // their own chart. super_admin gate removed (it made isBuilding always false
  // for non-super-admin users, breaking the build tracker entirely) — and
  // nothing was substituted, which left this route readable by ANY
  // authenticated user for ANY chart_id. V3-E-011: chart-level authz
  // restored via requireChartPermission (owner, super_admin, or a
  // chart_grants 'view' grantee), mirroring the already-merged sibling
  // GET /api/cockpit/runs.
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const chart_id = req.nextUrl.searchParams.get('chart_id')
  if (!chart_id) return NextResponse.json({ error: 'chart_id query param required' }, { status: 400 })

  const denied = await requireChartPermission({ uid: user.uid, chartId: chart_id, access: 'read' })
  if (denied) return denied

  try {
    const wantsPreparationStatus = req.nextUrl.searchParams.get('preparation') === 'true'
    const [data, readiness] = await Promise.all([
      readActiveBuildRun(chart_id),
      wantsPreparationStatus ? getChartReadinessMap([chart_id]) : null,
    ])
    return NextResponse.json({
      data,
      ...(readiness ? { preparation_incomplete: readiness.get(chart_id)?.preparationDataUnavailable === true } : {}),
    })
  } catch (err) {
    console.error('[cockpit/runs/active]', err)
    return NextResponse.json({ error: 'Run status is temporarily unavailable.' }, { status: 503 })
  }
}

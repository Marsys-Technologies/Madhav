/**
 * GET /api/build/data-readiness?chart_id=X
 *
 * Returns the build readiness state for a given chart.
 *
 * Algorithm:
 *   1. Find all known active data asset_ids from asset_registry (authoritative DAG)
 *   2. Find the latest build_id for the chart from build_events
 *   3. Find all build_checkpoints with status='success' for that build_id
 *   4. Classify assets as ready vs missing
 *
 * Response:
 *   {
 *     chart_id: string,
 *     build_status: 'none' | 'partial' | 'complete' | 'failed',
 *     ready: string[],       // asset_ids with status='success'
 *     missing: string[],     // asset_ids not yet built or failed
 *     partial_count: number,
 *     total_count: number
 *   }
 *
 * [PHASE-D-03] Data readiness API for consume-page banner + LLM context injection.
 */

import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { getDataReadiness } from '@/lib/build/dataReadiness'
import { requireChartPermission } from '@/lib/auth/requireChartPermission'

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest): Promise<Response> {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const chartId = req.nextUrl.searchParams.get('chart_id')
  if (!chartId) return NextResponse.json({ error: 'chart_id required' }, { status: 400 })

  // V3-E-011 finding 3: this route returned another tenant's build_status,
  // ready/missing asset lists to any authenticated user — a cross-tenant read
  // disclosure. `requireChartPermission` (read: owner, super_admin, or a
  // chart_grants 'view' grantee) gates this before any of the readiness data
  // below is queried.
  const denied = await requireChartPermission({ uid: user.uid, chartId, access: 'read' })
  if (denied) return denied

  const { readiness, hasBuild } = await getDataReadiness(chartId)
  if (!hasBuild) return NextResponse.json(readiness)

  return NextResponse.json(readiness, {
    headers: { 'Cache-Control': 'max-age=30' },
  })
}

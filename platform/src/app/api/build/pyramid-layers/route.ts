/**
 * GET /api/build/pyramid-layers
 *
 * Returns layer status derived from the pyramid table for a given chart_id.
 * Used by the LayerTower component and useChartBuildState hook.
 *
 * Query param: chart_id (required)
 *
 * Returns:
 *   { chart_id, layers: Layer[] }
 *   Layer: { layer, name, status, asset_count, assets: Asset[] }
 *   status: 'built' | 'building' | 'failed' | 'attention' | 'not-built'
 */

import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { readLegacyPyramidStatus } from '@/lib/build/legacyPyramidStatus'
import { requireChartPermission } from '@/lib/auth/requireChartPermission'

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest): Promise<NextResponse> {
  const chartId = req.nextUrl.searchParams.get('chart_id')
  if (!chartId) {
    return NextResponse.json({ error: 'chart_id required' }, { status: 400 })
  }

  const user = await getServerUser()
  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // V3-E-011 finding 4: this route returned another tenant's per-layer build
  // status to any authenticated user — a cross-tenant read disclosure. Gate
  // added immediately after the existing user check (order of the chart_id
  // presence check running before getServerUser() is preserved above).
  const denied = await requireChartPermission({ uid: user.uid, chartId, access: 'read' })
  if (denied) return denied

  const layers = await readLegacyPyramidStatus(chartId)

  return NextResponse.json({ chart_id: chartId, layers })
}

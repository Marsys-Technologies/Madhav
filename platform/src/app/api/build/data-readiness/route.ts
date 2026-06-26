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
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

interface DataReadinessResponse {
  chart_id: string
  build_status: 'none' | 'partial' | 'complete' | 'failed'
  ready: string[]
  missing: string[]
  partial_count: number
  total_count: number
}

export async function GET(req: NextRequest): Promise<Response> {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const chartId = req.nextUrl.searchParams.get('chart_id')
  if (!chartId) return NextResponse.json({ error: 'chart_id required' }, { status: 400 })

  // ── 1. Get all known active data asset_ids from asset_registry ──────────────
  // asset_registry.depends_on is the authoritative DAG source; build_dependencies
  // (A1..A22 scheme) is retired from this route.
  const depsResult = await query<{ asset_id: string }>(
    `SELECT asset_id FROM asset_registry
      WHERE is_active = true AND (asset_type IS NULL OR asset_type != 'service')
        AND (asset_kind IS NULL OR asset_kind != 'service')
      ORDER BY sort_order ASC`,
  )
  const assetList = depsResult.rows.map(r => r.asset_id).filter(Boolean)

  // ── 2. Find latest build_id for this chart ──────────────────────────────────
  const buildResult = await query<{ build_id: string }>(
    `SELECT build_id
       FROM build_events
      WHERE chart_id = $1
      ORDER BY emitted_at DESC
      LIMIT 1`,
    [chartId],
  )
  const buildId = buildResult.rows[0]?.build_id ?? null

  if (!buildId) {
    const response: DataReadinessResponse = {
      chart_id: chartId,
      build_status: 'none',
      ready: [],
      missing: assetList,
      partial_count: 0,
      total_count: assetList.length,
    }
    return NextResponse.json(response)
  }

  // ── 3. Get build_checkpoints status per asset ───────────────────────────────
  const checkpointsResult = await query<{ asset_id: string; status: string }>(
    `SELECT DISTINCT ON (asset_id) asset_id, status
       FROM build_checkpoints
      WHERE build_id = $1
      ORDER BY asset_id, completed_at DESC NULLS LAST`,
    [buildId],
  )
  const checkpointMap = new Map<string, string>()
  for (const row of checkpointsResult.rows) {
    checkpointMap.set(row.asset_id, row.status)
  }

  // ── 4. Classify ready vs missing ────────────────────────────────────────────
  const ready: string[] = []
  const missing: string[] = []

  for (const asset of assetList) {
    const status = checkpointMap.get(asset)
    if (status === 'success') {
      ready.push(asset)
    } else {
      missing.push(asset)
    }
  }

  // ── 5. Determine overall build_status ───────────────────────────────────────
  const hasFailed = [...checkpointMap.values()].some(s => s === 'failed')
  let buildStatus: DataReadinessResponse['build_status']
  if (ready.length === 0 && hasFailed) {
    buildStatus = 'failed'
  } else if (ready.length === assetList.length) {
    buildStatus = 'complete'
  } else if (ready.length > 0) {
    buildStatus = 'partial'
  } else {
    buildStatus = 'none'
  }

  const response: DataReadinessResponse = {
    chart_id: chartId,
    build_status: buildStatus,
    ready,
    missing,
    partial_count: ready.length,
    total_count: assetList.length,
  }

  return NextResponse.json(response, {
    headers: { 'Cache-Control': 'max-age=30' },
  })
}

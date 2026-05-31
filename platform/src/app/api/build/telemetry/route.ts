/**
 * GET /api/build/telemetry?build_id=<id>
 *
 * Returns telemetry aggregations for a given build to drive TelemetryStrip.
 * Reads from build_events to compute QPS, active writers, and queue depth.
 *
 * Response shape:
 *   { qps: number; active_writers: number; queue_depth: number;
 *     sidecar_healthy: boolean; build_id: string }
 *
 * Auth: requires authenticated user (401 if not).
 * Returns 200 with zeroed metrics if build_id not found (avoids 404 noise
 * during graph init before the first event arrives).
 *
 * [C-S6]
 */

import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

interface TelemetryRow {
  event_count: string
  unique_assets: string
}

export async function GET(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const buildId = req.nextUrl.searchParams.get('build_id')
  if (!buildId) {
    return NextResponse.json(
      { qps: 0, active_writers: 0, queue_depth: 0, sidecar_healthy: false, build_id: '' },
      { status: 200 },
    )
  }

  try {
    // Count events in the last 60s to estimate QPS
    const rows = await query<TelemetryRow>(
      `SELECT
         COUNT(*)                                         AS event_count,
         COUNT(DISTINCT COALESCE(asset_id, event_type))  AS unique_assets
       FROM build_events
       WHERE build_id = $1
         AND emitted_at > NOW() - INTERVAL '60 seconds'`,
      [buildId],
    )

    const row = rows.rows[0]
    const eventCount = parseInt(row?.event_count ?? '0', 10)
    const uniqueAssets = parseInt(row?.unique_assets ?? '0', 10)

    // Queue depth: pending build_steps for this build
    const pendingRows = await query<{ pending_count: string }>(
      `SELECT COUNT(*) AS pending_count
       FROM build_steps
       WHERE build_id = $1 AND status = 'pending'`,
      [buildId],
    )
    const queueDepth = parseInt(pendingRows.rows[0]?.pending_count ?? '0', 10)

    return NextResponse.json(
      {
        qps:            parseFloat((eventCount / 60).toFixed(2)),
        active_writers: uniqueAssets,
        queue_depth:    queueDepth,
        sidecar_healthy: eventCount > 0 || queueDepth > 0,
        build_id:       buildId,
      },
      {
        status: 200,
        headers: { 'Cache-Control': 'no-store' },
      },
    )
  } catch {
    // DB error — return graceful zeroed response; TelemetryStrip degrades safely
    return NextResponse.json(
      { qps: 0, active_writers: 0, queue_depth: 0, sidecar_healthy: false, build_id: buildId },
      { status: 200 },
    )
  }
}

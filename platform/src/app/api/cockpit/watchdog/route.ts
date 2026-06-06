/**
 * POST /api/cockpit/watchdog
 * Invoked by Cloud Scheduler every 5 min.
 * Marks orphan build_runs as failed and stuck asset_throughput rows as error.
 * Emits Pub/Sub events so connected cockpits update immediately.
 */
import { type NextRequest, NextResponse } from 'next/server'
import { query } from '@/lib/db/client'

async function publishEvent(event: Record<string, unknown>): Promise<void> {
  if (process.env.PUBSUB_DISABLED || !process.env.GOOGLE_CLOUD_PROJECT) return
  try {
    const { PubSub } = await import('@google-cloud/pubsub')
    const client = new PubSub({ projectId: process.env.GOOGLE_CLOUD_PROJECT })
    const topic = client.topic(process.env.PUBSUB_TOPIC ?? 'cockpit-events')
    await topic.publishMessage({
      data: Buffer.from(JSON.stringify(event)),
      attributes: {
        chart_id: String(event.chart_id ?? ''),
        type: String(event.type ?? ''),
      },
    })
  } catch (err) {
    console.error('[watchdog] publish failed:', (err as Error).message)
  }
}

export async function POST(req: NextRequest): Promise<NextResponse> {
  const authHeader = req.headers.get('x-watchdog-auth')
  if (!process.env.WATCHDOG_SECRET || authHeader !== process.env.WATCHDOG_SECRET) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  // 1. Orphan build_runs: running > 30 min with no recent asset progress
  const orphanRuns = await query<{ id: string; chart_id: string }>(
    `UPDATE build_runs
     SET state = 'failed', ended_at = NOW()
     WHERE state = 'running'
       AND started_at < NOW() - INTERVAL '30 minutes'
       AND NOT EXISTS (
         SELECT 1 FROM asset_throughput
         WHERE chart_id = build_runs.chart_id
           AND last_built_at > NOW() - INTERVAL '10 minutes'
       )
     RETURNING id, chart_id`
  )

  // 2. asset_throughput stuck building > 15 min
  const stuckAssets = await query<{ chart_id: string; asset_id: string }>(
    `UPDATE asset_throughput
     SET state = 'error',
         last_error = 'orphan-watchdog: writer never reported back'
     WHERE state = 'building'
       AND last_built_at < NOW() - INTERVAL '15 minutes'
     RETURNING chart_id, asset_id`
  )

  // 3. Emit events
  await Promise.allSettled([
    ...orphanRuns.rows.map(r =>
      publishEvent({ type: 'run.state_change', chart_id: r.chart_id, run_id: r.id, state: 'failed' })
    ),
    ...stuckAssets.rows.map(a =>
      publishEvent({ type: 'asset.state_change', chart_id: a.chart_id, asset_id: a.asset_id, to_state: 'error' })
    ),
  ])

  return NextResponse.json({
    orphan_runs_failed: orphanRuns.rowCount ?? 0,
    stuck_assets_failed: stuckAssets.rowCount ?? 0,
  })
}

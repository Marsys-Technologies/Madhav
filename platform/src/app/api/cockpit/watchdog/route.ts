/**
 * POST /api/cockpit/watchdog
 * Invoked by Cloud Scheduler every 5 min.
 * Marks orphan build_runs as failed and stuck asset_throughput rows as error.
 * Emits Pub/Sub events so connected cockpits update immediately.
 *
 * ── Reaper thresholds (Orchestrator Convergence Phase 1 — confirmed, do NOT loosen) ──
 * These thresholds protect against genuine hangs and MUST hold. A long-running heavy
 * asset (e.g. ga_dashas, ~40 min) is kept visibly alive NOT by relaxing the reaper but
 * by the Phase 3 per-sub-step heartbeat (each sub-step UPDATEs asset_throughput.last_built_at).
 * The heartbeat cadence must beat BOTH thresholds below:
 *   1. Orphan-run reaper: a build_runs row 'running' for > 30 min with NO asset_throughput
 *      row (for that chart) whose last_built_at advanced in the last 10 min → 'failed'.
 *      ⇒ Heartbeat must advance last_built_at at least every 10 min while a run is in flight.
 *   2. Stuck-asset reaper: an asset_throughput row 'building' whose last_built_at is
 *      older than 15 min → 'error'.
 *      ⇒ Heartbeat must advance last_built_at at least every 15 min while an asset is building.
 * Phase 3 emits a heartbeat per sub-step (35 sub-steps over ~40 min ⇒ ~1-2 min cadence),
 * which clears both with wide margin. No logic change here in Phase 1 — thresholds confirmed only.
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

export const maxDuration = 10

export async function POST(req: NextRequest): Promise<NextResponse> {
  // M-2: Warn explicitly when WATCHDOG_SECRET is unset so misconfiguration is visible in logs
  // rather than silently disabling the stuck-build reaper.
  if (!process.env.WATCHDOG_SECRET) {
    console.warn('[watchdog] WATCHDOG_SECRET is not set — watchdog endpoint is effectively disabled (all requests return 401). Set WATCHDOG_SECRET to enable the stuck-build reaper.')
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }
  const authHeader = req.headers.get('x-watchdog-auth')
  if (authHeader !== process.env.WATCHDOG_SECRET) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  try {
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

  // M-5: Also surface the orphan error in build_run_assets so the UI can show it instead
  // of a blank "Failed" state when bra.error was never written by the writer.
  await query(
    `UPDATE build_run_assets bra
     SET error = 'orphan-watchdog: writer never reported back'
     FROM build_runs br
     WHERE bra.run_id = br.id
       AND bra.state = 'running'
       AND br.state = 'running'
       AND br.started_at < NOW() - INTERVAL '30 minutes'
       AND bra.error IS NULL`
  )

  // 3. Orphan build_runs: planned > 10 min with started_at IS NULL (dispatch never happened)
  const undispatchedRuns = await query<{ id: string; chart_id: string }>(
    `UPDATE build_runs
     SET state = 'failed', ended_at = NOW(),
         last_error = 'orphan-watchdog: run never dispatched'
     WHERE state = 'planned'
       AND started_at IS NULL
       AND created_at < NOW() - INTERVAL '10 minutes'
     RETURNING id, chart_id`
  )
  // Also abort the queued assets so they don't sit in limbo
  if (undispatchedRuns.rows.length > 0) {
    const runIds = undispatchedRuns.rows.map(r => r.id)
    await query(
      `UPDATE build_run_assets SET state = 'aborted'
       WHERE run_id = ANY($1) AND state = 'queued'`,
      [runIds]
    )
  }

  // 4. Emit events
  await Promise.allSettled([
    ...orphanRuns.rows.map(r =>
      publishEvent({ type: 'run.state_change', chart_id: r.chart_id, run_id: r.id, state: 'failed' })
    ),
    ...stuckAssets.rows.map(a =>
      publishEvent({ type: 'asset.state_change', chart_id: a.chart_id, asset_id: a.asset_id, to_state: 'error' })
    ),
    ...undispatchedRuns.rows.map(r =>
      publishEvent({ type: 'run.state_change', chart_id: r.chart_id, run_id: r.id, state: 'failed' })
    ),
  ])

  // M-4: Prune old completed/failed/stopped build runs and their child assets (retention: 90 days)
  // Delete build_run_assets first in case there is no CASCADE FK.
  await query(
    `DELETE FROM build_run_assets
     WHERE run_id IN (
       SELECT id FROM build_runs
       WHERE state IN ('completed', 'failed', 'stopped')
         AND created_at < NOW() - INTERVAL '90 days'
     )`
  )
  const pruned = await query(
    `DELETE FROM build_runs
     WHERE state IN ('completed', 'failed', 'stopped')
       AND created_at < NOW() - INTERVAL '90 days'
     RETURNING id`
  )

  return NextResponse.json({
    orphan_runs_failed: orphanRuns.rowCount ?? 0,
    stuck_assets_failed: stuckAssets.rowCount ?? 0,
    undispatched_runs_failed: undispatchedRuns.rowCount ?? 0,
    pruned_runs: pruned.rowCount ?? 0,
  })
  } catch (err) {
    console.error('[cockpit/watchdog]', err)
    return NextResponse.json({ error: 'db error' }, { status: 500 })
  }
}

/**
 * POST /api/cockpit/watchdog
 * Invoked by Cloud Scheduler every 5 min.
 * Marks orphan build_runs as failed and stuck asset_throughput rows as error.
 * Emits Pub/Sub events so connected cockpits update immediately.
 *
 * RR-fix (D-3) Part B: a heartbeat timeout alone is NOT proof of failure. Before
 * the stuck-asset reaper below marks a 'building' row 'error', it probes the
 * asset's actual data via asset_registry.count_sql — a slow-but-succeeding write
 * (data landed, state-flip write itself raced a crash/connection drop) is rescued
 * to 'lit' instead of blind-failed. See the stuck-asset block for detail.
 *
 * SAMĀPTI B-WATCHDOG-LIT (DVA Ruling 10, finding F3): that rescue is now gated on
 * the asset having NO substep plan. A has_substeps=true writer commits data per
 * substep, so rows exist after substep 1 of N — rows-present alone would promote a
 * 78/303-complete asset to 'lit' the moment its heartbeat went stale. This route
 * cannot prove plan completeness (no access to the Python writers' plan_substeps,
 * and no persisted plan total anywhere), so for those assets it withholds the
 * promotion and records 'incomplete' instead. See the stuck-asset block.
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
import { classifyStuckCandidate } from './classifyStuckCandidate'

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

  // 2. asset_throughput stuck building > 15 min — RR-fix (D-3) Part B: before
  //    blindly marking these as errored, probe each candidate's actual data via
  //    asset_registry.count_sql, mirroring the orchestrator's data-presence-probe
  //    pattern (_data_rows_present / _guard_state_write, commit b13640d1,
  //    platform/python-sidecar/pipeline/orchestrator/asset_runner.py). A writer
  //    whose data fully landed but whose own state-flip write raced a connection
  //    drop / crash (last_built_at goes stale even though the work is done) must
  //    not be misreported as a failure — a slow-but-succeeding write is not a
  //    stuck write.
  //
  //    ── SAMĀPTI B-WATCHDOG-LIT (DVA Ruling 10, F3) ────────────────────────────
  //    Rows-present is NECESSARY BUT NOT SUFFICIENT for a multi-substep writer.
  //    A writer with a real substep plan (asset_registry.has_substeps = true)
  //    commits data incrementally — one commit per substep (see asset_runner.py
  //    `_drive_substeps`). Rows therefore exist after substep 1 of N. The probe
  //    above cannot tell 78/303-done from 303/303-done, so before this fix ANY
  //    stale heartbeat on a heavy writer promoted it straight to 'lit' at
  //    whatever partial state it happened to be in — falsely unblocking every
  //    downstream dependant on a half-built asset. That is the same "unearned
  //    lit" defect class the Python path already closed (SATYA-DĪPA,
  //    asset_runner.py:596-630 + migration 474's 'incomplete' state); this route
  //    implemented only the rows-present half of that pattern and omitted the
  //    plan-completeness half.
  //
  //    The Python path proves completeness by re-invoking the writer's own
  //    `plan_substeps(ctx)` and requiring it to return zero remaining substeps.
  //    THIS ROUTE CANNOT DO THAT: it is an out-of-band TypeScript reaper with no
  //    access to the Python writers, and the plan's total size is never persisted
  //    anywhere — `build_substep_progress` records only which substeps DID commit
  //    (migration 436), and `_drive_substeps`'s `total = len(substeps)` lives only
  //    in-process and in a transient SSE event. Inferring a total would be a
  //    fabricated computation (CLAUDE.md §B.10).
  //
  //    So the honest rule, and the strictly-more-conservative one, is:
  //      * has_substeps = false/NULL  → no plan to complete; retain today's
  //        rows-present rescue exactly as-is (light writers stay rescuable).
  //      * has_substeps = true        → completeness is UNPROVEN from here, and
  //        unproven is not proven. Never promote to 'lit'. If data is present,
  //        record the honest 'incomplete' state (migration 474: "ran, some data
  //        present, plan work may remain" — deliberately NOT in the
  //        ('lit','service_ok') dependency-satisfied allowlist, so downstream
  //        stays correctly blocked). If no data is present, it falls through to
  //        the unchanged 'error' path below.
  //    This can only ever promote FEWER assets than before, never more.
  //
  //    The committed-substep count is read (read-only) purely as evidence for the
  //    log line and the emitted event — it is never used to synthesise a total.
  const stuckCandidates = await query<{
    chart_id: string | null
    asset_id: string
    count_sql: string | null
    target_floor: number | null
    has_substeps: boolean | null
    substeps_committed: number | null
  }>(
    `SELECT at.chart_id, at.asset_id, ar.count_sql, ar.target_floor, ar.has_substeps,
            (SELECT COUNT(*) FROM build_substep_progress bsp
              WHERE bsp.chart_id = at.chart_id
                AND bsp.asset_id = at.asset_id)::int AS substeps_committed
     FROM asset_throughput at
     JOIN asset_registry ar ON ar.asset_id = at.asset_id
     WHERE at.state = 'building'
       AND at.last_built_at < NOW() - INTERVAL '15 minutes'`
  )

  const rescued: { chart_id: string | null; asset_id: string; rows: number }[] = []
  const trulyStuck: { chart_id: string | null; asset_id: string }[] = []
  // has_substeps assets with data present but unprovable plan completeness.
  const withheld: {
    chart_id: string | null
    asset_id: string
    rows: number
    substepsCommitted: number
  }[] = []

  for (const c of stuckCandidates.rows) {
    let actualRows: number | null = null
    if (c.count_sql) {
      try {
        const countParams = /\$1/.test(c.count_sql) ? [c.chart_id] : []
        const r = await query<{ count: string }>(c.count_sql, countParams)
        actualRows = parseInt(r.rows[0]?.count ?? '0', 10)
      } catch (err) {
        console.error(
          `[watchdog] presence probe failed for ${c.asset_id} (chart ${c.chart_id ?? 'NULL'}):`,
          (err as Error).message
        )
        actualRows = null
      }
    }
    switch (classifyStuckCandidate(c, actualRows)) {
      case 'error':
        trulyStuck.push({ chart_id: c.chart_id, asset_id: c.asset_id })
        break
      case 'withhold-incomplete':
        withheld.push({
          chart_id: c.chart_id,
          asset_id: c.asset_id,
          rows: actualRows ?? 0,
          substepsCommitted: c.substeps_committed ?? 0,
        })
        break
      case 'rescue-lit':
        rescued.push({ chart_id: c.chart_id, asset_id: c.asset_id, rows: actualRows ?? 0 })
        break
    }
  }

  for (const r of rescued) {
    await query(
      `UPDATE asset_throughput
       SET state = 'lit', rows_written = $3, last_error = NULL, last_built_at = NOW()
       WHERE chart_id IS NOT DISTINCT FROM $1 AND asset_id = $2 AND state = 'building'`,
      [r.chart_id, r.asset_id, r.rows]
    )
    await query(
      `UPDATE build_run_assets bra
       SET state = 'complete', ended_at = NOW()
       FROM build_runs br
       WHERE bra.run_id = br.id
         AND br.chart_id IS NOT DISTINCT FROM $1
         AND bra.asset_id = $2
         AND bra.state = 'building'`,
      [r.chart_id, r.asset_id]
    )
    console.warn(
      `[watchdog] RESCUED stuck asset ${r.asset_id} (chart ${r.chart_id ?? 'NULL'}): ` +
      `${r.rows} row(s) confirmed present via count_sql — marked 'lit' instead of blind-failing ` +
      `a heartbeat timeout with no data-presence check.`
    )
    await publishEvent({
      type: 'asset.state_change',
      chart_id: r.chart_id,
      asset_id: r.asset_id,
      to_state: 'lit',
      watchdog_rescue: true,
    })
  }

  // SAMĀPTI B-WATCHDOG-LIT: withheld promotions → 'incomplete'.
  //
  // Deliberately mirrors the 'error' path below, NOT the rescue path above: the
  // asset_throughput row is restated and `last_error` explains why, but
  // build_run_assets.state is left untouched. Flipping it to 'complete' (as the
  // rescue path does) would be exactly the false completion claim this fix
  // exists to prevent.
  //
  // `last_error` is set rather than left NULL on purpose. It is the field the
  // cockpit's existing badge-honesty path keys on: deriveState() downgrades a
  // has_substeps asset with committed substeps to the 'partial' badge when an
  // error string is present, whereas a NULL error with rows present would render
  // a 'lit' badge from count_sql — re-introducing the falsely-lit report at the
  // UI layer even though the stored state is honest.
  for (const w of withheld) {
    await query(
      `UPDATE asset_throughput
       SET state = 'incomplete', rows_written = $3, last_built_at = NOW(),
           last_error = $4
       WHERE chart_id IS NOT DISTINCT FROM $1 AND asset_id = $2 AND state = 'building'`,
      [
        w.chart_id,
        w.asset_id,
        w.rows,
        'orphan-watchdog: heartbeat went stale while a substep plan was in flight. ' +
          `${w.substepsCommitted} substep(s) committed and ${w.rows} data row(s) are present, ` +
          'but this route cannot prove the plan finished, so the asset was NOT promoted to ' +
          "'lit'. Re-run the build to complete the plan (substep progress is resumable).",
      ]
    )
    console.warn(
      `[watchdog] WITHHELD promotion for ${w.asset_id} (chart ${w.chart_id ?? 'NULL'}): ` +
      `${w.rows} row(s) present and ${w.substepsCommitted} substep(s) committed, but ` +
      `has_substeps=true and substep-plan completeness is not provable from this route — ` +
      `marked 'incomplete', NOT 'lit'. Downstream dependants stay blocked until a rebuild ` +
      `actually finishes the plan.`
    )
    await publishEvent({
      type: 'asset.state_change',
      chart_id: w.chart_id,
      asset_id: w.asset_id,
      to_state: 'incomplete',
      watchdog_promotion_withheld: true,
      substeps_committed: w.substepsCommitted,
      rows_present: w.rows,
    })
  }

  const stuckAssets =
    trulyStuck.length > 0
      ? await query<{ chart_id: string; asset_id: string }>(
          `UPDATE asset_throughput
           SET state = 'error',
               last_error = 'orphan-watchdog: writer never reported back'
           WHERE state = 'building'
             AND last_built_at < NOW() - INTERVAL '15 minutes'
             AND (${trulyStuck.map((_, i) => `(chart_id IS NOT DISTINCT FROM $${i * 2 + 1} AND asset_id = $${i * 2 + 2})`).join(' OR ')})
           RETURNING chart_id, asset_id`,
          trulyStuck.flatMap((c) => [c.chart_id, c.asset_id])
        )
      : { rows: [] as { chart_id: string; asset_id: string }[], rowCount: 0 }

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
    stuck_assets_rescued: rescued.length,
    // SAMĀPTI B-WATCHDOG-LIT: has_substeps assets with data present whose plan
    // completeness could not be proven — marked 'incomplete' instead of 'lit'.
    stuck_assets_withheld_incomplete: withheld.length,
    stuck_assets_failed: stuckAssets.rowCount ?? 0,
    undispatched_runs_failed: undispatchedRuns.rowCount ?? 0,
    pruned_runs: pruned.rowCount ?? 0,
  })
  } catch (err) {
    console.error('[cockpit/watchdog]', err)
    return NextResponse.json({ error: 'db error' }, { status: 500 })
  }
}

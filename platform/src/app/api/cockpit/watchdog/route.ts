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
 * ── Reaper thresholds (Orchestrator Convergence Phase 1 — confirmed; REVISED post-incident) ──
 * These thresholds protect against genuine hangs and MUST hold. A long-running heavy
 * asset (e.g. ga_dashas, ~40 min) is kept visibly alive NOT by relaxing the reaper but
 * by the Phase 3 per-sub-step heartbeat (each sub-step UPDATEs asset_throughput.last_built_at).
 * The heartbeat cadence must beat BOTH thresholds below:
 *   1. Orphan-run reaper: a build_runs row 'running' for > 30 min with NO asset_throughput
 *      row (for that chart) whose last_built_at advanced in the last 15 min, AND NO
 *      build_substep_progress row (for that chart) whose completed_at advanced in the last
 *      15 min → 'failed'.
 *      ⇒ Heartbeat must advance last_built_at (or commit a substep) at least every 15 min
 *        while a run is in flight.
 *   2. Stuck-asset reaper: an asset_throughput row 'building' whose last_built_at is
 *      older than 15 min → 'error'.
 *      ⇒ Heartbeat must advance last_built_at at least every 15 min while an asset is building.
 *
 * INCIDENT (2026-07-31/08-01, ka_gochara_sweep chart 1c826d5a, run e5cde4dc): clause 1's
 * original 10-min window (and its reliance on asset_throughput alone) false-killed a run
 * whose Cloud Run container was ALIVE and progressing — build_substep_progress showed
 * substeps landing every ~5-6.5 min (worst case ~7 min for this writer), leaving only a
 * thin margin against a 10-min window. Root-cause read (systematic-debugging pass over
 * platform/python-sidecar/pipeline/orchestrator/asset_runner.py, the heartbeat write path):
 * the "client-stamped naive utcnow() vs DB clock" hypothesis is RULED OUT — every
 * last_built_at / build_substep_progress.completed_at write already uses DB-side NOW(),
 * not a Python-side timestamp (asset_runner.py `_drive_substeps` heartbeat UPDATE;
 * services/ka_gochara_sweep/writer.py `_record_substep` INSERT). The genuinely
 * contributing factor is a PostgreSQL semantic, not a client-clock bug: NOW()/
 * CURRENT_TIMESTAMP returns the START time of the CURRENT TRANSACTION, not the actual
 * wall-clock moment of the statement — and each heavy-writer substep runs as ONE
 * multi-minute transaction (SAVEPOINT open → run_substep() compute → commit), so a
 * substep's own heartbeat stamp can silently understate its true commit time by up to
 * that substep's own duration. That structurally eats into the reaper's grace window
 * before the reaper even starts counting, on top of ordinary jitter (a slow substep, a
 * DB round-trip stall). Fix here is additive and does not touch the FROZEN orchestrator
 * or writer code (out of this lane's scope; flagged as a follow-up candidate): widen the
 * window to 15 min (comfortably above the ~7 min worst-case substep cadence) AND treat a
 * recent build_substep_progress row for the chart as independent, corroborating evidence
 * of life — a truly dead run has NEITHER signal, so the genuine-hang case is unchanged.
 * build_substep_progress is READ-ONLY from this route; its data is never written or
 * deleted here.
 */
import { type NextRequest, NextResponse } from 'next/server'
import { verifyOidcToken } from '@/lib/auth/oidc'
import { query } from '@/lib/db/client'
import { classifyStuckCandidate } from './classifyStuckCandidate'

// Packet A2 ("Always record why it failed") — named, attributable messages shared
// between the build_runs.last_error write and the companion build_run_assets.error
// write, so both tables record the SAME text instead of one of them staying blank.
// Exported for tests that assert the propagated text without duplicating the literal.
export const ORPHAN_RUN_MESSAGE =
  'orphan-watchdog: run orphaned — no asset_throughput heartbeat or build_substep_progress ' +
  'commit in the last 15 minutes on a run running 30+ minutes'
export const STUCK_ASSET_MESSAGE = 'orphan-watchdog: writer never reported back'
export const UNDISPATCHED_RUN_MESSAGE = 'orphan-watchdog: run never dispatched'

const WATCHDOG_OIDC_AUDIENCE = process.env.WATCHDOG_SCHEDULER_OIDC_AUDIENCE
  ?? 'https://amjis-web-938361928218.asia-south1.run.app'
const WATCHDOG_SCHEDULER_SERVICE_ACCOUNT = process.env.WATCHDOG_SCHEDULER_SERVICE_ACCOUNT
  ?? 'amjis-scheduler@madhav-astrology.iam.gserviceaccount.com'

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
  const authorization = req.headers.get('authorization')
  let authorized = false
  if (authorization?.startsWith('Bearer ')) {
    try {
      authorized = Boolean(await verifyOidcToken(authorization.slice('Bearer '.length), {
        expectedAudience: WATCHDOG_OIDC_AUDIENCE,
        expectedServiceAccount: WATCHDOG_SCHEDULER_SERVICE_ACCOUNT,
      }))
    } catch {
      authorized = false
    }
  }
  if (!authorized) {
    const hadCredential = Boolean(authorization || req.headers.get('x-watchdog-auth'))
    return NextResponse.json(
      { error: hadCredential ? 'forbidden' : 'Unauthorized' },
      { status: hadCredential ? 403 : 401 },
    )
  }

  try {
  // 1. Orphan build_runs: running > 30 min with no recent asset progress.
  //    Two independent "still alive" signals are checked (either is sufficient to
  //    spare the run): asset_throughput.last_built_at (the per-substep heartbeat) AND
  //    build_substep_progress.completed_at (the substep-commit ledger, migration 436 —
  //    read-only here; never written or deleted by this route). See the file-header
  //    incident note above for why a single 10-min asset_throughput-only check false-
  //    killed a genuinely progressing heavy writer. Window widened 10min -> 15min to
  //    comfortably clear the slowest known substep cadence (ka_gochara_sweep, ~7 min
  //    worst case) with margin.
  // Packet A2: this reaper used to write build_runs.last_error = NULL (no clause
  // at all) and never touched build_run_assets, leaving that run's still-'queued'
  // or still-'building' asset rows silently stranded with no error text forever.
  // Now writes the SAME attributable message to build_runs.last_error AND
  // terminalizes the run's non-terminal build_run_assets rows in the one
  // statement — 'building' rows (a writer was mid-flight when the run itself was
  // judged dead) -> 'error'; 'queued' rows (never got a chance) -> 'aborted'.
  // Mirrors the reference CTE shape (_terminalize_preflight_failure,
  // platform/python-sidecar/pipeline/orchestrator/runner.py:325-337), extended to
  // two target states since this reaper can find a run in either shape.
  const orphanRuns = await query<{ id: string; chart_id: string }>(
    `WITH failed_run AS (
       UPDATE build_runs
       SET state = 'failed', ended_at = NOW(), last_error = $1
       WHERE state = 'running'
         AND started_at < NOW() - INTERVAL '30 minutes'
         AND NOT EXISTS (
           SELECT 1 FROM asset_throughput
           WHERE chart_id = build_runs.chart_id
             AND last_built_at > NOW() - INTERVAL '15 minutes'
         )
         AND NOT EXISTS (
           SELECT 1 FROM build_substep_progress
           WHERE chart_id = build_runs.chart_id
             AND completed_at > NOW() - INTERVAL '15 minutes'
         )
       RETURNING id, chart_id
     ),
     aborted_queued AS (
       UPDATE build_run_assets
       SET state = 'aborted', ended_at = NOW(), error = $1
       WHERE run_id IN (SELECT id FROM failed_run)
         AND state = 'queued'
       RETURNING 1
     ),
     errored_building AS (
       UPDATE build_run_assets
       SET state = 'error', ended_at = NOW(), error = $1
       WHERE run_id IN (SELECT id FROM failed_run)
         AND state = 'building'
       RETURNING 1
     )
     SELECT id, chart_id FROM failed_run`,
    [ORPHAN_RUN_MESSAGE]
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

  // Packet A2: this reaper used to write asset_throughput.last_error but never
  // touched build_run_assets for the same (chart_id, asset_id) — the row the
  // cockpit's run view actually reads stayed 'building' with error=NULL forever.
  // Now both tables get the SAME text in one
  // statement: the `stuck` CTE does the asset_throughput write exactly as before
  // (unchanged shape/params, still returns chart_id/asset_id for the caller), and
  // a second CTE joins through build_runs (chart_id -> its one active run, per
  // the build_runs_one_active_per_chart_idx UNIQUE constraint) to terminalize the
  // matching build_run_assets row from 'building' to 'error' with the same text.
  const stuckAssets =
    trulyStuck.length > 0
      ? await query<{ chart_id: string; asset_id: string }>(
          `WITH stuck AS (
             UPDATE asset_throughput
             SET state = 'error',
                 last_error = $1
             WHERE state = 'building'
               AND last_built_at < NOW() - INTERVAL '15 minutes'
               AND (${trulyStuck.map((_, i) => `(chart_id IS NOT DISTINCT FROM $${i * 2 + 2} AND asset_id = $${i * 2 + 3})`).join(' OR ')})
             RETURNING chart_id, asset_id
           ),
           bra_terminalized AS (
             UPDATE build_run_assets bra
             SET state = 'error', ended_at = NOW(), error = $1
             FROM build_runs br
             WHERE bra.run_id = br.id
               AND br.state = 'running'
               AND bra.state = 'building'
               AND EXISTS (
                 SELECT 1 FROM stuck s
                 WHERE br.chart_id IS NOT DISTINCT FROM s.chart_id
                   AND bra.asset_id = s.asset_id
               )
             RETURNING 1
           )
           SELECT chart_id, asset_id FROM stuck`,
          [STUCK_ASSET_MESSAGE, ...trulyStuck.flatMap((c) => [c.chart_id, c.asset_id])]
        )
      : { rows: [] as { chart_id: string; asset_id: string }[], rowCount: 0 }

  // M-5 REMOVED (packet A2 correction pass, post independent gate review,
  // 00_ARCHITECTURE/briefs/nirmana/engine/reviews/A2_review_20260926T123936Z.md
  // §C1). The block that lived here corrected M-5's illegal `bra.state =
  // 'running'` predicate to the legal `'building'`, but that repair resurrected
  // logic whose ONLY time predicate was the age of the *run* (`br.started_at <
  // NOW() - INTERVAL '30 minutes'`) — it never checked staleness on the *asset*.
  // Any build running longer than 30 minutes would have its currently-building
  // asset stamped "writer never reported back" while that writer's heartbeat
  // was completely healthy, and neither `mark_asset_complete` nor the
  // 'building' transition clears `error` afterward, so the false stamp would
  // have survived into a 'complete' row and been served by
  // /api/cockpit/runs/[id]/assets next to a live, progressing asset. Site 2
  // (the `stuckAssets` block immediately above) already covers M-5's genuine
  // cohort directly, with a real staleness gate on the asset itself
  // (`asset_throughput.last_built_at < NOW() - INTERVAL '15 minutes'`, via
  // classifyStuckCandidate) and a real state transition — M-5 never had either.
  // Deleting it removes nothing the engine ever actually had: its predicate was
  // an illegal enum value for its entire life, so it never fired. A *correct*
  // version needs a real asset-level heartbeat-age detector rather than a
  // run-age proxy; that is new behaviour, carried to packet C2 ("stuck
  // states") for its own before/after measurement rather than smuggled in here.

  // 3. Orphan build_runs: planned > 10 min with started_at IS NULL (dispatch never happened)
  //
  // Packet A2 — THE dominant defect: 295 of 301 (98%) of all empty-error
  // build_run_assets records traced to this exact code path. The text
  // ('orphan-watchdog: run never dispatched') was already computed and written
  // to build_runs.last_error one statement above; the separate abort UPDATE
  // simply never had an `error` clause in its SET list. Combined into one CTE
  // (mirrors _terminalize_preflight_failure,
  // platform/python-sidecar/pipeline/orchestrator/runner.py:325-337) so the same
  // parameter reaches both tables atomically and the old two-statement,
  // conditional-on-rows.length dance is no longer needed.
  const undispatchedRuns = await query<{ id: string; chart_id: string }>(
    `WITH failed_run AS (
       UPDATE build_runs
       SET state = 'failed', ended_at = NOW(), last_error = $1
       WHERE state = 'planned'
         AND started_at IS NULL
         AND created_at < NOW() - INTERVAL '10 minutes'
       RETURNING id, chart_id
     ),
     aborted_queued AS (
       UPDATE build_run_assets
       SET state = 'aborted', ended_at = NOW(), error = $1
       WHERE run_id IN (SELECT id FROM failed_run)
         AND state = 'queued'
       RETURNING 1
     )
     SELECT id, chart_id FROM failed_run`,
    [UNDISPATCHED_RUN_MESSAGE]
  )

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

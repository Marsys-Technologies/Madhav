/**
 * recalibrationEnqueue.ts — debounced, targeted LEL recalibration enqueue.
 *
 * When a new life event is saved, the calibration surfaces that depend on the
 * chart's LEL corpus become stale. Rather than a full rebuild, we enqueue a
 * TARGETED `scope='asset_set'` run over just the LEL-dependent assets for THAT
 * chart. This reuses the exact build_runs + build_run_assets INSERT shape and
 * `resolveBuildPlan` used by POST /api/cockpit/runs (no duplicated planning),
 * invoked as an internal server-side function rather than an HTTP round-trip.
 *
 * DEBOUNCE (two guards, both coalesce silently — never an error to the caller):
 *
 *   1. Quiet-window. LEL saves arrive in bursts. We read the window seconds from
 *      brahma_formula_constants `mimamsa_recalibration_debounce_seconds`
 *      (seeded {"seconds":600} by migration 424). We track the last recalibration
 *      via the most recent asset_set recalibration `build_runs.created_at` for the
 *      chart (a "last-recalibration marker" — simplest correct approach: it is a
 *      leading-edge debounce that cannot starve, unlike keying off the last
 *      life_events.recorded_at which every burst-save would re-trip). If a
 *      recalibration ran within the window → coalesce.
 *
 *   2. RUN_ACTIVE. If any run is already active/pending for the chart (mirrors
 *      the runs-route Gate 0 409), we treat it as "already queued" and coalesce.
 *
 *   `force` bypasses guard 1 (quiet-window) but STILL respects guard 2
 *   (RUN_ACTIVE) — an explicit "recalibrate now" cannot double-run a chart.
 *
 * @module build/recalibrationEnqueue
 */

import 'server-only'
import { query } from '@/lib/db/client'
import {
  resolveBuildPlan,
  type RegistryEntry,
  type ThroughputEntry,
  type AssetId,
} from './plan'
import { invokeRunJob } from './jobInvoker'

/**
 * The assets that consume a chart's LEL corpus / calibration state. A new life
 * event invalidates exactly these (L5 jivanaghatana + its pramana, L4
 * rectification + its pramana). Kept as a documented constant so the debounce
 * target and the recalibration-run signature stay in one place.
 */
export const LEL_DEPENDENT_ASSETS = [
  'mi_jivanaghatana',
  'mi_pramana',
  'ph_rectification',
  'ph_pramana',
] as const

/** Comma-separated scope_target for the asset_set recalibration run. */
export const LEL_RECAL_SCOPE_TARGET = LEL_DEPENDENT_ASSETS.join(',')

const RECAL_SCOPE = 'asset_set' as const
const RECAL_ACTION = 'rebuild' as const
const DEFAULT_DEBOUNCE_SECONDS = 600
const RECAL_TRIGGERED_BY = 'lel_intake-api'

export interface EnqueueRecalibrationArgs {
  chartId: string
  /** uid stamped into build_runs.triggered_by. */
  triggeredBy?: string
  /** Bypass the quiet-window guard (still respects RUN_ACTIVE). */
  force?: boolean
}

export type EnqueueRecalibrationResult =
  | { enqueued: true; run_id: string; plan: AssetId[] }
  | {
      enqueued: false
      reason: 'debounced' | 'run_active' | 'nothing_to_build'
      existing_run_id?: string
      debounce_seconds?: number
    }

interface RegistryRow extends RegistryEntry {
  scope: string
}

/**
 * Read the recalibration quiet-window seconds from brahma_formula_constants.
 * Falls back to DEFAULT_DEBOUNCE_SECONDS if the constant is missing/malformed.
 */
export async function getRecalibrationDebounceSeconds(): Promise<number> {
  try {
    const { rows } = await query<{ value_jsonb: { seconds?: number } }>(
      `SELECT value_jsonb FROM brahma_formula_constants
        WHERE constant_id = 'mimamsa_recalibration_debounce_seconds'`
    )
    const seconds = rows[0]?.value_jsonb?.seconds
    return typeof seconds === 'number' && seconds > 0 ? seconds : DEFAULT_DEBOUNCE_SECONDS
  } catch {
    return DEFAULT_DEBOUNCE_SECONDS
  }
}

/**
 * Enqueue a debounced, targeted LEL recalibration run for one chart.
 *
 * Never throws for a debounce/coalesce condition — those return
 * `{ enqueued: false, reason }`. Only unexpected DB/dispatch failures throw.
 */
export async function enqueueLelRecalibration(
  { chartId, triggeredBy = RECAL_TRIGGERED_BY, force = false }: EnqueueRecalibrationArgs
): Promise<EnqueueRecalibrationResult> {
  // ── Guard 1: quiet-window (skipped when force) ─────────────────────────────
  if (!force) {
    const debounceSeconds = await getRecalibrationDebounceSeconds()
    const { rows: lastRecal } = await query<{ id: string }>(
      `SELECT id FROM build_runs
        WHERE chart_id = $1 AND scope = $2 AND scope_target = $3
          AND created_at > now() - ($4 || ' seconds')::interval
        ORDER BY created_at DESC
        LIMIT 1`,
      [chartId, RECAL_SCOPE, LEL_RECAL_SCOPE_TARGET, String(debounceSeconds)]
    )
    if (lastRecal.length > 0) {
      return { enqueued: false, reason: 'debounced', debounce_seconds: debounceSeconds }
    }
  }

  // ── Guard 2: RUN_ACTIVE (mirrors runs-route Gate 0; coalesce, not error) ────
  const { rows: active } = await query<{ id: string }>(
    `SELECT id FROM build_runs
      WHERE chart_id = $1 AND state IN ('planned','running','paused')
      LIMIT 1`,
    [chartId]
  )
  if (active.length > 0) {
    return { enqueued: false, reason: 'run_active', existing_run_id: active[0].id }
  }

  // ── Resolve the plan over the LEL-dependent asset_set ──────────────────────
  const [registryResult, throughputResult] = await Promise.all([
    query<RegistryRow>(
      `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds, scope
         FROM asset_registry WHERE is_active = true AND has_writer = true ORDER BY layer, sort_order`
    ),
    query<ThroughputEntry>(
      `SELECT DISTINCT ON (asset_id) asset_id, state
         FROM asset_throughput
        WHERE chart_id = $1 OR chart_id IS NULL
        ORDER BY asset_id, (chart_id = $1) DESC NULLS LAST`,
      [chartId]
    ),
  ])

  const throughput = new Map(throughputResult.rows.map(r => [r.asset_id, r]))
  const buildPlan = resolveBuildPlan({
    scope: RECAL_SCOPE,
    scope_target: LEL_RECAL_SCOPE_TARGET,
    action: RECAL_ACTION,
    registry: registryResult.rows,
    throughput,
  })
  const plan = buildPlan.plan_waves.flat()

  if (buildPlan.status !== 'ok' || plan.length === 0) {
    return { enqueued: false, reason: 'nothing_to_build' }
  }

  // ── INSERT the run (same shape as the runs route standard build path) ──────
  const runResult = await query<{ id: string }>(
    `INSERT INTO build_runs (chart_id, scope, scope_target, action, state, plan, triggered_by)
     VALUES ($1, $2, $3, $4, 'planned', $5, $6)
     RETURNING id`,
    [chartId, RECAL_SCOPE, LEL_RECAL_SCOPE_TARGET, RECAL_ACTION, JSON.stringify(plan), triggeredBy]
  )
  const runId = runResult.rows[0].id

  const placeholders = plan.map((_, i) => `($1, $${i * 3 + 2}, $${i * 3 + 3}, $${i * 3 + 4})`).join(', ')
  const flatParams = [runId, ...plan.flatMap((asset_id, i) => [asset_id, i, 'queued'])]
  await query(
    `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ${placeholders}
     ON CONFLICT (run_id, asset_id) DO NOTHING`,
    flatParams
  )

  // Dispatch the job — failure marks the run failed so it does not orphan as 'planned'.
  try {
    await invokeRunJob(runId)
  } catch (err) {
    const errMsg = (err as Error).message
    console.error('[recalibrationEnqueue] invokeRunJob failed — marking run failed:', errMsg)
    await query(`UPDATE build_runs SET state='failed', ended_at=NOW(), last_error=$1 WHERE id=$2`, [errMsg, runId])
    await query(`UPDATE build_run_assets SET state='aborted' WHERE run_id=$1 AND state='queued'`, [runId])
    throw err
  }

  return { enqueued: true, run_id: runId, plan }
}

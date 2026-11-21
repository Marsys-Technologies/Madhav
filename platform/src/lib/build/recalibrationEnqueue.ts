/**
 * recalibrationEnqueue.ts — debounced, targeted LEL recalibration enqueue.
 *
 * When a new life event is saved, the calibration surfaces that depend on the
 * chart's LEL corpus become stale. Rather than a full rebuild, we enqueue a
 * TARGETED `scope='asset_set'` run over just the LEL-dependent assets for THAT
 * chart. Shared Build preparation applies chart-scoped writer, protection and
 * freshness rules and persists the frozen plan with its queued assets before
 * dispatch. Recalibration does not clear data before the run.
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
import { query, withTransaction } from '@/lib/db/client'
import type { AssetId, BlockerEntry, ProtectedAssetBlocker } from './plan'
import { invokeRunJob, RunSubmissionRejected } from './jobInvoker'
import { terminalizeFailedRun } from './terminalizeFailedRun'
import {
  BuildPreparationError,
  findActiveRun,
  isActiveRunConflict,
  persistPreparedRun,
  resolveRunPreparation,
} from './runPreparation'

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
  | { enqueued: false; reason: 'dispatch_unknown'; run_id: string }
  | {
      enqueued: false
      reason: 'debounced' | 'run_active' | 'nothing_to_build' | 'protected'
      existing_run_id?: string
      debounce_seconds?: number
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
 * Coalesced, blocked and protected runs return `{ enqueued: false, reason }`.
 * Preparation and dispatch errors propagate to the caller's partial result.
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

  let queued: { runId: string; plan: AssetId[] }
  try {
    queued = await withTransaction(async (client) => {
      const prepared = await resolveRunPreparation(client, {
        chartId,
        scope: RECAL_SCOPE,
        scopeTarget: LEL_RECAL_SCOPE_TARGET,
        action: RECAL_ACTION,
        allowedScopes: ['per_chart'],
        clearPolicy: 'none',
        triggeredBy,
      })
      const runId = await persistPreparedRun(client, prepared, triggeredBy)
      return { runId, plan: prepared.plan }
    })
  } catch (error) {
    // A competing insert can win after both requests pass the active-run read.
    // withTransaction has rolled back before we query for the winning run.
    if (isActiveRunConflict(error)) {
      const existingRunId = await findActiveRun({ query }, chartId)
      return existingRunId
        ? { enqueued: false, reason: 'run_active', existing_run_id: existingRunId }
        : { enqueued: false, reason: 'run_active' }
    }
    if (!(error instanceof BuildPreparationError)) throw error

    if (error.code === 'RUN_ACTIVE') {
      const existingRunId = error.details.existing_run_id
      return typeof existingRunId === 'string'
        ? { enqueued: false, reason: 'run_active', existing_run_id: existingRunId }
        : { enqueued: false, reason: 'run_active' }
    }
    const protectedAssets = error.details.protected_assets
    const blockers = error.details.blockers
    const blockedByProtection = error.code === 'UPSTREAM_BLOCKED' &&
      Array.isArray(protectedAssets) && Array.isArray(blockers) &&
      blockers.some((blocker: BlockerEntry) =>
        protectedAssets.some((asset: ProtectedAssetBlocker) => asset.asset_id === blocker.dep_asset_id))
    if (error.code === 'PROTECTED' || blockedByProtection) {
      return { enqueued: false, reason: 'protected' }
    }
    if (error.code === 'UPSTREAM_BLOCKED' || error.code === 'ALL_LIT') {
      return { enqueued: false, reason: 'nothing_to_build' }
    }
    throw error
  }

  try {
    const dispatch = await invokeRunJob(queued.runId, { reportDefiniteRejection: true })
    if (!dispatch.executionName) {
      return { enqueued: false, reason: 'dispatch_unknown', run_id: queued.runId }
    }
  } catch (error) {
    if (!(error instanceof RunSubmissionRejected)) {
      const message = error instanceof Error ? error.message : String(error)
      console.error('[recalibrationEnqueue] run submission outcome unknown:', queued.runId, message)
      return { enqueued: false, reason: 'dispatch_unknown', run_id: queued.runId }
    }
    try {
      await terminalizeFailedRun(queued.runId, error.message, { unclaimedOnly: true })
    } catch (recordError) {
      const message = recordError instanceof Error ? recordError.message : String(recordError)
      console.error('[recalibrationEnqueue] could not record submission refusal:', queued.runId, message)
    }
    throw error
  }

  return { enqueued: true, run_id: queued.runId, plan: queued.plan }
}

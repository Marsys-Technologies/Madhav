import 'server-only'
import { getPool } from '@/lib/db/client'
import {
  BuildPreparationError,
  isActiveRunConflict,
  persistPreparedRun,
  resolveRunPreparation,
  findActiveRun,
  type Queryable,
} from '@/lib/build/runPreparation'
import { invalidateAssets, InvalidationError } from '@/lib/build/assetInvalidation'
import { dispatchPreparedRun } from '@/lib/build/runDispatch'
import { JOB_DISPATCH_FAILED_PREFIX } from '@/lib/charts/readiness'
import type { ChartInputSnapshot } from '@/lib/charts/types'
import {
  classifyChartChanges,
  normalizeChartUpdate,
  normalizeStoredChart,
  resolveTimezoneOffsetMinutes,
  type ChartChangeField,
  type NormalizedChartInputs,
  type StoredChartRow,
} from '@/lib/charts/updateChart'

/**
 * Atomic chart correction and recompute (Jātaka chart workspace, Task 6).
 *
 * One SERIALIZABLE transaction on one client: lock the chart row, refuse an
 * active build, classify server-side, and for a computation-affecting change
 * resolve the complete per-chart rebuild plan, archive every active
 * conversation with the pre-correction snapshot, update the inputs, strictly
 * clear governed derived data in reverse dependency order, reset throughput,
 * and persist one frozen global rebuild run. Any failure rolls all of it back
 * and the original chart stays usable. Dispatch happens only after COMMIT; a
 * dispatch failure is the honest Needs rebuild state, and old results are never
 * restored or served for corrected details.
 */

export type ChartUpdateResult =
  | { mode: 'noop'; chartId: string; changedFields: [] }
  | { mode: 'display-only'; chartId: string; changedFields: ChartChangeField[] }
  | { mode: 'recompute-started'; chartId: string; changedFields: ChartChangeField[]; runId: string }
  | { mode: 'needs-rebuild'; chartId: string; changedFields: ChartChangeField[]; runId: string; error: string }

export type ChartUpdateErrorCode =
  | 'VALIDATION_FAILED'
  | 'CHART_NOT_FOUND'
  | 'RUN_ACTIVE'
  | 'PROTECTED'
  | 'INVALID_BUILD_PLAN'
  | 'CLEAR_SPEC_MISSING'
  | 'RECOMPUTE_PREPARATION_FAILED'

const STATUS: Record<ChartUpdateErrorCode, number> = {
  VALIDATION_FAILED: 422,
  CHART_NOT_FOUND: 404,
  RUN_ACTIVE: 409,
  PROTECTED: 422,
  INVALID_BUILD_PLAN: 422,
  CLEAR_SPEC_MISSING: 422,
  RECOMPUTE_PREPARATION_FAILED: 500,
}

export class ChartUpdateError extends Error {
  readonly status: number
  constructor(
    readonly code: ChartUpdateErrorCode,
    message: string,
    readonly fields?: Record<string, string>,
    readonly details: Record<string, unknown> = {},
  ) {
    super(message)
    this.name = 'ChartUpdateError'
    this.status = STATUS[code]
  }
}

function toChartUpdateError(error: unknown): ChartUpdateError {
  if (error instanceof ChartUpdateError) return error
  if (error instanceof BuildPreparationError) {
    switch (error.code) {
      case 'RUN_ACTIVE':
        return new ChartUpdateError('RUN_ACTIVE', error.message, undefined, error.details)
      case 'PROTECTED':
        return new ChartUpdateError('PROTECTED', 'A required per-chart asset is protected; the correction cannot recompute it.', undefined, error.details)
      case 'CLEAR_SPEC_MISSING':
        return new ChartUpdateError('CLEAR_SPEC_MISSING', error.message, undefined, error.details)
      default:
        // UPSTREAM_BLOCKED, ALL_LIT, INVALID_BUILD_PLAN, CODE_DIGEST_UNAVAILABLE:
        // the complete Gaṇita → Mīmāṃsā plan cannot be frozen.
        return new ChartUpdateError('INVALID_BUILD_PLAN', error.message, undefined, { reason: error.code, ...error.details })
    }
  }
  if (error instanceof InvalidationError) {
    return new ChartUpdateError('CLEAR_SPEC_MISSING', error.message, undefined, { asset_id: error.assetId })
  }
  if (isActiveRunConflict(error)) {
    return new ChartUpdateError('RUN_ACTIVE', 'A build is already in progress for this chart')
  }
  return new ChartUpdateError('RECOMPUTE_PREPARATION_FAILED', 'Chart correction could not be prepared; nothing was changed.')
}

function snapshotOf(stored: NormalizedChartInputs, capturedAt: string): ChartInputSnapshot {
  let offset: number | null = null
  if (stored.timezone_id) {
    try {
      offset = resolveTimezoneOffsetMinutes(stored.birth_date, stored.birth_time, stored.timezone_id)
    } catch {
      offset = null
    }
  }
  return {
    name: stored.name,
    preferred_name: stored.preferred_name,
    subject_name: stored.subject_name,
    birth_date: stored.birth_date,
    birth_time: stored.birth_time,
    birth_place: stored.birth_place,
    birth_lat: stored.birth_lat,
    birth_lng: stored.birth_lng,
    timezone_id: stored.timezone_id,
    effective_tz_offset_minutes: offset,
    ayanamshas: stored.ayanamshas,
    captured_at: capturedAt,
  }
}

async function lockChart(db: Queryable, chartId: string): Promise<StoredChartRow> {
  const { rows } = await db.query<StoredChartRow & { id: string }>(
    `SELECT id, name, preferred_name, subject_name,
            birth_date::text AS birth_date, birth_time::text AS birth_time, birth_place,
            birth_lat::float8 AS birth_lat, birth_lng::float8 AS birth_lng, timezone_id,
            ayanamsa, owner_id, client_id
       FROM charts
      WHERE id=$1
      FOR UPDATE`,
    [chartId],
  )
  const row = rows[0]
  if (!row) throw new ChartUpdateError('CHART_NOT_FOUND', 'Chart not found')
  return row
}

export async function updateChartAndMaybeRecompute(args: {
  chartId: string
  principalId: string
  input: unknown
}): Promise<ChartUpdateResult> {
  const { chartId, principalId } = args
  const normalized = normalizeChartUpdate(args.input)
  if (!normalized.ok) {
    throw new ChartUpdateError('VALIDATION_FAILED', 'Some chart details are invalid.', normalized.fields)
  }
  const submitted = normalized.value

  const pool = await getPool()
  const client = await pool.connect()
  let outcome: { runId: string; changedFields: ChartChangeField[] } | null = null
  try {
    await client.query('BEGIN ISOLATION LEVEL SERIALIZABLE')
    const stored = normalizeStoredChart(await lockChart(client, chartId))

    const activeRunId = await findActiveRun(client, chartId)
    if (activeRunId) {
      throw new ChartUpdateError('RUN_ACTIVE', 'A build is already in progress for this chart', undefined, {
        existing_run_id: activeRunId,
      })
    }

    const classification = classifyChartChanges(stored, submitted)
    if (classification.mode === 'noop') {
      await client.query('COMMIT')
      return { mode: 'noop', chartId, changedFields: [] }
    }
    if (classification.mode === 'display-only') {
      await client.query(
        'UPDATE charts SET name=$2, preferred_name=$3, subject_name=$4 WHERE id=$1',
        [chartId, submitted.name, submitted.preferred_name, submitted.subject_name],
      )
      await client.query('COMMIT')
      return { mode: 'display-only', chartId, changedFields: classification.changedFields }
    }

    // Computation-affecting: resolve and freeze the complete per-chart plan first,
    // so a protected asset or an unfreezable plan refuses before any mutation.
    const prepared = await resolveRunPreparation(client, {
      chartId,
      scope: 'global',
      scopeTarget: null,
      action: 'rebuild',
      allowedScopes: ['per_chart'],
      clearPolicy: 'chart-correction-strict',
      triggeredBy: principalId,
      requireCompletePlan: true,
    })

    // Lock every conversation not already locked by an earlier correction —
    // active ones and manual archives alike, so a manual archive cannot later be
    // un-archived and continued against the corrected chart. A manual archive
    // keeps its original archive time.
    const archived = await client.query<{ id: string }>(
      `UPDATE conversations
          SET archived_at=COALESCE(archived_at, NOW()),
              updated_at=NOW(),
              archive_reason='chart_details_changed',
              archived_chart_snapshot=$2::jsonb
        WHERE chart_id=$1 AND archive_reason IS NULL
        RETURNING id`,
      [chartId, JSON.stringify(snapshotOf(stored, new Date().toISOString()))],
    )

    await client.query(
      `UPDATE charts
          SET name=$2, preferred_name=$3, subject_name=$4,
              birth_date=$5::date, birth_time=$6::time, birth_place=$7,
              birth_lat=$8, birth_lng=$9, timezone_id=$10, ayanamsa=$11
        WHERE id=$1`,
      [
        chartId,
        submitted.name,
        submitted.preferred_name,
        submitted.subject_name,
        submitted.birth_date,
        submitted.birth_time,
        submitted.birth_place,
        submitted.birth_lat,
        submitted.birth_lng,
        submitted.timezone_id,
        submitted.ayanamshas.join(','),
      ],
    )

    await invalidateAssets({ db: client, chartId, assets: prepared.clearAssets, policy: 'chart-correction-strict' })

    await client.query(
      `UPDATE asset_throughput
          SET state='dormant', last_built_at=NULL, rows_written=NULL,
              built_against_upstream_hash=NULL, built_against_writer_hash=NULL,
              last_error=NULL
        WHERE chart_id=$1 AND asset_id=ANY($2::text[])`,
      [chartId, prepared.plan],
    )

    const runId = await persistPreparedRun(client, prepared, principalId)

    // Attach the run only to the rows this correction archived — never sweep
    // older historical rows into a later correction.
    const archivedIds = archived.rows.map((row) => row.id)
    if (archivedIds.length > 0) {
      await client.query(`UPDATE conversations SET archived_by_run_id=$2 WHERE id=ANY($1::uuid[])`, [archivedIds, runId])
    }

    await client.query('COMMIT')
    outcome = { runId, changedFields: classification.changedFields }
  } catch (error) {
    await client.query('ROLLBACK').catch(() => null)
    const mapped = toChartUpdateError(error)
    if (mapped.code === 'RECOMPUTE_PREPARATION_FAILED') {
      console.error('[charts/recompute] correction transaction rolled back:', (error as Error)?.message)
    }
    throw mapped
  } finally {
    client.release()
  }

  const dispatch = await dispatchPreparedRun(outcome.runId, { failurePrefix: JOB_DISPATCH_FAILED_PREFIX })
  if (!dispatch.ok) {
    return { mode: 'needs-rebuild', chartId, changedFields: outcome.changedFields, runId: outcome.runId, error: dispatch.message }
  }
  return { mode: 'recompute-started', chartId, changedFields: outcome.changedFields, runId: outcome.runId }
}

import 'server-only'
import { query } from '@/lib/db/client'
import { BRAHMA_LAYER_ORDER, type BrahmaLayerId } from '@/lib/brahma/lexicon'
import type { LayerPip } from '@/lib/roster/types'

/**
 * Shared chart-readiness authority (Jātaka chart workspace, Task 1).
 *
 * The dashboard directory, the chart workspace and the Paripraśna availability
 * gate all read readiness from here so their labels and gates cannot drift.
 * Source of truth is active-registry `asset_throughput` plus the latest
 * `build_runs` row — never the legacy `pyramid_layers` table.
 */

export type ChartReadinessState =
  | 'not-built'
  | 'building'
  | 'partially-built'
  | 'ready'
  | 'failed'
  | 'needs-rebuild'

export interface ChartReadiness {
  state: ChartReadinessState
  percent: number
  label: string
  layerPips: LayerPip[]
  lastActivity: string | null
  activeRunId: string | null
  latestRunId: string | null
  latestError: string | null
  /**
   * Non-blocking notice: the latest small refresh failed or stopped but left
   * every asset it touched holding its previously valid data. Null/absent otherwise.
   */
  refreshWarning?: string | null
}

export interface UnresolvedFailure {
  assets: number
  /** True when any unresolved failed run never started (JOB_DISPATCH_FAILED). */
  dispatchFailed: boolean
}

export type ReadinessThroughputRow = {
  asset_id: string
  state: string
  rows_written: number | null
  last_built_at?: string | null
}

export type ReadinessRunRow = {
  id: string
  state: string
  scope?: string
  action?: string
  last_error: string | null
  created_at?: string
  started_at?: string | null
  ended_at?: string | null
}

type ThroughputRow = ReadinessThroughputRow & {
  chart_id: string
  last_built_at: string | null
}

type LatestRunRow = ReadinessRunRow & {
  chart_id: string
  action: string
  created_at: string
  started_at: string | null
  ended_at: string | null
}

export const CHART_READINESS_LABELS: Record<ChartReadinessState, string> = {
  'not-built': 'Not built',
  building: 'Building',
  'partially-built': 'Partially built',
  ready: 'Ready',
  failed: 'Failed',
  'needs-rebuild': 'Needs rebuild',
}

/** Prefix written to `build_runs.last_error` when a prepared run could not be dispatched. */
export const JOB_DISPATCH_FAILED_PREFIX = 'JOB_DISPATCH_FAILED'

const ACTIVE_RUN_STATES = new Set(['planned', 'running', 'paused'])

const ASSET_PREFIX_TO_LAYER: ReadonlyArray<[string, BrahmaLayerId]> = [
  ['ga_', 'ganita'],
  ['bo_', 'bodha'],
  ['ka_', 'kala'],
  ['ph_', 'phala'],
  ['mi_', 'mimamsa'],
]

function assetLayer(assetId: string): BrahmaLayerId | null {
  for (const [prefix, layer] of ASSET_PREFIX_TO_LAYER) {
    if (assetId.startsWith(prefix)) return layer
  }
  return null
}

export function deriveChartReadiness(input: {
  throughput: ReadinessThroughputRow[]
  latestRun: ReadinessRunRow | null
  /**
   * Failed or stopped runs of any age that still own broken per-chart assets:
   * for a small run, an asset it planned that no longer holds valid data; for a
   * full rebuild (a correction's recompute or an operator full rebuild), an
   * asset it planned that has not been rebuilt since it started. Omitted →
   * unknown, which fails closed after a failed/stopped latest run.
   */
  unresolvedFailure?: UnresolvedFailure | null
}): ChartReadiness {
  const { throughput, latestRun } = input
  const unresolvedFailure = input.unresolvedFailure ?? null

  // A layer holds data when any of its active assets is lit (zero-row-by-design
  // assets count) or has written rows (stale data is still present data).
  const layerData = new Map<BrahmaLayerId, { hasData: boolean; isBuilding: boolean }>()
  for (const row of throughput) {
    const layer = assetLayer(row.asset_id)
    if (!layer) continue
    const current = layerData.get(layer) ?? { hasData: false, isBuilding: false }
    layerData.set(layer, {
      hasData: current.hasData || row.state === 'lit' || (row.rows_written != null && row.rows_written > 0),
      isBuilding: current.isBuilding || row.state === 'building',
    })
  }

  // Brahmagyan (L0) is global infrastructure with no per-chart throughput — always lit.
  const layerPips: LayerPip[] = BRAHMA_LAYER_ORDER.map((layer) => {
    if (layer === 'brahmagyan') return { layer, state: 'lit' as const }
    const entry = layerData.get(layer)
    if (entry?.hasData) return { layer, state: 'lit' as const }
    if (entry?.isBuilding) return { layer, state: 'building' as const }
    return { layer, state: 'dim' as const }
  })

  const perChartLit = layerPips.filter((p) => p.layer !== 'brahmagyan' && p.state === 'lit').length
  const allLit = layerPips.every((p) => p.state === 'lit')
  const anyBuilding = throughput.some((row) => row.state === 'building')
  const runActive = latestRun !== null && ACTIVE_RUN_STATES.has(latestRun.state)
  const endedIncomplete = (run: ReadinessRunRow | null) => run?.state === 'failed' || run?.state === 'stopped'
  const latestDispatchFailed =
    latestRun?.state === 'failed' && (latestRun.last_error ?? '').startsWith(JOB_DISPATCH_FAILED_PREFIX)

  // Any failed or stopped run — of any age, not only the latest — that still owns
  // broken per-chart assets keeps the chart out of Ready: a later run can never
  // mask it. Without a known failure picture, a failed/stopped latest run fails closed.
  const unresolved = unresolvedFailure ? unresolvedFailure.assets > 0 : endedIncomplete(latestRun)
  const refreshWarningApplies = endedIncomplete(latestRun) && !unresolved

  let state: ChartReadinessState
  if (runActive || anyBuilding) state = 'building'
  else if (unresolved) state = unresolvedFailure?.dispatchFailed || latestDispatchFailed ? 'needs-rebuild' : 'failed'
  else if (latestDispatchFailed) state = 'needs-rebuild'
  else if (allLit) state = 'ready'
  else if (latestRun?.state === 'failed') state = 'failed'
  else if (perChartLit > 0) state = 'partially-built'
  else state = 'not-built'

  const refreshWarning =
    state === 'ready' && refreshWarningApplies
      ? 'The latest refresh did not finish; the previously computed chart remains in use.'
      : null

  // Brahmagyan counts toward the percentage only once the chart has computed data,
  // so a chart with nothing computed (or cleared for rebuild) reads 0%, not 17%.
  const litCount = perChartLit > 0 ? perChartLit + 1 : 0
  const percent = Math.round((litCount / BRAHMA_LAYER_ORDER.length) * 100)

  const timestamps = throughput.map((row) => row.last_built_at).filter((t): t is string => Boolean(t))
  const lastActivity = timestamps.length > 0 ? timestamps.reduce((a, b) => (a > b ? a : b)) : null

  return {
    state,
    percent,
    label: CHART_READINESS_LABELS[state],
    layerPips,
    lastActivity,
    activeRunId: runActive ? latestRun!.id : null,
    latestRunId: latestRun?.id ?? null,
    latestError: latestRun?.last_error ?? null,
    refreshWarning,
  }
}

export function emptyChartReadiness(): ChartReadiness {
  return deriveChartReadiness({ throughput: [], latestRun: null })
}

export function isDerivedChartReady(readiness: ChartReadiness): boolean {
  return readiness.state === 'ready'
}

export async function getChartReadinessMap(chartIds: string[]): Promise<Map<string, ChartReadiness>> {
  if (chartIds.length === 0) return new Map()
  const [throughput, runs, failures] = await Promise.all([
    query<ThroughputRow>(
      `SELECT at.chart_id, at.asset_id, at.state, at.rows_written, at.last_built_at
         FROM asset_throughput at
         JOIN asset_registry ar ON ar.asset_id = at.asset_id AND ar.is_active = true
        WHERE at.chart_id = ANY($1::uuid[])`,
      [chartIds],
    ),
    // Latest run of any kind and any state (a failed dispatch must be visible).
    query<LatestRunRow>(
      `SELECT DISTINCT ON (r.chart_id)
              r.id, r.chart_id, r.state, r.scope, r.action, r.last_error, r.created_at, r.started_at, r.ended_at
         FROM build_runs r
        WHERE r.chart_id = ANY($1::uuid[])
        ORDER BY r.chart_id, r.created_at DESC, r.id DESC`,
      [chartIds],
    ),
    // Failed/stopped runs of any age that still own broken active per-chart
    // assets. A small run's asset is broken when it no longer holds valid data;
    // a full rebuild's asset is broken until rebuilt after the rebuild started.
    query<{ chart_id: string; assets: number; dispatch_failed: boolean }>(
      `SELECT r.chart_id,
              COUNT(DISTINCT bra.asset_id)::int AS assets,
              COALESCE(bool_or(r.last_error LIKE 'JOB_DISPATCH_FAILED%'), false) AS dispatch_failed
         FROM build_runs r
         JOIN build_run_assets bra ON bra.run_id = r.id
         JOIN asset_registry ar ON ar.asset_id = bra.asset_id AND ar.is_active = true AND ar.scope = 'per_chart'
         LEFT JOIN asset_throughput at ON at.chart_id = r.chart_id AND at.asset_id = bra.asset_id
        WHERE r.chart_id = ANY($1::uuid[])
          AND r.state IN ('failed', 'stopped')
          AND NOT COALESCE(
                at.state IN ('lit', 'stale')
                AND (NOT (r.scope = 'global' AND r.action = 'rebuild') OR at.last_built_at >= r.created_at),
                false)
        GROUP BY r.chart_id`,
      [chartIds],
    ),
  ])
  return new Map(
    chartIds.map((id) => {
      const failure = failures.rows.find((row) => row.chart_id === id)
      return [
        id,
        deriveChartReadiness({
          throughput: throughput.rows.filter((row) => row.chart_id === id),
          latestRun: runs.rows.find((row) => row.chart_id === id) ?? null,
          unresolvedFailure: failure
            ? { assets: Number(failure.assets), dispatchFailed: Boolean(failure.dispatch_failed) }
            : { assets: 0, dispatchFailed: false },
        }),
      ]
    }),
  )
}

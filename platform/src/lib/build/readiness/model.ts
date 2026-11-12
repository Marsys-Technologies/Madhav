import { BRAHMA_LAYER_ORDER, type BrahmaLayerId } from '@/lib/brahma/lexicon'
import { runBlocksReadings } from './servingImpact'
import type {
  ChartReadiness,
  ChartReadinessState,
  LayerPip,
  ReadinessRunRow,
  ReadinessThroughputRow,
  UnresolvedFailure,
} from './types'

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

  const runActive = latestRun !== null && ACTIVE_RUN_STATES.has(latestRun.state)
  const activeRunBlocks = runActive && runBlocksReadings(latestRun!)
  // Assets a non-blocking active run is rebuilding keep serving their previous data.
  const nonBlockingAssets = new Set(runActive && !activeRunBlocks ? (latestRun!.planned_assets ?? []) : [])

  // A layer holds data when any of its active assets is lit (zero-row-by-design
  // assets count) or has written rows. A stale asset is not valid current data:
  // its layer needs attention and the chart is not Ready until it is rebuilt.
  const layerData = new Map<BrahmaLayerId, { hasData: boolean; isBuilding: boolean; isStale: boolean }>()
  for (const row of throughput) {
    const layer = assetLayer(row.asset_id)
    if (!layer) continue
    const current = layerData.get(layer) ?? { hasData: false, isBuilding: false, isStale: false }
    const stale = row.state === 'stale'
    layerData.set(layer, {
      hasData: current.hasData || (!stale && (row.state === 'lit' || (row.rows_written != null && row.rows_written > 0))),
      isBuilding: current.isBuilding || row.state === 'building',
      isStale: current.isStale || stale,
    })
  }

  // Brahmagyan (L0) is global infrastructure with no per-chart throughput — always lit.
  const layerPips: LayerPip[] = BRAHMA_LAYER_ORDER.map((layer) => {
    if (layer === 'brahmagyan') return { layer, state: 'lit' as const }
    const entry = layerData.get(layer)
    if (entry?.isStale) return { layer, state: 'amber' as const }
    if (entry?.hasData) return { layer, state: 'lit' as const }
    if (entry?.isBuilding) return { layer, state: 'building' as const }
    return { layer, state: 'dim' as const }
  })

  const perChartLit = layerPips.filter((p) => p.layer !== 'brahmagyan' && p.state === 'lit').length
  const allLit = layerPips.every((p) => p.state === 'lit')
  const anyBuilding = throughput.some((row) => row.state === 'building' && !nonBlockingAssets.has(row.asset_id))
  const endedIncomplete = (run: ReadinessRunRow | null) => run?.state === 'failed' || run?.state === 'stopped'
  const latestDispatchFailed =
    latestRun?.state === 'failed' && (latestRun.last_error ?? '').startsWith(JOB_DISPATCH_FAILED_PREFIX)

  // Any failed or stopped run — of any age, not only the latest — that still owns
  // broken per-chart assets keeps the chart out of Ready: a later run can never
  // mask it. Without a known failure picture, a failed/stopped latest run fails closed.
  const unresolved = unresolvedFailure ? unresolvedFailure.assets > 0 : endedIncomplete(latestRun)
  const refreshWarningApplies = endedIncomplete(latestRun) && !unresolved

  let state: ChartReadinessState
  if (activeRunBlocks || anyBuilding) state = 'building'
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
    activeRunBlocksReadings: activeRunBlocks || anyBuilding,
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

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
}): ChartReadiness {
  const { throughput, latestRun } = input

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
  const runFailed = latestRun?.state === 'failed'
  const dispatchFailed = runFailed && (latestRun?.last_error ?? '').startsWith(JOB_DISPATCH_FAILED_PREFIX)
  // A global rebuild (a chart correction's recompute, or an operator full rebuild)
  // that failed or was stopped leaves a mix of new and missing results that can
  // still light every layer; it is never Ready. A failed scoped refresh on a fully
  // lit chart is (the failure stays visible in latestError).
  const globalRebuildIncomplete =
    latestRun?.scope === 'global' &&
    latestRun?.action === 'rebuild' &&
    (latestRun.state === 'failed' || latestRun.state === 'stopped')

  let state: ChartReadinessState
  if (runActive || anyBuilding) state = 'building'
  else if (dispatchFailed) state = 'needs-rebuild'
  else if (globalRebuildIncomplete) state = 'failed'
  else if (allLit) state = 'ready'
  else if (runFailed) state = 'failed'
  else if (perChartLit > 0) state = 'partially-built'
  else state = 'not-built'

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
  const [throughput, runs] = await Promise.all([
    query<ThroughputRow>(
      `SELECT at.chart_id, at.asset_id, at.state, at.rows_written, at.last_built_at
         FROM asset_throughput at
         JOIN asset_registry ar ON ar.asset_id = at.asset_id AND ar.is_active = true
        WHERE at.chart_id = ANY($1::uuid[])`,
      [chartIds],
    ),
    query<LatestRunRow>(
      `SELECT DISTINCT ON (chart_id)
              id, chart_id, state, scope, action, last_error, created_at, started_at, ended_at
         FROM build_runs
        WHERE chart_id = ANY($1::uuid[])
        ORDER BY chart_id, created_at DESC`,
      [chartIds],
    ),
  ])
  return new Map(
    chartIds.map((id) => [
      id,
      deriveChartReadiness({
        throughput: throughput.rows.filter((row) => row.chart_id === id),
        latestRun: runs.rows.find((row) => row.chart_id === id) ?? null,
      }),
    ]),
  )
}

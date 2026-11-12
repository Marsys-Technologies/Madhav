import type { BrahmaLayerId } from '@/lib/brahma/lexicon'

export type LayerPipState = 'dim' | 'building' | 'amber' | 'lit'

export interface LayerPip {
  layer: BrahmaLayerId
  state: LayerPipState
}

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
  /**
   * Whether the active run (if any) blocks new readings. False only for a run
   * classified as leaving the served dataset valid (see servingImpact.ts).
   */
  activeRunBlocksReadings?: boolean
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
  /** Assets the run planned (build_run_assets). Null/absent → unknown → blocking. */
  planned_assets?: string[] | null
}

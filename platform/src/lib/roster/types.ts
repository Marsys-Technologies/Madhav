import type { Chart } from '@/lib/db/types'
import type { BrahmaLayerId } from '@/lib/brahma/lexicon'

export interface RosterStats {
  total: number
  inActiveBuild: number
  consumedToday: number
  predictionsOverdue: number
}

export type LayerPipState = 'dim' | 'building' | 'amber' | 'lit'

export interface LayerPip {
  layer: BrahmaLayerId
  state: LayerPipState
}

export interface ChartBuildState {
  build_id: string
  status: 'queued' | 'running' | 'complete' | 'failed' | 'cancelled' | 'cancelling'
  progress_pct: number
  ayanamshas: string[]
  started_at: string | null
  error_summary: string | null
}

export interface ChartWithMeta extends Chart {
  pyramidPercent: number
  lastLayerActivity: string | null
  buildState: ChartBuildState | null
  layerPips: LayerPip[]
  /** True only when the current user is owner or super_admin — not for view-grantees. */
  canBuild: boolean
}

export interface FilterState {
  q: string
  place: string
  dasha: string
  buildMin: number
  buildMax: number
  since: string
}

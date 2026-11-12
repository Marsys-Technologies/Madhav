import type { Chart } from '@/lib/db/types'
import type { ChartReadiness, LayerPip } from '@/lib/build/readiness/types'

export type { LayerPip, LayerPipState } from '@/lib/build/readiness/types'

export interface RosterStats {
  total: number
  inActiveBuild: number
  consumedToday: number
  predictionsOverdue: number
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
  /** Shared readiness authority (lib/build/readiness/model) — the only source for state labels. */
  readiness: ChartReadiness
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

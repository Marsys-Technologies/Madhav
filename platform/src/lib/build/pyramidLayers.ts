import 'server-only'
import { query } from '@/lib/db/client'

export interface BuildPyramidLayerRow {
  layer_key: string
  status: string
}

/** Build owns layer status; callers retain authorization and fallback policy. */
export function readChartPyramidLayers(id: string): Promise<{ rows: BuildPyramidLayerRow[] }> {
  return query<BuildPyramidLayerRow>(
    `SELECT layer AS layer_key, status FROM pyramid_layers WHERE chart_id = $1`,
    [id],
  )
}

/** Legacy Consult status selection only; this is not canonical chart readiness. */
export function legacyL1AvailabilityFromPyramid(pyramidRows: BuildPyramidLayerRow[]): 'ready' | 'l1-building' | 'no-build' {
  const l1Row = pyramidRows.find((r) => r.layer_key === 'L1')
  const isL1Built = l1Row?.status === 'built' || l1Row?.status === 'complete'
  const isL1Building = l1Row?.status === 'building' || l1Row?.status === 'in_progress'

  return pyramidRows.length === 0
    ? 'no-build'
    : isL1Built
      ? 'ready'
      : isL1Building
        ? 'l1-building'
        : 'no-build'
}

/**
 * capability-gate.ts
 *
 * Fetches the grounded layer status for a chart and returns the set of
 * capabilities that are verifiably backed by built layers.
 *
 * Layer → capability mapping:
 *   L0 (Brahmagyan / Foundation)   → classical_text_search, ephemeris_lookup, panchang_query
 *   L1 (Gaṇita / Chart Facts)      → chart_positions, dasha_query, strength_analysis, divisional_charts
 *   L2 (Bodha / Intelligence)      → signal_analysis, yoga_detection, holistic_bundle
 *   L3 (Kāla / Temporal)           → timeline_query, convergence_windows, transit_analysis
 *   L4 (Phala / Prediction)        → prediction_anchors, muhurta_query, rectification
 *   L5 (Mīmāṃsā / Learning)        → lel_analysis, calibration_report, learning_metrics
 *
 * A capability is available only when its layer's status === 'built'.
 * 'building', 'not-built', 'failed', 'attention' → excluded.
 *
 * WS-1-S3-A
 */

export type LayerStatus = 'built' | 'building' | 'failed' | 'attention' | 'not-built' | 'not_started'

export interface PyramidLayer {
  layer: string
  name: string
  status: LayerStatus
  asset_count: number
}

export interface PyramidLayersResponse {
  chart_id: string
  layers: PyramidLayer[]
}

/** Maps layer key → capabilities unlocked when that layer is 'built' */
const LAYER_CAPABILITIES: Record<string, string[]> = {
  L0: ['classical_text_search', 'ephemeris_lookup', 'panchang_query'],
  L1: ['chart_positions', 'dasha_query', 'strength_analysis', 'divisional_charts'],
  L2: ['signal_analysis', 'yoga_detection', 'holistic_bundle'],
  L3: ['timeline_query', 'convergence_windows', 'transit_analysis'],
  L4: ['prediction_anchors', 'muhurta_query', 'rectification'],
  L5: ['lel_analysis', 'calibration_report', 'learning_metrics'],
}

/**
 * Returns the array of capability strings for layers that are fully 'built'.
 *
 * @param chartId  - The chart UUID
 * @param baseUrl  - Optional base URL override for server-side calls. Defaults
 *                   to the NEXT_PUBLIC_APP_URL env var or an empty string (for
 *                   relative fetches in a browser context).
 */
export async function getGroundedCapabilities(
  chartId: string,
  baseUrl?: string,
): Promise<string[]> {
  const root = baseUrl ?? (typeof process !== 'undefined' ? process.env.NEXT_PUBLIC_APP_URL ?? '' : '')
  const url = `${root}/api/build/pyramid-layers?chart_id=${encodeURIComponent(chartId)}`

  let data: PyramidLayersResponse

  try {
    const res = await fetch(url, { cache: 'no-store' })
    if (!res.ok) return []
    data = (await res.json()) as PyramidLayersResponse
  } catch {
    return []
  }

  const capabilities: string[] = []
  for (const layer of data.layers ?? []) {
    if (layer.status === 'built') {
      const caps = LAYER_CAPABILITIES[layer.layer]
      if (caps) capabilities.push(...caps)
    }
  }
  return capabilities
}

/**
 * Convenience: returns whether a specific layer is 'built' for the given chart.
 */
export async function isLayerBuilt(
  chartId: string,
  layerKey: string,
  baseUrl?: string,
): Promise<boolean> {
  const root = baseUrl ?? (typeof process !== 'undefined' ? process.env.NEXT_PUBLIC_APP_URL ?? '' : '')
  const url = `${root}/api/build/pyramid-layers?chart_id=${encodeURIComponent(chartId)}`

  try {
    const res = await fetch(url, { cache: 'no-store' })
    if (!res.ok) return false
    const data = (await res.json()) as PyramidLayersResponse
    const layer = (data.layers ?? []).find((l) => l.layer === layerKey)
    return layer?.status === 'built'
  } catch {
    return false
  }
}

/**
 * Server-side variant: fetches pyramid layers directly via the DB client,
 * bypassing the HTTP round-trip.  Import only in server components / route
 * handlers (uses 'server-only' indirectly via @/lib/db/client).
 *
 * Returns the full layer array from the pyramid_layers table.
 */
export async function getPyramidLayersForChart(chartId: string): Promise<PyramidLayer[]> {
  // Lazy import — keeps this file importable in client bundles (tree-shaken).
  const { query } = await import('@/lib/db/client')

  const { rows } = await query<{
    layer_key: string
    layer_name: string
    status: string
    asset_count: number
  }>(
    `SELECT layer_key, layer_name, status, COUNT(asset_key) AS asset_count
     FROM pyramid_layers
     WHERE chart_id = $1
     GROUP BY layer_key, layer_name, status
     ORDER BY layer_key`,
    [chartId],
  )

  return rows.map((r) => ({
    layer: r.layer_key,
    name: r.layer_name,
    status: normalizeStatus(r.status),
    asset_count: Number(r.asset_count),
  }))
}

function normalizeStatus(raw: string | null): LayerStatus {
  switch (raw) {
    case 'complete':
    case 'built':
      return 'built'
    case 'building':
    case 'in_progress':
      return 'building'
    case 'failed':
      return 'failed'
    case 'attention':
      return 'attention'
    default:
      return 'not-built'
  }
}

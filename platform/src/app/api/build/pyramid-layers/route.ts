/**
 * GET /api/build/pyramid-layers
 *
 * Returns layer status derived from the pyramid table for a given chart_id.
 * Used by the LayerTower component and useChartBuildState hook.
 *
 * Query param: chart_id (required)
 *
 * Returns:
 *   { chart_id, layers: Layer[] }
 *   Layer: { layer, name, status, asset_count, assets: Asset[] }
 *   status: 'built' | 'building' | 'failed' | 'attention' | 'not-built'
 */

import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

const LAYER_ORDER = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5'] as const

const LAYER_NAMES: Record<string, { sanskrit: string; english: string }> = {
  L0: { sanskrit: 'Brahmagyan', english: 'Foundation' },
  L1: { sanskrit: 'Gaṇita', english: 'Chart Facts' },
  L2: { sanskrit: 'Bodha', english: 'Chart Intelligence' },
  L3: { sanskrit: 'Kāla', english: 'Temporal' },
  L4: { sanskrit: 'Phala', english: 'Prediction' },
  L5: { sanskrit: 'Mīmāṃsā', english: 'Learning' },
}

type LayerStatus = 'built' | 'building' | 'failed' | 'attention' | 'not-built'

interface Asset {
  asset_key: string
  status: LayerStatus
}

interface Layer {
  layer: string
  name: string
  status: LayerStatus
  asset_count: number
  assets: Asset[]
}

function deriveLayerStatus(assets: Asset[]): LayerStatus {
  if (!assets.length) return 'not-built'
  if (assets.every((a) => a.status === 'built')) return 'built'
  if (assets.some((a) => a.status === 'building')) return 'building'
  if (assets.some((a) => a.status === 'failed')) return 'failed'
  if (assets.some((a) => a.status === 'attention')) return 'attention'
  return 'not-built'
}

function normalizeStatus(raw: string | null): LayerStatus {
  switch (raw) {
    case 'complete':
    case 'built':
      return 'built'
    case 'in_progress':
    case 'building':
      return 'building'
    case 'failed':
    case 'error':
      return 'failed'
    case 'attention':
    case 'amber':
      return 'attention'
    default:
      return 'not-built'
  }
}

export async function GET(req: NextRequest): Promise<NextResponse> {
  const chartId = req.nextUrl.searchParams.get('chart_id')
  if (!chartId) {
    return NextResponse.json({ error: 'chart_id required' }, { status: 400 })
  }

  const user = await getServerUser()
  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // Query pyramid_layers table for this chart
  const result = await query<{ layer: string; sublayer: string | null; status: string | null }>(
    `SELECT layer, sublayer, status
     FROM pyramid_layers
     WHERE chart_id = $1
     ORDER BY layer, sublayer`,
    [chartId],
  )

  // Group rows by layer
  const byLayer: Record<string, Asset[]> = {}
  for (const l of LAYER_ORDER) byLayer[l] = []

  for (const row of result.rows) {
    const key = (row.layer ?? '').toUpperCase()
    const bucket = byLayer[key]
    if (bucket) {
      bucket.push({
        asset_key: row.sublayer ?? '',
        status: normalizeStatus(row.status),
      })
    }
  }

  const layers: Layer[] = LAYER_ORDER.map((l) => {
    const assets = byLayer[l]
    return {
      layer: l,
      name: `${LAYER_NAMES[l]?.sanskrit ?? l} — ${LAYER_NAMES[l]?.english ?? ''}`,
      status: deriveLayerStatus(assets),
      asset_count: assets.length,
      assets,
    }
  })

  return NextResponse.json({ chart_id: chartId, layers })
}

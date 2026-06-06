'use client'

import { useAssetRegistry } from '@/hooks/useAssetRegistry'
import { useAssetStats } from '@/hooks/useAssetStats'
import { useActiveRun } from '@/hooks/useActiveRun'
import { LayerPanel } from './LayerPanel'

const LAYER_ORDER = [
  'brahmagyan',
  'ganita',
  'bodha',
  'kala',
  'phala',
  'mimamsa',
] as const

const LAYER_SANSKRIT: Record<string, string> = {
  brahmagyan: 'Brahmagyan',
  ganita: 'Gaṇita',
  bodha: 'Bodha',
  kala: 'Kāla',
  phala: 'Phala',
  mimamsa: 'Mīmāṃsā',
}

interface Props {
  chartId: string
}

export function DataAssetsView({ chartId }: Props) {
  const { assets, isLoading, error } = useAssetRegistry()
  const { stats } = useAssetStats({ chartId })
  const { run: activeRun, refresh: refreshRun } = useActiveRun(chartId)

  if (isLoading && assets.length === 0) {
    return (
      <div
        style={{
          padding: '32px 24px',
          color: 'var(--on-dark-mut)',
          fontFamily: 'var(--ui-stack)',
          fontSize: '14px',
        }}
      >
        Loading assets…
      </div>
    )
  }

  if (error) {
    return (
      <div
        style={{
          padding: '32px 24px',
          color: 'var(--marsys-error)',
          fontFamily: 'var(--ui-stack)',
          fontSize: '14px',
        }}
      >
        Failed to load registry: {error}
      </div>
    )
  }

  // Group assets by layer in canonical order
  const byLayer = new Map<string, typeof assets>()
  for (const layer of LAYER_ORDER) byLayer.set(layer, [])

  for (const asset of assets) {
    const bucket = byLayer.get(asset.layer)
    if (bucket) bucket.push(asset)
    else byLayer.set(asset.layer, [asset])
  }

  // Build display order: canonical layers first, then any extras
  const orderedLayers: string[] = [
    ...LAYER_ORDER.filter((l) => (byLayer.get(l)?.length ?? 0) > 0),
    ...[...byLayer.keys()].filter(
      (l) => !LAYER_ORDER.includes(l as (typeof LAYER_ORDER)[number])
    ),
  ]

  return (
    <div style={{ padding: '8px 0' }}>
      {orderedLayers.map((layer) => {
        const layerAssets = byLayer.get(layer) ?? []
        return (
          <LayerPanel
            key={layer}
            layer={layer}
            sanskritName={LAYER_SANSKRIT[layer] ?? layer}
            assets={layerAssets}
            stats={stats}
            defaultExpanded={layer === 'bodha'}
            chartId={chartId}
            activeRun={activeRun}
            onRunStarted={refreshRun}
          />
        )
      })}
    </div>
  )
}

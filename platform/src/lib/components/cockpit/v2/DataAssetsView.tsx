'use client'

import { useCallback, useRef, useState } from 'react'
import { useAssetRegistry } from '@/hooks/useAssetRegistry'
import { useAssetStats } from '@/hooks/useAssetStats'
import { useActiveRun } from '@/hooks/useActiveRun'
import { LayerPanel } from './LayerPanel'
import { LiveDependencyGraph } from './LiveDependencyGraph'
import type { AssetWithState } from './LiveDependencyGraph'

const LAYER_ORDER = [
  'brahmagyan',
  'ganita',
  'bodha',
  'kala',
  'phala',
  'mimamsa',
] as const

interface Props {
  chartId: string
}

export function DataAssetsView({ chartId }: Props) {
  const { assets, isLoading, error } = useAssetRegistry()
  const { stats } = useAssetStats({ chartId })
  const { run: activeRun, refresh: refreshRun } = useActiveRun(chartId)
  const [focusedAssetId, setFocusedAssetId] = useState<string | null>(null)
  const layerRefs = useRef<Map<string, HTMLDivElement>>(new Map())

  const handleNodeClick = useCallback((assetId: string) => {
    const asset = assets.find(a => a.asset_id === assetId)
    if (!asset) return
    setFocusedAssetId(assetId)
    // Scroll the LayerPanel into view
    const el = layerRefs.current.get(asset.layer)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    // Clear highlight after 1.5s
    setTimeout(() => setFocusedAssetId(null), 1500)
  }, [assets])

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

  // Merge assets + stats into AssetWithState for LiveDependencyGraph
  const assetsWithState: AssetWithState[] = assets.map(a => {
    const s = stats.get(a.asset_id)
    return {
      ...a,
      state: s?.state ?? null,
      last_built_at: s?.last_built_at ?? null,
      actual_rows: s?.actual_rows ?? null,
    }
  })

  // Auto-expand layers that have an active run in scope
  const activeRunPlan: string[] = activeRun?.plan ?? []
  function isLayerExpanded(layer: string): boolean {
    if (!activeRun) return false
    if (activeRun.scope === 'layer' && activeRun.scope_target === layer) return true
    if (activeRun.scope === 'global' && activeRunPlan.some(id => id.startsWith(layer + '.'))) return true
    return false
  }

  return (
    <div style={{ display: 'flex', gap: '24px', padding: '8px 0', alignItems: 'flex-start' }}>
      {/* 60% — layer panels */}
      <div style={{ flex: '0 0 60%', minWidth: 0 }}>
        {orderedLayers.map((layer) => {
          const layerAssets = byLayer.get(layer) ?? []
          const focusedInLayer = focusedAssetId != null && layerAssets.some(a => a.asset_id === focusedAssetId)
          return (
            <div
              key={layer}
              ref={el => { if (el) layerRefs.current.set(layer, el) }}
            >
              <LayerPanel
                layer={layer}
                assets={layerAssets}
                stats={stats}
                defaultExpanded={isLayerExpanded(layer)}
                forceExpand={focusedInLayer}
                focusedAssetId={focusedAssetId}
                chartId={chartId}
                activeRun={activeRun}
                onRunStarted={refreshRun}
              />
            </div>
          )
        })}
      </div>

      {/* 40% — Live dependency graph */}
      <div style={{ flex: '0 0 40%', minWidth: 0, position: 'sticky', top: '24px' }}>
        <LiveDependencyGraph
          assets={assetsWithState}
          activeRun={activeRun}
          onNodeClick={handleNodeClick}
        />
      </div>
    </div>
  )
}

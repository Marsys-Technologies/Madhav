'use client'

/**
 * CockpitShell — v2 build cockpit container.
 *
 * Assembles the four visual contract components per VISUAL_CONTRACT v2
 * §C-S8.5 wiring spec:
 *   LiveDependencyGraph  [C-S3]  — force-graph DAG with SSE node/edge events
 *   OverallProgress      [C-S5]  — Sampurna gati progress bar
 *   TelemetryStrip       [C-S6]  — QPS / writers / queue / sidecar / build-id
 *   AssetTable           [C-S7]  — per-layer asset rows with rebuild actions
 *   LayerTower           [WS1-S2/D] — bottom-up L0–L5 tower with pip rail
 *   AssetInspector       [WS1-S2/F] — right-panel asset detail inspector
 *
 * Polls /api/build/active every 10 s to obtain the active build for this
 * chart. Each child component degrades gracefully in the pre-build zero state.
 */

import { useState, useEffect, useCallback } from 'react'
import { LiveDependencyGraph } from './LiveDependencyGraph'
import { OverallProgress } from './OverallProgress'
import { TelemetryStrip } from './TelemetryStrip'
import { AssetTable } from './AssetTable'
import { BuildControlsBar } from './BuildControlsBar'
import { LayerTower, type Layer } from '@/components/brahma/LayerTower'
import { AssetInspector } from '@/components/brahma/AssetInspector'

interface ActiveBuild {
  build_id: string
  chart_id: string
  status: string
}

export function CockpitShell({ chartId }: { chartId: string }) {
  const [build, setBuild] = useState<ActiveBuild | null>(null)
  const [layers, setLayers] = useState<Layer[]>([])
  const [selectedAsset, setSelectedAsset] = useState<string | null>(null)

  const poll = useCallback(async () => {
    const res = await fetch('/api/build/active').catch(() => null)
    if (!res?.ok) return
    const data = (await res.json()) as ActiveBuild[]
    setBuild(data.find((b) => b.chart_id === chartId) ?? null)
  }, [chartId])

  // Fetch pyramid layers for the tower
  const fetchLayers = useCallback(async () => {
    const res = await fetch(`/api/build/pyramid-layers?chart_id=${chartId}`).catch(() => null)
    if (!res?.ok) return
    const data = (await res.json()) as { chart_id: string; layers: Layer[] }
    setLayers(data.layers ?? [])
  }, [chartId])

  useEffect(() => {
    void poll()
    void fetchLayers()
    const id = setInterval(() => {
      void poll()
      void fetchLayers()
    }, 10_000)
    return () => clearInterval(id)
  }, [poll, fetchLayers])

  function handleBuildStart(buildId?: string) {
    if (buildId) {
      setBuild({ build_id: buildId, chart_id: chartId, status: 'queued' })
    }
  }

  return (
    <div data-testid="cockpit-shell" className="space-y-4">
      <BuildControlsBar
        chartId={chartId}
        buildId={build?.build_id}
        buildStatus={build?.status}
        onBuildStart={handleBuildStart}
      />

      <OverallProgress
        totalNodes={0}
        completeNodes={0}
        perAyanamsha={[]}
      />

      <div data-testid="live-dependency-graph">
        <LiveDependencyGraph buildId={build?.build_id ?? null} />
      </div>

      <TelemetryStrip
        qps={0}
        activeWriters={0}
        queueDepth={0}
        sidecarHealthy={false}
        buildId={build?.build_id ?? ''}
      />

      {/* Layer tower — bottom-up L0→L5 with pip rail */}
      <div data-testid="layer-tower-section">
        <LayerTower
          layers={layers}
          onAssetClick={setSelectedAsset}
          selectedAsset={selectedAsset}
        />
      </div>

      {/* Asset inspector — right-panel detail; opens on pip click */}
      {selectedAsset && (
        <AssetInspector
          chartId={chartId}
          assetKey={selectedAsset}
          onClose={() => setSelectedAsset(null)}
        />
      )}

      <AssetTable
        buildId={build?.build_id ?? ''}
        chartId={chartId}
        assets={[]}
      />
    </div>
  )
}

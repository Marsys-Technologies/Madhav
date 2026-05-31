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

interface ActiveBuild {
  build_id: string
  chart_id: string
  status: string
}

export function CockpitShell({ chartId }: { chartId: string }) {
  const [build, setBuild] = useState<ActiveBuild | null>(null)

  const poll = useCallback(async () => {
    const res = await fetch('/api/build/active').catch(() => null)
    if (!res?.ok) return
    const data = (await res.json()) as ActiveBuild[]
    setBuild(data.find((b) => b.chart_id === chartId) ?? null)
  }, [chartId])

  useEffect(() => {
    void poll()
    const id = setInterval(() => void poll(), 10_000)
    return () => clearInterval(id)
  }, [poll])

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

      <AssetTable
        buildId={build?.build_id ?? ''}
        chartId={chartId}
        assets={[]}
      />
    </div>
  )
}

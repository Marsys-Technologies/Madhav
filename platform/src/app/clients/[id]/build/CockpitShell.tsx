'use client'

/**
 * CockpitShell — client-side wrapper that mounts the full v2 Yantra Chitra
 * cockpit component tree per VISUAL_CONTRACT_v2.md "Page 2".
 *
 * Fetches the active build for this chart (polling /api/build/active every
 * 5s) and passes the buildId down to each v2 component.
 */

import { useState, useEffect, useCallback } from 'react'

import { BuildControlsBar } from '@/components/cockpit/BuildControlsBar'
import { OverallProgress } from '@/components/cockpit/OverallProgress'
import { LiveDependencyGraph } from '@/components/cockpit/LiveDependencyGraph'
import { TelemetryStrip } from '@/components/cockpit/TelemetryStrip'
import { AssetTable } from '@/components/cockpit/AssetTable'
import type { AssetRow } from '@/components/cockpit/AssetTable'
import { useBuildProgress } from '@/hooks/useBuildProgress'

interface ActiveBuildItem {
  build_id?: string
  status?: string
}

interface Props {
  chartId: string
}

const POLL_MS = 5000

export function CockpitShell({ chartId }: Props) {
  const [activeBuildId, setActiveBuildId] = useState<string | null>(null)
  const progress = useBuildProgress(chartId)

  const pollActive = useCallback(async () => {
    try {
      const res = await fetch(`/api/build/active?chart_id=${encodeURIComponent(chartId)}`)
      if (!res.ok) return
      const data: ActiveBuildItem[] | ActiveBuildItem = await res.json()
      const builds = Array.isArray(data) ? data : [data]
      const first = builds[0]?.build_id ?? null
      setActiveBuildId(first)
    } catch {
      // non-fatal — retain last known state
    }
  }, [chartId])

  useEffect(() => {
    pollActive()
    const timer = setInterval(pollActive, POLL_MS)
    return () => clearInterval(timer)
  }, [pollActive])

  const handleBuildStart = (buildId?: string) => {
    if (buildId) setActiveBuildId(buildId)
  }

  // Asset rows are populated via SSE-driven updates; initial state is empty
  // (AssetTable degrades gracefully — shows layer headers with no rows).
  const assets: AssetRow[] = []

  return (
    <div
      data-testid="cockpit-shell"
      style={{
        background: 'var(--obsidian-bg, #070605)',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
        padding: '16px 24px',
      }}
    >
      {/* Header controls bar: Stop · Continue · Rebuild all · Build */}
      <BuildControlsBar
        chartId={chartId}
        buildId={activeBuildId ?? undefined}
        onBuildStart={handleBuildStart}
      />

      {/* Sampurna gati — overall progress bar */}
      <OverallProgress
        totalNodes={progress.totalNodes}
        completeNodes={progress.completeNodes}
        etaSeconds={progress.etaSeconds}
        perAyanamsha={progress.perAyanamsha}
      />

      {/* Yantra Chitra force-graph hero panel */}
      <LiveDependencyGraph buildId={activeBuildId} />

      {/* Telemetry strip below the graph */}
      <TelemetryStrip
        qps={0}
        activeWriters={0}
        queueDepth={0}
        sidecarHealthy={true}
        buildId={activeBuildId ?? ''}
      />

      {/* Per-layer asset table */}
      <AssetTable
        buildId={activeBuildId ?? ''}
        chartId={chartId}
        assets={assets}
      />
    </div>
  )
}

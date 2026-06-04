'use client'

import { useEffect, useState, useRef } from 'react'
import type { ChartBuildState, LayerPip } from '@/lib/roster/types'
import { BRAHMA_LAYER_ORDER, PYRAMID_TO_BRAHMA } from '@/lib/brahma/lexicon'
import type { BrahmaLayerId } from '@/lib/brahma/lexicon'

export type OverallBuildState =
  | 'not-built'
  | 'building'
  | 'built'
  | 'attention'
  | 'failed'

export interface ChartBuildStateResult {
  overall: OverallBuildState
  buildState: ChartBuildState | null
  currentLayer: BrahmaLayerId | null
  currentLayerPercent: number
  layerPips: LayerPip[]
}

interface ActiveBuildRow {
  build_id: string
  chart_id: string
  status: string
  progress_pct: number
  ayanamshas: string[]
  started_at: string | null
  error_summary: string | null
}

interface PyramidLayerRow {
  layer: string
  sublayer: string
  status: string
}

const POLL_INTERVAL_MS = 5_000

export function useChartBuildState(chartId: string): ChartBuildStateResult {
  const [result, setResult] = useState<ChartBuildStateResult>({
    overall: 'not-built',
    buildState: null,
    currentLayer: null,
    currentLayerPercent: 0,
    layerPips: BRAHMA_LAYER_ORDER.map((layer) => ({ layer, state: 'dim' })),
  })
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    let cancelled = false

    async function fetchState() {
      try {
        const [buildRes, layersRes] = await Promise.all([
          fetch(`/api/build/active?chart_id=${chartId}`),
          fetch(`/api/build/pyramid-layers?chart_id=${chartId}`),
        ])

        if (cancelled) return

        const activeBuild: ActiveBuildRow | null = buildRes.ok
          ? ((await buildRes.json()) as ActiveBuildRow[] | null)?.[0] ?? null
          : null

        const layerRows: PyramidLayerRow[] = layersRes.ok
          ? ((await layersRes.json()) as PyramidLayerRow[])
          : []

        const layerPips: LayerPip[] = BRAHMA_LAYER_ORDER.map((brahmaLayer) => {
          const row = layerRows.find(
            (r) => PYRAMID_TO_BRAHMA[`${r.layer}:${r.sublayer}`] === brahmaLayer,
          )
          if (!row) return { layer: brahmaLayer, state: 'dim' as const }
          if (row.status === 'complete') return { layer: brahmaLayer, state: 'lit' as const }
          if (row.status === 'in_progress') return { layer: brahmaLayer, state: 'building' as const }
          return { layer: brahmaLayer, state: 'dim' as const }
        })

        let overall: OverallBuildState = 'not-built'
        let currentLayer: BrahmaLayerId | null = null
        let currentLayerPercent = 0

        if (activeBuild) {
          if (activeBuild.status === 'failed') {
            overall = 'failed'
          } else if (activeBuild.status === 'running' || activeBuild.status === 'queued') {
            overall = 'building'
            const buildingPip = layerPips.find((p) => p.state === 'building')
            currentLayer = buildingPip?.layer ?? null
            currentLayerPercent = activeBuild.progress_pct
          } else if (activeBuild.status === 'complete') {
            overall = layerPips.every((p) => p.state === 'lit') ? 'built' : 'attention'
          }
        } else {
          const litCount = layerPips.filter((p) => p.state === 'lit').length
          if (litCount === 0) overall = 'not-built'
          else if (litCount === BRAHMA_LAYER_ORDER.length) overall = 'built'
          else overall = 'attention'
        }

        const buildState: ChartBuildState | null = activeBuild
          ? {
              build_id: activeBuild.build_id,
              status: activeBuild.status as ChartBuildState['status'],
              progress_pct: activeBuild.progress_pct,
              ayanamshas: activeBuild.ayanamshas,
              started_at: activeBuild.started_at,
              error_summary: activeBuild.error_summary,
            }
          : null

        setResult({ overall, buildState, currentLayer, currentLayerPercent, layerPips })
      } catch {
        // Silently ignore poll errors
      }

      if (!cancelled) {
        timerRef.current = setTimeout(fetchState, POLL_INTERVAL_MS)
      }
    }

    fetchState()
    return () => {
      cancelled = true
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [chartId])

  return result
}

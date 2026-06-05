'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
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

// Fallback polling interval (used when EventSource is unavailable)
const FALLBACK_POLL_INTERVAL_MS = 5_000

// SSE reconnect backoff (1s, 2s, 4s, 8s, 16s, 30s cap)
const SSE_BACKOFF_BASE_MS = 1_000
const SSE_BACKOFF_MAX_MS = 30_000

export function useChartBuildState(chartId: string): ChartBuildStateResult {
  const [result, setResult] = useState<ChartBuildStateResult>({
    overall: 'not-built',
    buildState: null,
    currentLayer: null,
    currentLayerPercent: 0,
    layerPips: BRAHMA_LAYER_ORDER.map((layer) => ({ layer, state: 'dim' })),
  })

  // Ref to the active build_id for SSE subscription
  const activeBuildIdRef = useRef<string | null>(null)
  const esRef = useRef<EventSource | null>(null)
  const backoffRef = useRef<number>(SSE_BACKOFF_BASE_MS)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const fallbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ── Shared state derivation ──────────────────────────────────────────────────

  const deriveState = useCallback(
    (activeBuild: ActiveBuildRow | null, layerRows: PyramidLayerRow[]) => {
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

      // Track active build_id for SSE subscription
      activeBuildIdRef.current = activeBuild?.build_id ?? null
    },
    [],
  )

  // ── Fetch state (used for initial load + fallback polling) ───────────────────

  const fetchState = useCallback(async (): Promise<void> => {
    try {
      const [buildRes, layersRes] = await Promise.all([
        fetch(`/api/build/active?chart_id=${chartId}`),
        fetch(`/api/build/pyramid-layers?chart_id=${chartId}`),
      ])

      const activeBuild: ActiveBuildRow | null = buildRes.ok
        ? ((await buildRes.json()) as ActiveBuildRow[] | null)?.[0] ?? null
        : null

      const layerData = layersRes.ok
        ? ((await layersRes.json()) as { chart_id: string; layers: Array<{ layer: string; assets: Array<{ asset_key: string; status: string }> }> })
        : null

      // Flatten pyramid-layers response into PyramidLayerRow[]
      const layerRows: PyramidLayerRow[] = []
      if (layerData?.layers) {
        for (const l of layerData.layers) {
          for (const a of l.assets) {
            layerRows.push({ layer: l.layer, sublayer: a.asset_key, status: a.status })
          }
        }
      }

      deriveState(activeBuild, layerRows)
    } catch {
      // Silently ignore errors
    }
  }, [chartId, deriveState])

  // ── Re-fetch layers after an SSE event (without re-fetching active build) ───

  const refetchLayers = useCallback(async (): Promise<void> => {
    try {
      const layersRes = await fetch(`/api/build/pyramid-layers?chart_id=${chartId}`)
      if (!layersRes.ok) return

      const layerData = (await layersRes.json()) as {
        chart_id: string
        layers: Array<{ layer: string; assets: Array<{ asset_key: string; status: string }> }>
      }

      const layerRows: PyramidLayerRow[] = []
      for (const l of layerData.layers ?? []) {
        for (const a of l.assets) {
          layerRows.push({ layer: l.layer, sublayer: a.asset_key, status: a.status })
        }
      }

      // Re-derive using the current build state
      setResult((prev) => {
        const activeBuild: ActiveBuildRow | null = prev.buildState
          ? {
              build_id: prev.buildState.build_id,
              chart_id: chartId,
              status: prev.buildState.status,
              progress_pct: prev.buildState.progress_pct,
              ayanamshas: prev.buildState.ayanamshas,
              started_at: prev.buildState.started_at,
              error_summary: prev.buildState.error_summary,
            }
          : null

        const layerPips: LayerPip[] = BRAHMA_LAYER_ORDER.map((brahmaLayer) => {
          const row = layerRows.find(
            (r) => PYRAMID_TO_BRAHMA[`${r.layer}:${r.sublayer}`] === brahmaLayer,
          )
          if (!row) return { layer: brahmaLayer, state: 'dim' as const }
          if (row.status === 'complete' || row.status === 'built')
            return { layer: brahmaLayer, state: 'lit' as const }
          if (row.status === 'in_progress' || row.status === 'building')
            return { layer: brahmaLayer, state: 'building' as const }
          return { layer: brahmaLayer, state: 'dim' as const }
        })

        let overall: OverallBuildState = prev.overall
        if (activeBuild?.status === 'complete') {
          overall = layerPips.every((p) => p.state === 'lit') ? 'built' : 'attention'
        }

        return { ...prev, layerPips, overall }
      })
    } catch {
      // Silently ignore
    }
  }, [chartId])

  // ── SSE subscription ─────────────────────────────────────────────────────────

  const openSSE = useCallback(
    (buildId: string) => {
      if (esRef.current) {
        esRef.current.close()
        esRef.current = null
      }

      const es = new EventSource(`/api/build/events/${buildId}`)
      esRef.current = es

      es.addEventListener('message', () => {
        // Each SSE message = a build_event row arrived; re-fetch pyramid layers
        void refetchLayers()
        backoffRef.current = SSE_BACKOFF_BASE_MS // reset backoff on successful message
      })

      es.addEventListener('done', () => {
        // Build finished; do a final full fetch then close
        void fetchState()
        es.close()
        esRef.current = null
      })

      es.onerror = () => {
        es.close()
        esRef.current = null

        // Exponential backoff reconnect
        const delay = backoffRef.current
        backoffRef.current = Math.min(backoffRef.current * 2, SSE_BACKOFF_MAX_MS)

        reconnectTimerRef.current = setTimeout(() => {
          // Only reconnect if build is still active
          if (activeBuildIdRef.current === buildId) {
            openSSE(buildId)
          }
        }, delay)
      }
    },
    [fetchState, refetchLayers],
  )

  // ── Main effect ──────────────────────────────────────────────────────────────

  useEffect(() => {
    let cancelled = false

    // Check EventSource availability (may be undefined in SSR / some envs)
    const hasEventSource = typeof EventSource !== 'undefined'

    async function init() {
      await fetchState()
      if (cancelled) return

      if (!hasEventSource) {
        // Fallback: 5s polling
        const schedulePoll = () => {
          fallbackTimerRef.current = setTimeout(async () => {
            if (cancelled) return
            await fetchState()
            schedulePoll()
          }, FALLBACK_POLL_INTERVAL_MS)
        }
        schedulePoll()
        return
      }

      // If we have an active build, open SSE
      if (activeBuildIdRef.current) {
        openSSE(activeBuildIdRef.current)
      }

      // Poll /api/build/active every 10s to detect new builds starting
      const activePollId = setInterval(async () => {
        if (cancelled) return
        const prevBuildId = activeBuildIdRef.current
        await fetchState()
        const newBuildId = activeBuildIdRef.current
        // If a new build started, open SSE for it
        if (newBuildId && newBuildId !== prevBuildId && !esRef.current) {
          openSSE(newBuildId)
        }
      }, 10_000)

      // Store for cleanup
      ;(init as { _pollId?: ReturnType<typeof setInterval> })._pollId = activePollId
    }

    const initRef = init as typeof init & { _pollId?: ReturnType<typeof setInterval> }
    void init()

    return () => {
      cancelled = true
      if (initRef._pollId) clearInterval(initRef._pollId)
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
      if (fallbackTimerRef.current) clearTimeout(fallbackTimerRef.current)
      if (esRef.current) {
        esRef.current.close()
        esRef.current = null
      }
    }
  }, [chartId, fetchState, openSSE])

  return result
}

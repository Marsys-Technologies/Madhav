'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import type { AssetStats } from '@/app/api/cockpit/stats/route'

export type { AssetStats }

export function useAssetStats({
  chartId,
  isBuilding = false,
}: {
  chartId: string
  isBuilding?: boolean
}): {
  stats: Map<string, AssetStats>
  lastFetched: Date | null
  error: string | null
  refetch: () => void
  refetchLive: () => void
} {
  const [stats, setStats] = useState<Map<string, AssetStats>>(new Map())
  const [lastFetched, setLastFetched] = useState<Date | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inFlightRef = useRef(false)

  const fetchStats = useCallback(
    async (signal: AbortSignal, liveMode = false) => {
      if (inFlightRef.current) { console.log('[AS] skipping — in flight'); return }
      inFlightRef.current = true
      const modeParam = liveMode ? '&mode=live' : ''
      console.log('[AS] fetching stats for chartId=', chartId, liveMode ? '(live)' : '')
      try {
        const r = await fetch(
          `/api/cockpit/stats?chart_id=${encodeURIComponent(chartId)}${modeParam}`,
          { credentials: 'include', signal }
        )
        console.log('[AS] fetch returned, ok=', r.ok, 'aborted=', signal.aborted)
        if (signal.aborted) return
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const json = await r.json()
        const list: AssetStats[] = json?.data?.assets ?? []
        console.log('[AS] parsed', list.length, 'stats entries')
        const map = new Map<string, AssetStats>()
        for (const a of list) map.set(a.asset_id, a)
        setStats(map)
        setLastFetched(new Date())
        setError(null)
        console.log('[AS] setStats called')
      } catch (e) {
        console.log('[AS] catch:', (e as Error)?.name, (e as Error)?.message)
        if (signal.aborted) return
        if ((e as Error)?.name === 'AbortError') return
        setError((e as Error)?.message ?? 'Failed to fetch stats')
      } finally {
        inFlightRef.current = false
      }
    },
    [chartId]
  )

  useEffect(() => {
    console.log('[AS] effect start, isBuilding=', isBuilding)
    const controller = new AbortController()
    inFlightRef.current = false

    fetchStats(controller.signal)
    const pollMs = isBuilding ? 5_000 : 30_000
    const id = setInterval(() => fetchStats(controller.signal), pollMs)

    return () => {
      console.log('[AS] cleanup, aborting')
      controller.abort()
      clearInterval(id)
      inFlightRef.current = false
    }
  }, [fetchStats, isBuilding])

  // Expose a one-shot refetch for callers that need to force an immediate poll
  // (e.g. after a run ends so the cleared SSE overlay is backfilled at once).
  const refetch = useCallback(() => {
    const controller = new AbortController()
    fetchStats(controller.signal)
  }, [fetchStats])

  // Live-mode refetch: bypasses the rows_written shortcut for global assets so count_sql runs.
  // Used by the global Refresh path (C2 native ruling — live count on explicit Refresh).
  const refetchLive = useCallback(() => {
    const controller = new AbortController()
    fetchStats(controller.signal, true)
  }, [fetchStats])

  return { stats, lastFetched, error, refetch, refetchLive }
}

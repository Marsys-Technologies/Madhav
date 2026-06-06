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
} {
  const [stats, setStats] = useState<Map<string, AssetStats>>(new Map())
  const [lastFetched, setLastFetched] = useState<Date | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inFlightRef = useRef(false)

  const fetchStats = useCallback(
    async (signal: AbortSignal) => {
      if (inFlightRef.current) { console.log('[AS] skipping — in flight'); return }
      inFlightRef.current = true
      console.log('[AS] fetching stats for chartId=', chartId)
      try {
        const r = await fetch(
          `/api/cockpit/stats?chart_id=${encodeURIComponent(chartId)}`,
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

  return { stats, lastFetched, error }
}

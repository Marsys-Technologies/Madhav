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
      if (inFlightRef.current) return
      inFlightRef.current = true
      try {
        const r = await fetch(
          `/api/cockpit/stats?chart_id=${encodeURIComponent(chartId)}`,
          { credentials: 'include', signal }
        )
        if (signal.aborted) return
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const json = await r.json()
        const list: AssetStats[] = json?.data?.assets ?? []
        const map = new Map<string, AssetStats>()
        for (const a of list) map.set(a.asset_id, a)
        setStats(map)
        setLastFetched(new Date())
        setError(null)
      } catch (e) {
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
    const controller = new AbortController()
    inFlightRef.current = false

    fetchStats(controller.signal)
    const pollMs = isBuilding ? 5_000 : 30_000
    const id = setInterval(() => fetchStats(controller.signal), pollMs)

    return () => {
      controller.abort()
      clearInterval(id)
      inFlightRef.current = false
    }
  }, [fetchStats, isBuilding])

  return { stats, lastFetched, error }
}

'use client'

import { useState, useEffect, useRef } from 'react'
import type { AssetStats } from '@/app/api/cockpit/stats/route'

export type { AssetStats }

interface UseAssetStatsProps {
  chartId: string
  isBuilding?: boolean
}

export function useAssetStats({ chartId, isBuilding = false }: UseAssetStatsProps): {
  stats: Map<string, AssetStats>
  lastFetched: Date | null
  error: string | null
} {
  const [stats, setStats] = useState<Map<string, AssetStats>>(new Map())
  const [lastFetched, setLastFetched] = useState<Date | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Track in-flight fetch to prevent overlap
  const inFlightRef = useRef(false)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval>

    const fetchStats = async () => {
      // Skip if previous fetch still in flight
      if (inFlightRef.current) return

      // Cancel any previous request
      if (abortRef.current) {
        abortRef.current.abort()
      }
      const controller = new AbortController()
      abortRef.current = controller

      inFlightRef.current = true
      try {
        const res = await fetch(
          `/api/cockpit/stats?chart_id=${encodeURIComponent(chartId)}`,
          { signal: controller.signal }
        )
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const json = await res.json()
        const assets: AssetStats[] = json?.data?.assets ?? []
        const map = new Map<string, AssetStats>()
        for (const a of assets) map.set(a.asset_id, a)
        setStats(map)
        setLastFetched(new Date())
        setError(null)
      } catch (err) {
        if ((err as Error).name === 'AbortError') return
        setError((err as Error).message ?? 'Failed to fetch stats')
      } finally {
        inFlightRef.current = false
      }
    }

    // Fetch immediately on mount / when building state changes
    fetchStats()

    // Poll at different rates depending on build state
    const pollMs = isBuilding ? 5_000 : 30_000
    intervalId = setInterval(fetchStats, pollMs)

    return () => {
      clearInterval(intervalId)
      if (abortRef.current) abortRef.current.abort()
      inFlightRef.current = false
    }
  }, [chartId, isBuilding])

  return { stats, lastFetched, error }
}

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
  const statsRef = useRef(new Map<string, AssetStats>())
  const controllersRef = useRef<AbortController[]>([])

  const fetchStats = useCallback(
    async (signal: AbortSignal, liveMode = false, force = false) => {
      // Idle polls coalesce (skip if one is already running) to avoid pile-ups, but an
      // explicit refetch after a mutation (clear/build/run-complete) must NEVER be dropped —
      // otherwise the tracker keeps showing pre-action numbers until the next poll. force=true
      // bypasses the in-flight guard so post-action refreshes always reach the DB.
      if (inFlightRef.current && !force) return
      inFlightRef.current = true
      const modeParam = liveMode ? '&mode=live' : ''
      try {
        const r = await fetch(
          `/api/cockpit/stats?chart_id=${encodeURIComponent(chartId)}${modeParam}`,
          { credentials: 'include', signal }
        )
        if (signal.aborted) return
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const json = await r.json()
        const list: AssetStats[] = json?.data?.assets ?? []
        const map = new Map<string, AssetStats>()
        for (const a of list) map.set(a.asset_id, a)

        // Only update state if something actually changed to avoid unnecessary re-renders
        const prevStats = statsRef.current
        let changed = map.size !== prevStats.size
        if (!changed) {
          for (const [id, a] of map) {
            const prev = prevStats.get(id)
            if (!prev || prev.actual_rows !== a.actual_rows || prev.state !== a.state || prev.build_state_stale !== a.build_state_stale) {
              changed = true
              break
            }
          }
        }
        if (changed) {
          statsRef.current = map
          setStats(map)
        }
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
    const pollMs = isBuilding ? 2_000 : 30_000
    const id = setInterval(() => fetchStats(controller.signal), pollMs)

    return () => {
      controller.abort()
      controllersRef.current.forEach(c => c.abort())
      controllersRef.current = []
      clearInterval(id)
      inFlightRef.current = false
    }
  }, [fetchStats, isBuilding])

  // Expose a one-shot refetch for callers that need to force an immediate poll
  // (e.g. after a run ends so the cleared SSE overlay is backfilled at once).
  // force=true so it is never dropped by the in-flight guard.
  const refetch = useCallback(() => {
    const controller = new AbortController()
    controllersRef.current.push(controller)
    fetchStats(controller.signal, false, true)
  }, [fetchStats])

  // Live-mode refetch: bypasses the rows_written shortcut for global assets so count_sql runs
  // and the displayed counts match the live DB (a stale rows_written cache otherwise lingers,
  // e.g. a global asset whose table was emptied out-of-band). Used by the global Refresh path
  // AND every post-mutation refresh (clear/build/run-complete) so the tracker reflects the DB.
  // force=true so it is never dropped by the in-flight guard.
  const refetchLive = useCallback(() => {
    const controller = new AbortController()
    controllersRef.current.push(controller)
    fetchStats(controller.signal, true, true)
  }, [fetchStats])

  return { stats, lastFetched, error, refetch, refetchLive }
}

'use client'

/**
 * useBuildProgress — polls /api/build/active?chart_id=X every 5s and
 * returns aggregated progress statistics.
 *
 * [C-S5]
 */

import { useState, useEffect, useRef, useCallback } from 'react'

export interface AyanamshaProgress {
  id: string
  complete: number
  total: number
}

export interface BuildProgressState {
  totalNodes: number
  completeNodes: number
  etaSeconds?: number
  perAyanamsha: AyanamshaProgress[]
  loading: boolean
}

const POLL_INTERVAL_MS = 5000
const INITIAL: BuildProgressState = {
  totalNodes: 0,
  completeNodes: 0,
  perAyanamsha: [],
  loading: true,
}

interface ActiveBuildResponse {
  build_id?: string
  total_nodes?: number
  complete_nodes?: number
  eta_seconds?: number
  per_ayanamsha?: AyanamshaProgress[]
}

export function useBuildProgress(chartId: string | null): BuildProgressState {
  const [state, setState] = useState<BuildProgressState>(INITIAL)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchProgress = useCallback(async () => {
    if (!chartId) return
    try {
      const res = await fetch(`/api/build/active?chart_id=${encodeURIComponent(chartId)}`)
      if (!res.ok) return
      const data: ActiveBuildResponse = await res.json()
      setState({
        totalNodes:    data.total_nodes    ?? 0,
        completeNodes: data.complete_nodes ?? 0,
        etaSeconds:    data.eta_seconds,
        perAyanamsha:  data.per_ayanamsha  ?? [],
        loading: false,
      })
    } catch {
      // network error — retain last known state, don't crash
    }
  }, [chartId])

  useEffect(() => {
    if (!chartId) {
      setState(INITIAL)
      return
    }

    fetchProgress()
    timerRef.current = setInterval(fetchProgress, POLL_INTERVAL_MS)

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [chartId, fetchProgress])

  return state
}

'use client'

/**
 * useChartList — loads charts accessible to the current user.
 *
 * Calls GET /api/panchang/charts which reads from the `charts` table
 * filtered by the Firebase-authenticated user's profile (RLS enforced
 * server-side: astrologer sees all; client sees own chart only).
 *
 * Returns { charts, isLoading, error }.
 *
 * Phase: 4C-5 (Item 3)
 */

import { useEffect, useState } from 'react'

export interface ChartSummary {
  id: string
  name: string
  birth_date: string   // YYYY-MM-DD
  birth_place: string
  client_id: string
}

interface UseChartListResult {
  charts: ChartSummary[]
  isLoading: boolean
  error: string | null
}

export function useChartList(): UseChartListResult {
  const [charts, setCharts] = useState<ChartSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)

    fetch('/api/panchang/charts')
      .then(async (res) => {
        if (!res.ok) {
          if (res.status === 401) throw new Error('Not authenticated')
          throw new Error(`Failed to load charts (HTTP ${res.status})`)
        }
        const data = await res.json() as { charts: ChartSummary[] }
        return data.charts ?? []
      })
      .then((list) => {
        if (!cancelled) {
          setCharts(list)
          setIsLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load charts')
          setIsLoading(false)
        }
      })

    return () => { cancelled = true }
  }, [])

  return { charts, isLoading, error }
}

'use client'

/**
 * useMuhuratFinder — client-side data hook for the Muhurat Finder.
 *
 * Posts to /api/compute/muhurat (Next.js proxy → Python sidecar).
 * Returns { windows, isLoading, error } with manual trigger via `search()`.
 *
 * Results are cached in state — calling search() again with different params
 * replaces the cache (intentional: user re-submits the form).
 *
 * Phase: 4C-6-S3 (Item 2)
 */

import { useState, useCallback } from 'react'

// ── Types (mirrors sidecar MuhuratWindow response) ───────────────────────────

export interface MuhuratWindow {
  event: string
  /** ISO 8601 UTC — start of the window (sunrise for MVP) */
  start_utc: string | null
  /** ISO 8601 UTC — end of the window (sunset for MVP) */
  end_utc: string | null
  /** Integer 1–5 */
  star_rating: number
  /** Composite score (higher = better) */
  score: number
  /** Key → human label explaining the score contribution */
  breakdown: Record<string, number>
}

export interface MuhuratSearchParams {
  event: string
  date_from: string   // YYYY-MM-DD
  date_to: string     // YYYY-MM-DD
  lat: number
  lon: number
  tz_offset_minutes: number
  chart_id?: string | null
  top_n?: number
}

interface UseMuhuratFinderResult {
  windows: MuhuratWindow[] | null
  isLoading: boolean
  error: string | null
  /** Call this to trigger (or re-trigger) a search with given params. */
  search: (params: MuhuratSearchParams) => Promise<void>
}

export function useMuhuratFinder(): UseMuhuratFinderResult {
  const [windows, setWindows] = useState<MuhuratWindow[] | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = useCallback(async (params: MuhuratSearchParams) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/compute/muhurat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event: params.event,
          date_from: params.date_from,
          date_to: params.date_to,
          lat: params.lat,
          lon: params.lon,
          tz_offset_minutes: params.tz_offset_minutes,
          chart_id: params.chart_id ?? null,
          top_n: params.top_n ?? 10,
        }),
      })

      if (!response.ok) {
        let detail = `Server error (${response.status})`
        try {
          const body = await response.json() as { detail?: string }
          if (body.detail) detail = body.detail
        } catch {
          // ignore JSON parse error; use status string
        }
        setError(detail)
        setWindows(null)
        return
      }

      const data = await response.json() as { ok: boolean; windows: MuhuratWindow[]; count: number }
      setWindows(data.windows)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error — Muhurat engine unreachable')
      setWindows(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  return { windows, isLoading, error, search }
}

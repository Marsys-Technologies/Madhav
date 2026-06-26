'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

export interface ActiveRunAsset {
  asset_id: string
  position: number
  state: string
  started_at: string | null
  ended_at: string | null
  error: string | null
}

export interface ActiveRun {
  id: string
  scope: string
  scope_target: string | null
  action: string
  state: string
  plan: string[]
  current_asset_id: string | null
  created_at: string
  started_at: string | null
  pause_requested_at: string | null
  stop_requested_at: string | null
}

interface UseActiveRunResult {
  run: ActiveRun | null
  assets: ActiveRunAsset[]
  refresh: () => void
}

export function useActiveRun(
  chartId: string,
  options?: { onCompleted?: () => void }
): UseActiveRunResult {
  const [run, setRun] = useState<ActiveRun | null>(null)
  const [assets, setAssets] = useState<ActiveRunAsset[]>([])
  const prevRunRef = useRef<ActiveRun | null>(null)
  const onCompletedRef = useRef(options?.onCompleted)
  onCompletedRef.current = options?.onCompleted

  const fetch_ = useCallback(async () => {
    try {
      const r = await fetch(`/api/cockpit/runs/active?chart_id=${chartId}`, {
        credentials: 'include',
        cache: 'no-store',
      })
      if (!r.ok) return
      const body = await r.json()
      const newRun: ActiveRun | null = body.data?.run ?? null
      // Belt-and-suspenders: when an active run transitions to null (terminal),
      // trigger an immediate stats refetch so counts update within the 5s poll
      // cadence even when Pub/Sub SSE is not available (C1-Step2).
      if (prevRunRef.current !== null && newRun === null) {
        onCompletedRef.current?.()
      }
      prevRunRef.current = newRun
      setRun(newRun)
      setAssets(body.data?.assets ?? [])
    } catch {
      // network error — keep last known state
    }
  }, [chartId])

  const isRunning = run !== null
  useEffect(() => {
    fetch_()
    // Always poll at 5s — a build can move from planned→running→completed in seconds,
    // and a 30s interval misses the entire active window before isRunning flips.
    const t = setInterval(fetch_, 5_000)
    return () => clearInterval(t)
  }, [fetch_, isRunning])

  return { run, assets, refresh: fetch_ }
}

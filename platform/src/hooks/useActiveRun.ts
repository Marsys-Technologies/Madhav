'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

export interface ActiveRunAsset {
  asset_id: string
  position: number
  state: string
  started_at: string | null
  ended_at: string | null
  error: string | null
  // Packet B1 (review C-2b): build_run_assets.disposition, read verbatim — never
  // re-derived from `error` text. 'blocked_dependency' means this row is a
  // cascade CONSEQUENCE (an upstream failed/was blocked this run), not this
  // asset's own defect. blocked_by_asset_id (migration 1095) is prospective-only
  // and null in any environment where that column hasn't applied yet.
  disposition: string | null
  blocked_by_asset_id: string | null
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

  useEffect(() => {
    onCompletedRef.current = options?.onCompleted
  }, [options?.onCompleted])

  const fetch_ = useCallback(async (signal?: AbortSignal) => {
    try {
      const r = await fetch(`/api/cockpit/runs/active?chart_id=${chartId}`, {
        credentials: 'include',
        cache: 'no-store',
        signal,
      })
      if (!r.ok || signal?.aborted) return
      const body = await r.json()
      if (signal?.aborted) return
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
    } catch (e) {
      if ((e as Error)?.name === 'AbortError') return
      // network error — keep last known state
    }
  }, [chartId])

  useEffect(() => {
    const controller = new AbortController()
    const initialFetch = setTimeout(() => void fetch_(controller.signal), 0)
    // Poll at 5s during active run, 15s during idle — reduces 24 req/min to 8 req/min at idle
    const isRunning = prevRunRef.current !== null
    const t = setInterval(() => fetch_(controller.signal), isRunning ? 5_000 : 15_000)
    return () => {
      controller.abort()
      clearTimeout(initialFetch)
      clearInterval(t)
    }
  }, [fetch_])

  return { run, assets, refresh: () => fetch_() }
}

'use client'

import { useState, useEffect, useCallback } from 'react'

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

export function useActiveRun(chartId: string): UseActiveRunResult {
  const [run, setRun] = useState<ActiveRun | null>(null)
  const [assets, setAssets] = useState<ActiveRunAsset[]>([])

  const fetch_ = useCallback(async () => {
    try {
      const r = await fetch(`/api/cockpit/runs/active?chart_id=${chartId}`, {
        credentials: 'include',
        cache: 'no-store',
      })
      if (!r.ok) return
      const body = await r.json()
      setRun(body.data?.run ?? null)
      setAssets(body.data?.assets ?? [])
    } catch {
      // network error — keep last known state
    }
  }, [chartId])

  useEffect(() => {
    fetch_()
    const t = setInterval(fetch_, 5_000)
    return () => clearInterval(t)
  }, [fetch_])

  return { run, assets, refresh: fetch_ }
}

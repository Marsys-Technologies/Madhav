'use client'

import { useState, useEffect, useCallback } from 'react'
import type { AssetRow } from '@/app/api/cockpit/registry/route'

export type { AssetRow }

export function useAssetRegistry(): {
  assets: AssetRow[]
  isLoading: boolean
  error: string | null
  refetch: () => void
} {
  const [assets, setAssets] = useState<AssetRow[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  const refetch = useCallback(() => setTick((t) => t + 1), [])

  useEffect(() => {
    console.log('[AR] effect start, tick=', tick)
    const controller = new AbortController()
    let cancelled = false

    setIsLoading(true)
    ;(async () => {
      try {
        console.log('[AR] fetching /api/cockpit/registry')
        const r = await fetch('/api/cockpit/registry', {
          credentials: 'include',
          signal: controller.signal,
        })
        console.log('[AR] fetch returned, ok=', r.ok, 'status=', r.status, 'cancelled=', cancelled)
        if (cancelled) { console.log('[AR] cancelled after fetch'); return }
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const body = await r.json()
        console.log('[AR] body parsed, assets count=', body?.data?.assets?.length, 'cancelled=', cancelled)
        if (cancelled) { console.log('[AR] cancelled after parse'); return }
        setAssets(body?.data?.assets ?? [])
        setError(null)
        console.log('[AR] setAssets called with', body?.data?.assets?.length, 'items')
      } catch (e) {
        console.log('[AR] catch:', (e as Error)?.name, (e as Error)?.message)
        if (cancelled) return
        if ((e as Error)?.name === 'AbortError') return
        setError((e as Error)?.message ?? 'Failed to load registry')
      } finally {
        console.log('[AR] finally, cancelled=', cancelled)
        if (!cancelled) setIsLoading(false)
      }
    })()

    return () => {
      console.log('[AR] cleanup, setting cancelled=true')
      cancelled = true
      controller.abort()
    }
  }, [tick])

  return { assets, isLoading, error, refetch }
}

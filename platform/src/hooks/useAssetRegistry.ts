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
    const controller = new AbortController()
    let cancelled = false

    setIsLoading(true)
    ;(async () => {
      try {
        const r = await fetch('/api/cockpit/registry', {
          credentials: 'include',
          signal: controller.signal,
        })
        if (cancelled) return
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const body = await r.json()
        if (cancelled) return
        setAssets(body?.data?.assets ?? [])
        setError(null)
      } catch (e) {
        if (cancelled) return
        if ((e as Error)?.name === 'AbortError') return
        setError((e as Error)?.message ?? 'Failed to load registry')
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    })()

    return () => {
      cancelled = true
      controller.abort()
    }
  }, [tick])

  return { assets, isLoading, error, refetch }
}

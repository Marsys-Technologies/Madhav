'use client'

import { useState, useEffect, useCallback } from 'react'
import type { AssetRow } from '@/app/api/cockpit/registry/route'

export type { AssetRow }

// Module-level cache with 60s TTL
let _cache: { data: AssetRow[]; ts: number } | null = null

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

  const refetch = useCallback(() => {
    _cache = null
    setTick((t) => t + 1)
  }, [])

  useEffect(() => {
    let cancelled = false

    // Return cached result if fresh
    if (_cache && Date.now() - _cache.ts < 60_000) {
      setAssets(_cache.data)
      setIsLoading(false)
      setError(null)
      return
    }

    setIsLoading(true)

    fetch('/api/cockpit/registry')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((json) => {
        if (cancelled) return
        const data: AssetRow[] = json?.data?.assets ?? []
        _cache = { data, ts: Date.now() }
        setAssets(data)
        setError(null)
      })
      .catch((err: Error) => {
        if (cancelled) return
        setError(err.message ?? 'Failed to load registry')
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => { cancelled = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick])

  return { assets, isLoading, error, refetch }
}

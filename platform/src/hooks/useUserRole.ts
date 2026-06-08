'use client'

import { useState, useEffect } from 'react'

// Module-level cache — all hook instances share one in-flight fetch and one cached result.
// Eliminates the N×/api/me/role calls that occur when many components mount together.
const TTL_MS = 5 * 60 * 1000
let _cached: { role: string; ts: number } | null = null
let _inflight: Promise<string | null> | null = null

function getRole(): Promise<string | null> {
  if (_cached && Date.now() - _cached.ts < TTL_MS) return Promise.resolve(_cached.role)
  if (!_inflight) {
    _inflight = fetch('/api/me/role', { credentials: 'include' })
      .then(r => (r.ok ? r.json() : null))
      .then((body): string | null => {
        const role = body?.role ?? null
        if (role) _cached = { role, ts: Date.now() }
        _inflight = null
        return role
      })
      .catch(() => { _inflight = null; return null })
  }
  return _inflight
}

interface UserRoleState {
  role: string | null
  isSuperAdmin: boolean
  loading: boolean
}

export function useUserRole(): UserRoleState {
  const [role, setRole] = useState<string | null>(_cached?.role ?? null)
  const [loading, setLoading] = useState(!_cached)

  useEffect(() => {
    if (_cached && Date.now() - _cached.ts < TTL_MS) {
      setRole(_cached.role)
      setLoading(false)
      return
    }
    let cancelled = false
    getRole().then(r => {
      if (!cancelled) { setRole(r); setLoading(false) }
    })
    return () => { cancelled = true }
  }, [])

  return { role, isSuperAdmin: role === 'super_admin', loading }
}

'use client'

import { useState, useEffect } from 'react'

interface UserRoleState {
  role: string | null
  isSuperAdmin: boolean
  loading: boolean
}

export function useUserRole(): UserRoleState {
  const [role, setRole] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetch('/api/me/role', { credentials: 'include' })
      .then(r => (r.ok ? r.json() : null))
      .then(body => {
        if (!cancelled) setRole(body?.role ?? null)
      })
      .catch(() => {
        if (!cancelled) setRole(null)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  return { role, isSuperAdmin: role === 'super_admin', loading }
}

'use client'

import { createContext, useContext, useEffect, useMemo, useState } from 'react'

type Scope = 'mine' | 'portal' | 'user'
type Period = 'today' | '7d' | '30d'
interface ObservatoryContext {
  admin: boolean
  userId: string
  scope: Scope
  setScope: (scope: Scope) => void
  selectedUserId: string
  setSelectedUserId: (id: string) => void
  period: Period
  setPeriod: (period: Period) => void
  from: string
  to: string
  endpoint: string
  scopeParams: URLSearchParams
  users: { id: string; name: string }[]
}
const Context = createContext<ObservatoryContext | null>(null)

export function ObservatoryScope({ children, admin, userId }: { children: React.ReactNode; admin: boolean; userId: string }) {
  const [scope, setScope] = useState<Scope>('mine')
  const [selectedUserId, setSelectedUserId] = useState('')
  const [period, setPeriod] = useState<Period>('30d')
  const [users, setUsers] = useState<{ id: string; name: string }[]>([])
  const [clock] = useState(() => Date.now())
  useEffect(() => {
    if (!admin) return
    let cancelled = false
    fetch('/api/admin/users', { cache: 'no-store' }).then(async response => {
      if (!response.ok) return
      const data = await response.json() as { users?: { id: string; name: string | null; username: string | null }[] }
      if (!cancelled) setUsers((data.users ?? []).map(user => ({ id: user.id, name: user.name || user.username || 'Unnamed user' })))
    }).catch(() => {})
    return () => { cancelled = true }
  }, [admin])
  const value = useMemo(() => {
    const now = new Date(clock)
    const from = new Date(clock)
    if (period === 'today') from.setUTCHours(0, 0, 0, 0)
    else from.setUTCDate(from.getUTCDate() - (period === '7d' ? 7 : 30))
    const scopeParams = new URLSearchParams()
    if (admin) {
      if (scope === 'mine') scopeParams.set('userId', userId)
      if (scope === 'user') scopeParams.set('userId', selectedUserId || userId)
    }
    return { admin, userId, scope, setScope, selectedUserId, setSelectedUserId, period, setPeriod,
      from: from.toISOString(), to: now.toISOString(), endpoint: admin ? '/api/admin/observatory/metering' : '/api/usage',
      scopeParams, users }
  }, [admin, userId, scope, selectedUserId, period, clock, users])
  return <Context.Provider value={value}>{children}</Context.Provider>
}

export function useObservatoryScope() {
  const context = useContext(Context)
  if (!context) throw new Error('Observatory scope is missing')
  return context
}

'use client'

import { createContext, useCallback, useContext, useMemo, useState } from 'react'

type DirtyKey = string

interface DirtyRowsValue {
  isDirty: (key: DirtyKey) => boolean
  markDirty: (key: DirtyKey) => void
  dirtyCount: (predicate: (key: DirtyKey) => boolean) => number
}

const DirtyRowsContext = createContext<DirtyRowsValue | null>(null)

export function dirtyKey(stack: string, callType: string, role?: 'primary' | 'fallback' | 'param', param?: string): DirtyKey {
  return [stack, callType, role ?? '*', param ?? ''].join(':')
}

export function DirtyRowsProvider({ children }: { children: React.ReactNode }) {
  const [dirty, setDirty] = useState<Set<DirtyKey>>(() => new Set())

  const isDirty = useCallback((key: DirtyKey) => dirty.has(key), [dirty])

  const markDirty = useCallback((key: DirtyKey) => {
    setDirty(prev => {
      if (prev.has(key)) return prev
      const next = new Set(prev)
      next.add(key)
      return next
    })
  }, [])

  const dirtyCount = useCallback((predicate: (key: DirtyKey) => boolean) => {
    let n = 0
    for (const k of dirty) if (predicate(k)) n++
    return n
  }, [dirty])

  const value = useMemo<DirtyRowsValue>(() => ({ isDirty, markDirty, dirtyCount }), [isDirty, markDirty, dirtyCount])

  return <DirtyRowsContext.Provider value={value}>{children}</DirtyRowsContext.Provider>
}

export function useDirtyRows(): DirtyRowsValue {
  const ctx = useContext(DirtyRowsContext)
  if (!ctx) {
    return {
      isDirty: () => false,
      markDirty: () => undefined,
      dirtyCount: () => 0,
    }
  }
  return ctx
}

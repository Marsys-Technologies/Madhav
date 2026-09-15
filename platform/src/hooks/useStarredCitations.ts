'use client'

import { useCallback, useMemo, useSyncExternalStore } from 'react'

const STARRED_CHANGE_EVENT = 'marsys:starred-citations-change'

function starredKey(conversationId: string | null): string {
  return `marsys_chat_v2_starred_${conversationId ?? '__new__'}`
}

function readFromStorage(key: string): Set<number> {
  if (typeof window === 'undefined') return new Set()
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return new Set()
    const parsed = JSON.parse(raw) as number[]
    return new Set(Array.isArray(parsed) ? parsed : [])
  } catch {
    return new Set()
  }
}

function writeToStorage(key: string, set: Set<number>): void {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(key, JSON.stringify(Array.from(set)))
  } catch {}
}

/**
 * X-S3: Per-conversation citation star persistence via localStorage.
 * Key pattern: marsys_chat_v2_starred_<conversationId>
 * Returns [starredSet, toggleStar].
 * SSR-safe: all localStorage access is guarded.
 */
export function useStarredCitations(
  conversationId: string | null,
): [Set<number>, (index: number) => void] {
  const key = starredKey(conversationId)
  const serialized = useSyncExternalStore(
    (onChange) => {
      window.addEventListener('storage', onChange)
      window.addEventListener(STARRED_CHANGE_EVENT, onChange)
      return () => {
        window.removeEventListener('storage', onChange)
        window.removeEventListener(STARRED_CHANGE_EVENT, onChange)
      }
    },
    () => localStorage.getItem(key) ?? '[]',
    () => '[]',
  )
  const starredSet = useMemo(() => {
    try {
      const parsed = JSON.parse(serialized) as number[]
      return new Set(Array.isArray(parsed) ? parsed : [])
    } catch {
      return new Set<number>()
    }
  }, [serialized])

  const toggleStar = useCallback((n: number) => {
    const next = readFromStorage(key)
    if (next.has(n)) next.delete(n); else next.add(n)
    writeToStorage(key, next)
    window.dispatchEvent(new Event(STARRED_CHANGE_EVENT))
  }, [key])

  return [starredSet, toggleStar]
}

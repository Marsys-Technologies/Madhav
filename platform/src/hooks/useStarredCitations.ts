'use client'

import { useCallback, useEffect, useState } from 'react'

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

  const [starredSet, setStarredSet] = useState<Set<number>>(() =>
    readFromStorage(key)
  )

  // Reload when conversationId changes (switching conversations)
  useEffect(() => {
    setStarredSet(readFromStorage(key))
  }, [key])

  const toggleStar = useCallback((n: number) => {
    setStarredSet(prev => {
      const next = new Set(prev)
      if (next.has(n)) next.delete(n); else next.add(n)
      writeToStorage(key, next)
      return next
    })
  }, [key])

  return [starredSet, toggleStar]
}

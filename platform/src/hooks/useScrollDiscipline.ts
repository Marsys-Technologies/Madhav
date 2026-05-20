'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

interface UseScrollDisciplineReturn {
  isAtBottom: boolean
  unreadCount: number
  sentinelRef: React.RefObject<HTMLDivElement | null>
  incrementUnread: () => void
  resetUnread: () => void
  scrollToBottom: () => void
}

/**
 * X-S6: Scroll discipline via IntersectionObserver on a bottom sentinel element.
 *
 * Mount the returned sentinelRef on an element at the bottom of the scroll container.
 * The observer uses the nearest scrollable ancestor (data-testid="v2-thread-viewport")
 * as root. When the sentinel exits the viewport, the user has scrolled away;
 * auto-scroll should be suppressed and ScrollToBottomButton shown.
 */
export function useScrollDiscipline(): UseScrollDisciplineReturn {
  const [isAtBottom, setIsAtBottom] = useState(true)
  const [unreadCount, setUnreadCount] = useState(0)
  const sentinelRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel) return
    const viewport = sentinel.closest<HTMLElement>('[data-testid="v2-thread-viewport"]')

    const io = new IntersectionObserver(
      ([entry]) => {
        const atBottom = entry.isIntersecting
        setIsAtBottom(atBottom)
        if (atBottom) setUnreadCount(0)
      },
      { root: viewport ?? null, threshold: 0 },
    )
    io.observe(sentinel)
    return () => io.disconnect()
  }, [])

  const incrementUnread = useCallback(() => setUnreadCount((c) => c + 1), [])
  const resetUnread = useCallback(() => setUnreadCount(0), [])

  const scrollToBottom = useCallback(() => {
    const sentinel = sentinelRef.current
    const viewport = sentinel?.closest<HTMLElement>('[data-testid="v2-thread-viewport"]')
    if (viewport) {
      viewport.scrollTo({ top: viewport.scrollHeight, behavior: 'smooth' })
    } else {
      sentinel?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
    setUnreadCount(0)
    setIsAtBottom(true)
  }, [])

  return { isAtBottom, unreadCount, sentinelRef, incrementUnread, resetUnread, scrollToBottom }
}

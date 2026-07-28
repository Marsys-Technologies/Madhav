'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

const BOTTOM_THRESHOLD_PX = 120

/**
 * §5.5 scroll discipline, made structural (§5.8.0 ruling 7): the transcript
 * owns its own scroll container (fixed-height viewport); `overflow-anchor`
 * is disabled on it in the component (not here) so the browser's own
 * anchoring heuristic — the exact thing that shoved carets under tables in
 * the prior builds — never runs. Auto-follow writes `scrollTop` directly on
 * the same rAF as tail paint; there is exactly one writer.
 */
export function useFollowScroll<T extends HTMLElement>() {
  const ref = useRef<T | null>(null)
  const [pinned, setPinned] = useState(true)
  const [showFollowPill, setShowFollowPill] = useState(false)
  const rafRef = useRef<number | null>(null)

  const atBottom = useCallback(() => {
    const el = ref.current
    if (!el) return true
    return el.scrollTop + el.clientHeight >= el.scrollHeight - BOTTOM_THRESHOLD_PX
  }, [])

  const handleScroll = useCallback(() => {
    if (atBottom()) {
      setPinned(true)
      setShowFollowPill(false)
    } else {
      setPinned(false)
    }
  }, [atBottom])

  const handleWheel = useCallback((e: WheelEvent) => {
    if (e.deltaY < 0) setPinned(false)
  }, [])

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.addEventListener('scroll', handleScroll, { passive: true })
    el.addEventListener('wheel', handleWheel, { passive: true })
    el.addEventListener('touchmove', () => setPinned(false), { passive: true })
    return () => {
      el.removeEventListener('scroll', handleScroll)
      el.removeEventListener('wheel', handleWheel)
    }
  }, [handleScroll, handleWheel])

  /** Call on every paint of streaming/new content. Follows only if pinned; else shows the pill. */
  const notifyContentGrew = useCallback(
    (streamingNow: boolean) => {
      if (rafRef.current != null) return
      rafRef.current = requestAnimationFrame(() => {
        rafRef.current = null
        const el = ref.current
        if (!el) return
        if (pinned) {
          el.scrollTop = el.scrollHeight
          setShowFollowPill(false)
        } else if (streamingNow && !atBottom()) {
          setShowFollowPill(true)
        }
      })
    },
    [pinned, atBottom],
  )

  const followToBottom = useCallback(() => {
    setPinned(true)
    const el = ref.current
    if (el) el.scrollTop = el.scrollHeight
    setShowFollowPill(false)
  }, [])

  /** New-turn anchoring (§5.5): place the user's block in the upper third, constant and predictable. */
  const anchorNewTurn = useCallback((turnEl: HTMLElement | null) => {
    const container = ref.current
    if (!container || !turnEl) return
    const containerTop = container.getBoundingClientRect().top
    const turnTop = turnEl.getBoundingClientRect().top
    const offset = turnTop - containerTop
    const targetOffset = container.clientHeight * 0.12
    container.scrollTop += offset - targetOffset
  }, [])

  return { ref, pinned, showFollowPill, notifyContentGrew, followToBottom, anchorNewTurn }
}

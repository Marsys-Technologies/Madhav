'use client'

import { useState, useEffect, useCallback } from 'react'

export type SidebarState =
  | 'collapsed'        // narrow rail; icons only
  | 'hover-expanded'   // expanded on hover; will collapse on mouse-out
  | 'pinned-expanded'  // user clicked pin; stays expanded across sessions
  | 'mobile-closed'    // overlay closed (< 640px)
  | 'mobile-open'      // overlay open; full-width slide-in (< 640px)

const PIN_KEY = 'marsys.consume.sidebar.pinned'

function readPin(): boolean {
  if (typeof window === 'undefined') return false
  return localStorage.getItem(PIN_KEY) === 'true'
}

function writePin(v: boolean): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(PIN_KEY, String(v))
}

export interface UseSidebarStateReturn {
  state: SidebarState
  isExpanded: boolean
  isMobile: boolean
  onMouseEnter: () => void
  onMouseLeave: () => void
  onPinToggle: () => void
  onMobileToggle: () => void
}

/**
 * useSidebarState — 5-state sidebar machine for the consume chat sidebar.
 *
 * CO.4: implements Bug 3.2 fix (hover-expand / click-pin).
 *
 * Desktop (≥ 640px):
 *   collapsed + mouseEnter  → hover-expanded
 *   hover-expanded + mouseLeave → collapsed
 *   any + pinToggle → pinned-expanded
 *   pinned-expanded + pinToggle → collapsed
 *
 * Mobile (< 640px):
 *   mobile-closed + mobileToggle → mobile-open
 *   mobile-open + mobileToggle → mobile-closed
 *   hover events ignored
 *
 * Pin persists via localStorage (key: marsys.consume.sidebar.pinned).
 */
export function useSidebarState(): UseSidebarStateReturn {
  const [isMobile, setIsMobile] = useState(false)
  const [state, setState] = useState<SidebarState>(() => {
    if (typeof window === 'undefined') return 'collapsed'
    const mobile = window.innerWidth < 640
    if (mobile) return 'mobile-closed'
    return readPin() ? 'pinned-expanded' : 'collapsed'
  })

  // Sync isMobile and state on viewport resize.
  useEffect(() => {
    function onResize() {
      const mobile = window.innerWidth < 640
      setIsMobile(mobile)
      setState(prev => {
        if (mobile) {
          if (prev === 'mobile-closed' || prev === 'mobile-open') return prev
          return 'mobile-closed'
        } else {
          if (prev === 'mobile-closed' || prev === 'mobile-open') {
            return readPin() ? 'pinned-expanded' : 'collapsed'
          }
          return prev
        }
      })
    }

    const mq = window.matchMedia('(max-width: 639px)')
    setIsMobile(mq.matches)
    mq.addEventListener('change', onResize)
    return () => mq.removeEventListener('change', onResize)
  }, [])

  const onMouseEnter = useCallback(() => {
    if (isMobile) return
    setState(prev => prev === 'collapsed' ? 'hover-expanded' : prev)
  }, [isMobile])

  const onMouseLeave = useCallback(() => {
    if (isMobile) return
    setState(prev => prev === 'hover-expanded' ? 'collapsed' : prev)
  }, [isMobile])

  const onPinToggle = useCallback(() => {
    if (isMobile) return
    setState(prev => {
      if (prev === 'pinned-expanded') {
        writePin(false)
        return 'collapsed'
      }
      writePin(true)
      return 'pinned-expanded'
    })
  }, [isMobile])

  const onMobileToggle = useCallback(() => {
    setState(prev => {
      if (prev === 'mobile-open') return 'mobile-closed'
      if (prev === 'mobile-closed') return 'mobile-open'
      return prev
    })
  }, [])

  const isExpanded = state === 'hover-expanded' || state === 'pinned-expanded' || state === 'mobile-open'

  return { state, isExpanded, isMobile, onMouseEnter, onMouseLeave, onPinToggle, onMobileToggle }
}

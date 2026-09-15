'use client'

import { useState, useCallback } from 'react'
import { useMediaQuery } from '@/hooks/useMediaQuery'

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
  const isMobile = useMediaQuery('(max-width: 639px)')
  const [desktopState, setDesktopState] = useState<SidebarState>(() =>
    readPin() ? 'pinned-expanded' : 'collapsed'
  )
  const [mobileOpen, setMobileOpen] = useState(false)
  const state: SidebarState = isMobile
    ? (mobileOpen ? 'mobile-open' : 'mobile-closed')
    : desktopState

  const onMouseEnter = useCallback(() => {
    if (isMobile) return
    setDesktopState(prev => prev === 'collapsed' ? 'hover-expanded' : prev)
  }, [isMobile])

  const onMouseLeave = useCallback(() => {
    if (isMobile) return
    setDesktopState(prev => prev === 'hover-expanded' ? 'collapsed' : prev)
  }, [isMobile])

  const onPinToggle = useCallback(() => {
    if (isMobile) return
    setDesktopState(prev => {
      if (prev === 'pinned-expanded') {
        writePin(false)
        return 'collapsed'
      }
      writePin(true)
      return 'pinned-expanded'
    })
  }, [isMobile])

  const onMobileToggle = useCallback(() => {
    setMobileOpen(prev => !prev)
  }, [])

  const isExpanded = state === 'hover-expanded' || state === 'pinned-expanded' || state === 'mobile-open'

  return { state, isExpanded, isMobile, onMouseEnter, onMouseLeave, onPinToggle, onMobileToggle }
}

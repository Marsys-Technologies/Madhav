'use client'

import { useCallback, useState } from 'react'

const STORAGE_KEY = 'pariprashna.sidebar.collapsed'
// Mirrors DockController's own breakpoint constant (`dock/DockController.tsx`)
// so left and right rails collapse at the same viewport width.
const NARROW_VIEWPORT_QUERY = '(max-width: 900px)'

function hasWindow(): boolean {
  return typeof window !== 'undefined'
}

function readRemembered(): boolean | null {
  if (!hasWindow()) return null
  const v = window.localStorage.getItem(STORAGE_KEY)
  if (v === null) return null
  return v === '1'
}

function isNarrowViewport(): boolean {
  if (!hasWindow() || typeof window.matchMedia !== 'function') return false
  return window.matchMedia(NARROW_VIEWPORT_QUERY).matches
}

/**
 * Left-sidebar collapse state (§5.8.0 ruling 3: "collapsible to icons,
 * remembered per user"). Same shape as `dock/DockController.tsx`'s
 * collapse persistence, deliberately duplicated rather than shared: the
 * dock is a React context serving many deeply-nested citation chips, while
 * the sidebar has exactly one consumer (`PariprashnaApp`), so a plain hook
 * is the smaller surface for the same job. Defaults to open on desktop
 * widths and collapsed below the shared narrow-viewport breakpoint, unless
 * a prior visit already recorded an explicit preference.
 */
export function useSidebarCollapse(): { collapsed: boolean; setCollapsed: (next: boolean) => void } {
  const [collapsed, setCollapsedState] = useState<boolean>(() => readRemembered() ?? isNarrowViewport())

  const setCollapsed = useCallback((next: boolean) => {
    setCollapsedState(next)
    if (hasWindow()) {
      window.localStorage.setItem(STORAGE_KEY, next ? '1' : '0')
    }
  }, [])

  return { collapsed, setCollapsed }
}

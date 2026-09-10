'use client'

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

interface ActiveCitation {
  turnId: string
  n: number
}

interface DockControllerValue {
  open: boolean
  setOpen: (open: boolean) => void
  activeCitation: ActiveCitation | null
  /** Mobile only (§9.2): the dock is hidden below the mobile breakpoint, so a chip tap opens a bottom sheet instead. */
  mobileSheetCitation: ActiveCitation | null
  closeMobileSheet: () => void
  openToCitation: (turnId: string, n: number) => void
}

const DockContext = createContext<DockControllerValue | null>(null)

const STORAGE_KEY = 'pariprashna.dock.collapsed'
// matches the approved mockup's `@media(max-width:900px){.dock{display:none}}`.
// P2-close item 5: RightDock.tsx's own `max-[900px]:hidden` Tailwind class is
// the actual enforcement of that rule (this constant alone never hid
// anything — it only ever gated chip-tap routing below). The two MUST stay
// in sync; see RightDock.tsx's own comment for the full account.
const MOBILE_BREAKPOINT_QUERY = '(max-width: 900px)'

function readRememberedCollapsed(): boolean | null {
  if (typeof window === 'undefined') return null
  const v = window.localStorage.getItem(STORAGE_KEY)
  if (v === null) return null
  return v === '1'
}

function isNarrowViewport(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia(MOBILE_BREAKPOINT_QUERY).matches
}

/**
 * Shared controller so a citation chip anywhere in the (deeply nested,
 * per-turn) transcript can deep-link into the right dock without prop
 * drilling. Collapsed/open state is remembered per user (§3.2, §5.8.0
 * ruling 2: "Collapsed by default on smaller widths; remembered per user").
 *
 * Below the mobile breakpoint the dock itself is hidden (§9.1: rails become
 * overlays/hidden on narrow widths) — a chip tap there opens `CitationCard`
 * as a bottom sheet instead (§9.2 "tap-first everywhere… bottom sheet, not
 * popover"), tracked via `mobileSheetCitation` and rendered by
 * `overlay/OverlayLayer`.
 */
export function DockControllerProvider({ children, defaultOpen }: { children: ReactNode; defaultOpen: boolean }) {
  const [open, setOpenState] = useState<boolean>(() => readRememberedCollapsed() ?? defaultOpen)
  const [activeCitation, setActiveCitation] = useState<ActiveCitation | null>(null)
  const [mobileSheetCitation, setMobileSheetCitation] = useState<ActiveCitation | null>(null)

  const setOpen = useCallback((next: boolean) => {
    setOpenState(next)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, next ? '0' : '1')
    }
  }, [])

  const openToCitation = useCallback(
    (turnId: string, n: number) => {
      if (isNarrowViewport()) {
        setMobileSheetCitation({ turnId, n })
        return
      }
      setOpen(true)
      setActiveCitation({ turnId, n })
    },
    [setOpen],
  )

  const closeMobileSheet = useCallback(() => setMobileSheetCitation(null), [])

  const value = useMemo(
    () => ({ open, setOpen, activeCitation, mobileSheetCitation, closeMobileSheet, openToCitation }),
    [open, activeCitation, mobileSheetCitation, setOpen, openToCitation, closeMobileSheet],
  )

  return <DockContext.Provider value={value}>{children}</DockContext.Provider>
}

export function useDockController(): DockControllerValue {
  const ctx = useContext(DockContext)
  if (!ctx) throw new Error('useDockController must be used within DockControllerProvider')
  return ctx
}

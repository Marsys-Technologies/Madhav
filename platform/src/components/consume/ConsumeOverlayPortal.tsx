'use client'

import { useEffect, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { ZoneRoot } from '@/components/shared/ZoneRoot'

/**
 * Renders the consume route's full-viewport overlay as a portal to <body>,
 * escaping any ancestor stacking context or containing block (e.g. AppShell's
 * page-ascend animation). Before mount, renders inline as a fallback so SSR
 * has content and the user doesn't see a blank flash.
 */
export function ConsumeOverlayPortal({ children }: { children: ReactNode }) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true)
  }, [])

  const content = (
    <div className="fixed inset-0 z-50 bg-[oklch(0.07_0.010_70)]">
      <ZoneRoot zone="ink" style={{ height: '100%' }}>
        {children}
      </ZoneRoot>
    </div>
  )

  if (!mounted) return content
  return createPortal(content, document.body)
}

'use client'

import { useEffect, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { ZoneRoot } from '@/components/shared/ZoneRoot'

/**
 * Renders the consume route's full-viewport overlay as a portal to <body>,
 * escaping any ancestor stacking context or containing block (e.g. AppShell's
 * page-ascend animation). Before mount, renders inline as a fallback so SSR
 * has content.
 *
 * The consume layout injects `animation:none!important` on #main-content so
 * that <main> never starts at opacity:0 (which would form a stacking context
 * below z-50, trapping the inline overlay below the AppShellRail).
 */
export function ConsumeOverlayPortal({ children }: { children: ReactNode }) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true)
  }, [])

  const content = (
    <div
      className="fixed inset-0 z-50"
      style={{
        backgroundColor: '#0d0a05',
        backgroundImage:
          'radial-gradient(ellipse at 18% 85%, rgba(212,175,55,0.22) 0%, transparent 50%), radial-gradient(ellipse at 82% 10%, rgba(180,120,40,0.16) 0%, transparent 48%)',
      }}
    >
      <ZoneRoot zone="ink" style={{ height: '100%' }}>
        {children}
      </ZoneRoot>
    </div>
  )

  if (!mounted) return content
  return createPortal(content, document.body)
}

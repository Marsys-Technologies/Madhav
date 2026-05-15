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
        backgroundColor: '#0f0c06',
        /* Single bottom-up glow centred below the page — mirrors Gemini's
           upward-rising warm gradient. Ellipse extends past the bottom edge
           (110% y) so it fans out evenly across the full width. */
        backgroundImage:
          'radial-gradient(ellipse 180% 100% at 30% 115%, rgba(212,175,55,0.55) 0%, rgba(190,130,35,0.28) 25%, rgba(140,90,20,0.10) 50%, transparent 68%)',
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

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
        backgroundColor: '#0a0803',
        backgroundImage: [
          /* bottom-left warm gold pool — primary Gemini-style glow */
          'radial-gradient(ellipse 70% 55% at 8% 92%, rgba(212,175,55,0.42) 0%, rgba(180,120,30,0.20) 35%, transparent 65%)',
          /* top-right amber accent */
          'radial-gradient(ellipse 55% 45% at 90% 6%, rgba(190,130,40,0.28) 0%, rgba(160,100,20,0.10) 40%, transparent 65%)',
          /* centre warm haze to unify */
          'radial-gradient(ellipse 80% 50% at 45% 60%, rgba(160,100,20,0.08) 0%, transparent 70%)',
        ].join(', '),
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

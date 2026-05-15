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
    <div
      className="fixed inset-0 z-50"
      style={{
        backgroundColor: '#0f0c07',
        backgroundImage:
          'radial-gradient(ellipse at 15% 80%, rgba(212,175,55,0.13) 0%, transparent 55%), radial-gradient(ellipse at 85% 15%, rgba(180,120,40,0.09) 0%, transparent 52%)',
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

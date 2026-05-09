'use client'
import * as React from 'react'
import { cn } from '@/lib/utils'

interface LiveDotProps {
  tone?: 'success' | 'gold'
  label?: string
  className?: string
}

/** Pulsing dot used to indicate live / fresh data. Animation is paused
 *  globally by `prefers-reduced-motion: reduce` via the rule in globals.css. */
export function LiveDot({ tone = 'success', label, className }: LiveDotProps) {
  return (
    <span
      role="status"
      aria-label={label ?? 'live'}
      className={cn('inline-flex items-center gap-1.5', className)}
    >
      <span className="obs-live-dot" data-tone={tone === 'gold' ? 'gold' : undefined} />
      {label ? (
        <span className="bt-label uppercase text-[rgba(212,175,55,0.55)]">{label}</span>
      ) : null}
    </span>
  )
}

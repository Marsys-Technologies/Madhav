'use client'
import * as React from 'react'
import { cn } from '@/lib/utils'

export type ObsTone = 'neutral' | 'good' | 'warn' | 'bad' | 'hot'

interface ObsCardProps extends React.HTMLAttributes<HTMLDivElement> {
  tone?: ObsTone
  /** Render an animated conic-gradient outer hairline. Use sparingly — at most
   *  one instance per page. */
  conic?: boolean
  /** Render the slow red alert pulse for over-budget / breach states. */
  alertPulse?: boolean
  /** Padding scale — 'tight' for table-row containers, 'normal' for content. */
  padding?: 'none' | 'tight' | 'normal' | 'roomy'
}

const TONE_CLASS: Record<ObsTone, string> = {
  neutral: 'obs-glow-neutral',
  good: 'obs-glow-good',
  warn: 'obs-glow-warn',
  bad: 'obs-glow-bad',
  hot: 'obs-glow-hot',
}

const PADDING_CLASS = {
  none: '',
  tight: 'p-3',
  normal: 'p-5',
  roomy: 'p-6 sm:p-7',
} as const

export const ObsCard = React.forwardRef<HTMLDivElement, ObsCardProps>(function ObsCard(
  { tone = 'neutral', conic, alertPulse, padding = 'normal', className, children, ...rest },
  ref,
) {
  return (
    <div
      ref={ref}
      className={cn(
        'relative rounded-xl border border-[rgba(var(--brand-gold-rgb),0.14)]',
        'bg-[oklch(0.115_0.012_70)]',
        TONE_CLASS[tone],
        PADDING_CLASS[padding],
        conic && 'obs-hairline-conic',
        alertPulse && 'obs-alert-pulse',
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  )
})

'use client'
import * as React from 'react'
import { cn } from '@/lib/utils'
import { LiveDot } from './LiveDot'

interface ObsHeroProps {
  title: string
  subtitle?: string
  /** Show the Devanagari double-danda accent flanking the title. Use for top-of-page heroes only. */
  devanagari?: boolean
  /** Render the pulsing live-data dot beside the title. */
  live?: boolean
  liveLabel?: string
  /** Right-side slot (date toggles, filters, action buttons). */
  right?: React.ReactNode
  /** Optional bottom slot (e.g., advanced-filters disclosure). */
  bottom?: React.ReactNode
  /** Tone-tinted radial backdrop behind the hero (used for reconciliation banners). */
  tone?: 'neutral' | 'good' | 'warn' | 'bad'
  className?: string
}

const TONE_BG: Record<NonNullable<ObsHeroProps['tone']>, string> = {
  neutral:
    'bg-[radial-gradient(ellipse_80%_60%_at_20%_0%,color-mix(in_oklch,var(--brand-gold)_8%,transparent),transparent_70%)]',
  good:
    'bg-[radial-gradient(ellipse_80%_60%_at_20%_0%,color-mix(in_oklch,var(--status-success)_14%,transparent),transparent_70%)]',
  warn:
    'bg-[radial-gradient(ellipse_80%_60%_at_20%_0%,color-mix(in_oklch,var(--status-warn)_16%,transparent),transparent_70%)]',
  bad:
    'bg-[radial-gradient(ellipse_80%_60%_at_20%_0%,color-mix(in_oklch,var(--status-halt)_16%,transparent),transparent_70%)]',
}

export function ObsHero({
  title,
  subtitle,
  devanagari,
  live,
  liveLabel = 'live',
  right,
  bottom,
  tone = 'neutral',
  className,
}: ObsHeroProps) {
  return (
    <header
      className={cn(
        'relative border-b border-[color-mix(in_oklch,var(--brand-gold)_12%,transparent)] px-6 pt-7 pb-5',
        TONE_BG[tone],
        className,
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <h1
              className={cn(
                'bt-display text-[var(--brand-gold-cream)]',
                devanagari && 'bt-devanagari-rule',
              )}
            >
              {title}
            </h1>
            {live ? <LiveDot label={liveLabel} /> : null}
          </div>
          {subtitle ? (
            <p className="mt-1 text-[12px] text-[rgba(212,175,55,0.55)]">{subtitle}</p>
          ) : null}
        </div>
        {right ? <div className="shrink-0">{right}</div> : null}
      </div>
      {bottom ? <div className="mt-4">{bottom}</div> : null}
    </header>
  )
}

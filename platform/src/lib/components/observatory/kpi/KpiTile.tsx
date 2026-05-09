'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { ObsCard, type ObsTone } from '../shared/ObsCard'
import { Sparkline } from '../shared/Sparkline'

interface BaseProps {
  testId: string
  label: string
  loading?: boolean
  error?: boolean
  onRetry?: () => void
}

export interface KpiTileProps extends BaseProps {
  /** Primary value (formatted). */
  value?: React.ReactNode
  /** Optional secondary line (e.g., p95 underneath p50). */
  secondary?: React.ReactNode
  /** Delta string (e.g., "↓ 3.4%") and its semantic colour. */
  delta?: { text: string; tone: 'good' | 'bad' | 'neutral' } | null
  /** Hover-only tooltip for the entire tile. */
  title?: string
  /** Optional bottom slot for a sparkline / split bar. */
  footer?: React.ReactNode
  /** OBS-UX-S5 additive props ────────────────────────────────────────────── */
  /** Inline sparkline rendered in the lower-right of the tile. */
  sparkline?: number[]
  /** Tile size variant. `hero` enlarges the value to .bt-mega; `default` is .bt-num. */
  size?: 'default' | 'hero'
  /** Apply the gold inner-glow halo — use to mark the most important tile per row. */
  hot?: boolean
  /** Tone-tinted glow on the card. Defaults to neutral. */
  tone?: ObsTone
  /** Color the value text with the gold accent (used by hero cost tile). */
  accent?: boolean
}

const DELTA_TONE_CLASS: Record<'good' | 'bad' | 'neutral', string> = {
  good: 'text-[var(--status-success)]',
  bad: 'text-[var(--status-halt)]',
  neutral: 'text-[rgba(212,175,55,0.55)]',
}

const DELTA_FILL: Record<'good' | 'bad' | 'neutral', 'success' | 'halt' | 'gold'> = {
  good: 'success',
  bad: 'halt',
  neutral: 'gold',
}

export function KpiTile({
  testId,
  label,
  value,
  secondary,
  delta,
  title,
  footer,
  loading,
  error,
  onRetry,
  sparkline,
  size = 'default',
  hot,
  tone,
  accent,
}: KpiTileProps) {
  if (error) {
    return (
      <div
        data-testid={`${testId}-error`}
        role="alert"
        className="flex h-full flex-col justify-between rounded-xl border border-[rgba(var(--status-halt-rgb),0.3)] bg-[rgba(var(--status-halt-rgb),0.08)] p-5"
      >
        <p className="bt-label bt-label-upper text-[rgba(212,175,55,0.55)]">{label}</p>
        <p className="mt-2 text-sm text-[var(--status-halt)]">Failed to load.</p>
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            data-testid={`${testId}-retry`}
            className="mt-2 self-start rounded border border-[rgba(var(--brand-gold-rgb),0.22)] px-2 py-1 text-xs text-[var(--brand-gold-cream)] hover:bg-[rgba(var(--brand-gold-rgb),0.1)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)]"
          >
            Retry
          </button>
        ) : null}
      </div>
    )
  }

  if (loading) {
    return (
      <div
        data-testid={`${testId}-skeleton`}
        aria-busy="true"
        className="flex h-full flex-col rounded-xl border border-[rgba(var(--brand-gold-rgb),0.1)] bg-[oklch(0.115_0.012_70)] p-5"
      >
        <div className="h-3 w-1/2 animate-pulse rounded bg-[rgba(var(--brand-gold-rgb),0.1)]" />
        <div className="mt-4 h-8 w-3/4 animate-pulse rounded bg-[rgba(var(--brand-gold-rgb),0.1)]" />
        <div className="mt-2 h-3 w-1/3 animate-pulse rounded bg-[rgba(var(--brand-gold-rgb),0.08)]" />
      </div>
    )
  }

  const resolvedTone: ObsTone = hot ? 'hot' : tone ?? 'neutral'

  // Decide the value typography. .bt-mega for hero size; .bt-num for default.
  const valueClass = cn(
    'mt-2 leading-tight',
    size === 'hero' ? 'bt-mega' : 'bt-num',
    accent ? 'text-[var(--brand-gold)]' : 'text-[var(--brand-gold-cream)]',
  )

  return (
    <ObsCard
      tone={resolvedTone}
      padding="normal"
      className={cn('flex h-full flex-col justify-between', hot && 'min-h-[140px]')}
      data-testid={testId}
      title={title}
    >
      <div>
        <p className="bt-label bt-label-upper text-[rgba(212,175,55,0.55)]">{label}</p>
        <p data-testid={`${testId}-value`} className={valueClass}>
          {value}
        </p>
        {secondary ? (
          <p
            data-testid={`${testId}-secondary`}
            className="mt-1.5 text-[12px] text-[rgba(212,175,55,0.55)]"
          >
            {secondary}
          </p>
        ) : null}
      </div>
      <div className="mt-3 flex items-end justify-between gap-3">
        {delta ? (
          <span
            data-testid={`${testId}-delta`}
            data-tone={delta.tone}
            className={cn('text-xs font-medium tabular-nums', DELTA_TONE_CLASS[delta.tone])}
          >
            {delta.text}
          </span>
        ) : (
          <span />
        )}
        <div className="flex items-end gap-2">
          {sparkline && sparkline.length >= 2 ? (
            <Sparkline
              values={sparkline}
              fill={delta ? DELTA_FILL[delta.tone] : 'gold'}
              ariaLabel={`${label} trend`}
              width={88}
              height={26}
            />
          ) : null}
          {footer ? (
            <div data-testid={`${testId}-footer`} className="flex-1">
              {footer}
            </div>
          ) : null}
        </div>
      </div>
    </ObsCard>
  )
}

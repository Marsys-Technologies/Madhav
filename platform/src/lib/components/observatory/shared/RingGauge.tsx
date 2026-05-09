'use client'
import * as React from 'react'

interface RingGaugeProps {
  /** 0..1 progress (will be clamped). Pass null/undefined for indeterminate. */
  value: number | null | undefined
  size?: number
  thickness?: number
  /** Tone of the arc. Defaults to gold. */
  tone?: 'gold' | 'success' | 'warn' | 'halt'
  /** Centered label and sublabel. */
  label?: React.ReactNode
  sublabel?: React.ReactNode
  className?: string
  ariaLabel?: string
}

const TONE_FROM: Record<NonNullable<RingGaugeProps['tone']>, string> = {
  gold: 'var(--brand-gold-light)',
  success: 'var(--status-success)',
  warn: 'var(--status-warn)',
  halt: 'var(--status-halt)',
}
const TONE_TO: Record<NonNullable<RingGaugeProps['tone']>, string> = {
  gold: 'var(--brand-gold-deep)',
  success: 'var(--status-success)',
  warn: 'var(--status-warn)',
  halt: 'var(--status-halt)',
}

/** SVG ring gauge with gradient stroke. Hand-rolled, no deps. */
export const RingGauge = React.memo(function RingGauge({
  value,
  size = 176,
  thickness = 12,
  tone = 'gold',
  label,
  sublabel,
  className,
  ariaLabel,
}: RingGaugeProps) {
  const clamped = Math.max(0, Math.min(1, value ?? 0))
  const r = (size - thickness) / 2
  const c = 2 * Math.PI * r
  const offset = c * (1 - clamped)
  const cx = size / 2
  const cy = size / 2
  const gradId = React.useId()

  return (
    <div
      className={className}
      style={{ width: size, height: size, position: 'relative' }}
      role="img"
      aria-label={ariaLabel ?? `gauge ${Math.round(clamped * 100)}%`}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={TONE_FROM[tone]} />
            <stop offset="100%" stopColor={TONE_TO[tone]} />
          </linearGradient>
        </defs>
        {/* Track */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="color-mix(in oklch, var(--brand-gold) 12%, transparent)"
          strokeWidth={thickness}
        />
        {/* Progress arc — only if we have a numeric value */}
        {value === null || value === undefined ? null : (
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke={`url(#${gradId})`}
            strokeWidth={thickness}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
            transform={`rotate(-90 ${cx} ${cy})`}
            style={{ transition: 'stroke-dashoffset 600ms ease-out' }}
          />
        )}
      </svg>
      <div
        className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center"
        aria-hidden="true"
      >
        {label ? <div className="bt-num text-[var(--brand-gold-cream)]">{label}</div> : null}
        {sublabel ? (
          <div className="bt-label uppercase text-[rgba(212,175,55,0.55)] mt-1">{sublabel}</div>
        ) : null}
      </div>
    </div>
  )
})

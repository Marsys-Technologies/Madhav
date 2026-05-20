'use client'

/**
 * StarRating — reusable star rating display component.
 *
 * Props:
 *   value — number of filled stars (0..max)
 *   max   — total stars (default 5)
 *   size  — 'sm' | 'md' | 'lg'
 *
 * Uses Unicode star characters styled to brand gold.
 * Used by SpecialYogasList (4C-4-S3) and Muhurat Finder (4C-6).
 *
 * Phase: 4C-4-S3 (Item 5)
 */

interface StarRatingProps {
  value: number
  max?: number
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const SIZE_MAP = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
} as const

export function StarRating({ value, max = 5, size = 'sm', className = '' }: StarRatingProps) {
  const filled = Math.min(Math.max(Math.round(value), 0), max)
  const empty = max - filled

  return (
    <span
      className={`inline-flex items-center gap-px ${SIZE_MAP[size]} ${className}`}
      aria-label={`${filled} out of ${max} stars`}
      role="img"
    >
      {Array.from({ length: filled }).map((_, i) => (
        <span key={`f-${i}`} style={{ color: 'rgba(212,175,55,0.90)' }} aria-hidden="true">
          ★
        </span>
      ))}
      {Array.from({ length: empty }).map((_, i) => (
        <span key={`e-${i}`} style={{ color: 'rgba(212,175,55,0.20)' }} aria-hidden="true">
          ☆
        </span>
      ))}
    </span>
  )
}

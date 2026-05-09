'use client'
import * as React from 'react'

interface SparklineProps {
  values: number[]
  width?: number
  height?: number
  /** Line stroke; defaults to brand gold. */
  stroke?: string
  /** Fill under the curve (gradient with opacity). Defaults to a gold gradient. */
  fill?: 'gold' | 'success' | 'halt' | 'none'
  className?: string
  ariaLabel?: string
}

/** Hand-rolled SVG sparkline. No deps. Memoizes path generation, gates fill via
 *  a gradient defined inline. Renders nothing if fewer than 2 values. */
export const Sparkline = React.memo(function Sparkline({
  values,
  width = 96,
  height = 28,
  stroke = 'var(--brand-gold)',
  fill = 'gold',
  className,
  ariaLabel,
}: SparklineProps) {
  const gradId = React.useId()

  if (!values || values.length < 2) {
    return (
      <svg
        width={width}
        height={height}
        className={className}
        role="img"
        aria-label={ariaLabel ?? 'sparkline (insufficient data)'}
      />
    )
  }

  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1
  const stepX = width / (values.length - 1)
  const padY = 2

  const points = values.map((v, i) => {
    const x = i * stepX
    const y = height - padY - ((v - min) / span) * (height - padY * 2)
    return [x, y] as const
  })

  const linePath = points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ')
  const areaPath = `${linePath} L${width.toFixed(2)},${height} L0,${height} Z`
  const FILL_TOKEN: Record<Exclude<SparklineProps['fill'], undefined>, string> = {
    gold: 'var(--brand-gold)',
    success: 'var(--status-success)',
    halt: 'var(--status-halt)',
    none: 'transparent',
  }
  const fillColor = FILL_TOKEN[fill]

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      role="img"
      aria-label={ariaLabel ?? 'sparkline'}
    >
      {fill !== 'none' ? (
        <>
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={fillColor} stopOpacity={0.35} />
              <stop offset="100%" stopColor={fillColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          <path d={areaPath} fill={`url(#${gradId})`} />
        </>
      ) : null}
      <path d={linePath} fill="none" stroke={stroke} strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
})

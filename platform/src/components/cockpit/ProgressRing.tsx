'use client'

/**
 * ProgressRing — SVG arc progress indicator.
 *
 * Renders a circular progress ring using stroke-dasharray + stroke-dashoffset.
 * CSS transition on stroke-dashoffset (500ms ease-out) gives smooth animation
 * as the progress prop changes.
 *
 * Used by LiveDependencyGraph for running nodes; also standalone reusable.
 *
 * [C-S4]
 */

interface Props {
  /** Progress value 0–1. Values outside [0, 1] are clamped. */
  progress: number
  radius?: number
  strokeWidth?: number
}

export function ProgressRing({
  progress,
  radius = 16,
  strokeWidth = 3,
}: Props) {
  const clamped = Math.min(1, Math.max(0, progress))
  const pct = Math.round(clamped * 100)

  const cx = radius + strokeWidth
  const cy = radius + strokeWidth
  const size = (radius + strokeWidth) * 2
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference * (1 - clamped)

  return (
    <svg
      data-testid="progress-ring"
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      aria-label={`Progress: ${pct}%`}
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      {/* Track */}
      <circle
        cx={cx}
        cy={cy}
        r={radius}
        fill="none"
        stroke="var(--progress-ring-track, #1f1c17)"
        strokeWidth={strokeWidth}
      />
      {/* Fill arc */}
      <circle
        data-testid="progress-ring-arc"
        cx={cx}
        cy={cy}
        r={radius}
        fill="none"
        stroke="var(--progress-ring-stroke, #d4a648)"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={dashOffset}
        transform={`rotate(-90 ${cx} ${cy})`}
        style={{
          transition: 'stroke-dashoffset var(--transition-ring, 500ms ease-out)',
        }}
      />
      {/* Percentage label */}
      <text
        x={cx}
        y={cy}
        textAnchor="middle"
        dominantBaseline="central"
        style={{
          fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
          fontSize: Math.max(6, radius * 0.45),
          fill: 'var(--text-secondary, #888373)',
        }}
      >
        {pct}%
      </text>
    </svg>
  )
}

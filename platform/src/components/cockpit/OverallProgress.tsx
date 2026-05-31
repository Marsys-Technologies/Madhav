'use client'

/**
 * OverallProgress — Sampurna gati overall build progress bar.
 *
 * Renders per VISUAL_CONTRACT v2 §"Page 2 §2 Sampurna gati":
 *   - Italic Cormorant "Sampurna gati · Overall progress" left
 *   - Monospace "47 / 140 nodes · 33.6% · ETA 11m 42s" right
 *   - 6px tall track with gold fill (smooth CSS transition)
 *   - Below: per-ayanamsha sub-counts in 9px monospace
 *
 * Can be driven by the useBuildProgress hook (live) or static props
 * (for testing and static display).
 *
 * [C-S5]
 */

import type { AyanamshaProgress } from '@/hooks/useBuildProgress'

interface Props {
  totalNodes: number
  completeNodes: number
  etaSeconds?: number
  perAyanamsha: AyanamshaProgress[]
}

function formatEta(seconds: number): string {
  if (seconds <= 0) return '< 1s'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s}s`
  if (s === 0) return `${m}m`
  return `${m}m ${s}s`
}

function pct(complete: number, total: number): string {
  if (total === 0) return '0.0%'
  return `${((complete / total) * 100).toFixed(1)}%`
}

function barWidth(complete: number, total: number): string {
  if (total === 0) return '0%'
  return `${Math.min(100, (complete / total) * 100).toFixed(2)}%`
}

export function OverallProgress({ totalNodes, completeNodes, etaSeconds, perAyanamsha }: Props) {
  const percentage = pct(completeNodes, totalNodes)
  const fillWidth = barWidth(completeNodes, totalNodes)

  return (
    <div data-testid="overall-progress" className="space-y-2">
      {/* Label row */}
      <div className="flex items-center justify-between">
        <span
          data-testid="overall-progress-label"
          style={{
            fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
            fontStyle: 'italic',
            fontSize: 14,
            color: 'var(--text-secondary, #888373)',
          }}
        >
          Sampurna gati · Overall progress
        </span>
        <span
          data-testid="overall-progress-stats"
          style={{
            fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
            fontSize: 12,
            color: 'var(--text-primary, #e8e6df)',
          }}
        >
          {completeNodes} / {totalNodes} nodes · {percentage}
          {etaSeconds !== undefined && etaSeconds > 0 && (
            <> · ETA {formatEta(etaSeconds)}</>
          )}
        </span>
      </div>

      {/* Progress track */}
      <div
        data-testid="overall-progress-track"
        style={{
          height: 6,
          background: 'var(--progress-track-bg, #1a1816)',
          borderRadius: 999,
          overflow: 'hidden',
        }}
      >
        <div
          data-testid="overall-progress-fill"
          style={{
            height: '100%',
            width: fillWidth,
            background: 'var(--gold-primary, #d4a648)',
            borderRadius: 999,
            transition: 'width var(--transition-bar, 300ms ease-in-out)',
          }}
        />
      </div>

      {/* Per-ayanamsha sub-counts */}
      {perAyanamsha.length > 0 && (
        <div
          data-testid="per-ayanamsha-counts"
          className="flex flex-wrap gap-x-4"
          style={{
            fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
            fontSize: 'var(--text-mono-sm, 9px)',
            color: 'var(--text-tertiary, #5d5b54)',
          }}
        >
          {perAyanamsha.map((a) => (
            <span key={a.id} data-testid={`ayanamsha-count-${a.id}`}>
              {a.id} {a.complete}/{a.total}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

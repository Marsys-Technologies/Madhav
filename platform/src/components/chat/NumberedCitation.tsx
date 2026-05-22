'use client'

/**
 * Inline [N] citation superscript with hover preview tooltip.
 *
 * Y-S1: Tooltip shows citation snippet after 350ms dwell (preserved).
 * Y-S2: Confidence dot color thresholds preserved.
 * B-S7: Extended with sourceKind, sourceUrl, freshness, onActivate
 *   for full Claude citation parity (replaces the retired side panel).
 *   Web kind → click opens URL in new tab.
 *   Freshness shown in popover.
 *
 * Per NATIVE_RULINGS §3 — full Claude inline citation pivot.
 */

import { useRef, useState } from 'react'
import { ExternalLink } from 'lucide-react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type CitationSourceKind = 'signal' | 'asset' | 'chunk' | 'web'

export type FreshnessValue =
  | 'fresh'
  | 'stale'
  | 'unknown'
  | { age_days: number }

export interface NumberedCitationProps {
  n: number
  signalId: string
  snippet?: string
  confidence?: number
  /** B-S7: Source kind for rendering style + click behaviour. Defaults to 'signal'. */
  sourceKind?: CitationSourceKind
  /** B-S7: URL for 'web' and 'asset' kinds. When set + kind='web', clicking opens in new tab. */
  sourceUrl?: string
  /** B-S7: Freshness metadata shown in popover. */
  freshness?: FreshnessValue
  /**
   * B-S7: Unified activation callback (extends previous onPin back-compat).
   * Called on click for all kinds.
   */
  onActivate?: (n: number, signalId: string, url?: string) => void
  /**
   * @deprecated use onActivate instead. Retained for back-compat with existing callers.
   * Maps to onActivate internally.
   */
  onPin?: (n: number, signalId: string) => void
}

// ---------------------------------------------------------------------------
// Confidence helpers (Y-S2 thresholds — preserved verbatim)
// ---------------------------------------------------------------------------

function confidenceColor(c: number): string {
  if (c >= 0.8) return 'bg-green-500'
  if (c >= 0.5) return 'bg-yellow-500'
  return 'bg-red-500'
}

function confidenceLabel(c: number): string {
  if (c >= 0.8) return 'high'
  if (c >= 0.5) return 'medium'
  return 'low'
}

// ---------------------------------------------------------------------------
// Freshness helpers (B-S7)
// ---------------------------------------------------------------------------

function freshnessLabel(f: FreshnessValue): string {
  if (f === 'fresh') return 'fresh'
  if (f === 'stale') return 'stale'
  if (f === 'unknown') return 'unknown age'
  return `${f.age_days}d old`
}

function freshnessColor(f: FreshnessValue): string {
  if (f === 'fresh') return 'text-green-400'
  if (f === 'stale') return 'text-amber-400'
  if (f === 'unknown') return 'text-zinc-500'
  // age_days: fresh < 30d, stale >= 90d
  const days = f.age_days
  if (days < 30) return 'text-green-400'
  if (days < 90) return 'text-amber-400'
  return 'text-red-400'
}

// ---------------------------------------------------------------------------
// NumberedCitation
// ---------------------------------------------------------------------------

export function NumberedCitation({
  n,
  signalId,
  snippet,
  confidence,
  sourceKind = 'signal',
  sourceUrl,
  freshness,
  onActivate,
  onPin,
}: NumberedCitationProps) {
  const [visible, setVisible] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const tooltipId = `v2-citation-tooltip-${n}-${signalId}`

  // Y-S1: 350ms dwell preserved
  const handleMouseEnter = () => {
    timerRef.current = setTimeout(() => setVisible(true), 350)
  }

  const handleMouseLeave = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
    setVisible(false)
  }

  const displayText = snippet
    ? snippet.length > 100
      ? snippet.slice(0, 100) + '…'
      : snippet
    : signalId

  // B-S7: back-compat — onPin maps to onActivate
  const handleClick = () => {
    if (onActivate) {
      onActivate(n, signalId, sourceUrl)
    } else if (onPin) {
      onPin(n, signalId)
    }
    // Web kind: open URL in new tab
    if (sourceKind === 'web' && sourceUrl) {
      window.open(sourceUrl, '_blank', 'noopener,noreferrer')
    }
  }

  // Kind-specific button style
  const kindBadgeClass =
    sourceKind === 'web'
      ? 'bg-sky-900/40 text-sky-400 hover:bg-sky-800/60 hover:text-sky-300'
      : sourceKind === 'asset' || sourceKind === 'chunk'
      ? 'bg-violet-900/40 text-violet-400 hover:bg-violet-800/60 hover:text-violet-300'
      : 'bg-indigo-900/40 text-indigo-400 hover:bg-indigo-800/60 hover:text-indigo-300'

  return (
    <span className="relative inline-block">
      <button
        type="button"
        className={`inline-flex items-center justify-center gap-0.5 rounded px-1 text-[10px] font-semibold transition-colors leading-none select-none align-super ${kindBadgeClass}`}
        data-testid="v2-citation-badge"
        data-citation-index={n}
        data-signal-id={signalId}
        data-source-kind={sourceKind}
        aria-label={`Citation ${n}: ${signalId}${sourceKind === 'web' ? ' (opens in new tab)' : ''}`}
        aria-describedby={visible ? tooltipId : undefined}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
      >
        [{n}]
        {sourceKind === 'web' && (
          <ExternalLink
            className="h-2 w-2 shrink-0 opacity-70"
            aria-hidden="true"
          />
        )}
      </button>

      {/* Y-S2: Confidence dot — thresholds unchanged */}
      {process.env.NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS === 'true' && confidence !== undefined && (
        <span
          className={`absolute -right-1 -top-1 h-1.5 w-1.5 rounded-full ${confidenceColor(confidence)}`}
          data-testid="v2-citation-confidence-dot"
          data-confidence-band={confidenceLabel(confidence)}
          aria-label={`Signal confidence: ${confidenceLabel(confidence)}`}
          title={`Confidence: ${confidenceLabel(confidence)}`}
        />
      )}

      {/* Y-S1: 350ms hover tooltip — now with freshness badge (B-S7) */}
      {visible && (
        <span
          id={tooltipId}
          className="absolute bottom-full left-1/2 z-50 mb-1 w-max max-w-[280px] -translate-x-1/2 whitespace-normal rounded bg-zinc-800 px-2 py-1.5 text-[11px] leading-snug text-zinc-300 shadow-lg border border-zinc-700"
          data-testid="v2-citation-tooltip"
          role="tooltip"
        >
          {displayText}
          {freshness !== undefined && (
            <span
              className={`ml-1.5 text-[10px] font-medium ${freshnessColor(freshness)}`}
              data-testid="v2-citation-freshness-badge"
            >
              ({freshnessLabel(freshness)})
            </span>
          )}
          {sourceKind === 'web' && sourceUrl && (
            <span className="mt-1 block truncate text-[10px] text-sky-400/80">
              {sourceUrl}
            </span>
          )}
        </span>
      )}
    </span>
  )
}

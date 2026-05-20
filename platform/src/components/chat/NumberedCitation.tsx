'use client'

/**
 * Inline [N] citation superscript with hover preview tooltip.
 * Clicking pins the citation in the CitationSidePanel.
 * Y-S1: Tooltip shows citation snippet after 350ms dwell.
 */

import { useRef, useState } from 'react'

export interface NumberedCitationProps {
  n: number
  signalId: string
  snippet?: string
  confidence?: number
  onPin?: (n: number, signalId: string) => void
}

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

export function NumberedCitation({ n, signalId, snippet, confidence, onPin }: NumberedCitationProps) {
  const [visible, setVisible] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const tooltipId = `v2-citation-tooltip-${n}-${signalId}`

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

  return (
    <span className="relative inline-block">
      <button
        type="button"
        className="inline-flex items-center justify-center rounded bg-indigo-900/40 px-1 text-[10px] font-semibold text-indigo-400 hover:bg-indigo-800/60 hover:text-indigo-300 transition-colors leading-none select-none align-super"
        data-testid="v2-citation-badge"
        data-citation-index={n}
        data-signal-id={signalId}
        aria-label={`Citation ${n}: ${signalId}`}
        aria-describedby={visible ? tooltipId : undefined}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={() => onPin?.(n, signalId)}
      >
        [{n}]
      </button>

      {process.env.NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS === 'true' && confidence !== undefined && (
        <span
          className={`absolute -right-1 -top-1 h-1.5 w-1.5 rounded-full ${confidenceColor(confidence)}`}
          data-testid="v2-citation-confidence-dot"
          data-confidence-band={confidenceLabel(confidence)}
          aria-label={`Signal confidence: ${confidenceLabel(confidence)}`}
          title={`Confidence: ${confidenceLabel(confidence)}`}
        />
      )}

      {visible && (
        <span
          id={tooltipId}
          className="absolute bottom-full left-1/2 z-50 mb-1 w-max max-w-[260px] -translate-x-1/2 whitespace-normal rounded bg-zinc-800 px-2 py-1.5 text-[11px] leading-snug text-zinc-300 shadow-lg border border-zinc-700"
          data-testid="v2-citation-tooltip"
          role="tooltip"
        >
          {displayText}
        </span>
      )}
    </span>
  )
}

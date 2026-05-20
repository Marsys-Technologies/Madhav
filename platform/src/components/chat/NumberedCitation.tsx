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
  onPin?: (n: number, signalId: string) => void
}

export function NumberedCitation({ n, signalId, snippet, onPin }: NumberedCitationProps) {
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

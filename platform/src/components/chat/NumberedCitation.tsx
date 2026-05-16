'use client'

/**
 * Inline [N] citation superscript with hover preview tooltip.
 * Clicking pins the citation in the CitationSidePanel.
 */

import { useState } from 'react'

export interface NumberedCitationProps {
  n: number
  signalId: string
  onPin?: (n: number, signalId: string) => void
}

export function NumberedCitation({ n, signalId, onPin }: NumberedCitationProps) {
  const [hovered, setHovered] = useState(false)

  return (
    <span className="relative inline-block">
      <button
        type="button"
        className="inline-flex items-center justify-center rounded bg-indigo-900/40 px-1 text-[10px] font-semibold text-indigo-400 hover:bg-indigo-800/60 hover:text-indigo-300 transition-colors leading-none select-none align-super"
        data-testid="v2-citation-badge"
        data-citation-index={n}
        data-signal-id={signalId}
        aria-label={`Citation ${n}: ${signalId}`}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        onClick={() => onPin?.(n, signalId)}
      >
        [{n}]
      </button>

      {hovered && (
        <span
          className="absolute bottom-full left-1/2 z-50 mb-1 -translate-x-1/2 whitespace-nowrap rounded bg-zinc-800 px-2 py-1 text-[11px] text-zinc-300 shadow-lg border border-zinc-700"
          data-testid="v2-citation-tooltip"
          role="tooltip"
        >
          {signalId}
        </span>
      )}
    </span>
  )
}

'use client'

/**
 * Pinned-citations side panel for the V2 chat interface.
 * Receives a list of pinned citations and renders them as a collapsible panel.
 */

import type { CitationPart } from '@/lib/citations/citation_data_part'

export interface CitationSidePanelProps {
  citations: CitationPart[]
  pinned: Set<number>
  onUnpin: (n: number) => void
}

export function CitationSidePanel({ citations, pinned, onUnpin }: CitationSidePanelProps) {
  const pinnedCitations = citations.filter(c => pinned.has(c.index))

  if (pinnedCitations.length === 0) return null

  return (
    <aside
      className="flex w-64 shrink-0 flex-col gap-2 border-l border-zinc-800 bg-zinc-950 p-3"
      data-testid="v2-citation-panel"
      aria-label="Pinned citations"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
          Citations
        </h3>
        <span className="text-[10px] text-zinc-600">
          {pinnedCitations.length} pinned
        </span>
      </div>

      <ul className="flex flex-col gap-2">
        {pinnedCitations.map(c => (
          <li
            key={c.index}
            className="flex items-start gap-2 rounded-lg border border-zinc-800 bg-zinc-900 p-2 text-[11px]"
            data-testid="v2-citation-panel-item"
            data-citation-index={c.index}
          >
            <span className="shrink-0 font-semibold text-indigo-400">[{c.index}]</span>
            <div className="flex flex-col gap-0.5 min-w-0">
              <span className="font-mono text-zinc-300 text-[10px]">{c.signal_id}</span>
              {c.snippet && (
                <span className="text-zinc-500 line-clamp-2">{c.snippet}</span>
              )}
              <span className="text-zinc-700">{c.layer}</span>
            </div>
            <button
              type="button"
              onClick={() => onUnpin(c.index)}
              className="shrink-0 ml-auto text-zinc-600 hover:text-zinc-400 transition-colors"
              aria-label={`Unpin citation ${c.index}`}
              data-testid="v2-citation-unpin"
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </aside>
  )
}

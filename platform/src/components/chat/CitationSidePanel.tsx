'use client'

/**
 * Pinned-citations side panel for the V2 chat interface.
 * Receives a list of pinned citations and renders them as a collapsible panel.
 * O6: mobile peek-collapse — default collapsed on mobile, always expanded on md+.
 */

import { useState } from 'react'
import { cn } from '@/lib/utils'
import type { CitationPart } from '@/lib/citations/citation_data_part'

export interface CitationSidePanelProps {
  citations: CitationPart[]
  pinned: Set<number>
  onUnpin: (n: number) => void
}

export function CitationSidePanel({ citations, pinned, onUnpin }: CitationSidePanelProps) {
  const pinnedCitations = citations.filter(c => pinned.has(c.index))
  const [isCollapsed, setIsCollapsed] = useState(true)

  if (pinnedCitations.length === 0) return null

  return (
    <aside
      className={cn(
        'fixed bottom-0 inset-x-0 z-30 overflow-y-auto md:static md:w-64 md:shrink-0 md:overflow-y-auto flex flex-col gap-2 border-t md:border-t-0 md:border-l border-zinc-800 bg-zinc-950 p-3 transition-[max-height] duration-200',
        isCollapsed ? 'max-h-[60px]' : 'max-h-[45vh]',
        'md:max-h-none'
      )}
      data-testid="v2-citation-panel"
      aria-label="Pinned citations"
    >
      {/* Mobile peek header — visible only on mobile (md:hidden) */}
      <button
        type="button"
        onClick={() => setIsCollapsed(c => !c)}
        className="md:hidden flex items-center justify-between w-full text-xs font-semibold uppercase tracking-[0.20em] text-[rgba(var(--brand-gold-rgb),0.6)]"
        aria-expanded={!isCollapsed}
        aria-label={isCollapsed ? 'Expand citations' : 'Collapse citations'}
        data-testid="v2-citation-panel-peek-toggle"
      >
        <span>Citations · {pinnedCitations.length}</span>
        <span aria-hidden>{isCollapsed ? '▲' : '▼'}</span>
      </button>

      {/* Content — always rendered on desktop; hidden when mobile-collapsed */}
      <div className={cn('flex flex-col gap-2', isCollapsed && 'hidden md:flex')}>
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
              <div className="flex flex-col gap-1 min-w-0">
                {/* Signal ID + layer badge on the same row (AC-3: badge adjacent to signal ID) */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="font-mono text-[10px] text-[rgba(var(--brand-gold-rgb),0.70)]">{c.signal_id}</span>
                  {c.layer && (
                    <span className="inline-flex items-center rounded px-1 py-0.5 text-[9px] font-semibold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30" data-testid="v2-citation-layer-badge">
                      {c.layer}
                    </span>
                  )}
                </div>
                {/* Snippet text — wraps freely (AC-4: not truncated to one line) */}
                {c.snippet ? (
                  <span className="text-[11px] leading-snug text-zinc-300 overflow-visible whitespace-normal">{c.snippet}</span>
                ) : (
                  <span className="text-[10px] text-zinc-600 italic">No excerpt available</span>
                )}
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
      </div>
    </aside>
  )
}

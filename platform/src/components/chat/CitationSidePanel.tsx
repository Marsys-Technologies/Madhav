'use client'

/**
 * Citations side panel for the V2 chat interface.
 * R7-S4: auto-opens after streaming ends with all citations.
 * Pin icon per row replaces the old "pinned-only" filter — every row is
 * always shown; starred rows are visually highlighted.
 */

import { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import type { CitationPart } from '@/lib/citations/citation_data_part'

export interface CitationSidePanelProps {
  citations: CitationPart[]
  /** Indexes that are currently "starred" (previously called pinned). */
  pinned: Set<number>
  onUnpin: (n: number) => void
  /** Whether the panel is visible at all. */
  open?: boolean
  onClose?: () => void
  /** When set, the panel scrolls to the matching citation row and flashes it. */
  scrollTarget?: number | null
  /** Called after the scroll animation is triggered so the parent can clear scrollTarget. */
  onScrolled?: () => void
}

export function CitationSidePanel({
  citations,
  open = false,
  onClose,
  scrollTarget,
  onScrolled,
}: CitationSidePanelProps) {
  const sortedCitations = [...citations].sort((a, b) => a.index - b.index)
  const listRef = useRef<HTMLUListElement>(null)
  const [flashIndex, setFlashIndex] = useState<number | null>(null)
  const [mobileCollapsed, setMobileCollapsed] = useState(false)
  // AC-3: starred state is local to the panel; does not gate visibility or remove rows.
  const [starredSet, setStarredSet] = useState<Set<number>>(new Set())

  const toggleStar = (n: number) => {
    setStarredSet(prev => {
      const next = new Set(prev)
      if (next.has(n)) next.delete(n); else next.add(n)
      return next
    })
  }

  // Scroll-to-row + flash
  useEffect(() => {
    if (scrollTarget == null || !listRef.current) return
    const item = listRef.current.querySelector<HTMLLIElement>(
      `[data-citation-index="${scrollTarget}"]`
    )
    if (item) {
      item.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      setFlashIndex(scrollTarget)
      const t = setTimeout(() => setFlashIndex(null), 800)
      onScrolled?.()
      return () => clearTimeout(t)
    }
    onScrolled?.()
  }, [scrollTarget, onScrolled])

  if (!open || sortedCitations.length === 0) return null

  return (
    <aside
      className={cn(
        'fixed bottom-0 inset-x-0 z-30 overflow-y-auto md:static md:w-64 md:shrink-0 md:overflow-y-auto flex flex-col gap-2 border-t md:border-t-0 md:border-l border-zinc-800 bg-zinc-950 p-3 transition-[max-height] duration-200',
        mobileCollapsed ? 'max-h-[60px]' : 'max-h-[45vh]',
        'md:max-h-none'
      )}
      data-testid="v2-citation-panel"
      aria-label="Citations"
    >
      {/* Mobile peek header */}
      <button
        type="button"
        onClick={() => setMobileCollapsed(c => !c)}
        className="md:hidden flex items-center justify-between w-full text-xs font-semibold uppercase tracking-[0.20em] text-[rgba(var(--brand-gold-rgb),0.6)]"
        aria-expanded={!mobileCollapsed}
        aria-label={mobileCollapsed ? 'Expand citations' : 'Collapse citations'}
        data-testid="v2-citation-panel-peek-toggle"
      >
        <span>Citations · {sortedCitations.length}</span>
        <span aria-hidden>{mobileCollapsed ? '▲' : '▼'}</span>
      </button>

      {/* Content */}
      <div className={cn('flex flex-col gap-2', mobileCollapsed && 'hidden md:flex')}>
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Citations
          </h3>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-zinc-600">
              {sortedCitations.length} signal{sortedCitations.length !== 1 ? 's' : ''}
            </span>
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                className="text-zinc-600 hover:text-zinc-400 transition-colors leading-none"
                aria-label="Close citations panel"
                data-testid="v2-citation-panel-close"
              >
                ×
              </button>
            )}
          </div>
        </div>

        <ul ref={listRef} className="flex flex-col gap-2">
          {sortedCitations.map(c => (
            <li
              key={c.index}
              className={cn(
                'flex items-start gap-2 rounded-lg border bg-zinc-900 p-2 text-[11px] transition-colors duration-300',
                flashIndex === c.index
                  ? 'border-indigo-500/60 bg-indigo-950/40'
                  : 'border-zinc-800'
              )}
              data-testid="v2-citation-panel-item"
              data-citation-index={c.index}
            >
              <span className="shrink-0 font-semibold text-indigo-400">[{c.index}]</span>
              <div className="flex flex-col gap-1 min-w-0 flex-1">
                {/* Signal ID + layer badge on the same row (AC-3) */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="font-mono text-[10px] text-[rgba(var(--brand-gold-rgb),0.70)]">
                    {c.signal_id}
                  </span>
                  {c.layer && (
                    <span
                      className="inline-flex items-center rounded px-1 py-0.5 text-[9px] font-semibold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30"
                      data-testid="v2-citation-layer-badge"
                    >
                      {c.layer}
                    </span>
                  )}
                </div>
                {/* Snippet text — wraps freely */}
                {c.snippet ? (
                  <span className="text-[11px] leading-snug text-zinc-300 overflow-visible whitespace-normal">
                    {c.snippet}
                  </span>
                ) : (
                  <span className="text-[10px] text-zinc-600 italic">No excerpt available</span>
                )}
              </div>
              {/* Star toggle — local state only (AC-3); does not remove row or close panel */}
              <button
                type="button"
                onClick={() => toggleStar(c.index)}
                className={cn(
                  'shrink-0 ml-auto transition-colors text-sm leading-none',
                  starredSet.has(c.index)
                    ? 'text-amber-400 hover:text-amber-300'
                    : 'text-zinc-700 hover:text-zinc-500'
                )}
                aria-label={starredSet.has(c.index) ? `Unstar citation ${c.index}` : `Star citation ${c.index}`}
                aria-pressed={starredSet.has(c.index)}
                data-testid="v2-citation-unpin"
              >
                {starredSet.has(c.index) ? '★' : '☆'}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  )
}

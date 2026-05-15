'use client'

/**
 * EmptyState — Gate III §11.
 *
 * Shown when there are no messages and no conversationId loaded. Two tabs:
 *   • "By type"  — class-grouped example queries (hardcoded).
 *   • "By moment" — Flash-generated suggestions grounded in today's date.
 * Click any suggestion → fills the composer (does NOT auto-submit).
 */

import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'
import {
  CLASS_SUGGESTIONS,
  classLabel,
} from '@/lib/consume/class_suggestions'
import type { QueryClass } from '@/lib/jyotish/domain_labels'

// Curated short list for the welcome screen — full class explorer is the
// full CLASS_TAB_ORDER from class_suggestions.ts; we surface only these
// here to avoid overwhelming the user on first load.
const VISIBLE_CLASSES: QueryClass[] = ['factual', 'predictive', 'holistic']

interface Props {
  chartId: string
  chartName: string
  onPick: (text: string) => void
  className?: string
}

type Tab = 'type' | 'moment'

export function EmptyState({ chartId, chartName, onPick, className }: Props) {
  const [tab, setTab] = useState<Tab>('type')
  const [moments, setMoments] = useState<string[] | null>(null)
  const [loadingMoments, setLoadingMoments] = useState(false)
  const [momentsError, setMomentsError] = useState<string | null>(null)

  useEffect(() => {
    if (tab !== 'moment' || moments !== null) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoadingMoments(true)
    fetch(`/api/consume/suggestions/context?chartId=${encodeURIComponent(chartId)}`)
      .then(async r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const body = await r.json() as { suggestions: string[] }
        setMoments(body.suggestions ?? [])
      })
      .catch(err => setMomentsError(err instanceof Error ? err.message : 'failed'))
      .finally(() => setLoadingMoments(false))
  }, [tab, chartId, moments])

  return (
    <div className={cn('mx-auto w-full max-w-2xl px-4 py-12', className)}>
      <header className="mb-8 text-center">
        <h1 className="text-xl font-medium text-foreground">
          {chartName ? `Welcome, ${chartName}.` : 'Welcome.'}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Ask anything about your chart.
        </p>
      </header>

      <nav role="tablist" className="mb-4 flex justify-center border-b border-border/60">
        {([
          { id: 'type', label: 'By type' },
          { id: 'moment', label: 'By moment' },
        ] as Array<{ id: Tab; label: string }>).map(t => (
          <button
            key={t.id}
            role="tab"
            type="button"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              'px-4 py-2 text-sm transition-colors',
              tab === t.id
                ? 'border-b-2 border-[var(--brand-gold)] text-foreground'
                : 'border-b-2 border-transparent text-muted-foreground hover:text-foreground',
            )}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === 'type' ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {VISIBLE_CLASSES.map(c => (
            <ClassGroup key={c} c={c} onPick={onPick} />
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {loadingMoments && (
            <ul className="space-y-2">
              {[0, 1, 2, 3].map(i => (
                <li key={i} className="h-9 animate-pulse rounded-md bg-muted/40" />
              ))}
            </ul>
          )}
          {momentsError && (
            <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
              Couldn&rsquo;t load moment-based suggestions. Try the &ldquo;By type&rdquo; tab.
            </p>
          )}
          {!loadingMoments && !momentsError && moments && moments.length === 0 && (
            <p className="text-center text-xs text-muted-foreground">
              No moment-based suggestions available right now.
            </p>
          )}
          {!loadingMoments && moments && moments.length > 0 && (
            <ul className="space-y-2">
              {moments.map((q, i) => (
                <li key={i}>
                  <SuggestionButton text={q} onPick={onPick} />
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}

function ClassGroup({ c, onPick }: { c: QueryClass; onPick: (t: string) => void }) {
  const queries = CLASS_SUGGESTIONS[c] ?? []
  if (queries.length === 0) return null
  return (
    <section>
      <h2 className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        {classLabel(c)}
      </h2>
      <ul className="space-y-1">
        {queries.slice(0, 2).map(q => (
          <li key={q}>
            <SuggestionButton text={q} onPick={onPick} />
          </li>
        ))}
      </ul>
    </section>
  )
}

function SuggestionButton({ text, onPick }: { text: string; onPick: (t: string) => void }) {
  return (
    <button
      type="button"
      onClick={() => onPick(text)}
      className="w-full rounded-md border border-border bg-muted/20 px-3 py-2 text-left text-xs text-foreground/90 transition-colors hover:border-[rgba(var(--brand-gold-rgb),0.4)] hover:bg-[rgba(var(--brand-gold-rgb),0.05)]"
    >
      {text}
    </button>
  )
}

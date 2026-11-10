'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { LogEventDialog } from './LogEventDialog'
import type { LELEvent } from '@/lib/lel/parser'
import { EventCard } from './EventCard'
import { cn } from '@/lib/utils'

interface TimelineViewProps {
  events: LELEvent[]
  chartId: string
  canLogEvent: boolean
}

const CATEGORIES = [
  'all', 'career', 'education', 'relationship', 'family',
  'health', 'spiritual', 'travel', 'finance', 'loss', 'other',
]

export function TimelineView({ events, chartId, canLogEvent }: TimelineViewProps) {
  const router = useRouter()
  const [saved, setSaved] = useState(false)
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [yearFilter, setYearFilter] = useState('all')

  const categories = [...new Set([...CATEGORIES, ...events.map(event => event.category)])]
  // Derive filter options
  const years = Array.from(
    new Set(events.map(e => e.date.slice(0, 4)).filter(y => /^\d{4}$/.test(y)))
  ).sort((a, b) => b.localeCompare(a))

  const filteredEvents = events
    .filter(e => categoryFilter === 'all' || e.category === categoryFilter)
    .filter(e => yearFilter === 'all' || e.date.startsWith(yearFilter))
    .sort((a, b) => b.date.localeCompare(a.date))
  const resultsLabel = events.length === 0
    ? 'No life events recorded for this chart.'
    : filteredEvents.length === 0
      ? 'No events match the current filters.'
      : `Showing ${filteredEvents.length} of ${events.length} life events.`

  function finishLogging() {
    setCategoryFilter('all')
    setYearFilter('all')
    setSaved(true)
    router.refresh()
  }

  return (
    <div className="flex min-w-0 flex-col">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border/40 px-4 py-4 sm:px-6">
        <div>
          <h1 className="text-lg font-semibold">Life Events</h1>
          <p className="text-sm text-muted-foreground">Recorded events for this chart{!canLogEvent && ' · Read-only'}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Link href={`/clients/${chartId}`} className="inline-flex min-h-11 items-center text-sm text-primary underline">
            Back to chart
          </Link>
          <Link href={`/clients/${chartId}/samiksha`} className="inline-flex min-h-11 items-center text-sm text-primary underline">
            Prediction Review
          </Link>
          {canLogEvent && <LogEventDialog chartId={chartId} onSuccess={finishLogging} />}
        </div>
      </header>
      <div className="space-y-3 px-4 py-3 sm:px-6">
        <fieldset className="min-w-0">
          <legend className="mb-2 text-sm font-medium">Filter events by category</legend>
          <div className="flex flex-wrap gap-2">
            {categories.map(c => (
              <button
                key={c}
                type="button"
                aria-pressed={categoryFilter === c}
                onClick={() => {
                  setSaved(false)
                  setCategoryFilter(c)
                }}
                className={cn(
                  'min-h-11 max-w-full rounded-full border px-3 py-1 text-sm transition-colors [overflow-wrap:anywhere] focus-visible:outline-2 focus-visible:outline-offset-2',
                  categoryFilter === c
                    ? 'border-amber-400/60 bg-amber-400/15 text-amber-300'
                    : 'border-border/40 text-muted-foreground hover:border-border hover:text-foreground'
                )}
              >
                {c}
              </button>
            ))}
          </div>
        </fieldset>
        <select
          className="min-h-11 max-w-full rounded-md border border-input bg-background px-3 text-sm text-foreground"
          aria-label="Filter events by year"
          value={yearFilter}
          onChange={e => {
            setSaved(false)
            setYearFilter(e.target.value)
          }}
        >
          <option value="all">All years</option>
          {years.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      <div className="px-4 py-2 sm:px-6">
        <div role="status" className="mb-3 text-sm text-muted-foreground">
          {saved && <p>Event saved.</p>}
          <p>{resultsLabel}</p>
        </div>
        {filteredEvents.length > 0 && (
          <ol className="list-none">
            {filteredEvents.map(event => (
              <EventCard key={event.id} event={event} />
            ))}
          </ol>
        )}
      </div>
    </div>
  )
}

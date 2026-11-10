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

  function finishLogging() {
    setCategoryFilter('all')
    setYearFilter('all')
    setSaved(true)
    router.refresh()
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border/40 px-6 py-4">
        <div>
          <h1 className="text-lg font-semibold">Life Events</h1>
          <p className="text-sm text-muted-foreground">Recorded events for this chart{!canLogEvent && ' · Read-only'}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Link href={`/clients/${chartId}`} className="text-sm text-primary underline">
            Back to chart
          </Link>
          <Link href={`/clients/${chartId}/samiksha`} className="text-sm text-primary underline">
            Prediction Review
          </Link>
          {canLogEvent && <LogEventDialog chartId={chartId} onSuccess={finishLogging} />}
        </div>
      </header>
      {saved && <p role="status" className="px-6 pt-3 text-sm">Event saved.</p>}
      {/* Filter chips */}
      <div className="flex flex-wrap gap-2 overflow-x-auto px-6 py-3">
        <div className="flex gap-1">
          {categories.map(c => (
            <button
              key={c}
              type="button"
              aria-pressed={categoryFilter === c}
              onClick={() => setCategoryFilter(c)}
              className={cn(
                'rounded-full border px-2.5 py-0.5 text-xs transition-colors',
                categoryFilter === c
                  ? 'border-amber-400/60 bg-amber-400/15 text-amber-300'
                  : 'border-border/40 text-muted-foreground hover:border-border hover:text-foreground'
              )}
            >
              {c}
            </button>
          ))}
        </div>
        <select
          className="rounded-full border border-border/40 bg-transparent px-2.5 py-0.5 text-xs text-muted-foreground"
          aria-label="Filter events by year"
          value={yearFilter}
          onChange={e => setYearFilter(e.target.value)}
        >
          <option value="all">All years</option>
          {years.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      {/* Event list */}
      <div className="flex-1 overflow-y-auto px-6 py-2">
        {filteredEvents.length === 0 ? (
          <p className="py-12 text-center text-sm text-muted-foreground">
            {events.length === 0 ? 'No life events recorded for this chart.' : 'No events match the current filters.'}
          </p>
        ) : (
          <div>
            {filteredEvents.map(event => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

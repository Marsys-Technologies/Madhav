'use client'

import type { LELEvent } from '@/lib/lel/parser'
import { cn } from '@/lib/utils'

const CATEGORY_COLORS: Record<string, string> = {
  career: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  education: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  relationship: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
  family: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  health: 'bg-green-500/20 text-green-300 border-green-500/30',
  spiritual: 'bg-violet-500/20 text-violet-300 border-violet-500/30',
  travel: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  finance: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  residential: 'bg-teal-500/20 text-teal-300 border-teal-500/30',
  loss: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
  other: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
}

interface EventCardProps {
  event: LELEvent
}

export function EventCard({ event }: EventCardProps) {
  const colorClass = CATEGORY_COLORS[event.category] ?? CATEGORY_COLORS.other
  const chart = event.chart_state

  const dateDisplay = event.date
    .replace(/-XX/g, '')
    .replace(/XX-XX/, '')
    .replace(/XX$/, '')

  return (
    <li className="group relative flex gap-3">
      {/* Timeline spine */}
      <div aria-hidden="true" className="flex shrink-0 flex-col items-center">
        <div className="mt-1 h-3 w-3 rounded-full border-2 border-amber-400/70 bg-background ring-4 ring-background" />
        <div className="w-px flex-1 bg-border/40 group-last:hidden" />
      </div>

      {/* Card body */}
      <div className="mb-6 min-w-0 flex-1 rounded-lg border border-border/50 bg-card/60 p-4 shadow-sm [overflow-wrap:anywhere]">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <time className="text-xs font-mono text-muted-foreground">{dateDisplay}</time>
          <span
            className={cn(
              'rounded border px-1.5 py-0.5 text-xs font-medium',
              colorClass
            )}
          >
            {event.category}
          </span>
          {event.id && (
            <span className="ml-auto text-xs text-muted-foreground">{event.id}</span>
          )}
        </div>

        <p className="text-sm leading-relaxed text-foreground/90">{event.body}</p>

        {chart && (chart.maha_lord || chart.antar_lord) && (
          <div className="mt-3 rounded-md bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
            <span className="font-medium">Dasha:</span>{' '}
            {[chart.maha_lord, chart.antar_lord, chart.pratyantar_lord]
              .filter(Boolean)
              .join(' › ')}
            {chart.transit_notes && (
              <span className="ml-2 opacity-70">· {chart.transit_notes.split(';')[0]}</span>
            )}
          </div>
        )}
      </div>
    </li>
  )
}

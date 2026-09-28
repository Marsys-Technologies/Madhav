import { cn } from '@/lib/utils'
import type { ChartReadiness, ChartReadinessState } from '@/lib/charts/readiness'

/**
 * Presentational readiness bar for the Jātaka directory.
 *
 * The label always comes from the shared readiness authority
 * (`lib/charts/readiness`), so the card, the table and the chart workspace
 * cannot drift. State is conveyed by text beside the bar, never by colour alone.
 */

const FILL: Record<ChartReadinessState, string> = {
  'not-built': 'transparent',
  building: 'linear-gradient(90deg,#a26d0e,#f4d160)',
  'partially-built': 'linear-gradient(90deg,#a26d0e,#f4d160)',
  ready: 'linear-gradient(90deg,#a26d0e,#f4d160)',
  failed: 'rgb(220,38,38)',
  'needs-rebuild': 'rgb(220,38,38)',
}

const LABEL_CLASS: Record<ChartReadinessState, string> = {
  'not-built': 'text-[rgba(212,175,55,0.4)]',
  building: 'text-amber-300',
  'partially-built': 'text-[rgba(212,175,55,0.62)]',
  ready: 'text-[#fce29a]',
  failed: 'text-red-300',
  'needs-rebuild': 'text-red-300',
}

export function DirectoryReadiness({
  readiness,
  chartName,
}: {
  readiness: ChartReadiness
  chartName: string
}) {
  const detail =
    readiness.state === 'partially-built' || readiness.state === 'building'
      ? `${readiness.label} · ${readiness.percent}%`
      : readiness.label
  return (
    <div className="mt-3">
      <div
        role="progressbar"
        aria-label={`${chartName} readiness: ${readiness.label}`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={readiness.percent}
        aria-valuetext={detail}
        className="relative h-1.5 w-full overflow-hidden rounded-full border border-[rgba(212,175,55,0.18)] bg-[rgba(212,175,55,0.10)] forced-colors:border-[CanvasText]"
      >
        <div
          className={cn(
            'absolute inset-y-0 left-0 transition-[width] motion-reduce:transition-none forced-colors:bg-[Highlight]',
            readiness.state === 'building' && 'animate-pulse motion-reduce:animate-none',
          )}
          style={{ width: `${readiness.percent}%`, background: FILL[readiness.state] }}
        />
      </div>
      <p className={cn('mt-1 text-[11px] tracking-[0.04em]', LABEL_CLASS[readiness.state])}>{detail}</p>
    </div>
  )
}

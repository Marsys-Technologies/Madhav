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
  building: 'var(--folio-action)',
  'partially-built': 'var(--folio-action)',
  ready: 'var(--folio-action)',
  failed: 'var(--folio-error)',
  'needs-rebuild': 'var(--folio-error)',
}

const LABEL_CLASS: Record<ChartReadinessState, string> = {
  'not-built': 'text-[var(--folio-muted)]',
  building: 'text-[var(--folio-attention)]',
  'partially-built': 'text-[var(--folio-muted)]',
  ready: 'text-[var(--folio-action)]',
  failed: 'text-[var(--folio-error)]',
  'needs-rebuild': 'text-[var(--folio-error)]',
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
        className="relative h-1.5 w-full overflow-hidden rounded-full border border-[var(--folio-divider)] bg-[var(--folio-selected)] forced-colors:border-[CanvasText]"
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

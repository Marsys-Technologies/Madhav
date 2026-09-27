import type { ReactNode } from 'react'
import { RasiChartSVG } from '@/components/charts/RasiChartSVG'
import type { ForensicChart } from '@/lib/forensic/snapshot'
import { formatDate } from '@/lib/utils/date'

interface ChartHeroProps {
  chart: ForensicChart
  nativeName: string
  birthDate: string
  birthTime: string
  birthPlace: string
  /** IANA timezone identifier stored on the chart; omitted from the line when absent. */
  timezoneId?: string | null
  /** Slot for the understated secondary-actions control (ChartActionsMenu). */
  actions?: ReactNode
}

/**
 * Chart identity + D1/Rāśi hero for the Jātaka workspace.
 *
 * D1 is the dominant element and precedes identity in source order, so on
 * mobile the chart comes first; from `md` up the two sit side by side.
 * The D1 value passed in must belong to this chart — an uncomputed chart
 * arrives with `isEmpty` and RasiChartSVG renders its honest empty state.
 */
export function ChartHero({
  chart,
  nativeName,
  birthDate,
  birthTime,
  birthPlace,
  timezoneId,
  actions,
}: ChartHeroProps) {
  const time = birthTime ? birthTime.slice(0, 5) : ''
  const birthLine = [formatDate(birthDate), [time, timezoneId].filter(Boolean).join(' '), birthPlace]
    .filter(Boolean)
    .join(' · ')

  return (
    <section
      aria-labelledby="jw-identity-name"
      className="mx-auto grid w-full max-w-6xl grid-cols-1 items-center gap-8 px-4 pb-6 pt-8 sm:px-6 md:grid-cols-[minmax(0,420px)_minmax(0,1fr)] md:gap-12 md:pt-12"
    >
      <div className="jw-panel mx-auto w-full max-w-[420px] p-3" data-testid="d1-chart">
        <RasiChartSVG chart={chart} size={400} className="h-auto w-full" />
      </div>

      <div className="flex min-w-0 flex-col gap-4">
        <div className="flex items-start justify-between gap-4">
          <p className="jw-eyebrow">Jātaka</p>
          {actions}
        </div>
        <h1 id="jw-identity-name" className="jw-display break-words text-[clamp(2.25rem,5vw,3.5rem)]">
          {nativeName}
        </h1>
        <div className="h-px w-16 bg-[var(--jw-rule-strong)]" aria-hidden="true" />
        <dl className="grid gap-2 text-sm">
          <div>
            <dt className="sr-only">Birth</dt>
            <dd className="text-[var(--jw-ink-dim)]">{birthLine}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="jw-eyebrow self-center">Lagna</dt>
            <dd className="text-[var(--jw-ink)]">
              {chart.isEmpty || !chart.lagnaSign ? (
                <span className="text-[var(--jw-ink-dim)]">Not yet computed</span>
              ) : (
                <>
                  {chart.lagnaSign}
                  {chart.lagnaDegreeDms && (
                    <span className="ml-2 font-mono text-xs text-[var(--jw-gold)]">{chart.lagnaDegreeDms}</span>
                  )}
                </>
              )}
            </dd>
          </div>
        </dl>
      </div>
    </section>
  )
}

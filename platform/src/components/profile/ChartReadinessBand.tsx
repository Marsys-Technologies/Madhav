import Link from 'next/link'
import { BRAHMA_LEXICON } from '@/lib/brahma/lexicon'
import type { ChartReadiness } from '@/lib/charts/readiness'
import type { LayerPipState } from '@/lib/roster/types'
import { formatDate } from '@/lib/utils/date'

/**
 * Workspace readiness band — the same shared readiness value the Jātakas
 * directory shows, expanded with the six public layers and run context.
 * Every state is stated in text; colour only reinforces it.
 */

const PIP_TEXT: Record<LayerPipState, string> = {
  lit: 'built',
  building: 'building',
  amber: 'needs attention',
  dim: 'not built',
}

const PIP_CLASS: Record<LayerPipState, string> = {
  lit: 'bg-[var(--jw-gold)] border-[var(--jw-gold)]',
  building: 'border-[var(--jw-gold)] bg-transparent animate-pulse motion-reduce:animate-none',
  amber: 'border-amber-400 bg-amber-400/40',
  dim: 'border-[var(--jw-rule-strong)] bg-transparent',
}

function RetryCopy({ chartId, canBuild }: { chartId?: string; canBuild?: boolean }) {
  if (chartId && canBuild) {
    return (
      <Link
        href={`/clients/${chartId}/nirmana`}
        className="jw-control jw-touch inline-flex items-center border border-[var(--jw-rule-strong)] px-3 py-1.5 text-xs text-[var(--jw-ink)] hover:border-[var(--jw-gold)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--jw-gold)]"
      >
        Retry in Nirmāṇa
      </Link>
    )
  }
  return <span className="text-xs text-[var(--jw-ink-dim)]">The chart owner can retry in Nirmāṇa.</span>
}

export function ChartReadinessBand({
  readiness,
  chartId,
  canBuild,
}: {
  readiness: ChartReadiness
  chartId?: string
  canBuild?: boolean
}) {
  const needsAttention = readiness.state === 'needs-rebuild' || readiness.state === 'failed'
  return (
    <section aria-labelledby="jw-readiness-heading" className="jw-panel px-5 py-4" data-testid="chart-readiness-band">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
        <div className="flex items-baseline gap-3">
          <h2 id="jw-readiness-heading" className="jw-eyebrow">
            Computation
          </h2>
          <span
            className={
              needsAttention ? 'text-sm font-medium text-[var(--jw-danger)]' : 'text-sm font-medium text-[var(--jw-ink)]'
            }
          >
            {readiness.label}
          </span>
        </div>
        <span className="font-mono text-xs tabular-nums text-[var(--jw-gold)]" aria-hidden="true">
          {readiness.percent}%
        </span>
      </div>

      <div
        role="progressbar"
        aria-label="Chart computation readiness"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={readiness.percent}
        aria-valuetext={`${readiness.label}, ${readiness.percent}%`}
        className="mt-3 h-1 w-full overflow-hidden rounded-full bg-[var(--jw-tint)] forced-colors:border forced-colors:border-[CanvasText]"
      >
        <div
          className="h-full rounded-full bg-[var(--jw-gold)] transition-[width] motion-reduce:transition-none forced-colors:bg-[Highlight]"
          style={{ width: `${readiness.percent}%` }}
        />
      </div>

      <ol className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3 lg:grid-cols-6" aria-label="Layers">
        {readiness.layerPips.map((pip) => {
          const name = BRAHMA_LEXICON[pip.layer].sanskrit
          return (
            <li key={pip.layer} aria-label={`${name}: ${PIP_TEXT[pip.state]}`} className="flex items-center gap-2">
              <span aria-hidden="true" className={`h-2 w-2 shrink-0 rounded-full border ${PIP_CLASS[pip.state]}`} />
              <span aria-hidden="true" className="text-xs text-[var(--jw-ink-dim)]">{name}</span>
            </li>
          )
        })}
      </ol>

      <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-[var(--jw-ink-dim)]">
        {readiness.activeRunId && readiness.activeRunBlocksReadings !== false && (
          <span>Build run {readiness.activeRunId.slice(0, 8)} in progress — progress updates here.</span>
        )}
        {readiness.activeRunId && readiness.activeRunBlocksReadings === false && (
          <span>
            Recalibration run {readiness.activeRunId.slice(0, 8)} in progress — readings continue on the current chart.
          </span>
        )}
        {readiness.lastActivity && <span>Last built {formatDate(readiness.lastActivity)}</span>}
        {readiness.state === 'needs-rebuild' && (
          <>
            <span>Chart details changed and the recomputation did not start. Earlier results were cleared.</span>
            <RetryCopy chartId={chartId} canBuild={canBuild} />
          </>
        )}
        {readiness.state === 'failed' && <span>The latest build failed. Open Nirmāṇa for details.</span>}
        {readiness.refreshWarning && (
          <span role="status" className="text-amber-200/80">
            {readiness.refreshWarning}
          </span>
        )}
      </div>
    </section>
  )
}

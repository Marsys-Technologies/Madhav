'use client'

import * as React from 'react'
import {
  getBreakdowns,
  getSummary,
  getTimeseries,
  type BreakdownsParams,
  type SummaryParams,
  type TimeseriesParams,
} from '@/lib/api-clients/observatory'
import type {
  BreakdownsResponse,
  SummaryResponse,
  TimeseriesResponse,
} from '@/lib/observatory/types'
import { CostOverTimeChart } from '../charts'
import { CostByModelChart } from '../charts/CostByModelChart'
import { FiltersBar } from '../filters/FiltersBar'
import { useObservatoryFilters } from '../filters/useObservatoryFilters'
import type { DateRangePresetId, ObservatoryFilters as UiFilters } from '../filters/types'
import { KpiTilesRow } from '../kpi/KpiTilesRow'
import { StackBreakdownCards } from '../StackBreakdownCards'
import { EmptyObservatoryState } from '../EmptyObservatoryState'
import { uiToApiFilters, uiToDashboardRange } from './filterAdapter'
import { ObsPageShell, ObsCard, SectionLabel } from '../shared'

type GroupedBreakdowns = {
  provider: BreakdownsResponse | null
  pipeline_stage: BreakdownsResponse | null
  model: BreakdownsResponse | null
}

interface OverviewClientProps {
  apiClient?: {
    getSummary: (p: SummaryParams) => Promise<SummaryResponse>
    getTimeseries: (p: TimeseriesParams) => Promise<TimeseriesResponse>
    getBreakdowns: (p: BreakdownsParams) => Promise<BreakdownsResponse>
  }
}

const DEFAULT_API = { getSummary, getTimeseries, getBreakdowns }

export function OverviewClient({
  apiClient = DEFAULT_API,
}: OverviewClientProps = {}): React.ReactElement {
  const { filters, setFilters } = useObservatoryFilters()
  const [summary, setSummary] = React.useState<SummaryResponse | null>(null)
  const [timeseries, setTimeseries] = React.useState<TimeseriesResponse | null>(null)
  const [breakdowns, setBreakdowns] = React.useState<GroupedBreakdowns>({
    provider: null,
    pipeline_stage: null,
    model: null,
  })
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  const refetch = React.useCallback(
    async (f: UiFilters) => {
      setLoading(true)
      setError(null)
      try {
        const range = uiToDashboardRange(f)
        const apiF = uiToApiFilters(f)
        const [s, ts, prov, stage, model] = await Promise.all([
          apiClient.getSummary({ ...range, compare_to_previous: f.compare_to_previous, filters: apiF }),
          apiClient.getTimeseries({ ...range, granularity: 'day', dimension: 'provider', filters: apiF }),
          apiClient.getBreakdowns({ ...range, dimension: 'provider', filters: apiF }),
          apiClient.getBreakdowns({ ...range, dimension: 'pipeline_stage', filters: apiF }),
          apiClient.getBreakdowns({ ...range, dimension: 'model', filters: apiF }),
        ])
        setSummary(s)
        setTimeseries(ts)
        setBreakdowns({ provider: prov, pipeline_stage: stage, model })
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load observatory data')
      } finally {
        setLoading(false)
      }
    },
    [apiClient],
  )

  React.useEffect(() => {
    void refetch(filters)
  }, [filters, refetch])

  const modelOptions = React.useMemo(
    () => (breakdowns.model?.rows ?? []).map((r) => r.dim_value),
    [breakdowns.model],
  )

  const hasNoData = !loading && !error && summary !== null && summary.total_requests === 0

  const headerRight = (
    <div className="flex flex-wrap items-center gap-2">
      <QuickDateToggle
        preset={filters.preset}
        onChange={(preset) => setFilters({ ...filters, preset })}
      />
      <CompareToggle
        active={filters.compare_to_previous ?? false}
        onChange={(compare_to_previous) => setFilters({ ...filters, compare_to_previous })}
      />
    </div>
  )

  const headerBottom = (
    <details className="group">
      <summary className="inline-flex cursor-pointer items-center gap-1.5 bt-label bt-label-upper text-[rgba(212,175,55,0.45)] hover:text-[var(--brand-gold)] list-none select-none">
        <span aria-hidden="true" className="transition-transform group-open:rotate-90">▸</span>
        Advanced filters
      </summary>
      <div className="mt-3">
        <FiltersBar
          filters={filters}
          modelOptions={modelOptions}
          onFiltersChange={setFilters}
        />
      </div>
    </details>
  )

  return (
    <ObsPageShell
      testId="observatory-overview"
      title="LLM Observatory"
      subtitle="Token usage · cost · latency across all provider stacks"
      devanagari
      live={!loading && !error}
      liveLabel="live"
      headerRight={headerRight}
      headerBottom={headerBottom}
    >
      {/* Error */}
      {error ? (
        <div
          data-testid="observatory-overview-error"
          role="alert"
          className="rounded-xl border border-[color-mix(in_oklch,var(--status-halt)_30%,transparent)] bg-[color-mix(in_oklch,var(--status-halt)_8%,transparent)] p-4 text-sm text-[var(--status-halt)]"
        >
          {error}
          <button
            type="button"
            onClick={() => void refetch(filters)}
            className="ml-4 underline hover:no-underline"
          >
            Retry
          </button>
        </div>
      ) : null}

      {/* Empty state */}
      {hasNoData ? (
        <EmptyObservatoryState dateRangeLabel={filters.preset !== 'custom' ? filters.preset : undefined} />
      ) : (
        <>
          {/* Hero KPIs */}
          <section>
            <SectionLabel accent>Key metrics</SectionLabel>
            <KpiTilesRow
              summary={summary ?? undefined}
              loading={loading && !summary}
              mode="hero3"
              onRetry={() => void refetch(filters)}
            />
          </section>

          {/* Provider stack breakdown */}
          <section data-testid="observatory-overview-provider-breakdown">
            <SectionLabel>By provider stack</SectionLabel>
            <StackBreakdownCards
              data={breakdowns.provider}
              loading={loading && !breakdowns.provider}
            />
          </section>

          {/* Cost over time */}
          <section data-testid="observatory-overview-timeseries">
            <div className="mb-3 flex items-center justify-between">
              <SectionLabel>Cost over time</SectionLabel>
              <span className="bt-label bt-label-upper text-[rgba(212,175,55,0.40)]">
                by provider · daily
              </span>
            </div>
            <ObsCard padding="normal">
              <CostOverTimeChart
                data={timeseries}
                dimension="provider"
                granularity="day"
                loading={loading && !timeseries}
                onRetry={() => void refetch(filters)}
              />
            </ObsCard>
          </section>

          {/* Pipeline-stage breakdown */}
          <section data-testid="observatory-overview-stage-breakdown">
            <SectionLabel>By pipeline stage</SectionLabel>
            <ObsCard padding="normal">
              <CostByModelChart
                data={breakdowns.pipeline_stage}
                dimension="pipeline_stage"
                loading={loading && !breakdowns.pipeline_stage}
                onRetry={() => void refetch(filters)}
              />
            </ObsCard>
          </section>

          {/* All metrics drawer */}
          <details className="group">
            <summary className="mb-3 inline-flex cursor-pointer items-center gap-1.5 bt-label bt-label-upper text-[rgba(212,175,55,0.40)] hover:text-[var(--brand-gold)] list-none select-none">
              <span aria-hidden="true" className="transition-transform group-open:rotate-90">▸</span>
              All metrics detail
            </summary>
            <KpiTilesRow
              summary={summary ?? undefined}
              loading={loading && !summary}
              onRetry={() => void refetch(filters)}
            />
          </details>
        </>
      )}
    </ObsPageShell>
  )
}

// ── Sub-components ──────────────────────────────────────────────────────────

const DATE_PRESETS: Array<{ value: DateRangePresetId; label: string }> = [
  { value: 'today', label: 'Today' },
  { value: '7d', label: '7d' },
  { value: '30d', label: '30d' },
  { value: '90d', label: '90d' },
]

function QuickDateToggle({
  preset,
  onChange,
}: {
  preset: DateRangePresetId
  onChange: (p: DateRangePresetId) => void
}) {
  return (
    <div
      role="radiogroup"
      aria-label="Date range"
      className="obs-glass flex items-center gap-0.5 rounded-full p-0.5"
    >
      {DATE_PRESETS.map(({ value, label }) => {
        const active = preset === value
        return (
          <button
            key={value}
            role="radio"
            aria-checked={active}
            type="button"
            onClick={() => onChange(value)}
            className={
              active
                ? 'rounded-full bg-[color-mix(in_oklch,var(--brand-gold)_20%,transparent)] px-3 py-1 text-xs font-semibold text-[var(--brand-gold)] shadow-[inset_0_0_0_1px_color-mix(in_oklch,var(--brand-gold)_30%,transparent)]'
                : 'rounded-full px-3 py-1 text-xs font-medium text-[rgba(212,175,55,0.45)] hover:text-[var(--brand-gold)] transition-colors'
            }
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}

function CompareToggle({
  active,
  onChange,
}: {
  active: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={active}
      onClick={() => onChange(!active)}
      className={
        active
          ? 'obs-glass rounded-full px-3 py-1 text-[11px] font-medium text-[var(--brand-gold)]'
          : 'obs-glass rounded-full px-3 py-1 text-[11px] font-medium text-[rgba(212,175,55,0.45)] hover:text-[var(--brand-gold)] transition-colors'
      }
      title="Show change vs previous equal-length period"
    >
      Δ vs previous
    </button>
  )
}

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
import { SectionLabel } from '../shared'

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

  return (
    <div data-testid="observatory-overview" className="min-h-full bg-[var(--brand-charcoal,oklch(0.10_0.012_70))]">
      {/* ── Page header ── */}
      <div className="border-b border-[rgba(212,175,55,0.10)] px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="font-heading text-xl font-semibold text-[#fce29a] tracking-wide">
              LLM Observatory
            </h1>
            <p className="mt-0.5 text-xs text-[rgba(212,175,55,0.45)]">
              Token usage · cost · latency across all provider stacks
            </p>
          </div>

          {/* Quick date presets */}
          <QuickDateToggle
            preset={filters.preset}
            onChange={(preset) => setFilters({ ...filters, preset })}
          />
        </div>

        {/* Advanced filter bar (collapsed by default on small screens) */}
        <details className="mt-4 group">
          <summary className="inline-flex cursor-pointer items-center gap-1.5 text-[11px] font-medium text-[rgba(212,175,55,0.35)] hover:text-[rgba(212,175,55,0.65)] list-none select-none">
            <span aria-hidden="true" className="transition-transform group-open:rotate-90">▶</span>
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
      </div>

      {/* ── Main content ── */}
      <div className="flex flex-col gap-8 p-6">
        {/* Error */}
        {error ? (
          <div
            data-testid="observatory-overview-error"
            role="alert"
            className="rounded-lg border border-red-500/30 bg-red-500/5 p-4 text-sm text-red-400"
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
            {/* ── Zone 1: Hero KPIs ── */}
            <section>
              <SectionLabel>Key metrics</SectionLabel>
              <KpiTilesRow
                summary={summary ?? undefined}
                loading={loading && !summary}
                mode="hero3"
                onRetry={() => void refetch(filters)}
              />
            </section>

            {/* ── Zone 2: Stack breakdown cards ── */}
            <section data-testid="observatory-overview-provider-breakdown">
              <SectionLabel>By provider stack</SectionLabel>
              <StackBreakdownCards
                data={breakdowns.provider}
                loading={loading && !breakdowns.provider}
              />
            </section>

            {/* ── Zone 3: Cost over time ── */}
            <section data-testid="observatory-overview-timeseries">
              <div className="mb-3 flex items-center justify-between">
                <SectionLabel>Cost over time</SectionLabel>
                <span className="text-[10px] text-[rgba(212,175,55,0.30)] uppercase tracking-wider">
                  by provider · daily
                </span>
              </div>
              <div className="rounded-xl border border-[rgba(212,175,55,0.10)] bg-[oklch(0.11_0.010_70)] p-4">
                <CostOverTimeChart
                  data={timeseries}
                  dimension="provider"
                  granularity="day"
                  loading={loading && !timeseries}
                  onRetry={() => void refetch(filters)}
                />
              </div>
            </section>

            {/* ── Zone 4: Stage breakdown ── */}
            <section data-testid="observatory-overview-stage-breakdown">
              <SectionLabel>By pipeline stage</SectionLabel>
              <div className="rounded-xl border border-[rgba(212,175,55,0.10)] bg-[oklch(0.11_0.010_70)] p-4">
                <CostByModelChart
                  data={breakdowns.pipeline_stage}
                  dimension="pipeline_stage"
                  loading={loading && !breakdowns.pipeline_stage}
                  onRetry={() => void refetch(filters)}
                />
              </div>
            </section>

            {/* ── Zone 5: Full detail metrics (collapsed) ── */}
            <details className="group">
              <summary className="mb-3 inline-flex cursor-pointer items-center gap-1.5 text-[11px] font-medium text-[rgba(212,175,55,0.30)] hover:text-[rgba(212,175,55,0.60)] list-none select-none">
                <span aria-hidden="true" className="transition-transform group-open:rotate-90">▶</span>
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
      </div>
    </div>
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
    <div className="flex items-center gap-0.5 rounded-lg border border-[rgba(212,175,55,0.12)] bg-[rgba(0,0,0,0.2)] p-0.5">
      {DATE_PRESETS.map(({ value, label }) => (
        <button
          key={value}
          type="button"
          onClick={() => onChange(value)}
          className={
            preset === value
              ? 'rounded-md bg-[rgba(212,175,55,0.16)] px-3 py-1 text-xs font-semibold text-[#d4af37]'
              : 'rounded-md px-3 py-1 text-xs font-medium text-[rgba(212,175,55,0.35)] hover:text-[#d4af37] transition-colors'
          }
        >
          {label}
        </button>
      ))}
    </div>
  )
}

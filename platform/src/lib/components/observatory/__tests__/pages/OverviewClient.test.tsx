import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { defaultFilters } from '../../filters/serialization'
import type {
  BreakdownsParams,
  SummaryParams,
  TimeseriesParams,
} from '@/lib/api-clients/observatory'
import type {
  BreakdownsResponse,
  SummaryResponse,
  TimeseriesResponse,
} from '@/lib/observatory/types'

vi.mock('next/navigation', () => {
  const setFilters = vi.fn()
  return {
    useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
    usePathname: () => '/observatory',
    useSearchParams: () => new URLSearchParams(''),
    __setFilters: setFilters,
  }
})

import { OverviewClient } from '../../pages/OverviewClient'

const EMPTY_SUMMARY: SummaryResponse = {
  total_cost_usd: 0,
  total_requests: 0,
  total_input_tokens: 0,
  total_output_tokens: 0,
  total_cache_tokens: 0,
  avg_cost_per_request: 0,
  p50_latency_ms: 0,
  p95_latency_ms: 0,
  reconciliation_variance_pct: null,
  reconciliation_through_date: null,
}

const EMPTY_TIMESERIES: TimeseriesResponse = { buckets: [] }
const EMPTY_BREAKDOWNS: BreakdownsResponse = { rows: [] }

function emptyApiClient() {
  return {
    getSummary: vi.fn(
      async (_p: SummaryParams): Promise<SummaryResponse> => EMPTY_SUMMARY,
    ),
    getTimeseries: vi.fn(
      async (_p: TimeseriesParams): Promise<TimeseriesResponse> =>
        EMPTY_TIMESERIES,
    ),
    getBreakdowns: vi.fn(
      async (_p: BreakdownsParams): Promise<BreakdownsResponse> =>
        EMPTY_BREAKDOWNS,
    ),
  }
}

describe('OverviewClient (S1.13 wiring)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without throwing when the API returns empty data', async () => {
    const api = emptyApiClient()
    render(<OverviewClient apiClient={api} />)

    // Filters bar + KPI tiles always render in the loading skeleton.
    expect(screen.getByTestId('observatory-filters-bar')).toBeInTheDocument()
    expect(screen.getByTestId('kpi-tiles-row')).toBeInTheDocument()

    // Section headers are present even before the empty states resolve.
    expect(screen.getByTestId('observatory-overview-timeseries')).toBeInTheDocument()
    expect(
      screen.getByTestId('observatory-overview-provider-breakdown'),
    ).toBeInTheDocument()
    expect(
      screen.getByTestId('observatory-overview-stage-breakdown'),
    ).toBeInTheDocument()

    // Six fetches fire on initial load: summary + two timeseries (provider +
    // pipeline_stage, the second added so stage cards get sparklines and the
    // stage stacked-bar gets a series row) + three breakdowns.
    await waitFor(() => {
      expect(api.getSummary).toHaveBeenCalledTimes(1)
      expect(api.getTimeseries).toHaveBeenCalledTimes(2)
      expect(api.getBreakdowns).toHaveBeenCalledTimes(3)
    })

    // When total_requests === 0, the overview shows the empty state instead of charts.
    await waitFor(() => {
      expect(screen.getByTestId('observatory-empty-state')).toBeInTheDocument()
    })
  })

  it('passes the same date range to every endpoint', async () => {
    const api = emptyApiClient()
    render(<OverviewClient apiClient={api} />)
    await waitFor(() => {
      expect(api.getSummary).toHaveBeenCalled()
    })

    const summaryCall = api.getSummary.mock.calls[0]![0]!
    const tsCall = api.getTimeseries.mock.calls[0]![0]!
    const bdCall = api.getBreakdowns.mock.calls[0]![0]!
    expect(summaryCall.from).toBe(tsCall.from)
    expect(summaryCall.to).toBe(tsCall.to)
    expect(summaryCall.from).toBe(bdCall.from)
    expect(summaryCall.to).toBe(bdCall.to)

    // The from/to are derived from the default 30d preset; sanity-check shape.
    const def = defaultFilters()
    expect(summaryCall.from).toContain(def.date_range.from)
  })

  it('requests provider, pipeline_stage, and model breakdowns', async () => {
    const api = emptyApiClient()
    render(<OverviewClient apiClient={api} />)
    await waitFor(() => {
      expect(api.getBreakdowns).toHaveBeenCalledTimes(3)
    })
    const dimensions = api.getBreakdowns.mock.calls.map((c) => c[0]!.dimension)
    expect(dimensions).toEqual(
      expect.arrayContaining(['provider', 'pipeline_stage', 'model']),
    )
  })
})

import { describe, it, expect, vi, beforeAll } from 'vitest'
import { render, screen } from '@testing-library/react'

// Recharts in jsdom requires non-zero parent dimensions on ResponsiveContainer
// to render anything; we bypass that by mocking the chart primitives to render
// only their `data-testid` attribute. The data-transformation tests use the
// component-under-test's wrapper div + exported pure helpers, which do not
// depend on recharts SVG rendering.
vi.mock('recharts', () => {
  const passthrough = ({ children }: { children?: React.ReactNode }) => (
    <div>{children}</div>
  )
  const noop = () => null
  return {
    ResponsiveContainer: passthrough,
    AreaChart: passthrough,
    BarChart: passthrough,
    ComposedChart: passthrough,
    Area: noop,
    Bar: noop,
    Cell: noop,
    Line: noop,
    XAxis: noop,
    YAxis: noop,
    CartesianGrid: noop,
    ReferenceLine: noop,
    Tooltip: noop,
    Legend: noop,
  }
})

import {
  CostOverTimeChart,
  buildDrillDownTarget,
  rollUpModels,
  computeCacheSavings,
  formatCostUSD,
  formatTokenCount,
} from '../../charts'
import type {
  BreakdownsResponse,
  TimeseriesResponse,
} from '@/lib/observatory/types'

beforeAll(() => {
  // jsdom doesn't implement matchMedia or ResizeObserver — recharts touches
  // neither under the mocked surface, but harmless to add for safety.
  if (!('ResizeObserver' in globalThis)) {
    ;(globalThis as { ResizeObserver?: unknown }).ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
  }
})

const TS = '2026-05-01T00:00:00.000Z'
const TS2 = '2026-05-01T01:00:00.000Z'

function timeseriesFixture(seriesKeys: string[]): TimeseriesResponse {
  const series: Record<string, number> = {}
  for (const k of seriesKeys) series[k] = 1.5
  return { buckets: [{ time: TS, series }, { time: TS2, series }] }
}

function breakdownsFixture(
  rows: Array<Partial<BreakdownsResponse['rows'][number]> & { dim_value: string }>,
): BreakdownsResponse {
  return {
    rows: rows.map((r) => ({
      dim_value: r.dim_value,
      cost_usd: r.cost_usd ?? 0,
      request_count: r.request_count ?? 0,
      input_tokens: r.input_tokens ?? 0,
      output_tokens: r.output_tokens ?? 0,
      cache_tokens: r.cache_tokens ?? 0,
      avg_latency_ms: r.avg_latency_ms ?? 0,
    })),
  }
}

describe('CostOverTimeChart series count', () => {
  it('renders 5 series for provider dimension across 5 providers', () => {
    const data = timeseriesFixture([
      'anthropic',
      'openai',
      'gemini',
      'deepseek',
      'nim',
    ])
    render(
      <CostOverTimeChart data={data} dimension="provider" granularity="hour" />,
    )
    const wrapper = screen.getByTestId('cost-over-time-chart')
    expect(wrapper.dataset.seriesCount).toBe('5')
    expect(wrapper.dataset.dimension).toBe('provider')
  })

  it('renders 6 series for pipeline_stage dimension', () => {
    const data = timeseriesFixture([
      'classify',
      'compose',
      'retrieve',
      'synthesize',
      'audit',
      'other',
    ])
    render(
      <CostOverTimeChart
        data={data}
        dimension="pipeline_stage"
        granularity="day"
      />,
    )
    const wrapper = screen.getByTestId('cost-over-time-chart')
    expect(wrapper.dataset.seriesCount).toBe('6')
    expect(wrapper.dataset.dimension).toBe('pipeline_stage')
  })
})

describe('CostOverTimeChart empty state', () => {
  it('renders the empty placeholder for an empty buckets array', () => {
    render(
      <CostOverTimeChart
        data={{ buckets: [] }}
        dimension="provider"
        granularity="day"
      />,
    )
    expect(screen.getByTestId('cost-over-time-empty')).toBeInTheDocument()
    expect(screen.getByText(/No data in this range/i)).toBeInTheDocument()
    expect(screen.queryByTestId('cost-over-time-chart')).not.toBeInTheDocument()
  })
})

describe('CostByModelChart roll-up', () => {
  it('keeps top 15 models and groups the remainder into "Other (k models)"', () => {
    const rows = Array.from({ length: 20 }, (_, i) => ({
      dim_value: `model-${i}`,
      cost_usd: 100 - i, // descending
      request_count: 10,
    }))
    const result = rollUpModels(breakdownsFixture(rows))
    expect(result).toHaveLength(16) // 15 + Other
    expect(result.slice(0, 15).every((r) => !r.isOther)).toBe(true)
    const other = result[15]
    expect(other.isOther).toBe(true)
    expect(other.label).toBe('Other (5 models)')
    // Other's cost is the sum of models 15..19 (descending values 85..81)
    expect(other.cost_usd).toBe(85 + 84 + 83 + 82 + 81)
    expect(other.request_count).toBe(50)
  })
})

describe('CacheSavingsChart provider filter', () => {
  it('omits providers with zero cache tokens', () => {
    const data = breakdownsFixture([
      { dim_value: 'anthropic', cache_tokens: 1_000_000 },
      { dim_value: 'openai', cache_tokens: 0 },
      { dim_value: 'gemini', cache_tokens: 500_000 },
      { dim_value: 'deepseek', cache_tokens: 0 },
      { dim_value: 'nim', cache_tokens: 0 },
    ])
    const rows = computeCacheSavings(data)
    expect(rows.map((r) => r.provider).sort()).toEqual(['anthropic', 'gemini'])
    expect(rows.every((r) => r.estimated_savings_usd > 0)).toBe(true)
    expect(rows.every((r) => r.cost_with_cache_usd < r.cost_without_cache_usd)).toBe(
      true,
    )
  })
})

describe('formatCostUSD', () => {
  it('formats sub-cent values with six decimal places', () => {
    expect(formatCostUSD(0.000123)).toBe('$0.000123')
    expect(formatCostUSD(0.005)).toBe('$0.005000')
    // ≥ $1 reverts to 2dp for readability
    expect(formatCostUSD(1234.5)).toBe('$1,234.50')
  })
})

describe('formatTokenCount', () => {
  it('formats large counts with M/K suffixes; small counts as raw integers', () => {
    expect(formatTokenCount(1_500_000)).toBe('1.5M')
    expect(formatTokenCount(450_000)).toBe('450K')
    expect(formatTokenCount(12)).toBe('12')
    expect(formatTokenCount(0)).toBe('0')
  })
})

describe('CostOverTimeChart drill-down payload', () => {
  it('buildDrillDownTarget emits the correct (from, to, dimension, dimensionValue) shape on a data-point click', () => {
    const buckets: TimeseriesResponse['buckets'] = [
      { time: TS, series: { anthropic: 1 } },
      { time: TS2, series: { anthropic: 2 } },
    ]
    const onDrillDown = vi.fn()
    const target = buildDrillDownTarget(
      buckets,
      0,
      'hour',
      'provider',
      'anthropic',
    )
    onDrillDown(target)
    expect(onDrillDown).toHaveBeenCalledTimes(1)
    expect(onDrillDown).toHaveBeenCalledWith({
      from: TS,
      to: TS2, // bucket-window uses next bucket's time when present
      dimension: 'provider',
      dimensionValue: 'anthropic',
    })

    // Last bucket: window extends one granularity past start
    const lastTarget = buildDrillDownTarget(
      buckets,
      1,
      'hour',
      'provider',
      'anthropic',
    )
    expect(lastTarget.from).toBe(TS2)
    expect(new Date(lastTarget.to).getTime() - new Date(TS2).getTime()).toBe(
      3_600_000,
    )
  })
})

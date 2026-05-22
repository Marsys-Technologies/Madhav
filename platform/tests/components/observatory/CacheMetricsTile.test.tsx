/**
 * D-S6: CacheMetricsTile.test.tsx
 *
 * Tests for the Observatory cache hit rate dashboard tile (R11.D).
 *
 * AC1: Tile renders hit rate per provider.
 * AC2: Cost savings shown per provider.
 * AC3: NVIDIA shows "n/a" (null cacheMode).
 * AC4: computeProviderSummaries aggregates rows correctly.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CacheMetricsTile } from '../../../src/components/observatory/CacheMetricsTile'
import {
  computeProviderSummaries,
  formatHitRate,
  formatCostSavings,
  PROVIDER_CACHE_MODE,
  ALL_PROVIDER_IDS,
} from '../../../src/lib/observatory/cache_aggregation'
import type { CacheProviderSummary } from '../../../src/lib/observatory/cache_aggregation'

// ---------------------------------------------------------------------------
// computeProviderSummaries
// ---------------------------------------------------------------------------

describe('D-S6: computeProviderSummaries', () => {
  it('returns 5 summaries (one per provider)', () => {
    const result = computeProviderSummaries([])
    expect(result).toHaveLength(5)
    expect(result.map(r => r.provider)).toEqual(ALL_PROVIDER_IDS as unknown as string[])
  })

  it('aggregates hit counts correctly', () => {
    const rows = [
      { provider: 'anthropic', hitRequests: 10, totalRequests: 20, estimatedCostSavingsRatio: -0.5 },
      { provider: 'anthropic', hitRequests: 5, totalRequests: 10, estimatedCostSavingsRatio: -0.4 },
    ]
    const summaries = computeProviderSummaries(rows)
    const anthro = summaries.find(s => s.provider === 'anthropic')!
    expect(anthro.totalHitRequests).toBe(15)
    expect(anthro.totalRequests).toBe(30)
    expect(anthro.overallHitRate).toBeCloseTo(0.5)
  })

  it('overallHitRate is 0 when no requests', () => {
    const summaries = computeProviderSummaries([])
    for (const s of summaries) {
      expect(s.overallHitRate).toBe(0)
    }
  })

  it('NVIDIA summary has supported=false', () => {
    const summaries = computeProviderSummaries([])
    const nvidia = summaries.find(s => s.provider === 'nvidia')!
    expect(nvidia.supported).toBe(false)
    expect(nvidia.cacheMode).toBeNull()
  })

  it('all non-NVIDIA providers have supported=true', () => {
    const summaries = computeProviderSummaries([])
    for (const s of summaries.filter(s => s.provider !== 'nvidia')) {
      expect(s.supported).toBe(true)
    }
  })
})

// ---------------------------------------------------------------------------
// PROVIDER_CACHE_MODE constants
// ---------------------------------------------------------------------------

describe('D-S6: PROVIDER_CACHE_MODE', () => {
  it('anthropic is explicit_4bp', () => {
    expect(PROVIDER_CACHE_MODE.anthropic).toBe('explicit_4bp')
  })
  it('google is cached_content_api', () => {
    expect(PROVIDER_CACHE_MODE.google).toBe('cached_content_api')
  })
  it('openai is automatic', () => {
    expect(PROVIDER_CACHE_MODE.openai).toBe('automatic')
  })
  it('deepseek is implicit', () => {
    expect(PROVIDER_CACHE_MODE.deepseek).toBe('implicit')
  })
  it('nvidia is null', () => {
    expect(PROVIDER_CACHE_MODE.nvidia).toBeNull()
  })
})

// ---------------------------------------------------------------------------
// formatHitRate + formatCostSavings
// ---------------------------------------------------------------------------

describe('D-S6: formatHitRate', () => {
  it('formats 0 as "0%"', () => {
    expect(formatHitRate(0)).toBe('0%')
  })
  it('formats 0.843 as "84.3%"', () => {
    expect(formatHitRate(0.843)).toBe('84.3%')
  })
  it('formats 1.0 as "100.0%"', () => {
    expect(formatHitRate(1.0)).toBe('100.0%')
  })
})

describe('D-S6: formatCostSavings', () => {
  it('returns "n/a" when not supported', () => {
    expect(formatCostSavings(0, false)).toBe('n/a')
    expect(formatCostSavings(-0.5, false)).toBe('n/a')
  })
  it('returns "0%" for 0 ratio (supported)', () => {
    expect(formatCostSavings(0, true)).toBe('0%')
  })
  it('formats negative ratio as "–X%" (savings)', () => {
    expect(formatCostSavings(-0.5, true)).toBe('–50.0%')
  })
  it('formats positive ratio as "+X%" (surcharge)', () => {
    expect(formatCostSavings(0.25, true)).toBe('+25.0%')
  })
})

// ---------------------------------------------------------------------------
// CacheMetricsTile rendering
// ---------------------------------------------------------------------------

function makeSummaries(): CacheProviderSummary[] {
  return [
    { provider: 'anthropic', cacheMode: 'explicit_4bp', supported: true, totalRequests: 100, totalHitRequests: 80, overallHitRate: 0.8, avgCostSavingsRatio: -0.45 },
    { provider: 'google', cacheMode: 'cached_content_api', supported: true, totalRequests: 50, totalHitRequests: 40, overallHitRate: 0.8, avgCostSavingsRatio: -0.6 },
    { provider: 'openai', cacheMode: 'automatic', supported: true, totalRequests: 30, totalHitRequests: 20, overallHitRate: 0.667, avgCostSavingsRatio: -0.2 },
    { provider: 'deepseek', cacheMode: 'implicit', supported: true, totalRequests: 10, totalHitRequests: 7, overallHitRate: 0.7, avgCostSavingsRatio: -0.15 },
    { provider: 'nvidia', cacheMode: null, supported: false, totalRequests: 0, totalHitRequests: 0, overallHitRate: 0, avgCostSavingsRatio: 0 },
  ]
}

describe('D-S6: CacheMetricsTile rendering', () => {
  it('renders tile with title', () => {
    render(<CacheMetricsTile summaries={makeSummaries()} />)
    expect(screen.getByTestId('cache-tile-title')).toBeTruthy()
    expect(screen.getByTestId('cache-tile-title').textContent).toContain('Cache Hit Rates')
  })

  it('renders 5 provider rows', () => {
    render(<CacheMetricsTile summaries={makeSummaries()} />)
    const providerIds = ['anthropic', 'google', 'openai', 'deepseek', 'nvidia']
    for (const id of providerIds) {
      expect(screen.getByTestId(`cache-metrics-row-${id}`)).toBeTruthy()
    }
  })

  it('AC3: NVIDIA row shows "n/a" hit rate', () => {
    render(<CacheMetricsTile summaries={makeSummaries()} />)
    const nvidiaHitRate = screen.getByTestId('hit-rate-nvidia')
    expect(nvidiaHitRate.textContent).toBe('n/a')
  })

  it('AC3: NVIDIA cost savings shows "n/a"', () => {
    render(<CacheMetricsTile summaries={makeSummaries()} />)
    const nvidiaCost = screen.getByTestId('cost-savings-nvidia')
    expect(nvidiaCost.textContent).toBe('n/a')
  })

  it('AC1: Anthropic hit rate rendered', () => {
    render(<CacheMetricsTile summaries={makeSummaries()} />)
    const anthroRate = screen.getByTestId('hit-rate-anthropic')
    expect(anthroRate.textContent).toBe('80.0%')
  })

  it('renders date range when provided', () => {
    render(<CacheMetricsTile summaries={makeSummaries()} dateRange="2026-05-15 → 2026-05-22" />)
    const dateRange = screen.getByTestId('cache-tile-date-range')
    expect(dateRange.textContent).toContain('2026-05-15')
  })

  it('cache mode badges render for each supported provider', () => {
    render(<CacheMetricsTile summaries={makeSummaries()} />)
    expect(screen.getByTestId('cache-mode-badge-anthropic').textContent).toBe('4-breakpoint')
    expect(screen.getByTestId('cache-mode-badge-google').textContent).toBe('cachedContent')
    expect(screen.getByTestId('cache-mode-badge-openai').textContent).toBe('automatic')
    expect(screen.getByTestId('cache-mode-badge-deepseek').textContent).toBe('implicit')
    expect(screen.getByTestId('cache-mode-badge-nvidia').textContent).toBe('n/a')
  })
})

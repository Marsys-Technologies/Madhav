// Phase O — O.4 Analytics — USTAD_S4_4 pricing diff core module + panel tests.
//
// Layout:
//   §A  classification matrix (5): stale-only / variance-only / both / ok /
//                                  alert_fired flag
//   §B  alert dispatch (2): webhook fires when env set; never throws on
//                           webhook failure; provider union from both tables
//   §C  PricingDiffPanel render (1): all_healthy=false → warn banner +
//                                    per-provider chips
//
// Discipline:
//   - The DB is mocked via the QueryFn injection contract so no real pg
//     connection is needed.
//   - fetch is replaced on globalThis to assert webhook payload shape and
//     swallow-not-throw behaviour.
//   - jsdom (vitest config default) is used so the §C render test works
//     without environment switching.

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

import {
  STALE_PRICING_THRESHOLD_DAYS,
  SYSTEMATIC_VARIANCE_THRESHOLD_PCT,
  checkPricingHealth,
  type PricingDiffResult,
} from '@/lib/observatory/analytics/pricing_diff'
import { PricingDiffPanel } from '@/lib/components/observatory/analytics/PricingDiffPanel'

interface PricingFreshnessRow {
  provider: string
  last_pricing_update: string | null
}
interface VarianceRow {
  provider: string
  avg_abs_variance_pct: number | null
}

function isoDaysAgo(days: number, ref: Date = new Date()): string {
  const ms = ref.getTime() - days * 86_400_000
  return new Date(ms).toISOString().slice(0, 10)
}

interface MockQueryArgs {
  freshness: PricingFreshnessRow[]
  variance: VarianceRow[]
}

function makeQuery(args: MockQueryArgs) {
  return vi
    .fn()
    .mockImplementationOnce(async () => ({ rows: args.freshness }))
    .mockImplementationOnce(async () => ({ rows: args.variance }))
}

describe('§A — checkPricingHealth classification', () => {
  let warnSpy: ReturnType<typeof vi.spyOn>
  let originalFetch: typeof globalThis.fetch
  const originalWebhook = process.env.OBSERVATORY_ALERT_WEBHOOK_URL

  beforeEach(() => {
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    originalFetch = globalThis.fetch
    delete process.env.OBSERVATORY_ALERT_WEBHOOK_URL
  })

  afterEach(() => {
    warnSpy.mockRestore()
    globalThis.fetch = originalFetch
    if (originalWebhook === undefined) {
      delete process.env.OBSERVATORY_ALERT_WEBHOOK_URL
    } else {
      process.env.OBSERVATORY_ALERT_WEBHOOK_URL = originalWebhook
    }
  })

  it('1. is_pricing_stale=true when pricing_age_days > 30', async () => {
    const queryFn = makeQuery({
      freshness: [
        {
          provider: 'anthropic',
          last_pricing_update: isoDaysAgo(STALE_PRICING_THRESHOLD_DAYS + 5),
        },
      ],
      variance: [{ provider: 'anthropic', avg_abs_variance_pct: 1.0 }],
    })
    const result = await checkPricingHealth(queryFn)
    const p = result.providers[0]
    expect(p.provider).toBe('anthropic')
    expect(p.is_pricing_stale).toBe(true)
    expect(p.pricing_age_days).toBeGreaterThan(STALE_PRICING_THRESHOLD_DAYS)
    expect(p.has_systematic_variance).toBe(false)
    expect(p.status).toBe('stale_pricing')
    expect(result.stale_count).toBe(1)
    expect(result.variance_alert_count).toBe(0)
    expect(result.all_healthy).toBe(false)
  })

  it('2. has_systematic_variance=true when avg_7d_variance_pct > 5.0', async () => {
    const queryFn = makeQuery({
      freshness: [{ provider: 'openai', last_pricing_update: isoDaysAgo(2) }],
      variance: [
        {
          provider: 'openai',
          avg_abs_variance_pct: SYSTEMATIC_VARIANCE_THRESHOLD_PCT + 0.5,
        },
      ],
    })
    const result = await checkPricingHealth(queryFn)
    const p = result.providers[0]
    expect(p.is_pricing_stale).toBe(false)
    expect(p.has_systematic_variance).toBe(true)
    expect(p.avg_7d_variance_pct).toBeGreaterThan(
      SYSTEMATIC_VARIANCE_THRESHOLD_PCT,
    )
    expect(p.status).toBe('systematic_variance')
    expect(result.variance_alert_count).toBe(1)
    expect(result.stale_count).toBe(0)
  })

  it("3. status='both' when stale AND systematic variance", async () => {
    const queryFn = makeQuery({
      freshness: [
        {
          provider: 'gemini',
          last_pricing_update: isoDaysAgo(STALE_PRICING_THRESHOLD_DAYS + 10),
        },
      ],
      variance: [{ provider: 'gemini', avg_abs_variance_pct: 12.5 }],
    })
    const result = await checkPricingHealth(queryFn)
    const p = result.providers[0]
    expect(p.is_pricing_stale).toBe(true)
    expect(p.has_systematic_variance).toBe(true)
    expect(p.status).toBe('both')
    expect(p.alert_fired).toBe(true)
    expect(result.stale_count).toBe(1)
    expect(result.variance_alert_count).toBe(1)
  })

  it("4. alert_fired=false when status='ok'", async () => {
    const queryFn = makeQuery({
      freshness: [{ provider: 'deepseek', last_pricing_update: isoDaysAgo(3) }],
      variance: [{ provider: 'deepseek', avg_abs_variance_pct: 0.4 }],
    })
    const result = await checkPricingHealth(queryFn)
    const p = result.providers[0]
    expect(p.status).toBe('ok')
    expect(p.alert_fired).toBe(false)
    expect(result.all_healthy).toBe(true)
    expect(warnSpy).not.toHaveBeenCalled()
  })

  it("5. alert_fired=true when status != 'ok' (mock webhook dispatch)", async () => {
    process.env.OBSERVATORY_ALERT_WEBHOOK_URL = 'https://hook.example/pricing'
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response('ok', { status: 200 }))
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch

    const queryFn = makeQuery({
      freshness: [
        {
          provider: 'nim',
          last_pricing_update: isoDaysAgo(STALE_PRICING_THRESHOLD_DAYS + 1),
        },
      ],
      variance: [{ provider: 'nim', avg_abs_variance_pct: 0.0 }],
    })
    const result = await checkPricingHealth(queryFn)
    const p = result.providers[0]
    expect(p.status).toBe('stale_pricing')
    expect(p.alert_fired).toBe(true)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('https://hook.example/pricing')
    expect((init as RequestInit).method).toBe('POST')
    const body = JSON.parse(String((init as RequestInit).body))
    expect(body.provider).toBe('nim')
    expect(body.status).toBe('stale_pricing')
    expect(body.detail.is_pricing_stale).toBe(true)
    expect(warnSpy).toHaveBeenCalled()
  })
})

describe('§B — alert dispatch resilience', () => {
  let warnSpy: ReturnType<typeof vi.spyOn>
  let originalFetch: typeof globalThis.fetch
  const originalWebhook = process.env.OBSERVATORY_ALERT_WEBHOOK_URL

  beforeEach(() => {
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    originalFetch = globalThis.fetch
  })

  afterEach(() => {
    warnSpy.mockRestore()
    globalThis.fetch = originalFetch
    if (originalWebhook === undefined) {
      delete process.env.OBSERVATORY_ALERT_WEBHOOK_URL
    } else {
      process.env.OBSERVATORY_ALERT_WEBHOOK_URL = originalWebhook
    }
  })

  it('6. webhook failure does not throw; alert_fired still true', async () => {
    process.env.OBSERVATORY_ALERT_WEBHOOK_URL = 'https://hook.example/down'
    const fetchMock = vi
      .fn()
      .mockRejectedValue(new Error('network unreachable'))
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch

    const queryFn = makeQuery({
      freshness: [{ provider: 'openai', last_pricing_update: isoDaysAgo(2) }],
      variance: [{ provider: 'openai', avg_abs_variance_pct: 9.9 }],
    })
    let threw = false
    let result
    try {
      result = await checkPricingHealth(queryFn)
    } catch {
      threw = true
    }
    expect(threw).toBe(false)
    expect(result).toBeDefined()
    const p = result!.providers[0]
    expect(p.status).toBe('systematic_variance')
    expect(p.alert_fired).toBe(true)
    // The console.warn should have fired both for the alert headline and the
    // webhook failure note.
    expect(warnSpy.mock.calls.length).toBeGreaterThanOrEqual(2)
  })

  it('7. providers in pricing-only or variance-only tables are unioned', async () => {
    const queryFn = makeQuery({
      freshness: [
        { provider: 'anthropic', last_pricing_update: isoDaysAgo(2) },
      ],
      variance: [{ provider: 'openai', avg_abs_variance_pct: 1.0 }],
    })
    const result = await checkPricingHealth(queryFn)
    const names = result.providers.map((p) => p.provider).sort()
    expect(names).toEqual(['anthropic', 'openai'])
    const openai = result.providers.find((p) => p.provider === 'openai')!
    expect(openai.last_pricing_update).toBeNull()
    expect(openai.is_pricing_stale).toBe(true) // never seen → infinite age
    expect(openai.status).toBe('stale_pricing')
  })
})

describe('§C — PricingDiffPanel render', () => {
  it('8. all_healthy=false → warn banner + per-provider chip rendered', () => {
    const fixture: PricingDiffResult = {
      checked_at: '2026-05-03T10:00:00Z',
      stale_count: 1,
      variance_alert_count: 1,
      all_healthy: false,
      providers: [
        {
          provider: 'anthropic',
          last_pricing_update: '2025-01-01',
          pricing_age_days: 487,
          is_pricing_stale: true,
          avg_7d_variance_pct: 7.5,
          has_systematic_variance: true,
          status: 'both',
          alert_fired: true,
        },
        {
          provider: 'openai',
          last_pricing_update: '2026-05-01',
          pricing_age_days: 2,
          is_pricing_stale: false,
          avg_7d_variance_pct: 0.3,
          has_systematic_variance: false,
          status: 'ok',
          alert_fired: false,
        },
      ],
    }
    render(React.createElement(PricingDiffPanel, { initialResult: fixture }))
    expect(screen.getByTestId('pricing-diff-banner-warn')).toBeInTheDocument()
    expect(
      screen.queryByTestId('pricing-diff-banner-ok'),
    ).not.toBeInTheDocument()
    expect(screen.getByTestId('pricing-diff-row-anthropic')).toBeInTheDocument()
    expect(screen.getByTestId('pricing-diff-row-openai')).toBeInTheDocument()
    expect(
      screen.getByTestId('pricing-diff-chip-anthropic').textContent,
    ).toContain('Stale + variance')
    expect(
      screen.getByTestId('pricing-diff-chip-openai').textContent,
    ).toContain('OK')
  })
})

describe('webhook transport outcome', () => {
  const now = new Date('2026-06-01T12:00:00.000Z')
  const lastUpdate = '2026-04-01T12:00:00.000Z'
  const webhook = 'https://hook.example/transport'
  const staleRow = {
    provider: 'fixture',
    last_pricing_update: lastUpdate,
    pricing_age_days: 61,
    is_pricing_stale: true,
    avg_7d_variance_pct: 7,
    has_systematic_variance: true,
    status: 'both',
  } as const
  let fetchMock: ReturnType<typeof vi.fn>

  function staleQuery() {
    return makeQuery({
      freshness: [{ provider: staleRow.provider, last_pricing_update: lastUpdate }],
      variance: [{ provider: staleRow.provider, avg_abs_variance_pct: 7 }],
    })
  }

  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(now)
    vi.stubEnv('OBSERVATORY_ALERT_WEBHOOK_URL', webhook)
    fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it.each([
    [200, 'http_accepted'],
    [202, 'http_accepted'],
    [204, 'http_accepted'],
    [503, 'http_error'],
  ])('preserves the trigger and reports HTTP %i as %s', async (status, expected) => {
    const response = new Response(null, { status })
    const readBody = vi.spyOn(response, 'text')
    const readJson = vi.spyOn(response, 'json')
    fetchMock.mockResolvedValueOnce(response)
    const queryFn = staleQuery()

    expect(await checkPricingHealth(queryFn)).toEqual({
      checked_at: now.toISOString(),
      providers: [{ ...staleRow, alert_fired: true, alert_webhook_result: expected }],
      stale_count: 1,
      variance_alert_count: 1,
      all_healthy: false,
    })
    expect(queryFn.mock.calls).toEqual([
      ['SELECT provider, MAX(effective_from)::text AS last_pricing_update FROM llm_pricing_versions GROUP BY provider'],
      ["SELECT provider, AVG(ABS(variance_pct)) AS avg_abs_variance_pct FROM llm_cost_reconciliation WHERE reconciliation_date >= (NOW() - INTERVAL '7 days')::date   AND variance_pct IS NOT NULL GROUP BY provider"],
    ])
    expect(fetchMock.mock.calls).toEqual([[
      webhook,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: staleRow.provider,
          status: 'both',
          detail: { ...staleRow, alert_fired: false },
        }),
        signal: expect.any(AbortSignal),
      },
    ]])
    expect(readBody).not.toHaveBeenCalled()
    expect(readJson).not.toHaveBeenCalled()
    expect(vi.getTimerCount()).toBe(0)
  })

  it('reports healthy as not attempted even when a webhook is configured', async () => {
    const result = await checkPricingHealth(makeQuery({
      freshness: [{ provider: 'fixture', last_pricing_update: now.toISOString() }],
      variance: [],
    }))
    expect(result.providers[0]).toMatchObject({
      alert_fired: false, alert_webhook_result: 'not_attempted',
    })
    expect(fetchMock).not.toHaveBeenCalled()
    expect(vi.getTimerCount()).toBe(0)
  })

  it('reports an unhealthy trigger without a configured webhook', async () => {
    vi.stubEnv('OBSERVATORY_ALERT_WEBHOOK_URL', '')
    const result = await checkPricingHealth(staleQuery())
    expect(result.providers[0]).toMatchObject({
      alert_fired: true, alert_webhook_result: 'not_configured',
    })
    expect(fetchMock).not.toHaveBeenCalled()
    expect(vi.getTimerCount()).toBe(0)
  })

  it('reports an unknown outcome when the response is lost, with no retry', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('response lost'))
    const result = await checkPricingHealth(staleQuery())
    expect(result.providers[0]).toMatchObject({
      alert_fired: true, alert_webhook_result: 'unknown',
    })
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('aborts after 5 seconds and reports an unknown outcome without retry', async () => {
    let signal: AbortSignal | undefined
    fetchMock.mockImplementationOnce((_target: string, init: RequestInit) => {
      signal = init.signal ?? undefined
      return new Promise<Response>((_resolve, reject) => {
        signal?.addEventListener('abort', () => reject(new Error('timeout')), { once: true })
      })
    })
    const pending = checkPricingHealth(staleQuery())
    await vi.advanceTimersByTimeAsync(4_999)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(signal?.aborted).toBe(false)
    await vi.advanceTimersByTimeAsync(1)
    expect(signal?.aborted).toBe(true)
    expect((await pending).providers[0]).toMatchObject({
      alert_fired: true, alert_webhook_result: 'unknown',
    })
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('contains an unexpected alert setup failure', async () => {
    vi.spyOn(console, 'warn').mockImplementationOnce(() => { throw new Error('alert setup failed') })
    const result = await checkPricingHealth(staleQuery())
    expect(result.providers[0]).toMatchObject({
      alert_fired: true, alert_webhook_result: 'unknown',
    })
    expect(fetchMock).not.toHaveBeenCalled()
    expect(vi.getTimerCount()).toBe(0)
  })

  it('shows the same panel state with or without transport metadata', () => {
    const legacy: PricingDiffResult = {
      checked_at: now.toISOString(),
      providers: [{ ...staleRow, alert_fired: true }],
      stale_count: 1,
      variance_alert_count: 1,
      all_healthy: false,
    }
    const reported: PricingDiffResult = {
      ...legacy, providers: [{ ...staleRow, alert_fired: true, alert_webhook_result: 'http_accepted' }],
    }
    const { container, rerender } = render(React.createElement(PricingDiffPanel, { initialResult: legacy }))
    const before = container.innerHTML
    rerender(React.createElement(PricingDiffPanel, { key: 'reported', initialResult: reported }))
    expect(container.innerHTML).toBe(before)
    expect(screen.getByTestId('pricing-diff-chip-fixture')).toHaveTextContent('Stale + variance')
  })
})

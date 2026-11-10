// @vitest-environment node
//
// USTAD_S4_5 — Replay & Re-cost engine tests.
//
// Test plan (8 tests across module + UI; API tests live in
// src/app/api/admin/observatory/analytics/replay/__tests__/):
//   §A  replayAndRecost — happy path under known pricing
//   §B  Delta sign — positive when new prices are higher; negative when lower
//   §C  No anchor: latest-effective pricing is used per (provider, model)
//   §D  limit > hard-cap → throws
//   §E  Read-only — engine never issues UPDATE/INSERT/DELETE on llm_usage_events
//   §F  listReplayPricingVersions — returns the pricing-version dropdown rows
//
// Component test (ReplayPanel — empty state) lives in
// src/lib/components/observatory/__tests__/analytics/replay_ui.test.tsx.

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
  getPool: vi.fn(),
}))

import {
  REPLAY_DEFAULT_LIMIT,
  REPLAY_HARD_CAP_LIMIT,
  listReplayPricingVersions,
  replayAndRecost,
} from '../replay'

beforeEach(() => {
  queryMock.mockReset()
})

// ---------------------------------------------------------------------------
// §A — Happy path: known pricing, simple recompute
// ---------------------------------------------------------------------------

describe('§A — replayAndRecost happy path', () => {
  it('1. returns a ReplayResult with original/recost totals matching the seed math', async () => {
    // Pricing rows: anthropic / claude-opus-4-7
    //   input  = $15.00 / 1M
    //   output = $75.00 / 1M
    // No anchor passed: engine pulls latest pricing per (provider, model).
    queryMock.mockImplementation((sql: string) => {
      if (sql.includes('FROM llm_usage_events')) {
        return {
          rows: [
            {
              event_id: 'e-1',
              provider: 'anthropic',
              model: 'claude-opus-4-7',
              input_tokens: 1_000_000,
              output_tokens: 200_000,
              cache_read_tokens: 0,
              cache_write_tokens: 0,
              reasoning_tokens: 0,
              computed_cost_usd: 30, // pretend old cost
            },
          ],
        }
      }
      if (sql.includes('DISTINCT ON (provider, model, token_class)')) {
        return {
          rows: [
            {
              pricing_version_id: 'pv-1',
              provider: 'anthropic',
              model: 'claude-opus-4-7',
              token_class: 'input',
              price_per_million_usd: 15,
              effective_from: '2026-04-01',
            },
            {
              pricing_version_id: 'pv-1',
              provider: 'anthropic',
              model: 'claude-opus-4-7',
              token_class: 'output',
              price_per_million_usd: 75,
              effective_from: '2026-04-01',
            },
          ],
        }
      }
      return { rows: [] }
    })

    const result = await replayAndRecost({
      date_start: '2026-04-01',
      date_end: '2026-04-30',
    })

    // Recost = 1_000_000 * 15 / 1M + 200_000 * 75 / 1M = 15 + 15 = 30
    expect(result.events_processed).toBe(1)
    expect(result.original_total_usd).toBe(30)
    expect(result.recost_total_usd).toBeCloseTo(30, 6)
    expect(result.delta_total_usd).toBeCloseTo(0, 6)
    expect(result.target_pricing_version_id).toBe('pv-1')
    expect(result.target_pricing_effective_from).toBe('2026-04-01')
    expect(result.breakdown).toHaveLength(1)
    expect(result.breakdown[0].provider).toBe('anthropic')
    expect(result.breakdown[0].model).toBe('claude-opus-4-7')
    expect(result.breakdown[0].event_count).toBe(1)
  })
})

// ---------------------------------------------------------------------------
// §B — Delta sign: new prices higher → positive delta; lower → negative
// ---------------------------------------------------------------------------

describe('§B — delta sign', () => {
  it('2. delta_total_usd > 0 when new prices are higher than original', async () => {
    queryMock.mockImplementation((sql: string) => {
      if (sql.includes('FROM llm_usage_events')) {
        return {
          rows: [
            {
              event_id: 'e-1',
              provider: 'openai',
              model: 'gpt-4.1',
              input_tokens: 1_000_000,
              output_tokens: 0,
              cache_read_tokens: 0,
              cache_write_tokens: 0,
              reasoning_tokens: 0,
              computed_cost_usd: 5, // original $5
            },
          ],
        }
      }
      if (sql.includes('DISTINCT ON (provider, model, token_class)')) {
        return {
          rows: [
            {
              pricing_version_id: 'pv-2',
              provider: 'openai',
              model: 'gpt-4.1',
              token_class: 'input',
              price_per_million_usd: 12, // new $12 / 1M
              effective_from: '2026-05-01',
            },
          ],
        }
      }
      return { rows: [] }
    })

    const result = await replayAndRecost({
      date_start: '2026-04-01',
      date_end: '2026-04-30',
    })

    // Recost = 1_000_000 * 12 / 1M = 12
    expect(result.recost_total_usd).toBe(12)
    expect(result.original_total_usd).toBe(5)
    expect(result.delta_total_usd).toBe(7)
    expect(result.delta_total_pct).toBeCloseTo(140, 6)
  })

  it('3. delta_total_usd < 0 when new prices are lower than original', async () => {
    queryMock.mockImplementation((sql: string) => {
      if (sql.includes('FROM llm_usage_events')) {
        return {
          rows: [
            {
              event_id: 'e-1',
              provider: 'gemini',
              model: 'gemini-2.5-pro',
              input_tokens: 2_000_000,
              output_tokens: 0,
              cache_read_tokens: 0,
              cache_write_tokens: 0,
              reasoning_tokens: 0,
              computed_cost_usd: 20, // original $20
            },
          ],
        }
      }
      if (sql.includes('DISTINCT ON (provider, model, token_class)')) {
        return {
          rows: [
            {
              pricing_version_id: 'pv-3',
              provider: 'gemini',
              model: 'gemini-2.5-pro',
              token_class: 'input',
              price_per_million_usd: 5, // new $5 / 1M
              effective_from: '2026-05-15',
            },
          ],
        }
      }
      return { rows: [] }
    })

    const result = await replayAndRecost({
      date_start: '2026-04-01',
      date_end: '2026-04-30',
    })

    // Recost = 2_000_000 * 5 / 1M = 10; delta = 10 - 20 = -10
    expect(result.recost_total_usd).toBe(10)
    expect(result.original_total_usd).toBe(20)
    expect(result.delta_total_usd).toBe(-10)
    expect(result.delta_total_pct).toBeCloseTo(-50, 6)
  })
})

// ---------------------------------------------------------------------------
// §C — No anchor → latest pricing per (provider, model)
// ---------------------------------------------------------------------------

describe('§C — no target_pricing_version_id', () => {
  it('4. omitting target_pricing_version_id pulls latest pricing per key', async () => {
    queryMock.mockImplementation((sql: string) => {
      if (sql.includes('FROM llm_usage_events')) {
        return { rows: [] }
      }
      if (sql.includes('DISTINCT ON (provider, model, token_class)')) {
        return {
          rows: [
            {
              pricing_version_id: 'pv-old',
              provider: 'anthropic',
              model: 'claude-haiku-4-5',
              token_class: 'input',
              price_per_million_usd: 0.8,
              effective_from: '2026-01-01',
            },
            {
              pricing_version_id: 'pv-new',
              provider: 'anthropic',
              model: 'claude-haiku-4-5',
              token_class: 'output',
              price_per_million_usd: 4.0,
              effective_from: '2026-04-15',
            },
          ],
        }
      }
      return { rows: [] }
    })

    const result = await replayAndRecost({
      date_start: '2026-04-01',
      date_end: '2026-04-30',
    })

    expect(result.events_processed).toBe(0)
    // Most recent effective_from across both pricing rows is 2026-04-15.
    expect(result.target_pricing_effective_from).toBe('2026-04-15')
    expect(result.target_pricing_version_id).toBe('pv-new')

    // The DISTINCT-ON select was issued (no target lookup happened).
    const calls = queryMock.mock.calls.map((c) => c[0] as string)
    expect(calls.some((s) => s.includes('DISTINCT ON'))).toBe(true)
    expect(
      calls.some((s) => s.includes('WHERE pricing_version_id = $1')),
    ).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// §D — Limit cap
// ---------------------------------------------------------------------------

describe('§D — limit hard cap', () => {
  it('5. limit > 50_000 throws', async () => {
    await expect(
      replayAndRecost({
        date_start: '2026-04-01',
        date_end: '2026-04-30',
        limit: REPLAY_HARD_CAP_LIMIT + 1,
      }),
    ).rejects.toThrow(/exceeds hard cap/)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('6. default limit when omitted is 10_000 (passed as last SQL bind param)', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] }) // events
    queryMock.mockResolvedValueOnce({ rows: [] }) // pricing

    await replayAndRecost({
      date_start: '2026-04-01',
      date_end: '2026-04-30',
    })

    const eventsCall = queryMock.mock.calls.find((c) =>
      (c[0] as string).includes('FROM llm_usage_events'),
    )
    expect(eventsCall).toBeDefined()
    const params = eventsCall![1] as unknown[]
    // Last bound param is the LIMIT value.
    expect(params[params.length - 1]).toBe(REPLAY_DEFAULT_LIMIT)
  })
})

// ---------------------------------------------------------------------------
// §E — Read-only contract
// ---------------------------------------------------------------------------

describe('§E — read-only contract', () => {
  it('7. replayAndRecost never issues UPDATE/INSERT/DELETE on llm_usage_events', async () => {
    queryMock.mockImplementation((sql: string) => {
      if (sql.includes('FROM llm_usage_events')) {
        return {
          rows: [
            {
              event_id: 'e-1',
              provider: 'anthropic',
              model: 'claude-opus-4-7',
              input_tokens: 100,
              output_tokens: 50,
              cache_read_tokens: 0,
              cache_write_tokens: 0,
              reasoning_tokens: 0,
              computed_cost_usd: 0.005,
            },
          ],
        }
      }
      if (sql.includes('DISTINCT ON (provider, model, token_class)')) {
        return {
          rows: [
            {
              pricing_version_id: 'pv-x',
              provider: 'anthropic',
              model: 'claude-opus-4-7',
              token_class: 'input',
              price_per_million_usd: 15,
              effective_from: '2026-04-01',
            },
            {
              pricing_version_id: 'pv-x',
              provider: 'anthropic',
              model: 'claude-opus-4-7',
              token_class: 'output',
              price_per_million_usd: 75,
              effective_from: '2026-04-01',
            },
          ],
        }
      }
      return { rows: [] }
    })

    await replayAndRecost({
      date_start: '2026-04-01',
      date_end: '2026-04-30',
    })

    const all = queryMock.mock.calls.map((c) => (c[0] as string).toUpperCase())
    for (const sql of all) {
      // No mutation against llm_usage_events anywhere in the engine.
      expect(sql.includes('UPDATE LLM_USAGE_EVENTS')).toBe(false)
      expect(sql.includes('INSERT INTO LLM_USAGE_EVENTS')).toBe(false)
      expect(sql.includes('DELETE FROM LLM_USAGE_EVENTS')).toBe(false)
    }
    // And no mutation verbs anywhere at all.
    expect(all.some((s) => /^\s*UPDATE\s+/.test(s))).toBe(false)
    expect(all.some((s) => /^\s*INSERT\s+/.test(s))).toBe(false)
    expect(all.some((s) => /^\s*DELETE\s+/.test(s))).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// §F — listReplayPricingVersions
// ---------------------------------------------------------------------------

describe('§F — listReplayPricingVersions', () => {
  it('8. returns pricing-version rows sorted by effective_from DESC', async () => {
    queryMock.mockResolvedValueOnce({
      rows: [
        {
          pricing_version_id: 'pv-old',
          provider: 'anthropic',
          model: 'claude-opus-4-6',
          effective_from: '2026-01-15',
        },
        {
          pricing_version_id: 'pv-new',
          provider: 'anthropic',
          model: 'claude-opus-4-7',
          effective_from: '2026-04-20',
        },
        {
          pricing_version_id: 'pv-mid',
          provider: 'gemini',
          model: 'gemini-2.5-pro',
          effective_from: '2026-03-10',
        },
      ],
    })

    const versions = await listReplayPricingVersions()
    expect(versions).toHaveLength(3)
    expect(versions[0].effective_from).toBe('2026-04-20')
    expect(versions[1].effective_from).toBe('2026-03-10')
    expect(versions[2].effective_from).toBe('2026-01-15')

    // Verify the SQL is read-only.
    const sql = (queryMock.mock.calls[0][0] as string).toUpperCase()
    expect(sql.startsWith('SELECT')).toBe(true)
    expect(sql.includes('UPDATE')).toBe(false)
    expect(sql.includes('INSERT')).toBe(false)
    expect(sql.includes('DELETE')).toBe(false)
  })
})

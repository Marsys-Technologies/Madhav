// @vitest-environment node
//
// Phase O — O.2 Reconciliation framework: variance + base + API tests.
//
// Authored by USTAD_S2_1_RECONCILIATION_FRAMEWORK. All tests are unit-level
// and DB-mocked — no integration block. The schema-bound tests live with
// their per-provider reconcilers (S2.2–S2.5).

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

import {
  classifyVariance,
} from '@/lib/observatory/reconciliation/variance'
import {
  DEFAULT_RECONCILIATION_CONFIG,
} from '@/lib/observatory/reconciliation/types'
import {
  BaseReconciler,
  type FetchAuthoritativeCostResult,
} from '@/lib/observatory/reconciliation/base'
import type {
  ProviderName,
  ProviderReconcileInput,
} from '@/lib/observatory/reconciliation/types'

// ---------------------------------------------------------------------------
// 1. classifyVariance — pure unit tests, no DB.
// ---------------------------------------------------------------------------

describe('classifyVariance', () => {
  const cfg = DEFAULT_RECONCILIATION_CONFIG // tolerance=2, alert=5

  it('exactly at tolerance_pct boundary classifies as matched', () => {
    expect(classifyVariance(98, 100, cfg)).toBe('matched')
  })

  it('just above tolerance_pct classifies as variance_within_tolerance', () => {
    expect(classifyVariance(97.9, 100, cfg)).toBe('variance_within_tolerance')
  })

  it('exactly at alert_pct boundary classifies as variance_within_tolerance', () => {
    expect(classifyVariance(95, 100, cfg)).toBe('variance_within_tolerance')
  })

  it('just above alert_pct classifies as variance_alert', () => {
    expect(classifyVariance(94.9, 100, cfg)).toBe('variance_alert')
  })

  it('null/undefined/NaN authoritative classifies as missing_authoritative', () => {
    expect(classifyVariance(123, null, cfg)).toBe('missing_authoritative')
    expect(classifyVariance(123, undefined, cfg)).toBe('missing_authoritative')
    expect(classifyVariance(123, NaN, cfg)).toBe('missing_authoritative')
  })

  it('zero authoritative cost (free tier) with zero computed → matched', () => {
    expect(classifyVariance(0, 0, cfg)).toBe('matched')
  })

  it('zero authoritative cost with nonzero computed → variance_alert', () => {
    expect(classifyVariance(5, 0, cfg)).toBe('variance_alert')
  })
})

// ---------------------------------------------------------------------------
// 2. BaseReconciler template method — TestReconciler subclass; query() mocked.
// ---------------------------------------------------------------------------

class TestReconciler extends BaseReconciler {
  readonly provider: ProviderName = 'anthropic'
  constructor(
    private readonly fetcher: (
      input: ProviderReconcileInput,
    ) => Promise<FetchAuthoritativeCostResult>,
  ) {
    super()
  }
  protected fetchAuthoritativeCost(
    input: ProviderReconcileInput,
  ): Promise<FetchAuthoritativeCostResult> {
    return this.fetcher(input)
  }
}

describe('BaseReconciler.reconcile()', () => {
  beforeEach(() => {
    queryMock.mockReset()
  })

  it('successful fetch writes to both tables and returns matched status', async () => {
    queryMock.mockImplementation(async (sql: string) => {
      if (/INSERT INTO llm_provider_cost_reports/.test(sql)) {
        return { rows: [{ report_id: 'r-123' }] }
      }
      if (/FROM llm_usage_events/.test(sql)) {
        return { rows: [{ total_cost_usd: 100, event_count: '7' }] }
      }
      if (/INSERT INTO llm_cost_reconciliation/.test(sql)) {
        return { rows: [] }
      }
      return { rows: [] }
    })

    const reconciler = new TestReconciler(async () => ({
      cost_usd: 100,
      raw_payload: { ok: true },
    }))
    const result = await reconciler.reconcile(
      {
        provider: 'anthropic',
        period_start: '2026-05-01',
        period_end: '2026-05-01',
      },
      DEFAULT_RECONCILIATION_CONFIG,
    )

    expect(result.status).toBe('matched')
    expect(result.computed_cost_usd).toBe(100)
    expect(result.authoritative_cost_usd).toBe(100)
    expect(result.variance_usd).toBe(0)
    expect(result.event_count).toBe(7)
    expect(result.raw_report_id).toBe('r-123')

    const sqlCalls = queryMock.mock.calls.map(c => String(c[0]))
    expect(sqlCalls.some(s => /INSERT INTO llm_provider_cost_reports/.test(s))).toBe(true)
    expect(sqlCalls.some(s => /INSERT INTO llm_cost_reconciliation/.test(s))).toBe(true)
  })

  it('fetchAuthoritativeCost throwing → status=error, never rethrows', async () => {
    queryMock.mockImplementation(async () => ({ rows: [] }))

    const reconciler = new TestReconciler(async () => {
      throw new Error('admin api 500')
    })
    const result = await reconciler.reconcile(
      {
        provider: 'anthropic',
        period_start: '2026-05-01',
        period_end: '2026-05-01',
      },
      DEFAULT_RECONCILIATION_CONFIG,
    )

    expect(result.status).toBe('error')
    expect(result.notes).toContain('admin api 500')
    expect(result.raw_report_id).toBe('')
    expect(result.computed_cost_usd).toBe(0)
  })

  it('variance > alert_pct produces variance_alert status', async () => {
    queryMock.mockImplementation(async (sql: string) => {
      if (/INSERT INTO llm_provider_cost_reports/.test(sql)) {
        return { rows: [{ report_id: 'r-vary' }] }
      }
      if (/FROM llm_usage_events/.test(sql)) {
        return { rows: [{ total_cost_usd: 50, event_count: '3' }] }
      }
      return { rows: [] }
    })

    const reconciler = new TestReconciler(async () => ({
      cost_usd: 100,
      raw_payload: {},
    }))
    const result = await reconciler.reconcile(
      {
        provider: 'anthropic',
        period_start: '2026-05-01',
        period_end: '2026-05-01',
      },
      DEFAULT_RECONCILIATION_CONFIG,
    )

    expect(result.status).toBe('variance_alert')
    expect(result.variance_pct).toBe(50)
  })
})

// ---------------------------------------------------------------------------
// 3. POST /api/admin/observatory/reconciliation — endpoint behavior.
// ---------------------------------------------------------------------------

describe('POST /api/admin/observatory/reconciliation', () => {
  beforeEach(() => {
    queryMock.mockReset()
    vi.resetModules()
    process.env.MARSYS_FLAG_OBSERVATORY_ENABLED = 'true'
    vi.doMock('@/lib/auth/access-control', () => ({
      requireSuperAdmin: async () => ({
        user: { uid: 'admin-1' },
        profile: { id: 'admin-1', role: 'super_admin', status: 'active' },
      }),
    }))
  })

  async function loadRoute() {
    return await import(
      '@/app/api/admin/observatory/reconciliation/route'
    )
  }

  it('returns 400 manual_upload_required for DeepSeek', async () => {
    const { POST } = await loadRoute()
    const request = new Request('http://x/api/admin/observatory/reconciliation', {
      method: 'POST',
      body: JSON.stringify({
        provider: 'deepseek',
        period_start: '2026-05-01',
        period_end: '2026-05-01',
      }),
    })
    const response = await POST(request)
    expect(response).toBeInstanceOf(NextResponse)
    expect(response.status).toBe(400)
    const body = await response.json()
    expect(body.error).toBe('manual_upload_required')
    expect(body.provider).toBe('deepseek')
    expect(body.instructions).toMatch(/CSV/i)
  })

  it('returns 400 manual_upload_required for NIM', async () => {
    const { POST } = await loadRoute()
    const request = new Request('http://x/api/admin/observatory/reconciliation', {
      method: 'POST',
      body: JSON.stringify({
        provider: 'nim',
        period_start: '2026-05-01',
        period_end: '2026-05-01',
      }),
    })
    const response = await POST(request)
    expect(response.status).toBe(400)
    const body = await response.json()
    expect(body.error).toBe('manual_upload_required')
    expect(body.provider).toBe('nim')
  })

  // Anthropic stub-not-implemented test removed at S2.2 — `AnthropicReconciler`
  // is now wired into the factory. End-to-end success behavior is asserted in
  // `./anthropic.test.ts`.

  it('S2.4 ships Gemini — route returns a real reconciliation result, not 400 not_implemented', async () => {
    // Env vars unset in this test → GeminiReconciler.fetchAuthoritativeCost
    // throws "GOOGLE_CLOUD_BILLING_PROJECT_ID not configured", which BaseReconciler
    // catches and turns into a status='error' result. The point of this
    // test is to confirm the route no longer routes Gemini to the
    // not_implemented stub branch — it executes the real reconciler.
    delete process.env.GOOGLE_CLOUD_BILLING_PROJECT_ID
    delete process.env.GOOGLE_CLOUD_BILLING_DATASET_ID
    delete process.env.GOOGLE_CLOUD_BILLING_TABLE_ID
    queryMock.mockImplementation(async () => ({ rows: [] }))
    const { POST } = await loadRoute()
    const request = new Request('http://x/api/admin/observatory/reconciliation', {
      method: 'POST',
      body: JSON.stringify({
        provider: 'gemini',
        period_start: '2026-05-01',
        period_end: '2026-05-02',
      }),
    })
    const response = await POST(request)
    expect(response.status).toBe(200)
    const body = await response.json()
    expect(body.error).toBeUndefined()
    expect(body.provider).toBe('gemini')
    expect(body.status).toBe('error')
    expect(body.notes).toContain('GOOGLE_CLOUD_BILLING_PROJECT_ID not configured')
  })

  it('returns 400 for invalid date format', async () => {
    const { POST } = await loadRoute()
    const request = new Request('http://x/api/admin/observatory/reconciliation', {
      method: 'POST',
      body: JSON.stringify({
        provider: 'anthropic',
        period_start: 'not-a-date',
        period_end: '2026-05-01',
      }),
    })
    const response = await POST(request)
    expect(response.status).toBe(400)
  })

  it('returns 400 when period_end < period_start', async () => {
    const { POST } = await loadRoute()
    const request = new Request('http://x/api/admin/observatory/reconciliation', {
      method: 'POST',
      body: JSON.stringify({
        provider: 'anthropic',
        period_start: '2026-05-05',
        period_end: '2026-05-01',
      }),
    })
    const response = await POST(request)
    expect(response.status).toBe(400)
  })

  it('returns 403 when feature flag is off', async () => {
    process.env.MARSYS_FLAG_OBSERVATORY_ENABLED = 'false'
    const { POST } = await loadRoute()
    const request = new Request('http://x/api/admin/observatory/reconciliation', {
      method: 'POST',
      body: JSON.stringify({
        provider: 'anthropic',
        period_start: '2026-05-01',
        period_end: '2026-05-01',
      }),
    })
    const response = await POST(request)
    expect(response.status).toBe(403)
  })
})

// @vitest-environment node
//
// Phase O — O.3 Budgets — USTAD_S3_1_BUDGET_RULES_FRAMEWORK tests.
//
// 14 tests across the new budget framework + the two deferred O.2 MED fixes
// (RT.O2.3 CSV upload guards, RT.O2.4 partition pruning is covered by an
// in-test commentary on the existing gemini.test.ts and not retested here).
//
// Layout:
//   §A  RT.O2.3 fixes (2): file_too_large + invalid_mime_type
//   §B  computePeriodBounds (3): daily / weekly / monthly
//   §C  classifyBudgetStatus (4): below thresholds / first band / mid band / exceeded
//   §D  evaluateBudgetRule (3): happy path / alert band / DB error never-throws
//   §E  API endpoints (2): POST 201 / DELETE 204 → soft-delete

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

import {
  classifyBudgetStatus,
  computePeriodBounds,
  computeScopeSpend,
  evaluateBudgetRule,
} from '@/lib/observatory/budget/evaluate'
import type {
  BudgetRuleRow,
} from '@/lib/observatory/budget/types'

// ---------------------------------------------------------------------------
// §A — RT.O2.3 fixes (2 tests)
// ---------------------------------------------------------------------------

describe('§A — RT.O2.3 — CSV upload guards', () => {
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

  async function loadUploadRoute() {
    return await import(
      '@/app/api/admin/observatory/reconciliation/upload/route'
    )
  }

  function makeRequest(blob: Blob, fields: Record<string, string> = {}): Request {
    const form = new FormData()
    form.set('provider', fields.provider ?? 'deepseek')
    form.set('period_start', fields.period_start ?? '2026-05-01')
    form.set('period_end', fields.period_end ?? '2026-05-02')
    form.set('file', blob, fields.fileName ?? 'big.csv')
    return new Request(
      'http://x/api/admin/observatory/reconciliation/upload',
      { method: 'POST', body: form },
    )
  }

  it('1. file > 5 MB → 400 file_too_large', async () => {
    // 5 MB + 1 byte
    const oversize = 'a'.repeat(5 * 1024 * 1024 + 1)
    const blob = new Blob([oversize], { type: 'text/csv' })
    const { POST } = await loadUploadRoute()
    const response = await POST(makeRequest(blob))
    expect(response).toBeInstanceOf(NextResponse)
    expect(response.status).toBe(400)
    const body = await response.json()
    expect(body.error).toBe('file_too_large')
    expect(body.max_bytes).toBe(5 * 1024 * 1024)
    expect(body.actual_bytes).toBeGreaterThan(5 * 1024 * 1024)
    // The DB INSERTs must NOT have run.
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('2. unsupported MIME type (image/png) → 400 invalid_mime_type', async () => {
    const blob = new Blob(['fake-png-bytes'], { type: 'image/png' })
    const { POST } = await loadUploadRoute()
    const response = await POST(makeRequest(blob))
    expect(response.status).toBe(400)
    const body = await response.json()
    expect(body.error).toBe('invalid_mime_type')
    expect(body.received).toBe('image/png')
    expect(Array.isArray(body.allowed)).toBe(true)
    expect(body.allowed).toContain('text/csv')
    expect(queryMock).not.toHaveBeenCalled()
  })
})

// ---------------------------------------------------------------------------
// §B — computePeriodBounds (3 tests)
// ---------------------------------------------------------------------------

describe('§B — computePeriodBounds', () => {
  it('3. daily → start === end === asOf in UTC', () => {
    const asOf = new Date('2026-05-15T11:34:00Z')
    const { start, end } = computePeriodBounds('daily', asOf)
    expect(start).toBe('2026-05-15')
    expect(end).toBe('2026-05-15')
  })

  it('4. weekly → ISO Mon..Sun for a Wednesday asOf', () => {
    // 2026-05-13 is a Wednesday (UTC). Mon=2026-05-11, Sun=2026-05-17.
    const asOf = new Date('2026-05-13T16:00:00Z')
    const { start, end } = computePeriodBounds('weekly', asOf)
    expect(start).toBe('2026-05-11')
    expect(end).toBe('2026-05-17')
  })

  it('5. monthly → first..last of the asOf UTC month', () => {
    const asOf = new Date('2026-02-14T05:00:00Z')
    const { start, end } = computePeriodBounds('monthly', asOf)
    // 2026 is not a leap year — Feb has 28 days.
    expect(start).toBe('2026-02-01')
    expect(end).toBe('2026-02-28')
  })
})

// ---------------------------------------------------------------------------
// §C — classifyBudgetStatus (4 tests)
// ---------------------------------------------------------------------------

describe('§C — classifyBudgetStatus', () => {
  const thresholds = [
    { pct: 80, channel: 'log' },
    { pct: 95, channel: 'email' },
  ]

  it('6. pct=0 (no thresholds) → ok', () => {
    expect(classifyBudgetStatus(0, [])).toBe('ok')
    expect(classifyBudgetStatus(0, thresholds)).toBe('ok')
  })

  it('7. pct=79 below first threshold (80) → ok', () => {
    expect(classifyBudgetStatus(79, thresholds)).toBe('ok')
  })

  it('8. pct=85 between [80, 95] thresholds → warning', () => {
    expect(classifyBudgetStatus(85, thresholds)).toBe('warning')
  })

  it('9. pct=100 (regardless of thresholds) → exceeded', () => {
    expect(classifyBudgetStatus(100, thresholds)).toBe('exceeded')
    expect(classifyBudgetStatus(120, [])).toBe('exceeded')
    expect(classifyBudgetStatus(120, thresholds)).toBe('exceeded')
  })
})

// ---------------------------------------------------------------------------
// §D — evaluateBudgetRule (3 tests)
// ---------------------------------------------------------------------------

function makeRule(overrides: Partial<BudgetRuleRow> = {}): BudgetRuleRow {
  return {
    budget_rule_id: 'rule-1',
    name: 'Test Rule',
    scope: 'total',
    scope_value: null,
    period: 'monthly',
    amount_usd: 100,
    alert_thresholds: [{ pct: 80, channel: 'log' }],
    created_by_user_id: null,
    active: true,
    created_at: '2026-05-01T00:00:00Z',
    updated_at: '2026-05-01T00:00:00Z',
    ...overrides,
  }
}

describe('§D — evaluateBudgetRule', () => {
  beforeEach(() => {
    queryMock.mockReset()
  })

  it('10. happy path — spend=50, threshold=100 → status=ok, pct_used=50', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ total_cost_usd: 50 }] })
    const rule = makeRule({
      amount_usd: 100,
      alert_thresholds: [{ pct: 80, channel: 'log' }],
    })
    const result = await evaluateBudgetRule(rule)
    expect(result.current_spend_usd).toBe(50)
    expect(result.amount_usd).toBe(100)
    expect(result.pct_used).toBe(50)
    expect(result.status).toBe('ok')
    expect(result.alerts_triggered).toHaveLength(0)
  })

  it('11. spend=90, threshold=100, alert at 85 → status=alert', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ total_cost_usd: 90 }] })
    const rule = makeRule({
      amount_usd: 100,
      alert_thresholds: [{ pct: 85, channel: 'log' }],
    })
    const result = await evaluateBudgetRule(rule)
    expect(result.pct_used).toBe(90)
    expect(result.status).toBe('alert')
    expect(result.alerts_triggered).toHaveLength(1)
    expect(result.alerts_triggered[0].pct).toBe(85)
  })

  it('12. computeScopeSpend throws → returns status=ok, spend=0, no throw', async () => {
    queryMock.mockRejectedValueOnce(new Error('connection refused'))
    const rule = makeRule({ amount_usd: 100 })
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const result = await evaluateBudgetRule(rule)
    expect(result.current_spend_usd).toBe(0)
    expect(result.pct_used).toBe(0)
    expect(result.status).toBe('ok')
    expect(errorSpy).toHaveBeenCalled()
    errorSpy.mockRestore()
  })

  it('(bonus) computeScopeSpend total scope binds 2 params; provider scope binds 3', async () => {
    queryMock.mockResolvedValue({ rows: [{ total_cost_usd: 0 }] })
    await computeScopeSpend('total', null, '2026-05-01', '2026-05-15')
    const totalCall = queryMock.mock.calls[0]
    expect((totalCall[1] as unknown[])).toHaveLength(2)
    queryMock.mockClear()
    await computeScopeSpend('provider', 'anthropic', '2026-05-01', '2026-05-15')
    const providerCall = queryMock.mock.calls[0]
    expect((providerCall[1] as unknown[])).toHaveLength(3)
    expect((providerCall[1] as unknown[])[2]).toBe('anthropic')
  })
})

// ---------------------------------------------------------------------------
// §E — API endpoints (2 tests)
// ---------------------------------------------------------------------------

describe('§E — Budget rules API endpoints', () => {
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

  it('13. POST /budget-rules with valid input → 201 + rule object', async () => {
    queryMock.mockResolvedValueOnce({
      rows: [
        {
          budget_rule_id: 'br-new-1',
          name: 'Daily provider cap — Anthropic',
          scope: 'provider',
          scope_value: 'anthropic',
          period: 'daily',
          amount_usd: 25,
          alert_thresholds: [{ pct: 80, channel: 'log' }],
          created_by_user_id: 'admin-1',
          active: true,
          created_at: '2026-05-03T10:00:00Z',
          updated_at: '2026-05-03T10:00:00Z',
        },
      ],
    })

    const { POST } = await import(
      '@/app/api/admin/observatory/budget-rules/route'
    )
    const request = new Request(
      'http://x/api/admin/observatory/budget-rules',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Daily provider cap — Anthropic',
          scope: 'provider',
          scope_value: 'anthropic',
          period: 'daily',
          amount_usd: 25,
          alert_thresholds: [{ pct: 80, channel: 'log' }],
        }),
      },
    )
    const response = await POST(request)
    expect(response.status).toBe(201)
    const body = await response.json()
    expect(body.budget_rule_id).toBe('br-new-1')
    expect(body.scope).toBe('provider')
    expect(body.amount_usd).toBe(25)
    expect(body.active).toBe(true)
  })

  it('14a. ND.S3.2.1 — coerceThresholds preserves channel_target when present (round-trip)', async () => {
    // The DB row's alert_thresholds JSONB carries { pct, channel, channel_target };
    // post-fix evaluateBudgetRule must surface channel_target on the
    // alerts_triggered entry that the dispatcher consumes.
    queryMock.mockResolvedValueOnce({ rows: [{ total_cost_usd: 90 }] })
    const rule = makeRule({
      amount_usd: 100,
      alert_thresholds: [
        {
          pct: 80,
          channel: 'webhook',
          channel_target: 'https://hook.example/path',
        },
      ],
    })
    const result = await evaluateBudgetRule(rule)
    expect(result.alerts_triggered).toHaveLength(1)
    expect(result.alerts_triggered[0]).toEqual({
      pct: 80,
      channel: 'webhook',
      channel_target: 'https://hook.example/path',
    })
  })

  it('14b. ND.S3.2.1 — coerceThresholds omits channel_target when source is null/undefined/empty', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ total_cost_usd: 90 }] })
    const rule = makeRule({
      amount_usd: 100,
      alert_thresholds: [
        // Three entries: one with channel_target=null, one undefined, one empty string.
        { pct: 50, channel: 'log', channel_target: null },
        { pct: 60, channel: 'log' },
        { pct: 70, channel: 'log', channel_target: '' },
      ] as unknown as { pct: number; channel: string }[],
    })
    const result = await evaluateBudgetRule(rule)
    expect(result.alerts_triggered).toHaveLength(3)
    for (const triggered of result.alerts_triggered) {
      // Avoid an explicit `undefined` key leaking through; the property must
      // be absent (Object.keys does not list it).
      expect(Object.keys(triggered)).not.toContain('channel_target')
    }
  })

  it('15. DELETE /budget-rules/[id] → 204 (soft-delete) + GET shows active=false', async () => {
    // First call: the DELETE soft-delete UPDATE
    queryMock.mockResolvedValueOnce({
      rows: [{ budget_rule_id: 'br-existing-1' }],
    })
    // Second call: the GET-after-delete fetch
    queryMock.mockResolvedValueOnce({
      rows: [
        {
          budget_rule_id: 'br-existing-1',
          name: 'Soft-deleted rule',
          scope: 'total',
          scope_value: null,
          period: 'monthly',
          amount_usd: 500,
          alert_thresholds: [],
          created_by_user_id: null,
          active: false,
          created_at: '2026-05-01T00:00:00Z',
          updated_at: '2026-05-03T10:00:00Z',
        },
      ],
    })

    const { DELETE, GET } = await import(
      '@/app/api/admin/observatory/budget-rules/[id]/route'
    )

    const deleteResponse = await DELETE(
      new Request('http://x/api/admin/observatory/budget-rules/br-existing-1', {
        method: 'DELETE',
      }),
      { params: Promise.resolve({ id: 'br-existing-1' }) },
    )
    expect(deleteResponse.status).toBe(204)
    // 204 has no body — read-as-text returns empty.
    const deleteText = await deleteResponse.text()
    expect(deleteText).toBe('')

    // The first SQL call must be a soft-delete UPDATE, not a hard DELETE.
    const firstSql = String(queryMock.mock.calls[0][0])
    expect(firstSql).toMatch(/UPDATE llm_budget_rules/i)
    expect(firstSql).toMatch(/active\s*=\s*FALSE/i)
    expect(firstSql).not.toMatch(/^\s*DELETE\s+FROM/i)

    const getResponse = await GET(
      new Request('http://x/api/admin/observatory/budget-rules/br-existing-1'),
      { params: Promise.resolve({ id: 'br-existing-1' }) },
    )
    expect(getResponse.status).toBe(200)
    const body = await getResponse.json()
    expect(body.budget_rule_id).toBe('br-existing-1')
    expect(body.active).toBe(false)
  })
})

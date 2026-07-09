/**
 * lel_event_record.test.ts — POST /api/mcp/writes/lel_event_record.
 *
 * Coverage:
 *   1. Requires write (all) authz — denied for a view-only / deny principal.
 *   2. Happy path returns an envelope and triggers exactly ONE recalibration enqueue.
 *   3. A second save within the quiet-window does NOT enqueue a second run
 *      (the enqueue helper reports { enqueued:false, reason:'debounced' }).
 *   4. force=true forwards through to the enqueue helper (bypass quiet-window).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── rate limiter: always allow ────────────────────────────────────────────────
vi.mock('@/lib/mcp/rate_limiter', () => ({
  checkRateLimit: vi.fn().mockResolvedValue({ allowed: true }),
  buildRateLimitErrorEnvelope: vi.fn(() => ({ error: 'rate_limit' })),
}))

// ── writer + enqueue helper ───────────────────────────────────────────────────
const mockRecordLelEvent = vi.fn()
vi.mock('@/lib/mcp/lel_event_writer', () => ({ recordLelEvent: mockRecordLelEvent }))

const mockEnqueue = vi.fn()
vi.mock('@/lib/build/recalibrationEnqueue', () => ({ enqueueLelRecalibration: mockEnqueue }))

// ── dynamic-import authz surfaces ─────────────────────────────────────────────
const mockAuthorize = vi.fn()
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: mockAuthorize }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('guest') }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function makeReq(body: object): Request {
  return new Request('http://localhost/api/mcp/writes/lel_event_record', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-mcp-internal-token': 'test-token',
      'x-mcp-user': 'owner-uid',
      'x-mcp-audience-tier': 'super_admin',
      'x-mcp-key-id': 'mcp_test_KEY001',
    },
    body: JSON.stringify(body),
  })
}

const PARAMS = { params: Promise.resolve({ action: 'lel_event_record' }) }

const VALID_EVENT = {
  event_class: 'career_entry',
  event_date: '2015-06-01',
  description: 'Joined first firm',
  domain: 'career',
}

beforeEach(() => {
  vi.clearAllMocks()
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
  mockRecordLelEvent.mockResolvedValue({ event_id: 'evt-1', recorded_at: '2026-07-08T00:00:00Z', created: true })
})

describe('POST /api/mcp/writes/lel_event_record — authz', () => {
  it('denies a view-only principal (perm !== all) with 401 and the DISTINCT entitlement_denied envelope (R5.1 C2 item 3 — Denial ≠ empty)', async () => {
    mockAuthorize.mockResolvedValue('view')
    const { POST } = await import('../[action]/route')
    const res = await POST(makeReq({ chart_id: CHART, event: VALID_EVENT }), PARAMS)
    expect(res.status).toBe(401)
    expect(mockRecordLelEvent).not.toHaveBeenCalled()
    expect(mockEnqueue).not.toHaveBeenCalled()

    const body = await res.json()
    expect(body.ok).toBe(false)
    // NEW additive error class — never the bare 'auth' this used to carry, so a caller can
    // programmatically distinguish "you are denied" from any other 401/auth failure.
    expect(body.error.class).toBe('entitlement_denied')
    expect(body.denial).toEqual({
      reason: 'entitlement',
      chart_id: CHART,
      permission_found: 'deny',
      permission_required: 'all',
      distinct_from_empty: true,
    })
  })

  it('denies a deny principal with 401 and the distinct denial block', async () => {
    mockAuthorize.mockResolvedValue('deny')
    const { POST } = await import('../[action]/route')
    const res = await POST(makeReq({ chart_id: CHART, event: VALID_EVENT }), PARAMS)
    expect(res.status).toBe(401)
    expect(mockRecordLelEvent).not.toHaveBeenCalled()

    const body = await res.json()
    expect(body.error.class).toBe('entitlement_denied')
    expect(body.denial.distinct_from_empty).toBe(true)
    expect(body.denial.chart_id).toBe(CHART)
  })
})

describe('POST /api/mcp/writes/lel_event_record — happy path + debounce', () => {
  it('saves and triggers exactly ONE recalibration enqueue', async () => {
    mockAuthorize.mockResolvedValue('all')
    mockEnqueue.mockResolvedValue({ enqueued: true, run_id: 'run-1', plan: ['ph_rectification'] })

    const { POST } = await import('../[action]/route')
    const res = await POST(makeReq({ chart_id: CHART, event: VALID_EVENT }), PARAMS)
    expect(res.status).toBe(200)
    const body = await res.json()

    expect(mockRecordLelEvent).toHaveBeenCalledOnce()
    expect(mockEnqueue).toHaveBeenCalledOnce()
    expect(mockEnqueue).toHaveBeenCalledWith(expect.objectContaining({ chartId: CHART, force: false }))
    expect(body.result.event_id).toBe('evt-1')
    expect(body.result.recalibration.enqueued).toBe(true)
  })

  it('a second save within the quiet-window does NOT enqueue a second run', async () => {
    mockAuthorize.mockResolvedValue('all')
    // The enqueue helper's own debounce reports coalesced.
    mockEnqueue.mockResolvedValue({ enqueued: false, reason: 'debounced', debounce_seconds: 600 })

    const { POST } = await import('../[action]/route')
    const res = await POST(makeReq({ chart_id: CHART, event: VALID_EVENT }), PARAMS)
    expect(res.status).toBe(200)
    const body = await res.json()

    // The save still succeeds; the enqueue is called once and coalesces.
    expect(mockRecordLelEvent).toHaveBeenCalledOnce()
    expect(mockEnqueue).toHaveBeenCalledOnce()
    expect(body.result.recalibration.enqueued).toBe(false)
    expect(body.result.recalibration.reason).toBe('debounced')
  })

  it('force=true forwards the bypass flag to the enqueue helper', async () => {
    mockAuthorize.mockResolvedValue('all')
    mockEnqueue.mockResolvedValue({ enqueued: true, run_id: 'run-forced', plan: ['ph_rectification'] })

    const { POST } = await import('../[action]/route')
    const res = await POST(makeReq({ chart_id: CHART, event: VALID_EVENT, force: true }), PARAMS)
    expect(res.status).toBe(200)
    expect(mockEnqueue).toHaveBeenCalledWith(expect.objectContaining({ chartId: CHART, force: true }))
  })

  it('rejects an unknown event class from the writer with 400 (no enqueue)', async () => {
    mockAuthorize.mockResolvedValue('all')
    mockRecordLelEvent.mockRejectedValue(new Error("Unknown event class 'bogus': not present in brahma_event_ontology."))

    const { POST } = await import('../[action]/route')
    const res = await POST(makeReq({ chart_id: CHART, event: { ...VALID_EVENT, event_class: 'bogus' } }), PARAMS)
    expect(res.status).toBe(400)
    expect(mockEnqueue).not.toHaveBeenCalled()
  })

  it('a save that fails to enqueue still returns success (best-effort side effect)', async () => {
    mockAuthorize.mockResolvedValue('all')
    mockEnqueue.mockRejectedValue(new Error('dispatch boom'))

    const { POST } = await import('../[action]/route')
    const res = await POST(makeReq({ chart_id: CHART, event: VALID_EVENT }), PARAMS)
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.result.event_id).toBe('evt-1')
    expect(body.result.recalibration.enqueued).toBe(false)
    expect(body.result.recalibration.reason).toBe('enqueue_error')
  })

  it('requires chart_id (400 when absent)', async () => {
    mockAuthorize.mockResolvedValue('all')
    const { POST } = await import('../[action]/route')
    const res = await POST(makeReq({ event: VALID_EVENT }), PARAMS)
    expect(res.status).toBe(400)
  })
})

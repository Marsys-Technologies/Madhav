/**
 * Watchdog endpoint unit tests.
 * Covers: auth gate, existing two reaper clauses (contract — counts only),
 * and the new third clause: planned-orphan reaper (D2 fix).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

// ─── module-level mocks (must precede route import) ──────────────────────────

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

// Disable PubSub in all watchdog tests — publishEvent short-circuits when
// PUBSUB_DISABLED is set; we assert on query calls, not Pub/Sub messages.
beforeEach(() => {
  vi.clearAllMocks()
  process.env.WATCHDOG_SECRET = 'test-secret'
  process.env.PUBSUB_DISABLED = '1'
  delete process.env.GOOGLE_CLOUD_PROJECT
})

function makeReq(secret: string | null = 'test-secret'): NextRequest {
  const headers: Record<string, string> = {}
  if (secret !== null) headers['x-watchdog-auth'] = secret
  return new NextRequest('http://localhost/api/cockpit/watchdog', {
    method: 'POST',
    headers,
  })
}

/** Default mock: nothing to reap (0 rows for all three UPDATE clauses). */
function noOrphans() {
  mockQuery
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 1. orphan running runs
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 2. stuck building assets
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 3. undispatched planned runs
}

// ─── A — auth gate ────────────────────────────────────────────────────────────

describe('POST /api/cockpit/watchdog — auth', () => {
  it('returns 401 with no auth header', async () => {
    const { POST } = await import('../route')
    const res = await POST(makeReq(null))
    expect(res.status).toBe(401)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('returns 401 with wrong secret', async () => {
    const { POST } = await import('../route')
    const res = await POST(makeReq('wrong-secret'))
    expect(res.status).toBe(401)
  })

  it('passes with correct secret', async () => {
    noOrphans()
    const { POST } = await import('../route')
    const res = await POST(makeReq('test-secret'))
    expect(res.status).toBe(200)
  })
})

// ─── B — normal happy path (nothing to reap) ─────────────────────────────────

describe('POST /api/cockpit/watchdog — nothing to reap', () => {
  it('returns 200 with all-zero counts', async () => {
    noOrphans()
    const { POST } = await import('../route')
    const res = await POST(makeReq())
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.orphan_runs_failed).toBe(0)
    expect(body.stuck_assets_failed).toBe(0)
    expect(body.undispatched_runs_failed).toBe(0)
  })
})

// ─── C — undispatched planned-run reaper (D2 fix) ────────────────────────────

describe('POST /api/cockpit/watchdog — planned-orphan reaper (D2)', () => {
  it('marks planned runs failed and aborts their queued assets', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })          // 1. running orphans
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })          // 2. stuck assets
      .mockResolvedValueOnce({                                    // 3. undispatched
        rows: [
          { id: 'run-aaa', chart_id: 'chart-111' },
          { id: 'run-bbb', chart_id: 'chart-222' },
        ],
        rowCount: 2,
      })
      .mockResolvedValueOnce({ rows: [], rowCount: 2 })          // 4. abort assets

    const { POST } = await import('../route')
    const res = await POST(makeReq())
    expect(res.status).toBe(200)

    const body = await res.json()
    expect(body.undispatched_runs_failed).toBe(2)

    // The 4th query must be the build_run_assets abort update
    const calls = mockQuery.mock.calls as [string, unknown[]][]
    const assetAbortCall = calls[3]
    expect(assetAbortCall[0]).toMatch(/UPDATE build_run_assets/)
    expect(assetAbortCall[0]).toMatch(/aborted/)
    // run IDs passed as array param
    expect(assetAbortCall[1]).toEqual([['run-aaa', 'run-bbb']])
  })

  it('does not call asset-abort update when no planned orphans found', async () => {
    noOrphans()
    const { POST } = await import('../route')
    await POST(makeReq())
    // Only 3 UPDATE calls; no 4th (asset abort)
    expect(mockQuery).toHaveBeenCalledTimes(3)
  })

  it('undispatched reaper SQL targets planned + started_at IS NULL + created_at threshold', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })

    const { POST } = await import('../route')
    await POST(makeReq())

    const calls = mockQuery.mock.calls as [string][]
    const thirdCall = calls[2][0]
    expect(thirdCall).toMatch(/state = 'planned'/)
    expect(thirdCall).toMatch(/started_at IS NULL/)
    expect(thirdCall).toMatch(/created_at/)
    expect(thirdCall).toMatch(/10 minutes/)
    expect(thirdCall).toMatch(/orphan-watchdog: run never dispatched/)
  })
})

// ─── D — existing reaper clauses not regressed ───────────────────────────────

describe('POST /api/cockpit/watchdog — existing clauses unchanged', () => {
  it('first reaper targets running state with 30-minute threshold', async () => {
    noOrphans()
    const { POST } = await import('../route')
    await POST(makeReq())

    const calls = mockQuery.mock.calls as [string][]
    const firstCall = calls[0][0]
    expect(firstCall).toMatch(/state = 'running'/)
    expect(firstCall).toMatch(/30 minutes/)
  })

  it('second reaper targets building state with 15-minute threshold', async () => {
    noOrphans()
    const { POST } = await import('../route')
    await POST(makeReq())

    const calls = mockQuery.mock.calls as [string][]
    const secondCall = calls[1][0]
    expect(secondCall).toMatch(/state = 'building'/)
    expect(secondCall).toMatch(/15 minutes/)
  })
})

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

/** Default mock: nothing to reap (0 rows for all clauses + M-4 pruning DELETEs). */
function noOrphans() {
  mockQuery
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 1. orphan running runs
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 2. stuck building assets
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 3. M-5: UPDATE build_run_assets SET error
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 4. undispatched planned runs
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 5. M-4: DELETE build_run_assets (retention)
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 6. M-4: DELETE build_runs (retention)
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
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })          // 3. M-5 UPDATE build_run_assets SET error
      .mockResolvedValueOnce({                                    // 4. undispatched planned
        rows: [
          { id: 'run-aaa', chart_id: 'chart-111' },
          { id: 'run-bbb', chart_id: 'chart-222' },
        ],
        rowCount: 2,
      })
      .mockResolvedValueOnce({ rows: [], rowCount: 2 })          // 5. abort queued assets
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })          // 6. M-4 DELETE build_run_assets
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })          // 7. M-4 DELETE build_runs

    const { POST } = await import('../route')
    const res = await POST(makeReq())
    expect(res.status).toBe(200)

    const body = await res.json()
    expect(body.undispatched_runs_failed).toBe(2)

    // The 5th query (index 4) must be the build_run_assets abort update
    const calls = mockQuery.mock.calls as [string, unknown[]][]
    const assetAbortCall = calls[4]
    expect(assetAbortCall[0]).toMatch(/UPDATE build_run_assets/)
    expect(assetAbortCall[0]).toMatch(/aborted/)
    // run IDs passed as array param
    expect(assetAbortCall[1]).toEqual([['run-aaa', 'run-bbb']])
  })

  it('does not call asset-abort update when no planned orphans found', async () => {
    noOrphans()
    const { POST } = await import('../route')
    await POST(makeReq())
    // 6 queries total: 3 reapers + M-5 UPDATE + 2 M-4 DELETEs; no asset-abort (7th) call
    expect(mockQuery).toHaveBeenCalledTimes(6)
    const calls = mockQuery.mock.calls as [string][]
    // None of the 6 calls should be the asset-abort UPDATE (which targets aborted state)
    expect(calls.every(c => !(/aborted/.test(c[0])))).toBe(true)
  })

  it('undispatched reaper SQL targets planned + started_at IS NULL + created_at threshold', async () => {
    noOrphans()
    const { POST } = await import('../route')
    await POST(makeReq())

    // M-5 UPDATE moved to slot 3 (index 2); undispatched is now slot 4 (index 3)
    const calls = mockQuery.mock.calls as [string][]
    const undispatchedCall = calls[3][0]
    expect(undispatchedCall).toMatch(/state = 'planned'/)
    expect(undispatchedCall).toMatch(/started_at IS NULL/)
    expect(undispatchedCall).toMatch(/created_at/)
    expect(undispatchedCall).toMatch(/10 minutes/)
    expect(undispatchedCall).toMatch(/orphan-watchdog: run never dispatched/)
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

// ─── E — clause 1 false-kill fix (infra-watchdog-fix, 2026-08-01) ────────────
//
// INCIDENT: clause 1 checked asset_throughput.last_built_at ALONE with a 10-min
// window, and killed a run (e5cde4dc, chart 1c826d5a, ka_gochara_sweep) whose
// container was alive and progressing — build_substep_progress showed a fresh
// commit the reaper never consulted. Fix: widen the window to 15 min AND treat
// a recent build_substep_progress row for the chart as independent evidence of
// life. See orphanRunReaperPolicy.test.ts for the decision-boundary proof (RED
// pre-fix / GREEN post-fix over both directions); these tests confirm route.ts
// actually emits the fixed SQL and wires its result through.

describe('POST /api/cockpit/watchdog — clause 1 false-kill fix', () => {
  it('orphan-run reaper SQL uses a 15-minute asset_throughput window (widened from 10)', async () => {
    noOrphans()
    const { POST } = await import('../route')
    await POST(makeReq())

    const calls = mockQuery.mock.calls as [string][]
    const firstCall = calls[0][0]
    expect(firstCall).toMatch(/last_built_at > NOW\(\) - INTERVAL '15 minutes'/)
    expect(firstCall).not.toMatch(/10 minutes/)
  })

  it('orphan-run reaper SQL also checks build_substep_progress.completed_at within 15 minutes', async () => {
    noOrphans()
    const { POST } = await import('../route')
    await POST(makeReq())

    const calls = mockQuery.mock.calls as [string][]
    const firstCall = calls[0][0]
    expect(firstCall).toMatch(/build_substep_progress/)
    expect(firstCall).toMatch(/completed_at > NOW\(\) - INTERVAL '15 minutes'/)
    // build_substep_progress is read-only from this route — never DELETE/INSERT/UPDATE
    // targeting that table directly (a plain SELECT/NOT EXISTS reference is fine).
    expect(firstCall).not.toMatch(/(UPDATE|DELETE\s+FROM|INSERT\s+INTO)\s+build_substep_progress/i)
  })

  it('still marks a genuinely orphaned run failed and reports the count', async () => {
    mockQuery
      .mockResolvedValueOnce({                                    // 1. orphan running runs
        rows: [{ id: 'run-dead', chart_id: 'chart-dead' }],
        rowCount: 1,
      })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })            // 2. stuck assets
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })            // 3. M-5 UPDATE build_run_assets
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })            // 4. undispatched planned
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })            // 5. M-4 DELETE build_run_assets
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })            // 6. M-4 DELETE build_runs

    const { POST } = await import('../route')
    const res = await POST(makeReq())
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.orphan_runs_failed).toBe(1)
  })
})

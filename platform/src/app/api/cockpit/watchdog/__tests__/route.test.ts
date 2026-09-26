/**
 * Watchdog endpoint unit tests.
 * Covers: auth gate, existing two reaper clauses (contract — counts only),
 * and the new third clause: planned-orphan reaper (D2 fix).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'
// NOTE: deliberately not a static top-level import — this file's mock-hoisting
// trick (vi.mock factories referencing mockQuery/mockVerifyOidcToken, declared
// via plain `const` below rather than `vi.hoisted`) relies on route.ts only
// ever being imported dynamically, inside each test body, AFTER those consts
// have run. A static import here would force route.ts to load before they
// exist. Grab the named export from the same dynamic `await import('../route')`
// each test already performs instead.

// ─── module-level mocks (must precede route import) ──────────────────────────

const mockQuery = vi.fn()
const mockVerifyOidcToken = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/auth/oidc', () => ({ verifyOidcToken: mockVerifyOidcToken }))

// Disable PubSub in all watchdog tests — publishEvent short-circuits when
// PUBSUB_DISABLED is set; we assert on query calls, not Pub/Sub messages.
beforeEach(() => {
  vi.clearAllMocks()
  mockVerifyOidcToken.mockResolvedValue({
    email: 'amjis-scheduler@madhav-astrology.iam.gserviceaccount.com',
    sub: 'scheduler-subject',
  })
  process.env.PUBSUB_DISABLED = '1'
  delete process.env.GOOGLE_CLOUD_PROJECT
  delete process.env.WATCHDOG_LEGACY_FALLBACK_ENABLED
  delete process.env.WATCHDOG_SECRET
})

function makeReq(token: string | null = 'valid-google-id-token'): NextRequest {
  const headers: Record<string, string> = {}
  if (token !== null) headers.Authorization = `Bearer ${token}`
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
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 3. undispatched planned runs
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 4. M-4: DELETE build_run_assets (retention)
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 5. M-4: DELETE build_runs (retention)
}

// ─── A — auth gate ────────────────────────────────────────────────────────────

describe('POST /api/cockpit/watchdog — auth', () => {
  it('returns 401 with no auth header', async () => {
    const { POST } = await import('../route')
    const res = await POST(makeReq(null))
    expect(res.status).toBe(401)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('returns 403 for a token from the wrong identity', async () => {
    mockVerifyOidcToken.mockResolvedValue(null)
    const { POST } = await import('../route')
    const res = await POST(makeReq('wrong-identity'))
    expect(res.status).toBe(403)
  })

  it('passes with the pinned Scheduler identity', async () => {
    noOrphans()
    const { POST } = await import('../route')
    const res = await POST(makeReq())
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
  // Packet A2 ("Always record why it failed"): this reaper's build_runs UPDATE
  // and its build_run_assets abort UPDATE used to be two separate query() calls
  // (the second with no `error` clause at all — the packet's dominant defect,
  // 295/301 empty-error records). They are now ONE combined CTE statement, so
  // there is no longer a separate "5th query is the abort update" call to find —
  // asserting on the single combined call's SQL + params instead.
  //
  // Correction pass (A2_review_20260926T123936Z.md §C1): M-5 was deleted
  // outright (a run-age-only staleness proxy that stamped healthy in-flight
  // assets), so it no longer occupies a mock slot here.
  it('marks planned runs failed and aborts their queued assets', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })          // 1. running orphans
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })          // 2. stuck assets
      .mockResolvedValueOnce({                                    // 3. undispatched planned (combined CTE)
        rows: [
          { id: 'run-aaa', chart_id: 'chart-111' },
          { id: 'run-bbb', chart_id: 'chart-222' },
        ],
        rowCount: 2,
      })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })          // 4. M-4 DELETE build_run_assets
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })          // 5. M-4 DELETE build_runs

    const { POST, UNDISPATCHED_RUN_MESSAGE } = await import('../route')
    const res = await POST(makeReq())
    expect(res.status).toBe(200)

    const body = await res.json()
    expect(body.undispatched_runs_failed).toBe(2)

    // The 3rd query (index 2) is the combined statement: it fails build_runs AND
    // aborts build_run_assets in one round trip, propagating the SAME message
    // (bound once as $1) to both tables' error columns.
    const calls = mockQuery.mock.calls as [string, unknown[]][]
    const undispatchedCall = calls[2]
    expect(undispatchedCall[0]).toMatch(/UPDATE build_runs/)
    expect(undispatchedCall[0]).toMatch(/UPDATE build_run_assets/)
    expect(undispatchedCall[0]).toMatch(/state = 'aborted'/)
    expect(undispatchedCall[0]).toMatch(/last_error = \$1/)
    expect(undispatchedCall[0]).toMatch(/error = \$1/)
    // the message is bound once and referenced from both UPDATEs (no run-id array
    // param anymore — the WHERE clause selects the matching runs itself).
    expect(undispatchedCall[1]).toEqual([UNDISPATCHED_RUN_MESSAGE])
  })

  it('the undispatched-reaper statement is unconditional but affects zero rows when nothing matches', async () => {
    noOrphans()
    const { POST } = await import('../route')
    const res = await POST(makeReq())
    // 5 queries total: 3 reapers (M-5 deleted, see A2_review_20260926T123936Z.md
    // §C1) + 2 M-4 DELETEs. The combined statement always runs (it is a single
    // WHERE-scoped UPDATE, not a conditional second call), but with nothing to
    // match it reports 0 — the honest "ran, found nothing" case, not "never asked".
    expect(mockQuery).toHaveBeenCalledTimes(5)
    const body = await res.json()
    expect(body.undispatched_runs_failed).toBe(0)
  })

  it('undispatched reaper SQL targets planned + started_at IS NULL + created_at threshold, and binds the attributable message', async () => {
    noOrphans()
    const { POST, UNDISPATCHED_RUN_MESSAGE } = await import('../route')
    await POST(makeReq())

    // M-5 deleted (A2_review_20260926T123936Z.md §C1); undispatched is slot 3 (index 2)
    const calls = mockQuery.mock.calls as [string, unknown[]][]
    const [undispatchedSql, undispatchedParams] = calls[2]
    expect(undispatchedSql).toMatch(/state = 'planned'/)
    expect(undispatchedSql).toMatch(/started_at IS NULL/)
    expect(undispatchedSql).toMatch(/created_at/)
    expect(undispatchedSql).toMatch(/10 minutes/)
    // Packet A2: the message is now a bound parameter, not an inline SQL
    // literal (so the SAME value reaches build_run_assets.error too) — assert
    // on the param, not on SQL text containing the string.
    expect(undispatchedParams).toEqual([UNDISPATCHED_RUN_MESSAGE])
    expect(UNDISPATCHED_RUN_MESSAGE).toBe('orphan-watchdog: run never dispatched')
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
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })            // 3. undispatched planned
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })            // 4. M-4 DELETE build_run_assets
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })            // 5. M-4 DELETE build_runs

    const { POST } = await import('../route')
    const res = await POST(makeReq())
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.orphan_runs_failed).toBe(1)
  })
})

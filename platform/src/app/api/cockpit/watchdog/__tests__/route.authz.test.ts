/**
 * P2-B-008 — `POST /api/cockpit/watchdog`: the sweep's one DISPROVEN claim.
 *
 * The B-008 brief listed watchdog alongside stats/registry/atlas as "calls
 * `getServerUser()` zero times — fully unauthenticated". The first half is
 * literally true and the conclusion does not follow. This route is a machine-to-
 * machine endpoint invoked by Cloud Scheduler every 5 minutes; it has no user
 * session by design. It authenticates with a shared secret instead:
 *
 *     if (!process.env.WATCHDOG_SECRET) return 401     // fails CLOSED
 *     if (req.headers.get('x-watchdog-auth') !== process.env.WATCHDOG_SECRET) return 401
 *
 * Adding `getServerUser()` here would not harden anything — it would break the
 * scheduler and disable the stuck-build reaper. So this route is deliberately
 * left UNCHANGED by this PR.
 *
 * Per §N.8 (Earned-Signal Principle), "we looked and it seemed fine" is not a
 * result. The correct question is: what code path would have to run, and fail,
 * for this route's auth signal to correctly read false? These tests are that
 * detector — they assert the gate genuinely rejects (a) a missing secret and
 * (b) a wrong secret, and genuinely admits the correct one. Without them the
 * "already authenticated" disposition would be exactly the unearned green signal
 * §N.8 forbids.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { POST } from '../route'

const SECRET = 'test-watchdog-secret'
const originalSecret = process.env.WATCHDOG_SECRET

function makeReq(authHeader?: string): NextRequest {
  return new NextRequest('http://localhost/api/cockpit/watchdog', {
    method: 'POST',
    headers: authHeader === undefined ? {} : { 'x-watchdog-auth': authHeader },
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  // Every reaper query returns "nothing to reap" so an authorized call completes.
  mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })
  process.env.PUBSUB_DISABLED = '1'
})

afterEach(() => {
  if (originalSecret === undefined) delete process.env.WATCHDOG_SECRET
  else process.env.WATCHDOG_SECRET = originalSecret
})

describe('POST /api/cockpit/watchdog — shared-secret gate is real (B-008 claim disproven)', () => {
  it('fails CLOSED when WATCHDOG_SECRET is unset — and touches no build state', async () => {
    delete process.env.WATCHDOG_SECRET
    const res = await POST(makeReq(SECRET))
    expect(res.status).toBe(401)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('REJECTS a request with no auth header', async () => {
    process.env.WATCHDOG_SECRET = SECRET
    const res = await POST(makeReq())
    expect(res.status).toBe(401)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('REJECTS a request bearing the wrong secret', async () => {
    process.env.WATCHDOG_SECRET = SECRET
    const res = await POST(makeReq('not-the-secret'))
    expect(res.status).toBe(401)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('ADMITS the correct secret — proving the gate can read true as well as false', async () => {
    process.env.WATCHDOG_SECRET = SECRET
    const res = await POST(makeReq(SECRET))
    expect(res.status).toBe(200)
    expect(mockQuery).toHaveBeenCalled()
  })
})

/**
 * End to end through the real session lookup: a disabled or pending user whose
 * `__session` cookie still verifies is refused by routes that authenticate with
 * `getServerUser()` (SS N-413, S10). An active user, and a user with no profile row,
 * are unaffected.
 *
 * Routes: POST /api/clients/create (getServerUser directly), GET /api/charts/[id]
 * (getServerUser + authorizeChartAccess) and GET /api/cockpit/runs/active
 * (getServerUser + requireChartPermission). firebase-admin, the cookie jar and the
 * DB are faked; nothing else is.
 */
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'

vi.mock('server-only', () => ({}))
vi.mock('next/headers', () => ({
  cookies: async () => ({ get: (name: string) => (name === '__session' ? { value: 'cookie-value' } : undefined) }),
}))
vi.mock('@/lib/db/client', () => ({ query: vi.fn(), getPool: vi.fn() }))

import { query } from '@/lib/db/client'
import { installFakeFirebaseAdmin, verifySessionCookieMock } from './fakeFirebaseAdmin'

const mockQuery = vi.mocked(query)
let restore: () => void
beforeAll(() => {
  restore = installFakeFirebaseAdmin()
})
afterAll(() => restore())

const UID = 'user-1'
const CHART = 'chart-1'

/** SQL router standing in for the DB. `profile: null` = no profiles row. */
function setDb(profile: { status: string; role: string } | null) {
  mockQuery.mockImplementation((async (sql: string) => {
    const s = String(sql)
    if (/SELECT status FROM profiles/.test(s)) {
      return { rows: profile ? [{ status: profile.status }] : [] }
    }
    if (/FROM profiles/.test(s)) {
      return { rows: profile ? [{ role: profile.role, status: profile.status }] : [] }
    }
    if (/FROM charts WHERE id/.test(s)) {
      return {
        rows: [{ owner_id: UID, subject_name: 'Test Subject', birth_date: '2000-01-01', birth_time: '10:00:00', birth_place: 'Testville' }],
      }
    }
    return { rows: [] }
  }) as never)
}

beforeEach(() => {
  vi.clearAllMocks()
  verifySessionCookieMock.mockResolvedValue({ uid: UID })
})

async function callCreate() {
  const { POST } = await import('@/app/api/clients/create/route')
  // An empty JSON object passes auth and then fails field validation (422), which
  // is how "authenticated" is told apart from the 401.
  return POST(new Request('http://localhost/api/clients/create', { method: 'POST', body: '{}' }))
}
async function callChartGet() {
  const { GET } = await import('@/app/api/charts/[id]/route')
  return GET(new NextRequest(`http://localhost/api/charts/${CHART}`), { params: Promise.resolve({ id: CHART }) })
}
async function callRunsActive() {
  const { GET } = await import('@/app/api/cockpit/runs/active/route')
  return GET(new NextRequest(`http://localhost/api/cockpit/runs/active?chart_id=${CHART}`))
}

describe.each([
  ['disabled', 'disabled'],
  ['pending', 'pending'],
])('a %s user holding a valid session cookie', (_label, status) => {
  beforeEach(() => setDb({ status, role: 'guest' }))

  it('POST /api/clients/create -> 401', async () => {
    const res = await callCreate()
    expect(res.status).toBe(401)
    expect(await res.json()).toEqual({ error: 'unauthenticated' })
  })

  it('GET /api/charts/[id] (authorizeChartAccess route) -> 401, chart never read', async () => {
    const res = await callChartGet()
    expect(res.status).toBe(401)
    expect(mockQuery.mock.calls.some(([sql]) => /FROM charts/.test(String(sql)))).toBe(false)
  })

  it('GET /api/cockpit/runs/active (requireChartPermission route) -> refused, chart never read', async () => {
    const res = await callRunsActive()
    expect(res.status).toBe(403)
    expect(mockQuery.mock.calls.some(([sql]) => /FROM charts/.test(String(sql)))).toBe(false)
  })
})

describe('an active user', () => {
  beforeEach(() => setDb({ status: 'active', role: 'guest' }))

  it('passes auth on POST /api/clients/create (reaches field validation)', async () => {
    const res = await callCreate()
    expect(res.status).not.toBe(401)
  })

  it('reads their own chart on GET /api/charts/[id]', async () => {
    const res = await callChartGet()
    expect(res.status).toBe(200)
    expect((await res.json()).subject_name).toBe('Test Subject')
  })

  it('passes requireChartPermission on GET /api/cockpit/runs/active', async () => {
    const res = await callRunsActive()
    expect(res.status).toBe(200)
  })
})

describe('a user with NO profile row', () => {
  beforeEach(() => setDb(null))

  it('behaves exactly as before: authenticated by the cookie (POST /api/clients/create passes auth)', async () => {
    const res = await callCreate()
    expect(res.status).not.toBe(401)
  })
})

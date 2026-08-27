/**
 * Regression test for P2 blocker B-001 (historical finding E-012):
 * GET /api/charts/[id] checked only `getServerUser() !== null` — any
 * authenticated user could read ANY other user's `subject_name` /
 * `birth_date` / `birth_time` / `birth_place` for ANY chart id, including
 * sensitive birth data, because the handler never checked chart ownership
 * or a `chart_grants` row.
 *
 * The sibling DELETE handler in the same file already gets this right
 * (queries `owner_id`/`client_id`, enforces `role === 'super_admin' ||
 * isOwner`). This test exercises the real `authorizeChartAccess` brain
 * (only `@/lib/db/client` and `@/lib/firebase/server` are mocked) to prove
 * GET is routed through the same authorization gate.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { GET } from '../[id]/route'

const CHART_ID = 'chart-belongs-to-victim'

const CHART_ROW = {
  subject_name: 'Victim Name',
  birth_date: '1990-01-01',
  birth_time: '10:00:00',
  birth_place: 'Somewhere',
}

function makeReq(): NextRequest {
  return new NextRequest(`http://localhost/api/charts/${CHART_ID}`, { method: 'GET' })
}

function makeParams(): { params: Promise<{ id: string }> } {
  return { params: Promise.resolve({ id: CHART_ID }) }
}

/**
 * Wires mockQuery to answer every SQL shape the route + authorizeChartAccess
 * issue:
 *   - SELECT role FROM profiles          -> caller's role
 *   - SELECT owner_id FROM charts        -> chart ownership row
 *   - SELECT permission FROM chart_grants -> grant row (or none)
 *   - SELECT subject_name, ... FROM charts -> the sensitive chart row
 */
function setupMocks(opts: {
  uid: string
  role?: 'guest' | 'super_admin'
  ownerId?: string | null
  grantPermission?: string | null
  chartExists?: boolean
}) {
  const {
    uid,
    role = 'guest',
    ownerId = null,
    grantPermission = null,
    chartExists = true,
  } = opts

  mockGetServerUser.mockResolvedValue({ uid })

  mockQuery.mockImplementation((sql: string, _params: unknown[]) => {
    if (/FROM profiles/.test(sql)) {
      return Promise.resolve({ rows: [{ role }] })
    }
    if (/subject_name/.test(sql)) {
      // The sensitive-data SELECT the (fixed) route issues after authz passes.
      return Promise.resolve({ rows: chartExists ? [CHART_ROW] : [] })
    }
    if (/owner_id[\s\S]*FROM charts/.test(sql) || /FROM charts WHERE id/.test(sql)) {
      return Promise.resolve({
        rows: chartExists ? [{ owner_id: ownerId, client_id: null }] : [],
      })
    }
    if (/FROM chart_grants/.test(sql)) {
      return Promise.resolve({
        rows: grantPermission ? [{ permission: grantPermission }] : [],
      })
    }
    return Promise.resolve({ rows: [] })
  })
}

beforeEach(() => {
  mockQuery.mockReset()
  mockGetServerUser.mockReset()
})

describe('GET /api/charts/[id] — P2-B-001 / E-012 cross-user PII authz', () => {
  it('denies an authenticated user with NO grant/ownership on the chart (must NOT be 200)', async () => {
    setupMocks({ uid: 'attacker-uid', role: 'guest', ownerId: 'victim-uid' })
    const res = await GET(makeReq(), makeParams())
    expect(res.status).not.toBe(200)
    expect([401, 403]).toContain(res.status)
    const body = (await res.json()) as { subject_name?: string }
    expect(body.subject_name).toBeUndefined()
  })

  it('allows the owning user through with 200 and the expected fields', async () => {
    setupMocks({ uid: 'victim-uid', role: 'guest', ownerId: 'victim-uid' })
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(200)
    const body = (await res.json()) as typeof CHART_ROW
    expect(body.subject_name).toBe(CHART_ROW.subject_name)
    expect(body.birth_date).toBe(CHART_ROW.birth_date)
    expect(body.birth_time).toBe(CHART_ROW.birth_time)
    expect(body.birth_place).toBe(CHART_ROW.birth_place)
  })

  it('allows a user with a chart_grants view grant through with 200', async () => {
    setupMocks({
      uid: 'granted-uid',
      role: 'guest',
      ownerId: 'victim-uid',
      grantPermission: 'view',
    })
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(200)
  })

  it('allows super_admin through even without ownership/grant', async () => {
    setupMocks({ uid: 'admin-uid', role: 'super_admin', ownerId: 'victim-uid' })
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(200)
  })

  it('returns 401 for an unauthenticated caller', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(401)
  })
})

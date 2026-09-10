/**
 * Regression test for Paripraśna S1-F-001 (v3 assurance campaign, stream S1 —
 * Navigation, Shell & History): missing chart-level entitlement check on the
 * conversations CRUD surface.
 *
 * Before the fix, `POST /api/conversations` and `GET /api/conversations`
 * accepted a caller-supplied `chartId` with NO verification that the
 * authenticated user holds any `chart_grants` row (or ownership) for that
 * chart — the same missing-ownership-check family as B-001/B-007/B-008.
 * Proven LIVE against the deployed service 2026-08-27: a principal holding
 * exactly one `view` grant (on a synthetic chart) successfully created and
 * listed a conversation scoped to a real, unrelated chart it had zero grant
 * on (HTTP 201, then reflected via GET).
 *
 * This does NOT expose chart facts/reading content — the actual `/api/pariprashna`
 * ask pipeline independently re-checks `authorizeChartAccess` on every turn and
 * was also verified LIVE to deny (`FORBIDDEN`) even when handed the orphan
 * conversation. The gap is object-level authorization at the
 * conversation-creation/listing boundary itself: an unauthorized `chart_id`
 * association should never be creatable or listable at all.
 *
 * The fix routes both handlers through the same `authorizeChartAccess` brain
 * already used by `GET /api/charts/[id]`, `/api/chat/consult`, and the
 * `cockpit/*`/`mcp/*` surface, requiring `permission !== 'deny'` (a `view`
 * grant is sufficient — creating/listing a conversation is a read-adjacent,
 * non-destructive action, unlike the cockpit `clear` routes which require `all`).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { GET, POST } from '../route'

const OWNED_CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const UNGRANTED_CHART = 'cb73cd3d-9eba-4220-9902-0de91566e980'
const CALLER_UID = 'hunQRYVJ5Ec2mQnJnutK7AoQnsO2'

function makeGetReq(chartId: string): Request {
  return new Request(`http://localhost/api/conversations?chartId=${chartId}`, { method: 'GET' })
}

function makePostReq(chartId: string): Request {
  return new Request('http://localhost/api/conversations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chartId, module: 'consume' }),
  })
}

/** SQL-shape-dispatching mock, mirroring the cockpit/clear authz test pattern. */
function setupMocks(opts: { role?: string; ownerId?: string | null; grantPermission?: string | null }) {
  const { role = 'guest', ownerId = null, grantPermission = null } = opts
  mockGetServerUser.mockResolvedValue({ uid: CALLER_UID })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }], rowCount: 1 })
    if (/owner_id[\s\S]*FROM charts/.test(sql)) {
      return Promise.resolve({ rows: ownerId !== undefined ? [{ owner_id: ownerId }] : [], rowCount: ownerId !== undefined ? 1 : 0 })
    }
    if (/FROM chart_grants/.test(sql)) {
      return Promise.resolve({ rows: grantPermission ? [{ permission: grantPermission }] : [], rowCount: grantPermission ? 1 : 0 })
    }
    if (/INSERT INTO conversations/.test(sql)) {
      return Promise.resolve({ rows: [{ id: 'new-conv-id', chart_id: OWNED_CHART, user_id: CALLER_UID, module: 'consume', title: null, created_at: '2026-08-28T00:00:00Z' }], rowCount: 1 })
    }
    if (/FROM conversations/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

beforeEach(() => {
  mockQuery.mockReset()
  mockGetServerUser.mockReset()
})

describe('S1-F-001: /api/conversations chart-entitlement gate', () => {
  it('POST denies a chartId the caller has no grant on and is not the owner of (permission=deny)', async () => {
    setupMocks({ ownerId: 'someone-else', grantPermission: null })
    const res = await POST(makePostReq(UNGRANTED_CHART))
    expect(res.status).toBe(403)
  })

  it('POST allows a chartId the caller holds a view grant on', async () => {
    setupMocks({ ownerId: null, grantPermission: 'view' })
    const res = await POST(makePostReq(OWNED_CHART))
    expect(res.status).toBe(201)
  })

  it('POST allows a chartId the caller owns outright', async () => {
    setupMocks({ ownerId: CALLER_UID, grantPermission: null })
    const res = await POST(makePostReq(OWNED_CHART))
    expect(res.status).toBe(201)
  })

  it('GET denies listing a chartId the caller has no grant on', async () => {
    setupMocks({ ownerId: 'someone-else', grantPermission: null })
    const res = await GET(makeGetReq(UNGRANTED_CHART))
    expect(res.status).toBe(403)
  })

  it('GET allows listing a chartId the caller holds a view grant on', async () => {
    setupMocks({ ownerId: null, grantPermission: 'view' })
    const res = await GET(makeGetReq(OWNED_CHART))
    expect(res.status).toBe(200)
  })
})

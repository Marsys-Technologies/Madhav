/**
 * Regression test for V3-E-011 (Paripraśna Assurance systemic authorization
 * sweep, Session S5): cross-chart read disclosure on GET
 * /api/cockpit/runs/active.
 *
 * Same root-cause family as B-001/B-007/B-008: the handler checked only
 * `getServerUser() !== null` and then trusted the caller-supplied `chart_id`
 * with no ownership/grant check. A comment in the pre-fix route documented
 * that a super_admin gate had been REMOVED and nothing substituted — leaving
 * any authenticated user able to read an arbitrary chart's active
 * `build_runs` row (scope, scope_target, action, state, plan array,
 * current_asset_id, timestamps) plus every `build_run_assets` row (state,
 * error) for that run.
 *
 * Fix: gate the route through the same `requireChartPermission` helper used
 * by the already-merged sibling GET /api/cockpit/runs, at 'read' access
 * (owner, super_admin, or a chart_grants 'view' grantee) — this is a
 * read-only endpoint, matching that precedent's reasoning.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { GET } from '../route'

const VICTIM_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const VICTIM_UID = 'victim-uid'
const ATTACKER_UID = 'attacker-uid'
const ADMIN_UID = 'admin-uid'

const ACTIVE_RUN_ROW = {
  id: 'run-active-1',
  scope: 'layer',
  scope_target: 'kala',
  action: 'build',
  state: 'running',
  plan: ['ka_kshetra', 'ka_avadhi'],
  current_asset_id: 'ka_avadhi',
  created_at: '2026-08-01T00:00:00Z',
  started_at: '2026-08-01T00:00:01Z',
  pause_requested_at: null,
  stop_requested_at: null,
}

const ASSET_ROWS = [
  { asset_id: 'ka_kshetra', position: 0, state: 'completed', started_at: '2026-08-01T00:00:01Z', ended_at: '2026-08-01T00:00:30Z', error: null },
  { asset_id: 'ka_avadhi', position: 1, state: 'building', started_at: '2026-08-01T00:00:31Z', ended_at: null, error: null },
]

function makeReq(chartId: string): NextRequest {
  return new NextRequest(`http://localhost/api/cockpit/runs/active?chart_id=${chartId}`)
}

/** SQL-shape-dispatching mock, mirroring the runs/route.authz.test.ts precedent. */
function setupMocks(opts: { uid: string; role?: string; ownerId?: string | null; grantPermission?: string | null }) {
  const { uid, role = 'guest', ownerId = VICTIM_UID, grantPermission = null } = opts
  mockGetServerUser.mockResolvedValue({ uid })

  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }], rowCount: 1 })
    if (/FROM chart_grants/.test(sql)) {
      return Promise.resolve({
        rows: grantPermission ? [{ permission: grantPermission }] : [],
        rowCount: grantPermission ? 1 : 0,
      })
    }
    if (/owner_id[\s\S]*FROM charts/.test(sql)) {
      return Promise.resolve({
        rows: ownerId !== null ? [{ owner_id: ownerId }] : [],
        rowCount: ownerId !== null ? 1 : 0,
      })
    }
    if (/FROM build_run_assets/.test(sql)) return Promise.resolve({ rows: ASSET_ROWS, rowCount: ASSET_ROWS.length })
    if (/FROM build_runs/.test(sql)) return Promise.resolve({ rows: [ACTIVE_RUN_ROW], rowCount: 1 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('GET /api/cockpit/runs/active — V3-E-011 cross-chart active-run disclosure', () => {
  it('DENIES a non-owner guest reading another chart\'s active run', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    const body = await res.json()
    expect(body.data).toBeUndefined()
    expect(body.code).toBe('FORBIDDEN_CHART')
    // The real proof: build_runs / build_run_assets were never even queried.
    expect(mockQuery).not.toHaveBeenCalledWith(expect.stringMatching(/FROM build_runs/), expect.anything())
    expect(mockQuery).not.toHaveBeenCalledWith(expect.stringMatching(/FROM build_run_assets/), expect.anything())
  })

  it('DENIES a caller when the chart does not exist at all', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: null })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
  })

  it('DENIES an unauthenticated caller', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
  })

  it('ALLOWS the legitimate owner to read their own active run', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.data.run.id).toBe('run-active-1')
    expect(body.data.assets).toHaveLength(2)
  })

  it('ALLOWS a chart_grants view-grantee to read the active run — a read grant covers a read', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
  })

  it('ALLOWS super_admin to read the active run on a chart they do not own', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
  })
})

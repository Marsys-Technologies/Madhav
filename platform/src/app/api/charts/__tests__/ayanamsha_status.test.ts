/** Existing admission guards plus the retired endpoint contract; synthetic identities only. */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { GET, dynamic } from '../[id]/ayanamsha-status/route'

const CHART_ID = 'cccccccc-0000-0000-0000-000000000001'
const USER_ID = 'synthetic-owner'
const ROLE_SQL = 'SELECT role FROM profiles WHERE id=$1'
const OWNER_SQL = 'SELECT chart_id FROM charts WHERE chart_id=$1 AND owner_id=$2'
const ADMIN_SQL = 'SELECT chart_id FROM charts WHERE chart_id=$1'

function request() {
  return new Request(`http://fixture.invalid/api/charts/${CHART_ID}/ayanamsha-status`)
}
function params(id = CHART_ID) {
  return { params: Promise.resolve({ id }) }
}
function admit(role: string | null = 'guest', chartFound = true) {
  mockGetServerUser.mockResolvedValue({ uid: USER_ID })
  mockQuery
    .mockResolvedValue({ rows: [] })
    .mockResolvedValueOnce({ rows: role === null ? [] : [{ role }] })
    .mockResolvedValueOnce({ rows: chartFound ? [{ chart_id: CHART_ID }] : [] })
}
function expectAdmissionQueries(superAdmin = false, chartId = CHART_ID, uid = USER_ID) {
  expect(mockQuery.mock.calls).toEqual([
    [ROLE_SQL, [uid]],
    [superAdmin ? ADMIN_SQL : OWNER_SQL, superAdmin ? [chartId] : [chartId, uid]],
  ])
  expect(mockGetServerUser).toHaveBeenCalledTimes(1)
  expect(mockGetServerUser.mock.invocationCallOrder[0]).toBeLessThan(mockQuery.mock.invocationCallOrder[0])
}

beforeEach(() => {
  vi.resetAllMocks()
  vi.stubGlobal('fetch', vi.fn(() => { throw new Error('No HTTP/model/build requests permitted') }))
})
afterEach(() => {
  expect(fetch).not.toHaveBeenCalled()
  vi.unstubAllGlobals()
})

describe('ayanamsha-status retained admission guards', () => {
  it.each(['', '   '])('returns 400 for blank chart id %j before auth or SQL', async (id) => {
    const result = await GET(request(), params(id))
    expect(result.status).toBe(400)
    expect(await result.json()).toEqual({ error: 'missing_chart_id' })
    expect(mockGetServerUser).not.toHaveBeenCalled()
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('returns 400 for a missing chart id before auth or SQL', async () => {
    const result = await GET(request(), { params: Promise.resolve({} as { id: string }) })
    expect(result.status).toBe(400)
    expect(await result.json()).toEqual({ error: 'missing_chart_id' })
    expect(mockGetServerUser).not.toHaveBeenCalled()
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('returns 401 without session before any SQL', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const result = await GET(request(), params())
    expect(result.status).toBe(401)
    expect(await result.json()).toEqual({ error: 'unauthenticated' })
    expect(mockGetServerUser).toHaveBeenCalledTimes(1)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('returns 404 for missing or inaccessible owner chart after exact ordered SQL binds', async () => {
    admit('guest', false)
    const result = await GET(request(), params())
    expect(result.status).toBe(404)
    expect(await result.json()).toEqual({ error: 'not_found' })
    expectAdmissionQueries()
  })

  it('returns 404 for a super_admin when the chart does not exist', async () => {
    admit('super_admin', false)
    const result = await GET(request(), params())
    expect(result.status).toBe(404)
    expect(await result.json()).toEqual({ error: 'not_found' })
    expectAdmissionQueries(true)
  })

  it.each(['guest', 'client', 'acharya', 'admin', 'SUPER_ADMIN', ''])('keeps the owner SQL predicate for role %j', async (role) => {
    admit(role, false)
    const result = await GET(request(), params())
    expect(result.status).toBe(404)
    expectAdmissionQueries()
  })

  it('keeps the owner SQL predicate when the profile is missing', async () => {
    admit(null, false)
    const result = await GET(request(), params())
    expect(result.status).toBe(404)
    expectAdmissionQueries()
  })

  it('binds untrusted chart and user identifiers instead of interpolating SQL', async () => {
    const chartId = "chart' OR 1=1 --"
    const uid = "owner' OR 1=1 --"
    admit('guest', false)
    mockGetServerUser.mockResolvedValue({ uid })
    const result = await GET(request(), params(chartId))
    expect(result.status).toBe(404)
    expectAdmissionQueries(false, chartId, uid)
    expect(mockQuery.mock.calls.every(([sql]) => !sql.includes(chartId) && !sql.includes(uid))).toBe(true)
  })

  it('propagates session errors before any SQL or retirement notice', async () => {
    const failure = new Error('synthetic session failure')
    mockGetServerUser.mockRejectedValue(failure)
    await expect(GET(request(), params())).rejects.toBe(failure)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('propagates profile SQL errors without chart lookup or retirement notice', async () => {
    const failure = new Error('synthetic profile failure')
    mockGetServerUser.mockResolvedValue({ uid: USER_ID })
    mockQuery.mockRejectedValue(failure)
    await expect(GET(request(), params())).rejects.toBe(failure)
    expect(mockQuery.mock.calls).toEqual([[ROLE_SQL, [USER_ID]]])
  })

  it('propagates owner SQL errors without substituting an unavailable result', async () => {
    const failure = new Error('synthetic ownership failure')
    admit()
    mockQuery.mockReset().mockResolvedValueOnce({ rows: [{ role: 'guest' }] }).mockRejectedValueOnce(failure)
    await expect(GET(request(), params())).rejects.toBe(failure)
    expectAdmissionQueries()
  })

  it('propagates rejected params before session lookup or SQL', async () => {
    const failure = new Error('synthetic params failure')
    await expect(GET(request(), { params: Promise.reject(failure) })).rejects.toBe(failure)
    expect(mockGetServerUser).not.toHaveBeenCalled()
    expect(mockQuery).not.toHaveBeenCalled()
  })
})

describe('ayanamsha-status retirement contract', () => {
  it('returns an authenticated 410 machine-readable unavailable notice with no engine/build queries', async () => {
    admit()
    const result = await GET(request(), params())
    expect(result.status).toBe(410)
    const body = await result.json()
    expect(body).toMatchObject({ error: 'ENDPOINT_GONE', status: 'unavailable', message: expect.stringContaining('retired') })
    expect(body.message).toContain('compatibility notice only')
    expectAdmissionQueries()
    expect(Array.isArray(body)).toBe(false)
    expect(body).not.toHaveProperty('ayanamsha_status')
    expect(body).not.toHaveProperty('chart_id')
    const text = JSON.stringify(body)
    expect(text).not.toMatch(/not_built|steps_complete|steps_total|latest_build_id|engine_version|trigger a build|build first/i)
    expect(text).not.toContain(CHART_ID)
    expect(text).not.toContain(USER_ID)
    expect(dynamic).toBe('force-dynamic')
    expect(result.headers.get('Cache-Control')).toBe('no-store')
    expect(result.headers.get('Content-Type')).toContain('application/json')
  })

  it('admits super_admin across ownership using only its existing two exact Identity queries', async () => {
    admit('super_admin')
    const result = await GET(request(), params())
    expect(result.status).toBe(410)
    expect(await result.json()).toMatchObject({ error: 'ENDPOINT_GONE', status: 'unavailable' })
    expectAdmissionQueries(true)
  })

  it('limits current guidance to chart-level readiness, preparation and separate identity facts', async () => {
    admit()
    const result = await GET(request(), params())
    expect(result.status).toBe(410)
    const body = await result.json()
    expect(body.guidance.cockpit).toContain('chart-level run and asset readiness')
    expect(body.guidance.cockpit).toContain('does not provide per-ayanamsha engine versions or step progress')
    expect(body.guidance.preparation).toContain('do not reproduce the retired five-frame status contract')
    expect(body.guidance.fact_cross_check).toContain('chart_snapshot')
    expect(body.guidance.fact_cross_check).toContain('separately labelled identity fact cross-check')
    expect(body.guidance.fact_cross_check).toContain('does not measure per-ayanamsha build progress or consensus')
    expectAdmissionQueries()
  })
})

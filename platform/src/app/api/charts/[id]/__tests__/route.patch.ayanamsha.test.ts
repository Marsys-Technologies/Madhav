/**
 * PATCH /api/charts/[id] — ayanamsha edit guard end to end (SS N-319).
 *
 * Unlike route.patch.test.ts this does NOT mock the service: the real
 * updateChartAndMaybeRecompute runs against a fake transaction client (no
 * database), so an API caller who bypasses the edit form meets the same policy.
 * It proves the HTTP status and machine-readable code per policy and that a
 * refused request wrote nothing.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'

vi.mock('server-only', () => ({}))

const { mockGetServerUser, mockRequirePermission, mockGetPool, statements } = vi.hoisted(() => ({
  mockGetServerUser: vi.fn(),
  mockRequirePermission: vi.fn(),
  mockGetPool: vi.fn(),
  statements: [] as string[],
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn(), getPool: mockGetPool }))
vi.mock('@/lib/auth/requireChartPermission', () => ({ requireChartPermission: mockRequirePermission }))
vi.mock('@/lib/build/runDispatch', () => ({ dispatchPreparedRun: vi.fn() }))

import { PATCH } from '../route'

const CHART = '482012f1-0000-4000-8000-000000000001'
const ctx = { params: Promise.resolve({ id: CHART }) }

const STORED = {
  id: CHART,
  name: 'Test Native',
  preferred_name: 'Test',
  subject_name: null,
  birth_date: '1984-02-05',
  birth_time: '10:43:00',
  birth_place: 'Bhubaneswar',
  birth_lat: 20.2961,
  birth_lng: 85.8245,
  timezone_id: 'Asia/Kolkata',
  ayanamsa: 'lahiri_chitrapaksha',
  owner_id: 'owner-uid',
  client_id: 'owner-uid',
}

const BODY = {
  name: 'Test Native',
  preferred_name: 'Test',
  subject_name: null,
  birth_date: '1984-02-05',
  birth_time: '10:43',
  birth_place: 'Bhubaneswar',
  lat: 20.2961,
  lon: 85.8245,
  timezone_id: 'Asia/Kolkata',
  tz_offset: 5.5,
  ayanamshas: ['lahiri'],
}

function req(body: unknown) {
  return new NextRequest(`http://localhost/api/charts/${CHART}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  statements.length = 0
  mockGetServerUser.mockResolvedValue({ uid: 'owner-uid' })
  mockRequirePermission.mockResolvedValue(null)
  const client = {
    query: vi.fn(async (sql: string) => {
      statements.push(sql.trim())
      if (/FROM charts[\s\S]*FOR UPDATE/.test(sql)) return { rows: [STORED] }
      return { rows: [], rowCount: 0 }
    }),
    release: vi.fn(),
  }
  mockGetPool.mockResolvedValue({ connect: vi.fn().mockResolvedValue(client) })
})

afterEach(() => vi.unstubAllEnvs())

const wrote = () => statements.some((s) => /^(UPDATE|INSERT|DELETE)/i.test(s))

describe('PATCH /api/charts/[id] — ayanamsha edit policy', () => {
  it('default policy: 403 AYANAMSHA_EDIT_BLOCKED, names the ayanamsha, nothing written', async () => {
    vi.stubEnv('CHART_AYANAMSHA_EDIT_POLICY', '')
    const res = await PATCH(req({ ...BODY, ayanamshas: ['lahiri', 'kp'] }), ctx)
    expect(res.status).toBe(403)
    const json = await res.json()
    expect(json.code).toBe('AYANAMSHA_EDIT_BLOCKED')
    expect(json.error).toMatch(/ayanamsha of an existing chart can't be changed here/i)
    expect(json.error).toMatch(/contact support/i)
    expect(json.fields).toHaveProperty('ayanamshas')
    expect(wrote()).toBe(false)
    expect(statements).toContain('ROLLBACK')
  })

  it('an unknown policy value is block_all, not off', async () => {
    vi.stubEnv('CHART_AYANAMSHA_EDIT_POLICY', 'disabled')
    vi.spyOn(console, 'error').mockImplementation(() => undefined)
    const res = await PATCH(req({ ...BODY, ayanamshas: ['kp'] }), ctx)
    expect(res.status).toBe(403)
    expect((await res.json()).code).toBe('AYANAMSHA_EDIT_BLOCKED')
  })

  it('block_all refuses a mixed request as a whole (birth time + ayanamsha), nothing written', async () => {
    const res = await PATCH(req({ ...BODY, birth_time: '10:44', ayanamshas: ['kp'] }), ctx)
    expect(res.status).toBe(403)
    expect((await res.json()).error).toMatch(/ayanamsha[\s\S]*nothing was saved/i)
    expect(wrote()).toBe(false)
  })

  it('warn: 409 AYANAMSHA_EDIT_NEEDS_CONFIRMATION without the flag, nothing written', async () => {
    vi.stubEnv('CHART_AYANAMSHA_EDIT_POLICY', 'warn')
    const res = await PATCH(req({ ...BODY, ayanamshas: ['kp'] }), ctx)
    expect(res.status).toBe(409)
    const json = await res.json()
    expect(json.code).toBe('AYANAMSHA_EDIT_NEEDS_CONFIRMATION')
    expect(json.error).toMatch(/erases all built results/i)
    expect(json.error).toMatch(/archives its conversations/i)
    expect(json.error).toMatch(/requires confirmation/i)
    expect(wrote()).toBe(false)
  })

  it('warn with confirm_destructive: true gets past the guard (it proceeds into the recompute path)', async () => {
    vi.stubEnv('CHART_AYANAMSHA_EDIT_POLICY', 'warn')
    const res = await PATCH(req({ ...BODY, ayanamshas: ['kp'], confirm_destructive: true }), ctx)
    // The fake database has no build registry, so the plan cannot be frozen; the point is that
    // the refusal is not the ayanamsha guard.
    const json = await res.json()
    expect(json.code).not.toBe('AYANAMSHA_EDIT_NEEDS_CONFIRMATION')
    expect(json.code).not.toBe('AYANAMSHA_EDIT_BLOCKED')
    expect(statements.some((s) => /asset_registry/.test(s))).toBe(true)
  })

  it.each(['block_all', 'warn', 'off'])('%s: a long-form stored value equal to the submitted short list is a 200 no-op', async (policy) => {
    vi.stubEnv('CHART_AYANAMSHA_EDIT_POLICY', policy)
    const res = await PATCH(req(BODY), ctx)
    expect(res.status).toBe(200)
    expect((await res.json()).data.mode).toBe('noop')
    expect(wrote()).toBe(false)
  })

  it.each(['block_all', 'warn', 'off'])('%s: a name-only edit with the ayanamsha omitted is a 200 display-only', async (policy) => {
    vi.stubEnv('CHART_AYANAMSHA_EDIT_POLICY', policy)
    const { ayanamshas: _omit, ...withoutAyanamshas } = BODY
    void _omit
    const res = await PATCH(req({ ...withoutAyanamshas, name: 'Renamed' }), ctx)
    expect(res.status).toBe(200)
    expect((await res.json()).data).toMatchObject({ mode: 'display-only', changedFields: ['name'] })
  })
})

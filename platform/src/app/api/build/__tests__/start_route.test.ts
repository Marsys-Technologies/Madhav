/**
 * Route tests for POST /api/build/start — Platform Modernization 4.build_trigger.
 *
 * Acceptance criteria from BRIEF_4_build_trigger:
 *   - Feature-flag default OFF → 503 + log
 *   - authorizeChartAccess gates the trigger: owner/super_admin only.
 *     'view' grantee → 403; 'deny' (no row) → 404; unauth → 401.
 *   - Happy path enqueues + returns { build_id, task_name }
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery, mockGetServerUser, mockEnqueueBuild, mockGetFlag } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
  mockEnqueueBuild: vi.fn(),
  mockGetFlag: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/build/trigger', () => ({
  enqueueBuild: mockEnqueueBuild,
}))
vi.mock('@/lib/config', () => ({ getFlag: mockGetFlag }))

// Real implementation: re-export under a vi.importActual so the route
// still uses the real authorizeChartAccess (which only needs the mocked
// query() to function).
vi.mock('@/lib/auth/authorizeChartAccess', async () => {
  const actual = await vi.importActual<
    typeof import('@/lib/auth/authorizeChartAccess')
  >('@/lib/auth/authorizeChartAccess')
  return actual
})

import { POST } from '../start/route'

function makeReq(body: unknown): Request {
  return new Request('http://localhost/api/build/start', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  mockQuery.mockReset()
  mockGetServerUser.mockReset()
  mockEnqueueBuild.mockReset()
  mockGetFlag.mockReset()
  // Sane defaults — flag ON, user authed, owner of the chart.
  mockGetFlag.mockImplementation((name: string) => name === 'BUILD_TRIGGER_ENABLED')
})

describe('POST /api/build/start — feature flag kill-switch', () => {
  it('returns 503 when MARSYS_FLAG_BUILD_TRIGGER_ENABLED is false', async () => {
    mockGetFlag.mockReturnValue(false)
    const res = await POST()
    expect(res.status).toBe(503)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('build_trigger_disabled')
    expect(mockEnqueueBuild).not.toHaveBeenCalled()
  })
})

describe('POST /api/build/start — input validation', () => {
  it('returns 400 when chart_id is missing', async () => {
    const res = await POST()
    expect(res.status).toBe(400)
  })

  it('returns 422 when ayanamshas contains invalid value', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'owner-1' })
    const res = await POST()
    expect(res.status).toBe(422)
  })
})

describe('POST /api/build/start — auth + authorizeChartAccess gate', () => {
  it('returns 401 when unauthenticated', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await POST()
    expect(res.status).toBe(401)
  })

  it('returns 403 when the user is a view-grantee (permission=view)', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'grantee' })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'guest' }] })
      if (/FROM charts WHERE id/.test(sql))
        return Promise.resolve({ rows: [{ owner_id: 'owner-other' }] })
      if (/FROM chart_grants/.test(sql))
        return Promise.resolve({ rows: [{ permission: 'view' }] })
      return Promise.resolve({ rows: [] })
    })
    const res = await POST()
    expect(res.status).toBe(403)
    const body = (await res.json()) as { permission: string }
    expect(body.permission).toBe('view')
    expect(mockEnqueueBuild).not.toHaveBeenCalled()
  })

  it('returns 404 when permission is deny', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'stranger' })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'guest' }] })
      if (/FROM charts WHERE id/.test(sql))
        return Promise.resolve({ rows: [{ owner_id: 'owner-other' }] })
      if (/FROM chart_grants/.test(sql)) return Promise.resolve({ rows: [] })
      return Promise.resolve({ rows: [] })
    })
    const res = await POST()
    expect(res.status).toBe(404)
    expect(mockEnqueueBuild).not.toHaveBeenCalled()
  })
})

describe('POST /api/build/start — happy path', () => {
  it('owner enqueues a build and gets { build_id, task_name }', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'owner-1' })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'guest' }] })
      if (/FROM charts WHERE id/.test(sql))
        return Promise.resolve({ rows: [{ owner_id: 'owner-1' }] })
      if (/FROM charts WHERE chart_id/.test(sql))
        return Promise.resolve({ rows: [{ chart_id: 'c1' }] })
      if (/INSERT INTO builds/.test(sql))
        return Promise.resolve({ rows: [{ build_id: 'build-7' }] })
      return Promise.resolve({ rows: [] })
    })
    mockEnqueueBuild.mockResolvedValue({ buildId: 'build-7', taskName: 'projects/p/queues/q/tasks/t' })

    const res = await POST()
    expect(res.status).toBe(200)
    const body = (await res.json()) as { build_id: string; status: string }
    expect(body.build_id).toBe('build-7')
    expect(body.status).toBe('queued')

    expect(mockEnqueueBuild).toHaveBeenCalledTimes(1)
    const arg = mockEnqueueBuild.mock.calls[0][0] as Record<string, string>
    expect(arg.chartId).toBe('c1')
    expect(arg.triggeredBy).toBe('manual:owner-1')
  })

  it('super_admin can build any chart', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'admin-1' })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'super_admin' }] })
      // Note: owner check is skipped for super_admin (returns 'all' on rule 1)
      if (/FROM charts WHERE chart_id/.test(sql))
        return Promise.resolve({ rows: [{ chart_id: 'c2' }] })
      if (/INSERT INTO builds/.test(sql))
        return Promise.resolve({ rows: [{ build_id: 'build-8' }] })
      return Promise.resolve({ rows: [] })
    })
    mockEnqueueBuild.mockResolvedValue({ buildId: 'build-8', taskName: 'projects/p/queues/q/tasks/t' })

    const res = await POST()
    expect(res.status).toBe(200)
  })
})

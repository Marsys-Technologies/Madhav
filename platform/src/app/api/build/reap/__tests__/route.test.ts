/**
 * Route tests for POST /api/build/reap — L3 build reaper
 *
 * Brief: CLAUDECODE_BRIEF_BUILD_TIMEOUT_HARDENING_v1_0.md §L3.5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── Hoist mocks ──────────────────────────────────────────────────────────────

const { mockQuery, mockVerifyOidcToken, mockListLiveBuildExecutions } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockVerifyOidcToken: vi.fn(),
  mockListLiveBuildExecutions: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/auth/oidc', () => ({ verifyOidcToken: mockVerifyOidcToken }))
vi.mock('@/lib/cloud_run/jobs', () => ({ listLiveBuildExecutions: mockListLiveBuildExecutions }))

import { POST } from '../route'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function makeReq(opts: { auth?: string } = {}): Request {
  const headers: Record<string, string> = { 'content-type': 'application/json' }
  if (opts.auth !== undefined) headers['Authorization'] = opts.auth
  return new Request('http://localhost/api/build/reap', { method: 'POST', headers })
}

// ─── Setup ────────────────────────────────────────────────────────────────────

beforeEach(() => {
  mockQuery.mockReset()
  mockVerifyOidcToken.mockReset()
  mockListLiveBuildExecutions.mockReset()
  // Happy-path defaults
  mockVerifyOidcToken.mockResolvedValue({ email: 'build-reaper@madhav-astrology.iam.gserviceaccount.com', sub: 'sub123' })
  mockListLiveBuildExecutions.mockResolvedValue(new Set<string>())
  mockQuery.mockResolvedValue({ rows: [] })
})

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('POST /api/build/reap — auth', () => {
  it('returns 401 without Authorization header', async () => {
    const res = await POST(makeReq())
    expect(res.status).toBe(401)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('unauthorized')
  })

  it('returns 403 with invalid OIDC token (verifyOidcToken returns null)', async () => {
    mockVerifyOidcToken.mockResolvedValue(null)
    const res = await POST(makeReq({ auth: 'Bearer bad-token' }))
    expect(res.status).toBe(403)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('forbidden')
  })

  it('returns 403 when verifyOidcToken throws (e.g. signature mismatch)', async () => {
    mockVerifyOidcToken.mockRejectedValue(new Error('TokenExpiredError'))
    const res = await POST(makeReq({ auth: 'Bearer expired-token' }))
    expect(res.status).toBe(403)
  })
})

describe('POST /api/build/reap — reap logic', () => {
  it('returns {reaped:0} when no stale candidates', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    const res = await POST(makeReq({ auth: 'Bearer valid-token' }))
    expect(res.status).toBe(200)
    const body = (await res.json()) as { reaped: number }
    expect(body.reaped).toBe(0)
  })

  it('skips builds present in the live-execution set', async () => {
    mockListLiveBuildExecutions.mockResolvedValue(new Set(['live-build-id']))
    mockQuery.mockResolvedValue({
      rows: [{ build_id: 'live-build-id', status: 'running', age_minutes: 90 }],
    })
    const res = await POST(makeReq({ auth: 'Bearer valid-token' }))
    expect(res.status).toBe(200)
    const body = (await res.json()) as { reaped: number; live_skipped: number }
    expect(body.reaped).toBe(0)
    expect(body.live_skipped).toBe(1)
    // UPDATE should NOT have been called
    const updateCall = mockQuery.mock.calls.find(([sql]: string[]) => /UPDATE builds/.test(sql))
    expect(updateCall).toBeUndefined()
  })

  it('marks N builds cancelled, build_steps skipped, emits N notifications', async () => {
    const staleBuilds = [
      { build_id: 'stale-1', status: 'running', age_minutes: 75 },
      { build_id: 'stale-2', status: 'queued', age_minutes: 20 },
    ]
    mockListLiveBuildExecutions.mockResolvedValue(new Set<string>())
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM builds/.test(sql)) return Promise.resolve({ rows: staleBuilds })
      return Promise.resolve({ rows: [] })
    })

    const res = await POST(makeReq({ auth: 'Bearer valid-token' }))
    expect(res.status).toBe(200)
    const body = (await res.json()) as { reaped: number; build_ids: string[] }
    expect(body.reaped).toBe(2)
    expect(body.build_ids).toEqual(['stale-1', 'stale-2'])

    // Should have called: SELECT, UPDATE builds, UPDATE build_steps, INSERT notifications
    const updateBuilds = mockQuery.mock.calls.find(([sql]: string[]) =>
      /UPDATE builds/.test(sql) && /cancelled/.test(sql),
    )
    expect(updateBuilds).toBeDefined()
    expect(updateBuilds![1]).toEqual([['stale-1', 'stale-2']])

    const updateSteps = mockQuery.mock.calls.find(([sql]: string[]) =>
      /UPDATE build_steps/.test(sql) && /skipped/.test(sql),
    )
    expect(updateSteps).toBeDefined()

    const insertNotif = mockQuery.mock.calls.find(([sql]: string[]) =>
      /INSERT INTO build_notifications/.test(sql) && /reaped_stale/.test(sql),
    )
    expect(insertNotif).toBeDefined()
  })
})

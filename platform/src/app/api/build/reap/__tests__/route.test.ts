/**
 * Route tests for POST /api/build/reap — L3 build reaper
 *
 * Brief: CLAUDECODE_BRIEF_BUILD_TIMEOUT_HARDENING_v1_0.md §L3.5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── Hoist mocks ──────────────────────────────────────────────────────────────

const mockPoolQuery = vi.fn()
const mockClientQuery = vi.fn()
const mockClientRelease = vi.fn()

const { mockVerifyOidcToken, mockListLiveBuildExecutions, mockGetPool } = vi.hoisted(() => ({
  mockVerifyOidcToken: vi.fn(),
  mockListLiveBuildExecutions: vi.fn(),
  mockGetPool: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ getPool: mockGetPool }))
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
  mockVerifyOidcToken.mockReset()
  mockListLiveBuildExecutions.mockReset()
  mockGetPool.mockReset()
  mockPoolQuery.mockReset()
  mockClientQuery.mockReset()
  mockClientRelease.mockReset()

  // Happy-path defaults
  mockVerifyOidcToken.mockResolvedValue({
    email: 'build-reaper@madhav-astrology.iam.gserviceaccount.com',
    sub: 'sub123',
  })
  mockListLiveBuildExecutions.mockResolvedValue(new Set<string>())

  // Pool: direct .query() for SELECT; .connect() for the transaction client
  mockPoolQuery.mockResolvedValue({ rows: [] })
  mockClientQuery.mockResolvedValue({ rows: [] })
  mockGetPool.mockResolvedValue({
    query: mockPoolQuery,
    connect: vi.fn().mockResolvedValue({
      query: mockClientQuery,
      release: mockClientRelease,
    }),
  })
})

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('POST /api/build/reap — auth', () => {
  it('returns 401 without Authorization header', async () => {
    const res = await POST()
    expect(res.status).toBe(401)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('unauthorized')
  })

  it('returns 403 with invalid OIDC token (verifyOidcToken returns null)', async () => {
    mockVerifyOidcToken.mockResolvedValue(null)
    const res = await POST()
    expect(res.status).toBe(403)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('forbidden')
  })

  it('returns 403 when verifyOidcToken throws', async () => {
    mockVerifyOidcToken.mockRejectedValue(new Error('TokenExpiredError'))
    const res = await POST()
    expect(res.status).toBe(403)
  })

  it('returns 403 when email is not a service account and BUILD_REAPER_SA_EMAIL is unset', async () => {
    const original = process.env.BUILD_REAPER_SA_EMAIL
    delete process.env.BUILD_REAPER_SA_EMAIL
    mockVerifyOidcToken.mockResolvedValue({ email: 'user@gmail.com', sub: 'sub' })
    const res = await POST()
    expect(res.status).toBe(403)
    if (original !== undefined) process.env.BUILD_REAPER_SA_EMAIL = original
  })
})

describe('POST /api/build/reap — reap logic', () => {
  it('returns {reaped:0} when no stale candidates', async () => {
    mockPoolQuery.mockResolvedValue({ rows: [] })
    const res = await POST()
    expect(res.status).toBe(200)
    const body = (await res.json()) as { reaped: number }
    expect(body.reaped).toBe(0)
    // listLiveBuildExecutions should NOT be called when no candidates
    expect(mockListLiveBuildExecutions).not.toHaveBeenCalled()
  })

  it('skips builds present in the live-execution set', async () => {
    mockListLiveBuildExecutions.mockResolvedValue(new Set(['live-build-id']))
    mockPoolQuery.mockResolvedValue({
      rows: [{ build_id: 'live-build-id', status: 'running', age_minutes: 90 }],
    })
    const res = await POST()
    expect(res.status).toBe(200)
    const body = (await res.json()) as { reaped: number; live_skipped: number }
    expect(body.reaped).toBe(0)
    expect(body.live_skipped).toBe(1)
    // Transaction should NOT have been opened for a no-reap result
    expect(mockClientQuery).not.toHaveBeenCalled()
  })

  it('marks N builds cancelled, build_steps skipped, emits N notifications (single transaction)', async () => {
    const staleBuilds = [
      { build_id: 'stale-1', status: 'running', age_minutes: 75 },
      { build_id: 'stale-2', status: 'queued', age_minutes: 20 },
    ]
    mockPoolQuery.mockResolvedValue({ rows: staleBuilds })
    mockListLiveBuildExecutions.mockResolvedValue(new Set<string>())

    const res = await POST()
    expect(res.status).toBe(200)
    const body = (await res.json()) as { reaped: number; build_ids: string[] }
    expect(body.reaped).toBe(2)
    expect(body.build_ids).toEqual(['stale-1', 'stale-2'])

    // Transaction: BEGIN + UPDATE builds + UPDATE build_steps + INSERT notifications + COMMIT = 5 calls
    const txCalls = mockClientQuery.mock.calls.map(([sql]: string[]) => sql.trim().split(/\s+/)[0])
    expect(txCalls).toContain('BEGIN')
    expect(txCalls).toContain('COMMIT')
    const updateBuilds = mockClientQuery.mock.calls.find(([sql]: string[]) =>
      /UPDATE builds/.test(sql) && /cancelled/.test(sql),
    )
    expect(updateBuilds).toBeDefined()
    const updateSteps = mockClientQuery.mock.calls.find(([sql]: string[]) =>
      /UPDATE build_steps/.test(sql) && /skipped/.test(sql),
    )
    expect(updateSteps).toBeDefined()
    const insertNotif = mockClientQuery.mock.calls.find(([sql]: string[]) =>
      /INSERT INTO build_notifications/.test(sql) && /reaped_stale/.test(sql),
    )
    expect(insertNotif).toBeDefined()
    // Client must be released even on success
    expect(mockClientRelease).toHaveBeenCalled()
  })
})

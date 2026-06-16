/**
 * Route tests for POST /api/build/cancel/[buildId] — [BUILD-ORCH-D-02]
 *
 * Acceptance criteria (≥15 assertions):
 *   - Unauthenticated request → 401
 *   - Non-owner request → 403 (or 404 for missing build)
 *   - Cancel queued build → 200 with message
 *   - Cancel running build → 200 with message
 *   - Cancel already-cancelled build → 409
 *   - Cancel completed build → 409
 *   - Cancel failed build → 409
 *   - Cancel cancelling build → 200 with 'already in progress'
 *   - Non-existent buildId → 404
 *   - Response body includes build_id
 *   - Status updated to 'cancelling' in DB (verify mock call)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── Hoist mocks ─────────────────────────────────────────────────────────────

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { POST } from '../route'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeReq(): Request {
  return new Request('http://localhost/api/build/cancel/test-build-id', {
    method: 'POST',
  })
}

function makeParams(buildId: string): { params: Promise<{ buildId: string }> } {
  return { params: Promise.resolve({ buildId }) }
}

/** Sets up the standard auth mocks for a given user + role. */
function setupAuth(uid: string, role: 'guest' | 'super_admin' = 'guest') {
  mockGetServerUser.mockResolvedValue({ uid })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }] })
    return Promise.resolve({ rows: [] })
  })
}

/** Sets up build row mock to return the given status + owner. */
function setupBuildRow(uid: string, role: 'guest' | 'super_admin', buildStatus: string, ownerUid: string) {
  mockGetServerUser.mockResolvedValue({ uid })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }] })
    if (/FROM builds WHERE build_id/.test(sql))
      return Promise.resolve({
        rows: [{ build_id: 'build-123', triggered_by_uid: ownerUid, status: buildStatus }],
      })
    if (/UPDATE builds/.test(sql)) return Promise.resolve({ rows: [] })
    return Promise.resolve({ rows: [] })
  })
}

// ─── Setup ────────────────────────────────────────────────────────────────────

beforeEach(() => {
  mockQuery.mockReset()
  mockGetServerUser.mockReset()
})

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('POST /api/build/cancel/[buildId] — auth gate', () => {
  it('returns 401 when unauthenticated', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await POST()
    expect(res.status).toBe(401)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('unauthenticated')
  })

  it('returns 403 when build belongs to a different user and requester is not super_admin', async () => {
    setupBuildRow('non-owner-uid', 'guest', 'queued', 'actual-owner-uid')
    const res = await POST()
    expect(res.status).toBe(403)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('forbidden')
  })

  it('returns 404 when buildId is not found in the DB', async () => {
    setupAuth('user-uid')
    // Override to return empty rows for builds lookup
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'guest' }] })
      if (/FROM builds WHERE build_id/.test(sql)) return Promise.resolve({ rows: [] })
      return Promise.resolve({ rows: [] })
    })
    const res = await POST()
    expect(res.status).toBe(404)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('build_not_found')
  })
})

describe('POST /api/build/cancel/[buildId] — happy path (owner cancels)', () => {
  it('cancels a queued build and returns 200 with build_id', async () => {
    setupBuildRow('owner-uid', 'guest', 'queued', 'owner-uid')
    const res = await POST()
    expect(res.status).toBe(200)
    const body = (await res.json()) as { message: string; build_id: string }
    expect(body.message).toBe('Cancellation requested')
    expect(body.build_id).toBe('build-123')
  })

  it('cancels a running build and returns 200', async () => {
    setupBuildRow('owner-uid', 'guest', 'running', 'owner-uid')
    const res = await POST()
    expect(res.status).toBe(200)
    const body = (await res.json()) as { message: string }
    expect(body.message).toBe('Cancellation requested')
  })

  it('updates DB status to cancelling when cancelling a queued build', async () => {
    setupBuildRow('owner-uid', 'guest', 'queued', 'owner-uid')
    await POST()

    const updateCall = mockQuery.mock.calls.find(([sql]: string[]) =>
      /UPDATE builds/.test(sql) && /cancelling/.test(sql),
    )
    expect(updateCall).toBeDefined()
    expect(updateCall![1]).toContain('build-123')
  })

  it('updates DB status to cancelling when cancelling a running build', async () => {
    setupBuildRow('owner-uid', 'guest', 'running', 'owner-uid')
    await POST()

    const updateCall = mockQuery.mock.calls.find(([sql]: string[]) =>
      /UPDATE builds/.test(sql) && /cancelling/.test(sql),
    )
    expect(updateCall).toBeDefined()
  })
})

describe('POST /api/build/cancel/[buildId] — idempotent cancelling status', () => {
  it('returns 200 with "already in progress" if status is already cancelling', async () => {
    setupBuildRow('owner-uid', 'guest', 'cancelling', 'owner-uid')
    const res = await POST()
    expect(res.status).toBe(200)
    const body = (await res.json()) as { message: string; build_id: string }
    expect(body.message).toBe('Cancellation already in progress')
    expect(body.build_id).toBe('build-123')
  })

  it('does NOT issue an UPDATE when status is already cancelling', async () => {
    setupBuildRow('owner-uid', 'guest', 'cancelling', 'owner-uid')
    await POST()

    const updateCall = mockQuery.mock.calls.find(([sql]: string[]) =>
      /UPDATE builds/.test(sql),
    )
    expect(updateCall).toBeUndefined()
  })
})

describe('POST /api/build/cancel/[buildId] — terminal status rejections (409)', () => {
  it('returns 409 when build is already cancelled', async () => {
    setupBuildRow('owner-uid', 'guest', 'cancelled', 'owner-uid')
    const res = await POST()
    expect(res.status).toBe(409)
    const body = (await res.json()) as { error: string; current_status: string }
    expect(body.error).toBe('Build cannot be cancelled')
    expect(body.current_status).toBe('cancelled')
  })

  it('returns 409 when build is complete', async () => {
    setupBuildRow('owner-uid', 'guest', 'complete', 'owner-uid')
    const res = await POST()
    expect(res.status).toBe(409)
    const body = (await res.json()) as { error: string; current_status: string }
    expect(body.error).toBe('Build cannot be cancelled')
    expect(body.current_status).toBe('complete')
  })

  it('returns 409 when build has failed', async () => {
    setupBuildRow('owner-uid', 'guest', 'failed', 'owner-uid')
    const res = await POST()
    expect(res.status).toBe(409)
    const body = (await res.json()) as { error: string; current_status: string; build_id: string }
    expect(body.error).toBe('Build cannot be cancelled')
    expect(body.current_status).toBe('failed')
    expect(body.build_id).toBe('build-123')
  })

  it('does NOT issue an UPDATE for terminal statuses', async () => {
    setupBuildRow('owner-uid', 'guest', 'complete', 'owner-uid')
    await POST()

    const updateCall = mockQuery.mock.calls.find(([sql]: string[]) =>
      /UPDATE builds/.test(sql),
    )
    expect(updateCall).toBeUndefined()
  })
})

describe('POST /api/build/cancel/[buildId] — super_admin override', () => {
  it('super_admin can cancel a build owned by another user', async () => {
    setupBuildRow('admin-uid', 'super_admin', 'queued', 'other-owner-uid')
    const res = await POST()
    expect(res.status).toBe(200)
    const body = (await res.json()) as { message: string; build_id: string }
    expect(body.message).toBe('Cancellation requested')
    expect(body.build_id).toBe('build-123')
  })

  it('super_admin cancel issues the UPDATE to cancelling', async () => {
    setupBuildRow('admin-uid', 'super_admin', 'running', 'other-owner-uid')
    await POST()

    const updateCall = mockQuery.mock.calls.find(([sql]: string[]) =>
      /UPDATE builds/.test(sql) && /cancelling/.test(sql),
    )
    expect(updateCall).toBeDefined()
  })
})

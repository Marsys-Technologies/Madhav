/**
 * Route tests for GET /api/build/active — [BUILD-ORCH-D-03]
 *
 * Acceptance criteria (≥15 assertions):
 *   - Unauthenticated request → 401
 *   - No active builds → 200 with empty array
 *   - One queued build → included in response
 *   - running + cancelling builds both included
 *   - completed/failed builds NOT returned (enforced by query scope)
 *   - Response item has required fields
 *   - ayanamshas is an array
 *   - progress_pct = 0 when steps_total = 0
 *   - progress_pct computed correctly (e.g. 7/14 steps → 50)
 *   - super_admin can see other users' active builds
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── Hoist mocks ─────────────────────────────────────────────────────────────

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { GET } from '../active/route'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeReq(): Request {
  return new Request('http://localhost/api/build/active', { method: 'GET' })
}

/** Build row factory. */
function makeBuildRow(overrides: Partial<{
  build_id: string
  chart_id: string
  chart_name: string | null
  ayanamshas: string[]
  status: string
  queued_at: string
  started_at: string | null
  steps_complete: number
  steps_total: number
}> = {}) {
  return {
    build_id: 'build-abc',
    chart_id: 'chart-xyz',
    chart_name: 'Test Chart',
    ayanamshas: ['lahiri', 'kp'],
    status: 'queued',
    queued_at: '2026-05-29T10:00:00.000Z',
    started_at: null,
    steps_complete: 0,
    steps_total: 14,
    ...overrides,
  }
}

/**
 * Sets up auth + DB mocks.
 * `buildRows` is what the main builds query returns.
 */
function setupMocks(
  uid: string,
  role: 'guest' | 'super_admin',
  buildRows: ReturnType<typeof makeBuildRow>[],
) {
  mockGetServerUser.mockResolvedValue({ uid })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }] })
    // Main active-builds query
    return Promise.resolve({ rows: buildRows })
  })
}

// ─── Setup ────────────────────────────────────────────────────────────────────

beforeEach(() => {
  mockQuery.mockReset()
  mockGetServerUser.mockReset()
})

// ─── Tests: auth gate ─────────────────────────────────────────────────────────

describe('GET /api/build/active — auth gate', () => {
  it('returns 401 when unauthenticated', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await GET()
    expect(res.status).toBe(401)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('unauthenticated')
  })
})

// ─── Tests: empty result ──────────────────────────────────────────────────────

describe('GET /api/build/active — empty result', () => {
  it('returns 200 with empty array when no active builds exist', async () => {
    setupMocks('user-1', 'guest', [])
    const res = await GET()
    expect(res.status).toBe(200)
    const body = (await res.json()) as unknown[]
    expect(Array.isArray(body)).toBe(true)
    expect(body).toHaveLength(0)
  })
})

// ─── Tests: single build inclusion ───────────────────────────────────────────

describe('GET /api/build/active — queued build included', () => {
  it('returns a queued build in the response array', async () => {
    const row = makeBuildRow({ status: 'queued', build_id: 'b-queued' })
    setupMocks('user-1', 'guest', [row])
    const res = await GET()
    expect(res.status).toBe(200)
    const body = (await res.json()) as Array<{ build_id: string; status: string }>
    expect(body).toHaveLength(1)
    expect(body[0].build_id).toBe('b-queued')
    expect(body[0].status).toBe('queued')
  })

  it('includes a running build', async () => {
    const row = makeBuildRow({ status: 'running', build_id: 'b-running' })
    setupMocks('user-1', 'guest', [row])
    const res = await GET()
    const body = (await res.json()) as Array<{ status: string }>
    expect(body[0].status).toBe('running')
  })

  it('includes a cancelling build', async () => {
    const row = makeBuildRow({ status: 'cancelling', build_id: 'b-cancelling' })
    setupMocks('user-1', 'guest', [row])
    const res = await GET()
    const body = (await res.json()) as Array<{ status: string }>
    expect(body[0].status).toBe('cancelling')
  })
})

// ─── Tests: response shape ────────────────────────────────────────────────────

describe('GET /api/build/active — response item shape', () => {
  it('response item contains all required fields', async () => {
    const row = makeBuildRow({ steps_complete: 7, steps_total: 14 })
    setupMocks('user-1', 'guest', [row])
    const res = await GET()
    const body = (await res.json()) as Array<Record<string, unknown>>
    const item = body[0]
    expect(item).toHaveProperty('build_id')
    expect(item).toHaveProperty('chart_id')
    expect(item).toHaveProperty('chart_name')
    expect(item).toHaveProperty('ayanamshas')
    expect(item).toHaveProperty('status')
    expect(item).toHaveProperty('queued_at')
    expect(item).toHaveProperty('started_at')
    expect(item).toHaveProperty('steps_complete')
    expect(item).toHaveProperty('steps_total')
    expect(item).toHaveProperty('progress_pct')
  })

  it('ayanamshas is an array', async () => {
    const row = makeBuildRow({ ayanamshas: ['lahiri', 'kp', 'raman'] })
    setupMocks('user-1', 'guest', [row])
    const res = await GET()
    const body = (await res.json()) as Array<{ ayanamshas: unknown }>
    expect(Array.isArray(body[0].ayanamshas)).toBe(true)
    expect(body[0].ayanamshas).toHaveLength(3)
  })

  it('chart_name is null when not joined', async () => {
    const row = makeBuildRow({ chart_name: null })
    setupMocks('user-1', 'guest', [row])
    const res = await GET()
    const body = (await res.json()) as Array<{ chart_name: unknown }>
    expect(body[0].chart_name).toBeNull()
  })

  it('started_at is null for queued builds', async () => {
    const row = makeBuildRow({ status: 'queued', started_at: null })
    setupMocks('user-1', 'guest', [row])
    const res = await GET()
    const body = (await res.json()) as Array<{ started_at: unknown }>
    expect(body[0].started_at).toBeNull()
  })
})

// ─── Tests: progress computation ─────────────────────────────────────────────

describe('GET /api/build/active — progress_pct computation', () => {
  it('progress_pct is 0 when steps_total is 0', async () => {
    const row = makeBuildRow({ steps_complete: 0, steps_total: 0 })
    setupMocks('user-1', 'guest', [row])
    const res = await GET()
    const body = (await res.json()) as Array<{ progress_pct: number }>
    expect(body[0].progress_pct).toBe(0)
  })

  it('progress_pct = 50 when 7/14 steps complete', async () => {
    const row = makeBuildRow({ steps_complete: 7, steps_total: 14 })
    setupMocks('user-1', 'guest', [row])
    const res = await GET()
    const body = (await res.json()) as Array<{ progress_pct: number }>
    expect(body[0].progress_pct).toBe(50)
  })

  it('progress_pct = 100 when all steps complete', async () => {
    const row = makeBuildRow({ steps_complete: 14, steps_total: 14 })
    setupMocks('user-1', 'guest', [row])
    const res = await GET()
    const body = (await res.json()) as Array<{ progress_pct: number }>
    expect(body[0].progress_pct).toBe(100)
  })

  it('steps_complete and steps_total are numeric in response', async () => {
    const row = makeBuildRow({ steps_complete: 3, steps_total: 14 })
    setupMocks('user-1', 'guest', [row])
    const res = await GET()
    const body = (await res.json()) as Array<{ steps_complete: number; steps_total: number }>
    expect(typeof body[0].steps_complete).toBe('number')
    expect(typeof body[0].steps_total).toBe('number')
  })
})

// ─── Tests: super_admin scope ─────────────────────────────────────────────────

describe('GET /api/build/active — super_admin scope', () => {
  it('super_admin receives builds from other users', async () => {
    // Two builds from different owners returned by DB
    const rows = [
      makeBuildRow({ build_id: 'b-user1', status: 'running' }),
      makeBuildRow({ build_id: 'b-user2', status: 'queued' }),
    ]
    setupMocks('admin-uid', 'super_admin', rows)
    const res = await GET()
    expect(res.status).toBe(200)
    const body = (await res.json()) as Array<{ build_id: string }>
    expect(body).toHaveLength(2)
    const ids = body.map((b) => b.build_id)
    expect(ids).toContain('b-user1')
    expect(ids).toContain('b-user2')
  })

  it('super_admin query does NOT pass uid as parameter', async () => {
    setupMocks('admin-uid', 'super_admin', [])
    await GET()

    // The last query call (after profile lookup) should have empty params
    const calls = mockQuery.mock.calls as Array<[string, unknown[]]>
    const buildsCall = calls.find(([sql]) => /FROM builds/.test(sql))
    expect(buildsCall).toBeDefined()
    expect(buildsCall![1]).toHaveLength(0)
  })
})

// ─── Tests: Cache-Control header ─────────────────────────────────────────────

describe('GET /api/build/active — response headers', () => {
  it('sets Cache-Control: max-age=5', async () => {
    setupMocks('user-1', 'guest', [])
    const res = await GET()
    expect(res.headers.get('Cache-Control')).toBe('max-age=5')
  })
})

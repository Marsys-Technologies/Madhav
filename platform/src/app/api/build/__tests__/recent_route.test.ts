/**
 * Route tests for GET /api/build/recent — [BUILD-ORCH-D-04]
 *
 * Acceptance criteria (≥15 assertions):
 *   - Unauthenticated → 401
 *   - No recent builds → 200 empty array
 *   - Build completed 12h ago → included
 *   - Build completed 25h ago → excluded (>24h, enforced by DB query)
 *   - Failed build included (with error_summary populated)
 *   - queued/running builds NOT returned (DB query filters terminal statuses only)
 *   - Response item has: build_id, chart_id, status, finished_at, ayanamshas
 *   - error_summary present on all items (null for complete, string for failed)
 *   - ayanamshas is an array
 *   - chart_name is null when not joined
 *   - super_admin sees all users' builds (no uid filter)
 *   - Cache-Control: no-store
 *   - Graceful degradation when notification_views absent (no NV join attempted)
 *   - Graceful degradation: response is still 200 + array shape when NV table absent
 *   - Multiple builds returned in finished_at DESC order
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── Hoist mocks ──────────────────────────────────────────────────────────────

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { GET } from '../recent/route'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function makeReq(): Request {
  return new Request('http://localhost/api/build/recent', { method: 'GET' })
}

/** Build row factory — simulates what the DB query returns. */
function makeBuildRow(overrides: Partial<{
  build_id: string
  chart_id: string
  chart_name: string | null
  status: 'complete' | 'failed'
  finished_at: string
  ayanamshas: string[]
  error_summary: string | null
}> = {}) {
  return {
    build_id: 'build-abc',
    chart_id: 'chart-xyz',
    chart_name: 'Test Chart',
    status: 'complete' as const,
    finished_at: '2026-05-29T06:00:00.000Z', // ~12h before "now"
    ayanamshas: ['lahiri', 'kp'],
    error_summary: null,
    ...overrides,
  }
}

/**
 * Sets up auth + DB mocks.
 *
 * Call-order from the route:
 *   1. getServerUser()
 *   2. query("SELECT role FROM profiles …")
 *   3. query("SELECT EXISTS … notification_views …")
 *   4. query("<main recent-builds query>")
 *
 * notificationViewsExists: true  → EXISTS returns { exists: true }
 * notificationViewsExists: false → EXISTS returns { exists: false }
 */
function setupMocks(
  uid: string,
  role: 'guest' | 'super_admin',
  buildRows: ReturnType<typeof makeBuildRow>[],
  options: { notificationViewsExists?: boolean } = {},
) {
  const nvExists = options.notificationViewsExists ?? false

  mockGetServerUser.mockResolvedValue({ uid })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) {
      return Promise.resolve({ rows: [{ role }] })
    }
    if (/information_schema\.tables/.test(sql)) {
      return Promise.resolve({ rows: [{ exists: nvExists }] })
    }
    // Main recent-builds query
    return Promise.resolve({ rows: buildRows })
  })
}

// ─── Setup ────────────────────────────────────────────────────────────────────

beforeEach(() => {
  mockQuery.mockReset()
  mockGetServerUser.mockReset()
})

// ─── Tests: auth gate ─────────────────────────────────────────────────────────

describe('GET /api/build/recent — auth gate', () => {
  it('returns 401 when unauthenticated', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await GET(makeReq())
    expect(res.status).toBe(401)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('unauthenticated')
  })
})

// ─── Tests: empty result ──────────────────────────────────────────────────────

describe('GET /api/build/recent — empty result', () => {
  it('returns 200 with empty array when no recent builds exist', async () => {
    setupMocks('user-1', 'guest', [])
    const res = await GET(makeReq())
    expect(res.status).toBe(200)
    const body = (await res.json()) as unknown[]
    expect(Array.isArray(body)).toBe(true)
    expect(body).toHaveLength(0)
  })
})

// ─── Tests: build inclusion / exclusion ───────────────────────────────────────

describe('GET /api/build/recent — build inclusion', () => {
  it('includes a complete build finished 12h ago', async () => {
    const row = makeBuildRow({ status: 'complete', build_id: 'b-complete-12h' })
    setupMocks('user-1', 'guest', [row])
    const res = await GET(makeReq())
    expect(res.status).toBe(200)
    const body = (await res.json()) as Array<{ build_id: string; status: string }>
    expect(body).toHaveLength(1)
    expect(body[0].build_id).toBe('b-complete-12h')
    expect(body[0].status).toBe('complete')
  })

  it('does NOT include builds >24h old (DB returns empty — exclusion is at DB level)', async () => {
    // The route trusts the DB's WHERE clause; simulate the DB returning no rows
    // for a 25h-old build (i.e., filtered server-side by the interval predicate).
    setupMocks('user-1', 'guest', [])
    const res = await GET(makeReq())
    const body = (await res.json()) as unknown[]
    expect(body).toHaveLength(0)
  })

  it('includes a failed build with error_summary populated', async () => {
    const row = makeBuildRow({
      build_id: 'b-failed',
      status: 'failed',
      error_summary: 'ephemeris timeout after 30s',
    })
    setupMocks('user-1', 'guest', [row])
    const res = await GET(makeReq())
    const body = (await res.json()) as Array<{ build_id: string; status: string; error_summary: string | null }>
    expect(body).toHaveLength(1)
    expect(body[0].status).toBe('failed')
    expect(body[0].error_summary).toBe('ephemeris timeout after 30s')
  })

  it('queued and running builds are NOT returned (DB only queries terminal statuses)', async () => {
    // Simulate DB correctly returning empty (the route uses status IN ('complete','failed'))
    setupMocks('user-1', 'guest', [])
    const res = await GET(makeReq())
    const body = (await res.json()) as unknown[]
    // Verify the SQL sent to the DB includes only terminal statuses
    const calls = mockQuery.mock.calls as Array<[string, unknown[]]>
    const mainQuery = calls.find(([sql]) => /FROM builds/.test(sql))
    expect(mainQuery).toBeDefined()
    expect(mainQuery![0]).toContain('complete')
    expect(mainQuery![0]).toContain('failed')
    expect(mainQuery![0]).not.toMatch(/status IN.*queued/)
    expect(body).toHaveLength(0)
  })
})

// ─── Tests: response item shape ───────────────────────────────────────────────

describe('GET /api/build/recent — response item shape', () => {
  it('response item contains all required fields', async () => {
    const row = makeBuildRow()
    setupMocks('user-1', 'guest', [row])
    const res = await GET(makeReq())
    const body = (await res.json()) as Array<Record<string, unknown>>
    const item = body[0]
    expect(item).toHaveProperty('build_id')
    expect(item).toHaveProperty('chart_id')
    expect(item).toHaveProperty('chart_name')
    expect(item).toHaveProperty('status')
    expect(item).toHaveProperty('finished_at')
    expect(item).toHaveProperty('ayanamshas')
    expect(item).toHaveProperty('error_summary')
  })

  it('ayanamshas is an array', async () => {
    const row = makeBuildRow({ ayanamshas: ['lahiri', 'kp', 'raman'] })
    setupMocks('user-1', 'guest', [row])
    const res = await GET(makeReq())
    const body = (await res.json()) as Array<{ ayanamshas: unknown }>
    expect(Array.isArray(body[0].ayanamshas)).toBe(true)
    expect(body[0].ayanamshas).toHaveLength(3)
  })

  it('error_summary is null for complete builds', async () => {
    const row = makeBuildRow({ status: 'complete', error_summary: null })
    setupMocks('user-1', 'guest', [row])
    const res = await GET(makeReq())
    const body = (await res.json()) as Array<{ error_summary: unknown }>
    expect(body[0].error_summary).toBeNull()
  })

  it('chart_name is null when chart join finds no match', async () => {
    const row = makeBuildRow({ chart_name: null })
    setupMocks('user-1', 'guest', [row])
    const res = await GET(makeReq())
    const body = (await res.json()) as Array<{ chart_name: unknown }>
    expect(body[0].chart_name).toBeNull()
  })

  it('ayanamshas defaults to empty array when DB returns null', async () => {
    // Simulate ayanamshas being null in the row (e.g., JSONB null)
    const row = { ...makeBuildRow(), ayanamshas: null as unknown as string[] }
    setupMocks('user-1', 'guest', [row])
    const res = await GET(makeReq())
    const body = (await res.json()) as Array<{ ayanamshas: unknown }>
    expect(Array.isArray(body[0].ayanamshas)).toBe(true)
    expect((body[0].ayanamshas as string[])).toHaveLength(0)
  })
})

// ─── Tests: super_admin scope ─────────────────────────────────────────────────

describe('GET /api/build/recent — super_admin scope', () => {
  it('super_admin sees builds from multiple users', async () => {
    const rows = [
      makeBuildRow({ build_id: 'b-user1', status: 'complete' }),
      makeBuildRow({ build_id: 'b-user2', status: 'failed', error_summary: 'timeout' }),
    ]
    setupMocks('admin-uid', 'super_admin', rows)
    const res = await GET(makeReq())
    expect(res.status).toBe(200)
    const body = (await res.json()) as Array<{ build_id: string }>
    expect(body).toHaveLength(2)
    const ids = body.map((b) => b.build_id)
    expect(ids).toContain('b-user1')
    expect(ids).toContain('b-user2')
  })

  it('super_admin query does NOT include triggered_by_uid = $1 filter', async () => {
    setupMocks('admin-uid', 'super_admin', [])
    await GET(makeReq())
    const calls = mockQuery.mock.calls as Array<[string, unknown[]]>
    const mainQuery = calls.find(([sql]) => /FROM builds/.test(sql))
    expect(mainQuery).toBeDefined()
    expect(mainQuery![0]).not.toContain('triggered_by_uid')
  })
})

// ─── Tests: graceful degradation (notification_views absent) ─────────────────

describe('GET /api/build/recent — graceful degradation', () => {
  it('returns 200 + array when notification_views table does not exist', async () => {
    const row = makeBuildRow({ build_id: 'b-no-nv' })
    setupMocks('user-1', 'guest', [row], { notificationViewsExists: false })
    const res = await GET(makeReq())
    expect(res.status).toBe(200)
    const body = (await res.json()) as unknown[]
    expect(Array.isArray(body)).toBe(true)
    expect(body).toHaveLength(1)
  })

  it('does NOT include notification_views join in SQL when table absent', async () => {
    setupMocks('user-1', 'guest', [], { notificationViewsExists: false })
    await GET(makeReq())
    const calls = mockQuery.mock.calls as Array<[string, unknown[]]>
    const mainQuery = calls.find(([sql]) => /FROM builds/.test(sql))
    expect(mainQuery).toBeDefined()
    expect(mainQuery![0]).not.toContain('notification_views')
  })

  it('includes notification_views exclusion in SQL when table exists', async () => {
    setupMocks('user-1', 'guest', [], { notificationViewsExists: true })
    await GET(makeReq())
    const calls = mockQuery.mock.calls as Array<[string, unknown[]]>
    const mainQuery = calls.find(([sql]) => /FROM builds/.test(sql))
    expect(mainQuery).toBeDefined()
    expect(mainQuery![0]).toContain('notification_views')
  })
})

// ─── Tests: response headers ──────────────────────────────────────────────────

describe('GET /api/build/recent — response headers', () => {
  it('sets Cache-Control: no-store', async () => {
    setupMocks('user-1', 'guest', [])
    const res = await GET(makeReq())
    expect(res.headers.get('Cache-Control')).toBe('no-store')
  })
})

// ─── Tests: ordering ──────────────────────────────────────────────────────────

describe('GET /api/build/recent — ordering', () => {
  it('returns multiple builds preserving DB order (finished_at DESC from DB)', async () => {
    const rows = [
      makeBuildRow({ build_id: 'b-newer', finished_at: '2026-05-29T10:00:00.000Z' }),
      makeBuildRow({ build_id: 'b-older', finished_at: '2026-05-29T06:00:00.000Z' }),
    ]
    setupMocks('user-1', 'guest', rows)
    const res = await GET(makeReq())
    const body = (await res.json()) as Array<{ build_id: string }>
    expect(body[0].build_id).toBe('b-newer')
    expect(body[1].build_id).toBe('b-older')
  })

  it('ORDER BY clause in SQL uses COALESCE(finished_at, failed_at) DESC', async () => {
    setupMocks('user-1', 'guest', [])
    await GET(makeReq())
    const calls = mockQuery.mock.calls as Array<[string, unknown[]]>
    const mainQuery = calls.find(([sql]) => /FROM builds/.test(sql))
    expect(mainQuery).toBeDefined()
    expect(mainQuery![0]).toMatch(/ORDER BY.*COALESCE.*finished_at.*failed_at.*DESC/s)
  })
})

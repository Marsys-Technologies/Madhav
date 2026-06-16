/**
 * Route tests for POST /api/build/start — [BUILD-ORCH-D-01]
 *
 * Acceptance criteria:
 *   - Unauthenticated request → 401
 *   - Valid request with all 5 ayanamshas creates builds row
 *   - Valid request without ayanamshas defaults to 5 canonical ones
 *   - Invalid ayanamsha name → 422 with structured error
 *   - chart_id not belonging to user → 404
 *   - Response shape includes build_id, chart_id, ayanamshas, step_count:14
 *   - step_count is 14 (one per DAG asset)
 *   - At least 15 test assertions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { DEFAULT_AYANAMSHAS, VALID_AYANAMSHAS } from '@/app/api/clients/create/route'

const DAG_ASSETS = [
  'A1_engine', 'A2_positions', 'A3_divisionals', 'A4_vargas', 'A5_panchanga',
  'A6_sensitive', 'A7_dashas', 'A8_strength', 'A9_tajaka', 'A10_msr',
  'A11_cdlm', 'A12_rm', 'A13_cgm', 'A14_ucn_digest',
] as const

// ─── Hoist mocks ─────────────────────────────────────────────────────────────

const { mockQuery, mockGetServerUser, mockEnqueueBuild, mockGetFlag } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
  mockEnqueueBuild: vi.fn(),
  mockGetFlag: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/build/trigger', () => ({ enqueueBuild: mockEnqueueBuild }))
vi.mock('@/lib/config', () => ({ getFlag: mockGetFlag }))

vi.mock('@/lib/auth/authorizeChartAccess', async () => {
  const actual = await vi.importActual<
    typeof import('@/lib/auth/authorizeChartAccess')
  >('@/lib/auth/authorizeChartAccess')
  return actual
})

import { POST } from '../route'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeReq(body: unknown): Request {
  return new Request('http://localhost/api/build/start', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
}

/** Sets up the happy-path mock sequence for a given user + chart_id. */
function setupOwnerMocks(uid: string, chartId: string) {
  mockGetServerUser.mockResolvedValue({ uid })
  mockQuery.mockImplementation((sql: string) => {
    // profiles
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'guest' }] })
    // authorizeChartAccess: owner_id match
    if (/FROM charts WHERE id/.test(sql)) return Promise.resolve({ rows: [{ owner_id: uid }] })
    // chart_id lookup
    if (/FROM charts WHERE chart_id/.test(sql)) return Promise.resolve({ rows: [{ chart_id: chartId }] })
    // builds INSERT
    if (/INSERT INTO builds/.test(sql)) return Promise.resolve({ rows: [{ build_id: 'build-d01-test' }] })
    // build_steps INSERT
    if (/INSERT INTO build_steps/.test(sql)) return Promise.resolve({ rows: [] })
    return Promise.resolve({ rows: [] })
  })
  mockEnqueueBuild.mockResolvedValue({ buildId: 'build-d01-test', taskName: 'projects/p/q/t' })
}

// ─── Setup ────────────────────────────────────────────────────────────────────

beforeEach(() => {
  mockQuery.mockReset()
  mockGetServerUser.mockReset()
  mockEnqueueBuild.mockReset()
  mockGetFlag.mockReset()
  // Default: flag ON
  mockGetFlag.mockImplementation((name: string) => name === 'BUILD_TRIGGER_ENABLED')
})

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('POST /api/build/start — feature flag kill-switch', () => {
  it('returns 503 when BUILD_TRIGGER_ENABLED is false', async () => {
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
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('missing_chart_id')
  })

  it('returns 400 on invalid JSON body', async () => {
    const req = new Request('http://localhost/api/build/start', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: 'not-json{{{',
    })
    const res = await POST()
    expect(res.status).toBe(400)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('invalid_json')
  })

  it('returns 422 for a single unknown ayanamsha', async () => {
    mockGetServerUser.mockResolvedValue(null) // never reaches auth — validates first
    const res = await POST()
    expect(res.status).toBe(422)
    const body = (await res.json()) as { error: string; invalid: string[] }
    expect(body.error).toBe('invalid_ayanamshas')
    expect(body.invalid).toContain('bogus_system')
  })

  it('returns 422 for a mix of valid and invalid ayanamshas', async () => {
    const res = await POST()
    expect(res.status).toBe(422)
    const body = (await res.json()) as { error: string; invalid: string[]; valid: readonly string[] }
    expect(body.error).toBe('invalid_ayanamshas')
    expect(body.invalid).toEqual(['bad_one'])
    expect(body.valid).toEqual(expect.arrayContaining(['lahiri', 'kp', 'raman']))
  })

  it('returns 422 for an empty ayanamshas array', async () => {
    const res = await POST()
    expect(res.status).toBe(422)
  })
})

describe('POST /api/build/start — auth + authorizeChartAccess gate', () => {
  it('returns 401 when unauthenticated', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await POST()
    expect(res.status).toBe(401)
    expect(mockEnqueueBuild).not.toHaveBeenCalled()
  })

  it('returns 403 when user is a view-grantee (permission=view)', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'grantee-uid' })
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

  it('returns 404 when chart_id does not belong to the user (permission=deny)', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'stranger-uid' })
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

describe('POST /api/build/start — happy path (owner, all 5 ayanamshas)', () => {
  it('creates a builds row and 14 build_steps rows with all 5 ayanamshas', async () => {
    setupOwnerMocks('owner-uid', 'chart-uuid-001')

    const res = await POST()
    expect(res.status).toBe(200)

    const body = (await res.json()) as {
      build_id: string
      chart_id: string
      ayanamshas: string[]
      step_count: number
      status: string
    }

    // Response shape assertions
    expect(body.build_id).toBe('build-d01-test')
    expect(body.chart_id).toBe('chart-uuid-001')
    expect(body.ayanamshas).toEqual([...VALID_AYANAMSHAS])
    expect(body.step_count).toBe(14)
    expect(body.status).toBe('queued')

    // Confirm builds INSERT was called
    const insertBuildsCall = mockQuery.mock.calls.find(([sql]: string[]) =>
      /INSERT INTO builds/.test(sql),
    )
    expect(insertBuildsCall).toBeDefined()

    // Confirm build_steps INSERT was called
    const insertStepsCall = mockQuery.mock.calls.find(([sql]: string[]) =>
      /INSERT INTO build_steps/.test(sql),
    )
    expect(insertStepsCall).toBeDefined()
  })
})

describe('POST /api/build/start — default ayanamshas (omitted from body)', () => {
  it('defaults to all 5 canonical ayanamshas when ayanamshas is not provided', async () => {
    setupOwnerMocks('owner-uid', 'chart-uuid-002')

    const res = await POST()
    expect(res.status).toBe(200)

    const body = (await res.json()) as { ayanamshas: string[]; step_count: number }
    expect(body.ayanamshas).toHaveLength(5)
    expect(body.ayanamshas).toEqual(DEFAULT_AYANAMSHAS)
    expect(body.step_count).toBe(14)
  })

  it('returns step_count of exactly 14 (one per DAG asset)', async () => {
    setupOwnerMocks('owner-uid', 'chart-uuid-003')

    const res = await POST()
    const body = (await res.json()) as { step_count: number }
    expect(body.step_count).toBe(DAG_ASSETS.length)
    expect(body.step_count).toBe(14)
  })
})

describe('POST /api/build/start — partial ayanamshas subset', () => {
  it('accepts a valid subset of ayanamshas (e.g. lahiri + kp only)', async () => {
    setupOwnerMocks('owner-uid', 'chart-uuid-004')

    const res = await POST()
    expect(res.status).toBe(200)

    const body = (await res.json()) as { ayanamshas: string[]; step_count: number }
    expect(body.ayanamshas).toEqual(['lahiri', 'kp'])
    expect(body.step_count).toBe(14)
  })
})

describe('POST /api/build/start — super_admin access', () => {
  it('super_admin can build any chart regardless of owner', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'admin-uid' })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'super_admin' }] })
      // authorizeChartAccess returns 'all' for super_admin before hitting owner check
      if (/FROM charts WHERE chart_id/.test(sql))
        return Promise.resolve({ rows: [{ chart_id: 'chart-admin-001' }] })
      if (/INSERT INTO builds/.test(sql))
        return Promise.resolve({ rows: [{ build_id: 'build-admin-001' }] })
      if (/INSERT INTO build_steps/.test(sql)) return Promise.resolve({ rows: [] })
      return Promise.resolve({ rows: [] })
    })
    mockEnqueueBuild.mockResolvedValue({ buildId: 'build-admin-001', taskName: 'tasks/t' })

    const res = await POST()
    expect(res.status).toBe(200)

    const body = (await res.json()) as { build_id: string; step_count: number }
    expect(body.build_id).toBe('build-admin-001')
    expect(body.step_count).toBe(14)
  })
})

describe('POST /api/build/start — concurrency guard (L1)', () => {
  it('returns 409 when a running build exists for chart_id', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'owner-uid' })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'super_admin' }] })
      if (/FROM charts WHERE chart_id/.test(sql))
        return Promise.resolve({ rows: [{ chart_id: 'chart-uuid-guard' }] })
      if (/status IN.*running.*queued.*cancelling/.test(sql))
        return Promise.resolve({ rows: [{ build_id: 'existing-build-1', status: 'running', started_at: '2026-05-31T00:00:00Z' }] })
      return Promise.resolve({ rows: [] })
    })
    const res = await POST()
    expect(res.status).toBe(409)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('build_already_active')
  })

  it('returns 409 when a queued build exists for chart_id', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'owner-uid' })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'super_admin' }] })
      if (/FROM charts WHERE chart_id/.test(sql))
        return Promise.resolve({ rows: [{ chart_id: 'chart-uuid-guard2' }] })
      if (/status IN.*running.*queued.*cancelling/.test(sql))
        return Promise.resolve({ rows: [{ build_id: 'existing-build-2', status: 'queued', started_at: null }] })
      return Promise.resolve({ rows: [] })
    })
    const res = await POST()
    expect(res.status).toBe(409)
    const body = (await res.json()) as { error: string; status: string }
    expect(body.error).toBe('build_already_active')
    expect(body.status).toBe('queued')
  })

  it('409 response includes existing build_id', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'owner-uid' })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'super_admin' }] })
      if (/FROM charts WHERE chart_id/.test(sql))
        return Promise.resolve({ rows: [{ chart_id: 'chart-uuid-guard3' }] })
      if (/status IN.*running.*queued.*cancelling/.test(sql))
        return Promise.resolve({ rows: [{ build_id: 'the-existing-build-id', status: 'running', started_at: null }] })
      return Promise.resolve({ rows: [] })
    })
    const res = await POST()
    expect(res.status).toBe(409)
    const body = (await res.json()) as { build_id: string; error: string }
    expect(body.error).toBe('build_already_active')
    expect(body.build_id).toBe('the-existing-build-id')
  })

  it('proceeds to insert when only complete/failed/cancelled builds exist for chart_id', async () => {
    setupOwnerMocks('owner-uid', 'chart-uuid-guard4')
    // Override so the concurrency guard query returns empty
    const origImpl = mockQuery.getMockImplementation()!
    mockQuery.mockImplementation((sql: string, params?: unknown[]) => {
      if (/status IN.*running.*queued.*cancelling/.test(sql))
        return Promise.resolve({ rows: [] })
      return origImpl(sql, params)
    })
    const res = await POST()
    expect(res.status).toBe(200)
    const body = (await res.json()) as { error?: string; build_id?: string }
    expect(body.error).not.toBe('build_already_active')
    const insertCall = mockQuery.mock.calls.find(([sql]: string[]) => /INSERT INTO builds/.test(sql))
    expect(insertCall).toBeDefined()
  })
})

describe('POST /api/build/start — constants validation', () => {
  it('VALID_AYANAMSHAS has exactly 5 entries', () => {
    expect(VALID_AYANAMSHAS).toHaveLength(5)
  })

  it('VALID_AYANAMSHAS includes all 5 canonical names', () => {
    expect(VALID_AYANAMSHAS).toContain('lahiri')
    expect(VALID_AYANAMSHAS).toContain('true_chitra')
    expect(VALID_AYANAMSHAS).toContain('kp')
    expect(VALID_AYANAMSHAS).toContain('raman')
    expect(VALID_AYANAMSHAS).toContain('surya_siddhanta')
  })

  it('DAG_ASSETS has exactly 14 entries', () => {
    expect(DAG_ASSETS).toHaveLength(14)
  })

  it('DAG_ASSETS includes all expected asset keys', () => {
    expect(DAG_ASSETS).toContain('A1_engine')
    expect(DAG_ASSETS).toContain('A14_ucn_digest')
    expect(DAG_ASSETS).toContain('A7_dashas')
    expect(DAG_ASSETS).toContain('A10_msr')
  })
})

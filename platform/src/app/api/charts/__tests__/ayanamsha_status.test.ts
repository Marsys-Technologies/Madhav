/**
 * Route tests for GET /api/charts/[id]/ayanamsha-status — [BUILD-ORCH-D-08]
 *
 * Acceptance criteria (≥12 assertions):
 *   - Unauthenticated → 401
 *   - Chart not found (wrong owner) → 404
 *   - Returns array of exactly 5 items
 *   - All 5 canonical ayanamshas represented in correct order
 *   - status='not_built' when no build exists for an ayanamsha
 *   - status='complete' for a built ayanamsha
 *   - is_latest_engine=false when build uses older engine version
 *   - is_latest_engine=true when build matches current engine version
 *   - is_latest_engine=true when engine_versions table is empty
 *   - steps_complete and steps_total are present and numeric
 *   - finished_at falls back to failed_at for failed builds
 *   - super_admin can access charts not owned by them
 *   - display_name is set correctly for each ayanamsha
 *   - latest_build_id is null when status is not_built
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── Hoist mocks ──────────────────────────────────────────────────────────────

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { GET } from '../[id]/ayanamsha-status/route'

// ─── Constants ────────────────────────────────────────────────────────────────

const CANONICAL_ORDER = ['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta']
const DISPLAY_NAMES: Record<string, string> = {
  lahiri: 'Lahiri',
  true_chitra: 'True Chitra',
  kp: 'KP',
  raman: 'B.V. Raman',
  surya_siddhanta: 'Surya Siddhanta',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function makeReq(chartId = 'chart-abc'): Request {
  return new Request(`http://localhost/api/charts/${chartId}/ayanamsha-status`, {
    method: 'GET',
  })
}

function makeParams(chartId = 'chart-abc'): { params: Promise<{ id: string }> } {
  return { params: Promise.resolve({ id: chartId }) }
}

/** Factory for a build row as returned by the per-ayanamsha query. */
function makeBuildRow(overrides: Partial<{
  build_id: string
  status: string
  finished_at: string | null
  failed_at: string | null
  engine_version: string
  ayanamshas: string[]
  steps_complete: number
  steps_total: number
}> = {}) {
  return {
    build_id: 'build-001',
    status: 'complete',
    finished_at: '2026-05-29T10:00:00.000Z',
    failed_at: null,
    engine_version: 'natal_engine/0.2.0',
    ayanamshas: ['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta'],
    steps_complete: 8,
    steps_total: 10,
    ...overrides,
  }
}

/**
 * Wire up all mocks for a typical successful GET.
 *
 * Query call order from the route:
 *   1. SELECT role FROM profiles              → role row
 *   2. SELECT chart_id FROM charts            → chart row (or empty)
 *   3. SELECT version_str FROM engine_versions → version row (or empty)
 *   4-8. Per-ayanamsha build query (×5)       → build row per ayanamsha
 *
 * @param buildRowsByAyanamsha  Map of ayanamsha_id → build row (or null = not_built)
 * @param currentEngineVersion  Version string returned from engine_versions (null = empty table)
 */
function setupMocks(opts: {
  uid?: string
  role?: 'guest' | 'super_admin'
  chartFound?: boolean
  currentEngineVersion?: string | null
  buildRowsByAyanamsha?: Partial<Record<string, ReturnType<typeof makeBuildRow> | null>>
}) {
  const {
    uid = 'user-1',
    role = 'guest',
    chartFound = true,
    currentEngineVersion = 'natal_engine/0.2.0',
    buildRowsByAyanamsha = {},
  } = opts

  mockGetServerUser.mockResolvedValue({ uid })

  let engineCallCount = 0
  let ayanamshaCallIndex = 0

  mockQuery.mockImplementation((sql: string, _params: unknown[]) => {
    // 1. Profile role
    if (/FROM profiles/.test(sql)) {
      return Promise.resolve({ rows: [{ role }] })
    }

    // 2. Chart ownership check
    if (/FROM charts/.test(sql)) {
      return Promise.resolve({
        rows: chartFound ? [{ chart_id: 'chart-abc' }] : [],
      })
    }

    // 3. Engine version lookup
    if (/FROM engine_versions/.test(sql)) {
      engineCallCount++
      if (currentEngineVersion === null) {
        return Promise.resolve({ rows: [] })
      }
      return Promise.resolve({ rows: [{ version_str: currentEngineVersion }] })
    }

    // 4-8. Per-ayanamsha build query (identified by LEFT JOIN build_steps)
    if (/LEFT JOIN build_steps/.test(sql)) {
      const ayanamshaId = CANONICAL_ORDER[ayanamshaCallIndex]
      ayanamshaCallIndex++

      const customRow = buildRowsByAyanamsha[ayanamshaId ?? '']
      // undefined means use default; null means not_built (empty result)
      if (customRow === null) {
        return Promise.resolve({ rows: [] })
      }
      if (customRow !== undefined) {
        return Promise.resolve({ rows: [customRow] })
      }
      // Default: return a generic complete build row
      return Promise.resolve({ rows: [makeBuildRow()] })
    }

    return Promise.resolve({ rows: [] })
  })
}

// ─── Reset ────────────────────────────────────────────────────────────────────

beforeEach(() => {
  mockQuery.mockReset()
  mockGetServerUser.mockReset()
})

// ─── Tests: auth gate ─────────────────────────────────────────────────────────

describe('GET /api/charts/[id]/ayanamsha-status — auth gate', () => {
  it('returns 401 when unauthenticated', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(401)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('unauthenticated')
  })
})

// ─── Tests: chart not found ───────────────────────────────────────────────────

describe('GET /api/charts/[id]/ayanamsha-status — chart ownership', () => {
  it('returns 404 when chart does not belong to authenticated user', async () => {
    setupMocks({ uid: 'user-1', role: 'guest', chartFound: false })
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(404)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('not_found')
  })

  it('super_admin can access a chart not owned by them', async () => {
    setupMocks({ uid: 'admin-uid', role: 'super_admin', chartFound: true })
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(200)
  })
})

// ─── Tests: array shape ───────────────────────────────────────────────────────

describe('GET /api/charts/[id]/ayanamsha-status — array shape', () => {
  it('returns exactly 5 items', async () => {
    setupMocks({})
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(200)
    const body = (await res.json()) as unknown[]
    expect(Array.isArray(body)).toBe(true)
    expect(body).toHaveLength(5)
  })

  it('all 5 canonical ayanamshas are represented', async () => {
    setupMocks({})
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{ ayanamsha_id: string }>
    const ids = body.map((item) => item.ayanamsha_id)
    for (const canonical of CANONICAL_ORDER) {
      expect(ids).toContain(canonical)
    }
  })

  it('items are sorted in canonical order (lahiri, true_chitra, kp, raman, surya_siddhanta)', async () => {
    setupMocks({})
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{ ayanamsha_id: string }>
    const ids = body.map((item) => item.ayanamsha_id)
    expect(ids).toEqual(CANONICAL_ORDER)
  })

  it('each item has the correct display_name', async () => {
    setupMocks({})
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{ ayanamsha_id: string; display_name: string }>
    for (const item of body) {
      expect(item.display_name).toBe(DISPLAY_NAMES[item.ayanamsha_id])
    }
  })
})

// ─── Tests: not_built status ──────────────────────────────────────────────────

describe('GET /api/charts/[id]/ayanamsha-status — not_built', () => {
  it('status=not_built when no build exists for an ayanamsha', async () => {
    // kp has no build
    setupMocks({
      buildRowsByAyanamsha: { kp: null },
    })
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{ ayanamsha_id: string; status: string }>
    const kpItem = body.find((item) => item.ayanamsha_id === 'kp')
    expect(kpItem).toBeDefined()
    expect(kpItem!.status).toBe('not_built')
  })

  it('latest_build_id is null when status is not_built', async () => {
    setupMocks({ buildRowsByAyanamsha: { raman: null } })
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{ ayanamsha_id: string; latest_build_id: string | null }>
    const ramanItem = body.find((item) => item.ayanamsha_id === 'raman')
    expect(ramanItem!.latest_build_id).toBeNull()
  })

  it('steps_complete and steps_total are 0 when status is not_built', async () => {
    setupMocks({ buildRowsByAyanamsha: { surya_siddhanta: null } })
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{
      ayanamsha_id: string
      steps_complete: number
      steps_total: number
    }>
    const item = body.find((i) => i.ayanamsha_id === 'surya_siddhanta')
    expect(item!.steps_complete).toBe(0)
    expect(item!.steps_total).toBe(0)
  })
})

// ─── Tests: complete status ───────────────────────────────────────────────────

describe('GET /api/charts/[id]/ayanamsha-status — complete status', () => {
  it('status=complete and latest_build_id populated for a built ayanamsha', async () => {
    setupMocks({
      buildRowsByAyanamsha: {
        lahiri: makeBuildRow({ build_id: 'b-lahiri', status: 'complete' }),
      },
    })
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{
      ayanamsha_id: string
      status: string
      latest_build_id: string | null
    }>
    const lahiriItem = body.find((item) => item.ayanamsha_id === 'lahiri')
    expect(lahiriItem!.status).toBe('complete')
    expect(lahiriItem!.latest_build_id).toBe('b-lahiri')
  })

  it('steps_complete and steps_total are numeric', async () => {
    setupMocks({
      buildRowsByAyanamsha: {
        lahiri: makeBuildRow({ steps_complete: 12, steps_total: 15 }),
      },
    })
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{
      ayanamsha_id: string
      steps_complete: unknown
      steps_total: unknown
    }>
    const item = body.find((i) => i.ayanamsha_id === 'lahiri')
    expect(typeof item!.steps_complete).toBe('number')
    expect(typeof item!.steps_total).toBe('number')
    expect(item!.steps_complete).toBe(12)
    expect(item!.steps_total).toBe(15)
  })
})

// ─── Tests: is_latest_engine ──────────────────────────────────────────────────

describe('GET /api/charts/[id]/ayanamsha-status — is_latest_engine', () => {
  it('is_latest_engine=false when build uses an older engine version', async () => {
    setupMocks({
      currentEngineVersion: 'natal_engine/0.3.0',
      buildRowsByAyanamsha: {
        lahiri: makeBuildRow({ engine_version: 'natal_engine/0.2.0' }),
      },
    })
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{ ayanamsha_id: string; is_latest_engine: boolean }>
    const item = body.find((i) => i.ayanamsha_id === 'lahiri')
    expect(item!.is_latest_engine).toBe(false)
  })

  it('is_latest_engine=true when build matches the current engine version', async () => {
    const version = 'natal_engine/0.2.0'
    setupMocks({
      currentEngineVersion: version,
      buildRowsByAyanamsha: {
        lahiri: makeBuildRow({ engine_version: version }),
      },
    })
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{ ayanamsha_id: string; is_latest_engine: boolean }>
    const item = body.find((i) => i.ayanamsha_id === 'lahiri')
    expect(item!.is_latest_engine).toBe(true)
  })

  it('is_latest_engine=true (defaults to current) when engine_versions table is empty', async () => {
    setupMocks({
      currentEngineVersion: null, // table returns no rows
      buildRowsByAyanamsha: {
        lahiri: makeBuildRow({ engine_version: 'natal_engine/0.1.0' }),
      },
    })
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{ ayanamsha_id: string; is_latest_engine: boolean }>
    const item = body.find((i) => i.ayanamsha_id === 'lahiri')
    expect(item!.is_latest_engine).toBe(true)
  })
})

// ─── Tests: finished_at fallback ──────────────────────────────────────────────

describe('GET /api/charts/[id]/ayanamsha-status — finished_at fallback', () => {
  it('finished_at falls back to failed_at for failed builds', async () => {
    setupMocks({
      buildRowsByAyanamsha: {
        lahiri: makeBuildRow({
          status: 'failed',
          finished_at: null,
          failed_at: '2026-05-29T08:00:00.000Z',
        }),
      },
    })
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{
      ayanamsha_id: string
      status: string
      finished_at: string | null
    }>
    const item = body.find((i) => i.ayanamsha_id === 'lahiri')
    expect(item!.status).toBe('failed')
    expect(item!.finished_at).toBe('2026-05-29T08:00:00.000Z')
  })

  it('finished_at is null when both finished_at and failed_at are null', async () => {
    setupMocks({
      buildRowsByAyanamsha: {
        lahiri: makeBuildRow({ status: 'running', finished_at: null, failed_at: null }),
      },
    })
    const res = await GET(makeReq(), makeParams())
    const body = (await res.json()) as Array<{
      ayanamsha_id: string
      finished_at: string | null
    }>
    const item = body.find((i) => i.ayanamsha_id === 'lahiri')
    expect(item!.finished_at).toBeNull()
  })
})

// ─── Tests: response headers ──────────────────────────────────────────────────

describe('GET /api/charts/[id]/ayanamsha-status — response headers', () => {
  it('sets Cache-Control: max-age=10', async () => {
    setupMocks({})
    const res = await GET(makeReq(), makeParams())
    expect(res.headers.get('Cache-Control')).toBe('max-age=10')
  })
})

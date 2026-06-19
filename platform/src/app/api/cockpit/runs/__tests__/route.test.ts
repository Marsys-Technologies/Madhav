/**
 * Security boundary tests for POST /api/cockpit/runs
 *
 * Verifies the L0 authorization model:
 *   - super_admin can build L0 at scope='global'
 *   - scope='asset' + global asset rejected for everyone (L0 is singleton)
 *   - non-super-admin cannot build brahmagyan layer
 *   - client build global silently excludes L0/global assets (NO error message)
 *   - client build layer/ganita allowed; plan contains zero L0/global assets
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

// ─── module-level mocks (must precede route import) ───────────────────────────

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const mockGetServerUser = vi.fn()
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

const mockInvokeRunJob = vi.fn()
vi.mock('@/lib/build/jobInvoker', () => ({ invokeRunJob: mockInvokeRunJob }))

// ─── fixtures ─────────────────────────────────────────────────────────────────

const USER = { uid: 'user-123' }

const REGISTRY_WITH_L0 = [
  { asset_id: 'bg_ephemeris', layer: 'brahmagyan', scope: 'global',    depends_on: [], estimated_seconds: 60 },
  { asset_id: 'bg_ontology',  layer: 'brahmagyan', scope: 'global',    depends_on: [], estimated_seconds: 60 },
  { asset_id: 'ga_positions', layer: 'ganita',     scope: 'per_chart', depends_on: [], estimated_seconds: 30 },
  { asset_id: 'ga_strength',  layer: 'ganita',     scope: 'per_chart', depends_on: ['ga_positions'], estimated_seconds: 30 },
]

const REGISTRY_GANITA_ONLY = REGISTRY_WITH_L0.filter(r => r.scope === 'per_chart')

function makeReq(body: object): NextRequest {
  return new NextRequest('http://localhost/api/cockpit/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

/** Seed: user authenticated with given role */
function seedRole(role: string) {
  mockGetServerUser.mockResolvedValue(USER)
  mockQuery.mockResolvedValueOnce({ rows: [{ role }], rowCount: 1 }) // getUserRole
}

/** Seed: no active run, registry rows, empty throughput, successful insert */
function seedSuccessfulBuild(registryRows: typeof REGISTRY_WITH_L0) {
  mockQuery
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 409 gate — no active run
    .mockResolvedValueOnce({ rows: registryRows, rowCount: registryRows.length }) // asset_registry
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // asset_throughput (all dormant)
    .mockResolvedValue({ rows: [{ id: 'run-abc' }], rowCount: 1 }) // INSERT build_runs + assets
  mockInvokeRunJob.mockResolvedValue(undefined)
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ─── 1. Unauthenticated ───────────────────────────────────────────────────────

describe('POST /api/cockpit/runs — auth gate', () => {
  it('returns 403 when not authenticated', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', action: 'build' }))
    expect(res.status).toBe(403)
    expect(mockQuery).not.toHaveBeenCalled()
  })
})

// ─── 2. super_admin CAN build L0 at scope='global' ───────────────────────────

describe('POST /api/cockpit/runs — super_admin global build', () => {
  it('creates build_run with L0 assets in plan when super_admin + scope=global', async () => {
    seedRole('super_admin')
    seedSuccessfulBuild(REGISTRY_WITH_L0)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', scope_target: null, action: 'build' }))
    expect(res.status).toBe(201)
    const body = await res.json()
    // Plan must include L0 assets (bg_ephemeris, bg_ontology)
    expect(body.data.plan).toContain('bg_ephemeris')
    expect(body.data.plan).toContain('bg_ontology')
    expect(body.data.plan).toContain('ga_positions')
  })
})

// ─── 3. scope='asset' + global asset → rejected for everyone ─────────────────

describe('POST /api/cockpit/runs — scope=asset + global asset', () => {
  it('rejects super_admin trying to build a global asset at scope=asset', async () => {
    seedRole('super_admin')
    // getUserRole consumed above; next query is asset scope lookup
    mockQuery.mockResolvedValueOnce({ rows: [{ scope: 'global' }], rowCount: 1 })

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'asset', scope_target: 'bg_ephemeris', action: 'rebuild' }))
    expect(res.status).toBe(403)
    const body = await res.json()
    expect(body.code).toBe('FORBIDDEN_L0')
  })

  it('rejects client trying to build a global asset at scope=asset', async () => {
    seedRole('client')
    mockQuery.mockResolvedValueOnce({ rows: [{ scope: 'global' }], rowCount: 1 })

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'asset', scope_target: 'bg_ephemeris', action: 'rebuild' }))
    expect(res.status).toBe(403)
    const body = await res.json()
    expect(body.code).toBe('FORBIDDEN_L0')
  })
})

// ─── 4. non-super-admin cannot build brahmagyan layer ────────────────────────

describe('POST /api/cockpit/runs — client + scope=layer/brahmagyan', () => {
  it('returns 403 FORBIDDEN_L0 for client building brahmagyan layer', async () => {
    seedRole('client')

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'brahmagyan', action: 'build' }))
    expect(res.status).toBe(403)
    const body = await res.json()
    expect(body.code).toBe('FORBIDDEN_L0')
  })

  it('returns 403 FORBIDDEN_L0 for a non-super-admin rebuilding brahmagyan layer', async () => {
    seedRole('client')

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'brahmagyan', action: 'rebuild' }))
    expect(res.status).toBe(403)
    const body = await res.json()
    expect(body.code).toBe('FORBIDDEN_L0')
  })
})

// ─── 5. client build layer/ganita → allowed, plan = per_chart only ────────────

describe('POST /api/cockpit/runs — client + scope=layer/ganita', () => {
  it('allows client to build ganita layer; plan contains only per_chart assets', async () => {
    seedRole('client')
    // For layer/ganita, no asset scope lookup, jump straight to 409 gate + registry
    seedSuccessfulBuild(REGISTRY_WITH_L0)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'ganita', action: 'build' }))
    expect(res.status).toBe(201)
    const body = await res.json()
    // L0 assets must NOT appear in the plan
    expect(body.data.plan).not.toContain('bg_ephemeris')
    expect(body.data.plan).not.toContain('bg_ontology')
    // Ganita assets must appear
    expect(body.data.plan).toContain('ga_positions')
  })
})

// ─── 6. client build global → plan silently excludes L0 (NO error message) ───

describe('POST /api/cockpit/runs — client + scope=global (silent L0 drop)', () => {
  it('returns 201 with plan containing ONLY per_chart assets — no L0, no error', async () => {
    seedRole('client')
    seedSuccessfulBuild(REGISTRY_WITH_L0)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', scope_target: null, action: 'build' }))
    expect(res.status).toBe(201)
    const body = await res.json()
    // L0/global assets silently dropped — not in plan, no error key in response
    expect(body.data.plan).not.toContain('bg_ephemeris')
    expect(body.data.plan).not.toContain('bg_ontology')
    expect(body.data.plan).toContain('ga_positions')
    expect(body.data.plan).toContain('ga_strength')
    expect(body.error).toBeUndefined()
  })

  it('plan asset_count equals per_chart assets only', async () => {
    seedRole('client')
    seedSuccessfulBuild(REGISTRY_WITH_L0)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', scope_target: null, action: 'build' }))
    const body = await res.json()
    // Only 2 per_chart assets (ga_positions, ga_strength) — L0 silently excluded
    expect(body.data.asset_count).toBe(2)
  })
})

// ─── 7. client per_chart L1 build — scope=asset + per_chart asset ─────────────

describe('POST /api/cockpit/runs — client + scope=asset + per_chart asset', () => {
  it('allows client to build a per_chart asset by asset scope', async () => {
    seedRole('client')
    // Asset scope lookup returns per_chart
    mockQuery.mockResolvedValueOnce({ rows: [{ scope: 'per_chart' }], rowCount: 1 })
    // Proceed with successful build
    seedSuccessfulBuild(REGISTRY_GANITA_ONLY)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'asset', scope_target: 'ga_positions', action: 'rebuild' }))
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.data.plan).toContain('ga_positions')
    expect(body.data.plan).not.toContain('bg_ephemeris')
  })
})

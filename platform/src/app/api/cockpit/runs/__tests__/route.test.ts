/**
 * Security boundary tests for POST /api/cockpit/runs
 *
 * Verifies the L0 authorization model:
 *   - super_admin can build L0 at scope='global'
 *   - scope='asset' + global asset rejected for everyone (L0 is singleton)
 *   - non-super-admin cannot build brahmagyan layer
 *   - client build global silently excludes L0/global assets (NO error message)
 *   - client build layer/ganita allowed; plan contains zero L0/global assets
 *
 * Also covers SHAD-DARSHANA sweep-protection Phase 1a, Layer 1/2 — the
 * build_protected_assets planner guard (see "sweep-protection" describe block below).
 * Every seed helper queues a THIRD query result (after asset_registry, asset_throughput)
 * for the route's `SELECT asset_id FROM build_protected_assets WHERE chart_id=$1` call,
 * added to the same Promise.all as the registry/throughput queries.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'
import writerDigestInventory from '@/generated/nirmana-writer-digests.json'

// ─── module-level mocks (must precede route import) ───────────────────────────

const mockQuery = vi.fn()

// Pool client mock: BEGIN/COMMIT/ROLLBACK are swallowed (no mockQuery slot consumed);
// all data queries (SELECT, INSERT, etc.) are routed through mockQuery so the existing
// mockResolvedValueOnce chains work unchanged. Required by M-14 (TOCTOU SERIALIZABLE gate)
// and the atomic clear-before-build INSERT transaction, both of which use getPool().connect().
const _TRANSACTION_RE = /^\s*(BEGIN|COMMIT|ROLLBACK)/i
const mockPoolClientQuery = vi.fn((sql: string, ...rest: unknown[]) => {
  if (_TRANSACTION_RE.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
  return mockQuery(sql, ...rest)
})
const mockPoolClient = { query: mockPoolClientQuery, release: vi.fn() }
const mockPool = { connect: vi.fn().mockResolvedValue(mockPoolClient) }
const mockGetPool = vi.fn().mockResolvedValue(mockPool)

vi.mock('@/lib/db/client', () => ({ query: mockQuery, getPool: mockGetPool }))

const mockGetServerUser = vi.fn()
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

const mockInvokeRunJob = vi.fn()
vi.mock('@/lib/build/jobInvoker', () => ({ invokeRunJob: mockInvokeRunJob }))

// GCP SDK must be mocked to prevent GoogleAuth from trying to load credentials in CI.
vi.mock('@/lib/cloud_run/jobs', () => ({ getJobImageTag: vi.fn().mockResolvedValue(null) }))

// ─── fixtures ─────────────────────────────────────────────────────────────────

const USER = { uid: 'user-123' }

const REGISTRY_WITH_L0 = [
  { asset_id: 'bg_ephemeris', layer: 'brahmagyan', scope: 'global',    depends_on: [], estimated_seconds: 60 },
  { asset_id: 'bg_ontology',  layer: 'brahmagyan', scope: 'global',    depends_on: [], estimated_seconds: 60 },
  { asset_id: 'ga_positions', layer: 'ganita',     scope: 'per_chart', depends_on: [], estimated_seconds: 30 },
  { asset_id: 'ga_strength',  layer: 'ganita',     scope: 'per_chart', depends_on: ['ga_positions'], estimated_seconds: 30 },
]

const REGISTRY_GANITA_ONLY = REGISTRY_WITH_L0.filter(r => r.scope === 'per_chart')

const REGISTRY_EPHEMERIS_SERVICE = [{
  asset_id: 'bg_ephemeris_engine', layer: 'brahmagyan', scope: 'global', depends_on: [], estimated_seconds: 30,
  has_writer: false, asset_kind: 'service', asset_type: 'service', health_probe: { probe_type: 'ephemeris_engine' },
}]

const REGISTRY_PANCHANGA_SERVICE = [{
  asset_id: 'bg_panchanga', layer: 'brahmagyan', scope: 'global', depends_on: [], estimated_seconds: 30,
  has_writer: false, asset_kind: 'service', asset_type: 'service', health_probe: { probe_type: 'panchanga_engine' },
}]

const REGISTRY_UNTRUSTED_NO_WRITER_SERVICE = [{
  asset_id: 'bg_untrusted_no_writer_service', layer: 'brahmagyan', scope: 'global', depends_on: [], estimated_seconds: 30,
  has_writer: false, asset_kind: 'service', asset_type: 'service', health_probe: { probe_type: 'untrusted' },
}]

// The registry must retain bg_panchanga as a dependency identity for ga_panchanga,
// while the route must never select it in an ordinary build plan.
const REGISTRY_PANCHANGA_DEPENDENT = [
  { asset_id: 'ga_panchanga', layer: 'ganita', scope: 'per_chart', depends_on: ['bg_panchanga'], estimated_seconds: 30 },
  ...REGISTRY_PANCHANGA_SERVICE,
]

// Bodha registry: includes bo_* assets for G4 precondition gate tests
const REGISTRY_BODHA = [
  { asset_id: 'ga_structural', layer: 'ganita', scope: 'per_chart', depends_on: [],              estimated_seconds: 30 },
  { asset_id: 'bo_laksana',    layer: 'bodha',  scope: 'per_chart', depends_on: [],              estimated_seconds: 60 },
  { asset_id: 'bo_bimba',      layer: 'bodha',  scope: 'per_chart', depends_on: ['bo_laksana'],  estimated_seconds: 60 },
  { asset_id: 'bo_pramana_mapa', layer: 'bodha', scope: 'per_chart', depends_on: ['bo_bimba'],   estimated_seconds: 30 },
]

// Global/full registry: L1 Gaṇita builders AND L2 Bodha assets in one plan. A global
// rebuild builds L1 before L2 (DAG order), so the L1 preconditions are satisfied in-plan.
const REGISTRY_GLOBAL_FULL = [
  { asset_id: 'ga_positions',  layer: 'ganita', scope: 'per_chart', depends_on: [],               estimated_seconds: 30 },
  { asset_id: 'ga_structural', layer: 'ganita', scope: 'per_chart', depends_on: ['ga_positions'], estimated_seconds: 30 },
  { asset_id: 'bo_laksana',    layer: 'bodha',  scope: 'per_chart', depends_on: ['ga_structural'], estimated_seconds: 60 },
]

// No protected assets for this chart — the common case every existing test exercises.
const NO_PROTECTED_ASSETS = { rows: [], rowCount: 0 }
const NO_FRESHNESS = { rows: [], rowCount: 0 }

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
  // P2-B-008: the route now gates on authorizeChartAccess before any other work.
  // USER owns chart 'c1', so Rule 2 (owner_id match) returns 'all' on this single
  // query and chart_grants is never consulted — one extra queued response, no more.
  // (For role='super_admin' this same row satisfies Rule 1's chart-exists probe.)
  mockQuery.mockResolvedValueOnce({ rows: [{ owner_id: USER.uid }], rowCount: 1 }) // SELECT owner_id FROM charts
}

/**
 * Seed: no active run, registry rows, empty throughput, no protected assets,
 * successful insert.
 */
function seedSuccessfulBuild(registryRows: typeof REGISTRY_WITH_L0) {
  mockQuery
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // 409 gate — no active run
    .mockResolvedValueOnce({ rows: registryRows, rowCount: registryRows.length }) // asset_registry
    .mockResolvedValueOnce({ rows: [], rowCount: 0 }) // asset_throughput (all dormant)
    .mockResolvedValueOnce(NO_PROTECTED_ASSETS) // build_protected_assets — none
    .mockResolvedValueOnce(NO_FRESHNESS) // asset_freshness — no prior receipts
    .mockResolvedValue({ rows: [{ id: 'run-abc' }], rowCount: 1 }) // INSERT build_runs + assets
  mockInvokeRunJob.mockResolvedValue(undefined)
}

function freshnessRow(assetId: string, state: 'fresh' | 'stale') {
  const writerDigests = writerDigestInventory.writers as Record<string, string>
  return {
    asset_id: assetId,
    state,
    reasons: state === 'fresh' ? [] : ['probe receipt is stale'],
    code_digest: assetId === 'bg_panchanga' ? writerDigestInventory.probe_digest : writerDigests[assetId],
  }
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

// ─── 2. super_admin global build excludes L0 (native ruling 2026-06-26) ──────
// L0 is NEVER included in global scope for ANY role.
// super_admin triggers L0 only via scope='layer'/brahmagyan or scope='asset'/bg_*.

describe('POST /api/cockpit/runs — super_admin global build', () => {
  it('creates build_run WITHOUT L0 assets when super_admin + scope=global (native ruling)', async () => {
    seedRole('super_admin')
    seedSuccessfulBuild(REGISTRY_WITH_L0)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', scope_target: null, action: 'build' }))
    expect(res.status).toBe(201)
    const body = await res.json()
    // L0 assets must NOT be in the global plan (excluded for all roles)
    expect(body.data.plan).not.toContain('bg_ephemeris')
    expect(body.data.plan).not.toContain('bg_ontology')
    // Per-chart L1+ assets are included as usual
    expect(body.data.plan).toContain('ga_positions')
  })

  it('does not include either no-writer service probe in a broad global build', async () => {
    seedRole('super_admin')
    seedSuccessfulBuild([
      ...REGISTRY_WITH_L0,
      ...REGISTRY_EPHEMERIS_SERVICE,
      ...REGISTRY_PANCHANGA_SERVICE,
      ...REGISTRY_UNTRUSTED_NO_WRITER_SERVICE,
    ] as typeof REGISTRY_WITH_L0)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', scope_target: null, action: 'build' }))
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.data.plan).not.toContain('bg_ephemeris_engine')
    expect(body.data.plan).not.toContain('bg_panchanga')
    expect(body.data.plan).not.toContain('bg_untrusted_no_writer_service')
  })

  it('persists the ordered waves and registry dependency snapshot with the run', async () => {
    seedRole('super_admin')
    seedSuccessfulBuild(REGISTRY_WITH_L0)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', scope_target: null, action: 'build' }))
    expect(res.status).toBe(201)

    const insert = mockQuery.mock.calls.find(([sql]) => String(sql).includes('INSERT INTO build_runs'))
    expect(insert).toBeDefined()
    const params = insert![1] as unknown[]
    expect(JSON.parse(params[5] as string)).toEqual({
      version: 'nirmana-run-manifest/v1',
      chart_id: 'c1',
      scope: 'global',
      scope_target: null,
      action: 'build',
      waves: [['ga_positions'], ['ga_strength']],
      assets: [
        { asset_id: 'ga_positions', scope: 'per_chart', depends_on: [], natural_key_partition: null, has_cowriters: false, expected_code_digest: (writerDigestInventory.writers as Record<string, string>).ga_positions },
        { asset_id: 'ga_strength', scope: 'per_chart', depends_on: ['ga_positions'], natural_key_partition: null, has_cowriters: false, expected_code_digest: (writerDigestInventory.writers as Record<string, string>).ga_strength },
      ],
    })
    expect(params[6]).toMatch(/^[a-f0-9]{64}$/)
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

  it('maps the durable one-active-run constraint to 409 under a concurrent insert race', async () => {
    seedRole('client')
    const conflict = Object.assign(new Error('duplicate active run'), {
      code: '23505', constraint: 'build_runs_one_active_per_chart_idx',
    })
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: REGISTRY_GANITA_ONLY, rowCount: REGISTRY_GANITA_ONLY.length })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce(NO_PROTECTED_ASSETS)
      .mockResolvedValueOnce(NO_FRESHNESS)
      .mockRejectedValueOnce(conflict)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'ganita', action: 'build' }))

    expect(res.status).toBe(409)
    expect((await res.json()).code).toBe('RUN_ACTIVE')
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
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

// ─── G4: L1/L0 precondition gate — Bodha builds verify upstream before creating run ─

/**
 * Query order for a Bodha layer rebuild:
 *   1. getUserRole
 *   2. 409 gate (no active run)
 *   3. asset_registry
 *   4. asset_throughput
 *   5. build_protected_assets (sweep-protection guard — none, for these tests)
 *   6-8. Promise.all: chart_facts count · ga_structural state · remedy_corpus count
 *   9. INSERT build_runs RETURNING id
 *   10+. INSERT build_run_assets (per asset)
 */

describe('G4 — Bodha build precondition gate', () => {
  function seedBodhaBuildWithPreconditions(
    chartFactsCount: number,
    gaStructuralState: string | null,
    remedyCorpusCount: number,
  ) {
    // All assets dormant (so rebuild plan includes them all)
    const throughput: { asset_id: string; state: string }[] = []

    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                    // 409 gate
      .mockResolvedValueOnce({ rows: REGISTRY_BODHA, rowCount: REGISTRY_BODHA.length })   // asset_registry
      .mockResolvedValueOnce({ rows: throughput, rowCount: 0 })                            // asset_throughput
      .mockResolvedValueOnce(NO_PROTECTED_ASSETS)                                          // build_protected_assets
      .mockResolvedValueOnce(NO_FRESHNESS)                                                  // asset_freshness
      // Promise.all x3 preconditions (order matches Promise.all array in route.ts)
      .mockResolvedValueOnce({ rows: [{ count: String(chartFactsCount) }], rowCount: 1 }) // chart_facts count
      .mockResolvedValueOnce({ rows: gaStructuralState ? [{ state: gaStructuralState }] : [], rowCount: gaStructuralState ? 1 : 0 }) // ga_structural
      .mockResolvedValueOnce({ rows: [{ count: String(remedyCorpusCount) }], rowCount: 1 }) // remedy_corpus count
      .mockResolvedValue({ rows: [{ id: 'run-bo-001' }], rowCount: 1 })                   // INSERT build_runs + assets
    mockInvokeRunJob.mockResolvedValue(undefined)
  }

  it('RED — chart_facts empty: returns 422 PRECONDITION_FAILED (was 201 before guard)', async () => {
    seedRole('super_admin')
    seedBodhaBuildWithPreconditions(0, 'lit', 500)  // chart_facts=0 → precondition fails

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'bodha', action: 'rebuild' }))
    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.code).toBe('PRECONDITION_FAILED')
    expect(body.missing).toEqual(expect.arrayContaining([expect.stringContaining('chart_facts is empty')]))
  })

  it('RED — ga_structural not lit: returns 422 PRECONDITION_FAILED', async () => {
    seedRole('super_admin')
    seedBodhaBuildWithPreconditions(27000, null, 500)  // ga_structural missing → precondition fails

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'bodha', action: 'rebuild' }))
    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.code).toBe('PRECONDITION_FAILED')
    expect(body.missing).toEqual(expect.arrayContaining([expect.stringContaining('ga_structural is not lit')]))
  })

  it('RED — remedy corpus empty: returns 422 PRECONDITION_FAILED', async () => {
    seedRole('super_admin')
    seedBodhaBuildWithPreconditions(27000, 'lit', 0)  // remedy_corpus=0 → precondition fails

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'bodha', action: 'rebuild' }))
    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.code).toBe('PRECONDITION_FAILED')
    expect(body.missing).toEqual(expect.arrayContaining([expect.stringContaining('brahma_remedy_corpus is empty')]))
  })

  it('GREEN — all preconditions met: returns 201 and creates build_run', async () => {
    seedRole('super_admin')
    seedBodhaBuildWithPreconditions(27554, 'lit', 500)  // all OK

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'bodha', action: 'rebuild' }))
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.data.plan).toContain('bo_laksana')
    expect(body.data.plan).toContain('bo_pramana_mapa')
    expect(body.code).toBeUndefined()
  })

  it('GREEN — multiple failures reported together in missing array', async () => {
    seedRole('super_admin')
    seedBodhaBuildWithPreconditions(0, null, 0)  // all 3 fail

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'bodha', action: 'rebuild' }))
    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.code).toBe('PRECONDITION_FAILED')
    expect(body.missing).toHaveLength(3)
  })

  it('GREEN — global rebuild from empty L1: L1 preconditions satisfied IN-PLAN, build proceeds', async () => {
    // The plan includes ga_positions + ga_structural ahead of bo_laksana, so chart_facts being
    // empty and ga_structural not-yet-lit must NOT block — L1 builds first. Only L0 (remedy_corpus)
    // is a true external precondition, and it is present here. Regression for the global-rebuild
    // 422 where the gate fired against L1 the same plan was about to build.
    seedRole('super_admin')
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                              // 409 gate
      .mockResolvedValueOnce({ rows: REGISTRY_GLOBAL_FULL, rowCount: REGISTRY_GLOBAL_FULL.length })  // asset_registry
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                              // asset_throughput (all dormant)
      .mockResolvedValueOnce(NO_PROTECTED_ASSETS)                                                    // build_protected_assets
      .mockResolvedValueOnce(NO_FRESHNESS)                                                            // asset_freshness
      .mockResolvedValueOnce({ rows: [{ count: '0' }], rowCount: 1 })                                // chart_facts = 0 (empty)
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                              // ga_structural not lit
      .mockResolvedValueOnce({ rows: [{ count: '500' }], rowCount: 1 })                              // remedy_corpus present
      .mockResolvedValue({ rows: [{ id: 'run-global-001' }], rowCount: 1 })                          // INSERT build_runs + assets
    mockInvokeRunJob.mockResolvedValue(undefined)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', action: 'build' }))
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.code).toBeUndefined()
    expect(body.data.plan).toContain('ga_positions')
    expect(body.data.plan).toContain('bo_laksana')
  })

  it('RED — global plan still blocks when L0 remedy_corpus is empty', async () => {
    // Even with L1 in-plan, a missing L0 prerequisite (remedy_corpus) must still block.
    seedRole('super_admin')
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                              // 409 gate
      .mockResolvedValueOnce({ rows: REGISTRY_GLOBAL_FULL, rowCount: REGISTRY_GLOBAL_FULL.length })  // asset_registry
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                              // asset_throughput
      .mockResolvedValueOnce(NO_PROTECTED_ASSETS)                                                    // build_protected_assets
      .mockResolvedValueOnce(NO_FRESHNESS)                                                            // asset_freshness
      .mockResolvedValueOnce({ rows: [{ count: '0' }], rowCount: 1 })                                // chart_facts = 0
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                              // ga_structural not lit
      .mockResolvedValueOnce({ rows: [{ count: '0' }], rowCount: 1 })                                // remedy_corpus EMPTY
      .mockResolvedValue({ rows: [{ id: 'run-x' }], rowCount: 1 })
    mockInvokeRunJob.mockResolvedValue(undefined)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', action: 'build' }))
    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.code).toBe('PRECONDITION_FAILED')
    expect(body.missing).toEqual(expect.arrayContaining([expect.stringContaining('brahma_remedy_corpus is empty')]))
    // L1 preconditions must NOT be listed — they are satisfied in-plan
    expect(body.missing.some((m: string) => m.includes('chart_facts'))).toBe(false)
  })

  it('GREEN — non-Bodha plan skips precondition gate entirely', async () => {
    // A ganita-only plan must never trigger the Bodha precondition queries
    seedRole('super_admin')
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                       // 409 gate
      .mockResolvedValueOnce({ rows: REGISTRY_GANITA_ONLY, rowCount: REGISTRY_GANITA_ONLY.length }) // registry
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                       // throughput
      .mockResolvedValueOnce(NO_PROTECTED_ASSETS)                                              // build_protected_assets
      .mockResolvedValueOnce(NO_FRESHNESS)                                                      // asset_freshness
      .mockResolvedValue({ rows: [{ id: 'run-ga-001' }], rowCount: 1 })                      // INSERT
    mockInvokeRunJob.mockResolvedValue(undefined)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'ganita', action: 'rebuild' }))
    expect(res.status).toBe(201)
    // Confirm only 4 queries (role + 409 + registry + throughput + insert chain); no precondition queries
    // The key signal: no PRECONDITION_FAILED in response
    const body = await res.json()
    expect(body.code).toBeUndefined()
    expect(body.data.plan).not.toContain('bo_laksana')
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

// ─── 8. scope='asset_set' — targeted subset build for one chart ───────────────

describe('POST /api/cockpit/runs — scope=asset_set', () => {
  it('builds only the requested subset, dependency-ordered, and inserts build_runs with scope=asset_set', async () => {
    seedRole('client')
    // asset_set does NOT trigger the scope=asset global-asset lookup — same query flow as layer.
    seedSuccessfulBuild(REGISTRY_WITH_L0)

    const { POST } = await import('../route')
    const res = await POST(makeReq({
      chart_id: 'c1', scope: 'asset_set',
      scope_target: 'ga_strength,ga_positions', action: 'rebuild',
    }))
    expect(res.status).toBe(201)
    const body = await res.json()
    // Exactly the requested subset, dependency-ordered (ga_positions before ga_strength).
    expect(body.data.plan).toEqual(['ga_positions', 'ga_strength'])
    expect(body.data.asset_count).toBe(2)

    // build_runs INSERT carries scope='asset_set' and the comma-list scope_target.
    const insertCall = mockQuery.mock.calls.find(
      c => typeof c[0] === 'string' && c[0].includes('INSERT INTO build_runs')
    )
    expect(insertCall).toBeDefined()
    const params = insertCall![1] as unknown[]
    // params = [chart_id, scope, scope_target, action, state..., plan, triggered_by]
    expect(params[1]).toBe('asset_set')
    expect(params[2]).toBe('ga_strength,ga_positions')

    // build_run_assets rows inserted for each planned asset.
    const assetInsert = mockQuery.mock.calls.find(
      c => typeof c[0] === 'string' && c[0].includes('INSERT INTO build_run_assets')
    )
    expect(assetInsert).toBeDefined()
    const assetParams = assetInsert![1] as unknown[]
    expect(assetParams).toContain('ga_positions')
    expect(assetParams).toContain('ga_strength')
  })

  it('returns 400 EMPTY_ASSET_SET when scope_target is empty', async () => {
    // Scope validation short-circuits BEFORE getUserRole — only an authed user is needed
    // (queuing a getUserRole mock here would leak an unconsumed Once into the next test).
    mockGetServerUser.mockResolvedValue(USER)

    const { POST } = await import('../route')
    const res = await POST(makeReq({
      chart_id: 'c1', scope: 'asset_set', scope_target: '', action: 'rebuild',
    }))
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.code).toBe('EMPTY_ASSET_SET')
  })

  it('returns 400 EMPTY_ASSET_SET when scope_target is missing', async () => {
    mockGetServerUser.mockResolvedValue(USER)

    const { POST } = await import('../route')
    const res = await POST(makeReq({
      chart_id: 'c1', scope: 'asset_set', action: 'rebuild',
    }))
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.code).toBe('EMPTY_ASSET_SET')
  })
})

describe('POST /api/cockpit/runs — governed global service probes', () => {
  it('dispatches exactly one super_admin-selected no-writer service probe without a clear', async () => {
    seedRole('super_admin')
    seedSuccessfulBuild(REGISTRY_EPHEMERIS_SERVICE as typeof REGISTRY_WITH_L0)

    const { POST } = await import('../route')
    const res = await POST(makeReq({
      chart_id: 'c1', scope: 'asset_set', scope_target: 'bg_ephemeris_engine', action: 'rebuild', clear_before: false,
    }))
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.data.plan).toEqual(['bg_ephemeris_engine'])
    expect(body.data.asset_count).toBe(1)
    expect(mockInvokeRunJob).toHaveBeenCalledTimes(1)

    const insert = mockQuery.mock.calls.find(([sql]) => String(sql).includes('INSERT INTO build_runs'))
    const manifest = JSON.parse((insert![1] as unknown[])[5] as string)
    expect(manifest.waves).toEqual([['bg_ephemeris_engine']])
    expect(manifest.assets).toHaveLength(1)
    expect(manifest.assets[0].asset_id).toBe('bg_ephemeris_engine')

    const assetInsert = mockQuery.mock.calls.find(([sql]) => String(sql).includes('INSERT INTO build_run_assets'))
    expect(assetInsert![1]).toContain('bg_ephemeris_engine')
    expect(assetInsert![1]).not.toContain('ga_positions')
  })

  it('dispatches bg_panchanga as the same singleton, manifest-shaped probe contract', async () => {
    seedRole('super_admin')
    seedSuccessfulBuild(REGISTRY_PANCHANGA_SERVICE as typeof REGISTRY_WITH_L0)

    const { POST } = await import('../route')
    const res = await POST(makeReq({
      chart_id: 'c1', scope: 'asset_set', scope_target: 'bg_panchanga', action: 'rebuild', clear_before: false,
    }))

    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.data.plan).toEqual(['bg_panchanga'])
    expect(body.data.asset_count).toBe(1)

    const insert = mockQuery.mock.calls.find(([sql]) => String(sql).includes('INSERT INTO build_runs'))
    const manifest = JSON.parse((insert![1] as unknown[])[5] as string)
    expect(manifest).toMatchObject({
      scope: 'asset_set',
      scope_target: 'bg_panchanga',
      waves: [['bg_panchanga']],
    })
    expect(manifest.assets).toHaveLength(1)
    expect(manifest.assets[0].asset_id).toBe('bg_panchanga')
  })

  it('rejects a client before creating a global service-probe run', async () => {
    seedRole('client')
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: REGISTRY_EPHEMERIS_SERVICE, rowCount: 1 })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce(NO_PROTECTED_ASSETS)
      .mockResolvedValueOnce(NO_FRESHNESS)

    const { POST } = await import('../route')
    const res = await POST(makeReq({
      chart_id: 'c1', scope: 'asset_set', scope_target: 'bg_ephemeris_engine', action: 'rebuild',
    }))
    expect(res.status).toBe(403)
    expect((await res.json()).code).toBe('FORBIDDEN_SERVICE_PROBE')
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
    expect(mockQuery.mock.calls.some(([sql]) => String(sql).includes('INSERT INTO build_runs'))).toBe(false)
  })

  it('refuses clear_before for a service probe', async () => {
    seedRole('super_admin')
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: REGISTRY_EPHEMERIS_SERVICE, rowCount: 1 })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce(NO_PROTECTED_ASSETS)
      .mockResolvedValueOnce(NO_FRESHNESS)

    const { POST } = await import('../route')
    const res = await POST(makeReq({
      chart_id: 'c1', scope: 'asset_set', scope_target: 'bg_ephemeris_engine', action: 'rebuild', clear_before: true,
    }))
    expect(res.status).toBe(400)
    expect((await res.json()).code).toBe('SERVICE_PROBE_CLEAR_FORBIDDEN')
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

})

describe('POST /api/cockpit/runs — service probe dependency identities', () => {
  function seedPanchangaDependentBuild(
    throughputRows: ReadonlyArray<{ asset_id: string; state: string }>,
    freshnessRows: ReadonlyArray<ReturnType<typeof freshnessRow>>,
    scope: 'asset' | 'layer' | 'global' = 'asset',
  ) {
    seedRole('client')
    // scope=asset checks the target before the normal dispatch reads. A client
    // must retain the global probe as a dependency identity without gaining an
    // L0/service selection path.
    if (scope === 'asset') {
      mockQuery.mockResolvedValueOnce({ rows: [{ scope: 'per_chart' }], rowCount: 1 })
    }
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: REGISTRY_PANCHANGA_DEPENDENT, rowCount: REGISTRY_PANCHANGA_DEPENDENT.length })
      .mockResolvedValueOnce({ rows: throughputRows, rowCount: throughputRows.length })
      .mockResolvedValueOnce(NO_PROTECTED_ASSETS)
      .mockResolvedValueOnce({ rows: freshnessRows, rowCount: freshnessRows.length })
      .mockResolvedValue({ rows: [{ id: 'run-panchanga-001' }], rowCount: 1 })
    mockInvokeRunJob.mockResolvedValue(undefined)
  }

  it('allows ga_panchanga only when its retained service probe identity is healthy and fresh', async () => {
    seedPanchangaDependentBuild(
      [{ asset_id: 'bg_panchanga', state: 'service_ok' }],
      [freshnessRow('bg_panchanga', 'fresh')],
    )

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'asset', scope_target: 'ga_panchanga', action: 'build' }))

    expect(res.status).toBe(201)
    expect((await res.json()).data.plan).toEqual(['ga_panchanga'])
    const insert = mockQuery.mock.calls.find(([sql]) => String(sql).includes('INSERT INTO build_runs'))
    const manifest = JSON.parse((insert![1] as unknown[])[5] as string)
    expect(manifest.assets.map((asset: { asset_id: string }) => asset.asset_id)).toEqual(['ga_panchanga'])
  })

  it('blocks ga_panchanga when its service probe receipt is missing', async () => {
    seedPanchangaDependentBuild([], [])

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'asset', scope_target: 'ga_panchanga', action: 'build' }))

    expect(res.status).toBe(422)
    expect((await res.json()).blockers).toEqual(expect.arrayContaining([
      expect.objectContaining({ dep_asset_id: 'bg_panchanga', dep_state: 'unknown', required_by: ['ga_panchanga'] }),
    ]))
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('blocks ga_panchanga when its service probe receipt is stale', async () => {
    seedPanchangaDependentBuild(
      [{ asset_id: 'bg_panchanga', state: 'service_ok' }],
      [freshnessRow('bg_panchanga', 'stale')],
    )

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'asset', scope_target: 'ga_panchanga', action: 'build' }))

    expect(res.status).toBe(422)
    expect((await res.json()).blockers).toEqual(expect.arrayContaining([
      expect.objectContaining({ dep_asset_id: 'bg_panchanga', dep_state: 'stale', required_by: ['ga_panchanga'] }),
    ]))
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('never dispatches a no-writer service in an L0 layer build', async () => {
    seedRole('super_admin')
    seedSuccessfulBuild([
      ...REGISTRY_WITH_L0.filter(row => row.layer === 'brahmagyan'),
      ...REGISTRY_PANCHANGA_SERVICE,
    ] as typeof REGISTRY_WITH_L0)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'brahmagyan', action: 'rebuild' }))

    expect(res.status).toBe(201)
    expect((await res.json()).data.plan).toEqual(['bg_ephemeris', 'bg_ontology'])
  })

  it('allows a client ganita-layer build when the out-of-scope Panchanga probe is healthy and fresh', async () => {
    seedPanchangaDependentBuild(
      [{ asset_id: 'bg_panchanga', state: 'service_ok' }],
      [freshnessRow('bg_panchanga', 'fresh')],
      'layer',
    )

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'ganita', action: 'build' }))

    expect(res.status).toBe(201)
    expect((await res.json()).data.plan).toEqual(['ga_panchanga'])
  })

  it.each([
    ['missing', [], []],
    ['stale', [{ asset_id: 'bg_panchanga', state: 'service_ok' }], [freshnessRow('bg_panchanga', 'stale')]],
  ] as const)('blocks a client ganita-layer build when the Panchanga probe is %s', async (_state, throughputRows, freshnessRows) => {
    seedPanchangaDependentBuild(throughputRows, freshnessRows, 'layer')

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'ganita', action: 'build' }))

    expect(res.status).toBe(422)
    expect((await res.json()).blockers).toEqual(expect.arrayContaining([
      expect.objectContaining({ dep_asset_id: 'bg_panchanga', required_by: ['ga_panchanga'] }),
    ]))
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('allows global update only when the excluded Panchanga probe is healthy and fresh', async () => {
    seedPanchangaDependentBuild(
      [{ asset_id: 'ga_panchanga', state: 'dormant' }, { asset_id: 'bg_panchanga', state: 'service_ok' }],
      [freshnessRow('ga_panchanga', 'fresh'), freshnessRow('bg_panchanga', 'fresh')],
      'global',
    )

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', action: 'update' }))

    expect(res.status).toBe(201)
    expect((await res.json()).data.plan).toEqual(['ga_panchanga'])
  })

  it.each(['build', 'rebuild'] as const)('allows global %s when the excluded Panchanga probe is healthy and fresh', async (action) => {
    seedPanchangaDependentBuild(
      [{ asset_id: 'ga_panchanga', state: 'dormant' }, { asset_id: 'bg_panchanga', state: 'service_ok' }],
      [freshnessRow('ga_panchanga', 'fresh'), freshnessRow('bg_panchanga', 'fresh')],
      'global',
    )

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', action }))

    expect(res.status).toBe(201)
    expect((await res.json()).data.plan).toEqual(['ga_panchanga'])
  })

  it.each(['build', 'rebuild'] as const)('blocks global %s when its planned consumer has a stale excluded Panchanga probe', async (action) => {
    seedPanchangaDependentBuild(
      [{ asset_id: 'ga_panchanga', state: 'dormant' }, { asset_id: 'bg_panchanga', state: 'service_ok' }],
      [freshnessRow('ga_panchanga', 'fresh'), freshnessRow('bg_panchanga', 'stale')],
      'global',
    )

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', action }))

    expect(res.status).toBe(422)
    expect((await res.json()).blockers).toEqual(expect.arrayContaining([
      expect.objectContaining({ dep_asset_id: 'bg_panchanga', dep_state: 'stale' }),
    ]))
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('blocks global update and cascade when their planned consumer has a stale excluded Panchanga probe', async () => {
    seedPanchangaDependentBuild(
      [{ asset_id: 'ga_panchanga', state: 'dormant' }, { asset_id: 'bg_panchanga', state: 'service_ok' }],
      [freshnessRow('ga_panchanga', 'fresh'), freshnessRow('bg_panchanga', 'stale')],
      'global',
    )

    const { POST } = await import('../route')
    const update = await POST(makeReq({ chart_id: 'c1', scope: 'global', action: 'update' }))
    expect(update.status).toBe(422)
    expect((await update.json()).blockers).toEqual(expect.arrayContaining([
      expect.objectContaining({ dep_asset_id: 'bg_panchanga', dep_state: 'stale' }),
    ]))

    vi.clearAllMocks()
    seedPanchangaDependentBuild(
      [{ asset_id: 'ga_panchanga', state: 'lit' }, { asset_id: 'bg_panchanga', state: 'service_ok' }],
      [freshnessRow('ga_panchanga', 'fresh'), freshnessRow('bg_panchanga', 'stale')],
      'global',
    )
    const cascade = await POST(makeReq({ chart_id: 'c1', scope: 'global', action: 'cascade' }))
    expect(cascade.status).toBe(422)
    expect((await cascade.json()).blockers).toEqual(expect.arrayContaining([
      expect.objectContaining({ dep_asset_id: 'bg_panchanga', dep_state: 'stale' }),
    ]))
  })

  it('keeps global cascade as a no-op when all dependency identities are fresh', async () => {
    seedPanchangaDependentBuild(
      [{ asset_id: 'ga_panchanga', state: 'lit' }, { asset_id: 'bg_panchanga', state: 'service_ok' }],
      [freshnessRow('ga_panchanga', 'fresh'), freshnessRow('bg_panchanga', 'fresh')],
      'global',
    )

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'global', action: 'cascade' }))

    expect(res.status).toBe(422)
    expect((await res.json()).code).toBe('ALL_LIT')
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })
})

// ─── G1 — Build on lit layer returns ALL_LIT with Rebuild hint (not generic 422) ──

describe('G1 — All-lit Build returns ALL_LIT code with Rebuild redirect', () => {
  it('O-wave WP-1: trusts a fresh receipt classification even when the asset is absent from the generated writer-digest inventory', async () => {
    // Before the WP-1 fix, this route re-derived its own "expected" code_digest
    // from the generated nirmana-writer-digests.json and treated any asset the
    // inventory didn't cover (the large majority -- it only ever listed L0's
    // bg_* writers) as 'unknown', overriding the sidecar's own 'fresh'
    // classification. asset_freshness.freshness_state is now the sole runtime
    // authority (NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §3.1 "one authority");
    // the inventory remains campaign-evidence pinning only. A ga_* asset (never
    // in the inventory) reported 'fresh' by the sidecar must stay ALL_LIT, not
    // silently reclassified to 'unknown'/'stale' and rebuilt.
    seedRole('client')
    const registry = [REGISTRY_GANITA_ONLY[0]]
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: registry, rowCount: 1 })
      .mockResolvedValueOnce({ rows: [{ asset_id: registry[0].asset_id, state: 'lit' }], rowCount: 1 })
      .mockResolvedValueOnce(NO_PROTECTED_ASSETS)
      .mockResolvedValueOnce({
        rows: [{ asset_id: registry[0].asset_id, state: 'fresh', reasons: [] }],
        rowCount: 1,
      })

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'ganita', action: 'build' }))
    expect(res.status).toBe(422)
    expect((await res.json()).code).toBe('ALL_LIT')
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('RED — action=build on all-lit layer returns 422 with generic error (before G1 fix)', async () => {
    // Demonstrates the pre-G1 behavior: 422 with no actionable guidance.
    // After G1 the response now includes code=ALL_LIT + hint pointing to Rebuild.
    // This test documents the distinction by asserting the new behavior is richer.
    seedRole('client')
    const allLitThroughput = REGISTRY_GANITA_ONLY.map(r => ({ asset_id: r.asset_id, state: 'lit' }))
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                          // 409 gate
      .mockResolvedValueOnce({ rows: REGISTRY_GANITA_ONLY, rowCount: REGISTRY_GANITA_ONLY.length }) // registry
      .mockResolvedValueOnce({ rows: allLitThroughput, rowCount: allLitThroughput.length })     // throughput (all lit)
      .mockResolvedValueOnce(NO_PROTECTED_ASSETS)                                                // build_protected_assets
      .mockResolvedValueOnce({
        rows: REGISTRY_GANITA_ONLY.map(r => ({
          asset_id: r.asset_id,
          state: 'fresh',
          reasons: [],
          code_digest: (writerDigestInventory.writers as Record<string, string>)[r.asset_id],
        })),
        rowCount: REGISTRY_GANITA_ONLY.length,
      })                                                                                         // asset_freshness

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'ganita', action: 'build' }))
    expect(res.status).toBe(422)
    const body = await res.json()
    // GREEN assertion: after G1 the response is actionable
    expect(body.code).toBe('ALL_LIT')
    expect(body.hint).toContain('Rebuild')
    expect(body.error).toContain('already built')
  })

  it('GREEN — action=rebuild on lit layer bypasses ALL_LIT and creates the run', async () => {
    seedRole('client')
    const allLitThroughput = REGISTRY_GANITA_ONLY.map(r => ({ asset_id: r.asset_id, state: 'lit' }))
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                          // 409 gate
      .mockResolvedValueOnce({ rows: REGISTRY_GANITA_ONLY, rowCount: REGISTRY_GANITA_ONLY.length }) // registry
      .mockResolvedValueOnce({ rows: allLitThroughput, rowCount: allLitThroughput.length })     // throughput (all lit)
      .mockResolvedValueOnce(NO_PROTECTED_ASSETS)                                                // build_protected_assets
      .mockResolvedValueOnce(NO_FRESHNESS)                                                        // asset_freshness
      .mockResolvedValue({ rows: [{ id: 'run-rebuild-001' }], rowCount: 1 })
    mockInvokeRunJob.mockResolvedValue(undefined)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'ganita', action: 'rebuild' }))
    expect(res.status).toBe(201)
    const body = await res.json()
    // rebuild always includes all assets regardless of lit state
    expect(body.data.plan).toContain('ga_positions')
    expect(body.code).toBeUndefined()
  })
})

// ─── SHAD-DARSHANA sweep-protection Phase 1a — build_protected_assets planner guard ──
//
// Query order for an asset-scope build against a chart with a protected pair:
//   1. getUserRole
//   2. (scope='asset' + non-global asset skips the global-asset lookup entirely)
//   3. 409 gate
//   4. asset_registry
//   5. asset_throughput
//   6. build_protected_assets  ← the guard under test
//   7+. either the 422 short-circuit (no further queries) or the INSERT chain

describe('SHAD-DARSHANA sweep-protection — build_protected_assets planner guard', () => {
  const REGISTRY_SWEEP = [
    { asset_id: 'ka_gochara_sweep', layer: 'kala', scope: 'per_chart', depends_on: [], estimated_seconds: 1800 },
    { asset_id: 'ka_kshetra',       layer: 'kala', scope: 'per_chart', depends_on: [], estimated_seconds: 60 },
  ]

  it('a protected pair is blocked and surfaced — never silently dispatched (scope=asset, the only candidate)', async () => {
    seedRole('client')
    mockQuery
      .mockResolvedValueOnce({ rows: [{ scope: 'per_chart' }], rowCount: 1 })              // scope=asset: global-asset lookup
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                    // 409 gate
      .mockResolvedValueOnce({ rows: REGISTRY_SWEEP, rowCount: REGISTRY_SWEEP.length })   // asset_registry
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                    // asset_throughput (dormant)
      .mockResolvedValueOnce({ rows: [{ asset_id: 'ka_gochara_sweep' }], rowCount: 1 })   // build_protected_assets — protected!
      .mockResolvedValueOnce(NO_FRESHNESS)                                                // asset_freshness

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'asset', scope_target: 'ka_gochara_sweep', action: 'build' }))

    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.code).toBe('PROTECTED')
    expect(body.protected_assets).toEqual([
      { asset_id: 'ka_gochara_sweep', message: 'protected — native override required' },
    ])
    // The job was never dispatched and no build_run was ever inserted.
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
    expect(mockQuery.mock.calls.some(c => typeof c[0] === 'string' && c[0].includes('INSERT INTO build_runs'))).toBe(false)
  })

  it('a protected asset is withheld from a wider scope while non-protected assets in the same scope proceed normally', async () => {
    seedRole('client')
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                    // 409 gate
      .mockResolvedValueOnce({ rows: REGISTRY_SWEEP, rowCount: REGISTRY_SWEEP.length })   // asset_registry
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })                                    // asset_throughput (both dormant)
      .mockResolvedValueOnce({ rows: [{ asset_id: 'ka_gochara_sweep' }], rowCount: 1 })   // build_protected_assets
      .mockResolvedValueOnce(NO_FRESHNESS)                                                // asset_freshness
      .mockResolvedValue({ rows: [{ id: 'run-kala-001' }], rowCount: 1 })                 // INSERT build_runs + assets
    mockInvokeRunJob.mockResolvedValue(undefined)

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'kala', action: 'build' }))

    expect(res.status).toBe(201)
    const body = await res.json()
    // The non-protected asset proceeds — it is in the dispatched plan.
    expect(body.data.plan).toContain('ka_kshetra')
    // The protected asset is withheld from the plan entirely.
    expect(body.data.plan).not.toContain('ka_gochara_sweep')
    // ...and surfaced explicitly rather than silently dropped.
    expect(body.data.protected_assets).toEqual([
      { asset_id: 'ka_gochara_sweep', message: 'protected — native override required' },
    ])
  })

  it('a retired writer cannot be dispatched merely because protection was removed', async () => {
    seedRole('client')
    seedSuccessfulBuild(REGISTRY_SWEEP) // NO_PROTECTED_ASSETS — nothing protected for this chart

    const { POST } = await import('../route')
    const res = await POST(makeReq({ chart_id: 'c1', scope: 'layer', scope_target: 'kala', action: 'build' }))

    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.code).toBe('CODE_DIGEST_UNAVAILABLE')
    expect(body.error).toContain('ka_gochara_sweep')
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })
})

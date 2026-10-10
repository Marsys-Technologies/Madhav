// @vitest-environment node
/**
 * SS N-373 / PR-S1 — "lock the unauthenticated handlers".
 *
 * proxy.ts only checks that the `__session` cookie LOOKS right (non-
 * cryptographic), so a handler without its own real verification is reachable
 * with a forged cookie. This table-driven test pins, for every handler named in
 * the session-gate audit (SESSION_GATE_AUDIT.md section 2 / 9b):
 *
 *   unauthenticated                 -> 401, NO side effect
 *   authenticated, not super_admin  -> 403, NO side effect
 *   super_admin                     -> the handler's own success path
 *
 * "NO side effect" is asserted against the real effect spies (fs writes,
 * atomicApply, the model ping, DB INSERT/UPDATE), not against the status code
 * alone, so a guard placed AFTER the effect cannot pass.
 *
 * The build stop/skip routes are chart-scoped: chart owner or super_admin only.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest, NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))

// ── auth seams ───────────────────────────────────────────────────────────────
const requireSuperAdminMock = vi.fn()
vi.mock('@/lib/auth/access-control', () => ({
  requireSuperAdmin: () => requireSuperAdminMock(),
  getServerUserWithProfile: vi.fn(),
}))

const getServerUserMock = vi.fn()
vi.mock('@/lib/firebase/server', () => ({
  getServerUser: () => getServerUserMock(),
}))

// ── effect spies ─────────────────────────────────────────────────────────────
const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => queryMock(...a) }))

const atomicApplyMock = vi.fn()
vi.mock('@/lib/icr/atomic_apply', () => ({ atomicApply: (...a: unknown[]) => atomicApplyMock(...a) }))

const runHealthChecksMock = vi.fn()
const getAllHealthStatusesMock = vi.fn()
vi.mock('@/lib/models/health', () => ({
  runHealthChecks: () => runHealthChecksMock(),
  getAllHealthStatuses: () => getAllHealthStatusesMock(),
}))

const fsMock = {
  readFileSync: vi.fn(),
  writeFileSync: vi.fn(),
  mkdirSync: vi.fn(),
  rmSync: vi.fn(),
  renameSync: vi.fn(),
  appendFileSync: vi.fn(),
  existsSync: vi.fn(),
  readdirSync: vi.fn(),
}
vi.mock('fs', () => ({ default: fsMock, ...fsMock }))

// ── helpers ──────────────────────────────────────────────────────────────────
type Who = 'unauthenticated' | 'guest' | 'super_admin'

function setSuperAdminGate(who: Who) {
  if (who === 'unauthenticated') {
    requireSuperAdminMock.mockResolvedValue(NextResponse.json({ error: 'unauthorized' }, { status: 401 }))
  } else if (who === 'guest') {
    requireSuperAdminMock.mockResolvedValue(NextResponse.json({ error: 'forbidden' }, { status: 403 }))
  } else {
    requireSuperAdminMock.mockResolvedValue({
      user: { uid: 'admin-1' },
      profile: { id: 'admin-1', role: 'super_admin', status: 'active' },
    })
  }
}

function json(method: string, url: string, body?: unknown): NextRequest {
  return new NextRequest(`http://localhost${url}`, {
    method,
    headers: { 'content-type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

function fsMutations(): number {
  return (
    fsMock.writeFileSync.mock.calls.length +
    fsMock.mkdirSync.mock.calls.length +
    fsMock.rmSync.mock.calls.length +
    fsMock.renameSync.mock.calls.length +
    fsMock.appendFileSync.mock.calls.length
  )
}
function fsReads(): number {
  return fsMock.readFileSync.mock.calls.length + fsMock.readdirSync.mock.calls.length
}
function dbWrites(): number {
  return queryMock.mock.calls.filter(([sql]) => /^\s*(INSERT|UPDATE|DELETE)/i.test(String(sql))).length
}

beforeEach(() => {
  vi.resetModules()
  for (const m of [requireSuperAdminMock, getServerUserMock, queryMock, atomicApplyMock, runHealthChecksMock, getAllHealthStatusesMock]) m.mockReset()
  for (const m of Object.values(fsMock)) m.mockReset()
  atomicApplyMock.mockReturnValue({ ok: true })
  runHealthChecksMock.mockResolvedValue([{ model_id: 'm', status: 'healthy' }])
  getAllHealthStatusesMock.mockReturnValue([])
  fsMock.readFileSync.mockReturnValue('patch_id: p1\nstatus: PROPOSED\n')
  fsMock.existsSync.mockReturnValue(true)
  fsMock.readdirSync.mockReturnValue(['p1.yaml'])
  queryMock.mockResolvedValue({ rows: [], rowCount: 0 })
})

// ═════════════════════════════════════════════════════════════════════════════
// 1. requireSuperAdmin handlers
// ═════════════════════════════════════════════════════════════════════════════

interface SuperAdminCase {
  name: string
  /** Module under test, and the exported HTTP methods that MUST be guarded. */
  load: () => Promise<Record<string, unknown>>
  methods: string[]
  call: (mod: Record<string, (r: NextRequest) => Promise<Response>>) => Promise<Response>
  /** Total side effects observed (must be 0 when denied). */
  effects: () => number
  /** Status the handler returns for a super_admin. */
  okStatus: number
}

const HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']

const SUPER_ADMIN_CASES: SuperAdminCase[] = [
  {
    name: 'POST /api/icr/confirm (confirm)',
    load: () => import('@/app/api/icr/confirm/route'),
    methods: ['POST'],
    call: (m) => m.POST(json('POST', '/api/icr/confirm', { patch_file: 'p1.yaml', action: 'confirm' })),
    effects: () => atomicApplyMock.mock.calls.length + fsMutations() + fsReads(),
    okStatus: 200,
  },
  {
    name: 'POST /api/icr/confirm (reject)',
    load: () => import('@/app/api/icr/confirm/route'),
    methods: ['POST'],
    call: (m) => m.POST(json('POST', '/api/icr/confirm', { patch_file: 'p1.yaml', action: 'reject', reason: 'no' })),
    effects: () => atomicApplyMock.mock.calls.length + fsMutations() + fsReads(),
    okStatus: 200,
  },
  {
    name: 'POST /api/icr/confirm (escalate)',
    load: () => import('@/app/api/icr/confirm/route'),
    methods: ['POST'],
    call: (m) => m.POST(json('POST', '/api/icr/confirm', { patch_file: 'p1.yaml', action: 'escalate', reason: 'l1' })),
    effects: () => atomicApplyMock.mock.calls.length + fsMutations() + fsReads(),
    okStatus: 200,
  },
  {
    name: 'GET /api/icr/patches',
    load: () => import('@/app/api/icr/patches/route'),
    methods: ['GET'],
    call: (m) => m.GET(json('GET', '/api/icr/patches')),
    effects: () => fsReads(),
    okStatus: 200,
  },
  {
    name: 'POST /api/admin/maintenance/trace-cleanup',
    load: () => import('@/app/api/admin/maintenance/trace-cleanup/route'),
    methods: ['POST'],
    call: (m) => m.POST(json('POST', '/api/admin/maintenance/trace-cleanup')),
    effects: () => queryMock.mock.calls.length,
    okStatus: 200,
  },
  {
    name: 'GET /api/admin/model-health',
    load: () => import('@/app/api/admin/model-health/route'),
    methods: ['GET'],
    call: (m) => m.GET(json('GET', '/api/admin/model-health')),
    effects: () => runHealthChecksMock.mock.calls.length + getAllHealthStatusesMock.mock.calls.length,
    okStatus: 200,
  },
  {
    name: 'GET /api/admin/model-health?refresh=true (live provider pings)',
    load: () => import('@/app/api/admin/model-health/route'),
    methods: ['GET'],
    call: (m) => m.GET(json('GET', '/api/admin/model-health?refresh=true')),
    effects: () => runHealthChecksMock.mock.calls.length + getAllHealthStatusesMock.mock.calls.length,
    okStatus: 200,
  },
]

describe('super_admin-only handlers (SS N-373 item 1)', () => {
  for (const c of SUPER_ADMIN_CASES) {
    describe(c.name, () => {
      it('exports no HTTP method beyond the guarded set', async () => {
        const mod = await c.load()
        const exported = Object.keys(mod).filter((k) => HTTP_METHODS.includes(k)).sort()
        expect(exported).toEqual([...c.methods].sort())
      })

      it('unauthenticated -> 401 and no side effect', async () => {
        setSuperAdminGate('unauthenticated')
        const res = await c.call((await c.load()) as never)
        expect(res.status).toBe(401)
        expect(c.effects()).toBe(0)
      })

      it('authenticated non-super-admin -> 403 and no side effect', async () => {
        setSuperAdminGate('guest')
        const res = await c.call((await c.load()) as never)
        expect(res.status).toBe(403)
        expect(c.effects()).toBe(0)
      })

      it('super_admin -> handler runs', async () => {
        setSuperAdminGate('super_admin')
        const res = await c.call((await c.load()) as never)
        expect(res.status).toBe(c.okStatus)
        expect(c.effects()).toBeGreaterThan(0)
      })
    })
  }

  it('the 401 / 403 bodies match the shape of the already-guarded admin routes', async () => {
    setSuperAdminGate('unauthenticated')
    const mod = (await import('@/app/api/admin/maintenance/trace-cleanup/route')) as unknown as {
      POST: (r: NextRequest) => Promise<Response>
    }
    expect(await (await mod.POST(json('POST', '/x'))).json()).toEqual({ error: 'unauthorized' })
    setSuperAdminGate('guest')
    expect(await (await mod.POST(json('POST', '/x'))).json()).toEqual({ error: 'forbidden' })
  })

  it('model-health: the guard runs BEFORE the refresh ping', async () => {
    const order: string[] = []
    requireSuperAdminMock.mockImplementation(async () => {
      order.push('guard')
      return NextResponse.json({ error: 'forbidden' }, { status: 403 })
    })
    runHealthChecksMock.mockImplementation(async () => {
      order.push('ping')
      return []
    })
    const mod = (await import('@/app/api/admin/model-health/route')) as unknown as {
      GET: (r: NextRequest) => Promise<Response>
    }
    const res = await mod.GET(json('GET', '/api/admin/model-health?refresh=true'))
    expect(res.status).toBe(403)
    expect(order).toEqual(['guard'])
  })
})

// ═════════════════════════════════════════════════════════════════════════════
// 3. build stop / skip: chart owner or super_admin
// ═════════════════════════════════════════════════════════════════════════════

const BUILD_ID = '11111111-1111-4111-8111-111111111111'
const ORPHAN_BUILD_ID = '22222222-2222-4222-8222-222222222222'
const CHART_ID = 'chart-owned-by-owner-1'

interface BuildWorld {
  role: 'guest' | 'super_admin'
  /** build_runs.id -> chart_id */
  runs?: Record<string, string>
  /** build_events.build_id -> chart_ids */
  events?: Record<string, string[]>
  chartOwner?: Record<string, string>
  grants?: Array<{ chart_id: string; principal_id: string; permission: string }>
}

function installBuildWorld(w: BuildWorld) {
  queryMock.mockImplementation(async (sql: string, params: unknown[] = []) => {
    const s = String(sql)
    if (/FROM profiles/.test(s)) return { rows: [{ role: w.role }] }
    if (/^\s*SELECT[\s\S]*FROM build_runs/i.test(s)) {
      const chart = w.runs?.[String(params[0])]
      return { rows: chart ? [{ chart_id: chart }] : [] }
    }
    if (/^\s*SELECT[\s\S]*FROM build_events/i.test(s)) {
      return { rows: (w.events?.[String(params[0])] ?? []).map((chart_id) => ({ chart_id })) }
    }
    if (/FROM charts WHERE id/.test(s)) {
      const owner = w.chartOwner?.[String(params[0])]
      return { rows: owner ? [{ owner_id: owner }] : [] }
    }
    if (/FROM chart_grants/.test(s)) {
      const g = (w.grants ?? []).find((x) => x.chart_id === params[0] && x.principal_id === params[1])
      return { rows: g ? [{ permission: g.permission }] : [] }
    }
    return { rows: [], rowCount: 1 }
  })
}

const BUILD_ROUTES = [
  { name: 'POST /api/build/stop', load: () => import('@/app/api/build/stop/route'), body: { build_id: BUILD_ID } },
  { name: 'POST /api/build/asset/stop', load: () => import('@/app/api/build/asset/stop/route'), body: { build_id: BUILD_ID, asset_id: 'ga_x' } },
  { name: 'POST /api/build/asset/skip', load: () => import('@/app/api/build/asset/skip/route'), body: { build_id: BUILD_ID, asset_id: 'ga_x' } },
] as const

describe('build stop / skip are restricted to the chart owner or super_admin (SS N-373 item 3)', () => {
  for (const r of BUILD_ROUTES) {
    describe(r.name, () => {
      const call = async (body: unknown = r.body) => {
        const mod = (await r.load()) as unknown as { POST: (q: NextRequest) => Promise<Response> }
        return mod.POST(json('POST', '/api/build/x', body))
      }
      const world: Omit<BuildWorld, 'role'> = {
        runs: { [BUILD_ID]: CHART_ID },
        chartOwner: { [CHART_ID]: 'owner-1' },
      }

      it('unauthenticated -> 401, no DB access at all', async () => {
        getServerUserMock.mockResolvedValue(null)
        installBuildWorld({ role: 'guest', ...world })
        const res = await call()
        expect(res.status).toBe(401)
        expect(queryMock).not.toHaveBeenCalled()
      })

      it('guest of ANOTHER chart -> 403 and no write', async () => {
        getServerUserMock.mockResolvedValue({ uid: 'guest-2' })
        installBuildWorld({ role: 'guest', ...world })
        const res = await call()
        expect(res.status).toBe(403)
        expect(dbWrites()).toBe(0)
      })

      it('view-only grantee of the chart -> 403 and no write (a read grant is not a stop grant)', async () => {
        getServerUserMock.mockResolvedValue({ uid: 'viewer-3' })
        installBuildWorld({
          role: 'guest',
          ...world,
          grants: [{ chart_id: CHART_ID, principal_id: 'viewer-3', permission: 'view' }],
        })
        const res = await call()
        expect(res.status).toBe(403)
        expect(dbWrites()).toBe(0)
      })

      it('chart owner -> allowed and the write happens', async () => {
        getServerUserMock.mockResolvedValue({ uid: 'owner-1' })
        installBuildWorld({ role: 'guest', ...world })
        const res = await call()
        expect(res.status).toBe(200)
        expect(dbWrites()).toBe(1)
      })

      it('super_admin -> allowed and the write happens', async () => {
        getServerUserMock.mockResolvedValue({ uid: 'admin-1' })
        installBuildWorld({ role: 'super_admin', ...world })
        const res = await call()
        expect(res.status).toBe(200)
        expect(dbWrites()).toBe(1)
      })

      it('build not tied to any chart -> super_admin only (owner of any chart gets 403)', async () => {
        getServerUserMock.mockResolvedValue({ uid: 'owner-1' })
        installBuildWorld({ role: 'guest', ...world })
        const denied = await call({ ...r.body, build_id: ORPHAN_BUILD_ID })
        expect(denied.status).toBe(403)
        expect(dbWrites()).toBe(0)

        getServerUserMock.mockResolvedValue({ uid: 'admin-1' })
        installBuildWorld({ role: 'super_admin', ...world })
        const allowed = await call({ ...r.body, build_id: ORPHAN_BUILD_ID })
        expect(allowed.status).toBe(200)
        expect(dbWrites()).toBe(1)
      })

      it('build resolved through build_events (legacy) is chart-scoped the same way', async () => {
        const legacy = 'legacy-build-1'
        getServerUserMock.mockResolvedValue({ uid: 'guest-2' })
        installBuildWorld({ role: 'guest', events: { [legacy]: [CHART_ID] }, chartOwner: { [CHART_ID]: 'owner-1' } })
        expect((await call({ ...r.body, build_id: legacy })).status).toBe(403)
        getServerUserMock.mockResolvedValue({ uid: 'owner-1' })
        installBuildWorld({ role: 'guest', events: { [legacy]: [CHART_ID] }, chartOwner: { [CHART_ID]: 'owner-1' } })
        expect((await call({ ...r.body, build_id: legacy })).status).toBe(200)
      })

      it('a build spanning two charts needs write access on BOTH', async () => {
        getServerUserMock.mockResolvedValue({ uid: 'owner-1' })
        installBuildWorld({
          role: 'guest',
          runs: { [BUILD_ID]: CHART_ID },
          events: { [BUILD_ID]: ['other-chart'] },
          chartOwner: { [CHART_ID]: 'owner-1', 'other-chart': 'someone-else' },
        })
        const res = await call()
        expect(res.status).toBe(403)
        expect(dbWrites()).toBe(0)
      })

      it('a DB failure while resolving the chart fails CLOSED for a non-admin', async () => {
        getServerUserMock.mockResolvedValue({ uid: 'owner-1' })
        queryMock.mockImplementation(async (sql: string) => {
          if (/FROM profiles/.test(String(sql))) return { rows: [{ role: 'guest' }] }
          if (/^\s*SELECT/i.test(String(sql))) throw new Error('relation does not exist')
          return { rows: [], rowCount: 1 }
        })
        const res = await call()
        expect(res.status).toBe(403)
        expect(dbWrites()).toBe(0)
      })

      it('missing body fields still 400 for an authenticated caller', async () => {
        getServerUserMock.mockResolvedValue({ uid: 'owner-1' })
        installBuildWorld({ role: 'guest', ...world })
        const res = await call({})
        expect(res.status).toBe(400)
        expect(dbWrites()).toBe(0)
      })
    })
  }
})

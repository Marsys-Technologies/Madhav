/**
 * Regression test for P2 blocker B-008 — cross-chart read disclosure on
 * POST /api/cockpit/plan.
 *
 * The route's own comment said "Plan preview is a read-only operation — any
 * authenticated user may call it", and that reasoning is sound as far as it goes:
 * a plan preview genuinely is read-only, and it genuinely should not be
 * super_admin-only. The gap is that "any authenticated user" was applied to the
 * caller-supplied `chart_id` as well — so the read-only-ness was never the
 * question. It leaked, for an arbitrary chart:
 *
 *   - which assets are already built vs. dormant vs. stale (asset_throughput);
 *   - whether `chart_facts` is populated and whether `ga_structural` is lit
 *     (the bo_* precondition probes) — i.e. whether that chart has been built
 *     at all, and how far;
 *   - which assets are protected for that chart (build_protected_assets);
 *   - historical per-asset build durations for that chart's assets.
 *
 * That is a build-state profile of another user's chart. It carries no
 * subject_name / birth data — which is why this is graded below the destructive
 * routes rather than alongside them — but "no PII" is not "no disclosure", and
 * the current state was zero ownership check, so it gets the same gate.
 *
 * Level is 'read' (permission !== 'deny') rather than the 'write' the destructive
 * routes demand: a preview is precisely the kind of read a 'view' grant covers,
 * and the plan modal must keep working for view-grantees.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { POST } from '../route'

const VICTIM_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const VICTIM_UID = 'victim-uid'
const ATTACKER_UID = 'attacker-uid'
const ADMIN_UID = 'admin-uid'

const REGISTRY = [
  { asset_id: 'ka_kshetra', layer: 'kala', depends_on: [], estimated_seconds: 60 },
  { asset_id: 'ka_avadhi', layer: 'kala', depends_on: [], estimated_seconds: 90 },
]

let issued: string[] = []

function makeReq(body: object): NextRequest {
  return new NextRequest('http://localhost/api/cockpit/plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function setupMocks(opts: {
  uid: string
  role?: string
  ownerId?: string | null
  grantPermission?: string | null
}) {
  const { uid, role = 'guest', ownerId = VICTIM_UID, grantPermission = null } = opts
  mockGetServerUser.mockResolvedValue({ uid })
  issued = []

  mockQuery.mockImplementation((sql: string) => {
    issued.push(sql)
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }], rowCount: 1 })
    if (/FROM chart_grants/.test(sql)) {
      return Promise.resolve({
        rows: grantPermission ? [{ permission: grantPermission }] : [],
        rowCount: grantPermission ? 1 : 0,
      })
    }
    if (/owner_id[\s\S]*FROM charts/.test(sql)) {
      return Promise.resolve({ rows: [{ owner_id: ownerId }], rowCount: 1 })
    }
    if (/FROM asset_registry/.test(sql)) return Promise.resolve({ rows: REGISTRY, rowCount: REGISTRY.length })
    if (/FROM build_protected_assets/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM asset_throughput/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM build_run_assets/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

/** The chart-scoped state probes that must never run for an unauthorized caller. */
const chartStateProbes = () =>
  issued.filter(q => /FROM asset_throughput|FROM build_protected_assets|FROM chart_facts/i.test(q))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('POST /api/cockpit/plan — P2-B-008 cross-chart build-state disclosure', () => {
  it('DENIES a non-owner guest — and never probes the victim chart\'s build state', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala', action: 'build',
    }))
    expect(res.status).toBe(403)
    expect((await res.json()).code).toBe('FORBIDDEN_CHART')
    // No plan data, and the disclosure queries never ran at all.
    expect(chartStateProbes()).toHaveLength(0)
  })

  it('DENIES when the chart does not exist', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: null })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala', action: 'build',
    }))
    expect(res.status).toBe(403)
    expect(chartStateProbes()).toHaveLength(0)
  })

  it('ALLOWS the owner — the plan modal must keep working', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala', action: 'build',
    }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.data.plan_waves.flat()).toEqual(expect.arrayContaining(['ka_kshetra', 'ka_avadhi']))
  })

  it('ALLOWS a view-grantee — a preview is exactly what a read grant covers', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala', action: 'build',
    }))
    expect(res.status).toBe(200)
  })

  it('ALLOWS super_admin on a chart they do not own', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala', action: 'build',
    }))
    expect(res.status).toBe(200)
  })
})

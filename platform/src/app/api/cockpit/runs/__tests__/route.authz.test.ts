/**
 * Regression test for P2 blocker B-008 (Paripraśna Experience Assurance):
 * cross-user destructive authorization on POST/GET /api/cockpit/runs.
 *
 * Same root cause as B-001 (GET /api/charts/[id], PR #1597) and B-007
 * (cockpit Clear preview+execute, PR #1602): the handler checked only
 * `getServerUser() !== null` and then trusted the caller-supplied `chart_id`.
 *
 * What made THIS route worse than B-007's pre-fix state: B-007 at least had a
 * `preview_hash` round-trip between "ask" and "delete". `POST /api/cockpit/runs`
 * with `clear_before: true` has NO confirmation gate whatsoever — one request
 * from any authenticated user (default role `guest`) runs
 * `DELETE FROM <target_table> WHERE chart_id=$1` across every build-derived
 * table of a chart they have no relationship to, resets `asset_throughput` to
 * dormant, marks downstream stale, and then dispatches a Cloud Run build job
 * billed against the victim's chart.
 *
 * The non-clear path is a cross-tenant write too: it INSERTs `build_runs` /
 * `build_run_assets` rows for the victim's chart and invokes the job.
 *
 * GET is a cross-chart read disclosure: the last 20 build runs of any chart_id.
 *
 * Fix routes both handlers through the same `authorizeChartAccess` brain used by
 * GET /api/charts/[id] and the Clear routes, via the shared
 * `requireChartPermission` helper. POST requires `permission === 'all'` (owner or
 * super_admin) because dispatching/clearing is destructive — a `chart_grants`
 * 'view' grantee must NOT be able to wipe or spend on someone else's chart. GET
 * requires merely a non-'deny' permission, since reading build history is the
 * kind of read a 'view' grant is meant to cover.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetPool, mockGetServerUser, mockInvokeRunJob, mockGetJobImageTag } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetPool: vi.fn(),
  mockGetServerUser: vi.fn(),
  mockInvokeRunJob: vi.fn(),
  mockGetJobImageTag: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery, getPool: mockGetPool }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/build/jobInvoker', () => ({ invokeRunJob: mockInvokeRunJob }))
vi.mock('@/lib/cloud_run/jobs', () => ({ getJobImageTag: mockGetJobImageTag }))

import { POST, GET } from '../route'
import writerDigestInventory from '@/generated/nirmana-writer-digests.json'

const VICTIM_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const VICTIM_UID = 'victim-uid'
const ATTACKER_UID = 'attacker-uid'
const ADMIN_UID = 'admin-uid'

const DIGESTS = writerDigestInventory.writers as Record<string, string>

/**
 * Two real Kāla writers that carry a real sidecar digest, so the unpatched route
 * gets all the way past the CODE_DIGEST_UNAVAILABLE gate into the clear loop —
 * i.e. the "deny" tests below prove a genuine DELETE was prevented, not merely
 * that some earlier unrelated validation happened to reject the request.
 */
const A1 = 'ka_kshetra'
const A2 = 'ka_avadhi'

const REGISTRY = [
  {
    asset_id: A1, layer: 'kala', depends_on: [], estimated_seconds: 60,
    scope: 'per_chart', has_writer: true, target_table: 'kala_kshetra',
    count_sql: 'SELECT count(*) FROM kala_kshetra WHERE chart_id=$1',
    natural_key_partition: null, asset_kind: 'data', asset_type: 'data', health_probe: null,
  },
  {
    asset_id: A2, layer: 'kala', depends_on: [], estimated_seconds: 90,
    scope: 'per_chart', has_writer: true, target_table: 'kala_avadhi',
    count_sql: 'SELECT count(*) FROM kala_avadhi WHERE chart_id=$1',
    natural_key_partition: null, asset_kind: 'data', asset_type: 'data', health_probe: null,
  },
]

/** Every statement the route issues on a pool client (the destructive path). */
let clientQueries: string[] = []

function makeReq(body: object): NextRequest {
  return new NextRequest('http://localhost/api/cockpit/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function makeGetReq(chartId: string): NextRequest {
  return new NextRequest(`http://localhost/api/cockpit/runs?chart_id=${chartId}`)
}

/**
 * SQL-shape-dispatching mock rather than ordered mockResolvedValueOnce, so the
 * fixture does not need re-sequencing every time an authz query is added.
 */
function setupMocks(opts: {
  uid: string
  role?: string
  ownerId?: string | null
  grantPermission?: string | null
}) {
  const { uid, role = 'guest', ownerId = VICTIM_UID, grantPermission = null } = opts

  mockGetServerUser.mockResolvedValue({ uid })
  mockInvokeRunJob.mockResolvedValue(undefined)
  mockGetJobImageTag.mockResolvedValue('test-tag')

  mockQuery.mockImplementation((sql: string) => {
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
    if (/scope\s+FROM asset_registry/.test(sql)) return Promise.resolve({ rows: [{ scope: 'per_chart' }], rowCount: 1 })
    if (/FROM asset_registry/.test(sql)) return Promise.resolve({ rows: REGISTRY, rowCount: REGISTRY.length })
    if (/FROM build_protected_assets/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM asset_throughput/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM asset_freshness/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM build_runs/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })

  clientQueries = []
  const client = {
    query: vi.fn((sql: string) => {
      clientQueries.push(sql)
      // The build_runs INSERT ... RETURNING id needs a row back.
      if (/INSERT INTO build_runs/.test(sql)) {
        return Promise.resolve({ rows: [{ id: 'run-1' }], rowCount: 1 })
      }
      return Promise.resolve({ rows: [], rowCount: 0 })
    }),
    release: vi.fn(),
  }
  mockGetPool.mockResolvedValue({ connect: vi.fn().mockResolvedValue(client) })
}

const deletesIssued = () => clientQueries.filter(q => /^\s*DELETE/i.test(q))
const runInserts = () => clientQueries.filter(q => /INSERT INTO build_runs/i.test(q))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('POST /api/cockpit/runs — P2-B-008 cross-chart destructive authz', () => {
  it('sanity: the two fixture assets carry real sidecar digests', () => {
    // If this ever fails the deny-tests below would pass for the wrong reason
    // (CODE_DIGEST_UNAVAILABLE short-circuit instead of the authz gate).
    expect(DIGESTS[A1]).toBeTruthy()
    expect(DIGESTS[A2]).toBeTruthy()
  })

  it('(a) DENIES a non-owner guest a clear_before build — and issues NO DELETE', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala',
      action: 'rebuild', clear_before: true,
    }))
    expect(res.status).toBe(403)
    const body = await res.json()
    expect(body.code).toBe('FORBIDDEN_CHART')
    // The real proof: the destructive transaction never opened.
    expect(deletesIssued()).toHaveLength(0)
    expect(mockGetPool).not.toHaveBeenCalled()
    // And no Cloud Run spend was dispatched against the victim's chart.
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('(a2) DENIES a chart_grants view-grantee a clear_before build — a read grant is not a delete grant', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala',
      action: 'rebuild', clear_before: true,
    }))
    expect(res.status).toBe(403)
    expect(deletesIssued()).toHaveLength(0)
    expect(mockGetPool).not.toHaveBeenCalled()
  })

  it('(b) DENIES a non-owner guest a plain (non-clearing) build dispatch', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala', action: 'build',
    }))
    expect(res.status).toBe(403)
    expect((await res.json()).code).toBe('FORBIDDEN_CHART')
    // No build_runs row written for a chart the caller has no relationship to.
    expect(runInserts()).toHaveLength(0)
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('(c) DENIES a caller when the chart does not exist at all', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: null })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala', action: 'build',
    }))
    expect(res.status).toBe(403)
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('(d) ALLOWS the legitimate owner to dispatch a build on their own chart', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala', action: 'build',
    }))
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.data.run_id).toBe('run-1')
    expect(body.data.plan).toEqual(expect.arrayContaining([A1, A2]))
    expect(mockInvokeRunJob).toHaveBeenCalledWith('run-1')
  })

  it('(d2) ALLOWS the owner a clear_before rebuild — the real DELETE path must keep working', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala',
      action: 'rebuild', clear_before: true,
    }))
    expect(res.status).toBe(201)
    expect((await res.json()).data.cleared_asset_count).toBe(2)
    expect(deletesIssued().length).toBeGreaterThan(0)
  })

  it('(d3) ALLOWS super_admin to dispatch on a chart they do not own', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala', action: 'build',
    }))
    expect(res.status).toBe(201)
  })
})

describe('GET /api/cockpit/runs — P2-B-008 cross-chart build-history disclosure', () => {
  it('DENIES a non-owner guest reading another chart\'s build history', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await GET(makeGetReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    const body = await res.json()
    expect(body.data).toBeUndefined()
  })

  it('ALLOWS the owner to read their own build history', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await GET(makeGetReq(VICTIM_CHART))
    expect(res.status).toBe(200)
    expect((await res.json()).data).toEqual([])
  })

  it('ALLOWS a view-grantee to read build history — a read grant covers a read', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await GET(makeGetReq(VICTIM_CHART))
    expect(res.status).toBe(200)
  })
})

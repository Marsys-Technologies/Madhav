/**
 * FIX2 (portal Rebuild): POST /api/cockpit/runs
 *  (a) any run that follows a clear must FORCE execution (no delta-skip onto an empty table);
 *  (b) a global asset must never be cleared from a chart page;
 *  (c) every refusal explains itself in plain words.
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
const OWNER_UID = 'victim-uid'
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

const G1 = 'mi_kula' // real global writer (mimamsa, scope=global)
const PC = 'mi_abhilekha' // real per-chart writer in the same layer

const REGISTRY = [
  {
    asset_id: A1, layer: 'kala', depends_on: [], estimated_seconds: 60,
    scope: 'per_chart', has_writer: true, target_table: 'kala_kshetra',
    count_sql: 'SELECT count(*) FROM kala_kshetra WHERE chart_id=$1',
    natural_key_partition: null, asset_kind: 'data', asset_type: 'data', health_probe: null,
  },
  {
    asset_id: PC, layer: 'mimamsa', depends_on: [], estimated_seconds: 60,
    scope: 'per_chart', has_writer: true, target_table: 'mimamsa_journal',
    count_sql: null,
    natural_key_partition: null, asset_kind: 'data', asset_type: 'data', health_probe: null,
  },
  {
    asset_id: G1, layer: 'mimamsa', depends_on: [], estimated_seconds: 60,
    scope: 'global', has_writer: true, target_table: 'mimamsa_signal_families',
    count_sql: null,
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
  const { uid, role = 'guest', ownerId = OWNER_UID, grantPermission = null } = opts

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

describe('FIX2 (a): a clear forces execution', () => {
  it('clear_before on a per-chart asset dispatches with forceExecute and issues the DELETE', async () => {
    setupMocks({ uid: OWNER_UID, ownerId: OWNER_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'asset_set', scope_target: A1, action: 'rebuild', clear_before: true,
    }))
    expect(res.status).toBe(201)
    expect(deletesIssued().length).toBeGreaterThan(0)
    expect(mockInvokeRunJob).toHaveBeenCalledWith('run-1', { forceExecute: true })
  })

  it('a layer clear_before rebuild is forced too', async () => {
    setupMocks({ uid: OWNER_UID, ownerId: OWNER_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala', action: 'rebuild', clear_before: true,
    }))
    expect(res.status).toBe(201)
    expect(mockInvokeRunJob).toHaveBeenCalledWith('run-1', { forceExecute: true })
  })

  it('the second leg of the two-step Rebuild (clear/execute, THEN a run with no clear_before) is also forced', async () => {
    setupMocks({ uid: OWNER_UID, ownerId: OWNER_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'global', scope_target: null, action: 'rebuild',
    }))
    expect(res.status).toBe(201)
    expect(mockInvokeRunJob).toHaveBeenCalledWith('run-1', { forceExecute: true })
  })

  it('a plain Build (no clear, not a rebuild) is NOT forced: delta-skip stays available', async () => {
    setupMocks({ uid: OWNER_UID, ownerId: OWNER_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala', action: 'build',
    }))
    expect(res.status).toBe(201)
    expect(mockInvokeRunJob).toHaveBeenCalledWith('run-1')
  })
})

describe('FIX2 (b)(c): a global asset is never cleared from a chart page', () => {
  it('REFUSES clear_before on an asset_set naming a global asset (super_admin too), in plain words, with no DELETE and no dispatch', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: OWNER_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'asset_set', scope_target: `${PC},${G1}`, action: 'rebuild', clear_before: true,
    }))
    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.code).toBe('GLOBAL_CLEAR_FORBIDDEN')
    expect(body.error).toMatch(/shared by every chart/i)
    expect(body.error).toContain(G1)
    expect(deletesIssued()).toHaveLength(0)
    expect(runInserts()).toHaveLength(0)
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('REFUSES the L0 brahmagyan layer clear for super_admin: no 202 double-confirm any more', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: OWNER_UID })
    for (const extra of [{}, { force_l0: true }]) {
      const res = await POST(makeReq({
        chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'brahmagyan', action: 'rebuild', clear_before: true, ...extra,
      }))
      expect(res.status).toBe(422)
      const body = await res.json()
      expect(body.code).toBe('GLOBAL_CLEAR_FORBIDDEN')
      expect(body.error).toMatch(/shared by every chart/i)
    }
    expect(deletesIssued()).toHaveLength(0)
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('a mixed layer clear by super_admin deletes only per-chart tables and leaves the global table alone', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: OWNER_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'mimamsa', action: 'rebuild', clear_before: true,
    }))
    expect(res.status).toBe(201)
    const deletes = deletesIssued().join('\n')
    expect(deletes).toMatch(/DELETE FROM mimamsa_/)
    expect(deletes).not.toContain('mimamsa_signal_families')
    // No chart-unfiltered DELETE of any kind was issued.
    for (const d of deletesIssued()) expect(d).toMatch(/WHERE/i)
    expect((await res.json()).data.cleared_asset_count).toBe(1)
    expect(mockInvokeRunJob).toHaveBeenCalledWith('run-1', { forceExecute: true })
  })

  it('a chart-scoped clear of a per-chart asset stays allowed', async () => {
    setupMocks({ uid: OWNER_UID, ownerId: OWNER_UID })
    const res = await POST(makeReq({
      chart_id: VICTIM_CHART, scope: 'asset_set', scope_target: PC, action: 'rebuild', clear_before: true,
    }))
    expect(res.status).toBe(201)
    expect(deletesIssued().length).toBeGreaterThan(0)
  })
})

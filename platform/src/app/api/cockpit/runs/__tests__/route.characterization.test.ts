/**
 * POST /api/cockpit/runs — characterization before the shared build-service
 * extraction (Jātaka chart workspace, Task 5).
 *
 * Locks the cockpit's current HTTP contract and mutations so moving plan,
 * manifest, persistence, clearing and dispatch into lib/build services cannot
 * silently change operator behaviour. In particular the operator clear path
 * stays savepoint-based best effort; only the new chart-correction path is
 * strict.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
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

import { POST } from '../route'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const OWNER = 'owner-uid'

// Two real per-chart writers with sidecar digests in the generated inventory.
const REGISTRY = [
  {
    asset_id: 'ka_kshetra', layer: 'kala', depends_on: [], estimated_seconds: 60,
    scope: 'per_chart', has_writer: true, target_table: 'kala_kshetra',
    count_sql: 'SELECT count(*) FROM kala_kshetra WHERE chart_id=$1',
    natural_key_partition: null, asset_kind: 'data', asset_type: 'data', health_probe: null,
  },
  {
    asset_id: 'ka_avadhi', layer: 'kala', depends_on: [], estimated_seconds: 90,
    scope: 'per_chart', has_writer: true, target_table: 'kala_avadhi',
    count_sql: 'SELECT count(*) FROM kala_avadhi WHERE chart_id=$1',
    natural_key_partition: null, asset_kind: 'data', asset_type: 'data', health_probe: null,
  },
]

interface Harness {
  role?: string
  ownerId?: string
  grant?: string | null
  activeRunId?: string | null
  protectedIds?: string[]
  throughput?: Array<{ asset_id: string; state: string }>
  freshness?: Array<{ asset_id: string; state: string; reasons: string[] }>
  failClientSql?: RegExp
  registry?: Array<Omit<(typeof REGISTRY)[number], 'depends_on'> & { depends_on: string[] }>
}

let clientSql: string[] = []
let clientCalls: Array<{ sql: string; params: unknown[] }> = []
let poolSql: string[] = []

function setup(h: Harness = {}) {
  const { role = 'guest', ownerId = OWNER, grant = null, activeRunId = null } = h
  mockGetServerUser.mockResolvedValue({ uid: OWNER })
  mockInvokeRunJob.mockResolvedValue({ executionName: 'exec-1' })
  mockGetJobImageTag.mockResolvedValue('tag-1')
  poolSql = []
  mockQuery.mockImplementation((sql: string) => {
    poolSql.push(sql)
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }] })
    if (/FROM chart_grants/.test(sql)) return Promise.resolve({ rows: grant ? [{ permission: grant }] : [] })
    if (/owner_id[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ owner_id: ownerId }] })
    if (/FROM asset_registry/.test(sql)) return Promise.resolve({ rows: h.registry ?? REGISTRY })
    if (/FROM build_protected_assets/.test(sql)) return Promise.resolve({ rows: (h.protectedIds ?? []).map((asset_id) => ({ asset_id })) })
    if (/FROM asset_throughput/.test(sql)) return Promise.resolve({ rows: h.throughput ?? [] })
    if (/FROM asset_freshness/.test(sql)) return Promise.resolve({ rows: h.freshness ?? [] })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
  clientSql = []
  clientCalls = []
  const client = {
    query: vi.fn((sql: string, params: unknown[] = []) => {
      clientSql.push(sql)
      clientCalls.push({ sql, params })
      if (h.failClientSql?.test(sql)) return Promise.reject(new Error(`boom: ${sql.slice(0, 30)}`))
      if (/SELECT id FROM build_runs/.test(sql)) return Promise.resolve({ rows: activeRunId ? [{ id: activeRunId }] : [] })
      if (/INSERT INTO build_runs/.test(sql)) return Promise.resolve({ rows: [{ id: 'run-1' }], rowCount: 1 })
      return Promise.resolve({ rows: [], rowCount: 0 })
    }),
    release: vi.fn(),
  }
  mockGetPool.mockResolvedValue({ connect: vi.fn().mockResolvedValue(client) })
}

function req(body: object) {
  return new NextRequest('http://localhost/api/cockpit/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

const LAYER_BUILD = { chart_id: CHART, scope: 'layer', scope_target: 'kala', action: 'build' }
const LAYER_REBUILD_CLEAR = { chart_id: CHART, scope: 'layer', scope_target: 'kala', action: 'rebuild', clear_before: true }

const touched = (re: RegExp) => [...poolSql, ...clientSql].some((s) => re.test(s))

beforeEach(() => vi.clearAllMocks())

describe('cockpit runs characterization — authority', () => {
  it('a view-only grantee causes no registry read, clear, run insert or dispatch', async () => {
    setup({ ownerId: 'someone-else', grant: 'view' })
    const res = await POST(req(LAYER_REBUILD_CLEAR))
    expect(res.status).toBe(403)
    expect(touched(/FROM asset_registry/)).toBe(false)
    expect(touched(/^\s*DELETE/i)).toBe(false)
    expect(touched(/INSERT INTO build_runs/)).toBe(false)
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })
})

describe('cockpit runs characterization — gates', () => {
  it('an active run returns 409 RUN_ACTIVE with its id and mutates nothing', async () => {
    setup({ activeRunId: 'run-live' })
    const res = await POST(req(LAYER_BUILD))
    expect(res.status).toBe(409)
    expect(await res.json()).toMatchObject({ code: 'RUN_ACTIVE', existing_run_id: 'run-live' })
    expect(touched(/INSERT INTO build_runs/)).toBe(false)
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('a protected-only plan returns 422 PROTECTED', async () => {
    setup({ protectedIds: ['ka_kshetra', 'ka_avadhi'] })
    const res = await POST(req(LAYER_BUILD))
    expect(res.status).toBe(422)
    expect((await res.json()).code).toBe('PROTECTED')
    expect(touched(/INSERT INTO build_runs/)).toBe(false)
  })

  it('an out-of-plan stale upstream returns 422 UPSTREAM_BLOCKED', async () => {
    setup({ protectedIds: [], throughput: [], freshness: [] })
    mockQuery.mockImplementation((sql: string) => {
      poolSql.push(sql)
      if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'guest' }] })
      if (/owner_id[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ owner_id: OWNER }] })
      if (/FROM asset_registry/.test(sql)) {
        return Promise.resolve({
          rows: [
            { ...REGISTRY[0], asset_id: 'ga_positions', layer: 'ganita' },
            { ...REGISTRY[1], depends_on: ['ga_positions'] },
          ],
        })
      }
      if (/FROM asset_throughput/.test(sql)) return Promise.resolve({ rows: [{ asset_id: 'ga_positions', state: 'error' }] })
      return Promise.resolve({ rows: [] })
    })
    const res = await POST(req({ chart_id: CHART, scope: 'asset', scope_target: 'ka_avadhi', action: 'build' }))
    expect(res.status).toBe(422)
    expect((await res.json()).code).toBe('UPSTREAM_BLOCKED')
    expect(touched(/INSERT INTO build_runs/)).toBe(false)
  })
})

describe('cockpit runs characterization — persistence and clearing', () => {
  it('persists the run and every queued asset in one transaction, then dispatches', async () => {
    setup()
    const res = await POST(req(LAYER_BUILD))
    expect(res.status).toBe(201)
    const begin = clientSql.findIndex((s) => /^BEGIN$/.test(s.trim()))
    const run = clientSql.findIndex((s) => /INSERT INTO build_runs/.test(s))
    const assets = clientSql.findIndex((s) => /INSERT INTO build_run_assets/.test(s))
    const commit = clientSql.lastIndexOf('COMMIT')
    expect(begin).toBeGreaterThanOrEqual(0)
    expect(begin).toBeLessThan(run)
    expect(run).toBeLessThan(assets)
    expect(assets).toBeLessThan(commit)
    expect(mockInvokeRunJob).toHaveBeenCalledWith('run-1')
  })

  it('rolls back and never dispatches when the run-assets insert fails', async () => {
    setup({ failClientSql: /INSERT INTO build_run_assets/ })
    await expect(POST(req(LAYER_BUILD))).rejects.toThrow(/boom/)
    const afterInsert = clientSql.slice(clientSql.findIndex((s) => /INSERT INTO build_runs/.test(s)))
    expect(afterInsert).toContain('ROLLBACK')
    expect(afterInsert).not.toContain('COMMIT')
    expect(mockInvokeRunJob).not.toHaveBeenCalled()
  })

  it('uses only successful DELETEs for reset, causal staleness and reported count', async () => {
    const dep = (asset_id: string, depends_on: string[]) => ({
      ...REGISTRY[0], asset_id, layer: 'fixture-other-layer', depends_on,
    })
    setup({ failClientSql: /DELETE FROM kala_avadhi/, registry: [
      REGISTRY[0], REGISTRY[1],
      dep('fixture_failed_only', ['ka_avadhi']),
      dep('fixture_shared', ['ka_avadhi', 'ka_kshetra']),
      dep('fixture_transitive', ['fixture_shared']),
      { ...REGISTRY[0], asset_id: 'fixture_global', scope: 'global', target_table: 'fixture_global' },
    ] })
    const res = await POST(req(LAYER_REBUILD_CLEAR))
    expect(res.status).toBe(201)
    expect(clientSql.some(s => /^SAVEPOINT cb_\d+$/.test(s))).toBe(true)
    expect(clientSql.some(s => /^ROLLBACK TO SAVEPOINT cb_\d+$/.test(s))).toBe(true)
    expect(clientSql.some(s => /INSERT INTO build_runs/.test(s))).toBe(true)
    expect(clientSql).toContain('COMMIT')
    expect(clientCalls.find(call => call.sql.includes("SET state='dormant'"))?.params)
      .toEqual([CHART, ['ka_kshetra']])
    const stale = clientCalls.find(call => call.sql.includes("SET state='stale'"))?.params
    expect(stale?.[0]).toBe(CHART)
    expect(stale?.[1]).toEqual(expect.arrayContaining(['fixture_shared','fixture_transitive']))
    expect(stale?.[1]).toHaveLength(2)
    expect((await res.json()).data).toMatchObject({
      cleared_asset_count: 1, failed_clear_asset_ids: ['ka_avadhi'], global_assets_not_cleared: ['fixture_global'],
    })
    expect(touched(/^DELETE FROM fixture_global/)).toBe(false)
    expect(mockInvokeRunJob).toHaveBeenCalledExactlyOnceWith('run-1', { forceExecute: true })
  })

  it('all failed keeps the allowed planned dispatch, with zero cleared and no throughput mutations', async () => {
    setup({ failClientSql: /^DELETE/ })
    const res = await POST(req(LAYER_REBUILD_CLEAR))
    expect(res.status).toBe(201)
    expect((await res.json()).data).toMatchObject({
      cleared_asset_count: 0, failed_clear_asset_ids: ['ka_avadhi','ka_kshetra'],
    })
    expect(touched(/UPDATE asset_throughput/)).toBe(false)
    expect(mockInvokeRunJob).toHaveBeenCalledExactlyOnceWith('run-1', { forceExecute: true })
  })

  it('traverses a selected failed dependant without marking the selected failed row stale', async () => {
    setup({ failClientSql: /DELETE FROM kala_avadhi/, registry: [
      REGISTRY[0], { ...REGISTRY[1], depends_on: ['ka_kshetra'] },
      { ...REGISTRY[0], asset_id: 'fixture_beyond_selected', layer: 'fixture-other-layer', depends_on: ['ka_avadhi'] },
    ] })
    expect((await POST(req(LAYER_REBUILD_CLEAR))).status).toBe(201)
    expect(clientCalls.find(call => call.sql.includes("SET state='stale'"))?.params)
      .toEqual([CHART, ['fixture_beyond_selected']])
  })

  it('successful zero-row statements count, explicit append-only no-op does not', async () => {
    setup({ registry: [...REGISTRY, {
      ...REGISTRY[0], asset_id: 'mi_bhavisya', target_table: 'fixture_never_delete',
    }] })
    const res = await POST(req(LAYER_REBUILD_CLEAR))
    expect(res.status).toBe(201)
    const { data } = await res.json()
    expect(data.cleared_asset_count).toBe(2)
    expect(data.failed_clear_asset_ids).toBeUndefined()
    expect(data.notices).toEqual([expect.objectContaining({ assetId: 'mi_bhavisya' })])
    expect(touched(/^DELETE FROM fixture_never_delete/)).toBe(false)
    expect(clientCalls.find(call => call.sql.includes("SET state='dormant'"))?.params)
      .toEqual([CHART, ['ka_avadhi','ka_kshetra']])
  })
})

describe('cockpit runs characterization — dispatch failure', () => {
  it('all-failed clear dispatch failure keeps 503 and never claims data was cleared', async () => {
    setup({ failClientSql: /^DELETE/ })
    mockInvokeRunJob.mockRejectedValue(new Error('fixture dispatch refused'))
    const res = await POST(req(LAYER_REBUILD_CLEAR))
    expect(res.status).toBe(503)
    expect(await res.json()).toMatchObject({
      error: 'Build job failed to start', code: 'JOB_DISPATCH_FAILED', run_id: 'run-1',
      failed_clear_asset_ids: ['ka_avadhi','ka_kshetra'],
    })
    expect(touched(/UPDATE asset_throughput/)).toBe(false)
    expect(clientSql).toContain('COMMIT')
    expect(mockInvokeRunJob).toHaveBeenCalledExactlyOnceWith('run-1', { forceExecute: true })
  })

  it('non-clearing path: run failed with the raw error, queued assets aborted, HTTP 503', async () => {
    setup()
    mockInvokeRunJob.mockRejectedValue(new Error('cloud run down'))
    const res = await POST(req(LAYER_BUILD))
    expect(res.status).toBe(503)
    expect(await res.json()).toMatchObject({ run_id: 'run-1', detail: 'cloud run down' })
    // A2: one shared statement (terminalizeFailedRun) fails the run and aborts its queued assets,
    // binding the same raw error text to both build_runs.last_error and build_run_assets.error.
    const failCall = mockQuery.mock.calls.find(([s]) => /UPDATE build_runs\s+SET state = 'failed'/.test(s))
    expect(failCall?.[1]).toEqual(['cloud run down', 'run-1'])
    expect(/SET state = 'aborted'[^]*error = \$1/.test(String(failCall?.[0])) && /state = 'queued'/.test(String(failCall?.[0]))).toBe(true)
  })

  it('clearing path: 503 JOB_DISPATCH_FAILED carries the run id and records the raw error', async () => {
    setup()
    mockInvokeRunJob.mockRejectedValue(new Error('spawn failed'))
    const res = await POST(req(LAYER_REBUILD_CLEAR))
    expect(res.status).toBe(503)
    expect(await res.json()).toMatchObject({ code: 'JOB_DISPATCH_FAILED', run_id: 'run-1' })
    const failCall = mockQuery.mock.calls.find(([s]) => /UPDATE build_runs\s+SET state = 'failed'/.test(s))
    expect(failCall?.[1]).toEqual(['spawn failed', 'run-1'])
  })
})

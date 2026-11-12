/**
 * ga_fact_identity Clear at the execute route (POST /api/cockpit/clear/execute).
 *
 * chart_fact_identity (the Fact Identity Index) is built by the REGISTERED writer ga_fact_identity since
 * migration 1333, so a Clear of it is a rebuildable-cache clear (before 1333 it was an explicit null: the
 * hand-run G-IDX script could not be run by a build). A layer, global or asset Clear must issue EXACTLY ONE
 * chart-scoped DELETE against chart_fact_identity (bound to the chart), and a sibling asset in the same
 * scope is still cleared (so the test is not vacuous).
 *
 * The FK chart_fact_identity.fact_id -> chart_facts ON DELETE CASCADE (migration 552) is kept on purpose; this
 * file asserts only what the Clear itself issues.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'
import { createHash } from 'crypto'

const { mockQuery, mockGetPool, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetPool: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery, getPool: mockGetPool }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { POST as EXECUTE } from '../execute/route'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const OWNER_UID = 'owner-uid'
const ADMIN_UID = 'admin-uid'

// Registry rows as migration 1262 would add them (count_sql verbatim), plus a control sibling.
const REGISTRY = [
  {
    asset_id: 'ga_control', layer: 'ganita', depends_on: [], estimated_seconds: 60,
    scope: 'per_chart', target_table: 'ga_control_table',
    count_sql: 'SELECT count(*) FROM ga_control_table WHERE chart_id = $1',
    english_name: 'Control', sanskrit_name: 'Control',
  },
  {
    asset_id: 'ga_fact_identity', layer: 'ganita', depends_on: [], estimated_seconds: 0,
    scope: 'per_chart', target_table: 'chart_fact_identity',
    count_sql: 'SELECT count(*) FROM chart_fact_identity WHERE chart_id = $1',
    english_name: 'Fact Identity Index', sanskrit_name: 'Fact Identity Index',
  },
]

let clientQueries: string[] = []
let clientCalls: Array<{ sql: string; params: unknown[] }> = []

function makeReq(body: object): NextRequest {
  return new NextRequest('http://localhost/api/cockpit/clear/execute', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
}

function previewHash(scope: string, scope_target: string | null, affected: string[]): string {
  const timeSlot = Math.floor(Date.now() / (15 * 60 * 1000))
  return createHash('sha256')
    .update(JSON.stringify({ chart_id: CHART, scope, scope_target, affectedAssetIds: [...affected].sort(), timeSlot }))
    .digest('hex').slice(0, 32)
}

function setupMocks(role: 'client' | 'super_admin', options: {
  registry?: Array<Omit<(typeof REGISTRY)[number], 'depends_on'> & { depends_on: string[] }>; failDelete?: RegExp; rowCount?: number
} = {}) {
  const registry = options.registry ?? REGISTRY
  const uid = role === 'super_admin' ? ADMIN_UID : OWNER_UID
  mockGetServerUser.mockResolvedValue({ uid })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }], rowCount: 1 })
    if (/owner_id[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ owner_id: OWNER_UID }], rowCount: 1 })
    if (/subject_name[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ subject_name: 'Native', name: 'Native' }], rowCount: 1 })
    if (/FROM asset_registry WHERE asset_id/.test(sql)) return Promise.resolve({ rows: [{ scope: 'per_chart' }], rowCount: 1 })
    if (/FROM asset_registry/.test(sql)) return Promise.resolve({ rows: registry, rowCount: registry.length })
    if (/FROM build_protected_assets/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
  clientQueries = []
  clientCalls = []
  const client = {
    query: vi.fn((sql: string, params: unknown[] = []) => {
      clientQueries.push(sql)
      clientCalls.push({ sql, params })
      if (options.failDelete?.test(sql)) return Promise.reject(new Error('fixture private SQL detail'))
      return Promise.resolve({ rows: [], rowCount: options.rowCount ?? 2 })
    }),
    release: vi.fn(),
  }
  mockGetPool.mockResolvedValue({ connect: vi.fn().mockResolvedValue(client) })
}

const identityStatements = () => clientQueries.filter(q => /chart_fact_identity/i.test(q))
const deletesOf = (table: string) =>
  clientQueries.filter(q => new RegExp(`^\\s*(DELETE\\s+FROM|TRUNCATE)\\b[\\s\\S]*\\b${table}\\b`, 'i').test(q))

beforeEach(() => { vi.clearAllMocks() })

describe('POST /api/cockpit/clear/execute - chart_fact_identity is cleared by exactly one chart-scoped DELETE', () => {
  it('a LAYER Clear deletes the sibling AND issues exactly one chart-scoped DELETE against chart_fact_identity', async () => {
    setupMocks('client')
    const res = await EXECUTE(makeReq({
      chart_id: CHART, scope: 'layer', scope_target: 'ganita',
      preview_hash: previewHash('layer', 'ganita', ['ga_control', 'ga_fact_identity']),
    }))
    expect(res.status).toBe(200)
    expect(deletesOf('ga_control_table')).toHaveLength(1) // control: the clear really ran
    expect(identityStatements()).toEqual(['DELETE FROM chart_fact_identity WHERE chart_id = $1'])
  })

  it('a GLOBAL Clear (super_admin) issues exactly one chart-scoped DELETE against chart_fact_identity', async () => {
    setupMocks('super_admin')
    const res = await EXECUTE(makeReq({
      chart_id: CHART, scope: 'global', scope_target: null, typed_confirmation: 'Native',
      preview_hash: previewHash('global', null, ['ga_control', 'ga_fact_identity']),
    }))
    expect(res.status).toBe(200)
    expect(deletesOf('ga_control_table')).toHaveLength(1)
    expect(identityStatements()).toEqual(['DELETE FROM chart_fact_identity WHERE chart_id = $1'])
  })

  it('an ASSET Clear targeting ga_fact_identity itself issues exactly that one DELETE and nothing else', async () => {
    setupMocks('client')
    const res = await EXECUTE(makeReq({
      chart_id: CHART, scope: 'asset', scope_target: 'ga_fact_identity',
      preview_hash: previewHash('asset', 'ga_fact_identity', ['ga_fact_identity']),
    }))
    expect(res.status).toBe(200)
    expect(identityStatements()).toEqual(['DELETE FROM chart_fact_identity WHERE chart_id = $1'])
    expect(clientQueries.filter(q => /^\s*DELETE\b/i.test(q))).toEqual(['DELETE FROM chart_fact_identity WHERE chart_id = $1'])
  })
})


describe('true Clear reports and propagates only successful assets', () => {
  const request = () => makeReq({
    chart_id: CHART, scope: 'layer', scope_target: 'ganita',
    preview_hash: previewHash('layer', 'ganita', ['ga_control','ga_fact_identity']),
  })
  const downstream = (asset_id: string, depends_on: string[]) => ({
    ...REGISTRY[0], asset_id, layer: 'fixture-other-layer', depends_on,
  })
  it('excludes the failed-only branch and keeps a shared transitive dependant', async () => {
    setupMocks('client', { rowCount: 0, failDelete: /^DELETE FROM chart_fact_identity/,
      registry: [...REGISTRY, downstream('fixture_failed_only', ['ga_fact_identity']),
        downstream('fixture_shared', ['ga_control','ga_fact_identity']),
        downstream('fixture_transitive', ['fixture_shared']),
        { ...REGISTRY[0], asset_id: 'fixture_global', scope: 'global', target_table: 'fixture_global' }],
    })
    const res = await EXECUTE(request())
    expect(res.status).toBe(200)
    expect(await res.json()).toMatchObject({
      cleared: { assets: 1, ops: 1, rows: 0, downstream_stale: 2 },
      failed_tables: [{ table: 'ga_fact_identity', error: 'The asset could not be cleared.' }],
    })
    expect(clientQueries.some(sql => /^ROLLBACK TO SAVEPOINT clr_/.test(sql))).toBe(true)
    expect(clientCalls.find(call => call.sql.includes("SET state='dormant'"))?.params).toEqual([CHART, ['ga_control']])
    const stale = clientCalls.find(call => call.sql.includes("SET state='stale'"))?.params
    expect(stale?.[0]).toBe(CHART)
    expect(stale?.[1]).toEqual(expect.arrayContaining(['fixture_shared','fixture_transitive']))
    expect(stale?.[1]).toHaveLength(2)
    expect(deletesOf('fixture_global')).toEqual([])
    expect(clientQueries).toContain('COMMIT')
    expect(clientQueries.some(sql => /INSERT INTO build_run/.test(sql))).toBe(false)
  })

  it('all failed commits the empty best-effort transaction and changes no throughput', async () => {
    setupMocks('client', { failDelete: /^DELETE/ })
    const res = await EXECUTE(request())
    expect(res.status).toBe(200)
    expect(await res.json()).toMatchObject({
      cleared: { assets: 0, ops: 0, rows: 0, downstream_stale: 0 },
      failed_tables: [{ table: 'ga_fact_identity' },{ table: 'ga_control' }],
    })
    expect(clientQueries.some(sql => /UPDATE asset_throughput/.test(sql))).toBe(false)
    expect(clientQueries).toContain('COMMIT')
  })
})

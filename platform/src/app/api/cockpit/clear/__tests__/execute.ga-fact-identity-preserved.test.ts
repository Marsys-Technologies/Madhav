/**
 * ga_fact_identity Clear at the execute route (POST /api/cockpit/clear/execute).
 *
 * chart_fact_identity (the Fact Identity Index) is filled by a hand-run script, not a build
 * writer, so a Clear that deleted it could not be undone by any build (migration 1262 CLEAR
 * note). ga_fact_identity is an explicit null in EXPLICIT_CLEAR_OPS: a layer, global or asset
 * Clear must issue NO statement against chart_fact_identity, while a sibling asset in the same
 * scope is still cleared (so the test is not vacuous).
 *
 * KNOWN RESIDUAL: chart_fact_identity.fact_id references chart_facts ON DELETE CASCADE (migration 552),
 * so a Clear that deletes chart_facts rows still empties the index for those facts; this file asserts
 * only that no statement of the Clear names chart_fact_identity.
 *
 * The "nothing cleared" operator message channel for null specs comes from #3040
 * (mi_bhavisya append-only); this file pins only the no-DELETE guarantee.
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

function setupMocks(role: 'client' | 'super_admin') {
  const uid = role === 'super_admin' ? ADMIN_UID : OWNER_UID
  mockGetServerUser.mockResolvedValue({ uid })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }], rowCount: 1 })
    if (/owner_id[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ owner_id: OWNER_UID }], rowCount: 1 })
    if (/subject_name[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ subject_name: 'Native', name: 'Native' }], rowCount: 1 })
    if (/FROM asset_registry WHERE asset_id/.test(sql)) return Promise.resolve({ rows: [{ scope: 'per_chart' }], rowCount: 1 })
    if (/FROM asset_registry/.test(sql)) return Promise.resolve({ rows: REGISTRY, rowCount: REGISTRY.length })
    if (/FROM build_protected_assets/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
  clientQueries = []
  const client = {
    query: vi.fn((sql: string) => { clientQueries.push(sql); return Promise.resolve({ rows: [], rowCount: 2 }) }),
    release: vi.fn(),
  }
  mockGetPool.mockResolvedValue({ connect: vi.fn().mockResolvedValue(client) })
}

const deletesOf = (table: string) =>
  clientQueries.filter(q => new RegExp(`^\\s*(DELETE\\s+FROM|TRUNCATE)\\b[\\s\\S]*\\b${table}\\b`, 'i').test(q))

beforeEach(() => { vi.clearAllMocks() })

describe('POST /api/cockpit/clear/execute - chart_fact_identity is never DIRECTLY deleted', () => {
  it('a LAYER Clear of the layer deletes the sibling but issues no statement against chart_fact_identity', async () => {
    setupMocks('client')
    const res = await EXECUTE(makeReq({
      chart_id: CHART, scope: 'layer', scope_target: 'ganita',
      preview_hash: previewHash('layer', 'ganita', ['ga_control', 'ga_fact_identity']),
    }))
    expect(res.status).toBe(200)
    expect(deletesOf('ga_control_table')).toHaveLength(1) // control: the clear really ran
    expect(clientQueries.filter(q => /chart_fact_identity/i.test(q))).toEqual([])
  })

  it('a GLOBAL Clear (super_admin) issues no statement against chart_fact_identity', async () => {
    setupMocks('super_admin')
    const res = await EXECUTE(makeReq({
      chart_id: CHART, scope: 'global', scope_target: null, typed_confirmation: 'Native',
      preview_hash: previewHash('global', null, ['ga_control', 'ga_fact_identity']),
    }))
    expect(res.status).toBe(200)
    expect(deletesOf('ga_control_table')).toHaveLength(1)
    expect(clientQueries.filter(q => /chart_fact_identity/i.test(q))).toEqual([])
  })

  it('an ASSET Clear targeting ga_fact_identity itself issues no statement against it', async () => {
    setupMocks('client')
    const res = await EXECUTE(makeReq({
      chart_id: CHART, scope: 'asset', scope_target: 'ga_fact_identity',
      preview_hash: previewHash('asset', 'ga_fact_identity', ['ga_fact_identity']),
    }))
    expect(res.status).toBe(200)
    expect(clientQueries.filter(q => /chart_fact_identity/i.test(q))).toEqual([])
    expect(clientQueries.filter(q => /^\s*DELETE\b/i.test(q))).toEqual([])
  })
})

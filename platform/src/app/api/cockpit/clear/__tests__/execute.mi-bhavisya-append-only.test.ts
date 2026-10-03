/**
 * mi_bhavisya Clear at the execute route (POST /api/cockpit/clear/execute) - SS N-104.
 *
 * mimamsa_predictions / mimamsa_manifestation_sets are append-only calibration history, so the
 * asset's clear is an explicit null: NO statement is issued. A silent skip would let an operator
 * believe something was cleared, so the route returns an explicit notice, and the asset's
 * throughput row is NOT reset to dormant (nothing was cleared, the data is still there).
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

const REGISTRY = [
  {
    asset_id: 'mi_bhavisya', layer: 'mimamsa', depends_on: [], estimated_seconds: 60,
    scope: 'per_chart', target_table: 'mimamsa_predictions',
    count_sql: 'SELECT (SELECT count(*) FROM mimamsa_predictions WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_manifestation_sets WHERE chart_id = $1) AS count',
    english_name: 'Bhavisya', sanskrit_name: 'Bhavisya',
  },
]

let clientQueries: string[] = []

function makeReq(body: object): NextRequest {
  return new NextRequest('http://localhost/api/cockpit/clear/execute', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
}

function previewHash(affected: string[]): string {
  const timeSlot = Math.floor(Date.now() / (15 * 60 * 1000))
  return createHash('sha256')
    .update(JSON.stringify({ chart_id: CHART, scope: 'asset', scope_target: 'mi_bhavisya', affectedAssetIds: [...affected].sort(), timeSlot }))
    .digest('hex').slice(0, 32)
}

function setupMocks() {
  mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'client' }], rowCount: 1 })
    if (/owner_id[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ owner_id: OWNER_UID }], rowCount: 1 })
    if (/FROM asset_registry/.test(sql)) return Promise.resolve({ rows: REGISTRY, rowCount: 1 })
    if (/FROM build_protected_assets/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
  clientQueries = []
  const client = {
    query: vi.fn((sql: string) => { clientQueries.push(sql); return Promise.resolve({ rows: [], rowCount: 3 }) }),
    release: vi.fn(),
  }
  mockGetPool.mockResolvedValue({ connect: vi.fn().mockResolvedValue(client) })
}

beforeEach(() => { vi.clearAllMocks() })

describe('POST /api/cockpit/clear/execute - mi_bhavisya is append-only (SS N-104)', () => {
  it('returns the explicit message and issues no DELETE/UPDATE/INSERT against the frozen tables', async () => {
    setupMocks()
    const res = await EXECUTE(makeReq({
      chart_id: CHART, scope: 'asset', scope_target: 'mi_bhavisya', preview_hash: previewHash(['mi_bhavisya']),
    }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.notices).toEqual([{ asset_id: 'mi_bhavisya', message: 'mi_bhavisya is append-only (N-104): nothing cleared' }])
    expect(body.failed_tables).toBeUndefined()
    expect(body.cleared.ops).toBe(0)
    expect(body.cleared.rows).toBe(0)
    // not a single statement names the two tables, and the registry-derived fallback DELETE never runs
    expect(clientQueries.filter(q => /mimamsa_(predictions|manifestation_sets)/i.test(q))).toEqual([])
    expect(clientQueries.filter(q => /^\s*(DELETE|TRUNCATE)\b/i.test(q))).toEqual([])
  })

  it('does not reset the asset to dormant: nothing was cleared, so its throughput must not say so', async () => {
    setupMocks()
    await EXECUTE(makeReq({
      chart_id: CHART, scope: 'asset', scope_target: 'mi_bhavisya', preview_hash: previewHash(['mi_bhavisya']),
    }))
    expect(clientQueries.filter(q => /UPDATE asset_throughput\s+SET state='dormant'/i.test(q))).toEqual([])
  })
})

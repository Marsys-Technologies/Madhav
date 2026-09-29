/**
 * WP7 packet C-1 — EXPLICIT_CLEAR_OPS['ka_gochara'] refusal guard at the execute
 * route (POST /api/cockpit/clear/execute).
 *
 * Covers the packet §5 acceptance rows implementable at the route level:
 *   (a) chart-owner Clear when '4.0' IS the authoritative generation → REFUSED,
 *       no statements run, failed_tables carries the refusal message;
 *   (b) release-authority (super_admin) Clear of the authoritative generation →
 *       the three DELETEs run PLUS the cascade (authority reset + manifest
 *       'cleared') inside the same per-asset SAVEPOINT;
 *   (c) chart whose authority is '3.0' → the '4.0' Clear proceeds, no cascade;
 *   (d) the explicit entry takes precedence over count_sql for ka_gochara.
 *
 * Rows of §5 that need a live disposable DB (zero-rows verification, conjunct
 * (k), the P-1d unpublished hand-off) are covered by the WP6/Python integration
 * harness and are recorded in the packet's REVIEW_REQUEST note.
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

const REGISTRY = [
  {
    asset_id: 'ka_gochara', layer: 'kala', depends_on: [], estimated_seconds: 900,
    scope: 'per_chart', target_table: 'kala_gochara_windows',
    count_sql: "SELECT count(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'",
    english_name: 'Gochara', sanskrit_name: 'Gochara',
  },
]

let clientQueries: string[] = []

function makeReq(body: object): NextRequest {
  return new NextRequest('http://localhost/api/cockpit/clear/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function previewHash(affected: string[]): string {
  const timeSlot = Math.floor(Date.now() / (15 * 60 * 1000))
  return createHash('sha256')
    .update(JSON.stringify({ chart_id: CHART, scope: 'asset', scope_target: 'ka_gochara', affectedAssetIds: [...affected].sort(), timeSlot }))
    .digest('hex')
    .slice(0, 32)
}

function setupMocks(opts: { uid: string; role: string; authoritative40: boolean }) {
  const { uid, role, authoritative40 } = opts

  mockGetServerUser.mockResolvedValue({ uid })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }], rowCount: 1 })
    if (/owner_id[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ owner_id: OWNER_UID }], rowCount: 1 })
    if (/FROM asset_registry/.test(sql)) return Promise.resolve({ rows: REGISTRY, rowCount: 1 })
    if (/FROM build_protected_assets/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })

  clientQueries = []
  const client = {
    query: vi.fn((sql: string) => {
      clientQueries.push(sql)
      if (/FROM kala_gochara_authority/.test(sql) && /SELECT/.test(sql)) {
        return Promise.resolve({
          rows: authoritative40 ? [{ '?column?': 1 }] : [],
          rowCount: authoritative40 ? 1 : 0,
        })
      }
      return Promise.resolve({ rows: [], rowCount: 3 })
    }),
    release: vi.fn(),
  }
  mockGetPool.mockResolvedValue({ connect: vi.fn().mockResolvedValue(client) })
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('POST /api/cockpit/clear/execute — WP7 C-1 ka_gochara authoritative-generation guard', () => {
  it("(a) chart owner is REFUSED when '4.0' is the authoritative generation — no statements run", async () => {
    setupMocks({ uid: OWNER_UID, role: 'client', authoritative40: true })
    const res = await EXECUTE(makeReq({
      chart_id: CHART, scope: 'asset', scope_target: 'ka_gochara',
      preview_hash: previewHash(['ka_gochara']),
    }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.failed_tables).toHaveLength(1)
    expect(body.failed_tables[0].table).toBe('ka_gochara')
    expect(body.failed_tables[0].error).toMatch(/authoritative generation/)
    expect(body.failed_tables[0].error).toMatch(/release authority/)
    // The guard SELECT ran, but NOT ONE of the three DELETEs (or the cascade) did.
    expect(clientQueries.filter(q => /^\s*DELETE FROM kala_gochara/i.test(q))).toHaveLength(0)
    expect(clientQueries.filter(q => /kala_gochara_publication/i.test(q))).toHaveLength(0)
    expect(clientQueries.filter(q => /SAVEPOINT/i.test(q))).toHaveLength(0)
  })

  it('(b) the release authority clears the authoritative generation — three DELETEs + cascade, one SAVEPOINT', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', authoritative40: true })
    const res = await EXECUTE(makeReq({
      chart_id: CHART, scope: 'asset', scope_target: 'ka_gochara',
      preview_hash: previewHash(['ka_gochara']),
    }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.failed_tables).toBeUndefined()

    const gocharaDeletes = clientQueries.filter(q => /^\s*DELETE FROM kala_gochara/i.test(q))
    expect(gocharaDeletes).toEqual([
      "DELETE FROM kala_gochara_coverage WHERE chart_id = $1 AND generation = '4.0'",
      "DELETE FROM kala_gochara_contacts WHERE chart_id = $1 AND generation = '4.0'",
      "DELETE FROM kala_gochara_windows   WHERE chart_id = $1 AND generation = '4.0'",
      'DELETE FROM kala_gochara_authority WHERE chart_id = $1',
    ])
    expect(clientQueries).toContain(
      "UPDATE kala_gochara_publication SET status = 'cleared' WHERE chart_id = $1 AND generation = '4.0'"
    )
    // Cascade shares the asset's SAVEPOINT — exactly one savepoint for the asset.
    expect(clientQueries.filter(q => /^SAVEPOINT /.test(q))).toHaveLength(1)
  })

  it("(c) a chart whose authority is '3.0' proceeds — three DELETEs, no cascade, authority untouched", async () => {
    setupMocks({ uid: OWNER_UID, role: 'client', authoritative40: false })
    const res = await EXECUTE(makeReq({
      chart_id: CHART, scope: 'asset', scope_target: 'ka_gochara',
      preview_hash: previewHash(['ka_gochara']),
    }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.failed_tables).toBeUndefined()

    const gocharaDeletes = clientQueries.filter(q => /^\s*DELETE FROM kala_gochara/i.test(q))
    expect(gocharaDeletes).toHaveLength(3)
    expect(gocharaDeletes.some(q => /kala_gochara_authority/.test(q))).toBe(false)
    expect(clientQueries.filter(q => /kala_gochara_publication/i.test(q))).toHaveLength(0)
  })

  it('(d) the explicit entry takes precedence over count_sql — the derived windows-only DELETE never runs', async () => {
    setupMocks({ uid: OWNER_UID, role: 'client', authoritative40: false })
    await EXECUTE(makeReq({
      chart_id: CHART, scope: 'asset', scope_target: 'ka_gochara',
      preview_hash: previewHash(['ka_gochara']),
    }))
    // The derived path would emit exactly the count_sql prefix-swap (windows only,
    // single statement). The explicit three-statement entry runs instead.
    const gocharaDeletes = clientQueries.filter(q => /^\s*DELETE FROM kala_gochara/i.test(q))
    expect(gocharaDeletes).toHaveLength(3)
    expect(gocharaDeletes.some(q => /kala_gochara_coverage/.test(q))).toBe(true)
  })
})

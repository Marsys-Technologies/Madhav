/**
 * ka_gochara Clear at the execute route (POST /api/cockpit/clear/execute) — migration 1226.
 *
 * ka_gochara's registry row counts, checks and clears what its REGISTERED WRITER writes:
 * kala_gochara_windows_v2 at generation '2.0' plus the writer's delta-aware bookkeeping
 * (kala_gochara_v2_build_state, same generation). This replaces WP7 packet C-1's '4.0'
 * ledger Clear and its authoritative-generation refusal guard: a ka_gochara Clear can no
 * longer reach a '4.0' row, so there is nothing for that guard to refuse (the '4.0' pin
 * returns together with the writer switch at D-FLIP).
 *
 * Covers, at the route:
 *   (a) a chart owner's Clear runs EXACTLY the two scoped DELETEs, in one SAVEPOINT, and
 *       never touches an authority / publication / contacts / coverage / protected-window row;
 *   (b) the explicit entry takes precedence over the count_sql-derived windows-only DELETE;
 *   (c) the Clear is not refused or altered by a '3.0' or '4.0' authoritative generation —
 *       it cannot reach either.
 *
 * What executes the DELETEs against real rows (and proves they remove exactly the writer's
 * rows) is `src/lib/cockpit/__tests__/ka_gochara_registry_revert_1226.db.test.ts`.
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
    scope: 'per_chart', target_table: 'kala_gochara_windows_v2',
    count_sql: "SELECT count(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation='2.0'",
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

describe('POST /api/cockpit/clear/execute — ka_gochara clears the registered writer\'s own rows (migration 1226)', () => {
  const WRITER_DELETES = [
    "DELETE FROM kala_gochara_windows_v2 WHERE chart_id = $1 AND generation = '2.0'",
    "DELETE FROM kala_gochara_v2_build_state WHERE chart_id = $1 AND generation = '2.0'",
  ]

  it('(a) a chart owner\'s Clear runs exactly the two scoped DELETEs in one SAVEPOINT — nothing else in the gochara family', async () => {
    setupMocks({ uid: OWNER_UID, role: 'client', authoritative40: false })
    const res = await EXECUTE(makeReq({
      chart_id: CHART, scope: 'asset', scope_target: 'ka_gochara',
      preview_hash: previewHash(['ka_gochara']),
    }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.failed_tables).toBeUndefined()

    expect(clientQueries.filter(q => /^\s*(DELETE|UPDATE|INSERT)\b[\s\S]*kala_gochara/i.test(q))).toEqual(WRITER_DELETES)
    // no authority / publication / ledger statement of any kind
    expect(clientQueries.filter(q => /kala_gochara_(authority|publication|contacts|coverage)\b/i.test(q))).toHaveLength(0)
    expect(clientQueries.filter(q => /kala_gochara_windows\b(?!_v2)/i.test(q))).toHaveLength(0)
    expect(clientQueries.filter(q => /^SAVEPOINT /.test(q))).toHaveLength(1)
  })

  it('(b) the explicit entry takes precedence over count_sql — the derived windows-only DELETE never runs alone', async () => {
    setupMocks({ uid: OWNER_UID, role: 'client', authoritative40: false })
    await EXECUTE(makeReq({
      chart_id: CHART, scope: 'asset', scope_target: 'ka_gochara',
      preview_hash: previewHash(['ka_gochara']),
    }))
    // The derived path would emit one count_sql prefix-swap (windows only) and leave the writer's
    // class_fingerprint rows behind — after which a rebuild would be a delta-aware no-op.
    const deletes = clientQueries.filter(q => /^\s*DELETE FROM kala_gochara/i.test(q))
    expect(deletes).toHaveLength(2)
    expect(deletes.some(q => /kala_gochara_v2_build_state/.test(q))).toBe(true)
  })

  it('(c) a \'3.0\' or \'4.0\' authoritative generation neither refuses nor alters the Clear — it cannot reach either', async () => {
    setupMocks({ uid: OWNER_UID, role: 'client', authoritative40: true })
    const res = await EXECUTE(makeReq({
      chart_id: CHART, scope: 'asset', scope_target: 'ka_gochara',
      preview_hash: previewHash(['ka_gochara']),
    }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.failed_tables).toBeUndefined()
    expect(clientQueries.filter(q => /^\s*DELETE FROM kala_gochara/i.test(q))).toEqual(WRITER_DELETES)
    // the guard SELECT of the old entry is gone: nothing asks the authority table anything
    expect(clientQueries.filter(q => /kala_gochara_authority/i.test(q))).toHaveLength(0)
  })
})

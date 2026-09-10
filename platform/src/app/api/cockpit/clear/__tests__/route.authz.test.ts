/**
 * Regression test for P2 blocker B-007 (Paripraśna Experience Assurance):
 * cross-user destructive-clear authorization on the cockpit Clear routes.
 *
 * Before the fix, BOTH `POST /api/cockpit/clear` (preview) and
 * `POST /api/cockpit/clear/execute` (the actual DELETE) checked only
 * `getServerUser() !== null`. There was NO ownership / `chart_grants` check on
 * the caller-supplied `chart_id` at all. Any authenticated user (default role
 * `guest`) could therefore:
 *
 *   1. POST an arbitrary `chart_id` (including the native's real chart) to
 *      `/clear` and receive a `preview_hash` for wiping that chart's build data;
 *   2. POST that hash to `/clear/execute` and actually run
 *      `DELETE FROM <target_table> WHERE chart_id=$1` across every build-derived
 *      table, reset `asset_throughput` to dormant, and mark downstream stale —
 *      an irreversible wipe of another user's chart;
 *   3. read another user's `charts.subject_name` (PII) straight out of the
 *      `scope: 'global'` / `layer=brahmagyan` branch's
 *      `requires_typed_confirmation` field — which is exactly the value the ONE
 *      confirmation gate on execute compares against, so the leak also
 *      self-served the bypass for that gate.
 *
 * The fix routes both handlers through the same `authorizeChartAccess` brain
 * already used by GET /api/charts/[id] (P2-B-001, PR #1597) and by
 * `resolveChartPageAccess`, and requires permission === 'all' (owner or
 * super_admin) because a clear is destructive — a `chart_grants` 'view'
 * grantee must NOT be able to delete.
 *
 * Note on `scope: 'global'` for non-admins: it is deliberately NOT rejected
 * outright. `CockpitShell.tsx`'s "Clear all / Rebuild" control issues
 * `scope: 'global'` for every caller the page guard admits with
 * `canBuild === true` — i.e. plain chart OWNERS, not only super_admins. The
 * `filterScopeAssets` narrowing (allowedScopes = ['per_chart'] for non-admins,
 * plus the unconditional brahmagyan exclusion) is what keeps that request
 * confined to the caller's own chart-scoped assets; the missing piece was never
 * the narrowing, it was that nothing checked WHOSE chart_id it narrowed onto.
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

import { POST as PREVIEW } from '../route'
import { POST as EXECUTE } from '../execute/route'

const VICTIM_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const VICTIM_UID = 'victim-uid'
const ATTACKER_UID = 'attacker-uid'
const ADMIN_UID = 'admin-uid'

const REGISTRY = [
  {
    asset_id: 'ka_kshetra', layer: 'kala', depends_on: [], estimated_seconds: 60,
    scope: 'per_chart', target_table: 'kala_kshetra',
    count_sql: 'SELECT count(*) FROM kala_kshetra WHERE chart_id=$1',
    english_name: 'Kshetra', sanskrit_name: 'Kshetra',
  },
  {
    asset_id: 'ka_gochara_sweep', layer: 'kala', depends_on: [], estimated_seconds: 1800,
    scope: 'per_chart', target_table: 'kala_gochara_windows',
    count_sql: 'SELECT count(*) FROM kala_gochara_windows WHERE chart_id=$1',
    english_name: 'Forward Sweep', sanskrit_name: 'Gochara Cakra',
  },
]

const SUBJECT_NAME = 'Abhisek Mohanty'

/** The DELETE/UPDATE statements the execute route issues inside its transaction. */
let clientQueries: string[] = []

function makeReq(path: string, body: object): NextRequest {
  return new NextRequest(`http://localhost${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

/**
 * SQL-shape-dispatching mock (rather than ordered mockResolvedValueOnce) so the
 * fixture does not have to be re-sequenced every time an authz query is added.
 */
function setupMocks(opts: {
  uid: string
  role?: string
  ownerId?: string | null
  grantPermission?: string | null
}) {
  const { uid, role = 'guest', ownerId = VICTIM_UID, grantPermission = null } = opts

  mockGetServerUser.mockResolvedValue({ uid })

  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }], rowCount: 1 })
    if (/FROM chart_grants/.test(sql)) {
      return Promise.resolve({
        rows: grantPermission ? [{ permission: grantPermission }] : [],
        rowCount: grantPermission ? 1 : 0,
      })
    }
    if (/subject_name/.test(sql)) {
      return Promise.resolve({ rows: [{ subject_name: SUBJECT_NAME, name: SUBJECT_NAME }], rowCount: 1 })
    }
    if (/owner_id[\s\S]*FROM charts/.test(sql)) {
      return Promise.resolve({ rows: [{ owner_id: ownerId }], rowCount: 1 })
    }
    if (/scope\s+FROM asset_registry/.test(sql)) {
      return Promise.resolve({ rows: [{ scope: 'per_chart' }], rowCount: 1 })
    }
    if (/FROM asset_registry/.test(sql)) return Promise.resolve({ rows: REGISTRY, rowCount: REGISTRY.length })
    if (/FROM build_protected_assets/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM asset_throughput/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/count\(\*\)/.test(sql)) return Promise.resolve({ rows: [{ count: '11' }], rowCount: 1 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })

  clientQueries = []
  const client = {
    query: vi.fn((sql: string) => {
      clientQueries.push(sql)
      return Promise.resolve({ rows: [], rowCount: 3 })
    }),
    release: vi.fn(),
  }
  mockGetPool.mockResolvedValue({ connect: vi.fn().mockResolvedValue(client) })
}

/** Recompute the preview_hash the execute route expects, exactly as it does. */
function previewHash(scope: string, scopeTarget: string | null, affected: string[]): string {
  const timeSlot = Math.floor(Date.now() / (15 * 60 * 1000))
  return createHash('sha256')
    .update(JSON.stringify({ chart_id: VICTIM_CHART, scope, scope_target: scopeTarget, affectedAssetIds: [...affected].sort(), timeSlot }))
    .digest('hex')
    .slice(0, 32)
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('POST /api/cockpit/clear (preview) — P2-B-007 cross-chart destructive authz', () => {
  it('(a) DENIES a non-owner, non-admin authenticated user previewing another chart', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await PREVIEW(makeReq('/api/cockpit/clear', {
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala',
    }))
    expect(res.status).not.toBe(200)
    expect(res.status).toBe(403)
    const body = await res.json()
    expect(body.preview).toBeUndefined()
  })

  it('(c) DENIES the scope:global branch to a non-owner — no subject_name PII leak', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await PREVIEW(makeReq('/api/cockpit/clear', {
      chart_id: VICTIM_CHART, scope: 'global', scope_target: null,
    }))
    expect(res.status).toBe(403)
    // The typed-confirmation value is the ONE gate on execute; it must not leak.
    expect(JSON.stringify(await res.json())).not.toContain(SUBJECT_NAME)
  })

  it('(c2) DENIES a chart_grants view-grantee — a read grant is not a delete grant', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await PREVIEW(makeReq('/api/cockpit/clear', {
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala',
    }))
    expect(res.status).toBe(403)
  })

  it('(d) ALLOWS the legitimate owner to preview their own chart', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await PREVIEW(makeReq('/api/cockpit/clear', {
      chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala',
    }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.preview.affected_assets).toEqual(expect.arrayContaining(['ka_kshetra', 'ka_gochara_sweep']))
  })

  it('(d2) ALLOWS an owner the scope:global preview — CockpitShell Clear-all must keep working', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await PREVIEW(makeReq('/api/cockpit/clear', {
      chart_id: VICTIM_CHART, scope: 'global', scope_target: null,
    }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.preview.requires_typed_confirmation).toBe(SUBJECT_NAME)
  })

  it('(d3) ALLOWS super_admin to preview a chart they do not own', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    const res = await PREVIEW(makeReq('/api/cockpit/clear', {
      chart_id: VICTIM_CHART, scope: 'global', scope_target: null,
    }))
    expect(res.status).toBe(200)
  })
})

describe('POST /api/cockpit/clear/execute — P2-B-007 cross-chart destructive authz', () => {
  it('(b) DENIES a non-owner, non-admin user executing a clear — and issues NO DELETE', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await EXECUTE(makeReq('/api/cockpit/clear/execute', {
      chart_id: VICTIM_CHART,
      scope: 'layer',
      scope_target: 'kala',
      preview_hash: previewHash('layer', 'kala', ['ka_kshetra', 'ka_gochara_sweep']),
    }))
    expect(res.status).not.toBe(200)
    expect(res.status).toBe(403)
    // The real proof: the destructive transaction never opened.
    expect(mockGetPool).not.toHaveBeenCalled()
    expect(clientQueries.filter(q => /^\s*DELETE/i.test(q))).toHaveLength(0)
  })

  it('(b2) DENIES a view-grantee executing a clear', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await EXECUTE(makeReq('/api/cockpit/clear/execute', {
      chart_id: VICTIM_CHART,
      scope: 'layer',
      scope_target: 'kala',
      preview_hash: previewHash('layer', 'kala', ['ka_kshetra', 'ka_gochara_sweep']),
    }))
    expect(res.status).toBe(403)
    expect(mockGetPool).not.toHaveBeenCalled()
  })

  it('(d) ALLOWS the legitimate owner to execute a clear on their own chart', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await EXECUTE(makeReq('/api/cockpit/clear/execute', {
      chart_id: VICTIM_CHART,
      scope: 'layer',
      scope_target: 'kala',
      preview_hash: previewHash('layer', 'kala', ['ka_kshetra', 'ka_gochara_sweep']),
    }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.cleared.assets).toBe(2)
    expect(clientQueries.some(q => /^\s*DELETE/i.test(q))).toBe(true)
  })

  it('(d3) ALLOWS super_admin to execute a clear on a chart they do not own', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    const res = await EXECUTE(makeReq('/api/cockpit/clear/execute', {
      chart_id: VICTIM_CHART,
      scope: 'layer',
      scope_target: 'kala',
      preview_hash: previewHash('layer', 'kala', ['ka_kshetra', 'ka_gochara_sweep']),
    }))
    expect(res.status).toBe(200)
  })
})

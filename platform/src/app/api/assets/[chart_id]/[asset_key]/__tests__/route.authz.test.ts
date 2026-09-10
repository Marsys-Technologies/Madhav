/**
 * Regression test for V3-E-010 (EDIR_V3_REGISTER) — cross-tenant read on
 * GET /api/assets/[chart_id]/[asset_key].
 *
 * Same root-cause family as B-001/B-007/B-008: a caller-supplied `chart_id`
 * was trusted after only "is anyone logged in" — never checked against actual
 * chart ownership/grants. Before the fix this route checked only
 * `getServerUser() !== null` and then returned, for ANY caller-supplied
 * `chart_id` path parameter, that chart's asset row_count, provenance
 * (build_id, ayanamsha_id, computed_at), pyramid_layers build status,
 * gate_verdict, and up to 3 sample_rows straight from `chart_facts`.
 *
 * That is a cross-tenant READ. Gate level is 'read' (permission !== 'deny'),
 * matching the sibling B-008 read-path fixes (GET /api/cockpit/stats): a
 * `chart_grants` 'view' grantee legitimately passes, since this is disclosure
 * of read-only chart-scoped data, not a destructive/state-changing action.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { GET } from '../route'

const VICTIM_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const VICTIM_UID = 'victim-uid'
const ATTACKER_UID = 'attacker-uid'
const ADMIN_UID = 'admin-uid'
const ASSET_KEY = 'chart_facts'

/** A sentinel value that must never leak into a denied response. */
const VICTIM_ROW_MARKER = 'victim-sensitive-fact-value'

function makeReq(): NextRequest {
  return new NextRequest(`http://localhost/api/assets/${VICTIM_CHART}/${ASSET_KEY}`, { method: 'GET' })
}

function makeParams(): { params: Promise<{ chart_id: string; asset_key: string }> } {
  return { params: Promise.resolve({ chart_id: VICTIM_CHART, asset_key: ASSET_KEY }) }
}

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
    if (/owner_id[\s\S]*FROM charts/.test(sql)) {
      return Promise.resolve({ rows: [{ owner_id: ownerId }], rowCount: 1 })
    }
    if (/COUNT\(\*\) as count/.test(sql)) {
      return Promise.resolve({ rows: [{ count: '42' }], rowCount: 1 })
    }
    if (/build_id, provenance, created_at/.test(sql)) {
      return Promise.resolve({
        rows: [{ build_id: 'b-1', provenance: { ayanamsha_id: 'lahiri' }, created_at: '2026-08-01T00:00:00Z' }],
        rowCount: 1,
      })
    }
    if (/FROM pyramid_layers/.test(sql)) {
      return Promise.resolve({ rows: [{ status: 'lit' }], rowCount: 1 })
    }
    if (/fact_id, category, divisional_chart/.test(sql)) {
      return Promise.resolve({
        rows: [{
          fact_id: 'f-1', category: ASSET_KEY, divisional_chart: 'D1',
          value_text: VICTIM_ROW_MARKER, value_number: null,
          source_section: 'test', build_id: 'b-1', created_at: '2026-08-01T00:00:00Z',
        }],
        rowCount: 1,
      })
    }
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

const chartScopedReads = () =>
  mockQuery.mock.calls.filter((call: unknown[]) =>
    /FROM chart_facts|FROM pyramid_layers/.test(call[0] as string)
  )

beforeEach(() => {
  vi.clearAllMocks()
})

describe('GET /api/assets/[chart_id]/[asset_key] — V3-E-010 cross-tenant asset read', () => {
  it('DENIES a non-owner guest — and issues NO chart-scoped read', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(403)
    expect(JSON.stringify(await res.json())).not.toContain(VICTIM_ROW_MARKER)
    expect(chartScopedReads()).toHaveLength(0)
  })

  it('DENIES when the chart does not exist', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: null })
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(403)
    expect(chartScopedReads()).toHaveLength(0)
  })

  it('DENIES an unauthenticated caller', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(401)
    expect(chartScopedReads()).toHaveLength(0)
  })

  it('ALLOWS the owner — the legitimate AssetInspector path must keep working', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.row_count).toBe(42)
    expect(body.sample_rows[0].value_text).toBe(VICTIM_ROW_MARKER)
  })

  it('ALLOWS a chart_grants view-grantee — this is a read', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(200)
  })

  it('ALLOWS super_admin on a chart they do not own', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    const res = await GET(makeReq(), makeParams())
    expect(res.status).toBe(200)
  })
})

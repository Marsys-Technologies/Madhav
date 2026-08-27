/**
 * Regression test for P2 blocker B-008 — `GET /api/cockpit/stats`.
 *
 * Verified claim: this route called `getServerUser()` ZERO times. Fully
 * unauthenticated. Given a caller-supplied `chart_id` it returned, per registry
 * asset, that chart's real row counts (`count_sql` executed with the chart_id),
 * build state, `last_built_at`, live `rows_written` during an active build, and
 * committed substep progress.
 *
 * That is not subject-identifying data — no subject_name, no birth parameters —
 * which is why it is graded MEDIUM rather than alongside the atlas/sample dump.
 * But it is a per-chart profile served to anyone on the internet who can guess or
 * obtain a chart UUID, and it confirms chart existence. Two gates apply:
 * authentication always, and ownership whenever a chart_id is supplied.
 *
 * The no-chart_id call returns registry-wide asset counts with no chart scope; it
 * still requires authentication, but there is no owner to check.
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

let issued: string[] = []

function makeReq(chartId?: string): NextRequest {
  const url = chartId
    ? `http://localhost/api/cockpit/stats?chart_id=${chartId}`
    : 'http://localhost/api/cockpit/stats'
  return new NextRequest(url)
}

function setupMocks(opts: {
  uid: string | null
  role?: string
  ownerId?: string | null
  grantPermission?: string | null
}) {
  const { uid, role = 'guest', ownerId = VICTIM_UID, grantPermission = null } = opts
  mockGetServerUser.mockResolvedValue(uid ? { uid } : null)
  issued = []

  mockQuery.mockImplementation((sql: string) => {
    issued.push(sql)
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
    if (/FROM asset_registry/.test(sql)) {
      return Promise.resolve({
        rows: [{
          asset_id: 'ka_kshetra', count_sql: 'SELECT count(*) FROM kala_kshetra WHERE chart_id=$1',
          size_sql: null, scope: 'per_chart', is_active: true, target_floor: null,
          asset_type: 'data', asset_kind: 'data', health_probe: null,
          service_health: null, last_invoked_at: null, last_selftest_at: null, has_substeps: false,
        }],
        rowCount: 1,
      })
    }
    if (/FROM asset_throughput/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM build_substep_progress/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/count\(\*\)/.test(sql)) return Promise.resolve({ rows: [{ count: '4242' }], rowCount: 1 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

/** The chart-scoped reads that must not run for an unauthorized caller. */
const chartScopedReads = () =>
  issued.filter(q => /FROM asset_throughput|FROM build_substep_progress|count\(\*\)/i.test(q))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('GET /api/cockpit/stats — P2-B-008 unauthenticated per-chart disclosure', () => {
  it('DENIES an anonymous caller', async () => {
    setupMocks({ uid: null })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(401)
    expect(JSON.stringify(await res.json())).not.toContain('4242')
    expect(chartScopedReads()).toHaveLength(0)
  })

  it('DENIES an authenticated non-owner reading another chart\'s stats', async () => {
    setupMocks({ uid: ATTACKER_UID, ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    expect(JSON.stringify(await res.json())).not.toContain('4242')
    expect(chartScopedReads()).toHaveLength(0)
  })

  it('ALLOWS the owner — the cockpit stats poll must keep working', async () => {
    setupMocks({ uid: VICTIM_UID, ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.data.assets[0].actual_rows).toBe(4242)
  })

  it('ALLOWS a view-grantee — stats are a read', async () => {
    setupMocks({ uid: ATTACKER_UID, ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
  })

  it('ALLOWS an authenticated caller with no chart_id — registry-wide, no chart scope', async () => {
    setupMocks({ uid: ATTACKER_UID })
    const res = await GET(makeReq())
    expect(res.status).toBe(200)
  })
})

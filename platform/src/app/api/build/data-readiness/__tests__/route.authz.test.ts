/**
 * Regression test for V3-E-011 finding 3 — cross-tenant read disclosure on
 * GET /api/build/data-readiness.
 *
 * Before the fix this route checked only `getServerUser() !== null` and then
 * queried `build_events`/`build_checkpoints` for a caller-supplied `chart_id`
 * with no ownership check, returning that chart's build_status, ready/missing
 * asset lists to ANY authenticated user. Fix adds
 * `requireChartPermission({ access: 'read' })` right after `chart_id` is read,
 * before the first DB query — same brain/pattern as the sibling
 * V3-E-010 rebuild fixes (`POST /api/build/rebuild`).
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

let issued: string[] = []
let projectionCalls: Array<{ sql: string; args: unknown[][] }> = []
let assetRows: Array<{ asset_id: string }> = []
let buildRows: Array<{ build_id: string | null }> = []
let checkpointRows: Array<{ asset_id: string; status: string }> = []
let failingTable: string | null = null
const queryFailure = new Error('synthetic readiness query failure')

function makeReq(chartId: string): NextRequest {
  return new NextRequest(`http://localhost/api/build/data-readiness?chart_id=${chartId}`)
}

function setupMocks(opts: { uid: string; role?: string; ownerId?: string | null; grantPermission?: string | null }) {
  const { uid, role = 'guest', ownerId = VICTIM_UID, grantPermission = null } = opts
  mockGetServerUser.mockResolvedValue({ uid })
  issued = []

  mockQuery.mockImplementation((sql: string, ...args: unknown[][]) => {
    issued.push(sql)
    if (/FROM asset_registry|FROM build_events|FROM build_checkpoints/.test(sql)) {
      projectionCalls.push({ sql, args })
      if (failingTable && sql.includes('FROM ' + failingTable)) return Promise.reject(queryFailure)
    }
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }], rowCount: 1 })
    if (/FROM chart_grants/.test(sql)) {
      return Promise.resolve({
        rows: grantPermission ? [{ permission: grantPermission }] : [],
        rowCount: grantPermission ? 1 : 0,
      })
    }
    if (/owner_id[\s\S]*FROM charts/.test(sql)) {
      return Promise.resolve({ rows: ownerId ? [{ owner_id: ownerId }] : [], rowCount: ownerId ? 1 : 0 })
    }
    if (/FROM asset_registry/.test(sql)) {
      return Promise.resolve({ rows: assetRows, rowCount: assetRows.length })
    }
    if (/FROM build_events/.test(sql)) {
      return Promise.resolve({ rows: buildRows, rowCount: buildRows.length })
    }
    if (/FROM build_checkpoints/.test(sql)) {
      return Promise.resolve({ rows: checkpointRows, rowCount: checkpointRows.length })
    }
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

const dataQueries = () => issued.filter(q => /FROM build_events|FROM build_checkpoints|FROM asset_registry/i.test(q))

beforeEach(() => {
  vi.clearAllMocks()
  issued = []
  projectionCalls = []
  assetRows = [{ asset_id: 'ga_chart_facts' }]
  buildRows = [{ build_id: 'build-1' }]
  checkpointRows = [{ asset_id: 'ga_chart_facts', status: 'success' }]
  failingTable = null
})

describe('GET /api/build/data-readiness — V3-E-011 finding 3 cross-tenant read disclosure', () => {
  it('DENIES a non-owner guest — and never discloses build readiness data', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    expect(dataQueries()).toHaveLength(0)
  })

  it('DENIES a chart_grants view-grantee only if not granted — sanity: no grant at all', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: null })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
  })

  it('DENIES when the chart does not exist', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: null })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    expect(dataQueries()).toHaveLength(0)
  })

  it('DENIES an unauthenticated caller', async () => {
    mockGetServerUser.mockResolvedValue(null)
    issued = []
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(401)
    expect(dataQueries()).toHaveLength(0)
  })

  it('ALLOWS the owner — the legitimate readiness-check path must keep working', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.chart_id).toBe(VICTIM_CHART)
    expect(dataQueries().length).toBeGreaterThan(0)
  })

  it('ALLOWS a chart_grants view-grantee — read disclosure is exactly what a view grant is for', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
  })

  it('ALLOWS super_admin on a chart they do not own', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
  })
})


function assertProjectionQueries(chartId: string, withBuild = true) {
  expect(projectionCalls.map(({ sql, args }) => [sql.replace(/\s+/g, ' ').trim(), args])).toEqual([
    ["SELECT asset_id FROM asset_registry WHERE is_active = true AND (asset_type IS NULL OR asset_type != 'service') AND (asset_kind IS NULL OR asset_kind != 'service') ORDER BY sort_order ASC", []],
    ['SELECT build_id FROM build_events WHERE chart_id = $1 ORDER BY emitted_at DESC LIMIT 1', [[chartId]]],
    ...(withBuild ? [['SELECT DISTINCT ON (asset_id) asset_id, status FROM build_checkpoints WHERE build_id = $1 ORDER BY asset_id, completed_at DESC NULLS LAST', [['build-1']]]] : []),
  ])
}

describe('GET data-readiness projection compatibility', () => {
  it('checks authentication before a missing chart parameter without issuing SQL', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await GET(makeReq(''))
    expect(res.status).toBe(401)
    expect(await res.text()).toBe('{"error":"unauthenticated"}')
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('rejects missing chart before permission or readiness SQL', async () => {
    setupMocks({ uid: VICTIM_UID })
    const res = await GET(makeReq(''))
    expect(res.status).toBe(400)
    expect(await res.text()).toBe('{"error":"chart_id required"}')
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('retains exact permission-denied response and finishes authorization before data SQL', async () => {
    setupMocks({ uid: ATTACKER_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    expect(await res.json()).toEqual({ error: 'Forbidden', code: 'FORBIDDEN_CHART' })
    expect(projectionCalls).toEqual([])
  })

  it('preserves no-build ordering, falsey asset filtering, duplicates and absent cache header', async () => {
    setupMocks({ uid: VICTIM_UID })
    assetRows = [{ asset_id: 'z' }, { asset_id: '' }, { asset_id: 'a' }, { asset_id: 'z' }]
    buildRows = []
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
    expect(res.headers.get('Cache-Control')).toBeNull()
    expect(await res.text()).toBe(JSON.stringify({ chart_id: VICTIM_CHART, build_status: 'none', ready: [], missing: ['z', 'a', 'z'], partial_count: 0, total_count: 3 }))
    assertProjectionQueries(VICTIM_CHART, false)
    expect(issued.findIndex(sql => sql.includes('FROM charts'))).toBeLessThan(issued.findIndex(sql => sql.includes('FROM asset_registry')))
  })

  it.each([[[]], [[{ build_id: null }]], [[{ build_id: '' }]]])('preserves no-build zero-asset output for latest row %j', async (latest) => {
    setupMocks({ uid: VICTIM_UID })
    assetRows = []
    buildRows = latest
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.headers.get('Cache-Control')).toBeNull()
    expect(await res.json()).toEqual({ chart_id: VICTIM_CHART, build_status: 'none', ready: [], missing: [], partial_count: 0, total_count: 0 })
    assertProjectionQueries(VICTIM_CHART, false)
  })

  it.each([
    ['success', [{ asset_id: 'a', status: 'success' }, { asset_id: 'b', status: 'success' }], 'complete', ['a', 'b'], []],
    ['partial despite unrelated failure', [{ asset_id: 'a', status: 'success' }, { asset_id: 'unknown', status: 'failed' }], 'partial', ['a'], ['b']],
    ['failed from unrelated checkpoint', [{ asset_id: 'unknown', status: 'failed' }], 'failed', [], ['a', 'b']],
    ['unknown status', [{ asset_id: 'a', status: 'unknown' }], 'none', [], ['a', 'b']],
    ['no checkpoints', [], 'none', [], ['a', 'b']],
  ] as const)('preserves classification for %s', async (_name, checkpoints, status, ready, missing) => {
    setupMocks({ uid: VICTIM_UID })
    assetRows = [{ asset_id: 'a' }, { asset_id: 'b' }]
    checkpointRows = [...checkpoints]
    const chartId = "opaque chart/Ω + ? % '"
    const res = await GET(new NextRequest('http://localhost/api/build/data-readiness?chart_id=' + encodeURIComponent(chartId)))
    expect(res.headers.get('Cache-Control')).toBe('max-age=30')
    expect(await res.text()).toBe(JSON.stringify({ chart_id: chartId, build_status: status, ready, missing, partial_count: ready.length, total_count: 2 }))
    assertProjectionQueries(chartId)
  })

  it.each([
    [[], 'complete'],
    [[{ asset_id: 'unknown', status: 'failed' }], 'failed'],
  ] as const)('preserves existing-build zero-asset classification %j', async (checkpoints, status) => {
    setupMocks({ uid: VICTIM_UID })
    assetRows = []
    checkpointRows = [...checkpoints]
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.headers.get('Cache-Control')).toBe('max-age=30')
    expect(await res.json()).toEqual({ chart_id: VICTIM_CHART, build_status: status, ready: [], missing: [], partial_count: 0, total_count: 0 })
    assertProjectionQueries(VICTIM_CHART)
  })

  it.each(['asset_registry', 'build_events', 'build_checkpoints'])('propagates %s failure and issues no later projection query', async (table) => {
    setupMocks({ uid: VICTIM_UID })
    failingTable = table
    await expect(GET(makeReq(VICTIM_CHART))).rejects.toBe(queryFailure)
    const expectedCount = ['asset_registry', 'build_events', 'build_checkpoints'].indexOf(table) + 1
    expect(projectionCalls).toHaveLength(expectedCount)
  })
})

it('gates the Build projection and keeps the route free of direct database imports', async () => {
  const chartId = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  const denied = new Response(null, { status: 403 })
  const requireChartPermission = vi.fn().mockResolvedValueOnce(denied).mockResolvedValueOnce(null)
  const readiness = {
    chart_id: chartId,
    build_status: 'none',
    ready: [],
    missing: [],
    partial_count: 0,
    total_count: 0,
  }
  const getDataReadiness = vi.fn().mockResolvedValue({ readiness, hasBuild: false })

  // Both collaborators own database access. Mock them so loading the database
  // client in this isolated route import can only come from a bypass.
  vi.resetModules()
  vi.doMock('@/lib/auth/requireChartPermission', () => ({ requireChartPermission }))
  vi.doMock('@/lib/build/dataReadiness', () => ({ getDataReadiness }))
  vi.doMock('@/lib/db/client', () => {
    throw new Error('data-readiness route imported the database client directly')
  })

  try {
    const { GET: isolatedGET } = await import('../route')
    mockGetServerUser.mockResolvedValue({ uid: ATTACKER_UID })
    await expect(isolatedGET(makeReq(chartId))).resolves.toBe(denied)
    expect(requireChartPermission).toHaveBeenCalledExactlyOnceWith({
      uid: ATTACKER_UID, chartId, access: 'read',
    })
    expect(getDataReadiness).not.toHaveBeenCalled()

    const response = await isolatedGET(makeReq(chartId))
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual(readiness)
    expect(getDataReadiness).toHaveBeenCalledExactlyOnceWith(chartId)
  } finally {
    vi.doUnmock('@/lib/auth/requireChartPermission')
    vi.doUnmock('@/lib/build/dataReadiness')
    vi.doMock('@/lib/db/client', () => ({ query: mockQuery }))
    vi.resetModules()
  }
})

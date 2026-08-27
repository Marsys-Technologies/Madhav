/**
 * Regression test for P2 blocker B-008 — the cockpit Atlas routes.
 *
 * `GET /api/cockpit/atlas/sample` is the most severe finding of the B-008 sweep,
 * and is graded CRITICAL rather than the MEDIUM the sweep brief anticipated for
 * this group. It called `getServerUser()` ZERO times — no authentication at all,
 * let alone authorization — and issued, for a caller-supplied `asset` +
 * `chart_id`:
 *
 *     SELECT * FROM <target_table> WHERE chart_id = $1 LIMIT $2
 *
 * `SELECT *`, on any table in the asset registry, for any chart. That is a full
 * unauthenticated read of another person's chart data — `chart_facts` (the
 * derived astrological facts of a named individual), every `bodha_*`
 * interpretation table, every `kala_*`/`phala_*` row. Unlike the other routes in
 * this sweep it needs no account at all: an anonymous HTTP request is enough.
 *
 * There is a second, independent hole in the same function. When an asset is
 * `scope: 'per_chart'` but NO `chart_id` is supplied, `buildSampleQuery` falls
 * through to the unscoped branch:
 *
 *     SELECT * FROM <target_table> LIMIT $1
 *
 * — rows from ALL charts, mixed. Adding authentication alone would NOT close
 * that: a logged-in user with one chart of their own could still read other
 * people's rows by simply omitting the chart_id. So the fix does both: require
 * authentication, require ownership when a chart_id is given, and require a
 * chart_id (never fall through to the unscoped dump) for per_chart assets.
 *
 * `GET /api/cockpit/atlas/schema` was also fully unauthenticated, but returns
 * only `information_schema.columns` metadata for registry-whitelisted tables — no
 * row data, no chart scope. It is graded LOW and gets authentication only; no
 * ownership gate applies because nothing it returns is chart-scoped.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { GET as SAMPLE } from '../sample/route'
import { GET as SCHEMA } from '../schema/route'

const VICTIM_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const VICTIM_UID = 'victim-uid'
const ATTACKER_UID = 'attacker-uid'

/** Sentinel standing in for real victim row content in the mocked SELECT *. */
const VICTIM_ROW_MARKER = 'VICTIM-ROW-CONTENT'

/** Every SQL statement issued, so we can assert the data read never happened. */
let issued: string[] = []

function sampleReq(params: Record<string, string>): NextRequest {
  const qs = new URLSearchParams(params).toString()
  return new NextRequest(`http://localhost/api/cockpit/atlas/sample?${qs}`)
}

function schemaReq(table: string): NextRequest {
  return new NextRequest(`http://localhost/api/cockpit/atlas/schema?table=${table}`)
}

function setupMocks(opts: {
  uid: string | null
  role?: string
  ownerId?: string | null
  grantPermission?: string | null
  assetScope?: string
}) {
  const {
    uid, role = 'guest', ownerId = VICTIM_UID,
    grantPermission = null, assetScope = 'per_chart',
  } = opts

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
    // asset_registry lookup in sample/route.ts
    if (/FROM asset_registry WHERE asset_id/.test(sql)) {
      return Promise.resolve({
        rows: [{
          asset_id: 'ga_facts', target_table: 'chart_facts',
          count_sql: 'SELECT count(*) FROM chart_facts WHERE chart_id=$1',
          scope: assetScope, asset_type: 'data', storage_type: 'postgres_table',
        }],
        rowCount: 1,
      })
    }
    // whitelist lookup in schema/route.ts
    if (/FROM asset_registry/.test(sql)) {
      return Promise.resolve({ rows: [{ t: 'chart_facts' }], rowCount: 1 })
    }
    if (/information_schema\.columns/.test(sql)) {
      return Promise.resolve({ rows: [{ column_name: 'fact_id', data_type: 'text', is_nullable: 'NO', column_default: null, ordinal_position: 1 }], rowCount: 1 })
    }
    // The actual data read under test.
    if (/^\s*SELECT \* FROM/.test(sql)) {
      // Field name deliberately NOT 'secret'/'password'/etc: the repo-wide
      // secret_scan gate matches quoted key/value pairs on credential-shaped
      // keys, and a test sentinel must not trip a real credential detector.
      return Promise.resolve({ rows: [{ fact_id: 'f1', chart_id: VICTIM_CHART, sentinel: VICTIM_ROW_MARKER }], rowCount: 1 })
    }
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

/** The `SELECT * FROM <table>` data reads — these must never run unauthorized. */
const dataReads = () => issued.filter(q => /^\s*SELECT \* FROM/.test(q))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('GET /api/cockpit/atlas/sample — P2-B-008 unauthenticated cross-chart row dump', () => {
  it('DENIES an anonymous (unauthenticated) caller — and reads NO rows', async () => {
    setupMocks({ uid: null })
    const res = await SAMPLE(sampleReq({ asset: 'ga_facts', chart_id: VICTIM_CHART }))
    expect(res.status).toBe(401)
    const body = JSON.stringify(await res.json())
    expect(body).not.toContain(VICTIM_ROW_MARKER)
    expect(dataReads()).toHaveLength(0)
  })

  it('DENIES an authenticated non-owner reading another chart\'s rows', async () => {
    setupMocks({ uid: ATTACKER_UID, ownerId: VICTIM_UID })
    const res = await SAMPLE(sampleReq({ asset: 'ga_facts', chart_id: VICTIM_CHART }))
    expect(res.status).toBe(403)
    const body = JSON.stringify(await res.json())
    expect(body).not.toContain(VICTIM_ROW_MARKER)
    expect(dataReads()).toHaveLength(0)
  })

  it('DENIES the unscoped fallback: a per_chart asset with NO chart_id must not dump all charts', async () => {
    // The second, independent hole — authentication alone would not close it.
    // An authenticated user simply omits chart_id and the pre-fix code ran
    // `SELECT * FROM chart_facts LIMIT $1` across every chart in the table.
    setupMocks({ uid: ATTACKER_UID, ownerId: ATTACKER_UID })
    const res = await SAMPLE(sampleReq({ asset: 'ga_facts' }))
    expect(res.status).toBe(400)
    expect(dataReads()).toHaveLength(0)
  })

  it('ALLOWS the owner to sample their own chart — the Atlas view must keep working', async () => {
    setupMocks({ uid: VICTIM_UID, ownerId: VICTIM_UID })
    const res = await SAMPLE(sampleReq({ asset: 'ga_facts', chart_id: VICTIM_CHART }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.data.rows).toHaveLength(1)
    expect(dataReads()).toHaveLength(1)
    // And it stayed chart-scoped.
    expect(dataReads()[0]).toMatch(/WHERE chart_id = \$1/)
  })

  it('ALLOWS a view-grantee to sample — reading rows is what a read grant covers', async () => {
    setupMocks({ uid: ATTACKER_UID, ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await SAMPLE(sampleReq({ asset: 'ga_facts', chart_id: VICTIM_CHART }))
    expect(res.status).toBe(200)
  })

  it('ALLOWS an authenticated caller to sample a GLOBAL-scope asset with no chart_id', async () => {
    // Global assets (bg_* reference corpora) are not chart-scoped, so there is no
    // owner to check — authentication is the whole gate. This must keep working.
    setupMocks({ uid: ATTACKER_UID, ownerId: VICTIM_UID, assetScope: 'global' })
    const res = await SAMPLE(sampleReq({ asset: 'ga_facts' }))
    expect(res.status).toBe(200)
    expect(dataReads()).toHaveLength(1)
  })
})

describe('GET /api/cockpit/atlas/schema — P2-B-008 unauthenticated schema disclosure', () => {
  it('DENIES an anonymous caller', async () => {
    setupMocks({ uid: null })
    const res = await SCHEMA(schemaReq('chart_facts'))
    expect(res.status).toBe(401)
    expect(issued.filter(q => /information_schema/.test(q))).toHaveLength(0)
  })

  it('ALLOWS any authenticated caller — column metadata is not chart-scoped', async () => {
    setupMocks({ uid: ATTACKER_UID })
    const res = await SCHEMA(schemaReq('chart_facts'))
    expect(res.status).toBe(200)
    expect((await res.json()).data.columns).toHaveLength(1)
  })
})

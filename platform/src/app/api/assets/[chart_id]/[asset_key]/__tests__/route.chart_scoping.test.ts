/**
 * Regression test for V3-E-020 (EDIR_V3_REGISTER) — chart_facts row-scoping
 * landmine on GET /api/assets/[chart_id]/[asset_key].
 *
 * V3-E-010 fixed the DOOR on this route: a caller-supplied `chart_id` is now
 * checked against real ownership/grants via `requireChartPermission`. But the
 * three `chart_facts` reads BEHIND that door filter on `category = $1` ONLY —
 * they never constrain `chart_id`. So a caller legitimately authorized for
 * chart A receives `row_count`, `provenance` (build_id / ayanamsha_id /
 * computed_at) and up to 3 `sample_rows` — including `value_text` — computed
 * across EVERY chart in the database.
 *
 * That is a cross-tenant read through an authorized door: the authz check
 * passes and then the query ignores it. The `pyramid_layers` read on the same
 * route already scopes by `chart_id = $1`, which is exactly the shape the
 * `chart_facts` reads must match.
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

const OWNED_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const OWNER_UID = 'owner-uid'
const ASSET_KEY = 'chart_facts'

function makeReq(): NextRequest {
  return new NextRequest(`http://localhost/api/assets/${OWNED_CHART}/${ASSET_KEY}`, { method: 'GET' })
}

function makeParams(): { params: Promise<{ chart_id: string; asset_key: string }> } {
  return { params: Promise.resolve({ chart_id: OWNED_CHART, asset_key: ASSET_KEY }) }
}

/** Every SQL statement issued against chart_facts, with its bound params. */
function chartFactsCalls(): Array<{ sql: string; params: unknown[] }> {
  return mockQuery.mock.calls
    .filter((call: unknown[]) => /FROM chart_facts/.test(call[0] as string))
    .map((call: unknown[]) => ({ sql: call[0] as string, params: (call[1] as unknown[]) ?? [] }))
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'guest' }], rowCount: 1 })
    if (/FROM chart_grants/.test(sql)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/owner_id[\s\S]*FROM charts/.test(sql)) {
      return Promise.resolve({ rows: [{ owner_id: OWNER_UID }], rowCount: 1 })
    }
    if (/COUNT\(\*\) as count/.test(sql)) return Promise.resolve({ rows: [{ count: '42' }], rowCount: 1 })
    if (/build_id, provenance, created_at/.test(sql)) {
      return Promise.resolve({
        rows: [{ build_id: 'b-1', provenance: { ayanamsha_id: 'lahiri' }, created_at: '2026-08-01T00:00:00Z' }],
        rowCount: 1,
      })
    }
    if (/FROM pyramid_layers/.test(sql)) return Promise.resolve({ rows: [{ status: 'lit' }], rowCount: 1 })
    if (/fact_id, category, divisional_chart/.test(sql)) {
      return Promise.resolve({ rows: [], rowCount: 0 })
    }
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
})

describe('GET /api/assets/[chart_id]/[asset_key] — V3-E-020 chart_facts row scoping', () => {
  it('issues all three chart_facts reads', async () => {
    await GET(makeReq(), makeParams())
    expect(chartFactsCalls()).toHaveLength(3)
  })

  it('constrains EVERY chart_facts read to the requested chart_id', async () => {
    await GET(makeReq(), makeParams())
    for (const call of chartFactsCalls()) {
      expect(call.sql).toMatch(/chart_id\s*=\s*\$\d/)
    }
  })

  // Position-pinned, not `toContain`: an order-insensitive membership check
  // cannot catch a swapped binding (`[assetKey, chartId]`), which would make
  // the predicate read `chart_id = 'chart_facts'`. That fails closed rather
  // than leaking, but it is a silent functional break worth pinning.
  it('binds the requested chart_id as $1 on every chart_facts read', async () => {
    await GET(makeReq(), makeParams())
    for (const call of chartFactsCalls()) {
      expect(call.params[0]).toBe(OWNED_CHART)
      expect(call.params[1]).toBe(ASSET_KEY)
    }
  })
})

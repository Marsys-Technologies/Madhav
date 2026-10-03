/**
 * Pravāha A2.5 / ASTRA v1.0 A9 — cockpit planning must exclude INACTIVE
 * assets, consistent with execution preparation.
 *
 * Before this fix the registry query selected every `has_writer = true` row
 * regardless of `is_active`, so an inert asset (the A2.5 '4.1' candidate is
 * seeded `is_active = false` precisely so no planner ever picks it up) still
 * appeared in cockpit plan previews — while runPreparation.ts (the execution
 * path) filters `WHERE is_active = true`. Plan and execution disagreed.
 *
 * This test invokes the real route with a mocked db client and asserts:
 *   1. the registry query's has_writer branch requires is_active = true;
 *   2. that predicate is the SAME predicate execution preparation applies
 *      (runPreparation.ts: `WHERE is_active = true`) — asserted against the
 *      real source so the two surfaces cannot drift apart again;
 *   3. end-to-end through the route: an inactive has_writer asset row that
 *      the query WOULD have returned under the old predicate never reaches
 *      the plan because the SQL now excludes it (the mock honours the
 *      predicate by inspection).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { POST } from '../route'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const UID = 'owner-uid'

function makeReq(): NextRequest {
  return new NextRequest('http://localhost/api/cockpit/plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chart_id: CHART, scope: 'layer', scope_target: 'kala', action: 'build' }),
  })
}

let registrySql = ''

beforeEach(() => {
  vi.clearAllMocks()
  registrySql = ''
  mockGetServerUser.mockResolvedValue({ uid: UID })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'guest' }], rowCount: 1 })
    if (/owner_id[\s\S]*FROM charts/.test(sql)) return Promise.resolve({ rows: [{ owner_id: UID }], rowCount: 1 })
    if (/FROM asset_registry/.test(sql)) {
      registrySql = sql
      // Honour the predicate like postgres would: the inactive candidate row
      // comes back ONLY when the query fails to require is_active = true.
      const excludesInactive = /has_writer\s*=\s*true\s+AND\s+is_active\s*=\s*true/.test(sql)
      const rows = [
        { asset_id: 'ka_kshetra', layer: 'kala', depends_on: [], estimated_seconds: 60 },
        ...(excludesInactive
          ? []
          : [{ asset_id: 'ka_gochara_v4_41_candidate', layer: 'kala', depends_on: [], estimated_seconds: null }]),
      ]
      return Promise.resolve({ rows, rowCount: rows.length })
    }
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
})

describe('POST /api/cockpit/plan — A9 inactive-asset exclusion (ASTRA A2.5)', () => {
  it('the registry query requires is_active = true in the has_writer branch', async () => {
    const res = await POST(makeReq())
    expect(res.status).toBe(200)
    expect(registrySql).toMatch(/has_writer\s*=\s*true\s+AND\s+is_active\s*=\s*true/)
  })

  it('is consistent with execution preparation (runPreparation filters is_active = true)', () => {
    const prep = readFileSync(
      join(__dirname, '../../../../../lib/build/runPreparation.ts'), 'utf8')
    // the execution path's registry read
    expect(prep).toMatch(/WHERE is_active = true/)
    // and the cockpit plan route now applies the same gate
    const route = readFileSync(join(__dirname, '../route.ts'), 'utf8')
    expect(route).toMatch(/has_writer = true AND is_active = true/)
  })

  it('an inactive has_writer asset never reaches plan_waves', async () => {
    const res = await POST(makeReq())
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.data.plan_waves.flat()).not.toContain('ka_gochara_v4_41_candidate')
    expect(body.data.plan_waves.flat()).toContain('ka_kshetra')
  })
})

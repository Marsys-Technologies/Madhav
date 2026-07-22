/**
 * G2_authz_live gate — Unit 2c (Stream B).
 *
 * Pure-unit tests for authorizeChartAccess; no real DB. The mock DbLike returns
 * canned rows per SQL fragment.
 */
import { describe, it, expect } from 'vitest'
import {
  authorizeChartAccess,
  type DbLike,
  type Principal,
} from '../authorizeChartAccess'

type FakeRowMap = {
  owner?: { owner_id: string | null } | undefined
  grant?: { permission: string } | undefined
}

function makeDb(rows: FakeRowMap): DbLike {
  return {
    async query<T = Record<string, unknown>>(
      sql: string,
      _params?: unknown[]
    ): Promise<{ rows: T[] }> {
      if (sql.includes('FROM charts')) {
        return { rows: rows.owner ? [rows.owner as unknown as T] : [] }
      }
      if (sql.includes('FROM chart_grants')) {
        return { rows: rows.grant ? [rows.grant as unknown as T] : [] }
      }
      return { rows: [] }
    },
  }
}

const guest: Principal = { uid: 'firebase-uid-guest-1', role: 'guest' }
const superAdmin: Principal = { uid: 'firebase-uid-admin', role: 'super_admin' }
const chartId = 'chart-uuid-abc'

describe('authorizeChartAccess (G2 gate)', () => {
  it("super_admin returns 'all' for an existing chart", async () => {
    // Chart exists (owner row present) — super_admin short-circuits to 'all'.
    const db = makeDb({ owner: { owner_id: 'someone-else' } })
    const perm = await authorizeChartAccess({
      principal: superAdmin,
      chartId,
      db,
    })
    expect(perm).toBe('all')
  })

  it("super_admin returns 'deny' (not a silent grant) for a non-existent chart_id", async () => {
    // RC-12 regression: no owner row (chart doesn't exist) must produce a
    // clean not-found even for super_admin — never a silent 'all' grant.
    const db = makeDb({})
    const perm = await authorizeChartAccess({
      principal: superAdmin,
      chartId: 'does-not-exist',
      db,
    })
    expect(perm).toBe('deny')
  })

  it("owner returns 'all'", async () => {
    const db = makeDb({ owner: { owner_id: guest.uid } })
    const perm = await authorizeChartAccess({ principal: guest, chartId, db })
    expect(perm).toBe('all')
  })

  it("granted principal returns 'view'", async () => {
    const db = makeDb({
      owner: { owner_id: 'someone-else' },
      grant: { permission: 'view' },
    })
    const perm = await authorizeChartAccess({ principal: guest, chartId, db })
    expect(perm).toBe('view')
  })

  it("non-granted/non-owner returns 'deny'", async () => {
    const db = makeDb({ owner: { owner_id: 'someone-else' } })
    const perm = await authorizeChartAccess({ principal: guest, chartId, db })
    expect(perm).toBe('deny')
  })

  it("chart not found (no owner row) returns 'deny' for non-admin", async () => {
    const db = makeDb({})
    const perm = await authorizeChartAccess({ principal: guest, chartId, db })
    expect(perm).toBe('deny')
  })

  it("null owner_id treated as no-match (returns 'deny' when no grant)", async () => {
    const db = makeDb({ owner: { owner_id: null } })
    const perm = await authorizeChartAccess({ principal: guest, chartId, db })
    expect(perm).toBe('deny')
  })
})

/**
 * Tests for the shared auth + chart resolution stage.
 *
 * Mirrors the inline behaviour of consult/route.ts lines 218–319 — the
 * route's golden transcript depends on this stage producing identical
 * outcomes (AC.3).
 */

import { describe, it, expect } from 'vitest'
import { resolveAuthAndChart } from '../auth_and_chart'
import type { DbLike } from '@/lib/auth/authorizeChartAccess'

const GOOD_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

function makeDb(opts: {
  chart?: { id: string; client_id: string }
  role?: string
  grants?: Array<{ chart_id: string; principal_id: string; permission: string }>
  throwOnQuery?: boolean
}): DbLike {
  return {
    async query<T>(sql: string, params?: unknown[]) {
      if (opts.throwOnQuery) throw new Error('db down')
      if (/FROM charts WHERE id=\$1/i.test(sql)) {
        if (!opts.chart) return { rows: [] }
        return {
          rows: [
            {
              id: opts.chart.id,
              name: 'Subject',
              birth_date: '1984-02-05',
              birth_time: '10:43:00',
              birth_place: 'Bhubaneswar',
              client_id: opts.chart.client_id,
              owner_id: opts.chart.client_id,
            },
          ] as unknown as T[],
        }
      }
      if (/FROM profiles WHERE id=\$1/i.test(sql)) {
        return { rows: (opts.role ? [{ role: opts.role }] : []) as unknown as T[] }
      }
      if (/FROM chart_grants/i.test(sql)) {
        const cid = String(params?.[0] ?? '')
        const pid = String(params?.[1] ?? '')
        const g = (opts.grants ?? []).find(
          x => x.chart_id === cid && x.principal_id === pid,
        )
        return { rows: g ? ([{ permission: g.permission }] as unknown as T[]) : [] }
      }
      return { rows: [] }
    },
  }
}

describe('resolveAuthAndChart', () => {
  it('rejects invalid chart_id shape', async () => {
    const db = makeDb({})
    const r = await resolveAuthAndChart({ userUid: 'u1', chartId: 'not-a-uuid', db })
    expect(r.ok).toBe(false)
    if (!r.ok) expect(r.reason).toBe('invalid_chart_id')
  })

  it('returns chart_not_found when SELECT returns no rows', async () => {
    const db = makeDb({})
    const r = await resolveAuthAndChart({ userUid: 'u1', chartId: GOOD_UUID, db })
    expect(r.ok).toBe(false)
    if (!r.ok) expect(r.reason).toBe('chart_not_found')
  })

  it('returns db_error when the query throws', async () => {
    const db = makeDb({ throwOnQuery: true })
    const r = await resolveAuthAndChart({ userUid: 'u1', chartId: GOOD_UUID, db })
    expect(r.ok).toBe(false)
    if (!r.ok) expect(r.reason).toBe('db_error')
  })

  it("returns forbidden when authorizeChartAccess yields 'deny'", async () => {
    const db = makeDb({
      chart: { id: GOOD_UUID, client_id: 'someone-else' },
    })
    const r = await resolveAuthAndChart({ userUid: 'u1', chartId: GOOD_UUID, db })
    expect(r.ok).toBe(false)
    if (!r.ok) expect(r.reason).toBe('forbidden')
  })

  it('returns ok=true with super_admin principal', async () => {
    const db = makeDb({ chart: { id: GOOD_UUID, client_id: 'other' }, role: 'super_admin' })
    const r = await resolveAuthAndChart({ userUid: 'u1', chartId: GOOD_UUID, db })
    expect(r.ok).toBe(true)
    if (r.ok) {
      expect(r.ctx.auth.isSuperAdmin).toBe(true)
      expect(r.ctx.auth.permission).toBe('all')
      expect(r.ctx.chart.chartId).toBe(GOOD_UUID)
    }
  })

  it("returns ok=true with 'view' permission via chart_grants", async () => {
    const db = makeDb({
      chart: { id: GOOD_UUID, client_id: 'owner-other' },
      grants: [{ chart_id: GOOD_UUID, principal_id: 'u1', permission: 'view' }],
    })
    const r = await resolveAuthAndChart({ userUid: 'u1', chartId: GOOD_UUID, db })
    expect(r.ok).toBe(true)
    if (r.ok) {
      expect(r.ctx.auth.isSuperAdmin).toBe(false)
      expect(r.ctx.auth.permission).toBe('view')
    }
  })
})

/**
 * DELETE /api/charts/[id] — DEFAULT behaviour (chart deletion unavailable).
 *
 * The route is unsound today (CHART_DELETION_COMPLETENESS_DESIGN section 2.1):
 * its transaction control goes through the pool-level query(), and its first
 * statement targets a relation that does not exist, so it can lose part of a
 * user's data and cannot complete. Until the full deletion program lands the
 * route refuses up front: no transaction, no DELETE, a stable 503 code.
 * The real availability module is used here (not mocked): flipping its default
 * turns this file red.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'
import { makeFakeDeletePool } from './_fakeDeletePool'

vi.mock('server-only', () => ({}))

const { mockGetServerUser, mockQuery, mockGetPool } = vi.hoisted(() => ({
  mockGetServerUser: vi.fn(),
  mockQuery: vi.fn(),
  mockGetPool: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery, getPool: mockGetPool }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: vi.fn() }))
vi.mock('@/lib/auth/requireChartPermission', () => ({ requireChartPermission: vi.fn() }))
vi.mock('@/lib/charts/recomputeChart', () => ({
  ChartUpdateError: class extends Error {},
  updateChartAndMaybeRecompute: vi.fn(),
}))

import { DELETE } from '../route'
import {
  CHART_DELETION_ENABLED,
  CHART_DELETION_UNAVAILABLE_CODE,
} from '@/lib/charts/chartDeletionAvailability'

const CHART = '482012f1-0000-4000-8000-000000000001'
const ctx = { params: Promise.resolve({ id: CHART }) }
const del = () => new NextRequest(`http://localhost/api/charts/${CHART}`, { method: 'DELETE' })

function wire(opts: Parameters<typeof makeFakeDeletePool>[0] = {}) {
  const fake = makeFakeDeletePool(opts)
  mockQuery.mockImplementation((sql: string, params?: unknown[]) => fake.pool.query(sql, params))
  mockGetPool.mockResolvedValue(fake.pool)
  return fake
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetServerUser.mockResolvedValue({ uid: 'owner-uid' })
})

describe('DELETE /api/charts/[id] — default: deletion unavailable', () => {
  it('ships with the availability flag OFF', () => {
    expect(CHART_DELETION_ENABLED).toBe(false)
  })

  it('refuses an authorized owner with a stable 503 and deletes nothing', async () => {
    const fake = wire()
    const res = await DELETE(del(), ctx)
    expect(res.status).toBe(503)
    const body = await res.json()
    expect(body.code).toBe(CHART_DELETION_UNAVAILABLE_CODE)
    expect(body.code).toBe('CHART_DELETION_UNAVAILABLE')
    expect(body.error).toMatch(/chart deletion is temporarily unavailable/i)
    expect(fake.rowsLeft()).toBe(3)
  })

  it('issues no statement beyond the two auth queries: no BEGIN, no DELETE, no connection checkout', async () => {
    const fake = wire()
    await DELETE(del(), ctx)
    expect(fake.log.map((l) => l.sql)).toEqual([
      'SELECT role FROM profiles WHERE id = $1',
      'SELECT owner_id, client_id FROM charts WHERE id = $1',
    ])
    expect(fake.log.some((l) => /BEGIN|DELETE|COMMIT|ROLLBACK/.test(l.sql))).toBe(false)
    expect(mockGetPool).not.toHaveBeenCalled()
    expect(fake.releases).toEqual([])
  })

  it('a super_admin who is not the owner is refused the same way', async () => {
    const fake = wire({ role: 'super_admin', owner: 'someone-else' })
    const res = await DELETE(del(), ctx)
    expect(res.status).toBe(503)
    expect(fake.log.length).toBe(2)
    expect(mockGetPool).not.toHaveBeenCalled()
  })

  it('auth checks still run first: 401 without a session (no query at all)', async () => {
    const fake = wire()
    mockGetServerUser.mockResolvedValue(null)
    const res = await DELETE(del(), ctx)
    expect(res.status).toBe(401)
    expect(fake.log).toEqual([])
  })

  it('auth checks still run first: 403 for a non-owner guest, 404 for an absent chart', async () => {
    wire({ owner: 'someone-else' })
    const forbidden = await DELETE(del(), ctx)
    expect(forbidden.status).toBe(403)

    mockQuery.mockImplementation(async (sql: string) =>
      /FROM profiles/.test(sql) ? { rows: [{ role: 'guest' }] } : { rows: [] },
    )
    const absent = await DELETE(del(), ctx)
    expect(absent.status).toBe(404)
    expect(mockGetPool).not.toHaveBeenCalled()
  })
})

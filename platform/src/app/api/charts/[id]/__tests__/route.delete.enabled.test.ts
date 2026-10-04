/**
 * DELETE /api/charts/[id] — behaviour when the availability flag is ON.
 *
 * The flag is forced on here so the dedicated-connection transaction code stays
 * proven for the day the full deletion program enables it. The central claim:
 * BEGIN ... COMMIT/ROLLBACK run on ONE checked-out connection and cannot escape
 * to another pooled connection, even with an unrelated request interleaved
 * (design report fixture: a ROLLBACK that left 3 of 3 deleted rows deleted).
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
vi.mock('@/lib/charts/chartDeletionAvailability', () => ({
  CHART_DELETION_ENABLED: true,
  CHART_DELETION_UNAVAILABLE_CODE: 'CHART_DELETION_UNAVAILABLE',
  CHART_DELETION_UNAVAILABLE_MESSAGE: 'unavailable',
}))

import { DELETE } from '../route'

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

describe('DELETE /api/charts/[id] — flag ON: one dedicated connection', () => {
  it('runs BEGIN, every DELETE and COMMIT on a single connection, then releases it once', async () => {
    const fake = wire()
    const res = await DELETE(del(), ctx)
    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ deleted: true, chart_id: CHART })

    const tx = fake.txStatements()
    expect(tx[0].sql).toBe('BEGIN')
    expect(tx[tx.length - 1].sql).toBe('COMMIT')
    expect(tx.filter((l) => /^DELETE FROM/.test(l.sql)).length).toBeGreaterThanOrEqual(3)
    expect(new Set(tx.map((l) => l.conn)).size).toBe(1)
    expect(fake.rowsLeft()).toBe(0)
    expect(fake.releases).toHaveLength(1)
    expect(fake.releases[0].err).toBeUndefined()
  })

  it('a mid-transaction failure ROLLS BACK on that same connection and keeps 3 of 3 rows', async () => {
    const fake = wire({ failOn: 'DELETE FROM charts' })
    const res = await DELETE(del(), ctx)
    expect(res.status).toBe(500)
    expect(await res.json()).toEqual({ error: 'Delete failed' })

    const tx = fake.txStatements()
    expect(tx[tx.length - 1].sql).toBe('ROLLBACK')
    expect(new Set(tx.map((l) => l.conn)).size).toBe(1)
    expect(tx.some((l) => l.sql === 'COMMIT')).toBe(false)
    expect(fake.rowsLeft()).toBe(3)
    expect(fake.releases).toHaveLength(1)
  })

  it('an unrelated request interleaved mid-transaction cannot capture the transaction', async () => {
    const fake = wire({ failOn: 'DELETE FROM charts', gateOn: 'DELETE FROM asset_throughput' })
    const pending = DELETE(del(), ctx)
    await fake.gateReached

    // another request's pool-level statement arrives while the delete is open
    await mockQuery('SELECT 1 /* unrelated request */', [])
    fake.gate.release()
    const res = await pending

    expect(res.status).toBe(500)
    const tx = fake.txStatements().filter((l) => !/unrelated request/.test(l.sql))
    const txConn = tx[0].conn
    expect(tx.every((l) => l.conn === txConn)).toBe(true)
    const other = fake.log.find((l) => /unrelated request/.test(l.sql))!
    expect(other.conn).not.toBe(txConn)
    expect(fake.rowsLeft()).toBe(3)
  })

  it('discards (release(err)) a connection whose ROLLBACK itself fails, and still answers 500', async () => {
    const fake = wire({ failOn: 'DELETE FROM charts', failRollback: true })
    const res = await DELETE(del(), ctx)
    expect(res.status).toBe(500)
    expect(fake.releases).toHaveLength(1)
    expect(fake.releases[0].err).toBeTruthy()
  })

  it('a failure checking out the connection is a 500 and issues no DELETE', async () => {
    const fake = wire()
    mockGetPool.mockResolvedValue({
      connect: async () => {
        throw new Error('pool exhausted')
      },
    })
    const res = await DELETE(del(), ctx)
    expect(res.status).toBe(500)
    expect(fake.log.some((l) => /DELETE/.test(l.sql))).toBe(false)
  })

  it('authorization still precedes the transaction (403 for a non-owner opens nothing)', async () => {
    wire({ owner: 'someone-else' })
    const res = await DELETE(del(), ctx)
    expect(res.status).toBe(403)
    expect(mockGetPool).not.toHaveBeenCalled()
  })
})

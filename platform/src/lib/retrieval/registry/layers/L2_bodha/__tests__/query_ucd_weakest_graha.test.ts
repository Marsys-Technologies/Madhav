/**
 * CR-55 residual fix (flagged by L4's Night-1 reconciliation pass) — deriveShadbalaWeakestGraha
 * must never return a shadow point (Rahu/Ketu) as the "weakest graha," even though their
 * shadbala_total values are always lower than the seven classical grahas'. Chart 482012f1's
 * classical-graha minimum is Venus (4.64); before this fix the query's bare MIN() returned
 * Rahu (0.375) because it had no exclusion for shadow points.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { deriveShadbalaWeakestGraha } from '../query_ucd'

describe('CR-55 — deriveShadbalaWeakestGraha excludes shadow points', () => {
  beforeEach(() => queryMock.mockReset())

  it('returns Venus as weakest on 482012f1-shaped data, not Rahu', async () => {
    // The mock simulates the SQL's own filter: shadow points are excluded before ORDER BY/LIMIT,
    // so a correct query never sees them in its result set at all.
    queryMock.mockResolvedValueOnce({ rows: [{ fact_subject: 'VEN', fact_value_num: 4.64 }] })
    const result = await deriveShadbalaWeakestGraha('482012f1-710e-4a25-994a-93821f5871aa', 'lahiri_chitrapaksha')
    expect(result?.graha).toBe('Venus')
    expect(result?.shadbala_rupa).toBe(4.64)
  })

  it('passes a query that excludes RAH_MEAN and KET_MEAN', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })
    await deriveShadbalaWeakestGraha('some-chart-id', 'lahiri_chitrapaksha')
    const [sql] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).toMatch(/RAH_MEAN/)
    expect(sql).toMatch(/KET_MEAN/)
    expect(sql).toMatch(/NOT IN/)
  })

  it('returns null (never fabricated) when the query throws', async () => {
    queryMock.mockRejectedValueOnce(new Error('db unavailable'))
    const result = await deriveShadbalaWeakestGraha('x', 'lahiri_chitrapaksha')
    expect(result).toBeNull()
  })

  it('returns null when no classical graha has a shadbala row', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })
    const result = await deriveShadbalaWeakestGraha('x', 'lahiri_chitrapaksha')
    expect(result).toBeNull()
  })
})

import { beforeEach, describe, expect, it, vi } from 'vitest'

const { query, probe } = vi.hoisted(() => ({ query: vi.fn(), probe: vi.fn() }))
vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query }))
vi.mock('@/lib/db/columnPresence', () => ({ blockedByAssetIdColumnPresent: probe }))

import { readBuildRunAssets } from '../runAssets'

beforeEach(() => vi.resetAllMocks())

describe('Build run-assets read owner', () => {
  it.each([true, false])('retains the exact projection and optional-column branch (%s)', async present => {
    const rows = [{ asset_id: 'bo_cdlm_summary', rows_written: 70, error: null }]
    probe.mockResolvedValue(present)
    query.mockResolvedValue({ rows })
    expect(await readBuildRunAssets('run-1')).toBe(rows)
    expect(probe).toHaveBeenCalledExactlyOnceWith()
    expect(query).toHaveBeenCalledTimes(1)
    const [sql, binds] = query.mock.calls[0]
    expect(binds).toEqual(['run-1'])
    expect(sql).toContain('at2.rows_written')
    expect(sql).toContain('COALESCE(bra.error, at2.last_error) AS error')
    expect(sql).toContain('(chart_id = br.chart_id OR chart_id IS NULL)')
    expect(sql).toContain('ORDER BY (chart_id IS NOT NULL) DESC')
    expect(sql).toContain('ORDER BY bra.position')
    expect(sql.includes('bra.blocked_by_asset_id')).toBe(present)
    expect(sql.includes('NULL::text AS blocked_by_asset_id')).toBe(!present)
    expect(sql).not.toMatch(/ayanamsha_id/)
  })

  it('preserves successful empty rows', async () => {
    probe.mockResolvedValue(false)
    query.mockResolvedValue({ rows: [] })
    expect(await readBuildRunAssets('empty-run')).toEqual([])
  })

  it('propagates the original probe failure before issuing the data query', async () => {
    const error = new Error('column probe failed')
    probe.mockRejectedValue(error)
    await expect(readBuildRunAssets('run-1')).rejects.toBe(error)
    expect(query).not.toHaveBeenCalled()
  })

  it('propagates the original data-query failure', async () => {
    const error = new Error('read failed')
    probe.mockResolvedValue(true)
    query.mockRejectedValue(error)
    await expect(readBuildRunAssets('run-1')).rejects.toBe(error)
  })
})

import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReactElement } from 'react'

const { query, resolveAccess, redirect } = vi.hoisted(() => ({
  query: vi.fn(), resolveAccess: vi.fn(),
  redirect: vi.fn((url: string): never => { throw new Error(`REDIRECT:${url}`) }),
}))
vi.mock('@/lib/db/client', () => ({ query }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: resolveAccess }))
vi.mock('next/navigation', () => ({ redirect }))
vi.mock('@/components/cockpit/CockpitShell', () => ({ CockpitShell: () => null }))
import Page from '../page'

const chartId = 'synthetic-chart'
const chart = { id: chartId, name: 'Synthetic', birth_date: '2000-01-01', birth_time: '00:00', birth_place: 'Synthetic', created_at: '2026-01-01T00:00:00Z' }
const run = { build_id: 'synthetic-run', status: 'paused', created_at: '2026-01-01T01:00:00Z', ayanamshas: [] }
const chartSql = 'SELECT id, name, birth_date, birth_time::text AS birth_time, birth_place, created_at FROM charts WHERE id=$1'
const runSql = `SELECT id AS build_id, state AS status, created_at, '{}'::text[] AS ayanamshas
       FROM build_runs WHERE chart_id=$1 ORDER BY created_at DESC LIMIT 1`
const input = () => ({ params: Promise.resolve({ id: chartId }) })
const propsOf = (element: ReactElement) => element.props as { chartId: string; chartName: string; birthDate: string; birthTime: string; birthPlace: string; latestBuild: unknown; latestBuildUnavailable?: boolean }
beforeEach(() => {
  vi.clearAllMocks()
  resolveAccess.mockResolvedValue({ canBuild: true })
  query.mockImplementation((sql: string) => Promise.resolve({ rows: sql === chartSql ? [chart] : [] }))
})

describe('saved cockpit latest run read boundary', () => {
  it('redirects unauthenticated before any chart or run read', async () => {
    resolveAccess.mockResolvedValue(null)
    await expect(Page(input())).rejects.toThrow('REDIRECT:/login')
    expect(query).not.toHaveBeenCalled()
  })

  it('retains view-only redirect to Folio before any chart or run read', async () => {
    resolveAccess.mockResolvedValue({ canBuild: false })
    await expect(Page(input())).rejects.toThrow(`REDIRECT:/clients/${chartId}`)
    expect(query).not.toHaveBeenCalled()
  })

  it('retains missing chart redirect without looking for a run', async () => {
    query.mockResolvedValue({ rows: [] })
    await expect(Page(input())).rejects.toThrow('REDIRECT:/dashboard')
    expect(query.mock.calls).toEqual([[chartSql, [chartId]]])
  })

  it('preserves successful empty lookup, exact query order/binds and explicit availability', async () => {
    const props = propsOf(await Page(input()))
    expect(props.latestBuild).toBeNull()
    expect(props.latestBuildUnavailable).toBe(false)
    expect(query.mock.calls).toEqual([[chartSql, [chartId]], [runSql, [chartId]]])
    expect(resolveAccess).toHaveBeenCalledExactlyOnceWith(chartId)
    expect(resolveAccess.mock.invocationCallOrder[0]).toBeLessThan(query.mock.invocationCallOrder[0])
  })

  it('preserves the current known row and authorized chart identity fields', async () => {
    query.mockImplementation((sql: string) => Promise.resolve({ rows: sql === chartSql ? [chart] : [run] }))
    const props = propsOf(await Page(input()))
    expect(props).toEqual({ chartId, chartName: chart.name, birthDate: chart.birth_date, birthTime: chart.birth_time, birthPlace: chart.birth_place, latestBuild: run, latestBuildUnavailable: false })
    expect(query.mock.calls).toEqual([[chartSql, [chartId]], [runSql, [chartId]]])
  })

  it('distinguishes latest lookup failure from absence while retaining independent chart fields', async () => {
    query.mockImplementation((sql: string) => sql === chartSql ? Promise.resolve({ rows: [chart] }) : Promise.reject(new Error('PRIVATE_SQL_DETAIL')))
    const props = propsOf(await Page(input()))
    expect(props).toEqual({ chartId, chartName: chart.name, birthDate: chart.birth_date, birthTime: chart.birth_time, birthPlace: chart.birth_place, latestBuild: null, latestBuildUnavailable: true })
    expect(JSON.stringify(props)).not.toContain('PRIVATE_SQL_DETAIL')
    expect(query.mock.calls).toEqual([[chartSql, [chartId]], [runSql, [chartId]]])
    expect(redirect).not.toHaveBeenCalled()
  })

  it('does not broaden the catch to hide a chart metadata failure', async () => {
    query.mockRejectedValue(new Error('CHART_READ_FAILURE'))
    await expect(Page(input())).rejects.toThrow('CHART_READ_FAILURE')
    expect(query.mock.calls).toEqual([[chartSql, [chartId]]])
  })

  it('preserves a guard failure before any data read', async () => {
    resolveAccess.mockRejectedValue(new Error('GUARD_FAILURE'))
    await expect(Page(input())).rejects.toThrow('GUARD_FAILURE')
    expect(query).not.toHaveBeenCalled()
  })
})

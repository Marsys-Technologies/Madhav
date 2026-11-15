import { beforeEach, describe, expect, it, vi } from 'vitest'
const { queryMock, accessMock, redirectMock, shellMock, events } = vi.hoisted(() => {
  const events: string[] = []
  return {
    events,
    queryMock: vi.fn(),
    accessMock: vi.fn(),
    redirectMock: vi.fn((url: string) => { events.push(`redirect:${url}`); throw new Error(`redirect:${url}`) }),
    shellMock: vi.fn(),
  }
})
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: accessMock }))
vi.mock('next/navigation', () => ({ redirect: redirectMock }))
vi.mock('@/components/cockpit/CockpitShell', () => ({ CockpitShell: shellMock }))
vi.mock('server-only', () => ({}))
import * as owner from '../cockpitLatestBuild'
import CockpitPage from '@/app/clients/[id]/cockpit/page'

const CHART_SQL = 'SELECT id, name, birth_date, birth_time::text AS birth_time, birth_place, created_at FROM charts WHERE id=$1'
const BUILD_SQL = `SELECT id AS build_id, state AS status, created_at
       FROM build_runs WHERE chart_id=$1 ORDER BY created_at DESC LIMIT 1`
const chart = { id: 'chart', name: 'Fixture', birth_date: '2000-01-01', birth_time: '10:00:00', birth_place: 'Place', created_at: '2026-01-01' }
const run = { build_id: 'run', status: 'running', created_at: '2026-01-02' }
beforeEach(() => {
  vi.restoreAllMocks()
  queryMock.mockReset()
  accessMock.mockReset()
  redirectMock.mockClear()
  shellMock.mockClear()
  events.length = 0
  accessMock.mockImplementation(async () => { events.push('access'); return { canBuild: true } })
})

describe('Build-owned latest cockpit run projection', () => {
  it('preserves the exact one-query SQL, bind, first row and row identity', async () => {
    queryMock.mockResolvedValue({ rows: [run, { ...run, build_id: 'ignored-second' }] })
    const result = await owner.readCockpitLatestBuild('chart')
    expect(queryMock).toHaveBeenCalledExactlyOnceWith(BUILD_SQL, ['chart'])
    expect(result).toEqual({ latestBuild: run, latestBuildUnavailable: false })
    expect(result.latestBuild).toBe(run)
  })
  it('keeps an empty observed run as null with unavailable false', async () => {
    queryMock.mockResolvedValue({ rows: [] })
    expect(await owner.readCockpitLatestBuild('chart')).toEqual({ latestBuild: null, latestBuildUnavailable: false })
    expect(queryMock).toHaveBeenCalledOnce()
  })
  it.each(['rejected query', 'synchronous query error'])('keeps %s unavailable without inventing a run', async kind => {
    if (kind === 'rejected query') queryMock.mockRejectedValue(new Error('synthetic table absent'))
    else queryMock.mockImplementation(() => { throw new Error('synthetic table absent') })
    expect(await owner.readCockpitLatestBuild('chart')).toEqual({ latestBuild: null, latestBuildUnavailable: true })
    expect(queryMock).toHaveBeenCalledExactlyOnceWith(BUILD_SQL, ['chart'])
  })
})

describe('actual chart cockpit page owner connection and Identity gate', () => {
  it.each(['observed run', 'empty run', 'unavailable run'])('preserves page props and actual connected owner order: %s', async kind => {
    queryMock.mockImplementation(async (sql: string) => {
      if (sql === CHART_SQL) { events.push('chart'); return { rows: [chart] } }
      expect(sql).toBe(BUILD_SQL)
      events.push('build')
      if (kind === 'unavailable run') throw new Error('synthetic table absent')
      return { rows: kind === 'empty run' ? [] : [run] }
    })
    const read = vi.spyOn(owner, 'readCockpitLatestBuild')
    const result = await CockpitPage({ params: Promise.resolve({ id: 'chart' }) })
    expect(read).toHaveBeenCalledExactlyOnceWith('chart')
    expect(events).toEqual(['access', 'chart', 'build'])
    expect(queryMock.mock.calls).toEqual([[CHART_SQL, ['chart']], [BUILD_SQL, ['chart']]])
    expect(result.type).toBe(shellMock)
    expect(result.props).toEqual({
      chartId: 'chart', chartName: chart.name, birthDate: chart.birth_date,
      birthTime: chart.birth_time, birthPlace: chart.birth_place,
      latestBuild: kind === 'observed run' ? run : null,
      latestBuildUnavailable: kind === 'unavailable run',
    })
  })
  it('awaits params before access and data', async () => {
    let resolve!: (value: { id: string }) => void
    const params = new Promise<{ id: string }>(done => { resolve = done })
    queryMock.mockImplementation(async (sql: string) => ({ rows: sql === CHART_SQL ? [chart] : [] }))
    const pending = CockpitPage({ params })
    expect(accessMock).not.toHaveBeenCalled()
    expect(queryMock).not.toHaveBeenCalled()
    resolve({ id: 'chart' })
    await pending
    expect(accessMock).toHaveBeenCalledExactlyOnceWith('chart')
  })
  it('retains login redirect without chart/build reads for denied access', async () => {
    accessMock.mockResolvedValue(null)
    const read = vi.spyOn(owner, 'readCockpitLatestBuild')
    await expect(CockpitPage({ params: Promise.resolve({ id: 'chart' }) })).rejects.toThrow('redirect:/login')
    expect(redirectMock).toHaveBeenCalledExactlyOnceWith('/login')
    expect(queryMock).not.toHaveBeenCalled()
    expect(read).not.toHaveBeenCalled()
  })
  it('retains chart redirect before data reads when build access is absent', async () => {
    accessMock.mockResolvedValue({ canBuild: false })
    const read = vi.spyOn(owner, 'readCockpitLatestBuild')
    await expect(CockpitPage({ params: Promise.resolve({ id: 'chart' }) })).rejects.toThrow('redirect:/clients/chart')
    expect(redirectMock).toHaveBeenCalledExactlyOnceWith('/clients/chart')
    expect(queryMock).not.toHaveBeenCalled()
    expect(read).not.toHaveBeenCalled()
  })
  it('keeps missing chart redirect before the Build owner', async () => {
    queryMock.mockResolvedValue({ rows: [] })
    const read = vi.spyOn(owner, 'readCockpitLatestBuild')
    await expect(CockpitPage({ params: Promise.resolve({ id: 'chart' }) })).rejects.toThrow('redirect:/dashboard')
    expect(queryMock).toHaveBeenCalledExactlyOnceWith(CHART_SQL, ['chart'])
    expect(read).not.toHaveBeenCalled()
  })
  it('does not swallow Identity chart-read failure as Build unavailability', async () => {
    const error = new Error('synthetic chart query failure')
    queryMock.mockRejectedValue(error)
    const read = vi.spyOn(owner, 'readCockpitLatestBuild')
    await expect(CockpitPage({ params: Promise.resolve({ id: 'chart' }) })).rejects.toBe(error)
    expect(queryMock).toHaveBeenCalledExactlyOnceWith(CHART_SQL, ['chart'])
    expect(read).not.toHaveBeenCalled()
  })
})

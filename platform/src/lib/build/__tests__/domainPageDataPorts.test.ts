import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { NextRequest, NextResponse } from 'next/server'
import type { ReactElement } from 'react'

const h = vi.hoisted(() => ({ query: vi.fn(), principal: vi.fn(), chartAccess: vi.fn(), admin: vi.fn(), atlasGuard: vi.fn(), activeGuard: vi.fn(), session: vi.fn(), permission: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: h.query }))
vi.mock('@/lib/auth/access-control', () => ({ getServerUserWithProfile: h.principal, requireSuperAdmin: h.admin }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: h.chartAccess }))
vi.mock('@/lib/auth/super-admin-page-guard', () => ({ requireSuperAdminPage: h.atlasGuard }))
vi.mock('@/lib/auth/active-user-page-guard', () => ({ requireActiveUserPage: h.activeGuard }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: h.session }))
vi.mock('@/lib/auth/requireChartPermission', () => ({ requireChartPermission: h.permission }))
vi.mock('next/navigation', () => ({ redirect: (path: string) => { throw new Error(`REDIRECT:${path}`) } }))
vi.mock('@/components/timeline/TimelineView', () => ({ TimelineView: () => null }))
vi.mock('@/components/journey1/ChartNav', () => ({ ChartNav: () => null }))
vi.mock('@/components/build/AtlasView', () => ({ AtlasView: () => null }))
vi.mock('@/app/panchang/components/PanchangClientView', () => ({ PanchangClientView: () => null }))

import TrackerPage from '@/app/admin/tracker/page'
import TimelinePage from '@/app/clients/[id]/timeline/page'
import AtlasPage from '@/app/information/atlas/page'
import PanchangPage from '@/app/panchang/page'
import { GET } from '@/app/api/build/pyramid-layers/route'
import { TimelineView } from '@/components/timeline/TimelineView'
import { AtlasView } from '@/components/build/AtlasView'
import { PanchangClientView } from '@/app/panchang/components/PanchangClientView'
import { fetchActiveBuilds, fetchRecentBuilds, fetchAyanamshaMatrix } from '../trackerPageData'
import { readAtlasAssets } from '../atlasPageData'
import { readTimelineEvents } from '@/lib/mimamsa/timelinePageData'
import { readPanchangPageData } from '@/lib/kala/panchangPageData'

function propsOf(node: unknown, type: unknown): Record<string, unknown> | undefined {
  if (!node || typeof node !== 'object') return undefined
  const el = node as ReactElement<Record<string, unknown>>
  if (el.type === type) return el.props
  const children = el.props?.children
  for (const child of Array.isArray(children) ? children : [children]) {
    const found = propsOf(child, type)
    if (found) return found
  }
}
const id = 'fixture-chart'
const fetchMock = vi.fn()
beforeEach(() => {
  vi.resetAllMocks()
  h.query.mockResolvedValue({ rows: [] })
  h.principal.mockResolvedValue({ profile: { role: 'super_admin' } })
  h.chartAccess.mockResolvedValue({ role: 'guest', permission: 'view', canBuild: false })
  h.session.mockResolvedValue({ uid: 'fixture-user' })
  h.permission.mockResolvedValue(null)
  vi.stubGlobal('fetch', fetchMock)
  vi.stubEnv('PYTHON_SIDECAR_URL', 'http://sidecar.invalid')
  vi.stubEnv('PYTHON_SIDECAR_API_KEY', 'fixture-secret')
})
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); vi.restoreAllMocks() })

describe('connected Build tracker/catalog and Mimamsa event ports', () => {
  it('keeps tracker denial before reads and independent null/empty error policies', async () => {
    h.principal.mockResolvedValueOnce(null)
    await expect(TrackerPage()).rejects.toThrow('REDIRECT:/admin')
    expect(h.query).not.toHaveBeenCalled()
    h.query.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ rows: [] })
    await expect(fetchActiveBuilds()).resolves.toBeNull()
    await expect(fetchRecentBuilds()).resolves.toEqual([])
    await expect(fetchAyanamshaMatrix()).resolves.toBeNull()
    expect(h.query.mock.calls.map((call) => call[1])).toEqual([[], []])
  })
  it('gates Atlas before its real port and preserves its row array and propagated error', async () => {
    h.atlasGuard.mockRejectedValueOnce(new Error('denied'))
    await expect(AtlasPage()).rejects.toThrow('denied')
    expect(h.query).not.toHaveBeenCalled()
    const assets = [{ asset_id: 'fixture-asset', count_sql: null }]
    h.query.mockResolvedValueOnce({ rows: assets })
    const view = propsOf(await AtlasPage(), AtlasView)
    expect(view?.assets).toBe(assets)
    expect(view?.defaultChartId).toBe('482012f1-710e-4a25-994a-93821f5871aa')
    expect(h.query.mock.calls[0]).toHaveLength(1)
    h.query.mockRejectedValueOnce(new Error('catalog unavailable'))
    await expect(readAtlasAssets()).rejects.toThrow('catalog unavailable')
  })
  it('keeps timeline admission, existence and old-tab redirect ahead of events', async () => {
    h.chartAccess.mockResolvedValueOnce({ permission: 'deny' })
    await expect(TimelinePage({ params: Promise.resolve({ id }) })).rejects.toThrow('REDIRECT:/dashboard')
    expect(h.query).not.toHaveBeenCalled()
    h.query.mockResolvedValueOnce({ rows: [] })
    await expect(TimelinePage({ params: Promise.resolve({ id }) })).rejects.toThrow('REDIRECT:/dashboard')
    expect(h.query).toHaveBeenCalledTimes(1)
    h.query.mockClear().mockResolvedValueOnce({ rows: [{ name: 'Fixture' }] })
    await expect(TimelinePage({ params: Promise.resolve({ id }), searchParams: Promise.resolve({ tab: 'predictions' }) })).rejects.toThrow(`REDIRECT:/clients/${id}/samiksha`)
    expect(h.query).toHaveBeenCalledExactlyOnceWith('SELECT name FROM charts WHERE id=$1', [id])
    const events = [{ id: 'e1', date: '2001-02', body: 'Fixture', category: 'education', chart_state: {} }]
    h.query.mockClear().mockResolvedValueOnce({ rows: [{ name: 'Fixture' }] }).mockResolvedValueOnce({ rows: events })
    const view = propsOf(await TimelinePage({ params: Promise.resolve({ id }) }), TimelineView)
    expect(view?.events).toBe(events)
    expect(view?.chartId).toBe(id)
    expect(view?.canLogEvent).toBe(false)
    expect(h.admin).not.toHaveBeenCalled()
    expect(h.query.mock.calls[1][1]).toEqual([id])
    expect(h.query.mock.calls[1][0]).toContain('ORDER BY event_date DESC, event_id ASC')
    h.query.mockRejectedValueOnce(new Error('events unavailable'))
    await expect(readTimelineEvents(id)).rejects.toThrow('events unavailable')
  })
})

describe('connected legacy Build pyramid projection', () => {
  const req = () => new NextRequest(`http://fixture.invalid/api/build/pyramid-layers?chart_id=${id}`)
  it('keeps parameter/session/chart denial ahead of domain reads', async () => {
    expect((await GET(new NextRequest('http://fixture.invalid/api/build/pyramid-layers'))).status).toBe(400)
    expect(h.session).not.toHaveBeenCalled()
    h.session.mockResolvedValueOnce(null)
    expect((await GET(req())).status).toBe(401)
    expect(h.permission).not.toHaveBeenCalled()
    h.permission.mockResolvedValueOnce(NextResponse.json({ error: 'deny' }, { status: 403 }))
    expect((await GET(req())).status).toBe(403)
    expect(h.query).not.toHaveBeenCalled()
    expect(h.permission).toHaveBeenCalledWith({ uid: 'fixture-user', chartId: id, access: 'read' })
  })
  it('retains six-layer wire order, legacy precedence, null sublayer and unknown-row policy', async () => {
    h.query.mockResolvedValueOnce({ rows: [
      { layer: 'l0', sublayer: 'bg_fixture', status: 'complete' },
      { layer: 'L1', sublayer: null, status: 'amber' },
      { layer: 'L1', sublayer: 'ga_fixture', status: 'error' },
      { layer: 'L1', sublayer: 'ga_next', status: 'in_progress' },
      { layer: 'L2', sublayer: 'bo_fixture', status: 'failed' },
      { layer: 'L3', sublayer: 'ka_fixture', status: 'attention' },
      { layer: 'L4', sublayer: 'ph_fixture', status: 'unknown' },
      { layer: 'unsupported', sublayer: 'other', status: 'built' },
    ] })
    const body = await (await GET(req())).json()
    expect(body.chart_id).toBe(id)
    expect(body.layers.map((l: { layer: string; status: string }) => [l.layer, l.status])).toEqual([
      ['L0', 'built'], ['L1', 'building'], ['L2', 'failed'], ['L3', 'attention'], ['L4', 'not-built'], ['L5', 'not-built'],
    ])
    expect(body.layers[0]).toEqual({ layer: 'L0', name: 'Brahmagyan — Foundation', status: 'built', asset_count: 1, assets: [{ asset_key: 'bg_fixture', status: 'built' }] })
    expect(body.layers[1].assets[0]).toEqual({ asset_key: '', status: 'attention' })
    expect(body.layers[5]).toEqual({ layer: 'L5', name: 'Mīmāṃsā — Learning', status: 'not-built', asset_count: 0, assets: [] })
    expect(h.query).toHaveBeenCalledExactlyOnceWith(expect.stringContaining('ORDER BY layer, sublayer'), [id])
    h.query.mockRejectedValueOnce(new Error('pyramid unavailable'))
    await expect(GET(req())).rejects.toThrow('pyramid unavailable')
  })
})

describe('connected Kala Panchang SSR transport and mapping', () => {
  it('keeps admission before transport and preserves tuple, key, no-store and mapped wire data', async () => {
    h.activeGuard.mockRejectedValueOnce(new Error('login'))
    await expect(PanchangPage({ searchParams: Promise.resolve({}) })).rejects.toThrow('login')
    expect(fetchMock).not.toHaveBeenCalled()
    const raw = { ok: true, panchang: { tithi: { name: 'Fixture' } } }
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => raw })
    const view = propsOf(await PanchangPage({ searchParams: Promise.resolve({ d: '2020-03-04', lat: '12.5', lon: '77.2' }) }), PanchangClientView)
    expect(fetchMock).toHaveBeenCalledExactlyOnceWith('http://sidecar.invalid/api/compute/panchanga', {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'x-api-key': 'fixture-secret' },
      body: JSON.stringify({ date: '2020-03-04', lat: 12.5, lon: 77.2, tz_offset_minutes: 330 }), cache: 'no-store',
    })
    expect(view).toMatchObject({ initialDate: '2020-03-04', initialLat: 12.5, initialLon: 77.2,
      initialData: { date: '2020-03-04', lat: 12.5, lon: 77.2, tz_offset_minutes: 330, angas: { tithi: { name: 'Fixture' } }, native_context: null } })
    expect((view?.initialData as { raw: unknown }).raw).toBe(raw.panchang)
  })
  it('keeps URL/default/null and error logging behavior', async () => {
    const log = vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.stubEnv('PYTHON_SIDECAR_URL', '')
    await expect(readPanchangPageData('2020-01-01', 1, 2, 330)).resolves.toBeNull()
    expect(fetchMock).not.toHaveBeenCalled()
    vi.stubEnv('PYTHON_SIDECAR_URL', 'http://sidecar.invalid')
    vi.stubEnv('PYTHON_SIDECAR_API_KEY', undefined)
    fetchMock.mockResolvedValueOnce({ ok: false })
    const view = propsOf(await PanchangPage({ searchParams: Promise.resolve({ d: 'bad', lat: 'bad', lon: ['1'] }) }), PanchangClientView)
    expect(view).toMatchObject({ initialLat: 20.27, initialLon: 85.84, initialData: null })
    expect(fetchMock.mock.calls[0][1].headers['x-api-key']).toBe('')
    expect(log).not.toHaveBeenCalled()
    const error = new Error('offline')
    fetchMock.mockRejectedValueOnce(error)
    await expect(readPanchangPageData('2020-01-01', 1, 2, 330)).resolves.toBeNull()
    expect(log).toHaveBeenLastCalledWith('[PanchangPage] SSR sidecar fetch failed:', error)
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => { throw error } })
    await expect(readPanchangPageData('2020-01-01', 1, 2, 330)).resolves.toBeNull()
    expect(log).toHaveBeenCalledTimes(2)
  })
})

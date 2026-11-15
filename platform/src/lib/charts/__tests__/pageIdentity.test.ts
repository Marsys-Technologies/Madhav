import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({ query: vi.fn(), access: vi.fn(), user: vi.fn(),
  readiness: vi.fn(), consumed: vi.fn(), flag: vi.fn(), review: vi.fn(), badge: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mocks.query }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: mocks.access }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mocks.user }))
vi.mock('@/lib/config/index', () => ({ configService: { getFlag: mocks.flag } }))
vi.mock('@/lib/charts/readiness', () => ({ getChartReadinessMap: mocks.readiness, emptyChartReadiness: () => ({ state: 'empty', percent: 0, layerPips: [] }) }))
vi.mock('@/lib/roster/stats', () => ({ fetchConsumedTodayCount: mocks.consumed }))
vi.mock('@/lib/pariprashna/samiksha/review', () => ({ getReviewData: mocks.review }))
vi.mock('@/lib/pariprashna/samiksha/badge', () => ({ countBadge: mocks.badge }))
vi.mock('@/app/clients/[id]/samiksha/actions', () => ({ confirmCandidateAction: vi.fn(), editCandidateAction: vi.fn(), dismissCandidateAction: vi.fn(), resolvePredictionAction: vi.fn(), batchResolveAction: vi.fn() }))
vi.mock('next/navigation', () => ({ redirect: (to: string) => { throw new Error(`redirect:${to}`) } }))
vi.mock('next/headers', () => ({ headers: async () => new Headers() }))
vi.mock('@/lib/build/cockpitLatestBuild', () => ({ readCockpitLatestBuild: vi.fn() }))
vi.mock('@/components/cockpit/CockpitShell', () => ({ CockpitShell: () => null }))
vi.mock('@/lib/components/cockpit/v2/CockpitShell', () => ({ CockpitShell: () => null }))
vi.mock('@/components/clients/EditClientForm', () => ({ EditClientForm: () => null }))
vi.mock('@/components/sharing/SharingPanel', () => ({ SharingPanel: () => null }))
vi.mock('@/components/journey1/JourneyShell', () => ({ JourneyShell: () => null }))
vi.mock('@/components/shared/AppShell', () => ({ AppShell: () => null }))
vi.mock('@/components/shared/ZoneRoot', () => ({ ZoneRoot: () => null }))
vi.mock('@/components/nav/ConditionalChartSwitcherBar', () => ({ ConditionalChartSwitcherBar: () => null }))
vi.mock('@/components/journey1/ChartNav', () => ({ ChartNav: () => null }))
vi.mock('@/components/journey1/Titles', () => ({ PageTitle: () => null }))
vi.mock('@/components/pariprashna/PariprashnaApp', () => ({ PariprashnaApp: () => null }))
vi.mock('@/components/pariprashna/samiksha/SamiksaReview', () => ({ SamiksaReview: () => null }))
vi.mock('@/app/panchang/components/PanchangClientView', () => ({ PanchangClientView: () => null }))
vi.mock('@/components/dashboard/ClientRoster', () => ({ ClientRoster: () => null }))
vi.mock('@/components/brahma/ChartCreatedToast', () => ({ ChartCreatedToast: () => null }))

import * as charts from '../pageIdentity'
import * as roster from '@/lib/roster/pageIdentity'
import * as profiles from '@/lib/auth/pageIdentity'
import Dashboard from '@/app/dashboard/page'
import Layout, { generateMetadata } from '@/app/clients/[id]/layout'
import Panchang from '@/app/clients/[id]/panchang/page'
import Timeline from '@/app/clients/[id]/timeline/layout'
import Consultation from '@/app/clients/[id]/pariprashna/page'
import Review from '@/app/clients/[id]/samiksha/page'
import Cockpit from '@/app/clients/[id]/cockpit/page'
import Edit from '@/app/clients/[id]/edit/page'
import Preparation, { generateMetadata as preparationMetadata } from '@/app/clients/[id]/nirmana/page'

const id = 'synthetic-chart'
const uid = 'synthetic-principal'
const params = Promise.resolve({ id })
const calls = [
  () => Layout({ params, children: null }),
  () => Panchang({ params }),
  () => Timeline({ params, children: null }),
  () => Consultation({ params }),
  () => Review({ params }),
]
beforeEach(() => {
  vi.resetAllMocks()
  mocks.access.mockResolvedValue({ user: { uid }, role: 'guest', permission: 'view', canBuild: false })
  mocks.user.mockResolvedValue({ uid })
  mocks.flag.mockReturnValue(true)
  mocks.query.mockResolvedValue({ rows: [] })
  mocks.readiness.mockResolvedValue(new Map())
  mocks.consumed.mockResolvedValue(0)
  mocks.review.mockResolvedValue({})
  mocks.badge.mockResolvedValue(0)
})

describe('connected Identity page contracts', () => {
  it.each([Cockpit, Edit, Preparation])('retains the build admission bar before identity reads', async page => {
    await expect(page({ params })).rejects.toThrow(`redirect:/clients/${id}`)
    expect(mocks.query).not.toHaveBeenCalled()
    mocks.access.mockResolvedValueOnce(null)
    await expect(page({ params })).rejects.toThrow('redirect:/login')
    expect(mocks.query).not.toHaveBeenCalled()
  })
  it('retains preparation metadata and SSR prefetch error fallbacks independently', async () => {
    mocks.access.mockResolvedValue({ user: { uid }, role: 'guest', permission: 'all', canBuild: true })
    mocks.query.mockRejectedValueOnce(new Error('metadata failed'))
    expect(await preparationMetadata({ params })).toEqual({ title: 'Nirmāṇa · Chart — MARSYS-JIS' })
    mocks.query.mockRejectedValueOnce(new Error('prefetch failed'))
    const page = await Preparation({ params })
    // The final child is CockpitShell; a failed SSR prefetch still mounts it with null.
    expect(page.props.children.at(-1).props).toMatchObject({ chartId: id, initialChartMeta: null, variant: 'preparation' })
    expect(mocks.query.mock.calls.map(call => call[1])).toEqual([[id], [id]])
  })
  it.each(calls.map((call, index) => ({ call, index })))('denies page $index before any identity/domain data read', async ({ call }) => {
    mocks.access.mockResolvedValueOnce(null)
    await expect(call()).rejects.toThrow('redirect:/login')
    mocks.access.mockResolvedValueOnce({ user: { uid }, permission: 'deny' })
    await expect(call()).rejects.toThrow('redirect:/dashboard')
    expect(mocks.query).not.toHaveBeenCalled()
    expect(mocks.readiness).not.toHaveBeenCalled()
    expect(mocks.review).not.toHaveBeenCalled()
  })
  it.each([Consultation, Review])('applies the feature gate before access and data', async page => {
    mocks.flag.mockReturnValue(false)
    await expect(page({ params })).rejects.toThrow(`redirect:/clients/${id}/consult`)
    expect(mocks.access).not.toHaveBeenCalled()
    expect(mocks.query).not.toHaveBeenCalled()
  })
  it.each(calls.map((call, index) => ({ call, index })))('preserves missing-row redirect on page $index after the guarded read', async ({ call }) => {
    await expect(call()).rejects.toThrow('redirect:/dashboard')
    expect(mocks.access).toHaveBeenCalledBefore(mocks.query)
    expect(mocks.query.mock.calls[0]?.[1]).toEqual([id])
    expect(mocks.review).not.toHaveBeenCalled()
    expect(mocks.badge).not.toHaveBeenCalled()
    // Consultation already starts canonical readiness in parallel with its identity read.
    if (call !== calls[3]) expect(mocks.readiness).not.toHaveBeenCalled()
  })
  it('keeps generic metadata private until admitted, retaining missing/null/error behavior', async () => {
    mocks.access.mockResolvedValueOnce(null)
    expect(await generateMetadata({ params })).toEqual({ title: 'Chart — MARSYS-JIS' })
    expect(mocks.query).not.toHaveBeenCalled()
    mocks.query.mockResolvedValueOnce({ rows: [{ name: null }] })
    expect(await generateMetadata({ params })).toEqual({ title: 'Chart — MARSYS-JIS' })
    mocks.query.mockResolvedValueOnce({ rows: [{ name: 'Synthetic name' }] })
    expect(await generateMetadata({ params })).toEqual({ title: 'Synthetic name — MARSYS-JIS' })
    const error = new Error('read failed')
    mocks.query.mockRejectedValueOnce(error)
    await expect(generateMetadata({ params })).rejects.toBe(error)
  })
  it('reads the chart before its legacy guest switcher with one principal bind and exact ordering', async () => {
    mocks.query.mockResolvedValueOnce({ rows: [{ name: null }] }).mockResolvedValueOnce({ rows: [] })
    await Layout({ params, children: null })
    expect(mocks.query.mock.calls[0]).toEqual(['SELECT name FROM charts WHERE id=$1', [id]])
    expect(mocks.query.mock.calls[1]).toEqual([`SELECT c.id, c.name FROM charts c
           WHERE c.owner_id = $1
              OR c.client_id = $1
              OR EXISTS (SELECT 1 FROM chart_grants g WHERE g.chart_id = c.id AND g.principal_id = $1)
           ORDER BY c.name NULLS LAST, c.created_at DESC LIMIT 100`, [uid]])
  })
  it.each(['guest', 'super_admin', 'client', undefined])('keeps dashboard role=%s selection before parallel readiness/stats', async role => {
    mocks.query.mockResolvedValueOnce({ rows: role ? [{ role }] : [] }).mockResolvedValueOnce({ rows: [{ id, owner_id: uid }] })
    await Dashboard()
    expect(mocks.user).toHaveBeenCalledBefore(mocks.query)
    expect(mocks.query.mock.calls[0]).toEqual(['SELECT id, role, name, username, email, status FROM profiles WHERE id=$1', [uid]])
    const [sql, binds] = mocks.query.mock.calls[1]
    if (role === 'super_admin') {
      expect(sql).toBe('SELECT * FROM charts ORDER BY created_at DESC')
      expect(binds).toEqual([])
    } else {
      expect(sql).toBe(`SELECT c.* FROM charts c
         WHERE c.owner_id = $1
            OR c.client_id = $1
            OR EXISTS (
              SELECT 1 FROM chart_grants g
              WHERE g.chart_id = c.id AND g.principal_id = $1
            )
         ORDER BY c.created_at DESC`)
      expect(binds).toEqual([uid])
    }
    expect(mocks.query.mock.invocationCallOrder[1]).toBeLessThan(mocks.readiness.mock.invocationCallOrder[0])
    expect(mocks.query.mock.invocationCallOrder[1]).toBeLessThan(mocks.consumed.mock.invocationCallOrder[0])
    expect(mocks.readiness).toHaveBeenCalledWith([id])
    expect(mocks.consumed).toHaveBeenCalledWith([id])
  })
  it('redirects unsigned dashboard before profile/roster reads and propagates roster errors before readiness', async () => {
    mocks.user.mockResolvedValueOnce(null)
    await expect(Dashboard()).rejects.toThrow('redirect:/login')
    expect(mocks.query).not.toHaveBeenCalled()
    const failure = new Error('roster failed')
    mocks.query.mockResolvedValueOnce({ rows: [] }).mockRejectedValueOnce(failure)
    await expect(Dashboard()).rejects.toBe(failure)
    expect(mocks.readiness).not.toHaveBeenCalled()
    expect(mocks.consumed).not.toHaveBeenCalled()
  })
})

describe('Identity read port result and failure semantics', () => {
  const ports = [...Object.values(charts), ...Object.values(profiles), ...Object.values(roster)]
  it.each(ports.map(port => ({ port, name: port.name })))('$name preserves the driver result/promise and does not normalize rows or catch errors', async ({ port }) => {
    const result = { rows: [], rowCount: 0, command: 'SELECT' }
    const pending = Promise.resolve(result)
    mocks.query.mockReturnValueOnce(pending)
    const read = port(id)
    expect(read).toBe(pending)
    expect(await read).toBe(result)
    expect(mocks.query).toHaveBeenCalledTimes(1)
    const failure = new Error('synthetic SQL error')
    mocks.query.mockRejectedValueOnce(failure)
    await expect(port(id)).rejects.toBe(failure)
  })
  it('keeps editable field casts and preparation prefetch projection separate', async () => {
    await charts.readEditableChartIdentity(id)
    expect(mocks.query.mock.calls[0]).toEqual([`SELECT id, name, preferred_name, subject_name,
            birth_date::text AS birth_date, birth_time::text AS birth_time, birth_place,
            birth_lat::float8 AS birth_lat, birth_lng::float8 AS birth_lng, timezone_id, ayanamsa
       FROM charts WHERE id = $1`, [id]])
    await charts.readPreparationChartIdentity(id)
    expect(mocks.query.mock.calls[1]).toEqual(['SELECT subject_name, birth_date, birth_time::text, birth_place FROM charts WHERE id=$1', [id]])
  })
})

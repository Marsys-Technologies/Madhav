// @vitest-environment jsdom
/**
 * The two Consult server pages tolerate the retired reports relation. The mock
 * rejects every reports query while mounted preparation controls exercise the
 * current server permission decisions with synthetic chart and actor fixtures.
 */
import { createElement } from 'react'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const CHART = '00000000-0000-4000-8000-000000000001'
const OTHER = '00000000-0000-4000-8000-000000000002'
const CONVERSATION = '00000000-0000-4000-8000-000000000003'
const fixtures = vi.hoisted(() => ({
  issuedSql: [] as { sql: string; params?: unknown[] }[],
  owner: 'tester-uid' as string | null,
  client: 'tester-uid',
  role: 'guest',
  grant: 'view' as string | null,
  failWriteCheck: false,
  conversationChart: '00000000-0000-4000-8000-000000000001',
  archived: false,
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'tester-uid' })) }))
vi.mock('@/lib/auth/chart-page-guard', () => ({
  resolveChartPageAccess: vi.fn(async () => ({
    user: { uid: 'tester-uid' }, permission: 'all', role: 'guest', canBuild: true,
  })),
}))
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params?: unknown[]) => {
    fixtures.issuedSql.push({ sql, params })
    if (/from\s+reports\b/i.test(sql)) throw Object.assign(new Error('retired reports'), { code: '42P01' })
    if (/SELECT owner_id FROM charts/i.test(sql)) {
      if (fixtures.failWriteCheck) throw new Error('synthetic permission lookup failure')
      return { rows: [{ owner_id: fixtures.owner }] }
    }
    if (/from\s+chart_grants\b/i.test(sql)) return { rows: fixtures.grant ? [{ permission: fixtures.grant }] : [] }
    if (/from\s+charts\b/i.test(sql)) return { rows: [{ name: 'Synthetic Chart', birth_date: null, birth_place: null, client_id: fixtures.client }] }
    if (/from\s+profiles\b/i.test(sql)) return { rows: [{ role: fixtures.role }] }
    if (/from\s+pyramid_layers\b/i.test(sql)) return { rows: [{ layer_key: 'L1', status: 'built' }] }
    return { rows: [] }
  }),
}))
vi.mock('@/lib/conversations', () => ({
  listConversations: vi.fn(async () => []),
  getConversation: vi.fn(async () => ({ chart_id: fixtures.conversationChart,
    archive_reason: fixtures.archived ? 'chart_details_changed' : null })),
}))
vi.mock('@/lib/persistence/conversation_writer', () => ({ loadConversationMessagesV2: vi.fn(async () => []) }))
vi.mock('@/lib/config/index', () => ({ configService: { getFlag: vi.fn(() => false) } }))
vi.mock('@/lib/config/feature_flags', () => ({ FEATURE_FLAGS: { panelMode: 'panel', costVisibilityForUsers: 'cost' } }))
vi.mock('next/server', () => ({ NextResponse: { json: (body: unknown, init?: ResponseInit) => Response.json(body, init) } }))
vi.mock('next/navigation', () => ({
  redirect: vi.fn((to: string) => { throw new Error(`redirect(${to})`) }),
  notFound: vi.fn(() => { throw new Error('notFound()') }),
}))
vi.mock('@/lib/conversations/historicalReading', () => ({ loadHistoricalConversationMessages: vi.fn(async () => []) }))
vi.mock('@/components/consume/HistoricalConversationView', () => ({ HistoricalConversationView: () => createElement('div', null, 'Synthetic history') }))
vi.mock('@/components/consume/ReviewSourceReading', () => ({ ReviewSourceReading: () => createElement('div', null, 'Synthetic source review') }))
vi.mock('@/components/consume/ConsumeChat', async () => {
  const { PartialDataBanner, useChartDataReadiness } = await import('@/components/consume/PartialDataBanner')
  function MountedPreparation({ chartId, buildPreparationHref }: { chartId: string; buildPreparationHref?: string }) {
    const readiness = useChartDataReadiness(chartId)
    return createElement(PartialDataBanner, { chartId, readiness, buildPreparationHref })
  }
  return { ConsumeChat: MountedPreparation }
})

import { getServerUser } from '@/lib/firebase/server'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import ConsultPage from '../page'
import ConsultConversationPage from '../[conversationId]/page'

beforeEach(() => {
  fixtures.issuedSql.length = 0
  Object.assign(fixtures, { owner: 'tester-uid', client: 'tester-uid', role: 'guest', grant: 'view',
    failWriteCheck: false, conversationChart: CHART, archived: false })
  vi.mocked(getServerUser).mockResolvedValue({ uid: 'tester-uid' } as Awaited<ReturnType<typeof getServerUser>>)
  vi.mocked(resolveChartPageAccess).mockResolvedValue({ user: { uid: 'tester-uid' }, permission: 'all', role: 'guest', canBuild: true } as Awaited<ReturnType<typeof resolveChartPageAccess>>)
  vi.stubGlobal('fetch', vi.fn(async () => Response.json({ chart_id: CHART, build_status: 'partial',
    ready: ['asset-ready'], missing: ['asset-pending'], partial_count: 1, total_count: 2 })))
})
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

async function mountActive() {
  render(await ConsultPage({ params: Promise.resolve({ id: CHART }), searchParams: Promise.resolve({}) }))
}
async function mountSaved() {
  render(await ConsultConversationPage({ params: Promise.resolve({ id: CHART, conversationId: CONVERSATION }) }))
}
function ownerReads() { return fixtures.issuedSql.filter(row => /SELECT owner_id FROM charts/i.test(row.sql)) }

describe('Consult page reports tolerance and preparation permission', () => {
  it.each([mountActive, mountSaved])('renders the mounted preparation entry without touching retired reports %#', async mount => {
    await mount()
    const link = await screen.findByRole('link', { name: 'Open Chart Preparation' })
    expect(link.getAttribute('href')).toBe(`/clients/${CHART}/nirmana`)
    expect(fixtures.issuedSql.some(row => /from\s+reports\b/i.test(row.sql))).toBe(false)
    expect(fixtures.issuedSql.some(row => /from\s+charts\b/i.test(row.sql))).toBe(true)
  })

  it('uses the existing active canBuild witness without an extra permission read', async () => {
    vi.mocked(resolveChartPageAccess).mockResolvedValue({ user: { uid: 'tester-uid' }, permission: 'view', role: 'guest', canBuild: false } as Awaited<ReturnType<typeof resolveChartPageAccess>>)
    await mountActive()
    await screen.findByText('Chart partially built.')
    expect(screen.queryByRole('link')).toBeNull()
    expect(ownerReads()).toEqual([])
  })

  it('keeps a live saved view read-only when its legacy client is not the current chart owner', async () => {
    fixtures.owner = 'other-owner'
    await mountSaved()
    await screen.findByText('Chart partially built.')
    expect(screen.queryByRole('link')).toBeNull()
    expect(ownerReads()).toEqual([{ sql: 'SELECT owner_id FROM charts WHERE id=$1', params: [CHART] }])
    expect(fixtures.issuedSql.find(row => /FROM chart_grants/i.test(row.sql))?.params).toEqual([CHART, 'tester-uid'])
  })

  it('allows a saved superadmin on the existing chart through the canonical write check', async () => {
    fixtures.role = 'super_admin'
    fixtures.client = 'other-client'
    fixtures.owner = 'other-owner'
    await mountSaved()
    await screen.findByRole('link', { name: 'Open Chart Preparation' })
    expect(ownerReads()).toHaveLength(1)
    expect(fixtures.issuedSql.some(row => /FROM chart_grants/i.test(row.sql))).toBe(false)
  })

  it('preserves saved viewing when the optional write decision fails', async () => {
    fixtures.failWriteCheck = true
    await mountSaved()
    await screen.findByText('Chart partially built.')
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('checks the saved chart and conversation before the optional write read', async () => {
    fixtures.conversationChart = OTHER
    await expect(mountSaved()).rejects.toThrow('notFound()')
    expect(ownerReads()).toEqual([])
    expect(fetch).not.toHaveBeenCalled()
  })

  it('keeps correction archives and source-part reading outside the preparation branch', async () => {
    fixtures.archived = true
    await mountSaved()
    screen.getByText('Synthetic history')
    expect(ownerReads()).toEqual([])
    cleanup()
    render(await ConsultConversationPage({ params: Promise.resolve({ id: CHART, conversationId: CONVERSATION }), searchParams: Promise.resolve({ sourcePart: 'synthetic-part' }) }))
    screen.getByText('Synthetic source review')
    expect(ownerReads()).toEqual([])
    expect(fetch).not.toHaveBeenCalled()
  })

  it('retains unsigned and denied active redirects before readiness or optional reads', async () => {
    vi.mocked(resolveChartPageAccess).mockResolvedValueOnce(null)
    await expect(mountActive()).rejects.toThrow('redirect(/login)')
    vi.mocked(resolveChartPageAccess).mockResolvedValueOnce({ user: { uid: 'tester-uid' }, permission: 'deny', role: 'guest', canBuild: false } as Awaited<ReturnType<typeof resolveChartPageAccess>>)
    await expect(mountActive()).rejects.toThrow('redirect(/dashboard)')
    vi.mocked(getServerUser).mockResolvedValueOnce(null)
    await expect(mountSaved()).rejects.toThrow('redirect(/login)')
    expect(ownerReads()).toEqual([])
    expect(fetch).not.toHaveBeenCalled()
  })
})

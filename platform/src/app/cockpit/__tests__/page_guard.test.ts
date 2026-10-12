// @vitest-environment node
/**
 * SS N-373 item 2 — cockpit/page.tsx and information/atlas/page.tsx load data
 * server-side. A layout guard alone does not protect them (a crafted RSC request
 * can skip a layout; see clients/[id]/layout.tsx), so each page must verify the
 * super_admin itself, with the SAME rule and the SAME redirects as its layout,
 * BEFORE any data is loaded.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const getServerUserWithProfileMock = vi.fn()
vi.mock('@/lib/auth/access-control', () => ({
  getServerUserWithProfile: () => getServerUserWithProfileMock(),
  requireSuperAdmin: vi.fn(),
}))

class Redirect extends Error {
  constructor(public readonly to: string) {
    super(`NEXT_REDIRECT:${to}`)
  }
}
vi.mock('next/navigation', () => ({
  redirect: (to: string) => {
    throw new Redirect(to)
  },
}))
vi.mock('next/link', () => ({ default: () => null }))

// data sources: every one is a "data was loaded" tripwire
const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => queryMock(...a) }))
const fetchBuildStateMock = vi.fn()
vi.mock('@/lib/build/dataSource', () => ({ fetchBuildState: () => fetchBuildStateMock() }))
const usageSummaryMock = vi.fn()
vi.mock('@/lib/metering/queries', () => ({
  parseUsageFilter: (...a: unknown[]) => ({ filter: a }),
  usageSummary: (...a: unknown[]) => usageSummaryMock(...a),
}))
vi.mock('@/lib/metering/types', () => ({ meteringEnabled: () => true }))
vi.mock('@/lib/config', () => ({ getFlag: () => false }))
vi.mock('@/components/build/AtlasView', () => ({ AtlasView: () => null }))
vi.mock('@/components/shared/AppShell', () => ({ AppShell: () => null }))
vi.mock('@/components/build/BuildHeader', () => ({ BuildHeader: () => null }))
vi.mock('@/components/build/FreshnessIndicator', () => ({ FreshnessIndicator: () => null }))

const ADMIN = {
  user: { uid: 'admin-1' },
  profile: { id: 'admin-1', role: 'super_admin', status: 'active' },
}

function dataLoaded(): number {
  return queryMock.mock.calls.length + fetchBuildStateMock.mock.calls.length + usageSummaryMock.mock.calls.length
}

beforeEach(() => {
  vi.resetModules()
  for (const m of [getServerUserWithProfileMock, queryMock, fetchBuildStateMock, usageSummaryMock]) m.mockReset()
  queryMock.mockResolvedValue({ rows: [] })
  fetchBuildStateMock.mockResolvedValue({ generated_at: 'x' })
  usageSummaryMock.mockResolvedValue({ transport_attempts: 0, complete_usage: 0, transport_failed: 0, validation_attempts: 0 })
})

const PAGES: Array<{ name: string; load: () => Promise<{ default: () => Promise<unknown> }> }> = [
  { name: 'cockpit/page.tsx', load: () => import('@/app/cockpit/page') as never },
  { name: 'information/atlas/page.tsx', load: () => import('@/app/information/atlas/page') as never },
]

describe('page-level super_admin guard (mirrors cockpit/layout.tsx and information/layout.tsx)', () => {
  for (const p of PAGES) {
    describe(p.name, () => {
      it('no verified session -> redirect /login, no data loaded', async () => {
        getServerUserWithProfileMock.mockResolvedValue(null)
        const Page = (await p.load()).default
        await expect(Page()).rejects.toMatchObject({ to: '/login' })
        expect(dataLoaded()).toBe(0)
      })

      it('inactive profile -> redirect /login, no data loaded', async () => {
        getServerUserWithProfileMock.mockResolvedValue({ ...ADMIN, profile: { ...ADMIN.profile, status: 'pending' } })
        const Page = (await p.load()).default
        await expect(Page()).rejects.toMatchObject({ to: '/login' })
        expect(dataLoaded()).toBe(0)
      })

      it('active guest -> redirect /dashboard, no data loaded', async () => {
        getServerUserWithProfileMock.mockResolvedValue({ ...ADMIN, profile: { ...ADMIN.profile, role: 'guest' } })
        const Page = (await p.load()).default
        await expect(Page()).rejects.toMatchObject({ to: '/dashboard' })
        expect(dataLoaded()).toBe(0)
      })

      it('active super_admin -> renders and loads its data', async () => {
        getServerUserWithProfileMock.mockResolvedValue(ADMIN)
        const Page = (await p.load()).default
        await expect(Page()).resolves.toBeTruthy()
        expect(dataLoaded()).toBeGreaterThan(0)
      })
    })
  }
})

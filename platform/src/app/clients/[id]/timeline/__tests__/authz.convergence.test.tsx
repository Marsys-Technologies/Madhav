/**
 * V3-E-019 — timeline/* carries a divergent per-chart authorization model.
 *
 * `authorizeChartAccess` (Unit 2c, "one authorization brain") states in its own
 * docstring that it *replaces* the inline `chart.client_id !== user.uid` check.
 * `clients/[id]/timeline/layout.tsx` and `clients/[id]/timeline/page.tsx` had not
 * been converged onto it: both still run
 *
 *     if (profile?.role !== 'super_admin' && chart.client_id !== user.uid) redirect('/dashboard')
 *
 * which consults neither `charts.owner_id` nor `chart_grants`. Two concrete
 * divergences from the canonical model, in opposite directions:
 *
 *  - OVER-DENIAL (the user-visible one): a `chart_grants` view-grantee — and an
 *    `owner_id` owner whose legacy `client_id` differs — is admitted by the
 *    parent `clients/[id]/layout.tsx` guard and then bounced to /dashboard by
 *    timeline. Grants-based sharing is simply broken for this route.
 *  - UNDER-DENIAL (the latent one): a principal matching only the legacy
 *    `client_id` column passes timeline's check while the canonical model
 *    denies them. The parent layout currently contains this, so it is a latent
 *    divergence rather than a live escalation — but it means this route's
 *    authorization answer is decided by a model the codebase retired.
 *
 * These tests pin the convergence: both timeline modules must reach their
 * admit/deny decision through `resolveChartPageAccess`, on the same
 * `permission === 'deny'` bar the parent layout uses, and pin `canWrite` to the
 * canonical build bar.
 *
 * SCOPE, stated honestly: this convergence is NOT repo-wide. Independent
 * verification of this fix found `src/app/api/pyramid/route.ts` still running the
 * same retired inline check — and because it is an API route handler, no layout
 * guard sits above it, so its over-denial of chart_grants view-grantees is LIVE
 * today, not latent like timeline's was. That route is filed as a separate lead
 * in EDIR_V3_REGISTER; it is deliberately NOT fixed here (S5's remediation plan
 * is frozen, so it needs its own governed finding). Do not read this file as
 * evidence that the inline model is gone from the codebase.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockQuery, mockResolveAccess, mockRedirect, mockGetServerUser, mockParseLEL } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockResolveAccess: vi.fn(),
  mockRedirect: vi.fn((path: string) => {
    throw new Error(`REDIRECT:${path}`)
  }),
  mockGetServerUser: vi.fn(),
  mockParseLEL: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: mockResolveAccess }))
vi.mock('next/navigation', () => ({ redirect: mockRedirect }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/lel/parser', () => ({ parseLEL: mockParseLEL }))
vi.mock('@/components/shared/AppShell', () => ({ AppShell: () => null }))
vi.mock('@/components/shared/ZoneRoot', () => ({ ZoneRoot: () => null }))
vi.mock('@/components/timeline/TimelineView', () => ({ TimelineView: () => null }))

import { TimelineView } from '@/components/timeline/TimelineView'

/** Walk the returned element tree and return the TimelineView element. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function findTimelineView(node: any): any {
  if (!node || typeof node !== 'object') return null
  if (node.type === TimelineView) return node
  const kids = node.props?.children
  for (const kid of Array.isArray(kids) ? kids : [kids]) {
    const hit = findTimelineView(kid)
    if (hit) return hit
  }
  return null
}

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const GRANTEE_UID = 'grantee-uid'
const LEGACY_CLIENT_UID = 'legacy-client-uid'

/** The chart row as the DB actually holds it: owned by someone else, and a
 *  legacy `client_id` that does NOT match the grantee. */
function chartRow() {
  return { name: 'Abhisek Mohanty', client_id: LEGACY_CLIENT_UID }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetServerUser.mockResolvedValue({ uid: GRANTEE_UID })
  mockParseLEL.mockResolvedValue({ events: [], predictions: [], parseErrors: [] })
  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role: 'guest', status: 'active' }], rowCount: 1 })
    if (/FROM charts/.test(sql)) return Promise.resolve({ rows: [chartRow()], rowCount: 1 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
  // Canonical model: this principal IS a legitimate chart_grants view-grantee.
  mockResolveAccess.mockResolvedValue({
    user: { uid: GRANTEE_UID },
    role: 'guest',
    permission: 'view',
    canBuild: false,
  })
})

describe('timeline layout — V3-E-019 authorization-model convergence', () => {
  it('resolves access through the canonical resolveChartPageAccess brain', async () => {
    const mod = await import('../layout')
    await mod.default({ children: null, params: Promise.resolve({ id: CHART_ID }) }).catch(() => {})
    expect(mockResolveAccess).toHaveBeenCalledWith(CHART_ID)
  })

  it('does NOT bounce a chart_grants view-grantee the parent layout already admitted', async () => {
    const mod = await import('../layout')
    await mod.default({ children: null, params: Promise.resolve({ id: CHART_ID }) })
    expect(mockRedirect).not.toHaveBeenCalled()
  })

  it('still denies a principal the canonical model denies', async () => {
    mockResolveAccess.mockResolvedValue({
      user: { uid: GRANTEE_UID }, role: 'guest', permission: 'deny', canBuild: false,
    })
    const mod = await import('../layout')
    await expect(
      mod.default({ children: null, params: Promise.resolve({ id: CHART_ID }) })
    ).rejects.toThrow('REDIRECT:/dashboard')
  })
})

describe('timeline page — V3-E-019 authorization-model convergence', () => {
  it('resolves access through the canonical resolveChartPageAccess brain', async () => {
    const mod = await import('../page')
    await mod.default({ params: Promise.resolve({ id: CHART_ID }) }).catch(() => {})
    expect(mockResolveAccess).toHaveBeenCalledWith(CHART_ID)
  })

  it('does NOT bounce a chart_grants view-grantee, and DOES read their LEL', async () => {
    const mod = await import('../page')
    await mod.default({ params: Promise.resolve({ id: CHART_ID }) })
    expect(mockRedirect).not.toHaveBeenCalled()
    expect(mockParseLEL).toHaveBeenCalledWith(CHART_ID)
  })

  // §N.8: `canWrite` had no detector at all until this assertion — a hostile
  // mutation to `canWrite={true}`, handing the write UI to every view-grantee,
  // survived the suite 6/6 green. The claim now has a check behind it.
  it('passes canWrite=false for a view-grantee — no write UI for a read grant', async () => {
    const mod = await import('../page')
    const el = await mod.default({ params: Promise.resolve({ id: CHART_ID }) })
    const view = findTimelineView(el)
    expect(view).not.toBeNull()
    expect(view.props.canWrite).toBe(false)
  })

  it('passes canWrite=true for an owner/super_admin — the canonical build bar', async () => {
    mockResolveAccess.mockResolvedValue({
      user: { uid: 'owner-1' }, role: 'guest', permission: 'all', canBuild: true,
    })
    const mod = await import('../page')
    const el = await mod.default({ params: Promise.resolve({ id: CHART_ID }) })
    const view = findTimelineView(el)
    expect(view).not.toBeNull()
    expect(view.props.canWrite).toBe(true)
  })

  it('still denies a principal the canonical model denies — and reads no LEL for them', async () => {
    mockResolveAccess.mockResolvedValue({
      user: { uid: GRANTEE_UID }, role: 'guest', permission: 'deny', canBuild: false,
    })
    const mod = await import('../page')
    await expect(
      mod.default({ params: Promise.resolve({ id: CHART_ID }) })
    ).rejects.toThrow('REDIRECT:/dashboard')
    expect(mockParseLEL).not.toHaveBeenCalled()
  })
})

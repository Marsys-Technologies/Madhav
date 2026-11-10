/**
 * V3-E-018 — generateMetadata() unauthenticated PII disclosure guard on the
 * PARENT chart layout.
 *
 * Same defect class as V3-E-007 (fixed in `clients/[id]/nirmana/page.tsx`,
 * PR #1611), but one level up and therefore with a materially broader blast
 * radius: `clients/[id]/layout.tsx` is the parent layout of every sibling
 * chart route (nirmana, consult, timeline, panchang, profile, …). Its
 * `generateMetadata` ran a raw `SELECT name FROM charts WHERE id=$1` OUTSIDE
 * the layout body's own `resolveChartPageAccess` guard — so any request for a
 * known chart_id (unauthenticated curl, a link-preview crawler) got the real
 * chart `name` (a real person's name) back in the rendered <title> tag, for
 * ANY route under this layout.
 *
 * The layout BODY denies only on `permission === 'deny'` (owner, super_admin
 * and chart_grants view-grantees all legitimately see the name in the
 * breadcrumb), so metadata's authorization bar must match that exact bar —
 * not the stricter `canBuild` bar V3-E-007 used, whose page body genuinely
 * gates on build access.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockQuery, mockResolveAccess, mockHeaders } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockResolveAccess: vi.fn(),
  mockHeaders: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: mockResolveAccess }))
vi.mock('next/headers', () => ({ headers: mockHeaders }))
vi.mock('next/navigation', () => ({
  redirect: (path: string) => { throw new Error(`REDIRECT:${path}`) },
}))

// The layout module also imports the shell component tree, which reaches the
// Firebase *client* SDK at import time and throws without browser env keys.
// These tests exercise generateMetadata only, so the shell is stubbed out —
// nothing under test is mocked away.
vi.mock('@/components/shared/AppShell', () => ({ AppShell: () => null }))
vi.mock('@/components/shared/ZoneRoot', () => ({ ZoneRoot: () => null }))
vi.mock('@/components/nav/ConditionalChartSwitcherBar', () => ({
  ConditionalChartSwitcherBar: () => null,
}))

const TEST_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const REAL_CHART_NAME = 'Abhisek Mohanty'

beforeEach(() => {
  mockQuery.mockReset()
  mockResolveAccess.mockReset()
  mockHeaders.mockResolvedValue(new Headers())
  // The `charts` row genuinely holds the PII in every case below — a raw,
  // unguarded query (the pre-fix defect) WOULD return the real name. The fix
  // must keep that value out of the title for unauthorized callers.
  mockQuery.mockResolvedValue({ rows: [{ name: REAL_CHART_NAME }] })
})

describe('chart layout sign-in return', () => {
  it('preserves the exact chart subpage when server verification refuses the session', async () => {
    mockResolveAccess.mockResolvedValue(null)
    mockHeaders.mockResolvedValue(new Headers({
      'x-madhav-chart-return-path': `/clients/${TEST_CHART_ID}/consult/reading-123`,
    }))

    const { default: Layout } = await import('../layout')
    await expect(Layout({ params: Promise.resolve({ id: TEST_CHART_ID }), children: null }))
      .rejects.toThrow(`REDIRECT:/login?next=%2Fclients%2F${TEST_CHART_ID}%2Fconsult%2Freading-123`)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('uses plain sign-in when the forwarded path belongs to another chart', async () => {
    mockResolveAccess.mockResolvedValue(null)
    mockHeaders.mockResolvedValue(new Headers({ 'x-madhav-chart-return-path': '/clients/another-chart/edit' }))

    const { default: Layout } = await import('../layout')
    await expect(Layout({ params: Promise.resolve({ id: TEST_CHART_ID }), children: null }))
      .rejects.toThrow(/^REDIRECT:\/login$/)
  })

  it('sends a signed-in user without chart access to the dashboard', async () => {
    mockResolveAccess.mockResolvedValue({ user: { uid: 'guest-1' }, role: 'guest', permission: 'deny' })

    const { default: Layout } = await import('../layout')
    await expect(Layout({ params: Promise.resolve({ id: TEST_CHART_ID }), children: null }))
      .rejects.toThrow(/^REDIRECT:\/dashboard$/)
    expect(mockQuery).not.toHaveBeenCalled()
  })
})

describe('clients/[id]/layout generateMetadata — V3-E-018 PII disclosure guard', () => {
  it('does NOT leak the chart name when the caller is unauthenticated', async () => {
    mockResolveAccess.mockResolvedValue(null)

    const { generateMetadata } = await import('../layout')
    const metadata = await generateMetadata({ params: Promise.resolve({ id: TEST_CHART_ID }) })

    expect(String(metadata.title)).not.toContain(REAL_CHART_NAME)
  })

  it('does NOT leak the chart name when the caller has no access (permission=deny)', async () => {
    mockResolveAccess.mockResolvedValue({
      user: { uid: 'attacker-1' },
      role: 'guest',
      permission: 'deny',
      canBuild: false,
    })

    const { generateMetadata } = await import('../layout')
    const metadata = await generateMetadata({ params: Promise.resolve({ id: TEST_CHART_ID }) })

    expect(String(metadata.title)).not.toContain(REAL_CHART_NAME)
  })

  it('issues NO chart-name query at all for an unauthorized caller', async () => {
    mockResolveAccess.mockResolvedValue({
      user: { uid: 'attacker-1' },
      role: 'guest',
      permission: 'deny',
      canBuild: false,
    })

    const { generateMetadata } = await import('../layout')
    await generateMetadata({ params: Promise.resolve({ id: TEST_CHART_ID }) })

    // Pinned to the PII query specifically — a bare /FROM charts/ would also
    // match the guard's own `SELECT owner_id FROM charts` probe, so it would
    // read clean only for as long as the guard stays mocked.
    const chartNameReads = mockQuery.mock.calls.filter((call: unknown[]) =>
      /SELECT name FROM charts/.test(call[0] as string)
    )
    expect(chartNameReads).toHaveLength(0)
  })

  it('DOES show the chart name for a chart_grants view-grantee — matches the layout body bar', async () => {
    mockResolveAccess.mockResolvedValue({
      user: { uid: 'grantee-1' },
      role: 'guest',
      permission: 'view',
      canBuild: false,
    })

    const { generateMetadata } = await import('../layout')
    const metadata = await generateMetadata({ params: Promise.resolve({ id: TEST_CHART_ID }) })

    expect(String(metadata.title)).toContain(REAL_CHART_NAME)
  })

  it('DOES show the chart name for the owner/super_admin — regression guard', async () => {
    mockResolveAccess.mockResolvedValue({
      user: { uid: 'owner-1' },
      role: 'super_admin',
      permission: 'all',
      canBuild: true,
    })

    const { generateMetadata } = await import('../layout')
    const metadata = await generateMetadata({ params: Promise.resolve({ id: TEST_CHART_ID }) })

    expect(String(metadata.title)).toContain(REAL_CHART_NAME)
  })
})

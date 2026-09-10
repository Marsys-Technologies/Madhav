/**
 * V3-E-007 — generateMetadata() unauthenticated PII disclosure guard.
 *
 * `clients/[id]/nirmana/page.tsx`'s `generateMetadata` used to run a raw
 * `SELECT subject_name FROM charts WHERE id=$1` OUTSIDE the page body's
 * `resolveChartPageAccess` / `canBuild` authorization guard. Any request for a
 * known chart_id — unauthenticated curl, a link-preview crawler — got the real
 * subject_name (a real person's name) back in the rendered <title> HTML tag.
 *
 * These tests exercise `generateMetadata` directly (not the page body, which
 * was already correctly guarded) and assert the real subject_name never
 * reaches the returned title unless the caller resolves to `canBuild: true`
 * via the SAME `resolveChartPageAccess` path the page body uses.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockQuery, mockResolveAccess } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockResolveAccess: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: mockResolveAccess }))

const TEST_CHART_ID = 'test-chart'
const REAL_SUBJECT_NAME = 'Abhisek Mohanty'

beforeEach(() => {
  mockQuery.mockReset()
  mockResolveAccess.mockReset()
  // Even in the DENY/unauthenticated cases below, the underlying `charts`
  // table DOES have the real PII — a raw, unguarded query on it (the
  // pre-fix defect) WOULD return the real name. The fix under test must
  // never let that query's result reach the title unless authorized.
  mockQuery.mockResolvedValue({ rows: [{ subject_name: REAL_SUBJECT_NAME }] })
})

describe('nirmana generateMetadata — V3-E-007 unauthenticated PII disclosure guard', () => {
  it('does NOT leak subject_name when caller is unauthenticated (resolveChartPageAccess -> null)', async () => {
    mockResolveAccess.mockResolvedValue(null)

    const { generateMetadata } = await import('../page')
    const metadata = await generateMetadata({ params: Promise.resolve({ id: TEST_CHART_ID }) })

    expect(metadata.title).not.toContain(REAL_SUBJECT_NAME)
  })

  it('does NOT leak subject_name when caller is authenticated but lacks build access (permission=view)', async () => {
    mockResolveAccess.mockResolvedValue({
      user: { uid: 'u1' },
      role: 'guest',
      permission: 'view',
      canBuild: false,
    })

    const { generateMetadata } = await import('../page')
    const metadata = await generateMetadata({ params: Promise.resolve({ id: TEST_CHART_ID }) })

    expect(metadata.title).not.toContain(REAL_SUBJECT_NAME)
  })

  it('does NOT leak subject_name when caller has no access at all (permission=deny)', async () => {
    mockResolveAccess.mockResolvedValue({
      user: { uid: 'u1' },
      role: 'guest',
      permission: 'deny',
      canBuild: false,
    })

    const { generateMetadata } = await import('../page')
    const metadata = await generateMetadata({ params: Promise.resolve({ id: TEST_CHART_ID }) })

    expect(metadata.title).not.toContain(REAL_SUBJECT_NAME)
  })

  it('DOES show subject_name for an authorized owner/super_admin (permission=all, canBuild=true) — regression guard', async () => {
    mockResolveAccess.mockResolvedValue({
      user: { uid: 'owner-1' },
      role: 'guest',
      permission: 'all',
      canBuild: true,
    })

    const { generateMetadata } = await import('../page')
    const metadata = await generateMetadata({ params: Promise.resolve({ id: TEST_CHART_ID }) })

    expect(metadata.title).toContain(REAL_SUBJECT_NAME)
  })
})

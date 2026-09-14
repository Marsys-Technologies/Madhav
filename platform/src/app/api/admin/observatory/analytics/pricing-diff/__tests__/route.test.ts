// @vitest-environment node
//
// USTAD_S4_4 — pricing diff route tests.
//
// Layout:
//   §A  GET /api/admin/observatory/analytics/pricing-diff (2):
//       200 valid for super-admin / 403 for non-super-admin
//   §B  POST /api/admin/observatory/analytics/pricing-diff/run (1):
//       200 returns identical PricingDiffResult shape

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

describe('§A — GET /api/admin/observatory/analytics/pricing-diff', () => {
  beforeEach(() => {
    queryMock.mockReset()
    vi.resetModules()
    process.env.MARSYS_FLAG_OBSERVATORY_ENABLED = 'true'
    delete process.env.OBSERVATORY_ALERT_WEBHOOK_URL
  })

  it('200 — super-admin auth + healthy providers', async () => {
    vi.doMock('@/lib/auth/access-control', () => ({
      requireSuperAdmin: async () => ({
        user: { uid: 'admin-1' },
        profile: { id: 'admin-1', role: 'super_admin', status: 'active' },
      }),
    }))
    queryMock
      .mockResolvedValueOnce({
        rows: [
          {
            provider: 'anthropic',
            last_pricing_update: new Date().toISOString().slice(0, 10),
          },
        ],
      })
      .mockResolvedValueOnce({
        rows: [{ provider: 'anthropic', avg_abs_variance_pct: 0.2 }],
      })

    const { GET } = await import(
      '@/app/api/admin/observatory/analytics/pricing-diff/route'
    )
    const response = await GET()
    expect(response).toBeInstanceOf(NextResponse)
    expect(response.status).toBe(200)
    const body = await response.json()
    expect(body.providers).toHaveLength(1)
    expect(body.providers[0].provider).toBe('anthropic')
    expect(body.providers[0].status).toBe('ok')
    expect(body.all_healthy).toBe(true)
    expect(typeof body.checked_at).toBe('string')
  })

  it('403 — non-super-admin', async () => {
    vi.doMock('@/lib/auth/access-control', () => {
      return {
        requireSuperAdmin: async () =>
          NextResponse.json(
            { error: { code: 'AUTH_FORBIDDEN', message: 'forbidden' } },
            { status: 403 },
          ),
      }
    })

    const { GET } = await import(
      '@/app/api/admin/observatory/analytics/pricing-diff/route'
    )
    const response = await GET()
    expect(response).toBeInstanceOf(NextResponse)
    expect(response.status).toBe(403)
  })
})

describe('§B — POST /api/admin/observatory/analytics/pricing-diff/run', () => {
  beforeEach(() => {
    queryMock.mockReset()
    vi.resetModules()
    process.env.MARSYS_FLAG_OBSERVATORY_ENABLED = 'true'
    delete process.env.OBSERVATORY_ALERT_WEBHOOK_URL
  })

  it('200 — runs same check; returns PricingDiffResult', async () => {
    vi.doMock('@/lib/auth/access-control', () => ({
      requireSuperAdmin: async () => ({
        user: { uid: 'admin-1' },
        profile: { id: 'admin-1', role: 'super_admin', status: 'active' },
      }),
    }))
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    queryMock
      .mockResolvedValueOnce({
        rows: [
          {
            provider: 'gemini',
            last_pricing_update: new Date(
              Date.now() - 90 * 86_400_000,
            )
              .toISOString()
              .slice(0, 10),
          },
        ],
      })
      .mockResolvedValueOnce({
        rows: [{ provider: 'gemini', avg_abs_variance_pct: 0.1 }],
      })

    const { POST } = await import(
      '@/app/api/admin/observatory/analytics/pricing-diff/run/route'
    )
    const response = await POST()
    expect(response.status).toBe(200)
    const body = await response.json()
    expect(body.providers[0].provider).toBe('gemini')
    expect(body.providers[0].status).toBe('stale_pricing')
    expect(body.stale_count).toBe(1)
    expect(body.all_healthy).toBe(false)

    warnSpy.mockRestore()
  })
})

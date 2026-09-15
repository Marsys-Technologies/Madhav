// @vitest-environment node
//
// USTAD_S4_6 — anomaly route tests.
//
// Layout:
//   §A  GET /api/admin/observatory/analytics/anomaly (2):
//       200 valid for super-admin / 403 for non-super-admin
//   §B  POST /api/admin/observatory/analytics/anomaly/run (2):
//       200 returns AnomalyResult shape; accepts JSON config in body

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

describe('§A — GET /api/admin/observatory/analytics/anomaly', () => {
  beforeEach(() => {
    queryMock.mockReset()
    vi.resetModules()
    process.env.MARSYS_FLAG_OBSERVATORY_ENABLED = 'true'
    delete process.env.OBSERVATORY_ALERT_WEBHOOK_URL
  })

  it('200 — super-admin auth + no anomalies', async () => {
    vi.doMock('@/lib/auth/access-control', () => ({
      requireSuperAdmin: async () => ({
        user: { uid: 'admin-1' },
        profile: { id: 'admin-1', role: 'super_admin', status: 'active' },
      }),
    }))
    queryMock.mockResolvedValueOnce({ rows: [] })

    const { GET } = await import(
      '@/app/api/admin/observatory/analytics/anomaly/route'
    )
    const response = await GET(
      new Request('http://localhost/api/admin/observatory/analytics/anomaly'),
    )
    expect(response).toBeInstanceOf(NextResponse)
    expect(response.status).toBe(200)
    const body = await response.json()
    expect(body.anomalies).toEqual([])
    expect(body.alert_fired).toBe(false)
    expect(typeof body.checked_at).toBe('string')
    expect(body.config.z_threshold).toBe(2.5)
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
      '@/app/api/admin/observatory/analytics/anomaly/route'
    )
    const response = await GET(
      new Request('http://localhost/api/admin/observatory/analytics/anomaly'),
    )
    expect(response).toBeInstanceOf(NextResponse)
    expect(response.status).toBe(403)
  })
})

describe('§B — POST /api/admin/observatory/analytics/anomaly/run', () => {
  beforeEach(() => {
    queryMock.mockReset()
    vi.resetModules()
    process.env.MARSYS_FLAG_OBSERVATORY_ENABLED = 'true'
    delete process.env.OBSERVATORY_ALERT_WEBHOOK_URL
  })

  it('200 — runs detection; returns AnomalyResult; honours body config', async () => {
    vi.doMock('@/lib/auth/access-control', () => ({
      requireSuperAdmin: async () => ({
        user: { uid: 'admin-1' },
        profile: { id: 'admin-1', role: 'super_admin', status: 'active' },
      }),
    }))
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    queryMock.mockResolvedValueOnce({
      rows: [
        {
          dimension: 'provider',
          dimension_value: 'anthropic',
          cost_date: '2026-05-02',
          observed_cost_usd: 100,
          mean_cost_usd: 5,
          stddev_cost_usd: 1,
          data_points: 14,
          z_score: 95,
        },
      ],
    })

    const { POST } = await import(
      '@/app/api/admin/observatory/analytics/anomaly/run/route'
    )
    const request = new Request(
      'http://localhost/api/admin/observatory/analytics/anomaly/run',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ z_threshold: 3.0 }),
      },
    )
    const response = await POST(request)
    expect(response.status).toBe(200)
    const body = await response.json()
    expect(body.config.z_threshold).toBe(3.0)
    expect(body.anomalies).toHaveLength(1)
    expect(body.alert_fired).toBe(true)
    expect(body.anomalies[0].z_score).toBe(95)

    warnSpy.mockRestore()
  })

  it('200 — empty body uses defaults', async () => {
    vi.doMock('@/lib/auth/access-control', () => ({
      requireSuperAdmin: async () => ({
        user: { uid: 'admin-1' },
        profile: { id: 'admin-1', role: 'super_admin', status: 'active' },
      }),
    }))

    queryMock.mockResolvedValueOnce({ rows: [] })

    const { POST } = await import(
      '@/app/api/admin/observatory/analytics/anomaly/run/route'
    )
    const request = new Request(
      'http://localhost/api/admin/observatory/analytics/anomaly/run',
      { method: 'POST' },
    )
    const response = await POST(request)
    expect(response.status).toBe(200)
    const body = await response.json()
    expect(body.config.z_threshold).toBe(2.5)
    expect(body.config.lookback_days).toBe(14)
  })
})

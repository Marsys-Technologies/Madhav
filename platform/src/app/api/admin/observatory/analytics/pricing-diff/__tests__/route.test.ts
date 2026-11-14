// @vitest-environment node
// Route guards, read/command separation, and production webhook transport to a
// synthetic loopback sink. Auth and SQL are mocked; no external service is used.

import { createServer } from 'node:http'
import type { AddressInfo } from 'node:net'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))
const { queryMock, requireSuperAdmin } = vi.hoisted(() => ({
  queryMock: vi.fn(),
  requireSuperAdmin: vi.fn(),
}))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('@/lib/auth/access-control', () => ({ requireSuperAdmin }))

const now = new Date('2026-06-01T12:00:00.000Z')
const lastUpdate = '2026-04-01T12:00:00.000Z'
const unhealthyDetail = {
  provider: 'fixture',
  last_pricing_update: lastUpdate,
  pricing_age_days: 61,
  is_pricing_stale: true,
  avg_7d_variance_pct: 7,
  has_systematic_variance: true,
  status: 'both',
  alert_fired: false,
}

function unhealthyQuery() {
  queryMock
    .mockResolvedValueOnce({ rows: [{ provider: 'fixture', last_pricing_update: lastUpdate }] })
    .mockResolvedValueOnce({ rows: [{ provider: 'fixture', avg_abs_variance_pct: 7 }] })
}

async function handlers() {
  const { GET } = await import('@/app/api/admin/observatory/analytics/pricing-diff/route')
  const { POST } = await import('@/app/api/admin/observatory/analytics/pricing-diff/run/route')
  return { GET, POST }
}

beforeEach(() => {
  vi.resetModules()
  queryMock.mockReset()
  requireSuperAdmin.mockReset()
  requireSuperAdmin.mockResolvedValue({
    user: { uid: 'admin-1' },
    profile: { id: 'admin-1', role: 'super_admin', status: 'active' },
  })
  vi.stubEnv('MARSYS_FLAG_OBSERVATORY_ENABLED', 'true')
  vi.stubEnv('OBSERVATORY_ALERT_WEBHOOK_URL', '')
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('pricing diff read and command routes', () => {
  it('GET returns healthy pricing without attempting delivery', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    queryMock
      .mockResolvedValueOnce({ rows: [{ provider: 'anthropic', last_pricing_update: new Date().toISOString() }] })
      .mockResolvedValueOnce({ rows: [{ provider: 'anthropic', avg_abs_variance_pct: 0.2 }] })
    const { GET } = await handlers()
    const response = await GET()
    expect(response).toBeInstanceOf(NextResponse)
    expect(response.status).toBe(200)
    const body = await response.json()
    expect(body.providers).toEqual([expect.objectContaining({
      provider: 'anthropic', status: 'ok', alert_fired: false, alert_webhook_result: 'not_attempted',
    })])
    expect(body.all_healthy).toBe(true)
    expect(typeof body.checked_at).toBe('string')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('repeated unhealthy GETs do not dispatch; each POST dispatches once', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 503 }))
    vi.stubGlobal('fetch', fetchMock)
    vi.stubEnv('OBSERVATORY_ALERT_WEBHOOK_URL', 'http://127.0.0.1/unused-mocked')
    const { GET, POST } = await handlers()
    for (const [index, handler] of [GET, GET, POST, POST].entries()) {
      unhealthyQuery()
      const response = await handler()
      expect(response.status).toBe(200)
      const body = await response.json()
      expect(body.providers).toEqual([expect.objectContaining({
        provider: 'fixture', status: 'both',
        alert_fired: index >= 2,
        alert_webhook_result: index < 2 ? 'not_attempted' : 'http_error',
      })])
      expect(body.all_healthy).toBe(false)
      expect(fetchMock).toHaveBeenCalledTimes(Math.max(0, index - 1))
      expect(queryMock).toHaveBeenCalledTimes((index + 1) * 2)
    }
    expect(requireSuperAdmin).toHaveBeenCalledTimes(4)
  })

  it('POST reports not_configured while preserving the unhealthy health result', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    unhealthyQuery()
    const { POST } = await handlers()
    const response = await POST()
    expect(response.status).toBe(200)
    const body = await response.json()
    expect(body.providers[0]).toMatchObject({
      status: 'both', alert_fired: true, alert_webhook_result: 'not_configured',
    })
    expect(body.stale_count).toBe(1)
    expect(body.variance_alert_count).toBe(1)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it.each([401, 403])('refuses both routes with status %i before queries or delivery', async (status) => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    requireSuperAdmin.mockImplementation(async () => NextResponse.json(
      { error: { code: 'AUTH_FIXTURE' } }, { status },
    ))
    const { GET, POST } = await handlers()
    expect((await GET()).status).toBe(status)
    expect((await POST()).status).toBe(status)
    expect(requireSuperAdmin).toHaveBeenCalledTimes(2)
    expect(queryMock).not.toHaveBeenCalled()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('refuses both routes before auth when the feature is disabled', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    vi.stubEnv('MARSYS_FLAG_OBSERVATORY_ENABLED', 'false')
    const { GET, POST } = await handlers()
    expect((await GET()).status).toBe(403)
    expect((await POST()).status).toBe(403)
    expect(requireSuperAdmin).not.toHaveBeenCalled()
    expect(queryMock).not.toHaveBeenCalled()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it.each(['GET', 'POST'] as const)('%s contains SQL failures before any alert dispatch', async (method) => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    const routes = await handlers()
    for (const failedQuery of [1, 2]) {
      queryMock.mockReset()
      if (failedQuery === 2) {
        queryMock.mockResolvedValueOnce({ rows: [{ provider: 'fixture', last_pricing_update: lastUpdate }] })
      }
      queryMock.mockRejectedValueOnce(new Error('synthetic SQL failure'))
      const response = await routes[method]()
      expect(response.status).toBe(500)
      expect(queryMock).toHaveBeenCalledTimes(failedQuery)
      expect(fetchMock).not.toHaveBeenCalled()
    }
  })
})

describe('production dispatcher with real fetch and a local HTTP sink', () => {
  it.each([
    [202, 'http_accepted'],
    [503, 'http_error'],
  ])('GET sends nothing; POST sends exact legacy JSON and reports HTTP %i as %s', async (status, outcome) => {
    // Freeze Date only: the real socket/fetch/abort timers must keep running.
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(now)
    const received: { method: string | undefined; contentType: string | undefined; body: string }[] = []
    const sink = createServer((request, response) => {
      let body = ''
      request.setEncoding('utf8')
      request.on('data', (chunk: string) => { body += chunk })
      request.on('end', () => {
        received.push({ method: request.method, contentType: request.headers['content-type'], body })
        response.writeHead(status)
        response.end()
      })
    })
    try {
      await new Promise<void>((resolve, reject) => {
        sink.once('error', reject)
        sink.listen(0, '127.0.0.1', resolve)
      })
      const { port } = sink.address() as AddressInfo
      vi.stubEnv('OBSERVATORY_ALERT_WEBHOOK_URL', `http://127.0.0.1:${port}/pricing`)
      const { GET, POST } = await handlers()
      for (let i = 0; i < 2; i += 1) {
        unhealthyQuery()
        const response = await GET()
        expect(response.status).toBe(200)
        expect((await response.json()).providers[0]).toEqual({
          ...unhealthyDetail, alert_webhook_result: 'not_attempted',
        })
      }
      expect(received).toEqual([])
      expect(console.warn).not.toHaveBeenCalled()
      for (let i = 0; i < 2; i += 1) {
        unhealthyQuery()
        const response = await POST()
        expect(response.status).toBe(200)
        const body = await response.json()
        expect(body.providers[0]).toEqual({
          ...unhealthyDetail, alert_fired: true, alert_webhook_result: outcome,
        })
        expect(received).toHaveLength(i + 1)
        expect(received[i]).toEqual({
          method: 'POST',
          contentType: 'application/json',
          body: JSON.stringify({ provider: 'fixture', status: 'both', detail: unhealthyDetail }),
        })
      }
      expect(queryMock).toHaveBeenCalledTimes(8)
    } finally {
      await new Promise<void>((resolve, reject) => {
        sink.close((error) => { if (error) reject(error); else resolve() })
        sink.closeAllConnections()
      })
    }
  })
})

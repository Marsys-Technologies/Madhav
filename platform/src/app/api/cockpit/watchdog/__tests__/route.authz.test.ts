/** Cloud Scheduler OIDC is the watchdog's machine-to-machine gate. */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockVerifyOidcToken } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockVerifyOidcToken: vi.fn(),
}))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/auth/oidc', () => ({ verifyOidcToken: mockVerifyOidcToken }))

import { POST } from '../route'

function makeReq(token?: string, legacy?: string): NextRequest {
  const headers: Record<string, string> = {}
  if (token !== undefined) headers.Authorization = `Bearer ${token}`
  if (legacy !== undefined) headers['x-watchdog-auth'] = legacy
  return new NextRequest('http://localhost/api/cockpit/watchdog', {
    method: 'POST',
    headers,
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })
  mockVerifyOidcToken.mockResolvedValue({
    email: 'amjis-scheduler@madhav-astrology.iam.gserviceaccount.com',
    sub: 'scheduler-subject',
  })
  process.env.PUBSUB_DISABLED = '1'
  delete process.env.WATCHDOG_LEGACY_FALLBACK_ENABLED
  delete process.env.WATCHDOG_SECRET
})

describe('POST /api/cockpit/watchdog — audience and service-account-bound OIDC', () => {
  it('rejects a request with no bearer token before touching build state', async () => {
    const res = await POST(makeReq())
    expect(res.status).toBe(401)
    expect(mockVerifyOidcToken).not.toHaveBeenCalled()
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('rejects a token that does not resolve to the pinned identity', async () => {
    mockVerifyOidcToken.mockResolvedValue(null)
    const res = await POST(makeReq('wrong-identity'))
    expect(res.status).toBe(403)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('fails closed when cryptographic token verification throws', async () => {
    mockVerifyOidcToken.mockRejectedValue(new Error('bad signature'))
    const res = await POST(makeReq('malformed'))
    expect(res.status).toBe(403)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('admits the pinned scheduler identity and starts the reaper', async () => {
    const res = await POST(makeReq('valid-google-id-token'))
    expect(res.status).toBe(200)
    expect(mockVerifyOidcToken).toHaveBeenCalledWith('valid-google-id-token', {
      expectedAudience: 'https://amjis-web-938361928218.asia-south1.run.app',
      expectedServiceAccount: 'amjis-scheduler@madhav-astrology.iam.gserviceaccount.com',
    })
    expect(mockQuery).toHaveBeenCalled()
  })

  it('rejects the retired legacy scheduler header even when the old bridge variables exist', async () => {
    process.env.WATCHDOG_LEGACY_FALLBACK_ENABLED = 'true'
    process.env.WATCHDOG_SECRET = 'transition-secret'
    const res = await POST(makeReq(undefined, 'transition-secret'))
    expect(res.status).toBe(403)
    expect(mockVerifyOidcToken).not.toHaveBeenCalled()
    expect(mockQuery).not.toHaveBeenCalled()
  })
})

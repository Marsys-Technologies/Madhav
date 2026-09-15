import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  validate: vi.fn(), authorize: vi.fn(), loadRing: vi.fn(), issue: vi.fn(),
  verify: vi.fn(), probe: vi.fn(), rateLimit: vi.fn(),
}))
vi.mock('@/lib/mcp/auth', () => ({ validateMcpKey: mocks.validate }))
vi.mock('@/lib/mcp/rate_limiter', () => ({ checkRateLimit: mocks.rateLimit }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: mocks.authorize }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/vidhi/inquiry', () => ({
  loadInquiryLifecycleSigningKeyRing: mocks.loadRing,
  issueInquiryLifecycleToken: mocks.issue,
  verifyInquiryLifecycleToken: mocks.verify,
}))
vi.mock('@/lib/vidhi/inquiry/store_pool', () => ({ probeInquiryStoreReadiness: mocks.probe }))

import { POST } from './route'

const chartId = 'aaaaaaaa-1111-4000-8000-000000000001'
function request(body: unknown, bearer = 'candidate-key') {
  return new Request('http://localhost/api/mcp/inquiry/readiness', {
    method: 'POST',
    headers: { Authorization: `Bearer ${bearer}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  process.env.PURNA_READINESS_CANARY_KEY_ID = 'key-1'
  process.env.NIRMANA_DEPLOYED_SHA = 'candidate-sha'
  process.env.K_REVISION = 'amjis-web-probe-candidate'
  mocks.validate.mockResolvedValue({ user_uid: 'user-1', key_id: 'key-1', role: 'guest' })
  mocks.rateLimit.mockResolvedValue({ allowed: true })
  mocks.authorize.mockResolvedValue('all')
  mocks.loadRing.mockReturnValue({ current: { kid: 'inquiry-v1', material: Buffer.alloc(32) } })
  mocks.issue.mockReturnValue({ token: 'signed-token', claims: {} })
  mocks.probe.mockResolvedValue({
    dedicated_login: true, least_privilege_role: true, rls_tables: 4,
    same_principal_rows: 4, cross_principal_rows: 0,
    security_definer_search_path: true, rolled_back: true,
  })
})

describe('POST /api/mcp/inquiry/readiness', () => {
  it('rejects an invalid canary key before authorization or storage', async () => {
    mocks.validate.mockResolvedValue(null)
    const res = await POST(request({ chart_id: chartId }))
    expect(res.status).toBe(401)
    expect(mocks.authorize).not.toHaveBeenCalled()
    expect(mocks.probe).not.toHaveBeenCalled()
  })

  it('rejects a valid customer key that is not the pinned deploy canary', async () => {
    mocks.validate.mockResolvedValue({ user_uid: 'user-2', key_id: 'customer-key', role: 'guest' })
    const res = await POST(request({ chart_id: chartId }, 'customer-key-material'))
    expect(res.status).toBe(401)
    expect(mocks.authorize).not.toHaveBeenCalled()
    expect(mocks.probe).not.toHaveBeenCalled()
  })

  it('rejects a chart the authenticated canary principal cannot access', async () => {
    mocks.authorize.mockResolvedValue('deny')
    const res = await POST(request({ chart_id: chartId }))
    expect(res.status).toBe(403)
    expect(mocks.probe).not.toHaveBeenCalled()
  })

  it('rate-limits the pinned canary before authorization or storage work', async () => {
    mocks.rateLimit.mockResolvedValue({ allowed: false, retry_after_seconds: 17 })
    const res = await POST(request({ chart_id: chartId }))
    expect(res.status).toBe(429)
    expect(res.headers.get('Retry-After')).toBe('17')
    expect(await res.json()).toEqual({ ok: false, error: 'RATE_LIMITED' })
    expect(mocks.authorize).not.toHaveBeenCalled()
    expect(mocks.probe).not.toHaveBeenCalled()
  })

  it('requires signing round-trip and the rolled-back RLS probe', async () => {
    const res = await POST(request({ chart_id: chartId }))
    expect(res.status).toBe(200)
    expect(mocks.verify).toHaveBeenCalledWith('signed-token', expect.anything(), 'user-1:key-1')
    expect(mocks.probe).toHaveBeenCalledWith({
      principalUid: 'user-1', principalKeyId: 'key-1', chartId,
    })
    expect(await res.json()).toMatchObject({
      ok: true,
      deployed_sha: 'candidate-sha',
      revision: 'amjis-web-probe-candidate',
      signing_round_trip: true,
      database: { same_principal_rows: 4, cross_principal_rows: 0, rolled_back: true },
    })
  })

  it('fails closed without leaking the underlying readiness error', async () => {
    mocks.probe.mockRejectedValue(new Error('credential material detail'))
    const res = await POST(request({ chart_id: chartId }))
    expect(res.status).toBe(503)
    expect(await res.json()).toEqual({ ok: false, error: 'INQUIRY_READINESS_FAILED' })
  })
})

import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  authorize: vi.fn(), create: vi.fn(), get: vi.fn(), claim: vi.fn(),
  progress: vi.fn(), complete: vi.fn(), fail: vi.fn(),
}))

vi.mock('@/lib/mcp/service_token', () => ({ validateMcpServiceRequest: async () => true }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('guest') }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: mocks.authorize }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/vidhi/inquiry/managed_job_store', () => ({
  createManagedPrashnaJob: mocks.create,
  getManagedPrashnaJob: mocks.get,
  claimManagedPrashnaJob: mocks.claim,
  updateManagedPrashnaJobProgress: mocks.progress,
  completeManagedPrashnaJob: mocks.complete,
  failManagedPrashnaJob: mocks.fail,
}))

import { POST } from './route'

const chartId = 'aaaaaaaa-1111-4000-8000-000000000001'
const jobId = 'bbbbbbbb-1111-4000-8000-000000000001'
const workerId = 'cccccccc-1111-4000-8000-000000000001'
const inquiryId = 'dddddddd-1111-4000-8000-000000000001'

function row(overrides: Record<string, unknown> = {}) {
  return {
    job_id: jobId, principal_uid: 'user-1', principal_key_id: 'key-1', chart_id: chartId,
    principal_auth_kind: 'api_key', api_key_id: 'key-1', oauth_token_hash: null,
    request_jsonb: { inquiry_id: inquiryId, question: 'wealth?', response_format: 'standard' },
    status: 'pending', progress_jsonb: null, result_jsonb: null, error_text: null,
    lease_owner: null, lease_expires_at: null, attempt_count: 0,
    created_at: '2026-09-15T00:00:00.000Z', updated_at: '2026-09-15T00:00:00.000Z',
    retention_expires_at: '2026-09-16T00:00:00.000Z', ...overrides,
  }
}

function request(body: unknown, headers: Record<string, string> = {}): Request {
  return new Request('http://localhost/api/mcp/prashna_jobs', {
    method: 'POST',
    headers: {
      'content-type': 'application/json', 'x-mcp-user': 'user-1', 'x-mcp-key-id': 'key-1',
      'x-mcp-auth-kind': 'api_key',
      ...headers,
    },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.authorize.mockResolvedValue('all')
  mocks.create.mockResolvedValue(row())
  mocks.get.mockResolvedValue(row())
})

describe('durable managed Prashna job route', () => {
  it('persists a bounded request only after current chart authorization', async () => {
    const response = await POST(request({
      action: 'create', job_id: jobId, chart_id: chartId, inquiry_id: inquiryId, question: 'wealth?', response_format: 'standard',
    }))
    expect(response.status).toBe(200)
    expect(mocks.create).toHaveBeenCalledWith(expect.objectContaining({
      principal_uid: 'user-1', principal_key_id: 'key-1', chart_id: chartId,
      principal_auth_kind: 'api_key',
      request: { inquiry_id: inquiryId, question: 'wealth?', response_format: 'standard' },
    }))
    expect(await response.json()).toMatchObject({ ok: true, job: { job_id: jobId, status: 'pending' } })
  })

  it('denies create before persistence when chart entitlement is revoked', async () => {
    mocks.authorize.mockResolvedValue('deny')
    const response = await POST(request({
      action: 'create', job_id: jobId, chart_id: chartId, inquiry_id: inquiryId, question: 'wealth?', response_format: 'standard',
    }))
    expect(response.status).toBe(401)
    expect(mocks.create).not.toHaveBeenCalled()
  })

  it('rejects an unsupported response format before authorization or persistence', async () => {
    const response = await POST(request({
      action: 'create', job_id: jobId, chart_id: chartId, inquiry_id: inquiryId, question: 'wealth?', response_format: 'xml',
    }))
    expect(response.status).toBe(400)
    expect(mocks.authorize).not.toHaveBeenCalled()
    expect(mocks.create).not.toHaveBeenCalled()
  })

  it('does not distinguish an unknown job from one not owned by the user/key pair', async () => {
    mocks.get.mockResolvedValue(null)
    const response = await POST(request({ action: 'get', job_id: jobId }))
    expect(response.status).toBe(404)
    expect(await response.json()).toEqual({ ok: false, error: 'MANAGED_JOB_NOT_FOUND_OR_EXPIRED' })
    expect(mocks.authorize).not.toHaveBeenCalled()
  })

  it('returns an atomic claim disposition and the persisted request to the lease winner', async () => {
    mocks.claim.mockResolvedValue(row({
      status: 'running', lease_owner: workerId, lease_expires_at: '2026-09-15T00:06:00.000Z', attempt_count: 1,
    }))
    const response = await POST(request({ action: 'claim', job_id: jobId, worker_id: workerId }))
    expect(response.status).toBe(200)
    expect(await response.json()).toMatchObject({
      ok: true, disposition: 'acquired', job: { job_id: jobId, request: { question: 'wealth?' } },
    })
  })

  it('rejects an oversized terminal result before a database mutation', async () => {
    const response = await POST(request({
      action: 'complete', job_id: jobId, worker_id: workerId,
      result: { reading: 'x'.repeat(2 * 1024 * 1024) },
    }))
    expect(response.status).toBe(413)
    expect(mocks.complete).not.toHaveBeenCalled()
  })

  it('rejects a non-object terminal result before a database mutation', async () => {
    const response = await POST(request({
      action: 'complete', job_id: jobId, worker_id: workerId, result: 'not-an-envelope',
    }))
    expect(response.status).toBe(400)
    expect(mocks.complete).not.toHaveBeenCalled()
  })


  it('fails closed with a stable error when the durable store is unavailable', async () => {
    mocks.get.mockRejectedValue(new Error('database details must not leak'))
    const logged = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    const response = await POST(request({ action: 'get', job_id: jobId }))
    expect(response.status).toBe(500)
    expect(await response.json()).toMatchObject({ ok: false, error: 'MANAGED_JOB_STORE_UNAVAILABLE' })
    expect(logged).toHaveBeenCalled()
    logged.mockRestore()
  })
})

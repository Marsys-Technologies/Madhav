import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { PlatformManagedPrashnaJobStore } from './managed_prashna_jobs.js'
import type { Principal } from '../types.js'

const fetchMock = vi.fn()
vi.stubGlobal('fetch', fetchMock)

const principal: Principal = { user_uid: 'user-a', key_id: 'key-a', role: 'guest' }
const chartId = 'aaaaaaaa-1111-4000-8000-000000000001'
const jobId = 'bbbbbbbb-1111-4000-8000-000000000001'
const workerId = 'cccccccc-1111-4000-8000-000000000001'

function job(overrides: Record<string, unknown> = {}) {
  return {
    job_id: jobId, chart_id: chartId, status: 'pending', progress: null, result: null,
    error: null, attempt_count: 0, created_at: '2026-09-15T00:00:00.000Z',
    updated_at: '2026-09-15T00:00:00.000Z', lease_expires_at: null, ...overrides,
  }
}

function response(payload: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => payload } as Response
}

beforeEach(() => {
  fetchMock.mockReset()
  process.env.PLATFORM_URL = 'https://platform.test'
  process.env.SERVICE_TOKEN = 'oidc-test'
  process.env.MCP_INTERNAL_TOKEN = 'internal-test'
})

afterEach(() => {
  delete process.env.PLATFORM_URL
  delete process.env.SERVICE_TOKEN
  delete process.env.MCP_INTERNAL_TOKEN
})

describe('platform durable managed-job client', () => {
  it('binds create to service and principal headers and never starts with a local-only row', async () => {
    fetchMock.mockResolvedValueOnce(response({ ok: true, job: job() }))
    const store = new PlatformManagedPrashnaJobStore()
    const created = await store.create(principal, {
      job_id: jobId, chart_id: chartId, request: { question: 'wealth?', response_format: 'standard' },
    })
    expect(created).toMatchObject({ job_id: jobId, status: 'pending' })
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('https://platform.test/api/mcp/prashna_jobs')
    expect(init.headers).toMatchObject({
      'Authorization': 'Bearer oidc-test', 'X-MCP-Internal-Token': 'internal-test',
      'X-MCP-User': 'user-a', 'X-MCP-Key-Id': 'key-a', 'X-MCP-Auth-Kind': 'api_key',
    })
    expect(JSON.parse(init.body as string)).toEqual({
      action: 'create', job_id: jobId, chart_id: chartId, question: 'wealth?', response_format: 'standard',
    })
  })

  it('carries the one durable inquiry identity through an ambiguous create retry', async () => {
    const inquiryId = 'dddddddd-1111-4000-8000-000000000001'
    fetchMock
      .mockRejectedValueOnce(new Error('response lost after commit'))
      .mockResolvedValueOnce(response({ ok: true, job: job({ inquiry_id: inquiryId }) }))

    const created = await new PlatformManagedPrashnaJobStore().create(principal, {
      job_id: jobId, chart_id: chartId, inquiry_id: inquiryId,
      request: { question: 'wealth?', response_format: 'standard' },
    } as never)

    expect((created as unknown as { inquiry_id?: string }).inquiry_id).toBe(inquiryId)
    const firstBody = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string)
    const retryBody = JSON.parse((fetchMock.mock.calls[1][1] as RequestInit).body as string)
    expect(firstBody.inquiry_id).toBe(inquiryId)
    expect(retryBody.inquiry_id).toBe(inquiryId)
  })

  it('retries an ambiguous create with the same caller-generated idempotency key', async () => {
    fetchMock
      .mockRejectedValueOnce(new Error('response lost after commit'))
      .mockResolvedValueOnce(response({ ok: true, job: job() }))
    const created = await new PlatformManagedPrashnaJobStore().create(principal, {
      job_id: jobId, chart_id: chartId, request: { question: 'wealth?', response_format: 'standard' },
    })
    expect(created.job_id).toBe(jobId)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    const firstBody = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string)
    const retryBody = JSON.parse((fetchMock.mock.calls[1][1] as RequestInit).body as string)
    expect(retryBody).toEqual(firstBody)
    expect(retryBody.job_id).toBe(jobId)
  })

  it('retries ambiguous terminal writes with an identical worker and payload', async () => {
    const result = { ok: true, trace_id: 'trace-1', chart_id: chartId, outcome: 'plan' }
    fetchMock
      .mockRejectedValueOnce(new Error('completion acknowledgement lost'))
      .mockResolvedValueOnce(response({ ok: true, job: job({ status: 'complete', result }) }))

    const completed = await new PlatformManagedPrashnaJobStore().complete(
      principal,
      jobId,
      workerId,
      result as never,
    )
    expect(completed.status).toBe('complete')
    expect(fetchMock).toHaveBeenCalledTimes(2)
    const firstBody = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string)
    const retryBody = JSON.parse((fetchMock.mock.calls[1][1] as RequestInit).body as string)
    expect(retryBody).toEqual(firstBody)
    expect(retryBody).toMatchObject({ action: 'complete', job_id: jobId, worker_id: workerId, result })
  })

  it('marks a full token-hash credential as OAuth without exposing a token prefix', async () => {
    fetchMock.mockResolvedValueOnce(response({ ok: true, job: job() }))
    const oauthPrincipal: Principal = {
      user_uid: 'user-a', key_id: `oauth_sha256:${'a'.repeat(64)}`, role: 'guest',
    }
    await new PlatformManagedPrashnaJobStore().create(oauthPrincipal, {
      job_id: jobId, chart_id: chartId, request: { question: 'wealth?', response_format: 'standard' },
    })
    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect(init.headers).toMatchObject({
      'X-MCP-Key-Id': oauthPrincipal.key_id,
      'X-MCP-Auth-Kind': 'oauth',
    })
  })

  it('returns null for the deliberately indistinguishable unknown/unauthorized lookup', async () => {
    fetchMock.mockResolvedValueOnce(response({ ok: false, error: 'MANAGED_JOB_NOT_FOUND_OR_EXPIRED' }, 404))
    await expect(new PlatformManagedPrashnaJobStore().get(principal, jobId)).resolves.toBeNull()
  })

  it('requires the server claim disposition and persisted request', async () => {
    fetchMock.mockResolvedValueOnce(response({
      ok: true, disposition: 'acquired',
      job: job({ status: 'running', attempt_count: 1, request: { question: 'wealth?', response_format: 'standard' } }),
    }))
    const claimed = await new PlatformManagedPrashnaJobStore().claim(principal, jobId, workerId)
    expect(claimed).toMatchObject({
      disposition: 'acquired', job: { attempt_count: 1, request: { question: 'wealth?' } },
    })
  })

  it('rejects malformed or unavailable durable responses without a memory fallback', async () => {
    fetchMock.mockResolvedValueOnce(response({ ok: true, job: { id: 'not-the-contract' } }))
    await expect(new PlatformManagedPrashnaJobStore().get(principal, jobId)).rejects.toThrow()
    fetchMock.mockRejectedValueOnce(new Error('network down'))
    await expect(new PlatformManagedPrashnaJobStore().get(principal, jobId)).rejects.toThrow('network down')
  })
})

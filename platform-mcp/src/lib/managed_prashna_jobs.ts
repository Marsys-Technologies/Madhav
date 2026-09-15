import { GoogleAuth, type IdTokenClient } from 'google-auth-library'
import { z } from 'zod'
import type { Principal } from '../types.js'
import type { PrashnaAskEngineResponse, PrashnaAskScopeTuple } from './prashna_ask_bridge.js'

export type ManagedPrashnaJobStatus = 'pending' | 'running' | 'complete' | 'failed'
export type ManagedPrashnaResponseFormat = 'digest' | 'summary' | 'standard' | 'narrative' | 'full'

export interface ManagedPrashnaJobRequest {
  question: string
  response_format: ManagedPrashnaResponseFormat
  scope_tuple?: PrashnaAskScopeTuple
}

export interface ManagedPrashnaJobProgress {
  message: string
  pct: number
}

export interface ManagedPrashnaJob {
  job_id: string
  chart_id: string
  status: ManagedPrashnaJobStatus
  progress: ManagedPrashnaJobProgress | null
  result: PrashnaAskEngineResponse | null
  error: string | null
  attempt_count: number
  created_at: string
  updated_at: string
  lease_expires_at: string | null
  request?: ManagedPrashnaJobRequest
}

export interface ManagedPrashnaJobStore {
  create(principal: Principal, input: { job_id: string; chart_id: string; request: ManagedPrashnaJobRequest }): Promise<ManagedPrashnaJob>
  get(principal: Principal, jobId: string): Promise<ManagedPrashnaJob | null>
  claim(principal: Principal, jobId: string, workerId: string): Promise<{ disposition: 'acquired' | 'not_acquired'; job: ManagedPrashnaJob } | null>
  updateProgress(principal: Principal, jobId: string, workerId: string, progress: ManagedPrashnaJobProgress): Promise<ManagedPrashnaJob>
  complete(principal: Principal, jobId: string, workerId: string, result: PrashnaAskEngineResponse): Promise<ManagedPrashnaJob>
  fail(principal: Principal, jobId: string, workerId: string, error: string): Promise<ManagedPrashnaJob>
}

const JobSchema = z.object({
  job_id: z.string().uuid(), chart_id: z.string().uuid(),
  status: z.enum(['pending', 'running', 'complete', 'failed']),
  progress: z.object({ message: z.string(), pct: z.number() }).nullable(),
  result: z.unknown().nullable(), error: z.string().nullable(),
  attempt_count: z.number().int().min(0), created_at: z.string(), updated_at: z.string(),
  lease_expires_at: z.string().nullable(),
  request: z.object({
    question: z.string(),
    response_format: z.enum(['digest', 'summary', 'standard', 'narrative', 'full']),
    scope_tuple: z.unknown().optional(),
  }).optional(),
})

const PLATFORM_URL = () => (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
let cachedClient: IdTokenClient | null = null

async function identityToken(): Promise<string> {
  if (process.env['SERVICE_TOKEN']) return process.env['SERVICE_TOKEN'] as string
  try {
    cachedClient ??= await new GoogleAuth().getIdTokenClient(PLATFORM_URL())
    const headers = await cachedClient.getRequestHeaders(PLATFORM_URL())
    const value = (headers as Record<string, string>)['Authorization'] ?? ''
    return value.startsWith('Bearer ') ? value.slice(7) : value
  } catch {
    return process.env['MCP_INTERNAL_TOKEN'] ?? ''
  }
}

function parseJob(value: unknown): ManagedPrashnaJob {
  const parsed = JobSchema.parse(value)
  return parsed as ManagedPrashnaJob
}

export class PlatformManagedPrashnaJobStore implements ManagedPrashnaJobStore {
  private async call(
    principal: Principal,
    body: Record<string, unknown>,
    retryAmbiguousWrite = false,
  ): Promise<Record<string, unknown> | null> {
    for (let attempt = 0; ; attempt += 1) {
      let response: Response
      try {
        response = await fetch(`${PLATFORM_URL()}/api/mcp/prashna_jobs`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${await identityToken()}`,
            'X-MCP-Internal-Token': process.env['MCP_INTERNAL_TOKEN'] ?? '',
            'X-MCP-User': principal.user_uid,
            'X-MCP-Key-Id': principal.key_id,
            'X-MCP-Auth-Kind': principal.key_id.startsWith('oauth_sha256:') ? 'oauth' : 'api_key',
          },
          body: JSON.stringify(body),
          signal: AbortSignal.timeout(20_000),
        })
      } catch (error) {
        if (retryAmbiguousWrite && attempt === 0) continue
        throw error
      }
      let payload: Record<string, unknown>
      try {
        payload = await response.json() as Record<string, unknown>
      } catch {
        if (retryAmbiguousWrite && attempt === 0) continue
        throw new Error(`MANAGED_JOB_STORE_UNAVAILABLE: non-JSON response (${response.status})`)
      }
      if (retryAmbiguousWrite && attempt === 0 && response.status >= 500) continue
      if (response.status === 404) return null
      if (!response.ok || payload.ok !== true) {
        const code = typeof payload.error === 'string' ? payload.error : 'MANAGED_JOB_STORE_UNAVAILABLE'
        throw new Error(code)
      }
      return payload
    }
  }

  async create(principal: Principal, input: { job_id: string; chart_id: string; request: ManagedPrashnaJobRequest }): Promise<ManagedPrashnaJob> {
    const payload = await this.call(principal, {
      action: 'create', job_id: input.job_id, chart_id: input.chart_id, question: input.request.question,
      response_format: input.request.response_format, scope_tuple: input.request.scope_tuple,
    }, true)
    return parseJob(payload?.job)
  }

  async get(principal: Principal, jobId: string): Promise<ManagedPrashnaJob | null> {
    const payload = await this.call(principal, { action: 'get', job_id: jobId })
    return payload ? parseJob(payload.job) : null
  }

  async claim(principal: Principal, jobId: string, workerId: string): Promise<{ disposition: 'acquired' | 'not_acquired'; job: ManagedPrashnaJob } | null> {
    const payload = await this.call(principal, { action: 'claim', job_id: jobId, worker_id: workerId, lease_seconds: 450 })
    if (!payload) return null
    const disposition = payload.disposition
    if (disposition !== 'acquired' && disposition !== 'not_acquired') throw new Error('MANAGED_JOB_STORE_INVALID_RESPONSE')
    return { disposition, job: parseJob(payload.job) }
  }

  async updateProgress(principal: Principal, jobId: string, workerId: string, progress: ManagedPrashnaJobProgress): Promise<ManagedPrashnaJob> {
    const payload = await this.call(principal, { action: 'progress', job_id: jobId, worker_id: workerId, progress, lease_seconds: 450 })
    return parseJob(payload?.job)
  }

  async complete(principal: Principal, jobId: string, workerId: string, result: PrashnaAskEngineResponse): Promise<ManagedPrashnaJob> {
    const payload = await this.call(principal, { action: 'complete', job_id: jobId, worker_id: workerId, result }, true)
    return parseJob(payload?.job)
  }

  async fail(principal: Principal, jobId: string, workerId: string, error: string): Promise<ManagedPrashnaJob> {
    const payload = await this.call(principal, { action: 'fail', job_id: jobId, worker_id: workerId, error }, true)
    return parseJob(payload?.job)
  }
}

let store: ManagedPrashnaJobStore = new PlatformManagedPrashnaJobStore()

/** Production facade. Tests may replace its backend explicitly; there is no runtime memory fallback. */
export const managedPrashnaJobs: ManagedPrashnaJobStore = {
  create: (...args) => store.create(...args),
  get: (...args) => store.get(...args),
  claim: (...args) => store.claim(...args),
  updateProgress: (...args) => store.updateProgress(...args),
  complete: (...args) => store.complete(...args),
  fail: (...args) => store.fail(...args),
}

export function __setManagedPrashnaJobStoreForTests(replacement: ManagedPrashnaJobStore): void {
  store = replacement
}

export function __resetManagedPrashnaJobStoreForTests(): void {
  store = new PlatformManagedPrashnaJobStore()
  cachedClient = null
}

type TestJob = ManagedPrashnaJob & {
  owner_uid: string
  owner_key_id: string
  lease_owner: string | null
  terminal_worker_id: string | null
}

/** Explicit test backend. Production never selects this class or falls back to it. */
export class InMemoryManagedPrashnaJobStoreForTests implements ManagedPrashnaJobStore {
  private readonly jobs = new Map<string, TestJob>()

  clear(): void { this.jobs.clear() }

  expireLease(jobId: string): void {
    const job = this.jobs.get(jobId)
    if (job) job.lease_expires_at = new Date(Date.now() - 1).toISOString()
  }

  async create(principal: Principal, input: { job_id: string; chart_id: string; request: ManagedPrashnaJobRequest }): Promise<ManagedPrashnaJob> {
    const existing = this.jobs.get(input.job_id)
    if (existing) {
      const sameRequest = JSON.stringify(existing.request) === JSON.stringify(input.request)
      if (existing.owner_uid !== principal.user_uid || existing.owner_key_id !== principal.key_id
        || existing.chart_id !== input.chart_id || !sameRequest) {
        throw new Error('MANAGED_JOB_IDEMPOTENCY_CONFLICT')
      }
      return { ...existing }
    }
    const now = new Date().toISOString()
    const job: TestJob = {
      job_id: input.job_id, chart_id: input.chart_id, status: 'pending',
      progress: null, result: null, error: null, attempt_count: 0,
      created_at: now, updated_at: now, lease_expires_at: null,
      request: input.request, owner_uid: principal.user_uid, owner_key_id: principal.key_id,
      lease_owner: null, terminal_worker_id: null,
    }
    this.jobs.set(job.job_id, job)
    return { ...job }
  }

  private owned(principal: Principal, jobId: string): TestJob | null {
    const job = this.jobs.get(jobId)
    return job?.owner_uid === principal.user_uid && job.owner_key_id === principal.key_id ? job : null
  }

  async get(principal: Principal, jobId: string): Promise<ManagedPrashnaJob | null> {
    const job = this.owned(principal, jobId)
    return job ? { ...job } : null
  }

  async claim(principal: Principal, jobId: string, workerId: string): Promise<{ disposition: 'acquired' | 'not_acquired'; job: ManagedPrashnaJob } | null> {
    const job = this.owned(principal, jobId)
    if (!job) return null
    if (job.status === 'complete' || job.status === 'failed'
      || (job.status === 'running' && job.lease_expires_at && Date.parse(job.lease_expires_at) > Date.now())) {
      return { disposition: 'not_acquired', job: { ...job } }
    }
    if (job.attempt_count >= 3) {
      Object.assign(job, {
        status: 'failed', error: 'MANAGED_JOB_RETRY_EXHAUSTED', lease_owner: null,
        lease_expires_at: null, terminal_worker_id: workerId,
      })
      return { disposition: 'not_acquired', job: { ...job } }
    }
    Object.assign(job, {
      status: 'running', lease_owner: workerId, attempt_count: job.attempt_count + 1,
      lease_expires_at: new Date(Date.now() + 450_000).toISOString(),
      progress: job.progress ?? { message: 'prashna_ask: engine call started', pct: 0 },
      updated_at: new Date().toISOString(),
    })
    return { disposition: 'acquired', job: { ...job } }
  }

  async updateProgress(principal: Principal, jobId: string, workerId: string, progress: ManagedPrashnaJobProgress): Promise<ManagedPrashnaJob> {
    const job = this.owned(principal, jobId)
    if (!job || job.status !== 'running' || job.lease_owner !== workerId) throw new Error('MANAGED_JOB_LEASE_LOST')
    Object.assign(job, { progress, lease_expires_at: new Date(Date.now() + 450_000).toISOString(), updated_at: new Date().toISOString() })
    return { ...job }
  }

  async complete(principal: Principal, jobId: string, workerId: string, result: PrashnaAskEngineResponse): Promise<ManagedPrashnaJob> {
    const job = this.owned(principal, jobId)
    if (job?.status === 'complete' && job.terminal_worker_id === workerId
      && JSON.stringify(job.result) === JSON.stringify(result)) return { ...job }
    if (!job || job.status !== 'running' || job.lease_owner !== workerId) throw new Error('MANAGED_JOB_LEASE_LOST')
    Object.assign(job, { status: 'complete', result, error: null, progress: { message: 'prashna_ask: complete', pct: 100 }, lease_owner: null, lease_expires_at: null, terminal_worker_id: workerId, updated_at: new Date().toISOString() })
    return { ...job }
  }

  async fail(principal: Principal, jobId: string, workerId: string, error: string): Promise<ManagedPrashnaJob> {
    const job = this.owned(principal, jobId)
    if (job?.status === 'failed' && job.terminal_worker_id === workerId && job.error === error) return { ...job }
    if (!job || job.status !== 'running' || job.lease_owner !== workerId) throw new Error('MANAGED_JOB_LEASE_LOST')
    Object.assign(job, { status: 'failed', result: null, error, progress: { message: 'prashna_ask: failed', pct: 100 }, lease_owner: null, lease_expires_at: null, terminal_worker_id: workerId, updated_at: new Date().toISOString() })
    return { ...job }
  }
}

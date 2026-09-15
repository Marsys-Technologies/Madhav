/** Internal durable store for managed-MCP Prashna jobs. Engine execution remains in /prashna_ask. */
import 'server-only'
import { randomUUID } from 'node:crypto'
import { NextResponse } from 'next/server'
import { z } from 'zod'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { query } from '@/lib/db/client'
import { resolveMcpPrincipalRole } from '@/lib/mcp/auth'
import { validateMcpServiceRequest } from '@/lib/mcp/service_token'
import { ScopeTupleSchema } from '@/lib/vidhi/scope_classifier'
import {
  claimManagedPrashnaJob,
  completeManagedPrashnaJob,
  createManagedPrashnaJob,
  failManagedPrashnaJob,
  getManagedPrashnaJob,
  updateManagedPrashnaJobProgress,
  type ManagedPrashnaJobRow,
} from '@/lib/vidhi/inquiry/managed_job_store'

export const maxDuration = 30

const BodySchema = z.discriminatedUnion('action', [
  z.object({
    action: z.literal('create'), job_id: z.string().uuid(), chart_id: z.string().uuid(),
    question: z.string().trim().min(1).max(4000),
    response_format: z.enum(['digest', 'summary', 'standard', 'narrative', 'full']),
    scope_tuple: ScopeTupleSchema.optional(),
  }).strict(),
  z.object({ action: z.literal('get'), job_id: z.string().uuid() }).strict(),
  z.object({
    action: z.literal('claim'), job_id: z.string().uuid(), worker_id: z.string().uuid(),
    lease_seconds: z.number().int().min(30).max(600).optional(),
  }).strict(),
  z.object({
    action: z.literal('progress'), job_id: z.string().uuid(), worker_id: z.string().uuid(),
    progress: z.object({ message: z.string().trim().min(1).max(500), pct: z.number().int().min(0).max(99) }).strict(),
    lease_seconds: z.number().int().min(30).max(600).optional(),
  }).strict(),
  z.object({
    action: z.literal('complete'), job_id: z.string().uuid(), worker_id: z.string().uuid(),
    result: z.record(z.string(), z.unknown()),
  }).strict(),
  z.object({ action: z.literal('fail'), job_id: z.string().uuid(), worker_id: z.string().uuid(), error: z.string().trim().min(1).max(1000) }).strict(),
])

function response(data: Record<string, unknown>, status = 200) {
  return NextResponse.json(data, { status })
}

function projectJob(row: ManagedPrashnaJobRow, includeRequest = false): Record<string, unknown> {
  return {
    job_id: row.job_id,
    chart_id: row.chart_id,
    status: row.status,
    progress: row.progress_jsonb,
    result: row.result_jsonb,
    error: row.error_text,
    attempt_count: row.attempt_count,
    created_at: row.created_at,
    updated_at: row.updated_at,
    lease_expires_at: row.lease_expires_at,
    ...(includeRequest ? { request: row.request_jsonb } : {}),
  }
}

async function entitled(uid: string, chartId: string): Promise<boolean> {
  const role = await resolveMcpPrincipalRole(uid)
  return (await authorizeChartAccess({ principal: { uid, role }, chartId, db: { query } })) !== 'deny'
}

export async function POST(request: Request) {
  if (!(await validateMcpServiceRequest(request))) return response({ ok: false, error: 'Unauthorized' }, 401)
  const principalUid = request.headers.get('x-mcp-user')
  const principalKeyId = request.headers.get('x-mcp-key-id')
  const principalAuthKind = request.headers.get('x-mcp-auth-kind')
  if (!principalUid || !principalKeyId || (principalAuthKind !== 'api_key' && principalAuthKind !== 'oauth')) {
    return response({ ok: false, error: 'Principal headers required' }, 401)
  }

  let raw: unknown
  try { raw = await request.json() } catch { return response({ ok: false, error: 'INVALID_JSON' }, 400) }
  const parsed = BodySchema.safeParse(raw)
  if (!parsed.success) return response({ ok: false, error: 'INVALID_REQUEST' }, 400)
  const body = parsed.data

  try {
    if (body.action === 'create') {
      if (!(await entitled(principalUid, body.chart_id))) return response({ ok: false, error: 'AUTHZ_DENIED' }, 401)
      const row = await createManagedPrashnaJob({
        job_id: body.job_id, principal_uid: principalUid, principal_key_id: principalKeyId,
        principal_auth_kind: principalAuthKind,
        chart_id: body.chart_id,
        request: { question: body.question, response_format: body.response_format, scope_tuple: body.scope_tuple },
      })
      return response({ ok: true, job: projectJob(row) })
    }

    const current = await getManagedPrashnaJob({
      job_id: body.job_id, principal_uid: principalUid, principal_key_id: principalKeyId,
    })
    if (!current) return response({ ok: false, error: 'MANAGED_JOB_NOT_FOUND_OR_EXPIRED' }, 404)
    if (!(await entitled(principalUid, current.chart_id))) return response({ ok: false, error: 'AUTHZ_DENIED' }, 401)

    if (body.action === 'get') return response({ ok: true, job: projectJob(current) })
    if (body.action === 'claim') {
      const claimed = await claimManagedPrashnaJob({
        job_id: body.job_id, principal_uid: principalUid, principal_key_id: principalKeyId,
        lease_owner: body.worker_id, lease_seconds: body.lease_seconds,
      })
      if (!claimed) return response({ ok: false, error: 'MANAGED_JOB_NOT_FOUND_OR_EXPIRED' }, 404)
      return response({
        ok: true,
        disposition: claimed.status === 'running' && claimed.lease_owner === body.worker_id ? 'acquired' : 'not_acquired',
        job: projectJob(claimed, true),
      })
    }
    if (body.action === 'progress') {
      const updated = await updateManagedPrashnaJobProgress({
        job_id: body.job_id, principal_uid: principalUid, principal_key_id: principalKeyId,
        lease_owner: body.worker_id, progress: body.progress, lease_seconds: body.lease_seconds,
      })
      return response({ ok: true, job: projectJob(updated) })
    }
    if (body.action === 'complete') {
      const serialized = JSON.stringify(body.result)
      if (!serialized || Buffer.byteLength(serialized) > 2 * 1024 * 1024) {
        return response({ ok: false, error: 'MANAGED_JOB_RESULT_TOO_LARGE' }, 413)
      }
      const updated = await completeManagedPrashnaJob({
        job_id: body.job_id, principal_uid: principalUid, principal_key_id: principalKeyId,
        lease_owner: body.worker_id, result: body.result,
      })
      return response({ ok: true, job: projectJob(updated) })
    }
    const updated = await failManagedPrashnaJob({
      job_id: body.job_id, principal_uid: principalUid, principal_key_id: principalKeyId,
      lease_owner: body.worker_id, error: body.error,
    })
    return response({ ok: true, job: projectJob(updated) })
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    if (message === 'MANAGED_JOB_ACTIVE_LIMIT_REACHED' || message === 'MANAGED_JOB_CREATION_RATE_LIMITED') {
      return response({ ok: false, error: message }, 429)
    }
    if (message === 'MANAGED_JOB_LEASE_LOST') return response({ ok: false, error: message }, 409)
    const traceId = randomUUID()
    console.error('[mcp:prashna_jobs] store failure', { traceId, error })
    return response({ ok: false, error: 'MANAGED_JOB_STORE_UNAVAILABLE', trace_id: traceId }, 500)
  }
}

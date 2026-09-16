/**
 * Pre-traffic Pūrṇa readiness probe. Every Pūrṇa probe/store write is rolled
 * back; normal MCP key last-used telemetry may commit during authentication.
 */
import 'server-only'
import { randomUUID } from 'node:crypto'
import { NextResponse } from 'next/server'
import { z } from 'zod'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { query } from '@/lib/db/client'
import { validateMcpKey } from '@/lib/mcp/auth'
import { checkRateLimit } from '@/lib/mcp/rate_limiter'
import {
  issueInquiryLifecycleToken,
  loadInquiryLifecycleSigningKeyRing,
  verifyInquiryLifecycleToken,
} from '@/lib/vidhi/inquiry'
import { probeInquiryStoreReadiness } from '@/lib/vidhi/inquiry/store_pool'

const BodySchema = z.object({ chart_id: z.string().uuid() }).strict()

function response(data: Record<string, unknown>, status = 200) {
  return NextResponse.json(data, { status, headers: { 'Cache-Control': 'no-store' } })
}

function readinessFailureCode(error: unknown, stage: 'signing' | 'database'): string {
  const message = error instanceof Error ? error.message : ''
  if (/^INQUIRY_[A-Z0-9_]+$/.test(message)) return message

  const code = typeof error === 'object' && error !== null && 'code' in error
    ? String((error as { code?: unknown }).code ?? '')
    : ''
  if (/^[A-Z0-9]{5}$/.test(code)) return `PG_${code}`
  if (['ECONNREFUSED', 'ETIMEDOUT', 'ENETUNREACH', 'EHOSTUNREACH'].includes(code)) {
    return 'DB_CONNECTIVITY_FAILED'
  }
  if (/password authentication failed/i.test(message)) return 'DB_AUTHENTICATION_FAILED'
  if (/permission denied/i.test(message)) return 'DB_PERMISSION_FAILED'
  if (/cloud sql|connector/i.test(message)) return 'DB_CONNECTOR_FAILED'
  return stage === 'signing' ? 'INQUIRY_SIGNING_READINESS_UNCLASSIFIED' : 'INQUIRY_DATABASE_READINESS_UNCLASSIFIED'
}

export async function POST(request: Request) {
  const principal = await validateMcpKey(request.headers.get('authorization'))
  if (!principal) return response({ ok: false, error: 'Unauthorized' }, 401)
  const canaryKeyId = process.env.PURNA_READINESS_CANARY_KEY_ID
  if (!canaryKeyId || principal.key_id !== canaryKeyId) {
    return response({ ok: false, error: 'Unauthorized' }, 401)
  }
  const rateLimit = await checkRateLimit(`purna-readiness:${principal.key_id}`)
  if (!rateLimit.allowed) {
    return NextResponse.json(
      { ok: false, error: 'RATE_LIMITED' },
      {
        status: 429,
        headers: {
          'Cache-Control': 'no-store',
          'Retry-After': String(rateLimit.retry_after_seconds ?? 60),
        },
      },
    )
  }

  let raw: unknown
  try { raw = await request.json() } catch { return response({ ok: false, error: 'INVALID_JSON' }, 400) }
  const parsed = BodySchema.safeParse(raw)
  if (!parsed.success) return response({ ok: false, error: 'INVALID_REQUEST' }, 400)

  const permission = await authorizeChartAccess({
    principal: { uid: principal.user_uid, role: principal.role },
    chartId: parsed.data.chart_id,
    db: { query },
  })
  if (permission === 'deny') return response({ ok: false, error: 'AUTHZ_DENIED' }, 403)

  let signingRing: ReturnType<typeof loadInquiryLifecycleSigningKeyRing>
  try {
    signingRing = loadInquiryLifecycleSigningKeyRing()
    const subject = `${principal.user_uid}:${principal.key_id}`
    const issued = issueInquiryLifecycleToken({
      sub: subject,
      inquiry_id: randomUUID(),
      chart_id: parsed.data.chart_id,
      contract_hash: 'sha256:readiness-contract',
      execution_plan_hash: 'sha256:readiness-plan',
      contract_state_hash: 'sha256:readiness-state',
      catalog_hash: 'sha256:readiness-catalog',
      compatibility_version: 'readiness-v1',
      overlay_version: 'sha256:readiness-overlay',
      chart_build_id: 'readiness-build',
      revision: 0,
      allowed_transition: 'finalize',
      next_action_ids: [],
      ttl_seconds: 60,
    }, signingRing)
    verifyInquiryLifecycleToken(issued.token, signingRing, subject)

  } catch (error) {
    const failureCode = readinessFailureCode(error, 'signing')
    console.error('[mcp:inquiry:readiness] candidate probe failed', {
      code: 'INQUIRY_READINESS_FAILED', stage: 'signing', failure_code: failureCode,
    })
    return response({
      ok: false,
      error: 'INQUIRY_READINESS_FAILED',
      failure_stage: 'signing',
      failure_code: failureCode,
    }, 503)
  }

  try {
    const database = await probeInquiryStoreReadiness({
      principalUid: principal.user_uid,
      principalKeyId: principal.key_id,
      chartId: parsed.data.chart_id,
    })
    return response({
      ok: true,
      deployed_sha: process.env.NIRMANA_DEPLOYED_SHA ?? null,
      revision: process.env.K_REVISION ?? null,
      signing_round_trip: true,
      database,
    })
  } catch (error) {
    const failureCode = readinessFailureCode(error, 'database')
    console.error('[mcp:inquiry:readiness] candidate probe failed', {
      code: 'INQUIRY_READINESS_FAILED', stage: 'database', failure_code: failureCode,
    })
    return response({
      ok: false,
      error: 'INQUIRY_READINESS_FAILED',
      failure_stage: 'database',
      failure_code: failureCode,
    }, 503)
  }
}

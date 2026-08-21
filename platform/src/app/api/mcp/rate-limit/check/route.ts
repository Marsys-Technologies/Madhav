/**
 * POST /api/mcp/rate-limit/check — RATE-07 fleet-wide bucket consume.
 *
 * Called by the MCP sidecar's OAuth rate-limit gate
 * (`platform-mcp/src/lib/oauth_rate_limit.ts`). The sidecar has NO direct
 * database access — every OAuth DB operation it performs already routes through
 * this service over `X-MCP-Internal-Token` (see
 * `platform-mcp/src/oauth/oauth_platform_client.ts`) — so the rate-limit store
 * reaches it the same way, over a dependency those endpoints already have.
 *
 * Service-to-service only: `X-MCP-Internal-Token` required, fail-closed.
 *
 * Request (JSON body):
 *   { route: string, subject_kind: 'ip'|'client'|'principal'|'route_global',
 *     subject: string, limit: number, window_seconds: number }
 *
 * Response 200:
 *   { allowed, limit, hits, remaining, window_seconds, retry_after_seconds }
 *   ↑ 200 for BOTH allowed and denied. This endpoint reports a decision; it does
 *     not enforce one. The 429 belongs to the OAuth endpoint the caller is
 *     protecting, where the OAuth-shaped error body and Retry-After header
 *     belong too. Returning 429 from here would be ambiguous with "you, the
 *     sidecar, are being rate limited".
 *
 * Response 400: invalid arguments (never treated by the caller as "allowed").
 * Response 401: bad/absent service token.
 * Response 500: store failure — the caller MUST fail closed on this.
 *
 * PARIŚEṢA-V4 · GA-2 ruling · 2026-08-21
 */

import 'server-only'
import { NextResponse } from 'next/server'

import { validateServiceToken } from '@/lib/mcp/service_token'
import {
  consumeRateBucket,
  pruneExpiredRateBuckets,
  shouldPrune,
  RateBucketArgumentError,
  SUBJECT_KINDS,
  type SubjectKind,
} from '@/lib/mcp/oauth_rate_limit'

interface CheckBody {
  route?: unknown
  subject_kind?: unknown
  subject?: unknown
  limit?: unknown
  window_seconds?: unknown
}

export async function POST(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let body: CheckBody
  try {
    body = (await request.json()) as CheckBody
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const route = typeof body.route === 'string' ? body.route : ''
  const subjectKind = body.subject_kind
  const subject = typeof body.subject === 'string' ? body.subject : ''
  const limit = typeof body.limit === 'number' ? body.limit : NaN
  const windowSeconds = typeof body.window_seconds === 'number' ? body.window_seconds : NaN

  if (!SUBJECT_KINDS.includes(subjectKind as SubjectKind)) {
    return NextResponse.json(
      { error: `subject_kind must be one of: ${SUBJECT_KINDS.join(', ')}` },
      { status: 400 }
    )
  }

  try {
    const decision = await consumeRateBucket({
      route,
      subjectKind: subjectKind as SubjectKind,
      subject,
      limit,
      windowSeconds,
    })

    // Opportunistic, bounded garbage collection. Deliberately NOT awaited into
    // the decision path's latency budget beyond its own short statement, and
    // deliberately swallowing its own errors (see pruneExpiredRateBuckets).
    if (shouldPrune()) {
      void pruneExpiredRateBuckets()
    }

    return NextResponse.json({
      allowed: decision.allowed,
      limit: decision.limit,
      hits: decision.hits,
      remaining: decision.remaining,
      window_seconds: decision.windowSeconds,
      retry_after_seconds: decision.retryAfterSeconds,
    })
  } catch (err) {
    if (err instanceof RateBucketArgumentError) {
      return NextResponse.json({ error: err.message }, { status: 400 })
    }
    // Store failure. 500 with NO decision field — there is no honest decision to
    // report, and the caller is contractually required to fail closed rather
    // than infer one.
    console.error('[mcp:rate-limit:check] store failure:', err)
    return NextResponse.json({ error: 'rate_limit_store_unavailable' }, { status: 500 })
  }
}

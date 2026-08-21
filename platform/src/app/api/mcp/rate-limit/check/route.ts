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
 * ── BATCHED, WITH SERVER-SIDE STOP-ON-DENY (security review fix) ────────────
 * The body carries an ORDERED list of buckets. They are charged in order and
 * evaluation STOPS at the first denial. This is not a performance nicety — it
 * closes two real defects an adversarial review of the first draft found:
 *
 *   1. FLEET-WIDE DoS LEVER. The first draft charged the per-IP bucket and the
 *      route-wide global ceiling unconditionally (in parallel), so a single IP
 *      could pour its rejected traffic into the GLOBAL bucket and exhaust it for
 *      everyone. Against `oauth_register` (global 120/hour) roughly two seconds
 *      of traffic from one address would 429 client registration worldwide for
 *      an hour — and since rejected requests keep charging, the attacker could
 *      hold that window pinned indefinitely. Stopping at the first denial caps
 *      any one address's contribution to the global bucket at its OWN per-IP
 *      limit, which is what makes a route-wide ceiling meaningful rather than
 *      weaponisable.
 *   2. AMPLIFICATION INTO THE SHARED DB POOL. Two charges meant two HTTPS calls
 *      and two pool acquisitions per request, against a pool of `max: 10` that
 *      `amjis-web` shares with chart queries, chat and session verification —
 *      i.e. the control intended to stop a flood became the mechanism by which
 *      the flood took down the web app. One batched call is one acquisition, and
 *      a denied caller costs exactly one statement rather than two.
 *
 * Ordering therefore matters and is the caller's contract: charge the
 * narrowest, most caller-specific bucket FIRST.
 *
 * Request (JSON body):
 *   { buckets: [ { route, subject_kind, subject, limit, window_seconds }, … ] }
 *   1..4 entries.
 *
 * Response 200:
 *   { allowed, decisions: [ …one per bucket ACTUALLY CHARGED… ] }
 *   ↑ 200 for BOTH allowed and denied. This endpoint reports a decision; it does
 *     not enforce one. The 429 belongs to the OAuth endpoint the caller is
 *     protecting, where the OAuth-shaped error body and Retry-After header
 *     belong too. Returning 429 from here would be ambiguous with "you, the
 *     sidecar, are being rate limited".
 *     `decisions` is SHORTER than `buckets` when a stop-on-deny occurred — the
 *     buckets after the denial were deliberately not charged.
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

interface BucketSpec {
  route?: unknown
  subject_kind?: unknown
  subject?: unknown
  limit?: unknown
  window_seconds?: unknown
}

interface CheckBody {
  buckets?: unknown
}

/** Caps the work one authenticated service call can request. */
const MAX_BUCKETS_PER_CALL = 4

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

  if (!Array.isArray(body.buckets) || body.buckets.length === 0) {
    return NextResponse.json({ error: 'buckets must be a non-empty array' }, { status: 400 })
  }
  if (body.buckets.length > MAX_BUCKETS_PER_CALL) {
    return NextResponse.json(
      { error: `buckets may contain at most ${MAX_BUCKETS_PER_CALL} entries` },
      { status: 400 }
    )
  }

  // Validate the WHOLE batch before charging any of it, so a malformed trailing
  // entry cannot leave the earlier ones charged against a request that is then
  // rejected as a 400.
  const specs: Array<{ route: string; subjectKind: SubjectKind; subject: string; limit: number; windowSeconds: number }> = []
  for (const raw of body.buckets as BucketSpec[]) {
    const subjectKind = raw?.subject_kind
    if (!SUBJECT_KINDS.includes(subjectKind as SubjectKind)) {
      return NextResponse.json(
        { error: `subject_kind must be one of: ${SUBJECT_KINDS.join(', ')}` },
        { status: 400 }
      )
    }
    specs.push({
      route: typeof raw?.route === 'string' ? raw.route : '',
      subjectKind: subjectKind as SubjectKind,
      subject: typeof raw?.subject === 'string' ? raw.subject : '',
      limit: typeof raw?.limit === 'number' ? raw.limit : NaN,
      windowSeconds: typeof raw?.window_seconds === 'number' ? raw.window_seconds : NaN,
    })
  }

  try {
    const decisions = []
    let allowed = true

    for (const spec of specs) {
      const d = await consumeRateBucket(spec)
      decisions.push({
        subject_kind: spec.subjectKind,
        allowed: d.allowed,
        limit: d.limit,
        hits: d.hits,
        remaining: d.remaining,
        window_seconds: d.windowSeconds,
        retry_after_seconds: d.retryAfterSeconds,
      })
      if (!d.allowed) {
        // STOP-ON-DENY. Every later bucket in the batch is deliberately NOT
        // charged — see the header: this is what stops one caller's rejected
        // traffic from draining a shared route-wide ceiling, and what keeps a
        // flood to one statement per request instead of N.
        allowed = false
        break
      }
    }

    // Opportunistic, bounded garbage collection. AWAITED: `amjis-web` runs
    // without --no-cpu-throttling, so CPU is throttled the instant the response
    // is sent and a floating promise is not guaranteed to run at all — which
    // would quietly falsify migration 580's "no cron job maintains this table".
    // It is a bounded, LIMIT-ed DELETE and it swallows its own errors, so
    // awaiting it cannot fail or meaningfully delay a request.
    if (shouldPrune()) {
      // Its own try/catch, not just the helper's internal one: garbage
      // collection must be incapable of turning a completed decision into a
      // 500, no matter how the helper is changed later.
      try {
        await pruneExpiredRateBuckets()
      } catch (pruneErr) {
        console.warn('[mcp:rate-limit:check] prune failed (non-fatal):', pruneErr)
      }
    }

    return NextResponse.json({ allowed, decisions })
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

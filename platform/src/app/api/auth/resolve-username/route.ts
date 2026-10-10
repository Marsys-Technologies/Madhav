import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import { getTrustedClientIp, ipRateLimitKey } from '@/lib/security/client_ip'
import { BoundedRateLimiter } from '@/lib/security/bounded_rate_limiter'

/**
 * POST /api/auth/resolve-username — public (outside the proxy matcher). Turns a
 * username into the account's email so username login can sign in with Firebase.
 * The success contract (200 `{ email }`) is a SS ruling and must not change, so
 * the abuse controls (SS N-373 / PR-S1, item 4; SESSION_GATE_AUDIT HIGH) are:
 *
 *  1. A STRICT per-IP rate limit on the TRUSTED client IP (`getTrustedClientIp`:
 *     the hop our own infrastructure appended to X-Forwarded-For — never the
 *     client-controlled leftmost entry). The limiter runs BEFORE the lookup, so
 *     a throttled answer can never depend on whether the username exists, and the
 *     throttled body is the same canonical envelope for every caller.
 *  2. UNIFORM RESPONSE TIME: every outcome of the lookup (found, not found,
 *     database error) is held to a fixed minimum duration plus bounded jitter,
 *     so latency does not reveal whether the account exists.
 *  3. A BOUNDED counter map (hard cap + TTL sweep): attacker-reachable keys
 *     cannot grow memory without limit. `checkRpm` is not reused because its
 *     counter map never evicts (see bounded_rate_limiter.ts).
 *
 * The limit is per instance (in-memory), like the other limiters in this app.
 */

/** Lookups allowed per trusted IP per minute. A real login is one request. */
const LOOKUP_RPM = 10
const WINDOW_MS = 60_000
/** Hard cap on tracked IPs. */
const MAX_TRACKED_IPS = 10_000
/** Every lookup outcome takes at least this long... */
const MIN_LOOKUP_MS = 400
/** ...plus 0..JITTER_MS of random extra, so the floor itself is not a fingerprint. */
const JITTER_MS = 75
/** Longest identifier we will look up (an email address is at most 254). */
const MAX_USERNAME_LENGTH = 254

const limiter = new BoundedRateLimiter({
  limit: LOOKUP_RPM,
  windowMs: WINDOW_MS,
  maxEntries: MAX_TRACKED_IPS,
})

async function padToUniformDuration(startedAtMs: number): Promise<void> {
  const target = MIN_LOOKUP_MS + Math.floor(Math.random() * (JITTER_MS + 1))
  const remaining = target - (Date.now() - startedAtMs)
  if (remaining > 0) await new Promise<void>((resolve) => setTimeout(resolve, remaining))
}

export async function POST(request: Request) {
  const rate = limiter.check(ipRateLimitKey(getTrustedClientIp(request.headers)))
  if (!rate.allowed) return res.rateLimited(undefined, rate.retryAfterSeconds)

  let username: string | undefined
  try {
    const body = await request.json()
    username = body?.username
  } catch {
    return res.badRequest('invalid request body')
  }

  if (
    !username ||
    typeof username !== 'string' ||
    !username.trim() ||
    username.length > MAX_USERNAME_LENGTH
  ) {
    return res.badRequest('username required')
  }

  const startedAt = Date.now()
  let response: Response
  try {
    const result = await query<{ email: string | null; status: string }>(
      "SELECT email, status FROM profiles WHERE lower(username)=lower($1) AND status='active' LIMIT 1",
      [username.trim()]
    )
    const data = result.rows[0] ?? null
    response = !data || !data.email ? res.notFound() : Response.json({ email: data.email })
  } catch {
    response = res.dbError()
  }

  await padToUniformDuration(startedAt)
  return response
}

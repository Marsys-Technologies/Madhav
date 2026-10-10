import { createHash } from 'node:crypto'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import { getTrustedClientIp, ipRateLimitKey } from '@/lib/security/client_ip'
import { BoundedRateLimiter } from '@/lib/security/bounded_rate_limiter'

/**
 * POST /api/auth/resolve-username — public (outside the proxy matcher). Turns a
 * username into the account's email so username login can sign in with Firebase.
 * The success contract (200 `{ email }`) is a SS ruling and must not change, so
 * the abuse controls (SS N-373 / PR-S1, item 4; SESSION_GATE_AUDIT HIGH; reshaped
 * by SS N-403) are:
 *
 *  1. TWO rate limits, BOTH must pass, both BEFORE the lookup:
 *       (b) per TRUSTED client IP, 60/min (`getTrustedClientIp`: the hop our own
 *           infrastructure appended to X-Forwarded-For — never the client-
 *           controlled leftmost entry). Checked FIRST, before the body is read.
 *           It bounds how many distinct usernames one source can enumerate.
 *       (a) per REQUESTED USERNAME, global (not per IP), 5/min. The key is the
 *           sha256 hex of `username.trim().toLowerCase()` — never the raw
 *           username, which is never logged or stored. It keys on what was
 *           REQUESTED, not on whether the account exists, so a throttled answer
 *           can never reveal existence. It bounds guessing against one account
 *           however many source addresses the caller rotates through.
 *     Order: IP limit -> parse/validate body (400) -> username limit -> lookup.
 *     Both throttles return the SAME canonical `res.rateLimited` envelope (with
 *     Retry-After). A request refused by (a) never reaches the lookup and spends
 *     no further IP budget than the one token it already took.
 *     WHY TWO: browser traffic arrives through Firebase Hosting, where the
 *     trusted hop (MARSYS_TRUSTED_PROXY_HOPS = 1) is the Hosting address itself,
 *     so every browser login shares ONE per-IP bucket. A tight per-IP limit
 *     (was 10/min) therefore throttled all users together; the per-IP limit is
 *     now a coarse backstop and the per-username limit does the precise work.
 *     DISCLOSED TRADE-OFF: because the username limit is global, anyone can
 *     deliberately spend a victim's 5/min and delay that user's USERNAME login by
 *     up to a minute (their 429 carries Retry-After; email login is unaffected).
 *     Accepted: it is a delay, not a lockout, and not an enumeration oracle.
 *  2. UNIFORM RESPONSE TIME: every outcome of the lookup (found, not found,
 *     database error) is held to a fixed minimum duration plus bounded jitter,
 *     so latency does not reveal whether the account exists.
 *  3. BOUNDED counter maps (hard cap + TTL sweep + eviction): attacker-reachable
 *     keys cannot grow memory without limit. `checkRpm` is not reused because its
 *     counter map never evicts (see bounded_rate_limiter.ts).
 *
 * Both limits are per instance (in-memory), like the other limiters in this app.
 */

/** Lookups allowed per trusted IP per minute (shared Hosting address: coarse backstop). */
const IP_LOOKUP_RPM = 60
/** Lookups allowed per requested username per minute, across all IPs. */
const USERNAME_LOOKUP_RPM = 5
const WINDOW_MS = 60_000
/** Hard cap on tracked IPs. */
const MAX_TRACKED_IPS = 10_000
/** Hard cap on tracked usernames (hashes). */
const MAX_TRACKED_USERNAMES = 10_000
/** Every lookup outcome takes at least this long... */
const MIN_LOOKUP_MS = 400
/** ...plus 0..JITTER_MS of random extra, so the floor itself is not a fingerprint. */
const JITTER_MS = 75
/** Longest identifier we will look up (an email address is at most 254). */
const MAX_USERNAME_LENGTH = 254

const ipLimiter = new BoundedRateLimiter({
  limit: IP_LOOKUP_RPM,
  windowMs: WINDOW_MS,
  maxEntries: MAX_TRACKED_IPS,
})

const usernameLimiter = new BoundedRateLimiter({
  limit: USERNAME_LOOKUP_RPM,
  windowMs: WINDOW_MS,
  maxEntries: MAX_TRACKED_USERNAMES,
})

/** Limiter key for a requested username: sha256 hex of the normalised name (never the raw name). */
function usernameRateLimitKey(username: string): string {
  return createHash('sha256').update(username.trim().toLowerCase()).digest('hex')
}

async function padToUniformDuration(startedAtMs: number): Promise<void> {
  const target = MIN_LOOKUP_MS + Math.floor(Math.random() * (JITTER_MS + 1))
  const remaining = target - (Date.now() - startedAtMs)
  if (remaining > 0) await new Promise<void>((resolve) => setTimeout(resolve, remaining))
}

export async function POST(request: Request) {
  const ipRate = ipLimiter.check(ipRateLimitKey(getTrustedClientIp(request.headers)))
  if (!ipRate.allowed) return res.rateLimited(undefined, ipRate.retryAfterSeconds)

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

  const usernameRate = usernameLimiter.check(usernameRateLimitKey(username))
  if (!usernameRate.allowed) return res.rateLimited(undefined, usernameRate.retryAfterSeconds)

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

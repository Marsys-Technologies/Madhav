/**
 * oauth_rate_limit.ts — RATE-07 fleet-wide rate limiting for the five OAuth
 * mutation endpoints (PARIŚEṢA-V4 GA-2 ruling, 2026-08-21).
 *
 * ── WHAT WAS BROKEN ─────────────────────────────────────────────────────────
 * `POST /mcp/oauth/{authorize,token,refresh,register}` and
 * `GET /mcp/oauth/callback` had NO rate limiting at all. This service's only
 * limiter (`./rate_limiter.ts`) is an in-process Map keyed on `key_id`, wired
 * to exactly one call site (`POST /mcp`) AFTER principal resolution — OAuth
 * mutations carry no `key_id`, and four of the five are unauthenticated. That
 * Map is also per-instance (this service autoscales at `--concurrency=80`) and
 * never evicts.
 *
 * ── WHAT THIS MODULE IS ─────────────────────────────────────────────────────
 * A gate that charges a shared Postgres bucket via the platform API — the same
 * `X-MCP-Internal-Token` channel every OAuth handler here already uses for
 * every DB operation it performs. It is FAIL-CLOSED: if the store cannot be
 * reached, the request is rejected. That is affordable precisely because these
 * endpoints already cannot function without the platform API (createDbAuthCode,
 * validateOAuthClient, consumeDbAuthCode, issueDbTokens, refreshDbAccessToken
 * are all platform round-trips), so this adds no new failure domain — see the
 * ruling for why that argument decided Postgres over Redis.
 *
 * ── TWO-LAYER CHARGING, AND WHY ─────────────────────────────────────────────
 * Charging a bucket keyed on an UNVALIDATED identifier is a quota-poisoning
 * primitive: anyone who knows (or guesses) a victim's `client_id` could spend
 * that client's quota from an unrelated IP and lock the real client out. So:
 *
 *   LAYER 1 (pre-handler, always): keyed on the transport-derived client IP and
 *     on a route-wide global ceiling. Neither is caller-assertable.
 *   LAYER 2 (post-validation, opt-in per route): keyed on a principal or client
 *     that the handler has ALREADY proven — charged only after validation
 *     succeeds. A caller can therefore only ever spend its own quota.
 *
 * `chargeValidatedSubject` exists solely for layer 2 and is documented never to
 * be called with an unverified identifier.
 *
 * ── CLIENT IP DERIVATION: A DISCLOSED AMBIGUITY ─────────────────────────────
 * Behind Cloud Run, `req.socket.remoteAddress` is the Google front end, never
 * the client, and `X-Forwarded-For` is attacker-influenced on its LEFT: each
 * hop APPENDS, so a client that sends `X-Forwarded-For: 1.2.3.4` produces
 * `1.2.3.4, <real peer>`. Therefore:
 *
 *   - The leftmost XFF entry is NEVER used. It is fully caller-controlled.
 *   - The identity is taken from the RIGHT, `MCP_TRUSTED_PROXY_HOPS` entries in
 *     (default 1 = the rightmost = the value appended by the nearest trusted
 *     infrastructure hop).
 *
 * With `hops=1` and direct Cloud Run ingress — which is a real, reachable path:
 * `amjis-mcp` is deployed `--allow-unauthenticated` and its `*.run.app` URL is
 * live and smoke-tested by the deploy workflow — the rightmost entry IS the
 * true peer address.
 *
 * DISCLOSED, NOT RESOLVED: production also advertises `MCP_BASE_URL=
 * https://madhav.marsys.in/mcp`, and the repository does not contain the config
 * that routes that hostname to this service (`firebase.json` rewrites `**` to
 * `amjis-web`; there is no load-balancer or Cloud Armor module under `infra/`).
 * If that path traverses one or more additional proxies, the rightmost entry is
 * that proxy's address rather than the client's, and every request arriving by
 * that route shares one bucket. That failure mode is CONSERVATIVE (over-
 * restrictive, never permissive) and is never attacker-steerable onto an
 * innocent third party — but it is real, and it is why the hop count is an
 * explicit operator setting rather than a hardcoded guess. An operator who adds
 * a front door MUST raise `MCP_TRUSTED_PROXY_HOPS` to match, and the route-wide
 * global ceiling exists so that the endpoint stays protected either way.
 *
 * @module oauth_rate_limit
 */

import type { Request, Response } from 'express'

// ── Environment ──────────────────────────────────────────────────────────────

function env(name: string): string | undefined {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return ((globalThis as any)['process']?.env?.[name] as string | undefined) ?? undefined
}

function platformUrl(): string {
  return (env('PLATFORM_URL') ?? 'http://localhost:3000').replace(/\/$/, '')
}

/**
 * Kill switch. Default ON — a security control that ships defaulted-off is a
 * control nobody has. Set to 'false' only to roll back deliberately (and note
 * migration 580's DOWN section: turn this off BEFORE dropping the table).
 */
export function rateLimitEnabled(): boolean {
  return (env('MCP_OAUTH_RATE_LIMIT_ENABLED') ?? 'true').toLowerCase() !== 'false'
}

/**
 * How many proxy hops in front of this service are trusted to have appended to
 * X-Forwarded-For. 1 = direct Cloud Run ingress (the default and the
 * directly-reachable path). See the module header's disclosure.
 */
export function trustedProxyHops(): number {
  const raw = Number(env('MCP_TRUSTED_PROXY_HOPS') ?? '1')
  if (!Number.isInteger(raw) || raw < 1 || raw > 8) return 1
  return raw
}

// ── Per-route limits ─────────────────────────────────────────────────────────

export interface RouteLimit {
  /** Per-client-IP limit within `windowSeconds`. */
  perIp: number
  /** Route-wide ceiling across ALL callers. Bounds key cardinality under an
   *  IP-spray attack, and bounds absolute DB write amplification. */
  global: number
  /** Post-validation per-principal/per-client limit, when the route charges one. */
  perSubject: number
  windowSeconds: number
}

/**
 * Limits are ABUSE CEILINGS, not fairness quotas — deliberately generous
 * relative to any real OAuth client, whose whole flow is a handful of requests
 * per user session. They are sized so that the disclosed IP-collapse failure
 * mode above (many clients sharing one bucket behind an unmodelled proxy) does
 * not bite legitimate traffic, while still making a flood ineffective.
 *
 * `oauth_authorize` is the tightest per-IP because it is unauthenticated AND it
 * writes an `mcp_oauth_auth_codes` row per call for an unvalidated client_id.
 */
export const ROUTE_LIMITS: Record<string, RouteLimit> = {
  oauth_authorize: { perIp: 30, global: 600, perSubject: 60, windowSeconds: 60 },
  oauth_callback:  { perIp: 60, global: 900, perSubject: 60, windowSeconds: 60 },
  oauth_token:     { perIp: 60, global: 900, perSubject: 120, windowSeconds: 60 },
  oauth_refresh:   { perIp: 60, global: 900, perSubject: 120, windowSeconds: 60 },
  oauth_register:  { perIp: 10, global: 120, perSubject: 20, windowSeconds: 3600 },
}

export type OAuthRouteKey = keyof typeof ROUTE_LIMITS

// ── Client identity ──────────────────────────────────────────────────────────

export interface DerivedIdentity {
  ip: string
  /**
   * How the address was obtained. `socket` means no XFF was present at all,
   * which behind Cloud Run should not happen — it is reported so a canary can
   * notice rather than silently trusting a value of unknown provenance.
   */
  source: 'xff' | 'socket' | 'unknown'
}

/**
 * Derive the client IP. NEVER reads the leftmost X-Forwarded-For entry, and
 * never reads any single-value client-assertable header (`X-Real-IP`,
 * `CF-Connecting-IP`, `True-Client-IP`, …): behind Cloud Run those are
 * verbatim caller input with no appending hop to make them trustworthy.
 */
export function deriveClientIdentity(req: Request): DerivedIdentity {
  const rawHeader = req.headers['x-forwarded-for']
  // Express gives string | string[]; multiple XFF headers are joined in order.
  const joined = Array.isArray(rawHeader) ? rawHeader.join(',') : rawHeader

  if (typeof joined === 'string' && joined.trim().length > 0) {
    const parts = joined
      .split(',')
      .map((p) => p.trim())
      .filter((p) => p.length > 0)

    if (parts.length > 0) {
      // Count from the RIGHT. If the chain is shorter than the configured hop
      // count, clamp to the leftmost available entry rather than wrapping — a
      // truncated chain means fewer proxies than configured, and the leftmost
      // remaining value is the least-spoofable one still present.
      const idx = Math.max(0, parts.length - trustedProxyHops())
      const candidate = parts[idx]
      if (candidate) return { ip: normaliseIp(candidate), source: 'xff' }
    }
  }

  const socketAddr = req.socket?.remoteAddress
  if (socketAddr) return { ip: normaliseIp(socketAddr), source: 'socket' }

  return { ip: 'unknown', source: 'unknown' }
}

/** Strip an IPv4-mapped IPv6 prefix and any :port suffix so the same client
 *  cannot occupy two buckets by presenting two spellings of one address. */
export function normaliseIp(raw: string): string {
  let ip = raw.trim()
  if (ip.startsWith('::ffff:')) ip = ip.slice('::ffff:'.length)
  // IPv4 with port ("1.2.3.4:5678"). Never strip from bare IPv6 (many colons).
  const colons = (ip.match(/:/g) ?? []).length
  if (colons === 1) ip = ip.split(':')[0] ?? ip
  // Bracketed IPv6 with port ("[::1]:443").
  const bracketed = /^\[([^\]]+)\](?::\d+)?$/.exec(ip)
  if (bracketed?.[1]) ip = bracketed[1]
  return ip.toLowerCase()
}

// ── Store client ─────────────────────────────────────────────────────────────

export interface BucketDecision {
  allowed: boolean
  limit: number
  hits: number
  remaining: number
  window_seconds: number
  retry_after_seconds: number
}

/** Thrown when the shared store cannot render a decision. Callers fail closed. */
export class RateLimitStoreUnavailable extends Error {}

/**
 * Charge one bucket. Throws {@link RateLimitStoreUnavailable} on ANY failure —
 * network error, timeout, non-2xx, or malformed body. There is deliberately no
 * "assume allowed" branch anywhere in this function.
 */
export async function consumeBucket(args: {
  route: string
  subjectKind: 'ip' | 'client' | 'principal' | 'route_global'
  subject: string
  limit: number
  windowSeconds: number
}): Promise<BucketDecision> {
  let res: globalThis.Response
  try {
    res = await fetch(`${platformUrl()}/api/mcp/rate-limit/check`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': env('MCP_INTERNAL_TOKEN') ?? '',
      },
      body: JSON.stringify({
        route: args.route,
        subject_kind: args.subjectKind,
        subject: args.subject,
        limit: args.limit,
        window_seconds: args.windowSeconds,
      }),
      signal: AbortSignal.timeout(3_000),
    })
  } catch (err) {
    throw new RateLimitStoreUnavailable(
      `rate-limit store unreachable: ${err instanceof Error ? err.message : String(err)}`,
    )
  }

  if (!res.ok) {
    throw new RateLimitStoreUnavailable(`rate-limit store returned ${res.status}`)
  }

  let body: Partial<BucketDecision>
  try {
    body = (await res.json()) as Partial<BucketDecision>
  } catch {
    throw new RateLimitStoreUnavailable('rate-limit store returned a non-JSON body')
  }

  if (typeof body.allowed !== 'boolean') {
    // A body without an explicit boolean decision is not a decision. Refusing
    // to coerce it is the point (CLAUDE.md §N.8: no signal without a detector).
    throw new RateLimitStoreUnavailable('rate-limit store returned no explicit decision')
  }

  return {
    allowed: body.allowed,
    limit: Number(body.limit ?? args.limit),
    hits: Number(body.hits ?? 0),
    remaining: Number(body.remaining ?? 0),
    window_seconds: Number(body.window_seconds ?? args.windowSeconds),
    retry_after_seconds: Math.max(1, Number(body.retry_after_seconds ?? args.windowSeconds)),
  }
}

// ── Responses ────────────────────────────────────────────────────────────────

/**
 * 429 with `Retry-After` (RFC 6585 / RFC 7231 §7.1.3).
 *
 * DELIBERATE SHAPE DECISION: RFC 6749 §5.2 defines a closed set of `error`
 * codes for the token endpoint and `rate_limit_exceeded` is not among them.
 * We use it anyway, with `error_description`, because (a) the transport status
 * 429 is the machine-readable signal that actually matters here, (b) a client
 * that does not recognise the code treats it as an unknown error, which is the
 * correct behaviour, and (c) reusing a spec code such as `invalid_request`
 * would be actively misleading — the request was well-formed. The body also
 * mirrors this service's existing 429 on `POST /mcp` so both surfaces read the
 * same to a connector.
 */
export function sendRateLimited(res: Response, retryAfterSeconds: number, route: string): void {
  const n = Math.max(1, Math.ceil(retryAfterSeconds))
  res.setHeader('Retry-After', String(n))
  res.status(429).json({
    error: 'rate_limit_exceeded',
    error_description: `Too many requests to ${route}. Retry after ${n} seconds.`,
    retry_after_seconds: n,
  })
}

/**
 * 503 when the store itself is unavailable — fail CLOSED. A `Retry-After` is
 * included so a well-behaved client backs off instead of retrying into the same
 * outage. This is distinct from 429 on purpose: the caller did nothing wrong,
 * and conflating the two would tell an operator "we are being flooded" during
 * what is actually a store outage.
 */
export function sendStoreUnavailable(res: Response): void {
  res.setHeader('Retry-After', '30')
  res.status(503).json({
    error: 'temporarily_unavailable',
    error_description:
      'Rate-limit store unavailable; this endpoint fails closed rather than serving unlimited.',
  })
}

// ── The gate ─────────────────────────────────────────────────────────────────

/**
 * Express middleware for layer 1. Charges the per-IP bucket AND the route-wide
 * global ceiling before the handler runs — i.e. before any DB row is written
 * and before any credential is examined.
 *
 * Both buckets are charged on every request (not short-circuited on the first
 * rejection) so that a caller cannot use the global ceiling's rejection to
 * avoid having its own IP bucket counted.
 */
export function oauthRateLimit(route: OAuthRouteKey) {
  const limits = ROUTE_LIMITS[route]
  if (!limits) throw new Error(`[oauth_rate_limit] unknown route key: ${route}`)

  return async function gate(req: Request, res: Response, next: () => void): Promise<void> {
    if (!rateLimitEnabled()) {
      next()
      return
    }

    // NOTE the try starts BEFORE identity derivation, and covers everything.
    // Express 4 does not catch rejections from an async middleware: an
    // unexpected throw anywhere in here would leave the request hanging with no
    // response and no limit applied. Every escape route from this function is
    // therefore either next(), a 429, or a 503 — never an exception.
    try {
      const identity = deriveClientIdentity(req)

      const [ipDecision, globalDecision] = await Promise.all([
        consumeBucket({
          route,
          subjectKind: 'ip',
          subject: identity.ip,
          limit: limits.perIp,
          windowSeconds: limits.windowSeconds,
        }),
        consumeBucket({
          route,
          subjectKind: 'route_global',
          subject: '',
          limit: limits.global,
          windowSeconds: limits.windowSeconds,
        }),
      ])

      if (!ipDecision.allowed || !globalDecision.allowed) {
        const retry = Math.max(
          ipDecision.allowed ? 0 : ipDecision.retry_after_seconds,
          globalDecision.allowed ? 0 : globalDecision.retry_after_seconds,
        )
        console.warn(
          `[oauth_rate_limit] 429 route=${route} ip_source=${identity.source} ` +
            `ip_allowed=${ipDecision.allowed} global_allowed=${globalDecision.allowed}`,
        )
        sendRateLimited(res, retry, route)
        return
      }
    } catch (err) {
      console.error(
        `[oauth_rate_limit] FAIL-CLOSED route=${route}: ` +
          (err instanceof Error ? err.message : String(err)),
      )
      sendStoreUnavailable(res)
      return
    }

    next()
  }
}

/**
 * Layer 2. Charge a bucket keyed on an identity the HANDLER HAS ALREADY
 * VALIDATED — an authenticated principal uid, or a `client_id` whose secret has
 * just been verified.
 *
 * NEVER call this with an identifier taken straight from the request body or
 * from an unverified header: doing so hands any anonymous caller the ability to
 * exhaust a named victim's quota. That is the whole reason this is a separate
 * function from {@link oauthRateLimit} rather than an option on it.
 *
 * Returns `true` when the request may proceed. When it returns `false` it has
 * ALREADY written the response (429 or 503) and the caller must return
 * immediately without writing anything further.
 */
export async function chargeValidatedSubject(
  res: Response,
  route: OAuthRouteKey,
  subjectKind: 'client' | 'principal',
  validatedSubject: string,
): Promise<boolean> {
  if (!rateLimitEnabled()) return true

  const limits = ROUTE_LIMITS[route]
  if (!limits) throw new Error(`[oauth_rate_limit] unknown route key: ${route}`)

  if (!validatedSubject) {
    // An empty validated subject means the caller's own validation did not
    // actually produce an identity. Charging '' would merge every such caller
    // into one bucket and quietly mislabel it, so we refuse — but we refuse by
    // failing CLOSED rather than by throwing. Express 4 does not catch
    // rejections from an async route handler, so a throw here would hang the
    // request instead of answering it. The log line carries the diagnosis.
    console.error(
      `[oauth_rate_limit] BUG: chargeValidatedSubject called with an empty ${subjectKind} ` +
        `subject on route=${route} — failing closed rather than charging a merged bucket`,
    )
    sendStoreUnavailable(res)
    return false
  }

  try {
    const decision = await consumeBucket({
      route,
      subjectKind,
      subject: validatedSubject,
      limit: limits.perSubject,
      windowSeconds: limits.windowSeconds,
    })
    if (!decision.allowed) {
      console.warn(`[oauth_rate_limit] 429 route=${route} subject_kind=${subjectKind} (post-validation)`)
      sendRateLimited(res, decision.retry_after_seconds, route)
      return false
    }
    return true
  } catch (err) {
    console.error(
      `[oauth_rate_limit] FAIL-CLOSED (post-validation) route=${route}: ` +
        (err instanceof Error ? err.message : String(err)),
    )
    sendStoreUnavailable(res)
    return false
  }
}

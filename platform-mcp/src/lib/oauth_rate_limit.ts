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
 * Kill switch. The CODE default is ON — a security control that ships
 * defaulted-off is a control nobody has.
 *
 * ⚠️ THE DEPLOYED DEFAULT IS CURRENTLY THE OPPOSITE, DELIBERATELY AND
 * TEMPORARILY: `deploy.yml`'s `deploy-mcp` env_vars sets
 * `MCP_OAUTH_RATE_LIMIT_ENABLED=false` for the merge that introduces this
 * module, because `consumeBuckets()` below depends on an amjis-web route that
 * the SAME merge creates, and `deploy-mcp`/`deploy-web` run in parallel — the
 * MCP revision can promote traffic before that route exists and would then 503
 * every OAuth mutation. The follow-up that flips it to `true` is documented
 * inline at that env_vars line (follow-up item RATE-07-ENABLE). Do not
 * "correct" the code default to match the deployed one: the code default is
 * right, the deployment override is the temporary part.
 *
 * When false, both entrypoints — {@link oauthRateLimit} and
 * {@link chargeValidatedSubject} — return on their FIRST statement, ahead of
 * every fail-closed branch, so disabled is a true no-op and not merely a
 * usually-skips. Set to 'false' otherwise only to roll back deliberately (and
 * note migration 580's DOWN section: turn this off BEFORE dropping the table).
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
// There is deliberately NO `oauth_refresh` profile. `POST /mcp/oauth/refresh` is
// a thin alias that forces grant_type=refresh_token and delegates to the same
// handleToken as `POST /mcp/oauth/token`, so it shares the `oauth_token` bucket.
// A separate profile would have handed a refresh-token guessing attack the
// per-IP budget twice — once per URL — while the docs advertised it once.
export const ROUTE_LIMITS: Record<string, RouteLimit> = {
  oauth_authorize: { perIp: 30, global: 600, perSubject: 60, windowSeconds: 60 },
  oauth_callback:  { perIp: 60, global: 900, perSubject: 60, windowSeconds: 60 },
  oauth_token:     { perIp: 60, global: 900, perSubject: 120, windowSeconds: 60 },
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
  // Bracketed IPv6 with optional port ("[::1]:443") — unwrap FIRST, so the
  // colon-counting below sees the address rather than the brackets.
  const bracketed = /^\[([^\]]+)\](?::\d+)?$/.exec(ip)
  if (bracketed?.[1]) ip = bracketed[1]
  // IPv4-mapped IPv6, both the short and the long spelling. Without the long
  // form, `::ffff:1.2.3.4` and `0:0:0:0:0:ffff:1.2.3.4` would be two buckets
  // for one host.
  ip = ip.replace(/^::ffff:/i, '').replace(/^0:0:0:0:0:ffff:/i, '')
  // IPv4 with port ("1.2.3.4:5678"). Never strip from bare IPv6 (many colons).
  const colons = (ip.match(/:/g) ?? []).length
  if (colons === 1) ip = ip.split(':')[0] ?? ip
  return ip.toLowerCase()
}

/**
 * Reduce an address to the unit a rate limit should actually be charged to.
 *
 * WHY (security review finding — key cardinality): a per-EXACT-address bucket
 * is not bounded in any meaningful way on IPv6. A routed /64 is the standard
 * allocation for a single VPS or residential line, giving one attacker 2^64
 * free bucket keys — one new `mcp_rate_buckets` row per request, forever,
 * which no prune interval can outrun. So IPv6 is charged per /64 — the smallest
 * unit an attacker cannot multiply for free.
 *
 * IPv4 is deliberately charged per EXACT address, NOT per /24. The asymmetry is
 * the point: IPv4 addresses are scarce and cost real money, so the spray attack
 * that motivates prefix-grouping is not cheap there — while a blanket /24 would
 * group up to 256 unrelated ISP customers into one bucket for no gain. Grouping
 * only where the free-multiplication threat actually exists keeps the limit
 * honest for legitimate users.
 */
export function rateLimitSubjectForIp(ip: string): string {
  if (!ip.includes(':')) return ip // IPv4 (or the 'unknown' sentinel) — exact.

  const hextets = expandIpv6(ip)
  if (!hextets) return ip // Unparseable: charge it verbatim rather than guess.
  return `${hextets.slice(0, 4).join(':')}::/64`
}

/**
 * Expand an IPv6 address to its 8 canonical hextets, or null if it does not
 * parse. Leading zeros are stripped so `2001:0db8:…` and `2001:db8:…` cannot
 * become two buckets for one prefix.
 */
function expandIpv6(ip: string): string[] | null {
  const canon = (h: string): string => (h.replace(/^0+/, '') || '0').toLowerCase()

  const runs = ip.split('::')
  if (runs.length > 2) return null // more than one '::' is not a valid address

  if (runs.length === 1) {
    const parts = ip.split(':')
    return parts.length === 8 ? parts.map(canon) : null
  }

  const head = runs[0] ? runs[0].split(':') : []
  const tail = runs[1] ? runs[1].split(':') : []
  const missing = 8 - head.length - tail.length
  if (missing < 0) return null

  return [...head.map(canon), ...Array<string>(missing).fill('0'), ...tail.map(canon)]
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

export interface BucketSpec {
  route: string
  subjectKind: 'ip' | 'client' | 'principal' | 'route_global'
  subject: string
  limit: number
  windowSeconds: number
}

export interface BatchDecision {
  allowed: boolean
  /** One entry per bucket ACTUALLY charged — shorter than the request on a
   *  stop-on-deny, because later buckets were deliberately not charged. */
  decisions: Array<BucketDecision & { subject_kind: string }>
}

// ── Deny-only load shed (per-instance) ───────────────────────────────────────
//
// SECURITY REVIEW FINDING this addresses: under a flood, every request — even
// one certain to be rejected — still cost a round trip to the platform and one
// of the `max: 10` DB pool connections that `amjis-web` shares with chart
// queries, chat, and session verification. The control meant to stop a flood
// became the mechanism by which the flood took down the web app.
//
// THIS IS NOT A SECOND RATE LIMITER, and the distinction is load-bearing: this
// cache can only ever DENY. It never grants, never extends a limit, and is
// never consulted to decide that something is allowed. Losing it entirely (cold
// instance, restart, eviction) costs efficiency and nothing else — the
// authority remains the shared Postgres bucket. That is precisely why the
// per-instance state criticised in this module's header is unacceptable as an
// authority but correct as a shed valve.
//
// Bounded: entries are dropped once expired, and the map is hard-capped.

interface DenyEntry { until: number }
const denyUntil = new Map<string, DenyEntry>()
const DENY_CACHE_MAX = 10_000

/** Test-only: clear the shed cache. */
export function __resetDenyCacheForTests(): void {
  denyUntil.clear()
}

function shedKey(route: string, subject: string): string {
  return `${route}|${subject}`
}

/** Seconds remaining on a locally-remembered denial, or 0 if none applies. */
export function shedRemaining(route: string, subject: string, now = Date.now()): number {
  const e = denyUntil.get(shedKey(route, subject))
  if (!e) return 0
  if (e.until <= now) {
    denyUntil.delete(shedKey(route, subject))
    return 0
  }
  return Math.max(1, Math.ceil((e.until - now) / 1000))
}

function rememberDenial(route: string, subject: string, retryAfterSeconds: number, now = Date.now()): void {
  if (denyUntil.size >= DENY_CACHE_MAX) {
    // Drop expired entries first; if that frees nothing, refuse to grow. A full
    // cache simply means no shedding — the shared store still decides.
    for (const [k, v] of denyUntil) if (v.until <= now) denyUntil.delete(k)
    if (denyUntil.size >= DENY_CACHE_MAX) return
  }
  denyUntil.set(shedKey(route, subject), { until: now + retryAfterSeconds * 1000 })
}

/**
 * Charge an ORDERED batch of buckets in ONE call. The store charges them in
 * order and STOPS at the first denial, so:
 *   - a caller's rejected traffic can never drain a shared route-wide ceiling
 *     (the fleet-wide DoS lever an adversarial review found in the first draft);
 *   - a denied request costs one statement, not N.
 * Order the narrowest, most caller-specific bucket FIRST.
 *
 * Throws {@link RateLimitStoreUnavailable} on ANY failure — network error,
 * timeout, non-2xx, or malformed body. There is deliberately no "assume
 * allowed" branch anywhere in this function.
 */
export async function consumeBuckets(specs: BucketSpec[]): Promise<BatchDecision> {
  let res: globalThis.Response
  try {
    res = await fetch(`${platformUrl()}/api/mcp/rate-limit/check`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': env('MCP_INTERNAL_TOKEN') ?? '',
      },
      body: JSON.stringify({
        buckets: specs.map((s) => ({
          route: s.route,
          subject_kind: s.subjectKind,
          subject: s.subject,
          limit: s.limit,
          window_seconds: s.windowSeconds,
        })),
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

  let body: { allowed?: unknown; decisions?: unknown }
  try {
    body = (await res.json()) as { allowed?: unknown; decisions?: unknown }
  } catch {
    throw new RateLimitStoreUnavailable('rate-limit store returned a non-JSON body')
  }

  if (typeof body.allowed !== 'boolean' || !Array.isArray(body.decisions)) {
    // A body without an explicit boolean decision is not a decision. Refusing
    // to coerce it is the point (CLAUDE.md §N.8: no signal without a detector).
    throw new RateLimitStoreUnavailable('rate-limit store returned no explicit decision')
  }

  const decisions = (body.decisions as Array<Record<string, unknown>>).map((d, i) => ({
    subject_kind: String(d['subject_kind'] ?? specs[i]?.subjectKind ?? 'unknown'),
    allowed: d['allowed'] === true,
    limit: Number(d['limit'] ?? specs[i]?.limit ?? 0),
    hits: Number(d['hits'] ?? 0),
    remaining: Number(d['remaining'] ?? 0),
    window_seconds: Number(d['window_seconds'] ?? specs[i]?.windowSeconds ?? 60),
    retry_after_seconds: Math.max(1, Number(d['retry_after_seconds'] ?? specs[i]?.windowSeconds ?? 60)),
  }))

  return { allowed: body.allowed, decisions }
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
      const subject = rateLimitSubjectForIp(identity.ip)

      // Load shed BEFORE the round trip. Deny-only: a hit here means this
      // subject was already told 429 by the authoritative store and the window
      // has not yet elapsed, so re-asking cannot change the answer. A miss
      // decides nothing and falls through to the store.
      const shed = shedRemaining(route, subject)
      if (shed > 0) {
        sendRateLimited(res, shed, route)
        return
      }

      // ORDER IS LOAD-BEARING: the per-IP bucket is charged FIRST so that the
      // store's stop-on-deny prevents this caller's rejected traffic from
      // draining the shared route-wide ceiling. Charging them together (as the
      // first draft did) let one address 429 the entire fleet.
      const batch = await consumeBuckets([
        {
          route,
          subjectKind: 'ip',
          subject,
          limit: limits.perIp,
          windowSeconds: limits.windowSeconds,
        },
        {
          route,
          subjectKind: 'route_global',
          subject: '',
          limit: limits.global,
          windowSeconds: limits.windowSeconds,
        },
      ])

      if (!batch.allowed) {
        const denied = batch.decisions.find((d) => !d.allowed)
        const retry = denied?.retry_after_seconds ?? limits.windowSeconds
        // Only remember a denial that is attributable to THIS subject. A
        // route_global denial is everyone's, so caching it per-subject would
        // spread one global outage across per-caller entries for no benefit.
        if (denied?.subject_kind === 'ip') rememberDenial(route, subject, retry)
        console.warn(
          `[oauth_rate_limit] 429 route=${route} ip_source=${identity.source} ` +
            `denied_by=${denied?.subject_kind ?? 'unknown'}`,
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
    const batch = await consumeBuckets([
      {
        route,
        subjectKind,
        subject: validatedSubject,
        limit: limits.perSubject,
        windowSeconds: limits.windowSeconds,
      },
    ])
    if (!batch.allowed) {
      const denied = batch.decisions.find((d) => !d.allowed)
      console.warn(`[oauth_rate_limit] 429 route=${route} subject_kind=${subjectKind} (post-validation)`)
      sendRateLimited(res, denied?.retry_after_seconds ?? limits.windowSeconds, route)
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

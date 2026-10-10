/**
 * proxy.ts — the request boundary. Session gating for the whole app, plus (new)
 * per-caller rate limiting on the two Paripraśna serving doors.
 *
 * ── A note on the file name ─────────────────────────────────────────────────
 * The Paripraśna G1-D lane spec says "create `src/middleware.ts` (does not
 * exist)". `src/middleware.ts` indeed does not exist — because in Next.js 16
 * (this repo runs 16.2.4) the `middleware` convention was RENAMED to `proxy`
 * (`node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/
 * proxy.md`; `PROXY_LOCATION_REGEXP = (?:src/)?proxy` in next/dist/lib/
 * constants.js). THIS FILE IS THAT MIDDLEWARE, already in place and already
 * load-bearing: it is the app-wide session gate. So G1-D's rate limiting is
 * ADDED here rather than shipped as a second, competing request-boundary file.
 *
 * ── What G1-D added, and what it deliberately did not ───────────────────────
 * Added: a per-caller RPM window on `/api/pariprashna` and
 * `/api/mcp/prashna_ask`, using the SAME rolling-window implementation
 * `lib/mcp/rate_limiter.ts` uses (`checkRpm` from `rate_limiter_core.ts` — one
 * algorithm in the codebase, per the lane's "never a second implementation"
 * rule). It runs AFTER the session gate, so an unauthenticated caller still
 * gets 401/redirect rather than a misleading 429.
 *
 * NOT added: spend ceilings. NCD-8 requires them pre-dispatch with the VERIFIED
 * principal and a DB read; this layer verifies nothing cryptographically (see
 * the comment on parseJwtPayload) and the Next docs warn a proxy may be
 * CDN-deployed away from the app. So the authoritative NCD-8 gate — rate limit
 * AND spend ceilings — is `enforceTurnLimits()` inside each door, after auth and
 * before the first LLM call (`@/lib/limits`). This layer is the cheap outer
 * shield in front of it, not the accounting authority.
 *
 * Gated on `PARIPRASHNA_LIMITS_ENABLED` (default false): when off, this file
 * behaves exactly as it did before G1-D.
 *
 * ── SS N-373 / PR-S3: durable session gate (`SESSION_GATE_MODE`) ────────────
 * The shape check below (`isSessionValid`) is forgeable with no secret (audit
 * `SESSION_GATE_AUDIT.md` §0). This file now ALSO verifies the cookie
 * cryptographically (firebase-admin `verifySessionCookie(cookie, false)`: RS256
 * signature + exp + aud + iss; handlers keep `checkRevoked=true` via
 * `getServerUser`). All logic lives in `lib/security/session_gate.ts`.
 *
 *   SESSION_GATE_MODE   behaviour
 *   ------------------  ------------------------------------------------------
 *   off                 exactly the previous behaviour; no verification at all
 *   shadow  (DEFAULT)   previous decision stands; the cookie is also verified
 *                       and a failed verification (shape passed) logs
 *                       `session_gate_would_reject` {path, reason, mode} and
 *                       bumps a bounded counter. Never blocks. Infra errors
 *                       fail OPEN. Unset or unrecognised values mean shadow.
 *   enforce             shape AND cryptographic verification must pass, else
 *                       the same 401 (API) / redirect to /login (page) as for
 *                       an invalid session. Infra errors (firebase-admin init,
 *                       key fetch, timeout) FAIL CLOSED with a 401 (pages get a
 *                       plain 401, not a /login redirect, to avoid a redirect
 *                       loop while verification is down). Never throws.
 *
 * Runtime evidence (checked in the installed package, next 16.2.4, not memory):
 *   node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/
 *   proxy.md:217-219 "## Runtime — Proxy defaults to using the Node.js runtime.
 *   The `runtime` config option is not available in Proxy files. Setting the
 *   `runtime` config option in Proxy will throw an error."
 *   node_modules/next/dist/docs/01-app/02-guides/upgrading/version-16.md:629
 *   "The `edge` runtime is **NOT** supported in `proxy`. The `proxy` runtime is
 *   `nodejs`, and it cannot be configured."
 * So firebase-admin (Node-only) and node:crypto are importable here. This repo
 * deploys `output: "standalone"` to Cloud Run (a Node server), the case proxy.md
 * lists as supported. Next also says proxy state must not be assumed shared
 * with handlers, so the verdict cache/counters are per-process by design.
 *
 * Rollout: (1) deploy with the default (shadow); (2) read the Cloud Run logs
 * for `session_gate_would_reject` and `verify_error` for at least a day. Every
 * would-reject must be explained (expected: forged/expired cookies only; a
 * real user appearing means a config problem such as the wrong project's
 * credentials, fix BEFORE enforcing); (3) the owner sets SESSION_GATE_MODE=
 * enforce. Rollback: set SESSION_GATE_MODE=off (or shadow) as a Cloud Run env
 * change with no rebuild, or redeploy the previous revision.
 *
 * XFF observation (SS N-375): in shadow and enforce, the proxy logs
 * `{event:'xff_entry_count', host_class, count, path, mode}` for /api/* requests
 * (count = number of X-Forwarded-For entries; host_class = public | run_app |
 * other; never an address, the raw header or the host value; one line per
 * host_class+count+path per minute). Read these after a day of traffic to pick
 * MARSYS_TRUSTED_PROXY_HOPS. Set SESSION_GATE_PUBLIC_HOSTS (comma list) to pin
 * which hostnames count as `public`; unset, any non-run.app DNS name does.
 * LIMITATION: the matcher below excludes /api/auth/*, so the proxy never sees
 * resolve-username or recover; the sample comes from the other /api/* routes
 * behind the same front door and host.
 *
 * Rate-limit door: when cryptographic verification succeeded (shadow/enforce)
 * the web-door bucket is keyed on the VERIFIED `sub`; otherwise the previous
 * key is used. Known follow-ups NOT changed here: the client-supplied
 * `x-mcp-key-id` (MCP door) and the leftmost X-Forwarded-For fallback remain
 * spoofable, and the limiter itself is unchanged.
 */

import { NextResponse, type NextRequest } from 'next/server'

import { configService } from '@/lib/config/index'
import { checkRpm } from '@/lib/mcp/rate_limiter_core'
import { apiError } from '@/lib/errors'
import { RATE_LIMIT_ERROR_CODE } from '@/lib/limits/spend_ceiling'
import { safeNextPath } from '@/lib/auth/safe_next'
import {
  evaluateSessionGate,
  observeForwardedForEntryCount,
  resolveSessionGateMode,
} from '@/lib/security/session_gate'

// Lightweight JWT payload parse — no crypto. Real verification happens in each
// route handler via firebase-admin (Node.js runtime). Middleware only gates
// redirects; cryptographic enforcement is at the route layer.
function parseJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const segment = token.split('.')[1]
    if (!segment) return null
    const padded = segment.replace(/-/g, '+').replace(/_/g, '/').padEnd(
      segment.length + ((4 - (segment.length % 4)) % 4),
      '='
    )
    return JSON.parse(atob(padded)) as Record<string, unknown>
  } catch {
    return null
  }
}

function isSessionValid(sessionCookie: string | undefined): boolean {
  if (!sessionCookie) return false
  const payload = parseJwtPayload(sessionCookie)
  if (!payload) return false
  return (
    typeof payload.exp === 'number' &&
    payload.exp * 1000 > Date.now() &&
    typeof payload.iss === 'string' &&
    payload.iss.includes('session.firebase.google.com')
  )
}

// ── G1-D / NCD-8: per-caller rate limiting on the two serving doors ──────────

/** The two doors PPR-25 names. Kept as exact paths — this is not a prefix gate. */
const WEB_DOOR = '/api/pariprashna'
const MCP_DOOR = '/api/mcp/prashna_ask'

/**
 * Front-door window, deliberately looser than the per-turn gate inside each
 * door: this layer sheds obvious floods, it does not do the accounting.
 * Env: MARSYS_PROXY_RPM_LIMIT.
 */
const PROXY_RPM_LIMIT = parseInt(process.env.MARSYS_PROXY_RPM_LIMIT ?? '120', 10)

function isDoorPath(pathname: string): boolean {
  return pathname === WEB_DOOR || pathname.startsWith(`${WEB_DOOR}/`) || pathname === MCP_DOOR
}

/**
 * Per-caller key for the rolling window.
 *
 * MCP door: `x-mcp-key-id` is the resolved credential id every `/api/mcp/*`
 * route already keys its rate limit on — reuse it, do not invent a parallel
 * identity.
 *
 * Web door: the session cookie's `sub` claim is the Firebase uid, already
 * available from this file's own `parseJwtPayload`. It is a real per-USER key
 * — but note it is UNVERIFIED at this layer (same caveat as the session gate
 * above: cryptographic verification happens in the route handler). That is
 * acceptable for shedding load and is precisely why the authoritative per-user
 * limit lives behind real auth in `enforceTurnLimits()`.
 *
 * Neither present: the forwarded client IP, and finally one shared `anon`
 * bucket — an unidentifiable caller gets no private allowance.
 *
 * `verifiedSub` (SS N-373): when the session gate cryptographically verified the
 * cookie (shadow/enforce), that uid is trusted and wins, so a caller cannot
 * rotate a forged `sub` (or a spoofed `x-mcp-key-id`) to get a fresh bucket or
 * burn someone else's. Absent => exactly the previous keying.
 */
function rateLimitCallerKey(request: NextRequest, verifiedSub?: string): string {
  if (verifiedSub) return `proxy:web:uid:${verifiedSub}`

  const mcpKeyId = request.headers.get('x-mcp-key-id')
  if (mcpKeyId) return `proxy:mcp:key:${mcpKeyId}`

  const sessionCookie = request.cookies.get('__session')?.value
  const sub = sessionCookie ? parseJwtPayload(sessionCookie)?.sub : undefined
  if (typeof sub === 'string' && sub.length > 0) return `proxy:web:uid:${sub}`

  const forwarded = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim()
  if (forwarded) return `proxy:ip:${forwarded}`

  return 'proxy:anon'
}

/**
 * Returns a 429 when the caller has exhausted its window, else null.
 *
 * The refusal is a DESIGNED failure state: HTTP 429 with the same branchable
 * `LIMIT_RATE_LIMIT_EXCEEDED` code and canonical error envelope the doors
 * themselves return, plus `Retry-After`. Never a thrown error, never a 500.
 */
function checkDoorRateLimit(request: NextRequest, verifiedSub?: string): NextResponse | null {
  if (!configService.getFlag('PARIPRASHNA_LIMITS_ENABLED')) return null
  if (!isDoorPath(request.nextUrl.pathname)) return null
  // Only the request that actually starts a turn is metered. A GET (e.g. a
  // resume poll) costs nothing to serve and must not consume the allowance.
  if (request.method !== 'POST') return null

  const rpm = checkRpm(rateLimitCallerKey(request, verifiedSub), PROXY_RPM_LIMIT)
  if (rpm.allowed) return null

  return NextResponse.json(
    apiError(RATE_LIMIT_ERROR_CODE, 'Too many requests. Please slow down.', {
      retry: true,
      detail: rpm.retry_after_seconds
        ? `Rate limit of ${PROXY_RPM_LIMIT} requests/minute exceeded. Retry in ${rpm.retry_after_seconds}s.`
        : `Rate limit of ${PROXY_RPM_LIMIT} requests/minute exceeded.`,
    }),
    {
      status: 429,
      headers: rpm.retry_after_seconds
        ? { 'retry-after': String(rpm.retry_after_seconds) }
        : undefined,
    },
  )
}

/**
 * The refusal for an invalid session: 401 JSON for API paths, redirect to
 * /login for pages. `infraFailClosed` (enforce mode only, when the verifier
 * itself is unavailable) returns a plain 401 for pages too: a redirect to
 * /login for a possibly-valid user would loop while the verifier is down.
 *
 * SS N-383 (a): the page redirect carries `?next=<pathname>` ONLY when
 * `safeNextPath(pathname)` accepts the pathname (today: `/share/...` and
 * `/clients/...`), so the login page (which validates `next` with the same
 * function) can return the visitor to the page they asked for. Every other
 * page redirects to a plain `/login`, exactly as before. The pathname alone is
 * used, never the query string or hash (safeNextPath refuses both anyway), and
 * the value is only ever the validator's own return value, never raw input.
 * The same redirect is used in all `SESSION_GATE_MODE`s.
 */
function unauthorized(request: NextRequest, pathname: string, infraFailClosed = false): NextResponse {
  if (pathname.startsWith('/api/')) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }
  if (infraFailClosed) {
    return new NextResponse('Unauthorized', { status: 401 })
  }
  const loginUrl = new URL('/login', request.url)
  const next = safeNextPath(pathname)
  if (next) loginUrl.searchParams.set('next', next)
  return NextResponse.redirect(loginUrl)
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  // Public routes (no session required). The /api/auth/* prefix is also
  // excluded via the matcher below.
  const isPublic =
    pathname === '/' ||
    pathname === '/api/health' ||
    pathname.startsWith('/login') ||
    pathname.startsWith('/reset-password') ||
    pathname.startsWith('/api/access-requests') ||
    pathname.startsWith('/api/mcp/') ||
    pathname.startsWith('/api/admin/internal/') ||
    pathname.startsWith('/api/admin/cron/') ||
    pathname === '/api/cockpit/watchdog' ||
    // Safe because /api/retrieval/capability validates X-MCP-Internal-Token before any data access.
    // Do NOT remove that check — this allowlist entry depends on it.
    pathname.startsWith('/api/retrieval/')

  const gateMode = resolveSessionGateMode()
  // SS N-375: X-Forwarded-For ENTRY COUNT (a number, never an address) by host
  // class, rate-capped, to choose MARSYS_TRUSTED_PROXY_HOPS from data. No-op in `off`.
  if (pathname.startsWith('/api/')) {
    observeForwardedForEntryCount(gateMode, pathname, request.headers.get('host'), request.headers.get('x-forwarded-for'))
  }

  let verifiedSub: string | undefined
  if (!isPublic) {
    const sessionCookie = request.cookies.get('__session')?.value
    if (!isSessionValid(sessionCookie)) {
      return unauthorized(request, pathname)
    }

    // SS N-373: cryptographic verification, only for a cookie that already
    // passed the shape check. `off` does no work; `shadow` never denies.
    const decision = await evaluateSessionGate(gateMode, sessionCookie as string, pathname)
    if (decision.deny) {
      return unauthorized(request, pathname, decision.denyReason === 'verify_error')
    }
    verifiedSub = decision.verifiedSub
  }

  // G1-D / NCD-8. Placed AFTER the session gate on purpose: an unauthenticated
  // caller must get 401/redirect, never a 429 that misreports why it was
  // refused. No-op unless PARIPRASHNA_LIMITS_ENABLED is on AND this is a POST
  // to one of the two doors.
  const rateLimited = checkDoorRateLimit(request, verifiedSub)
  if (rateLimited) return rateLimited

  return NextResponse.next({ request })
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|icon.png|apple-icon.png|brand/|api/auth/).*)'],
}

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
 */

import { NextResponse, type NextRequest } from 'next/server'

import { configService } from '@/lib/config/index'
import { checkRpm } from '@/lib/mcp/rate_limiter_core'
import { apiError } from '@/lib/errors'
import { RATE_LIMIT_ERROR_CODE } from '@/lib/limits/spend_ceiling'

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
 */
function rateLimitCallerKey(request: NextRequest): string {
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
function checkDoorRateLimit(request: NextRequest): NextResponse | null {
  if (!configService.getFlag('PARIPRASHNA_LIMITS_ENABLED')) return null
  if (!isDoorPath(request.nextUrl.pathname)) return null
  // Only the request that actually starts a turn is metered. A GET (e.g. a
  // resume poll) costs nothing to serve and must not consume the allowance.
  if (request.method !== 'POST') return null

  const rpm = checkRpm(rateLimitCallerKey(request), PROXY_RPM_LIMIT)
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

  if (!isPublic) {
    const sessionCookie = request.cookies.get('__session')?.value
    if (!isSessionValid(sessionCookie)) {
      if (pathname.startsWith('/api/')) {
        return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
      }
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }

  // G1-D / NCD-8. Placed AFTER the session gate on purpose: an unauthenticated
  // caller must get 401/redirect, never a 429 that misreports why it was
  // refused. No-op unless PARIPRASHNA_LIMITS_ENABLED is on AND this is a POST
  // to one of the two doors.
  const rateLimited = checkDoorRateLimit(request)
  if (rateLimited) return rateLimited

  return NextResponse.next({ request })
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|icon.png|apple-icon.png|brand/|api/auth/).*)'],
}

/**
 * session_gate.ts — cryptographic session-cookie verification for the request
 * boundary (`src/proxy.ts`), behind the `SESSION_GATE_MODE` switch.
 *
 * Why this exists (SS N-373, PR-S3; audit `SESSION_GATE_AUDIT.md` §0, §9a):
 * `proxy.ts` historically gated on a base64 parse of the `__session` cookie
 * (exp in the future, `iss` contains `session.firebase.google.com`). That is a
 * SHAPE check; anyone can forge it with no secret. This module adds the real
 * check — firebase-admin `verifySessionCookie(cookie, false)` (RS256 signature
 * against Google's public session-cookie keys + exp + aud + iss) — without
 * touching the shape check's decision unless the owner flips the switch.
 *
 * Modes (`SESSION_GATE_MODE`; unset or unrecognised => `shadow`, NEVER `enforce`):
 *   off     today's behaviour exactly. No verification, no firebase-admin load.
 *   shadow  today's decision stands (nothing is blocked that is not blocked
 *           today). The cookie is ALSO verified; when verification fails while
 *           the shape check passed, a would-reject line is logged and a bounded
 *           counter bumped. Verification infrastructure errors fail OPEN here.
 *   enforce shape check AND cryptographic verification must both pass. An
 *           infrastructure error (firebase-admin init, key fetch, timeout)
 *           FAILS CLOSED (401) and never throws out of the proxy.
 *
 * `checkRevoked` is deliberately `false` here (local signature/claims check, no
 * per-request Firebase round trip). Handlers keep `getServerUser()` ->
 * `verifySessionCookie(cookie, true)` (revocation + disabled-user check).
 *
 * Secrecy: nothing in this module ever logs or stores the cookie, claims, uid,
 * email or a token. Log lines carry only {event, path, reason, mode}; the path
 * is run through `safePathForLog` (dynamic segments redacted, because
 * capability URLs such as `/share/<slug>` are credentials). The verification
 * cache is keyed on sha256(cookie), never the cookie.
 *
 * Bounded state: the result cache is capped (MAX_CACHE_ENTRIES, oldest-first
 * eviction, short TTL); counters are fixed-size (enumerated reason codes); log
 * output is capped per minute. Infra failures are never cached as results; a
 * short circuit breaker stops every request from re-paying a dead JWKS fetch.
 *
 * Process-local: Next documents that proxy state must not be assumed shared
 * with route handlers or other instances. Cache and counters here are
 * per-instance, per-process by design.
 */

import { createHash } from 'node:crypto'

import type { Auth } from 'firebase-admin/auth'

export type SessionGateMode = 'off' | 'shadow' | 'enforce'

/** Coarse, enumerated reason codes. Anything else is folded into `invalid`. */
export type SessionGateReason =
  | 'expired'
  | 'wrong_issuer'
  | 'wrong_audience'
  | 'bad_signature'
  | 'bad_format'
  | 'unknown_kid'
  | 'invalid'
  | 'verify_error'

export const SESSION_GATE_REASONS: readonly SessionGateReason[] = [
  'expired',
  'wrong_issuer',
  'wrong_audience',
  'bad_signature',
  'bad_format',
  'unknown_kid',
  'invalid',
  'verify_error',
]

export type SessionVerifyOutcome =
  | { ok: true; sub: string }
  | { ok: false; reason: SessionGateReason; infra: boolean }

/** Cache lifetime for a definitive verdict (success is also clamped to cookie exp). */
export const SESSION_GATE_CACHE_TTL_MS = 30_000
/** Hard cap on cached verdicts; oldest entries are evicted first. */
export const SESSION_GATE_MAX_CACHE_ENTRIES = 500
/** A verification that has not settled in this long counts as an infra error. */
export const SESSION_GATE_VERIFY_TIMEOUT_MS = 2_000
/** After an infra error, skip verification (fail per mode) for this long. */
export const SESSION_GATE_BREAKER_MS = 5_000
/** Log lines per rolling minute before suppression kicks in. */
export const SESSION_GATE_MAX_LOG_LINES_PER_MIN = 100

export function resolveSessionGateMode(
  env: Record<string, string | undefined> = process.env,
): SessionGateMode {
  const raw = env.SESSION_GATE_MODE?.trim().toLowerCase()
  if (raw === 'off' || raw === 'shadow' || raw === 'enforce') return raw
  return 'shadow'
}

// ── firebase-admin (Node-only; lazily loaded so mode=off pays nothing) ────────

let _auth: Auth | null = null

async function getAdminAuth(): Promise<Auth> {
  if (_auth) return _auth
  const { initializeApp, getApps, cert } = await import('firebase-admin/app')
  const { getAuth } = await import('firebase-admin/auth')

  let serviceAccount: object = {}
  try {
    serviceAccount = JSON.parse(process.env.FIREBASE_ADMIN_CREDENTIALS ?? '{}')
  } catch {
    // credentials not configured; cert({}) below throws and is reported as verify_error
  }

  // Same default-app pattern as lib/firebase/server.ts: reuse the app if one exists.
  const app = getApps().length > 0 ? getApps()[0] : initializeApp({ credential: cert(serviceAccount) })
  _auth = getAuth(app)
  return _auth
}

// ── error classification ──────────────────────────────────────────────────────

interface ErrorLike {
  code?: unknown
  message?: unknown
}

/**
 * Splits "the cookie is bad" (a cryptographic/claims rejection) from "we could
 * not verify" (infrastructure). The distinction decides fail-open vs fail-closed
 * logging and whether the circuit breaker trips, so the infra test must NOT be
 * satisfiable by attacker-controlled text: the verifier embeds token claims only
 * AFTER ` but got "`, which is cut off before any message matching.
 */
export function classifyVerifyError(err: unknown): { reason: SessionGateReason; infra: boolean } {
  const e = (typeof err === 'object' && err !== null ? err : {}) as ErrorLike
  const code = typeof e.code === 'string' ? e.code : ''
  const fullMessage = typeof e.message === 'string' ? e.message : ''
  const head = fullMessage.split(' but got "')[0]

  if (code === 'auth/session-cookie-expired') return { reason: 'expired', infra: false }

  // Infrastructure: not a firebase auth error at all (app/invalid-credential from
  // cert(), network errors), SDK internal error, missing project id/credential,
  // or the public-key fetch failing (surfaced by the SDK as an argument error
  // whose message STARTS with the fetch prefix).
  if (
    !code.startsWith('auth/') ||
    code === 'auth/internal-error' ||
    code === 'auth/invalid-credential' ||
    head.startsWith('Error fetching public keys')
  ) {
    return { reason: 'verify_error', infra: true }
  }

  if (head.includes('incorrect "iss"')) return { reason: 'wrong_issuer', infra: false }
  if (head.includes('incorrect "aud"')) return { reason: 'wrong_audience', infra: false }
  if (head.includes('invalid signature')) return { reason: 'bad_signature', infra: false }
  if (head.includes('does not correspond to a known public key')) {
    return { reason: 'unknown_kid', infra: false }
  }
  if (
    head.includes('Decoding') ||
    head.includes('no "kid"') ||
    head.includes('incorrect algorithm') ||
    head.includes('"sub"') ||
    head.includes('must be a')
  ) {
    return { reason: 'bad_format', infra: false }
  }
  return { reason: 'invalid', infra: false }
}

// ── bounded verdict cache, keyed by sha256(cookie) ────────────────────────────

interface CacheEntry {
  outcome: SessionVerifyOutcome
  expiresAt: number
}

const cache = new Map<string, CacheEntry>()
let breakerUntil = 0

function fingerprint(cookie: string): string {
  return createHash('sha256').update(cookie).digest('hex')
}

function cacheGet(key: string, now: number): SessionVerifyOutcome | null {
  const hit = cache.get(key)
  if (!hit) return null
  if (hit.expiresAt <= now) {
    cache.delete(key)
    return null
  }
  return hit.outcome
}

function cacheSet(key: string, outcome: SessionVerifyOutcome, expiresAt: number, now: number): void {
  if (cache.has(key)) cache.delete(key)
  if (cache.size >= SESSION_GATE_MAX_CACHE_ENTRIES) {
    // Drop already-expired entries first, then oldest-inserted until under the cap.
    for (const [k, v] of cache) if (v.expiresAt <= now) cache.delete(k)
    while (cache.size >= SESSION_GATE_MAX_CACHE_ENTRIES) {
      const oldest = cache.keys().next().value
      if (oldest === undefined) break
      cache.delete(oldest)
    }
  }
  cache.set(key, { outcome, expiresAt })
}

// ── stats / structured logging ────────────────────────────────────────────────

interface Stats {
  verified_ok: number
  would_reject_total: number
  would_reject_by_reason: Record<SessionGateReason, number>
}

function emptyStats(): Stats {
  const by = {} as Record<SessionGateReason, number>
  for (const r of SESSION_GATE_REASONS) by[r] = 0
  return { verified_ok: 0, would_reject_total: 0, would_reject_by_reason: by }
}

let stats: Stats = emptyStats()
let logWindowStart = 0
let logLinesInWindow = 0
let logSuppressed = 0

/** Read-only snapshot (counters + cache size) for diagnostics and tests. */
export function getSessionGateStats(): Stats & { cache_size: number } {
  return {
    verified_ok: stats.verified_ok,
    would_reject_total: stats.would_reject_total,
    would_reject_by_reason: { ...stats.would_reject_by_reason },
    cache_size: cache.size,
  }
}

/** Test hook: clears cache, breaker, counters and the cached admin Auth. */
export function __resetSessionGateForTest(): void {
  cache.clear()
  breakerUntil = 0
  stats = emptyStats()
  logWindowStart = 0
  logLinesInWindow = 0
  logSuppressed = 0
  xffSeen.clear()
  xffWindowStart = 0
  xffLinesInWindow = 0
  _auth = null
}

/**
 * Path for log lines. Capability URLs (`/share/<slug>`) and ids are credentials
 * or PII-adjacent, so keep only plain lowercase route-name segments (max 4);
 * anything containing a digit, an uppercase letter, or longer than 32 chars is
 * replaced with `:id`. Query strings never reach here (pathname only).
 */
export function safePathForLog(pathname: string): string {
  const segments = pathname.split('/').filter(Boolean).slice(0, 4)
  const safe = segments.map((s) => (/^[a-z][a-z._-]{0,31}$/.test(s) ? s : ':id'))
  if (safe[0] === 'share') return '/share/:slug'
  return '/' + safe.join('/')
}

function emit(line: Record<string, unknown>): void {
  console.warn(JSON.stringify(line))
}

function logWithCap(line: Record<string, unknown>, mode: SessionGateMode, now: number): void {
  if (now - logWindowStart >= 60_000) {
    if (logSuppressed > 0) {
      emit({ event: 'session_gate_log_suppressed', suppressed: logSuppressed, mode })
    }
    logWindowStart = now
    logLinesInWindow = 0
    logSuppressed = 0
  }
  if (logLinesInWindow >= SESSION_GATE_MAX_LOG_LINES_PER_MIN) {
    logSuppressed += 1
    return
  }
  logLinesInWindow += 1
  emit(line)
}

/** Records a shadow-mode would-reject: bumps the bounded counter and logs one line. */
export function recordWouldReject(pathname: string, reason: SessionGateReason): void {
  stats.would_reject_total += 1
  stats.would_reject_by_reason[reason] += 1
  logWithCap(
    { event: 'session_gate_would_reject', path: safePathForLog(pathname), reason, mode: 'shadow' },
    'shadow',
    Date.now(),
  )
}

// ── verification ──────────────────────────────────────────────────────────────

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('session_gate_verify_timeout')), ms)
    if (typeof timer === 'object' && timer !== null && 'unref' in timer) timer.unref()
    promise.then(
      (v) => {
        clearTimeout(timer)
        resolve(v)
      },
      (e) => {
        clearTimeout(timer)
        reject(e)
      },
    )
  })
}

/**
 * Verifies a session cookie (signature + claims, `checkRevoked=false`). Never
 * throws. Definitive verdicts (accept or reject) are cached for a short TTL
 * under sha256(cookie); infrastructure failures are not cached, they trip a
 * short breaker instead.
 */
export async function verifySessionForGate(cookie: string): Promise<SessionVerifyOutcome> {
  const now = Date.now()
  const key = fingerprint(cookie)

  const cached = cacheGet(key, now)
  if (cached) return cached

  if (breakerUntil > now) return { ok: false, reason: 'verify_error', infra: true }

  try {
    const auth = await getAdminAuth()
    const decoded = await withTimeout(auth.verifySessionCookie(cookie, false), SESSION_GATE_VERIFY_TIMEOUT_MS)
    const sub = typeof decoded?.sub === 'string' && decoded.sub.length > 0 ? decoded.sub : null
    if (!sub) {
      // A verifier that returns no subject is not a verdict we can trust.
      return { ok: false, reason: 'verify_error', infra: true }
    }
    const outcome: SessionVerifyOutcome = { ok: true, sub }
    const expMs = typeof decoded.exp === 'number' ? decoded.exp * 1000 : now + SESSION_GATE_CACHE_TTL_MS
    cacheSet(key, outcome, Math.min(now + SESSION_GATE_CACHE_TTL_MS, expMs), now)
    stats.verified_ok += 1
    return outcome
  } catch (err) {
    const { reason, infra } = classifyVerifyError(err)
    if (infra) {
      breakerUntil = Date.now() + SESSION_GATE_BREAKER_MS
      return { ok: false, reason, infra }
    }
    const outcome: SessionVerifyOutcome = { ok: false, reason, infra: false }
    cacheSet(key, outcome, now + SESSION_GATE_CACHE_TTL_MS, now)
    return outcome
  }
}

// ── the decision the proxy applies ────────────────────────────────────────────

export interface SessionGateDecision {
  /** true => the proxy must refuse (only ever true in `enforce`). */
  deny: boolean
  /** Why it was refused; `verify_error` marks an infrastructure fail-closed. */
  denyReason?: SessionGateReason
  /** Verified Firebase uid when cryptographic verification succeeded. */
  verifiedSub?: string
}

/**
 * Applies the mode to a cookie that has ALREADY passed the shape check. Never
 * throws. `off` does no work. `shadow` never denies (it logs + counts a
 * would-reject). `enforce` denies on any verification failure, infra included.
 */
export async function evaluateSessionGate(
  mode: SessionGateMode,
  cookie: string,
  pathname: string,
): Promise<SessionGateDecision> {
  if (mode === 'off') return { deny: false }

  let outcome: SessionVerifyOutcome
  try {
    outcome = await verifySessionForGate(cookie)
  } catch {
    // verifySessionForGate does not throw; this is the belt to its braces.
    outcome = { ok: false, reason: 'verify_error', infra: true }
  }

  if (outcome.ok) return { deny: false, verifiedSub: outcome.sub }

  if (mode === 'enforce') {
    logWithCap(
      { event: 'session_gate_rejected', path: safePathForLog(pathname), reason: outcome.reason, mode: 'enforce' },
      'enforce',
      Date.now(),
    )
    return { deny: true, denyReason: outcome.reason }
  }

  recordWouldReject(pathname, outcome.reason)
  return { deny: false }
}

// ── X-Forwarded-For entry-count observation (SS N-375) ────────────────────────
//
// Purpose: after a day of real traffic, decide MARSYS_TRUSTED_PROXY_HOPS from
// data. We log ONLY the number of entries in X-Forwarded-For, tagged with a
// three-way host class. Never an address, never the raw header, never the host
// value beyond the class. Bounded: one line per (host_class, count, path) per
// minute, a cap on distinct keys, and a total lines-per-minute cap.

export type HostClass = 'public' | 'run_app' | 'other'

/** Counts above this are folded into it (bounds cardinality; real chains are short). */
export const XFF_COUNT_CAP = 20
export const XFF_MAX_KEYS = 200
export const XFF_MAX_LINES_PER_MIN = 120
const XFF_WINDOW_MS = 60_000

/**
 * Host class from the Host header. `run_app` = a *.run.app host; `public` = a
 * host listed in SESSION_GATE_PUBLIC_HOSTS (comma-separated hostnames) or, when
 * that is unset, any other real DNS name (not localhost, not an IP literal);
 * everything else (localhost, IPs, empty) = `other`. The value itself is never
 * returned or logged.
 */
export function classifyHost(
  hostHeader: string | null | undefined,
  env: Record<string, string | undefined> = process.env,
): HostClass {
  const host = (hostHeader ?? '').trim().toLowerCase().replace(/:\d+$/, '')
  if (!host) return 'other'
  if (host === 'run.app' || host.endsWith('.run.app')) return 'run_app'
  const configured = (env.SESSION_GATE_PUBLIC_HOSTS ?? '')
    .split(',')
    .map((h) => h.trim().toLowerCase())
    .filter(Boolean)
  if (configured.length > 0) return configured.includes(host) ? 'public' : 'other'
  if (host === 'localhost' || /^[\d.]+$/.test(host) || host.includes(':') || !host.includes('.')) return 'other'
  return 'public'
}

/** Number of non-empty comma-separated entries (0 when absent). Never inspects their content. */
export function countForwardedForEntries(xff: string | null | undefined): number {
  if (!xff) return 0
  let n = 0
  for (const part of xff.split(',')) if (part.trim() !== '') n++
  return Math.min(n, XFF_COUNT_CAP)
}

const xffSeen = new Map<string, number>() // key -> window start
let xffWindowStart = 0
let xffLinesInWindow = 0

/**
 * Logs `{event:'xff_entry_count', host_class, count, path, mode}` at most once
 * per (host_class, count, path) per minute. `off` does nothing. Never throws.
 */
export function observeForwardedForEntryCount(
  mode: SessionGateMode,
  pathname: string,
  hostHeader: string | null | undefined,
  xff: string | null | undefined,
  now: number = Date.now(),
): void {
  if (mode === 'off') return
  try {
    if (now - xffWindowStart >= XFF_WINDOW_MS) {
      xffWindowStart = now
      xffLinesInWindow = 0
      xffSeen.clear()
    }
    const host_class = classifyHost(hostHeader)
    const count = countForwardedForEntries(xff)
    const path = safePathForLog(pathname)
    const key = `${host_class}|${count}|${path}`
    if (xffSeen.has(key)) return
    if (xffSeen.size >= XFF_MAX_KEYS || xffLinesInWindow >= XFF_MAX_LINES_PER_MIN) return
    xffSeen.set(key, now)
    xffLinesInWindow += 1
    console.info(JSON.stringify({ event: 'xff_entry_count', host_class, count, path, mode }))
  } catch {
    // observability must never affect a request
  }
}

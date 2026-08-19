/**
 * Canonical API error envelope and factory helpers for every route in `app/api/`.
 *
 * Spec: `00_NAK/NAK_ERROR_FRAMEWORK_v1_0.md` §2 (envelope), §3 (failure modes), §5 (HTTP mapping).
 * Adopted by all 30 API routes at NAK W2-R2 close (2026-04-30).
 *
 * Usage:
 *   import { res, dataError } from '@/lib/errors'
 *   if (!body.chartId) return res.badRequest('chartId required')
 *   if (!user)         return res.unauthenticated()
 */
import { NextResponse } from 'next/server'

/**
 * Canonical error envelope returned by every non-2xx API response.
 *
 * Clients read `body.error.message` for display and `body.error.code` for
 * branching/i18n. `detail` carries optional structured context (e.g. the
 * specific field that failed validation). `retry` signals whether the same
 * request, repeated unchanged, can succeed (true for transient failures).
 */
export interface ApiErrorBody {
  error: {
    /** Machine-readable code, e.g. `AUTH_FORBIDDEN`, `DATA_INVALID_INPUT`. */
    code: string
    /** User-facing, layman-readable message. Never a stack trace. */
    message: string
    /** Optional human-readable context (the offending field, the missing value). */
    detail?: string
    /** True if the same request, repeated, can succeed; false if the caller must change the input or auth state. */
    retry?: boolean
  }
}

/**
 * Build an `ApiErrorBody` literal. Pure — no `NextResponse` wrapping.
 *
 * Use this when you need the body shape outside a route handler (e.g. inside
 * a streamed `onError` callback). For route handlers, prefer the `res.*`
 * helpers below — they wrap the body in a `NextResponse` with the correct
 * HTTP status.
 */
export function apiError(
  code: string,
  message: string,
  options?: { detail?: string; retry?: boolean },
): ApiErrorBody {
  return { error: { code, message, ...options } }
}

/**
 * Generic HTTP-status mapper. Prefer the named `res.*` helpers; reach for
 * this only when no helper covers the status you need.
 */
export function errorResponse(
  code: string,
  message: string,
  status: number,
  options?: { detail?: string; retry?: boolean },
): NextResponse<ApiErrorBody> {
  return NextResponse.json(apiError(code, message, options), { status })
}

// ── NETWORK ──────────────────────────────────────────────────────────────────

/** Network-class failures: timeouts, unreachable upstreams. Always `retry: true`. */
export const networkError = {
  timeout: (detail?: string) =>
    apiError('NETWORK_TIMEOUT', 'Request timed out.', { retry: true, detail }),
  unreachable: (detail?: string) =>
    apiError('NETWORK_UNREACHABLE', 'Service unreachable.', { retry: true, detail }),
}

// ── AUTH ─────────────────────────────────────────────────────────────────────

/** Auth-class failures: never retryable — the caller must change auth state. */
export const authError = {
  unauthenticated: () =>
    apiError('AUTH_UNAUTHENTICATED', 'Authentication required.', { retry: false }),
  forbidden: () =>
    apiError('AUTH_FORBIDDEN', 'You do not have permission to perform this action.', { retry: false }),
  sessionExpired: () =>
    apiError('AUTH_SESSION_EXPIRED', 'Session has expired. Please sign in again.', { retry: false }),
}

// ── DATA ─────────────────────────────────────────────────────────────────────

/** Data-class failures: missing fields, validation, 404s, conflicts. Not retryable as-is. */
export const dataError = {
  invalidInput: (detail?: string) =>
    apiError('DATA_INVALID_INPUT', 'Invalid or missing input.', { retry: false, detail }),
  notFound: (detail?: string) =>
    apiError('DATA_NOT_FOUND', 'The requested resource was not found.', { retry: false, detail }),
  validationFailed: (detail?: string) =>
    apiError('DATA_VALIDATION_FAILED', 'Request validation failed.', { retry: false, detail }),
  corpusEmpty: () =>
    apiError('DATA_CORPUS_EMPTY', 'No corpus content available.', { retry: false }),
  constraintViolation: (detail?: string) =>
    apiError('DATA_CONSTRAINT_VIOLATION', 'A data constraint was violated.', { retry: false, detail }),
  conflict: (detail?: string) =>
    apiError('DATA_CONFLICT', 'Resource already exists or state conflict.', { retry: false, detail }),
}

// ── LIMIT ─────────────────────────────────────────────────────────────────────

/**
 * Limit-class refusals: rate limits and spend ceilings (NCD-8, Paripraśna G1-D).
 *
 * These are DESIGNED failure states, not errors. The request was well-formed, the
 * caller was authenticated and entitled, and the server is healthy — the turn is
 * simply not permitted to run right now. That is why they carry their own class
 * with `retry: true` and map to 429, never to a 500: a client must be able to
 * branch on `LIMIT_*` and say something true to the reader ("your daily ceiling
 * is reached, it resets at midnight UTC") instead of "something went wrong".
 */
export const limitError = {
  rateLimitExceeded: (detail?: string) =>
    apiError('LIMIT_RATE_LIMIT_EXCEEDED', 'Too many requests. Please slow down.', {
      retry: true,
      detail,
    }),
  spendCeilingExceeded: (detail?: string) =>
    apiError('LIMIT_SPEND_CEILING_EXCEEDED', 'Spend ceiling reached.', {
      retry: true,
      detail,
    }),
}

// ── SYSTEM ────────────────────────────────────────────────────────────────────

/** System-class failures: server-side problems. Most are transient (`retry: true`). */
export const systemError = {
  internal: (detail?: string) =>
    apiError('SYSTEM_INTERNAL', 'An unexpected server error occurred.', { retry: false, detail }),
  dbUnavailable: () =>
    apiError('SYSTEM_DB_UNAVAILABLE', 'Database is temporarily unavailable.', { retry: true }),
  sidecarUnavailable: () =>
    apiError('SYSTEM_SIDECAR_UNAVAILABLE', 'Analysis service is temporarily unavailable.', { retry: true }),
  llmError: () =>
    apiError('SYSTEM_LLM_ERROR', 'The AI model returned an error.', { retry: true }),
  timeout: () =>
    apiError('SYSTEM_TIMEOUT', 'The request timed out on the server.', { retry: true }),
}

// ── HTTP status shorthand ─────────────────────────────────────────────────────

/**
 * Route-handler shorthand: each helper returns a `NextResponse<ApiErrorBody>`
 * with the conventional HTTP status. Use these as the standard return value
 * in every API route. The HTTP status and the `error.code` are kept in sync
 * by construction (no surface should ever return e.g. a 400 with an `AUTH_*`
 * code or a 500 with a `DATA_*` code).
 *
 * Status mapping:
 *   400 → invalidInput      401 → unauthenticated     403 → forbidden
 *   404 → notFound          409 → conflict            422 → validationFailed
 *   429 → rateLimited | spendCeilingExceeded
 *   500 → internal          503 → dbError | sidecarDown
 */
export const res = {
  badRequest: (detail?: string) =>
    NextResponse.json(dataError.invalidInput(detail), { status: 400 }),
  unauthenticated: () =>
    NextResponse.json(authError.unauthenticated(), { status: 401 }),
  forbidden: () =>
    NextResponse.json(authError.forbidden(), { status: 403 }),
  notFound: (detail?: string) =>
    NextResponse.json(dataError.notFound(detail), { status: 404 }),
  conflict: (detail?: string) =>
    NextResponse.json(dataError.conflict(detail), { status: 409 }),
  validationFailed: (detail?: string) =>
    NextResponse.json(dataError.validationFailed(detail), { status: 422 }),
  /**
   * 429 — per-user rate limit. `retryAfterSeconds`, when known, is echoed as the
   * standard `Retry-After` header so a client can back off correctly instead of
   * guessing.
   */
  rateLimited: (detail?: string, retryAfterSeconds?: number) =>
    NextResponse.json(limitError.rateLimitExceeded(detail), {
      status: 429,
      headers: retryAfterSeconds ? { 'retry-after': String(retryAfterSeconds) } : undefined,
    }),
  /** 429 — NCD-8 spend ceiling ($2/turn, $40/day). A designed refusal, never a 500. */
  spendCeilingExceeded: (detail?: string) =>
    NextResponse.json(limitError.spendCeilingExceeded(detail), { status: 429 }),
  internal: (detail?: string) =>
    NextResponse.json(systemError.internal(detail), { status: 500 }),
  dbError: () =>
    NextResponse.json(systemError.dbUnavailable(), { status: 503 }),
  sidecarDown: () =>
    NextResponse.json(systemError.sidecarUnavailable(), { status: 503 }),
}

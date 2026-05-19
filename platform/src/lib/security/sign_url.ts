/**
 * sign_url.ts — HMAC-SHA256 URL signing for iCal feed tokens.
 *
 * Design per D3 settled 2026-05-19:
 *   - Signed time-boxed tokens (HMAC-SHA256)
 *   - 90-day expiry
 *   - No chart_id or user PII in token payload — only location + optional
 *     personalise hash (SHA-256 of chart_id, never raw chart_id)
 *
 * Token format: base64url(payload_json) + "." + hex(HMAC-SHA256)
 *
 * The HMAC secret is read from SESSION_SECRET or HMAC_SECRET env var.
 * Per-user revocation is implemented via a revocation list stored in the
 * database (panchang_feed_revocations table); see verifyFeedToken for details.
 *
 * Phase: 4C-7 (Item 3)
 */

import { createHmac } from 'crypto'

// ── Secret resolution ─────────────────────────────────────────────────────────

function getSecret(): string {
  const secret = process.env.SESSION_SECRET ?? process.env.HMAC_SECRET ?? ''
  if (!secret) {
    throw new Error(
      '[sign_url] SESSION_SECRET or HMAC_SECRET must be set in environment. ' +
      'Add SESSION_SECRET=<random-32+-char-string> to your .env.local',
    )
  }
  return secret
}

// ── Token payload type ────────────────────────────────────────────────────────

export interface FeedTokenPayload {
  /**
   * Random token identifier (UUID-like) — used as the DB key for revocation.
   * Contains NO user PII. User association is stored only in the DB row.
   */
  jti: string
  /** Human-readable location slug, e.g. "bhubaneswar" */
  location: string
  /**
   * SHA-256 hash of chart_id (first 16 hex chars) — enables personalised feed
   * without exposing chart_id. Omit for generic (non-personalised) feeds.
   */
  personalise?: string
  /** Unix timestamp (seconds) — when this token expires (90 days from issue) */
  expires_at: number
  /** Unix timestamp (seconds) — when this token was issued */
  issued_at: number
}

// ── 90-day expiry helper ──────────────────────────────────────────────────────

export const FEED_TOKEN_TTL_SECONDS = 90 * 24 * 60 * 60 // 90 days

export function makeFeedTokenExpiry(): number {
  return Math.floor(Date.now() / 1000) + FEED_TOKEN_TTL_SECONDS
}

// ── Sign ──────────────────────────────────────────────────────────────────────

/**
 * Sign a feed token payload, returning a URL-safe token string.
 *
 * Token format: `<base64url(json)>.<hex(hmac)>`
 *
 * @param params  FeedTokenPayload
 * @returns       Signed token string (URL-safe, no padding issues)
 */
export function signFeedToken(params: FeedTokenPayload): string {
  const secret = getSecret()
  const payload = JSON.stringify(params)
  const encoded = Buffer.from(payload, 'utf8').toString('base64url')
  const sig = createHmac('sha256', secret).update(encoded).digest('hex')
  return `${encoded}.${sig}`
}

// ── Verify ────────────────────────────────────────────────────────────────────

export type VerifyResult =
  | { ok: true; payload: FeedTokenPayload }
  | { ok: false; reason: 'invalid' | 'expired' | 'tampered' }

/**
 * Verify a signed feed token.
 *
 * Returns the decoded payload on success, or a typed failure reason:
 *   - 'tampered' — HMAC signature mismatch
 *   - 'expired'  — token past its expires_at timestamp
 *   - 'invalid'  — malformed token (bad format, bad JSON, missing fields)
 *
 * Note: revocation (per user) is checked separately by the feed route
 * using `isTokenRevoked` from db_revocations.ts.
 *
 * @param token  Raw token from ?token= query param
 */
export function verifyFeedToken(token: string): VerifyResult {
  try {
    const dotIndex = token.lastIndexOf('.')
    if (dotIndex === -1) return { ok: false, reason: 'invalid' }

    const encoded = token.slice(0, dotIndex)
    const sig = token.slice(dotIndex + 1)
    if (!encoded || !sig) return { ok: false, reason: 'invalid' }

    // Verify HMAC
    const secret = getSecret()
    const expected = createHmac('sha256', secret).update(encoded).digest('hex')
    if (sig !== expected) return { ok: false, reason: 'tampered' }

    // Decode payload
    const payloadStr = Buffer.from(encoded, 'base64url').toString('utf8')
    const payload = JSON.parse(payloadStr) as FeedTokenPayload

    // Validate required fields (no user PII in payload)
    if (!payload.jti || !payload.location || typeof payload.expires_at !== 'number') {
      return { ok: false, reason: 'invalid' }
    }

    // Check expiry
    if (payload.expires_at < Math.floor(Date.now() / 1000)) {
      return { ok: false, reason: 'expired' }
    }

    return { ok: true, payload }
  } catch {
    return { ok: false, reason: 'invalid' }
  }
}

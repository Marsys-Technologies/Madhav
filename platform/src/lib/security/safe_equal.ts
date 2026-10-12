/**
 * safe_equal.ts — the ONE timing-safe secret comparison for shared secrets and
 * HMAC signatures (SS N-373 / PR-S1, item 5).
 *
 * WHY: a plain `provided !== expected` short-circuits at the first differing
 * byte, which is an observable timing signal on a raw shared secret
 * (MARSYS_CRON_SECRET, the feed-token HMAC). `crypto.timingSafeEqual` is the
 * right primitive but THROWS on different-length buffers, and a length check in
 * front of it leaks the secret's length. So both sides are hashed with SHA-256
 * first: the buffers are always 32 bytes, nothing can throw, and the length of
 * either input cannot be read from the comparison time.
 *
 * FAIL CLOSED: an unset / empty secret never matches, whatever is provided.
 * (`undefined === undefined` and `'' === ''` are the two classic ways an unset
 * environment variable turns into an open door; this helper refuses both.)
 * A missing credential (absent header) is likewise never equal to anything.
 *
 * Same hash-then-compare construction as `lib/mcp/constant_time.ts`
 * (`constantTimeEquals`, SF-005), with the fail-closed guard in front.
 */
import { createHash, timingSafeEqual } from 'crypto'

function digest(value: string): Buffer {
  return createHash('sha256').update(value, 'utf8').digest()
}

/**
 * @param provided what the caller presented (header value, signature, ...)
 * @param expected the secret / recomputed signature it must equal
 * @returns true only when both are non-empty strings with identical content
 */
export function safeEqual(
  provided: string | null | undefined,
  expected: string | null | undefined,
): boolean {
  if (typeof provided !== 'string' || typeof expected !== 'string') return false
  if (provided.length === 0 || expected.length === 0) return false
  return timingSafeEqual(digest(provided), digest(expected))
}

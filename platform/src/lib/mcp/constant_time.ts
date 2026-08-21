/**
 * constant_time.ts — shared timing-safe string comparison (SF-005).
 *
 * `crypto.timingSafeEqual` requires equal-length buffers and throws
 * otherwise, so a raw string comparison can neither use it directly (the
 * inputs are attacker-influenced length) nor fall back to `===` (which
 * short-circuits at the first differing byte, an observable timing leak on
 * a raw shared secret).
 *
 * Fix: SHA-256 both sides first. This fixes the comparison length at 32
 * bytes — `timingSafeEqual` can never throw, and the *length* of the
 * original secret cannot leak either (a bare length-check-then-
 * timingSafeEqual guard would still leak length). The comparison of the
 * hashes is then genuinely constant-time in the size of the inputs.
 *
 * This is the one small helper SF-005 authorizes. It intentionally does
 * NOT replace `auth.ts::verifyKeyTail` — that function's length
 * equalization comes from PBKDF2's fixed-size output, not from hashing the
 * comparands, and its semantics (salt parsing, PBKDF2 re-derivation) are
 * unrelated to a raw shared-secret comparison. Do not build this out into
 * a larger crypto-util layer.
 */

import { createHash, timingSafeEqual } from 'crypto'

/**
 * Constant-time equality check for two secret strings.
 * Hashes both inputs (SHA-256) before comparing, so the comparison never
 * throws on mismatched lengths and never leaks the raw secret's length.
 */
export function constantTimeEquals(a: string, b: string): boolean {
  const ha = createHash('sha256').update(a, 'utf8').digest()
  const hb = createHash('sha256').update(b, 'utf8').digest()
  return timingSafeEqual(ha, hb)
}

/**
 * auth.ts — MCP API key validation.
 *
 * Every /api/mcp/* endpoint calls validateMcpKey(authHeader) before doing work.
 * Returns a resolved principal on success, null on any failure.
 * Never throws — the caller decides how to respond.
 *
 * Key format: mcp_<env>_<random40>
 *   - key_id = "mcp_<env>_" + first 8 chars of random40  (DB lookup handle)
 *   - tail   = remaining 32 chars (hashed and stored as key_hash)
 *
 * Hashing: PBKDF2-SHA256, 100 000 iterations, 32-byte output, stored as
 * "<salt_hex>:<hash_hex>". No external dependency — uses Node.js built-in
 * crypto. Timing-safe comparison via crypto.timingSafeEqual.
 *
 * Why this split: allows O(1) DB lookup by key_id without exposing the secret.
 */

import 'server-only'
import { query } from '@/lib/db/client'
import type { McpPrincipal } from '@/lib/mcp/types'
import { createHash, randomBytes, pbkdf2Sync, timingSafeEqual } from 'crypto'

const PBKDF2_ITERATIONS = 100_000
const PBKDF2_KEYLEN = 32
const PBKDF2_DIGEST = 'sha256'
const SALT_BYTES = 16

/**
 * Hash a key tail using PBKDF2-SHA256.
 * Returns "<salt_hex>:<hash_hex>" for storage.
 */
export function hashKeyTail(tail: string): string {
  const salt = randomBytes(SALT_BYTES)
  const hash = pbkdf2Sync(tail, salt, PBKDF2_ITERATIONS, PBKDF2_KEYLEN, PBKDF2_DIGEST)
  return `${salt.toString('hex')}:${hash.toString('hex')}`
}

/**
 * Timing-safe comparison of a tail string against a stored hash.
 * Returns true only when the tail matches.
 */
export function verifyKeyTail(tail: string, storedHash: string): boolean {
  const parts = storedHash.split(':')
  if (parts.length !== 2) return false
  const [saltHex, expectedHex] = parts
  try {
    const salt = Buffer.from(saltHex, 'hex')
    const expected = Buffer.from(expectedHex, 'hex')
    const actual = pbkdf2Sync(tail, salt, PBKDF2_ITERATIONS, PBKDF2_KEYLEN, PBKDF2_DIGEST)
    return timingSafeEqual(actual, expected)
  } catch {
    return false
  }
}

/**
 * Extract key_id and tail from a full MCP bearer token.
 *
 * Key format: mcp_<env>_<40 alphanumeric chars>
 * key_id     = mcp_<env>_<first8>
 * tail       = remaining 32 chars
 */
function splitKey(fullKey: string): { key_id: string; tail: string } | null {
  // Allow any lowercase env label (prod, dev, test, staging, etc.)
  const match = fullKey.match(/^(mcp_[a-z]+_[A-Za-z0-9]{8})([A-Za-z0-9]{32})$/)
  if (!match) return null
  return { key_id: match[1], tail: match[2] }
}

/**
 * Validate a Bearer token from the Authorization header.
 *
 * @returns McpPrincipal on success, null on any auth failure.
 */
export async function validateMcpKey(authHeader: string | null | undefined): Promise<McpPrincipal | null> {
  if (!authHeader) return null

  const parts = authHeader.split(' ')
  if (parts.length !== 2 || parts[0].toLowerCase() !== 'bearer') return null

  const fullKey = parts[1]
  if (!fullKey) return null

  const split = splitKey(fullKey)
  if (!split) return null

  const { key_id, tail } = split

  try {
    const { rows } = await query<{
      key_id: string
      key_hash: string
      user_uid: string
    }>(
      // audience_tier column dropped (Stream A 3.tier_excision migration 090 2026-05-28).
      `SELECT key_id, key_hash, user_uid
       FROM mcp_api_keys
       WHERE key_id = $1 AND revoked_at IS NULL
       LIMIT 1`,
      [key_id]
    )

    const row = rows[0]
    if (!row) {
      // Run a dummy compare to prevent timing-based key_id enumeration.
      createHash('sha256').update(tail).digest()
      return null
    }

    const valid = verifyKeyTail(tail, row.key_hash)
    if (!valid) return null

    // Update last_used_at — fire-and-forget (non-fatal on failure).
    void query(
      `UPDATE mcp_api_keys SET last_used_at = now() WHERE key_id = $1`,
      [key_id]
    ).catch((err: unknown) => {
      console.error('[mcp:auth] last_used_at update failed', err)
    })

    const role = await resolveMcpPrincipalRole(row.user_uid)

    return {
      user_uid: row.user_uid,
      // audience_tier removed (Stream A 3.tier_excision 2026-05-28).
      key_id: row.key_id,
      role,
    }
  } catch (err) {
    console.error('[mcp:auth] validateMcpKey DB error', err)
    return null
  }
}

/**
 * Resolve the Firebase role for a given user UID.
 * Reads from the profiles table; defaults to 'guest' if no row found.
 * Used by both the Bearer-key path and the OAuth path.
 */
export async function resolveMcpPrincipalRole(
  userUid: string
): Promise<'guest' | 'super_admin'> {
  try {
    const { rows } = await query<{ role: string }>(
      `SELECT role FROM profiles WHERE id = $1 LIMIT 1`,
      [userUid]
    )
    const r = rows[0]?.role
    return r === 'super_admin' ? 'super_admin' : 'guest'
  } catch {
    return 'guest'
  }
}

/**
 * Generate a new MCP API key.
 *
 * Returns:
 *   - full_key: the bearer token shown once to the user (mcp_<env>_<40chars>)
 *   - key_id:   the lookup prefix stored in the DB (mcp_<env>_<first8>)
 *   - key_hash: PBKDF2 hash of the tail, stored in the DB
 */
export async function generateMcpKey(env: 'prod' | 'dev' | 'test' = 'prod'): Promise<{
  key_id: string
  full_key: string
  key_hash: string
}> {
  // 40 cryptographically random alphanumeric characters.
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  const randomPart = Array.from(
    randomBytes(40),
    (byte) => chars[byte % chars.length]
  ).join('')

  const prefix = randomPart.slice(0, 8)   // stored in DB as part of key_id
  const tail = randomPart.slice(8)         // 32 chars — hashed and stored

  const key_id = `mcp_${env}_${prefix}`
  const full_key = `mcp_${env}_${randomPart}`
  const key_hash = hashKeyTail(tail)

  return { key_id, full_key, key_hash }
}

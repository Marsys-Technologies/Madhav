/**
 * auth.ts — Bearer key validation for the platform-mcp MCP server.
 *
 * Validates incoming Bearer tokens from MCP clients (Claude Chat, Cowork)
 * by calling back to the platform's /api/mcp/keys/validate endpoint.
 *
 * Architecture decision (MCP_BRIEF §5.1, Item 8): call-through to platform
 * is the correct approach — the MCP server has no direct DB connection.
 * Validation is delegated to the platform, which uses the same PBKDF2-SHA256
 * verification and timing-safe comparison that MCP-1-S1 implemented.
 *
 * F.5 fix (MCPT v3.1.0-S1): 60-second in-memory cache keyed by SHA-256 of the
 * Bearer token. Cache lookup before the platform roundtrip; cache write after a
 * successful validation. On revocation, the next cache miss (≤60s) picks up
 * the revocation — acceptable grace per MCP_DIAGNOSIS §6.1.
 *
 * Returns: Principal on success, null on any auth failure.
 * Never throws — callers receive null on error.
 */

import { createHash } from 'crypto'
import type { Principal, KeyValidateResponse } from './types.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// F.5: 60-second TTL in-memory validation cache.
// Key = SHA-256 hex of the raw Authorization header (never the token itself).
const CACHE_TTL_MS = 60_000
interface CacheEntry {
  principal: Principal
  expiresAt: number
}
const validationCache = new Map<string, CacheEntry>()

/**
 * Compute a stable cache key from the raw Authorization header.
 * Using SHA-256 means we never store the raw token in memory.
 */
function cacheKey(authHeader: string): string {
  return createHash('sha256').update(authHeader).digest('hex')
}

/**
 * Evict expired cache entries (called lazily on each lookup to bound memory use).
 */
function evictExpired(): void {
  const now = Date.now()
  for (const [key, entry] of validationCache) {
    if (entry.expiresAt <= now) {
      validationCache.delete(key)
    }
  }
}

/**
 * Validate the Authorization header from an incoming MCP request.
 *
 * Calls GET /api/mcp/keys/validate with the raw Authorization header forwarded.
 * Uses the X-MCP-Internal-Token service secret so the platform trusts the caller.
 *
 * F.5: cache hit skips the platform roundtrip; miss writes the result for 60s.
 *
 * @param authorizationHeader  The raw "Authorization" header value (e.g. "Bearer mcp_prod_...").
 * @returns  Principal on success, null on any failure (invalid key, network error, etc.).
 */
export async function validateMcpKeyFromHeader(
  authorizationHeader: string | undefined
): Promise<Principal | null> {
  if (!authorizationHeader) return null

  // F.5: check the cache before hitting the platform
  evictExpired()
  const key = cacheKey(authorizationHeader)
  const cached = validationCache.get(key)
  if (cached && cached.expiresAt > Date.now()) {
    return cached.principal
  }

  try {
    const response = await fetch(`${PLATFORM_URL}/api/mcp/keys/validate`, {
      method: 'GET',
      headers: {
        'Authorization': authorizationHeader,
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      },
      signal: AbortSignal.timeout(5000),
    })

    if (!response.ok) {
      // 401 from the platform means our service token is wrong (config issue)
      console.error(`[mcp:auth] Validate endpoint returned ${response.status}`)
      return null
    }

    const data = (await response.json()) as KeyValidateResponse

    if (!data.valid || !data.user_uid || !data.key_id) {
      return null
    }

    const principal: Principal = {
      user_uid: data.user_uid,
      // audience_tier excised (Stream A 3.tier_excision 2026-05-28).
      key_id: data.key_id,
      role: data.role ?? 'guest',
    }

    // F.5: write to cache on successful validation
    validationCache.set(key, {
      principal,
      expiresAt: Date.now() + CACHE_TTL_MS,
    })

    return principal
  } catch (err) {
    console.error('[mcp:auth] Key validation network error:', err instanceof Error ? err.message : String(err))
    return null
  }
}

/**
 * Exported for testing: returns the current cache size (number of non-expired entries).
 * Do not use in production code.
 */
export function _testGetCacheSize(): number {
  evictExpired()
  return validationCache.size
}

/**
 * Exported for testing: clears the validation cache.
 * Do not use in production code.
 */
export function _testClearCache(): void {
  validationCache.clear()
}

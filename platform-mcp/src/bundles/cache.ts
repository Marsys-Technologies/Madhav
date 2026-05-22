/**
 * cache.ts — 5-minute content-addressable bundle cache.
 *
 * Key: sha256(query_text + JSON.stringify(composition_params) + tier + chart_id)
 * Store: mcp_bundle_cache table (migration 072).
 * TTL: 5 minutes.
 *
 * On hit: return cached envelope with served_from_cache: true.
 * On miss: caller runs the bundle, stores result, returns with served_from_cache: false.
 *
 * MCPT v3.1.0-S2
 */

import { createHash } from 'crypto'

// ── Platform fetch config ─────────────────────────────────────────────────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Cache key derivation ──────────────────────────────────────────────────────

/**
 * Compute a deterministic cache key from all inputs that affect bundle output.
 */
export function computeCacheKey(params: {
  bundleName: string
  queryText: string
  compositionParams: Record<string, unknown>
  tier: string
  chartId: string
}): string {
  const raw = JSON.stringify({
    b: params.bundleName,
    q: params.queryText,
    p: params.compositionParams,
    t: params.tier,
    c: params.chartId,
  })
  return createHash('sha256').update(raw).digest('hex')
}

// ── Cache lookup ──────────────────────────────────────────────────────────────

export interface CacheHit {
  hit: true
  envelope: unknown
  cached_at: string
  expires_at: string
}

export interface CacheMiss {
  hit: false
}

export type CacheLookupResult = CacheHit | CacheMiss

/**
 * Look up a bundle result in mcp_bundle_cache.
 * Returns CacheHit (with envelope) on hit, CacheMiss on miss or error.
 */
export async function cacheLookup(cacheKey: string): Promise<CacheLookupResult> {
  try {
    const response = await fetch(`${PLATFORM_URL}/api/mcp/bundles/cache/lookup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      },
      body: JSON.stringify({ cache_key: cacheKey }),
      signal: AbortSignal.timeout(3_000),
    })

    if (!response.ok) return { hit: false }

    const data = (await response.json()) as {
      hit: boolean
      envelope?: unknown
      cached_at?: string
      expires_at?: string
    }

    if (data.hit && data.envelope && data.cached_at && data.expires_at) {
      return {
        hit: true,
        envelope: data.envelope,
        cached_at: data.cached_at,
        expires_at: data.expires_at,
      }
    }

    return { hit: false }
  } catch {
    // Cache lookup failures are non-fatal; treat as miss.
    return { hit: false }
  }
}

/**
 * Store a bundle result in mcp_bundle_cache.
 * Failures are logged but non-fatal.
 */
export async function cacheStore(params: {
  cacheKey: string
  bundleName: string
  audienceTier: string
  chartId: string
  envelope: unknown
}): Promise<void> {
  try {
    await fetch(`${PLATFORM_URL}/api/mcp/bundles/cache/store`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      },
      body: JSON.stringify({
        cache_key: params.cacheKey,
        bundle_name: params.bundleName,
        audience_tier: params.audienceTier,
        chart_id: params.chartId,
        envelope_json: params.envelope,
      }),
      signal: AbortSignal.timeout(5_000),
    })
  } catch (err) {
    console.warn('[mcp:bundle:cache] Cache store failed (non-fatal):', err)
  }
}

/**
 * In-process result cache for retrieval tool handlers.
 * 60-second TTL. Keyed by (tool_name, stable_args_hash) — and args ALWAYS carry
 * chart_id, so the key is chart-scoped.
 * Eliminates thundering-herd DB load when multiple users query the same chart simultaneously.
 *
 * WP-0.1 / LCA-17 (F-0893/0902/0905/0908): the previous key hash was a weak
 * 32-bit rolling hash. Two DIFFERENT chart_ids whose argument objects hashed to
 * the same 32-bit value collapsed to the SAME cache key, so a concurrent
 * different-chart request read the wrong chart's cached, chart-stamped payload —
 * a load-correlated cross-chart data substitution. The key is now a full-width
 * SHA-256 over a STABLE (key-sorted) serialization: collision-resistant and
 * order-independent, so the key strictly encodes the full argument set
 * (chart_id included). Isolation is made stricter, never looser.
 */

import { createHash } from 'crypto'

interface CacheEntry {
  result: unknown
  expiresAt: number
}

const _cache = new Map<string, CacheEntry>()
const _TTL_MS = 60_000

/**
 * Stable JSON serialization — sorts object keys recursively so two argument
 * objects that differ only in key insertion order hash identically, and
 * `undefined`-valued fields are elided consistently (matching JSON.stringify).
 */
function _stableStringify(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value) ?? 'null'
  if (Array.isArray(value)) return `[${value.map(_stableStringify).join(',')}]`
  const obj = value as Record<string, unknown>
  const keys = Object.keys(obj).filter((k) => obj[k] !== undefined).sort()
  return `{${keys.map((k) => `${JSON.stringify(k)}:${_stableStringify(obj[k])}`).join(',')}}`
}

function _hash(obj: unknown): string {
  // Full-width, collision-resistant cache-key hash (WP-0.1 LCA-17 fix).
  return createHash('sha256').update(_stableStringify(obj)).digest('hex')
}

export function cacheKey(toolName: string, args: Record<string, unknown>): string {
  return `${toolName}::${_hash(args)}`
}

export function cacheGet(key: string): unknown | undefined {
  const entry = _cache.get(key)
  if (!entry) return undefined
  if (Date.now() > entry.expiresAt) {
    _cache.delete(key)
    return undefined
  }
  return entry.result
}

export function cacheSet(key: string, result: unknown): void {
  // Evict oldest 20% when cache exceeds 500 entries
  if (_cache.size >= 500) {
    const now = Date.now()
    let evicted = 0
    for (const [k, v] of _cache) {
      if (v.expiresAt < now || evicted < 100) {
        _cache.delete(k)
        evicted++
      }
      if (evicted >= 100) break
    }
  }
  _cache.set(key, { result, expiresAt: Date.now() + _TTL_MS })
}

/**
 * Test-only: wipe the module-level cache so a test starts from a clean,
 * deterministic state. Not for production use — the cache is otherwise
 * self-managing via TTL + eviction. Exposed so the WP-0.1 cross-chart
 * isolation regression suite can assert on a known-empty cache.
 */
export function __clearRetrievalCache(): void {
  _cache.clear()
}

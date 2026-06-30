/**
 * In-process result cache for retrieval tool handlers.
 * 60-second TTL. Keyed by (chart_id, tool_name, stable_args_hash).
 * Eliminates thundering-herd DB load when multiple users query the same chart simultaneously.
 */

interface CacheEntry {
  result: unknown
  expiresAt: number
}

const _cache = new Map<string, CacheEntry>()
const _TTL_MS = 60_000

function _hash(obj: unknown): string {
  // Simple deterministic hash for cache keys — not cryptographic
  return JSON.stringify(obj).split('').reduce((acc, c) => (acc * 31 + c.charCodeAt(0)) & 0xffffffff, 0).toString(36)
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

/**
 * MARSYS-JIS Stream C — Shared cache adapter (Memorystore Redis-backed)
 * schema_version: 1.0
 *
 * Wave 4 unit 4.memorystore_caching.
 *
 * Provides a small Promise<T>-shaped API on top of ioredis with three
 * promises:
 *   1. NEVER throws on Redis trouble — every Redis call is guarded; failures
 *      return `undefined` so callers fall back to compute-on-miss cleanly.
 *      (This is the chaos-test recovery path.)
 *   2. Cache keys are namespaced (`marsys:<surface>:<hash>`) so per-surface
 *      invalidation is a single `SCAN + DEL` (`invalidateNamespace`).
 *   3. Per-chart invalidation hook (`invalidateChart(chartId)`) is a no-op
 *      stub — when a chart_id changes (rare; only on chart re-resolution),
 *      callers nuke any key whose params_hash subsumed that chart_id.
 *
 * Surfaces wired today:
 *   - `retrieval-bundle` keyed by (chart_id, ayanamsha_id, tool, params_hash)
 *   - `planner` keyed by (chart_id, planner_prompt_version, query_hash)
 *   - `vertex-embed` keyed by hash(text)
 *
 * Metrics hooks fire on hit/miss/error → consumed by the observability unit
 * (4.observability, sibling commit).
 */

import 'server-only'
import crypto from 'crypto'
import { getRedis } from './redis_client'

export type SharedCacheSurface = 'retrieval-bundle' | 'planner' | 'vertex-embed' | 'active-charts' | 'runtime-config' | 'mcp-capability'

export interface CacheMetricsEvent {
  surface: SharedCacheSurface
  outcome: 'hit' | 'miss' | 'set' | 'error' | 'skipped'
  latency_ms: number
  key_preview: string // first 80 chars of the key for trace correlation
  error?: string
}

type MetricsSink = (ev: CacheMetricsEvent) => void
let _metricsSink: MetricsSink = () => {}

export function setCacheMetricsSink(sink: MetricsSink): void {
  _metricsSink = sink
}

function emit(ev: CacheMetricsEvent): void {
  try {
    _metricsSink(ev)
  } catch {
    // never let metric emission break the cache
  }
}

const NAMESPACE_PREFIX = 'marsys'

/** Stable JSON stringify — sorts object keys so identical params hash identically. */
function stableStringify(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`
  const keys = Object.keys(value as Record<string, unknown>).sort()
  return `{${keys.map((k) => `${JSON.stringify(k)}:${stableStringify((value as Record<string, unknown>)[k])}`).join(',')}}`
}

export function hashParams(params: Record<string, unknown>): string {
  return crypto.createHash('sha256').update(stableStringify(params)).digest('hex').slice(0, 32)
}

export function buildKey(surface: SharedCacheSurface, parts: Record<string, unknown>): string {
  const hash = hashParams(parts)
  return `${NAMESPACE_PREFIX}:${surface}:${hash}`
}

export interface SharedCacheOptions {
  /** TTL in seconds. Required — there is no "forever" cache. */
  ttlSeconds: number
}

/**
 * Read from Redis. Returns `undefined` on miss, connection error, parse
 * error, or any other Redis trouble. NEVER throws.
 */
export async function cacheGet<T>(surface: SharedCacheSurface, key: string): Promise<T | undefined> {
  const t0 = Date.now()
  const r = getRedis()
  if (!r) {
    emit({ surface, outcome: 'skipped', latency_ms: 0, key_preview: key.slice(0, 80) })
    return undefined
  }
  try {
    const raw = await r.get(key)
    if (raw == null) {
      emit({ surface, outcome: 'miss', latency_ms: Date.now() - t0, key_preview: key.slice(0, 80) })
      return undefined
    }
    const parsed = JSON.parse(raw) as T
    emit({ surface, outcome: 'hit', latency_ms: Date.now() - t0, key_preview: key.slice(0, 80) })
    return parsed
  } catch (err) {
    emit({
      surface,
      outcome: 'error',
      latency_ms: Date.now() - t0,
      key_preview: key.slice(0, 80),
      error: err instanceof Error ? err.message : String(err),
    })
    return undefined
  }
}

/**
 * Write to Redis with TTL. Failure is silent — never throws. The compute
 * path already succeeded; an unwritten cache only loses the next-hit speedup.
 */
export async function cacheSet<T>(
  surface: SharedCacheSurface,
  key: string,
  value: T,
  opts: SharedCacheOptions,
): Promise<void> {
  const t0 = Date.now()
  const r = getRedis()
  if (!r) {
    emit({ surface, outcome: 'skipped', latency_ms: 0, key_preview: key.slice(0, 80) })
    return
  }
  try {
    const payload = JSON.stringify(value)
    await r.set(key, payload, 'EX', opts.ttlSeconds)
    emit({ surface, outcome: 'set', latency_ms: Date.now() - t0, key_preview: key.slice(0, 80) })
  } catch (err) {
    emit({
      surface,
      outcome: 'error',
      latency_ms: Date.now() - t0,
      key_preview: key.slice(0, 80),
      error: err instanceof Error ? err.message : String(err),
    })
  }
}

/**
 * Read-through helper — the canonical wrapper for "look in Redis, else
 * compute + store". Guarantees the compute closure runs at most once per
 * cache-cold call. NEVER throws on cache trouble.
 */
export async function cacheGetOrCompute<T>(
  surface: SharedCacheSurface,
  key: string,
  ttlSeconds: number,
  compute: () => Promise<T>,
): Promise<T> {
  const cached = await cacheGet<T>(surface, key)
  if (cached !== undefined) return cached
  const fresh = await compute()
  // Fire-and-forget — caller already has the answer.
  void cacheSet(surface, key, fresh, { ttlSeconds })
  return fresh
}

/**
 * Surface-wide invalidation. Uses SCAN (NOT KEYS — production-safe) and
 * UNLINK (async delete). Returns the count deleted, 0 on any error.
 */
export async function invalidateNamespace(surface: SharedCacheSurface): Promise<number> {
  const r = getRedis()
  if (!r) return 0
  try {
    const match = `${NAMESPACE_PREFIX}:${surface}:*`
    let cursor = '0'
    let deleted = 0
    do {
      const [next, keys] = await r.scan(cursor, 'MATCH', match, 'COUNT', 500)
      cursor = next
      if (keys.length > 0) {
        deleted += await r.unlink(...keys)
      }
    } while (cursor !== '0')
    return deleted
  } catch {
    return 0
  }
}

/**
 * Per-chart invalidation hook. Today: invalidates retrieval-bundle + planner +
 * mcp-capability surfaces (the ones that key on chart_id — mcp-capability
 * added W5/L6: the capability dispatcher cache keys on `args` which includes
 * `chart_id` for per_chart capabilities). When chart_id materially changes
 * (rare — only on chart re-resolution / kundali rebuild), call this.
 *
 * Implementation deliberately wipes the entire surface rather than walking
 * keys to filter by chart_id — Redis SCAN can't introspect JSON payloads,
 * and re-keying schemes are more failure-surface than they're worth for
 * an event that fires <1/day.
 */
export async function invalidateChart(_chartId: string): Promise<void> {
  await Promise.all([
    invalidateNamespace('retrieval-bundle'),
    invalidateNamespace('planner'),
    invalidateNamespace('mcp-capability'),
  ])
}

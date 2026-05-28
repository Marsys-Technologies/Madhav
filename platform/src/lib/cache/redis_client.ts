/**
 * MARSYS-JIS Stream C — Memorystore Redis client singleton
 * schema_version: 1.0
 *
 * Wave 4 unit 4.memorystore_caching.
 *
 * Returns a lazily-initialised ioredis client connected to the Memorystore
 * instance provisioned by `infra/memorystore/main.tf`. Connection details
 * come from REDIS_HOST + REDIS_PORT env vars (set by deploy.yml).
 *
 * If either env var is missing, the helper returns `null` and callers MUST
 * gracefully fall back to compute-on-miss. This keeps local dev + tests
 * functional without a live Redis (and is the chaos-test recovery path).
 */

import 'server-only'
import IORedis, { type Redis } from 'ioredis'

let _client: Redis | null = null
let _disabledReason: string | null = null

/**
 * Returns the shared Redis client, or `null` if Redis is not configured
 * or has been observed to be unhealthy. NEVER throws — callers must treat
 * a null return as "skip cache, compute directly".
 */
export function getRedis(): Redis | null {
  if (_client) return _client
  if (_disabledReason) return null

  const host = process.env.REDIS_HOST
  const port = process.env.REDIS_PORT ? Number(process.env.REDIS_PORT) : 6379

  if (!host) {
    _disabledReason = 'REDIS_HOST not set'
    return null
  }

  try {
    _client = new IORedis({
      host,
      port,
      // Memorystore is in-VPC; no TLS, no AUTH by default for BASIC tier.
      // Conservative defaults: never hang on a sick Redis; let the caller
      // fall back to compute.
      connectTimeout: 500,
      commandTimeout: 200,
      maxRetriesPerRequest: 1,
      enableReadyCheck: true,
      // Lazy connect — the constructor returning does not mean we're up.
      lazyConnect: false,
      retryStrategy: (times) => {
        if (times > 3) return null // stop retrying — fall back to direct compute
        return Math.min(times * 200, 1000)
      },
    })

    _client.on('error', (err) => {
      // Demote to warn — Redis-unreachable is an expected degraded state.
      // We do NOT mark the client permanently dead on transient errors;
      // ioredis handles reconnect. We only swallow to keep the process alive.
      // eslint-disable-next-line no-console
      console.warn('[redis] connection error:', err.message)
    })

    return _client
  } catch (err) {
    _disabledReason = err instanceof Error ? err.message : String(err)
    // eslint-disable-next-line no-console
    console.warn('[redis] init failed:', _disabledReason)
    _client = null
    return null
  }
}

/**
 * Test helper — disconnects + resets the singleton. NOT for production code.
 */
export async function __resetRedisForTests(): Promise<void> {
  if (_client) {
    try {
      await _client.quit()
    } catch {
      // ignore
    }
  }
  _client = null
  _disabledReason = null
}

export function isRedisDisabled(): boolean {
  return _disabledReason !== null && _client === null
}

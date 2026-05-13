import type { Provider } from '@/lib/models/registry'
import type { CatalogEntry, CatalogFetchResult } from './types'

const TTL_MS = 6 * 60 * 60 * 1000 // 6 hours

interface CacheEntry {
  models:        CatalogEntry[]
  fetched_at:    string
  expires_at:    number  // Date.now() + TTL
}

const _cache = new Map<Provider, CacheEntry>()

export function getCached(provider: Provider): CacheEntry | null {
  const entry = _cache.get(provider)
  if (!entry) return null
  if (Date.now() > entry.expires_at) return null
  return entry
}

export function setCached(provider: Provider, models: CatalogEntry[], fetched_at: string): void {
  _cache.set(provider, {
    models,
    fetched_at,
    expires_at: Date.now() + TTL_MS,
  })
}

/** Returns the last-known-good models from cache regardless of TTL. */
export function getStale(provider: Provider): CacheEntry | null {
  return _cache.get(provider) ?? null
}

/** Force-clear a provider's cache entry (used by force-refresh endpoint). */
export function invalidateProvider(provider: Provider): void {
  _cache.delete(provider)
}

/** Build a stale-enriched CatalogFetchResult from a failed fetch + cache. */
export function makeStaleResult(
  provider: Provider,
  failed: Pick<CatalogFetchResult, 'status' | 'raw' | 'fetched_at'>,
): CatalogFetchResult {
  const stale = getStale(provider)
  return {
    ...failed,
    models: stale?.models ?? [],
    stale:  true,
    last_successful_fetch: stale?.fetched_at ?? undefined,
  }
}

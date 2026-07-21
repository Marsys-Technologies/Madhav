/**
 * capability_dispatch_cache.ts — MCP capability dispatcher memoization
 * ======================================================================
 * W5 L6 (Adaptive Serving + Scale — funnel N+1 batching + pooling/replica +
 * sidecar memoization/caps, brief §E W5 / plan §9.7 W-29).
 *
 * PROBLEM (found live, not assumed): `/api/retrieval/capability/route.ts` —
 * the dispatcher `platform-mcp/src/tools/registry_bridge.ts`'s
 * `callRegistryCapability()` proxies EVERY MCP-served capability call
 * through (query_planet_position, query_planet_transit, call_panchanga_service,
 * query_aspects_at_time, etc. — several of which call out to the Python
 * sidecar over plain `fetch()`, and several of which hit chart_facts/
 * chart_dashas over the shared pg.Pool) dispatches with
 * `await capability.handler(safeArgs)` DIRECTLY — zero caching, zero
 * request-coalescing. This is a DIFFERENT code path from the web consult
 * route's `tool_fetch` loop (`executeWithCache` + `RequestScopedToolCache`),
 * which already had a two-tier cache; the MCP capability dispatcher — the
 * path the live MARSYS-JIS-direct connector actually uses (brief §B "the
 * live instrument") — had none. Two identical capability calls (same URI +
 * same args — e.g. two fan-out branches of a synthesis/judgment call both
 * asking for the same chart's chart_header, or a client re-asking the same
 * date's panchanga) each independently re-hit the DB/sidecar.
 *
 * FIX — the same two-tier shape as `with_cache.ts`, adapted to the raw
 * (uri, args) → content shape this route deals with instead of
 * (tool, plan) → ToolBundle:
 *   L1 — in-process, PROCESS-LIFETIME (not request-lifetime — this route has
 *        no natural request-scoped object to thread through; each POST is
 *        one capability call) Map of in-flight Promises, so concurrent
 *        identical calls within the same server instance share one compute.
 *        BOUNDED (`MAX_INFLIGHT_ENTRIES`) with FIFO eviction — the "caps"
 *        part of this lane's scope; unbounded key fan-out (many distinct
 *        chart_id/date/planet combinations) must not grow this map forever.
 *   L2 — shared Memorystore Redis (`mcp-capability` surface, added to
 *        `shared_cache.ts`'s `SharedCacheSurface` union by this lane),
 *        TTL-bounded, survives Cloud Run instance recycling — same
 *        cross-instance benefit `with_cache.ts` gives the web path.
 *
 * OPT-IN, NOT BLANKET: only capabilities that self-declare
 * `llm_hints.agentic.cacheable === true` are cached — this is the same
 * signal 99 existing descriptors already carry (chart_header, ephemeris
 * lookups, panchanga-for-a-date, reference data, …), so this lane adds no
 * new metadata surface, it just finally CONSUMES a field that was declared
 * but never read anywhere. A capability that doesn't declare cacheable:true
 * (e.g. anything with a write/mutation shape, or genuinely "as of right now"
 * semantics) bypasses this cache entirely and calls the handler directly,
 * unchanged from today.
 *
 * TTL is deliberately short (60s, matching `chart_header.ts`'s existing
 * in-process cache convention) — conservative given some cached capabilities
 * can carry time-indexed signals; a stale bundle is worse than a slow one.
 */
import { buildKey, cacheGet, cacheSet } from './shared_cache'

/** Matches `chart_header.ts`'s existing in-process TTL convention. */
export const CAPABILITY_CACHE_TTL_SECONDS = 60

/** FIFO cap on the in-process in-flight/coalescing map (the "caps" requirement). */
export const MAX_INFLIGHT_ENTRIES = 500

interface InflightEntry {
  promise: Promise<unknown>
}

let _inflight = new Map<string, InflightEntry>()

/** Test-only reset — process-lifetime state must not leak across test files. */
export function __resetCapabilityDispatchCacheForTests(): void {
  _inflight = new Map()
}

/** Test-only introspection — current in-flight map size. */
export function __inflightSizeForTests(): number {
  return _inflight.size
}

function buildCapabilityCacheKey(uri: string, args: Record<string, unknown>): string {
  return buildKey('mcp-capability', { uri, args })
}

function evictOldestIfAtCap(): void {
  if (_inflight.size < MAX_INFLIGHT_ENTRIES) return
  // Map preserves insertion order — the first key is the oldest (FIFO).
  const oldestKey = _inflight.keys().next().value
  if (oldestKey !== undefined) _inflight.delete(oldestKey)
}

/**
 * Memoized capability dispatch. Callers pass the raw `compute` closure
 * (typically `() => capability.handler(args)`); this wrapper:
 *   1. Coalesces concurrent identical in-process calls (L1, bounded FIFO map).
 *   2. Falls back to the shared Redis surface (L2, TTL-bounded).
 *   3. On a genuine miss, computes, stores into both tiers, and returns.
 *
 * `cacheable` gates entry — pass `capability.llm_hints?.agentic?.cacheable
 * === true` from the call site. When false, this function is a plain
 * pass-through to `compute()` with no caching side effects at all.
 */
export async function getOrComputeCapability<T>(
  uri: string,
  args: Record<string, unknown>,
  cacheable: boolean,
  compute: () => Promise<T>,
): Promise<T> {
  if (!cacheable) return compute()

  const key = buildCapabilityCacheKey(uri, args)

  // L1 — same-process coalescing of concurrent identical calls.
  const existing = _inflight.get(key)
  if (existing) return existing.promise as Promise<T>

  const promise = (async () => {
    try {
      // L2 — shared cross-instance cache.
      const cached = await cacheGet<T>('mcp-capability', key)
      if (cached !== undefined) return cached

      const fresh = await compute()
      void cacheSet('mcp-capability', key, fresh, { ttlSeconds: CAPABILITY_CACHE_TTL_SECONDS })
      return fresh
    } finally {
      // Always remove from the in-flight map once settled — L1 exists only to
      // coalesce CONCURRENT callers, not to hold a long-lived resolved value
      // (that's L2's + the TTL's job). This also keeps the map's steady-state
      // size bounded by actual concurrency, not by call volume over time.
      _inflight.delete(key)
    }
  })()

  evictOldestIfAtCap()
  _inflight.set(key, { promise })
  return promise
}

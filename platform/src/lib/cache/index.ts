/**
 * MARSYS-JIS Stream D — cache barrel export
 */

export { RequestScopedToolCache, createToolCache } from './tool_cache'
export { executeWithCache } from './with_cache'

// Stream C — Wave 4 unit 4.memorystore_caching
export { getRedis, isRedisDisabled, __resetRedisForTests } from './redis_client'
export {
  cacheGet,
  cacheSet,
  cacheGetOrCompute,
  buildKey,
  hashParams,
  invalidateNamespace,
  invalidateChart,
  setCacheMetricsSink,
} from './shared_cache'
export type {
  SharedCacheSurface,
  SharedCacheOptions,
  CacheMetricsEvent,
} from './shared_cache'
export { callPipelinePlannerCached } from './planner_cache'

// W5 L6 — MCP capability dispatcher memoization
export {
  getOrComputeCapability,
  CAPABILITY_CACHE_TTL_SECONDS,
  MAX_INFLIGHT_ENTRIES,
} from './capability_dispatch_cache'

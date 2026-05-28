/**
 * MARSYS-JIS Stream D — executeWithCache helper
 * schema_version: 1.1
 *
 * Wraps a RetrievalTool.retrieve() call with a TWO-tier cache:
 *   L1 — RequestScopedToolCache (in-process, request-scoped, coalesces
 *        concurrent identical calls within ONE panel turn).
 *   L2 — Shared Memorystore Redis (per-surface 'retrieval-bundle' namespace,
 *        TTL-bounded, survives Cloud Run instance recycling). [Stream C, Wave 4]
 *
 * Lookup order: L1 → L2 → compute. Store order: compute result → L1 (Promise)
 * → L2 (resolved JSON, fire-and-forget). L2 is OPTIONAL — absence of
 * REDIS_HOST or any Redis trouble falls back cleanly to L1-only behaviour.
 */

import type { QueryPlan, ToolBundle, RetrievalTool } from '../retrieve/types'
import { RequestScopedToolCache } from './tool_cache'
import { buildKey, cacheGet, cacheSet } from './shared_cache'

/**
 * Shared (L2) cache TTL for retrieval bundles. 10 minutes is conservative
 * given that bundles can include time-indexed signals — a stale bundle is
 * worse than a slow one.
 */
const SHARED_BUNDLE_TTL_SECONDS = 600

/**
 * Build the L2 cache key from the same fields as L1 plus the manifest
 * fingerprint (so a manifest rebuild auto-invalidates the cache) and the
 * audience_tier (so a super_admin's bundle does not leak to a client tier).
 */
function buildSharedBundleKey(
  toolName: string,
  plan: QueryPlan,
  plannerParams?: Record<string, unknown>,
): string {
  return buildKey('retrieval-bundle', {
    tool: toolName,
    manifest_fingerprint: plan.manifest_fingerprint,
    audience_tier: plan.audience_tier,
    query_class: plan.query_class,
    domains: [...(plan.domains ?? [])].sort(),
    planets: [...(plan.planets ?? [])].sort(),
    forward_looking: plan.forward_looking,
    dasha_context_required: plan.dasha_context_required ?? false,
    ...(plannerParams && Object.keys(plannerParams).length > 0
      ? { planner_params: Object.fromEntries(Object.entries(plannerParams).sort()) }
      : {}),
  })
}

/**
 * Execute a retrieval tool with optional request-scoped caching.
 *
 * Cache key is derived from the fields that determine what the tool retrieves
 * (query_class, domains, planets, forward_looking, dasha_context_required).
 * Unique-per-request fields like query_plan_id are intentionally excluded so
 * that semantically identical requests within a panel turn share one result.
 */
export async function executeWithCache(
  tool: RetrievalTool,
  plan: QueryPlan,
  cache?: RequestScopedToolCache,
  plannerParams?: Record<string, unknown>,
): Promise<ToolBundle> {
  const sharedKey = buildSharedBundleKey(tool.name, plan, plannerParams)

  if (!cache) {
    // No request-scoped cache supplied — still try L2.
    const l2 = await cacheGet<ToolBundle>('retrieval-bundle', sharedKey)
    if (l2) return { ...l2, served_from_cache: true }
    const fresh = await tool.retrieve(plan, plannerParams)
    void cacheSet('retrieval-bundle', sharedKey, fresh, { ttlSeconds: SHARED_BUNDLE_TTL_SECONDS })
    return fresh
  }

  const cacheKey: Record<string, unknown> = {
    query_class: plan.query_class,
    domains: [...(plan.domains ?? [])].sort(),
    planets: [...(plan.planets ?? [])].sort(),
    forward_looking: plan.forward_looking,
    dasha_context_required: plan.dasha_context_required ?? false,
    ...(plannerParams && Object.keys(plannerParams).length > 0
      ? { planner_params: Object.fromEntries(Object.entries(plannerParams).sort()) }
      : {}),
  }

  // L1 — same-request coalescing.
  const existing = cache.getPromise(tool.name, cacheKey)
  if (existing) {
    const cached = await existing
    return { ...cached, served_from_cache: true }
  }

  // L2 → compute → L1 fold.
  // We register a Promise into L1 that resolves either from L2 or from compute,
  // so that two concurrent first-time callers in the same request share work.
  const promise = (async () => {
    const l2 = await cacheGet<ToolBundle>('retrieval-bundle', sharedKey)
    if (l2) return { ...l2, served_from_cache: true }
    const fresh = await tool.retrieve(plan, plannerParams)
    void cacheSet('retrieval-bundle', sharedKey, fresh, { ttlSeconds: SHARED_BUNDLE_TTL_SECONDS })
    return fresh
  })()
  cache.put(tool.name, cacheKey, promise)
  return await promise
}

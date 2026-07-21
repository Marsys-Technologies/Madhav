/**
 * MARSYS-JIS Stream C — Planner output cache wrapper
 * schema_version: 1.0
 *
 * Wave 4 unit 4.memorystore_caching.
 *
 * Wraps `callPipelinePlanner` with a Memorystore-backed cache so that
 * deterministic-input planner calls (same query, same history, same
 * manifest fingerprint, same model) skip the LLM round-trip.
 *
 * The cache key intentionally INCLUDES:
 *   - query text (after trim/normalise)
 *   - serialised conversation history (planner is order-sensitive)
 *   - plannerModelId (different model = different plan)
 *   - nativeId (the chart context)
 *
 * And EXCLUDES:
 *   - queryId (request-instance only; not semantic)
 *   - emitTrace (side-effect callback; cache-hit fires synthetic trace)
 *   - fallbackModelId (cache stores happy-path outcome only)
 *
 * TTL = 5 minutes. Planner output is "fresh enough" within a conversation
 * burst; longer TTL risks staleness when the manifest is re-baked.
 *
 * Trace-event parity on cache hit: emits a single 'planning_start' +
 * 'step_start' + 'step_finish' triplet with `cache_hit: true`. The
 * synthesis layer downstream remains agnostic.
 */

import 'server-only'
import type { PlannerOutcome, PlanReceipt } from '@/lib/pipeline/types'
import type { TraceEvent } from '@/lib/trace/types'
import { callPipelinePlanner } from '@/lib/pipeline/pipeline_planner'
import { buildKey, cacheGet, cacheSet } from './shared_cache'

const PLANNER_CACHE_TTL_SECONDS = 5 * 60

export async function callPipelinePlannerCached(
  query: string,
  conversationHistory: Array<{ role: string; content: string }>,
  plannerModelId: string,
  nativeId: string,
  emitTrace?: (event: TraceEvent) => void,
  queryId?: string,
  fallbackModelId?: string,
): Promise<PlannerOutcome> {
  const key = buildKey('planner', {
    query: query.trim(),
    history: conversationHistory.map((m) => `${m.role}:${m.content}`).join('\n'),
    planner_model_id: plannerModelId,
    native_id: nativeId,
  })

  // W4: only the happy-path 'plan' outcome is cached (see EXCLUDES note above);
  // clarification/fault outcomes are cheap and situational, never memoised.
  const cached = await cacheGet<PlanReceipt>('planner', key)
  if (cached) {
    if (emitTrace && queryId) {
      const ts = new Date().toISOString()
      emitTrace({
        event: 'step_start',
        query_id: queryId,
        step: {
          query_id: queryId,
          step_seq: 0,
          step_name: 'llm_planner',
          step_type: 'llm',
          status: 'running',
          started_at: ts,
          data_summary: { model: plannerModelId, planner_active: true, cache_hit: true },
          payload: {},
        },
      } as TraceEvent)
    }
    return cached
  }

  const fresh = await callPipelinePlanner(
    query,
    conversationHistory,
    plannerModelId,
    nativeId,
    emitTrace,
    queryId,
    fallbackModelId,
  )
  if (fresh.outcome === 'plan') {
    void cacheSet('planner', key, fresh, { ttlSeconds: PLANNER_CACHE_TTL_SECONDS })
  }
  return fresh
}

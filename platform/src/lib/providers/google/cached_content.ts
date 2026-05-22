import 'server-only'

/**
 * google/cached_content.ts — D-S2 R11.D
 *
 * Helpers for the Gemini cachedContent API.
 *
 * Gemini caching works differently from Anthropic: instead of in-request
 * markers, you CREATE a `cachedContent` object (system prompt + static context)
 * via a separate API call, then reference its `name` in subsequent
 * `generateContent` calls. The cache object has a configurable TTL.
 *
 * Gemini cachedContent API shape (google-genai SDK):
 *   POST /v1beta/cachedContents
 *   { model, contents: [...], systemInstruction, ttl }
 *   → { name: "cachedContents/abc123", ... }
 *
 * Usage in generateContent:
 *   { cachedContent: "cachedContents/abc123", ... }
 *
 * MARSYS usage pattern:
 *   - Cache: synthesis system prompt + RAG bundle (large, stable within session)
 *   - Per-request: history turns + current user turn (dynamic)
 *   - TTL: 600s (10 min) — longer than Anthropic's 5-min ephemeral to absorb
 *     multi-turn sessions with slower query cadence.
 *
 * The helpers here return strongly-typed config objects consumed by the
 * GoogleAdapter.cache() method. No SDK import here — that coupling lives
 * in the R11.C chat() pipeline. This module only defines the config shapes.
 */

/** TTL for Gemini cached content objects. Default: 10 min (600s). */
export const GEMINI_CACHE_TTL_SECONDS = 600

/** Minimum cached content size — Gemini requires ≥32,768 tokens to cache.
 *  Below this threshold the cache API returns an error; the adapter must fall
 *  back to a standard (uncached) request. */
export const GEMINI_CACHE_MIN_TOKENS = 32768

/**
 * Input to the Gemini cachedContent creation call.
 * Caller provides content strings; this module produces the SDK payload shape.
 */
export interface GeminiCacheCreateInput {
  /** The fully-qualified model string (must include version). */
  model: string
  /** Static system prompt (the largest stable block). */
  systemPrompt?: string
  /** RAG bundle — retrieval context for this query set. */
  ragBundle?: string
  /** ISO-8601 duration string for TTL, e.g. "600s". Defaults to GEMINI_CACHE_TTL_SECONDS. */
  ttl?: string
}

/**
 * SDK-shaped payload for creating a Gemini cachedContent object.
 *
 * Matches the google-genai SDK `CachedContent` creation shape.
 * Actual SDK call: `genai.caches.create(payload)`.
 */
export interface GeminiCacheCreatePayload {
  /** Fully-qualified model name, e.g. "gemini-2.5-pro". */
  model: string
  /** System instruction (maps to systemInstruction in SDK). */
  systemInstruction?: { parts: Array<{ text: string }> }
  /** Contents to cache (maps to contents array in SDK). */
  contents?: Array<{ role: string; parts: Array<{ text: string }> }>
  /** TTL duration string, e.g. "600s". */
  ttl: string
  /** Display name for audit trail. */
  displayName?: string
}

/**
 * Builds the cachedContent creation payload from a GeminiCacheCreateInput.
 *
 * The system prompt is placed in `systemInstruction` (Gemini's dedicated field);
 * the RAG bundle is placed as a user-role `contents` entry so it precedes the
 * dynamic turn history.
 */
export function buildCacheCreatePayload(
  input: GeminiCacheCreateInput,
): GeminiCacheCreatePayload {
  const payload: GeminiCacheCreatePayload = {
    model: input.model,
    ttl: input.ttl ?? `${GEMINI_CACHE_TTL_SECONDS}s`,
    displayName: 'marsys-synthesis-cache',
  }

  if (input.systemPrompt) {
    payload.systemInstruction = {
      parts: [{ text: input.systemPrompt }],
    }
  }

  if (input.ragBundle) {
    payload.contents = [
      {
        role: 'user',
        parts: [{ text: input.ragBundle }],
      },
    ]
  }

  return payload
}

/**
 * Usage metrics captured from a Gemini response when cachedContent was used.
 * Sourced from `response.usageMetadata.cachedContentTokenCount`.
 */
export interface GeminiCacheUsageMetrics {
  /** Tokens served from the cachedContent object (reduces billable input). */
  cachedContentTokenCount: number
  /** Total prompt token count (cached + non-cached). */
  promptTokenCount: number
  /** Response (output) token count. */
  candidatesTokenCount: number
}

/**
 * Extracts cache usage metrics from a Gemini response usageMetadata object.
 * Returns null when cachedContentTokenCount is absent or zero.
 */
export function extractGeminiCacheMetrics(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  usageMetadata: Record<string, any> | undefined,
): GeminiCacheUsageMetrics | null {
  if (!usageMetadata) return null

  const cachedTokens: number = usageMetadata.cachedContentTokenCount ?? 0
  if (cachedTokens === 0) return null

  return {
    cachedContentTokenCount: cachedTokens,
    promptTokenCount: usageMetadata.promptTokenCount ?? 0,
    candidatesTokenCount: usageMetadata.candidatesTokenCount ?? 0,
  }
}

/**
 * Builds a structured log record for Gemini cache metrics.
 * Tagged with marsys_event_type: gemini_cache_metrics for log-filter routing.
 */
export function buildGeminiCacheMetricsRecord(params: {
  model: string
  conversationId?: string
  cachedContentName: string
  metrics: GeminiCacheUsageMetrics
}): Record<string, unknown> {
  const { metrics } = params
  const cacheHitRatio =
    metrics.promptTokenCount > 0
      ? metrics.cachedContentTokenCount / metrics.promptTokenCount
      : 0

  return {
    marsys_event_type: 'gemini_cache_metrics',
    provider: 'google',
    timestamp: new Date().toISOString(),
    conversationId: params.conversationId,
    model: params.model,
    cachedContentName: params.cachedContentName,
    cachedContentTokenCount: metrics.cachedContentTokenCount,
    promptTokenCount: metrics.promptTokenCount,
    candidatesTokenCount: metrics.candidatesTokenCount,
    cacheHitRatio,
    // At ~25% cost for cached tokens vs 100% for non-cached:
    // savings = 0.75 × cachedTokens / promptTokens of the input cost
    estimatedCostSavingsRatio: 0.75 * cacheHitRatio,
  }
}

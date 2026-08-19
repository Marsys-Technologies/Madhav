/**
 * rate_limiter_core.ts — the RPM rolling-window counter, extracted verbatim.
 *
 * WHY THIS FILE EXISTS (Paripraśna P1 lane G1-D "Limits", NCD-8): the roadmap is
 * explicit that per-user rate limiting must REUSE `lib/mcp/rate_limiter.ts` and
 * "never a second implementation". But `rate_limiter.ts` imports `@/lib/db/client`
 * at module top for its daily-token-budget query, so importing it from the request
 * proxy (`src/proxy.ts`) would drag the pg client into the request front door for a
 * check that needs no database at all.
 *
 * So the counter moved DOWN into this leaf module rather than being copied sideways.
 * `rate_limiter.ts` now imports `checkRpm` from here; so does `proxy.ts`. There is
 * exactly ONE `rpmCounters` Map and ONE window algorithm in the codebase, and both
 * consumers share the same counter state within a process. Nothing about the MCP
 * limiter's behaviour changed — this is a move, not a rewrite.
 *
 * NOTE (inherited, unchanged): the in-process counter resets on service restart and
 * is per-instance on multi-instance deployments. For a cross-instance guarantee this
 * Map becomes a Redis counter. That caveat belongs to the algorithm, so it lives here
 * with it. The DB-backed budget checks (daily tokens in `rate_limiter.ts`, daily USD
 * in `@/lib/limits/spend_ceiling.ts`) are always cross-instance safe.
 *
 * @module rate_limiter_core
 */

/** Maximum requests per 60-second rolling window. */
export const RPM_LIMIT = parseInt(process.env.MCP_RPM_LIMIT ?? '60', 10)

/** Window size in milliseconds (60 seconds). */
export const WINDOW_MS = 60_000

interface RpmEntry {
  count: number
  window_start_ms: number
}

// Module-level map — persists across requests within the same process.
// On Cloud Run with multiple instances, each instance has its own counter.
// Each key maps to its current rolling-window state.
const rpmCounters = new Map<string, RpmEntry>()

export interface RpmResult {
  allowed: boolean
  retry_after_seconds?: number
}

/**
 * Check and update the rolling-window counter for a key.
 * Returns `allowed: true` if the request is within limit; false if exceeded.
 *
 * @param key   Any stable per-caller identity — an MCP `key_id`, a `user:<uid>`
 *              string from the proxy, an `admin:<uid>` string. The counter is
 *              namespaced by whatever the caller passes; it does not interpret it.
 * @param limit Optional per-call-site override of {@link RPM_LIMIT}.
 */
export function checkRpm(key: string, limit: number = RPM_LIMIT): RpmResult {
  const now = Date.now()
  const existing = rpmCounters.get(key)

  if (!existing || now - existing.window_start_ms >= WINDOW_MS) {
    // New window (first call ever, or window expired)
    rpmCounters.set(key, { count: 1, window_start_ms: now })
    return { allowed: true }
  }

  if (existing.count >= limit) {
    // Window still active, limit exceeded
    const retry_after_seconds = Math.ceil((WINDOW_MS - (now - existing.window_start_ms)) / 1000)
    return { allowed: false, retry_after_seconds }
  }

  // Within window, under limit
  existing.count += 1
  return { allowed: true }
}

/**
 * Drop all window state. TEST-ONLY — the rolling window is module state shared by
 * every consumer, so a test that exercises the limit must be able to start clean.
 * Never call this from production code.
 */
export function __resetRpmCountersForTest(): void {
  rpmCounters.clear()
}

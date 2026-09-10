/**
 * rate_limiter.ts — Per-key MCP rate limiter.
 *
 * Two-tier enforcement per MCP_BRIEF §4.4 (Risk R3 mitigation):
 *
 *   1. RPM (requests per minute): in-process rolling window using a Map.
 *      No external dependency. Each entry: {count, window_start_ms}.
 *      Window resets once the 60-second window expires.
 *      Default limit: 60 RPM per key. Configurable via MCP_RPM_LIMIT env var.
 *
 *   2. Daily token budget: queried from query_trace_steps WHERE key_id = $1
 *      AND created_at >= now()::date. Tokens are computed from the payload
 *      token_estimate field. No new DB column required.
 *      Default: 500,000 tokens/day. Configurable via MCP_DAILY_TOKEN_BUDGET env var.
 *
 * NOTE: The in-process RPM counter resets on service restart. For multi-instance
 * production deployments, replace this Map with a Redis-based counter (Phase 2
 * hardening). The daily token budget check is always DB-backed and thus
 * safe across instances.
 *
 * @module rate_limiter
 */

import { query } from '@/lib/db/client'
import type { McpErrorEnvelope } from '@/lib/mcp/types'
import { checkRpm, RPM_LIMIT } from '@/lib/mcp/rate_limiter_core'

// ── Configuration ─────────────────────────────────────────────────────────────
//
// RPM_LIMIT and the rolling-window counter now live in `rate_limiter_core.ts` so
// the request proxy (`src/proxy.ts`, Paripraśna lane G1-D / NCD-8) can reuse the
// SAME counter without importing this module's pg client. Same algorithm, same
// Map, one implementation — see that file's header for why it was split out.

/** Maximum daily token budget per key. */
const DAILY_TOKEN_BUDGET = parseInt(process.env.MCP_DAILY_TOKEN_BUDGET ?? '500000', 10)

// ── Daily token budget check ──────────────────────────────────────────────────

/**
 * Compute daily token usage for a key_id from query_trace_steps.
 * Sums token_estimate values from payload items for today's date.
 * Returns 0 on any DB error (fail-open — rate limiting is best-effort).
 */
async function getDailyTokenUsage(key_id: string): Promise<number> {
  try {
    // The payload column is JSONB with structure: {items: [{token_estimate, ...}]}.
    // We sum the token_estimate from items stored for MCP calls tagged with this key_id.
    // The key_id is stored in the payload items text field as JSON.
    const { rows } = await query<{ total: string }>(
      `SELECT COALESCE(
         SUM(
           COALESCE(
             (elem->>'token_estimate')::numeric,
             0
           )
         ),
         0
       )::text AS total
       FROM query_trace_steps qts,
            LATERAL jsonb_array_elements(
              CASE WHEN qts.payload IS NOT NULL AND qts.payload ? 'items'
                   THEN qts.payload->'items'
                   ELSE '[]'::jsonb END
            ) AS elem
       WHERE qts.created_at >= CURRENT_DATE
         AND qts.payload IS NOT NULL
         AND EXISTS (
           SELECT 1
           FROM jsonb_array_elements(qts.payload->'items') AS check_elem
           WHERE check_elem->>'text' LIKE $1
         )`,
      [`%"key_id":"${key_id}"%`]
    )
    return parseFloat(rows[0]?.total ?? '0') || 0
  } catch (err) {
    // Fail-open: if we can't check, allow the request (log the issue)
    console.warn('[mcp:rate_limiter] Daily token usage query failed; failing open', err)
    return 0
  }
}

// ── Exported types ────────────────────────────────────────────────────────────

export interface RateLimitResult {
  allowed: boolean
  reason?: 'rpm_exceeded' | 'daily_budget_exceeded'
  retry_after_seconds?: number
}

// ── Main export ───────────────────────────────────────────────────────────────

/**
 * Check rate limits for a key_id before processing an MCP request.
 *
 * @param key_id          The MCP key ID to check (from resolved principal).
 * @param estimated_tokens Optional pre-execution token estimate. If provided,
 *                          used for budget pre-check. For ask_madhav, pass 4000
 *                          as a conservative estimate (actual is deducted post-synthesis
 *                          via trace step logging).
 * @returns RateLimitResult indicating whether the request is allowed.
 */
export async function checkRateLimit(
  key_id: string,
  estimated_tokens?: number
): Promise<RateLimitResult> {
  // Step 1: RPM check (synchronous, in-process)
  const rpmResult = checkRpm(key_id)
  if (!rpmResult.allowed) {
    return {
      allowed: false,
      reason: 'rpm_exceeded',
      retry_after_seconds: rpmResult.retry_after_seconds,
    }
  }

  // Step 2: Daily token budget check (async, DB-backed)
  if (estimated_tokens !== undefined && estimated_tokens > 0) {
    const dailyUsed = await getDailyTokenUsage(key_id)
    if (dailyUsed + estimated_tokens > DAILY_TOKEN_BUDGET) {
      return {
        allowed: false,
        reason: 'daily_budget_exceeded',
        retry_after_seconds: undefined,
      }
    }
  }

  return { allowed: true }
}

// ── Error envelope builder ────────────────────────────────────────────────────

/**
 * Build a rate-limit error envelope for returning as an HTTP response body.
 * Returns the standard MCP_BRIEF §4.2 error envelope shape.
 */
export function buildRateLimitErrorEnvelope(reason: string): McpErrorEnvelope {
  const isRpm = reason === 'rpm_exceeded'
  return {
    ok: false,
    trace_id: '',
    error: {
      class: 'rate_limit',
      message: isRpm
        ? `Rate limit exceeded: too many requests per minute (limit: ${RPM_LIMIT} RPM).`
        : `Rate limit exceeded: daily token budget exhausted (limit: ${DAILY_TOKEN_BUDGET.toLocaleString()} tokens/day).`,
      remediation: 'Reduce request frequency or contact admin to raise limits.',
    },
  }
}

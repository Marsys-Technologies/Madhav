/**
 * rate_limiter.ts — In-process per-key rate limiter for the MCP sidecar (M8).
 *
 * This module enforces a request-per-minute (RPM) cap at the MCP dispatch layer
 * in server.ts so that EVERY tool is rate-limited, regardless of whether it goes
 * through the registry/primitives path (which has its own DB-backed limiter on
 * the platform side) or the sidecar-direct path.
 *
 * Design:
 *   - In-process rolling 60-second window keyed on key_id.
 *   - Default limit: 60 RPM (configurable via MCP_RPM_LIMIT env var).
 *   - On Cloud Run multi-instance: each instance has its own counter.
 *     Global RPM across instances is thus limit × instance_count.
 *     Acceptable for MVP; replace with Redis counter for stricter enforcement.
 *   - The platform-side rate_limiter.ts (in /api/mcp/primitives) remains the
 *     authoritative token-budget limiter; this one adds a fast in-process guard.
 *
 * @module rate_limiter
 */

// ── Configuration ─────────────────────────────────────────────────────────────

/** Maximum requests per 60-second rolling window per key.
 * Reads MCP_RPM_LIMIT env var at module load; defaults to 60.
 * NOTE: process.env access — requires @types/node in tsconfig (pre-existing pattern). */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const RPM_LIMIT = parseInt(((globalThis as any)['process']?.env?.['MCP_RPM_LIMIT'] as string | undefined) ?? '60', 10)

/** Window size in milliseconds. */
const WINDOW_MS = 60_000

// ── Types ─────────────────────────────────────────────────────────────────────

interface RpmEntry {
  count: number
  window_start_ms: number
}

export interface SidecarRateLimitResult {
  allowed: boolean
  retry_after_seconds?: number
}

// ── State ─────────────────────────────────────────────────────────────────────

// Module-level map — persists across requests within the same process.
const rpmCounters = new Map<string, RpmEntry>()

/** Exported for tests only — reset in-process state between test cases. */
export function __resetForTests(): void {
  rpmCounters.clear()
}

// ── Check function ────────────────────────────────────────────────────────────

/**
 * Check and increment the RPM counter for a key_id.
 * Returns allowed=true if within limit; allowed=false with retry_after_seconds if exceeded.
 *
 * Thread-safe within a single V8 event loop (no async; Map ops are synchronous).
 */
export function checkMcpRateLimit(key_id: string): SidecarRateLimitResult {
  const now = Date.now()
  const existing = rpmCounters.get(key_id)

  if (!existing || now - existing.window_start_ms >= WINDOW_MS) {
    // New window (first call or window expired)
    rpmCounters.set(key_id, { count: 1, window_start_ms: now })
    return { allowed: true }
  }

  if (existing.count >= RPM_LIMIT) {
    const elapsed = now - existing.window_start_ms
    const retry_after_seconds = Math.ceil((WINDOW_MS - elapsed) / 1000)
    return { allowed: false, retry_after_seconds }
  }

  existing.count += 1
  return { allowed: true }
}

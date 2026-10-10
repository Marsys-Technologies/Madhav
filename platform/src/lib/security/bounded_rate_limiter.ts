/**
 * bounded_rate_limiter.ts — a fixed-window, per-key request limiter whose memory
 * is BOUNDED (SS N-373 / PR-S1, item 4).
 *
 * WHY NOT `@/lib/mcp/rate_limiter_core` (`checkRpm`)? It is the right algorithm
 * for the door limiter, but its `rpmCounters` Map never evicts: keys are only
 * overwritten when the SAME key returns after its window. For a PUBLIC endpoint
 * whose keys are attacker-reachable (IPs), that is an unbounded-growth primitive.
 * `checkRpm` is shared with proxy.ts and the MCP limiter and is out of scope here
 * (changing it would change behaviour of routes this PR does not list), so the
 * public auth routes get their own limiter with:
 *
 *   - a hard cap, `maxEntries`, on live keys (the map can never exceed it),
 *   - a TTL sweep of expired windows (at most once per window, plus on demand
 *     when the cap is reached),
 *   - oldest-first eviction only when the cap is hit and nothing has expired.
 *
 * Insertion order of a `Map` is the order windows were opened (a key is deleted
 * and re-inserted when its window rolls), so the oldest window is always the
 * first key and a sweep can stop at the first live entry: O(expired), not O(n).
 *
 * Per-instance, like `checkRpm` (Cloud Run runs several instances): the limit is
 * per instance, so the effective ceiling scales with instance count. Evicting the
 * oldest live entry at capacity means a flood from MORE than `maxEntries`
 * distinct trusted IPs can reset a throttled key early; reaching that needs that
 * many real source addresses (IPv6 is keyed by /64, see `ipRateLimitKey`).
 */
export interface BoundedRateLimiterOptions {
  /** Requests allowed per key per window. */
  limit: number
  /** Window length in milliseconds. */
  windowMs: number
  /** Hard cap on live keys. */
  maxEntries: number
  /** Clock, injectable for tests. */
  now?: () => number
}

export interface BoundedRateLimitResult {
  allowed: boolean
  /** Whole seconds until the window rolls; 0 when allowed. */
  retryAfterSeconds: number
}

interface Entry {
  count: number
  windowStart: number
}

export class BoundedRateLimiter {
  private readonly entries = new Map<string, Entry>()
  private readonly limit: number
  private readonly windowMs: number
  private readonly maxEntries: number
  private readonly now: () => number
  private lastSweep = 0

  constructor(opts: BoundedRateLimiterOptions) {
    if (!(opts.limit >= 1) || !(opts.windowMs >= 1) || !(opts.maxEntries >= 1)) {
      throw new Error('BoundedRateLimiter: limit, windowMs and maxEntries must all be >= 1')
    }
    this.limit = opts.limit
    this.windowMs = opts.windowMs
    this.maxEntries = Math.floor(opts.maxEntries)
    this.now = opts.now ?? Date.now
    this.lastSweep = this.now()
  }

  /** Live key count (always <= maxEntries). */
  get size(): number {
    return this.entries.size
  }

  check(key: string): BoundedRateLimitResult {
    const now = this.now()
    if (now - this.lastSweep >= this.windowMs) this.sweep(now)

    const existing = this.entries.get(key)
    if (existing && now - existing.windowStart < this.windowMs) {
      if (existing.count >= this.limit) {
        return {
          allowed: false,
          retryAfterSeconds: Math.max(1, Math.ceil((this.windowMs - (now - existing.windowStart)) / 1000)),
        }
      }
      existing.count += 1
      return { allowed: true, retryAfterSeconds: 0 }
    }

    // New key, or its window has rolled: (re)open a window at the tail.
    if (existing) this.entries.delete(key)
    if (this.entries.size >= this.maxEntries) {
      this.sweep(now)
      while (this.entries.size >= this.maxEntries) {
        const oldest = this.entries.keys().next()
        if (oldest.done) break
        this.entries.delete(oldest.value)
      }
    }
    this.entries.set(key, { count: 1, windowStart: now })
    return { allowed: true, retryAfterSeconds: 0 }
  }

  /** Drop every expired window. Stops at the first live entry (insertion order = window order). */
  private sweep(now: number): void {
    this.lastSweep = now
    for (const [key, entry] of this.entries) {
      if (now - entry.windowStart < this.windowMs) break
      this.entries.delete(key)
    }
  }
}

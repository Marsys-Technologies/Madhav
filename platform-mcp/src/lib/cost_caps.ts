/**
 * cost_caps.ts — Dual cost-cap tracker (call-count + wall-clock), fail-honest.
 *
 * Tracks how many sub-calls a long-running operation (e.g. prashna_ask's
 * engine loop) has made, and how much wall-clock time has elapsed since the
 * tracker was constructed. `checkAndRecordCall()` is called before each
 * sub-call; if either cap has been exceeded it returns `stopped: true` with
 * a `reason` naming which cap tripped and a `judgmentFlag` string carrying
 * that same information machine-readably.
 *
 * This module never truncates silently — a stopped result always carries a
 * `judgmentFlag` so a caller (Task 7's `register_prashna_ask.ts`) can build
 * an honest partial-result response instead of failing silently. Building
 * that response shape is NOT this module's job — this module only tracks
 * and reports.
 */

export interface CostCapConfig {
  maxCalls: number;
  maxWallClockMs: number;
}

export type CostCapStopReason = 'call_count_cap' | 'wall_clock_cap';

export interface CostCapCheckResult {
  stopped: boolean;
  reason?: CostCapStopReason;
  judgmentFlag?: string;
  callsMade: number;
  elapsedMs: number;
}

export class CostCapTracker {
  private calls = 0;
  private readonly startedAt = Date.now();
  private readonly config: CostCapConfig;

  constructor(config: CostCapConfig) {
    this.config = config;
  }

  /**
   * Check both caps and, if neither has tripped, record a call.
   *
   * Wall-clock is checked first — it can trip independent of call count
   * (e.g. a single sub-call that itself runs long). Call-count is checked
   * second. Only when neither cap has tripped does this increment the
   * internal call counter and return `stopped: false`.
   */
  checkAndRecordCall(): CostCapCheckResult {
    const elapsedMs = Date.now() - this.startedAt;
    if (elapsedMs > this.config.maxWallClockMs) {
      return {
        stopped: true,
        reason: 'wall_clock_cap',
        judgmentFlag: 'cost_cap_wall_clock_exceeded',
        callsMade: this.calls,
        elapsedMs,
      };
    }
    if (this.calls >= this.config.maxCalls) {
      return {
        stopped: true,
        reason: 'call_count_cap',
        judgmentFlag: 'cost_cap_call_count_exceeded',
        callsMade: this.calls,
        elapsedMs,
      };
    }
    this.calls += 1;
    return { stopped: false, callsMade: this.calls, elapsedMs };
  }
}

/**
 * Default cost caps, applied to the base 'guest' entitlement tier and to any
 * tier without an explicit override in `resolveCostCapsForEntitlement`.
 *
 * maxWallClockMs=120_000 confirmed against W4's measured worst-case
 * synthesis timings (see `00_ARCHITECTURE/briefs/retrieval_impl/STATE.md` and
 * `platform/src/lib/pipeline/__tests__/prashna_ask_spike.test.ts`) — the
 * recorded worst case is well under 80% of this budget, so no calibration
 * bump is needed (see Task 3 note in commit history).
 */
export const DEFAULT_COST_CAPS: CostCapConfig = {
  maxCalls: 10,
  maxWallClockMs: 120_000,
};

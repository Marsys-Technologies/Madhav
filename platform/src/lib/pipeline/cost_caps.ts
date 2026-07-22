import type { Principal } from '@/lib/auth/authorizeChartAccess'

/**
 * cost_caps.ts — Dual cost-cap tracker (call-count + wall-clock), fail-honest.
 *
 * Ported into `platform/src` from the original `platform-mcp/src/lib/cost_caps.ts`
 * attempt (W6 module-placement correction — see
 * `00_ARCHITECTURE/briefs/retrieval_impl/STATE.md`). The engine's tool-call loop
 * (prashna_ask's new internal route, `/api/chat/consult/route.ts`'s existing loop)
 * runs entirely inside the `platform` deployable, so this is where the cap must be
 * tracked and enforced — `platform-mcp` has no access to that loop.
 *
 * Entitlement vocabulary: `platform-mcp`'s `Principal.role` was `'guest' |
 * 'super_admin'`. On the `platform` side, the equivalent role vocabulary is
 * `authorizeChartAccess.ts`'s own `Principal.role` — ALSO exactly `'guest' |
 * 'super_admin'` (see `platform/src/lib/mcp/auth.ts`'s `resolveMcpPrincipalRole()`,
 * which resolves this same two-value role from the `profiles` table and is the
 * function every /api/mcp/* route — including the new prashna_ask route — calls to
 * get it). The two types are independently declared (no shared import boundary
 * between the deployables) but the literal union is identical; this file imports
 * the `platform`-side `Principal` type rather than redeclaring a third copy.
 *
 * Tracks how many sub-calls a long-running operation (e.g. prashna_ask's engine
 * loop) has made, and how much wall-clock time has elapsed since the tracker was
 * constructed. `checkAndRecordCall()` is called before each sub-call; if either cap
 * has been exceeded it returns `stopped: true` with a `reason` naming which cap
 * tripped and a `judgmentFlag` string carrying that same information machine-readably.
 *
 * This module never truncates silently — a stopped result always carries a
 * `judgmentFlag` so a caller (the prashna_ask route) can build an honest
 * partial-result response instead of failing silently. Building that response
 * shape is NOT this module's job — this module only tracks and reports.
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
 * synthesis timings (see `00_ARCHITECTURE/briefs/retrieval_impl/STATE.md`)
 * — the recorded worst case is well under 80% of this budget, so no calibration
 * bump is needed. Value ported unchanged from the platform-mcp attempt and
 * carried forward into the real `platform/src/app/api/mcp/prashna_ask/route.ts`
 * (see its test suite at `platform/src/app/api/mcp/prashna_ask/__tests__/route.test.ts`),
 * which superseded the retired `prashna_ask_spike.ts` reference implementation.
 */
export const DEFAULT_COST_CAPS: CostCapConfig = {
  maxCalls: 10,
  maxWallClockMs: 120_000,
};

/**
 * Per-tier cap overrides, keyed by the exact `Principal.role` vocabulary from
 * `platform/src/lib/auth/authorizeChartAccess.ts`. Hoisted to module scope so it
 * isn't reallocated on every `resolveCostCapsForEntitlement` call.
 *
 * 'super_admin' figures (25 calls / 300s) are a provisional 2.5x allowance for
 * operator diagnostic/multi-pass sessions — NOT empirically calibrated like
 * `DEFAULT_COST_CAPS` (which cites a measured W4 worst case). Revisit once real
 * super_admin prashna_ask usage data exists.
 */
const COST_CAP_OVERRIDES_BY_ENTITLEMENT: Partial<Record<Principal['role'], CostCapConfig>> = {
  super_admin: {
    maxCalls: 25,
    maxWallClockMs: 300_000,
  },
};

/**
 * Per-entitlement cost-cap resolution (ratified doctrine: both caps must be
 * configurable per entitlement, not a single global default).
 *
 * Tier names are the exact `Principal.role` vocabulary from
 * `platform/src/lib/auth/authorizeChartAccess.ts` — 'guest' | 'super_admin'. Do not
 * invent new tier names here; if a new tier is ever needed, add it to `Principal.role`
 * first and mirror it here.
 *
 * 'guest' gets `DEFAULT_COST_CAPS` (the base full-loop entitlement tier).
 * 'super_admin' gets a higher allowance — see the override table's comment.
 *
 * Accepts `Principal['role'] | string` — the literal union gives callers
 * compile-time checking for the real tier vocabulary, while the wider `string`
 * fallback (falling back to `DEFAULT_COST_CAPS` for anything unrecognized) is
 * intentional defense-in-depth, not a typing gap.
 */
export function resolveCostCapsForEntitlement(
  entitlement: Principal['role'] | (string & {})
): CostCapConfig {
  return COST_CAP_OVERRIDES_BY_ENTITLEMENT[entitlement as Principal['role']] ?? DEFAULT_COST_CAPS;
}

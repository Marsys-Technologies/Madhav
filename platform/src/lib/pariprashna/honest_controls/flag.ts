/**
 * Paripraśna honest controls — the ONE flag read site (lane P2-C, PPR-09/16).
 *
 * Same shape as `injection/flag.ts`/`safety/flag.ts`/`consent/flag.ts`: every
 * call site routes through `isHonestControlsEnabled()` rather than reading the
 * flag directly, so "nothing here is reachable until the flag is ON" is one
 * line, not several independently-armed halves.
 *
 * What this flag arms (see `feature_flags.ts` for the full account):
 *   · real length shaping in synthesis for `length_tier: brief | exhaustive`
 *     (`synthesis_stage.assembleSynthesisContext`);
 *   · the `reading_depth_received` disclosure grade, derived from the
 *     planner's `plan.scope_tuple.depth` (`plan_stage.ts`).
 *
 * `model_id` plumbing is NOT gated here — `bindTurnParams` already binds it
 * for real regardless of this flag (see the flag's own declaration comment in
 * `feature_flags.ts`); only the composer UI needed fixing, unconditionally.
 */

import { configService } from '@/lib/config/index'

/** The feature flag that arms honest-controls behavior. Default OFF. */
export const HONEST_CONTROLS_FLAG = 'PARIPRASHNA_HONEST_CONTROLS_ENABLED' as const

export function isHonestControlsEnabled(): boolean {
  return configService.getFlag(HONEST_CONTROLS_FLAG)
}

/**
 * Paripraśna injection containment — the ONE flag read site (lane G1-G, PPR-13).
 *
 * Same shape as `safety/flag.ts` and `consent/flag.ts`, and for the same reason:
 * every entry point in this directory routes its gate through
 * `isInjectionContainmentEnabled()` rather than reading the flag itself, so
 * "nothing here is reachable until the flag is ON" is enforced at one line
 * instead of a dozen, and a test can prove it by that one line.
 *
 * ── WHY A CONTAINMENT CONTROL SHIPS OFF ──────────────────────────────────────
 * Two of the four controls in this lane CHANGE THE MODEL'S INPUT: the question,
 * the retrieved evidence, the conversation history and every agentic tool result
 * get wrapped in structural delimiters with an explicit data-not-instruction
 * clause. That is the correct containment posture AND a real change to what the
 * synthesis model sees, which means it can move prose. The P1 pre-authorization
 * note therefore ships it dark: merging cannot alter production behaviour, and
 * the flip is a deliberate act at P1 close.
 *
 * The other two controls (plan closure, tool-sequence anomaly trace) are
 * detection-only or reject-only and would be safe hot; they are gated on the
 * same flag anyway so that "injection containment is on" is ONE question with
 * ONE answer, not four independently-armed halves.
 */

import { configService } from '@/lib/config/index'

/** The feature flag that arms every behavior in this directory. Default OFF. */
export const INJECTION_CONTAINMENT_FLAG = 'PARIPRASHNA_INJECTION_CONTAINMENT' as const

export function isInjectionContainmentEnabled(): boolean {
  return configService.getFlag(INJECTION_CONTAINMENT_FLAG)
}

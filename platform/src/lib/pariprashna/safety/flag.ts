/**
 * Paripraśna safety — the ONE flag read site (lane G1-A).
 *
 * Same shape as `consent/flag.ts` and for the same reason: every entry point in
 * this directory routes its gate through `isSafetyGateEnabled()` rather than
 * reading the flag itself, so "nothing here is reachable until the flag is ON"
 * is enforced at one line instead of a dozen, and a test can prove it by that
 * one line.
 *
 * ── WHY A SAFETY CONTROL SHIPS OFF ───────────────────────────────────────────
 * This looks backwards until you read what ON does. With the gate ON, a
 * health-crisis or mortality-window question on a chart whose subject is not
 * provably `native_self` produces NO reading at all until a human signs it off
 * (MP §3.5.C: "explicit native sign-off before any output leaves a session").
 * That is the correct fail-closed direction AND a real serving change. The P1
 * pre-authorization note therefore ships it dark: merging cannot alter
 * production behaviour, and the flip is a deliberate act at P1 close.
 */

import { configService } from '@/lib/config/index'

/** The feature flag that arms every behavior in this directory. Default OFF. */
export const SAFETY_GATE_FLAG = 'PARIPRASHNA_SAFETY_GATE_ENABLED' as const

export function isSafetyGateEnabled(): boolean {
  return configService.getFlag(SAFETY_GATE_FLAG)
}

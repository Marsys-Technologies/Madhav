/**
 * Paripraśna consent — the ONE flag read site.
 *
 * Every entry point in this directory routes its gate through
 * `isConsentEnforcementEnabled()` rather than reading the flag itself, so
 * "nothing here is reachable until the flag is ON" is enforced at one line
 * instead of five, and a test can prove it by that one line.
 *
 * It reads `configService.getFlag` rather than the bare `getFlag` helper on
 * purpose: that is the idiom the serving path already uses (`safety_gate.ts`,
 * `clients/[id]/pariprashna/page.tsx`), and this module is imported from inside
 * the serving path.
 */

import { configService } from '@/lib/config/index'

/** The feature flag that arms every behavior in this directory. Default OFF. */
export const CONSENT_FLAG = 'SUBJECT_CONSENT_ENFORCEMENT' as const

export function isConsentEnforcementEnabled(): boolean {
  return configService.getFlag(CONSENT_FLAG)
}

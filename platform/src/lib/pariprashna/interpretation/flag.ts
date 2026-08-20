/**
 * Paripraśna interpretation sets — the ONE flag read site (lane G3-B, PPR-02).
 *
 * Same shape as `receipt/flag.ts` / `semantics/flag.ts` / `injection/flag.ts`:
 * every call site routes through `isInterpretationSetsEnabled()` rather than
 * reading the flag directly.
 */

import { configService } from '@/lib/config/index'

/** The feature flag that arms significant-judgment detection + interpretation-set
 *  generation. Default OFF. Depends on PARIPRASHNA_RECEIPT_EMISSION_ENABLED
 *  (G3-A) — interpretation sets ride as an additive sub-field of the receipt. */
export const INTERPRETATION_SETS_FLAG = 'PARIPRASHNA_INTERPRETATION_SETS_ENABLED' as const

export function isInterpretationSetsEnabled(): boolean {
  return configService.getFlag(INTERPRETATION_SETS_FLAG)
}

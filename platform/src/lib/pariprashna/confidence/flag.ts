/**
 * Paripraśna typed confidence — the ONE flag read site (lane G3-C, PPR-03).
 *
 * Same shape as `receipt/flag.ts` / `injection/flag.ts` / `safety/flag.ts` /
 * `citations/flag.ts` / `honest_controls/flag.ts`: every call site routes
 * through `isTypedConfidenceEnabled()` rather than reading the flag directly.
 */

import { configService } from '@/lib/config/index'

/** The feature flag that arms PPR-03 confidence typing on the receipt. Default OFF. */
export const TYPED_CONFIDENCE_FLAG = 'PARIPRASHNA_TYPED_CONFIDENCE_ENABLED' as const

export function isTypedConfidenceEnabled(): boolean {
  return configService.getFlag(TYPED_CONFIDENCE_FLAG)
}

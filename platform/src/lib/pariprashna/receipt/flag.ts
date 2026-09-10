/**
 * Paripraśna receipt emission — the ONE flag read site (lane G3-A, PPR-01).
 *
 * Same shape as `injection/flag.ts` / `safety/flag.ts` / `citations/flag.ts` /
 * `honest_controls/flag.ts`: every call site routes through
 * `isReceiptEmissionEnabled()` rather than reading the flag directly.
 */

import { configService } from '@/lib/config/index'

/** The feature flag that arms `AcharyaReadingReceipt` assembly + persistence. Default OFF. */
export const RECEIPT_EMISSION_FLAG = 'PARIPRASHNA_RECEIPT_EMISSION_ENABLED' as const

export function isReceiptEmissionEnabled(): boolean {
  return configService.getFlag(RECEIPT_EMISSION_FLAG)
}

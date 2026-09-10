/**
 * Paripraśna semantic blocks — the ONE flag read site (lane P2-A, PPR-07/FD-1).
 *
 * Same shape as `injection/flag.ts` and `consent/flag.ts`, and for the same
 * reason: every entry point in this directory (the block classifier, and the
 * persistence stage's `prediction_card` emission) routes its gate through
 * `isSemanticBlocksEnabled()` rather than reading the flag itself, so
 * "nothing here is reachable until the flag is ON" is enforced at one line
 * and a test can prove it by that one line.
 *
 * Ships OFF: commit-time classification is a real change to what the wire
 * carries (new optional fields on `block.commit`, plus the new
 * `prediction_card` event type) — safe additively, but the deliberate flip
 * happens after the client renderers have been verified against a real
 * deployed reading, not automatically on merge.
 */

import { configService } from '@/lib/config/index'

/** The feature flag that arms commit-time block classification + the
 *  `prediction_card` wire event. Default OFF. */
export const SEMANTIC_BLOCKS_FLAG = 'PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED' as const

export function isSemanticBlocksEnabled(): boolean {
  return configService.getFlag(SEMANTIC_BLOCKS_FLAG)
}

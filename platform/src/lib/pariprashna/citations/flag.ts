/**
 * Paripraśna citations-at-first-paint — the ONE flag read site (lane G2-B,
 * PPR-08/FD-2/FD-6).
 *
 * Same shape as `injection/flag.ts` and `safety/flag.ts`: every call site
 * that wires the live `CitationStreamRewriter` into the synthesis stream
 * routes through `isFirstPaintCitationsEnabled()` rather than reading the
 * flag itself, so "is the new citation path live" is one question with one
 * answer.
 */

import { configService } from '@/lib/config/index'

/** The feature flag that arms the live citation-rewriter wiring. Default OFF. */
export const FIRST_PAINT_CITATIONS_FLAG = 'PARIPRASHNA_FIRST_PAINT_CITATIONS_ENABLED' as const

export function isFirstPaintCitationsEnabled(): boolean {
  return configService.getFlag(FIRST_PAINT_CITATIONS_FLAG)
}

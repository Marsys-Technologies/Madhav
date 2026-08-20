/**
 * Paripraśna voice enforcement — the ONE flag read site (lane G3-D / P2-L,
 * PPR-04 / roadmap line 104). Same shape as `injection/flag.ts`,
 * `semantics/flag.ts`, `citations/flag.ts` and `consent/flag.ts`: every entry
 * point in this directory routes its gate through `isVoiceEnforcementEnabled()`
 * rather than reading the flag itself, so "is voice enforcement live" is one
 * question with one answer, and a test can prove it by that one line.
 *
 * Ships OFF: `lintVoiceProse` (voice_lint.ts) and the pacing helpers
 * (pacing.ts) are pure functions with no I/O of their own, but the two call
 * sites that invoke them — the per-delta lint in `pipeline/synthesis_stage.ts`
 * (both the citation-stream-on and citation-stream-off branches) and the
 * whole-block backstop in `pipeline/reading_parts.ts`'s `commitBlock()` — are
 * gated behind this flag exactly like the register-leak lint's own G1-A/G1-G
 * neighbors, so flag-off is byte-for-byte what streaming and persistence do
 * today.
 */

import { configService } from '@/lib/config/index'

/** The feature flag that arms voice enforcement. Default OFF. */
export const VOICE_ENFORCEMENT_FLAG = 'PARIPRASHNA_VOICE_ENFORCEMENT_ENABLED' as const

export function isVoiceEnforcementEnabled(): boolean {
  return configService.getFlag(VOICE_ENFORCEMENT_FLAG)
}

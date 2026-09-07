/**
 * The window-opening ask — the ONE flag read site (lane P4-G).
 *
 * Same shape and same reason as `semantics/flag.ts`, `voice/flag.ts` and every other
 * Paripraśna sub-feature gate: every entry point in this directory routes its gate through
 * `isWindowAskEnabled()` rather than reading the environment itself, so "nothing here is
 * reachable until the flag is ON" is enforced at one line and a test can prove it by that one
 * line.
 *
 * Ships OFF. An unsolicited sentence is the single most intrusive thing this instrument can do
 * to a reader, so it does not turn itself on at merge.
 *
 * ── WHY THIS READS `process.env` DIRECTLY, unlike its sibling flag modules ──────────────────
 * The sibling modules call `configService.getFlag(NAME)`, whose `FeatureFlag` union lives in
 * `src/lib/config/feature_flags.ts`. That file is OUTSIDE lane P4-G's declared `may_touch`
 * (`platform/src/lib/pariprashna/**`), and widening a lane's scope to register a flag is not a
 * thing a lane may authorize for itself. So this module reproduces the config service's OWN
 * env-override convention exactly — same `FLAG_ENV_PREFIX`, same `=== 'true'` comparison, same
 * default-false — by importing the prefix constant rather than re-typing it. Behaviour is
 * identical to a registered flag whose default is `false`; the only thing missing is the
 * central registry entry.
 *
 * FOLLOW-UP (one line, outside this lane's scope): add
 * `'PARIPRASHNA_WINDOW_ASK_ENABLED'` to the `FeatureFlag` union + `DEFAULT_FLAGS: false` in
 * `src/lib/config/feature_flags.ts`, then swap the body below for
 * `configService.getFlag(WINDOW_ASK_FLAG)`. No behaviour changes when that happens.
 */

import { FLAG_ENV_PREFIX } from '@/lib/config/feature_flags'

/** The feature flag that arms the window-opening ask + its `window_ask` wire event. OFF. */
export const WINDOW_ASK_FLAG = 'PARIPRASHNA_WINDOW_ASK_ENABLED' as const

/** The full environment variable name the flag is overridden by (`MARSYS_FLAG_…`). */
export const WINDOW_ASK_FLAG_ENV = `${FLAG_ENV_PREFIX}${WINDOW_ASK_FLAG}` as const

export function isWindowAskEnabled(): boolean {
  return (process.env[WINDOW_ASK_FLAG_ENV] ?? '').toLowerCase() === 'true'
}

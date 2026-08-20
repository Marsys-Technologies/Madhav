/**
 * Paripraśna typed confidence — barrel (lane G3-C, PPR-03).
 *
 * `receipt/assemble.ts` imports the typing function + activation gate +
 * precision scan from here; nothing in the serving path should need a
 * deeper path than this module.
 */

export * from './types'
export * from './flag'
export * from './activation_gate'
export * from './engine_tier'
export * from './precision_scan'
export * from './type_claim'

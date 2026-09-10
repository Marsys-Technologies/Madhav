/**
 * Paripraśna interpretation sets — barrel (lane G3-B, PPR-02).
 *
 * `pipeline/persistence_stage.ts` imports the detector + generator +
 * assembler + flag from here; nothing in the serving path should need a
 * deeper path than this module.
 */

export * from './schema'
export * from './flag'
export * from './detect'
export * from './worker'
export * from './assemble'

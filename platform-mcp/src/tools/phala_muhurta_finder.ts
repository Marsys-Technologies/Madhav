/**
 * phala_muhurta_finder.ts — Re-export shim for BRAHMA-PH-4-4.
 *
 * The canonical implementation lives in muhurta_finder.ts (required by
 * server_tier_visibility.test.ts import path: '../tools/muhurta_finder.js').
 *
 * This shim satisfies the task contract path
 *   platform-mcp/src/tools/phala_muhurta_finder.ts
 * while keeping a single implementation.
 *
 * BRAHMA-PH-4-4
 */

export {
  MuhurtaFinderInputSchema,
  MUHURTA_FINDER_DESCRIPTION,
  handleMuhurtaFinder,
  registerMuhurtaFinder,
} from './muhurta_finder.js'

export type {
  MuhurtaFinderInput,
  MuhurtaFactors,
  MuhurtaWindow,
  MuhurtaProvenanceEnvelope,
  MuhurtaFinderResult,
} from './muhurta_finder.js'

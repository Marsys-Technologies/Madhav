/**
 * synthesis/ — Large-N Synthesis Instrument (WP-1.4 / LCA-15 / R-48): public API + registration
 * ==============================================================================================
 * The staged retrieval-with-aggregation instrument that composes N-hundred factors without a
 * flat top-K wall. Registered as one capability (compose_large_n) so the pre-aggregated L2
 * surfaces finally have a consumer. Wired into the unified catalog via a single import in
 * registry/catalog.ts (GATE A).
 */

import { registerCapability } from '../registry/index'
import { synthComposeLargeNCapability } from './capability'

registerCapability(synthComposeLargeNCapability)

export { composeLargeN } from './instrument'
export type { ComposeParams } from './instrument'
export { decompose } from './intent'
export { RegistrySurfaceGateway } from './surface_gateway'
export type { SurfaceGateway } from './surface_gateway'
export { synthComposeLargeNCapability } from './capability'
export type {
  LargeNAnswer, EvidenceContract, FamilyComposite, DerivationLedgerEntry,
  NarrativeSection, StageBudget, Domain,
} from './types'

/**
 * DEPRECATED compatibility surface for the L0 slice of the receipt spine.
 *
 * The spine is now layer-generic — see `./nirmana-analysis-receipts.ts`
 * (adjudication #1715, Conductor ruling, Option A). New code must import from
 * there and pass an explicit layer.
 *
 * This module is retained, and its exports are DERIVED rather than restated, so
 * that the pre-existing L0 tests continue to run verbatim against the
 * generalised implementation. That is deliberate: those tests are the detector
 * for the ruling's requirement 3 — L0's pinned constants stay byte-identical and
 * no L0 analysis is re-accepted. A shim that hardcoded the old values would
 * assert nothing; one that derives them fails loudly if the generalisation moved
 * L0 even slightly.
 */
import {
  NIRMANA_ANALYSIS_LAYER_PINS,
  NIRMANA_ANALYSIS_RECEIPTS,
  NIRMANA_FROZEN_MANIFEST_SOURCE,
  assertNirmanaWriterInventoryMatchesConvergence,
  getNirmanaAnalysisReceiptBase,
  nirmanaAnalysisReceiptsAvailable,
  type NirmanaAnalysisReceiptBase,
} from './nirmana-analysis-receipts'

export const NIRMANA_L0_CONVERGENCE_COMMIT = NIRMANA_ANALYSIS_LAYER_PINS.L0.convergence_commit
export const NIRMANA_L0_ANALYSIS_RECEIPT_COUNT = NIRMANA_ANALYSIS_LAYER_PINS.L0.receipt_count
export const NIRMANA_L0_WRITER_INVENTORY_SHA256 = NIRMANA_ANALYSIS_LAYER_PINS.L0.writer_inventory_sha256
export const NIRMANA_L0_FROZEN_MANIFEST_SOURCE = NIRMANA_FROZEN_MANIFEST_SOURCE

export type NirmanaL0AnalysisReceiptBase = NirmanaAnalysisReceiptBase

export function assertNirmanaL0WriterInventoryMatchesConvergence(inventory: unknown): asserts inventory is Record<string, string> {
  assertNirmanaWriterInventoryMatchesConvergence('L0', inventory)
}

export const NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE = nirmanaAnalysisReceiptsAvailable('L0')
export const NIRMANA_L0_ANALYSIS_RECEIPTS = NIRMANA_ANALYSIS_RECEIPTS.L0

export function getNirmanaL0AnalysisReceiptBase(assetId: string): Readonly<NirmanaAnalysisReceiptBase> | undefined {
  return getNirmanaAnalysisReceiptBase(assetId, 'L0')
}

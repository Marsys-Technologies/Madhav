import { createHash } from 'node:crypto'
import writerDigestInventory from './nirmana-writer-digests.json'
import layerPinRecord from './nirmana-analysis-layer-pins.json'

/**
 * Nirmāṇa asset-analysis receipt bases, for every layer.
 *
 * Generalised from the original L0-only module per adjudication #1715 (Conductor
 * ruling, Option A).  Before that, `asset_analysis_accepted` /
 * `optimization_verdict_accepted` were structurally unreachable for L1–L5, so 88
 * assets across five layers could not satisfy E-gate condition 2.
 *
 * Two properties are conditions of merge, not conveniences:
 *
 *  1. **Fail closed PER LAYER.** Each layer carries its own convergence commit
 *     and its own writer-inventory aggregate.  A writer edit invalidates only
 *     that layer's receipts.  A single global pin would let any layer's writer
 *     fix silently invalidate every other layer's accepted analyses.
 *  2. **The digest stays a real detector.** `analysis_digest` binds the receipt
 *     base, the frozen manifest asset, and the live registry contract.  Drop any
 *     of the three and C2 condition 3 stops being able to fail.
 *
 * The pin record is generated, not hand-maintained — see
 * `platform/scripts/generate/nirmana_analysis_layer_pins.py`.  A committed
 * generated file with no generator is the defect that produced the
 * convergence-pin drift recorded in CAMPAIGN_STATE; `--check` now re-derives
 * every claim in it offline.
 */

export const NIRMANA_ANALYSIS_LAYERS = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5'] as const
export type NirmanaAnalysisLayer = (typeof NIRMANA_ANALYSIS_LAYERS)[number]

// A durable receipt identifier, not a SQL relation reference.  Keeps existing
// accepted L0 bases stable after the physical table moved into the
// nirmana_evidence schema; the evidence parser resolves both identifiers.
export const NIRMANA_FROZEN_MANIFEST_SOURCE = 'nirmana_elevation_campaign_definitions.manifest' as const
export const NIRMANA_WRITER_DIGEST_REF = 'platform/src/generated/nirmana-writer-digests.json' as const

export interface NirmanaAnalysisReceiptBase {
  schema_version: 'nirmana-asset-analysis-receipt-base/v1'
  asset_id: string
  layer: NirmanaAnalysisLayer
  writer_digest_sha256: string | null
  grounding: {
    convergence_commit: string
    frozen_manifest_source: typeof NIRMANA_FROZEN_MANIFEST_SOURCE
    writer_digest_ref: typeof NIRMANA_WRITER_DIGEST_REF
  }
}

interface LayerPin {
  asset_prefix: string
  convergence_commit: string
  writer_inventory_sha256: string
  receipt_count: number
  non_writer_assets: readonly string[]
}

const layerPins = layerPinRecord.layers as Record<NirmanaAnalysisLayer, LayerPin>

export const NIRMANA_ANALYSIS_LAYER_PINS: Readonly<Record<NirmanaAnalysisLayer, Readonly<LayerPin>>> =
  Object.freeze(Object.fromEntries(
    NIRMANA_ANALYSIS_LAYERS.map((layer) => [layer, Object.freeze(layerPins[layer])]),
  )) as Readonly<Record<NirmanaAnalysisLayer, Readonly<LayerPin>>>

/**
 * Assert one layer's slice of the writer inventory still equals its pinned
 * aggregate.  Throws on drift — the per-layer fail-closed gate.
 */
export function assertNirmanaWriterInventoryMatchesConvergence(
  layer: NirmanaAnalysisLayer,
  inventory: unknown,
): asserts inventory is Record<string, string> {
  const pin = NIRMANA_ANALYSIS_LAYER_PINS[layer]
  const drift = new Error(`Nirmana ${layer} writer inventory does not match the pinned convergence inventory.`)
  if (inventory === null || typeof inventory !== 'object' || Array.isArray(inventory)) throw drift
  const layerInventory = Object.fromEntries(Object.entries(inventory)
    .filter(([assetId]) => assetId.startsWith(pin.asset_prefix))
    .sort(([left], [right]) => left.localeCompare(right)))
  if (Object.values(layerInventory).some((digest) => typeof digest !== 'string' || !/^[a-f0-9]{64}$/.test(digest))) {
    throw drift
  }
  if (createHash('sha256').update(JSON.stringify(layerInventory)).digest('hex') !== pin.writer_inventory_sha256) {
    throw drift
  }
}

const writerDigestsCandidate = writerDigestInventory.writers as unknown

function resolveLayerInventory(layer: NirmanaAnalysisLayer): Record<string, string> | null {
  try {
    assertNirmanaWriterInventoryMatchesConvergence(layer, writerDigestsCandidate)
    return writerDigestsCandidate as Record<string, string>
  } catch {
    // Writer corrections may be deployed before a new durable-main convergence
    // receipt is ratified.  Keep the service available, but make evidence
    // creation fail closed for THAT LAYER ONLY until its pin is advanced.
    return null
  }
}

function buildLayerReceipts(layer: NirmanaAnalysisLayer): Readonly<Record<string, Readonly<NirmanaAnalysisReceiptBase>>> {
  const pin = NIRMANA_ANALYSIS_LAYER_PINS[layer]
  const inventory = resolveLayerInventory(layer)
  if (inventory === null) return Object.freeze({})
  const assetIds = [
    ...Object.keys(inventory).filter((assetId) => assetId.startsWith(pin.asset_prefix)),
    ...pin.non_writer_assets,
  ].sort()
  if (assetIds.length !== pin.receipt_count) {
    throw new Error(`Expected ${pin.receipt_count} frozen ${layer} analysis receipt bases; found ${assetIds.length}.`)
  }
  return Object.freeze(Object.fromEntries(assetIds.map((assetId) => [assetId, Object.freeze({
    schema_version: 'nirmana-asset-analysis-receipt-base/v1',
    asset_id: assetId,
    layer,
    writer_digest_sha256: inventory[assetId] ?? null,
    grounding: {
      convergence_commit: pin.convergence_commit,
      frozen_manifest_source: NIRMANA_FROZEN_MANIFEST_SOURCE,
      writer_digest_ref: NIRMANA_WRITER_DIGEST_REF,
    },
  } satisfies NirmanaAnalysisReceiptBase)])))
}

export const NIRMANA_ANALYSIS_RECEIPTS: Readonly<Record<NirmanaAnalysisLayer, Readonly<Record<string, Readonly<NirmanaAnalysisReceiptBase>>>>> =
  Object.freeze(Object.fromEntries(
    NIRMANA_ANALYSIS_LAYERS.map((layer) => [layer, buildLayerReceipts(layer)]),
  )) as Readonly<Record<NirmanaAnalysisLayer, Readonly<Record<string, Readonly<NirmanaAnalysisReceiptBase>>>>>

export function nirmanaAnalysisReceiptsAvailable(layer: NirmanaAnalysisLayer): boolean {
  return Object.keys(NIRMANA_ANALYSIS_RECEIPTS[layer]).length > 0
}

/**
 * The receipt base for one asset, or undefined.
 *
 * `layer` is REQUIRED and is matched, not inferred: resolving by asset-id alone
 * would let a caller obtain an L1 base while claiming an L2 event, which is
 * exactly the binding the digest exists to enforce.
 */
export function getNirmanaAnalysisReceiptBase(
  assetId: string,
  layer: NirmanaAnalysisLayer,
): Readonly<NirmanaAnalysisReceiptBase> | undefined {
  return NIRMANA_ANALYSIS_RECEIPTS[layer]?.[assetId]
}

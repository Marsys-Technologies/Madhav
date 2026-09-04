import { createHash } from 'node:crypto'
import writerDigestInventory from './nirmana-writer-digests.json'

export const NIRMANA_L0_CONVERGENCE_COMMIT = '49bb5c98b864a2cb2fee037cdb7f14f6892a8263' as const
export const NIRMANA_L0_ANALYSIS_RECEIPT_COUNT = 40 as const
export const NIRMANA_L0_WRITER_INVENTORY_SHA256 = '8650e7a7e85beb27adbb66087344a13f3ee77b3fb1c84ebbb6170b9d7ad1c2ae' as const
// This is a durable receipt identifier, not a SQL relation reference.  Keep
// existing accepted L0 bases stable after the physical table moves into the
// nirmana_evidence schema; the evidence parser resolves both identifiers.
export const NIRMANA_L0_FROZEN_MANIFEST_SOURCE = 'nirmana_elevation_campaign_definitions.manifest' as const

export interface NirmanaL0AnalysisReceiptBase {
  schema_version: 'nirmana-asset-analysis-receipt-base/v1'
  asset_id: string
  layer: 'L0'
  writer_digest_sha256: string | null
  grounding: {
    convergence_commit: typeof NIRMANA_L0_CONVERGENCE_COMMIT
    frozen_manifest_source: typeof NIRMANA_L0_FROZEN_MANIFEST_SOURCE
    writer_digest_ref: 'platform/src/generated/nirmana-writer-digests.json'
  }
}

export function assertNirmanaL0WriterInventoryMatchesConvergence(inventory: unknown): asserts inventory is Record<string, string> {
  if (inventory === null || typeof inventory !== 'object' || Array.isArray(inventory)) {
    throw new Error('Nirmana L0 writer inventory does not match the pinned convergence inventory.')
  }
  const l0Inventory = Object.fromEntries(Object.entries(inventory)
    .filter(([assetId]) => assetId.startsWith('bg_'))
    .sort(([left], [right]) => left.localeCompare(right)))
  if (Object.values(l0Inventory).some((digest) => typeof digest !== 'string' || !/^[a-f0-9]{64}$/.test(digest))) {
    throw new Error('Nirmana L0 writer inventory does not match the pinned convergence inventory.')
  }
  const digest = createHash('sha256').update(JSON.stringify(l0Inventory)).digest('hex')
  if (digest !== NIRMANA_L0_WRITER_INVENTORY_SHA256) {
    throw new Error('Nirmana L0 writer inventory does not match the pinned convergence inventory.')
  }
}

const writerDigestsCandidate = writerDigestInventory.writers as unknown
const writerDigests = (() => {
  try {
    assertNirmanaL0WriterInventoryMatchesConvergence(writerDigestsCandidate)
    return writerDigestsCandidate
  } catch {
    // Writer corrections may be deployed before a new durable-main convergence
    // receipt is ratified. Keep the service available, but make evidence
    // creation fail closed until the pinned commit and aggregate are advanced.
    return null
  }
})()
export const NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE = writerDigests !== null
const nonWriterAssets = [
  'bg_ephemeris_engine',
  'bg_gochara_citation_resolution',
  'bg_panchanga',
  'bg_sarvatobhadra_grid',
] as const
const assetIds = NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE
  ? [
      ...Object.keys(writerDigests ?? {}).filter((assetId) => assetId.startsWith('bg_')),
      ...nonWriterAssets,
    ].sort()
  : []
const bases = assetIds.map((assetId): NirmanaL0AnalysisReceiptBase => ({
    schema_version: 'nirmana-asset-analysis-receipt-base/v1',
    asset_id: assetId,
    layer: 'L0',
    writer_digest_sha256: writerDigests?.[assetId] ?? null,
    grounding: {
      convergence_commit: NIRMANA_L0_CONVERGENCE_COMMIT,
      frozen_manifest_source: NIRMANA_L0_FROZEN_MANIFEST_SOURCE,
      writer_digest_ref: 'platform/src/generated/nirmana-writer-digests.json',
    },
  }))

if (NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE
  && bases.length !== NIRMANA_L0_ANALYSIS_RECEIPT_COUNT) {
  throw new Error(`Expected ${NIRMANA_L0_ANALYSIS_RECEIPT_COUNT} frozen L0 analysis receipt bases; found ${bases.length}.`)
}

export const NIRMANA_L0_ANALYSIS_RECEIPTS = Object.freeze(Object.fromEntries(
  bases.map((base) => [base.asset_id, Object.freeze(base)]),
)) as Readonly<Record<string, Readonly<NirmanaL0AnalysisReceiptBase>>>

export function getNirmanaL0AnalysisReceiptBase(assetId: string): Readonly<NirmanaL0AnalysisReceiptBase> | undefined {
  return NIRMANA_L0_ANALYSIS_RECEIPTS[assetId]
}

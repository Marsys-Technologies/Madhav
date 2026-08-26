import { createHash } from 'node:crypto'
import writerDigestInventory from './nirmana-writer-digests.json'

export const NIRMANA_L0_CONVERGENCE_COMMIT = '5f47906bce9148563cc57764b21a2c06415d9f49' as const
export const NIRMANA_L0_ANALYSIS_RECEIPT_COUNT = 40 as const
export const NIRMANA_L0_WRITER_INVENTORY_SHA256 = '6c4962804c0c6a6973b7107f7662c75eae69e982e278453be6b07b097b5a85f2' as const

export interface NirmanaL0AnalysisReceiptBase {
  schema_version: 'nirmana-asset-analysis-receipt-base/v1'
  asset_id: string
  layer: 'L0'
  writer_digest_sha256: string | null
  grounding: {
    convergence_commit: typeof NIRMANA_L0_CONVERGENCE_COMMIT
    frozen_manifest_source: 'nirmana_elevation_campaign_definitions.manifest'
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
      frozen_manifest_source: 'nirmana_elevation_campaign_definitions.manifest',
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

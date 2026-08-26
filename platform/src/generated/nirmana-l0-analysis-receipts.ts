import writerDigestInventory from './nirmana-writer-digests.json'

export const NIRMANA_L0_CONVERGENCE_COMMIT = '5f47906bce9148563cc57764b21a2c06415d9f49' as const
export const NIRMANA_L0_ANALYSIS_RECEIPT_COUNT = 40 as const

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

const writerDigests = writerDigestInventory.writers as Record<string, string>
const nonWriterAssets = [
  'bg_ephemeris_engine',
  'bg_gochara_citation_resolution',
  'bg_panchanga',
  'bg_sarvatobhadra_grid',
] as const
const assetIds = [
  ...Object.keys(writerDigests).filter((assetId) => assetId.startsWith('bg_')),
  ...nonWriterAssets,
].sort()
const bases = assetIds.map((assetId): NirmanaL0AnalysisReceiptBase => ({
    schema_version: 'nirmana-asset-analysis-receipt-base/v1',
    asset_id: assetId,
    layer: 'L0',
    writer_digest_sha256: writerDigests[assetId] ?? null,
    grounding: {
      convergence_commit: NIRMANA_L0_CONVERGENCE_COMMIT,
      frozen_manifest_source: 'nirmana_elevation_campaign_definitions.manifest',
      writer_digest_ref: 'platform/src/generated/nirmana-writer-digests.json',
    },
  }))

if (bases.length !== NIRMANA_L0_ANALYSIS_RECEIPT_COUNT) {
  throw new Error(`Expected ${NIRMANA_L0_ANALYSIS_RECEIPT_COUNT} frozen L0 analysis receipt bases; found ${bases.length}.`)
}

export const NIRMANA_L0_ANALYSIS_RECEIPTS = Object.freeze(Object.fromEntries(
  bases.map((base) => [base.asset_id, Object.freeze(base)]),
)) as Readonly<Record<string, Readonly<NirmanaL0AnalysisReceiptBase>>>

export function getNirmanaL0AnalysisReceiptBase(assetId: string): Readonly<NirmanaL0AnalysisReceiptBase> | undefined {
  return NIRMANA_L0_ANALYSIS_RECEIPTS[assetId]
}

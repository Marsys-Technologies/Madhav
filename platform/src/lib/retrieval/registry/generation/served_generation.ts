/**
 * Per-asset served-generation resolver (Pūrṇa Anveṣaṇa R1A / review RC-1).
 *
 * A chart has no chart-wide build identity: build runs are frequently scoped to a single
 * asset, so "the chart's latest completed run" usually wrote none of the rows a consumer
 * reads. Every consumer that must bind to current chart evidence resolves it here, per asset:
 *
 *   receipt  — the asset's proven, fresh, active-spec provenance receipt for the chart, issued
 *              by a completed run;
 *   rows     — the run that actually wrote the served rows. Normally the receipting run; after a
 *              `skip_no_delta` run re-attributes an unchanged receipt, the rows keep the id of
 *              the most recent completed run that built the asset before it.
 *
 * An asset that cannot be proven this way is returned UNRESOLVED with a typed reason. The
 * resolver never guesses and never falls back to another asset's run.
 *
 * Multi-writer tables (chart_facts, bodha_msr_signals, …) are fenced by the SET of resolved
 * rows builds. That is sound because L1+ writers are per-chart delete-then-insert
 * (CLAUDE.md §N.3): once an asset is rebuilt its earlier rows no longer exist, so a row whose
 * build id belongs to the served set is a row of the asset that build currently serves.
 *
 * Durable generation heads (migrations 1035/1036) are owned and populated by the data plane.
 * Until they are populated and proven, receipts are the only source (`source` below); a
 * consumer never needs to change when heads become the source.
 */
import { query as defaultQuery } from '@/lib/db/client'
import { stableFingerprint } from '../knowledge/stable'

export type ServedGenerationQueryExecutor = (
  sql: string,
  params?: unknown[],
) => Promise<{ rows: Record<string, unknown>[] }>

export type UnresolvedGenerationReason =
  | 'no_chart_receipt'
  | 'receipt_not_proven'
  | 'receipt_not_fresh'
  | 'receipt_spec_retired'
  | 'receipt_run_not_completed'
  | 'receipt_run_asset_missing'
  | 'receipt_disposition_unservable'
  | 'skip_chain_writer_missing'
  | 'partition_generation_split'

export interface ServedPartitionReceipt {
  readonly partition_key: string
  readonly receipt_version: string
  readonly receipt_build_id: string | null
  readonly rows_build_id: string | null
  readonly receipt_state: string
  readonly freshness_state: string | null
  readonly output_digest_spec_sha256: string | null
  readonly spec_active: boolean
  readonly receipt_run_state: string | null
  readonly receipt_disposition: string | null
  readonly observed_at: string
}

export interface ResolvedAssetGeneration {
  readonly asset_id: string
  readonly state: 'resolved'
  /** Run that issued the proven+fresh receipt (a skip_no_delta run after re-attribution). */
  readonly receipt_build_id: string
  /** Run whose rows are served — equal to receipt_build_id unless a no-delta run re-receipted. */
  readonly rows_build_id: string
  readonly rows_binding: 'receipt_run_wrote_rows' | 'skip_no_delta_writer'
  readonly output_digest_spec_sha256: string
  readonly observed_at: string
  readonly partitions: readonly ServedPartitionReceipt[]
}

export interface UnresolvedAssetGeneration {
  readonly asset_id: string
  readonly state: 'unresolved'
  readonly reason: UnresolvedGenerationReason
  readonly partitions: readonly ServedPartitionReceipt[]
}

export type AssetGeneration = ResolvedAssetGeneration | UnresolvedAssetGeneration

export interface ChartServedGeneration {
  readonly chart_id: string
  readonly source: 'per_asset_receipts'
  /** Stable identity of what is served: changes when any asset's served binding changes. */
  readonly generation_hash: string
  readonly assets: Readonly<Record<string, AssetGeneration>>
  /** Sorted, de-duplicated rows builds of every resolved asset. */
  readonly served_build_ids: readonly string[]
}

/**
 * SQL expression for the run whose rows a chart-scoped receipt currently serves.
 *
 * `receipt`, `receiptRun`, and `receiptAsset` are the aliases of the joined
 * asset_provenance_receipts, build_runs (receipt.build_id), and build_run_assets
 * (receipt run × receipt asset) rows. Evaluates to NULL when no writing run can be proven.
 * This is the single reviewed rule; every consumer that joins rows to a receipt uses it.
 */
export function servedRowsBuildIdSql(aliases: {
  readonly receipt: string
  readonly receiptRun: string
  readonly receiptAsset: string
}): string {
  const { receipt, receiptRun, receiptAsset } = aliases
  return `(CASE
      WHEN ${receiptAsset}.run_id IS NULL THEN NULL
      WHEN ${receiptAsset}.disposition = 'skip_no_delta' THEN (
        SELECT writer_asset.run_id
          FROM build_run_assets writer_asset
          JOIN build_runs writer_run ON writer_run.id = writer_asset.run_id
         WHERE writer_run.chart_id = ${receipt}.chart_id
           AND writer_asset.asset_id = ${receipt}.asset_id
           AND writer_run.state = 'completed'
           AND writer_asset.state = 'complete'
           AND (writer_asset.disposition IS NULL OR writer_asset.disposition = 'build')
           AND COALESCE(writer_asset.ended_at, writer_run.ended_at)
               <= COALESCE(${receiptAsset}.started_at, ${receiptRun}.started_at, ${receipt}.observed_at)
         ORDER BY COALESCE(writer_asset.ended_at, writer_run.ended_at) DESC, writer_asset.run_id DESC
         LIMIT 1)
      WHEN (${receiptAsset}.disposition IS NULL OR ${receiptAsset}.disposition = 'build')
       AND ${receiptAsset}.state = 'complete' THEN ${receipt}.build_id
      ELSE NULL
    END)`
}

const RESOLVER_SQL = `
  SELECT receipt.asset_id,
         receipt.partition_key,
         receipt.receipt_version,
         receipt.build_id::text AS receipt_build_id,
         ${servedRowsBuildIdSql({ receipt: 'receipt', receiptRun: 'receipt_run', receiptAsset: 'receipt_asset' })}::text
           AS rows_build_id,
         receipt.receipt_state,
         freshness.freshness_state,
         receipt.output_digest_spec_sha256,
         EXISTS (
           SELECT 1 FROM asset_output_digest_specs spec
            WHERE spec.asset_id = receipt.asset_id
              AND spec.spec_sha256 = receipt.output_digest_spec_sha256
              AND spec.retired_at IS NULL
         ) AS spec_active,
         receipt_run.state AS receipt_run_state,
         receipt_asset.run_id IS NOT NULL AS receipt_asset_present,
         receipt_asset.disposition AS receipt_disposition,
         receipt.observed_at::text AS observed_at
    FROM asset_provenance_receipts receipt
    LEFT JOIN asset_freshness freshness
      ON freshness.asset_id = receipt.asset_id
     AND freshness.scope_key = receipt.scope_key
     AND freshness.partition_key = receipt.partition_key
     AND freshness.receipt_version = receipt.receipt_version
    LEFT JOIN build_runs receipt_run
      ON receipt_run.id = receipt.build_id AND receipt_run.chart_id = receipt.chart_id
    LEFT JOIN build_run_assets receipt_asset
      ON receipt_asset.run_id = receipt.build_id AND receipt_asset.asset_id = receipt.asset_id
   WHERE receipt.chart_id = $1::uuid
     AND ($2::text[] IS NULL OR receipt.asset_id = ANY($2::text[]))
   ORDER BY receipt.asset_id, receipt.partition_key`

export interface ResolverRow extends ServedPartitionReceipt {
  readonly asset_id: string
  readonly receipt_asset_present: boolean
}

function text(value: unknown): string | null {
  return typeof value === 'string' && value.length > 0 ? value : null
}

function toRow(raw: Record<string, unknown>): ResolverRow {
  return {
    asset_id: String(raw['asset_id']),
    partition_key: String(raw['partition_key']),
    receipt_version: String(raw['receipt_version']),
    receipt_build_id: text(raw['receipt_build_id']),
    rows_build_id: text(raw['rows_build_id']),
    receipt_state: String(raw['receipt_state']),
    freshness_state: text(raw['freshness_state']),
    output_digest_spec_sha256: text(raw['output_digest_spec_sha256']),
    spec_active: raw['spec_active'] === true,
    receipt_run_state: text(raw['receipt_run_state']),
    receipt_asset_present: raw['receipt_asset_present'] === true,
    receipt_disposition: text(raw['receipt_disposition']),
    observed_at: String(raw['observed_at']),
  }
}

function partitionDefect(row: ResolverRow): UnresolvedGenerationReason | null {
  if (row.receipt_state !== 'proven') return 'receipt_not_proven'
  if (row.freshness_state !== 'fresh') return 'receipt_not_fresh'
  if (!row.spec_active) return 'receipt_spec_retired'
  if (row.receipt_run_state !== 'completed' || row.receipt_build_id === null) return 'receipt_run_not_completed'
  if (!row.receipt_asset_present) return 'receipt_run_asset_missing'
  if (row.rows_build_id === null) {
    return row.receipt_disposition === 'skip_no_delta' ? 'skip_chain_writer_missing' : 'receipt_disposition_unservable'
  }
  return null
}

function publicPartition(row: ResolverRow): ServedPartitionReceipt {
  return {
    partition_key: row.partition_key,
    receipt_version: row.receipt_version,
    receipt_build_id: row.receipt_build_id,
    rows_build_id: row.rows_build_id,
    receipt_state: row.receipt_state,
    freshness_state: row.freshness_state,
    output_digest_spec_sha256: row.output_digest_spec_sha256,
    spec_active: row.spec_active,
    receipt_run_state: row.receipt_run_state,
    receipt_disposition: row.receipt_disposition,
    observed_at: row.observed_at,
  }
}

/** Classify one asset's chart-scoped receipts into a served binding or a typed refusal. */
export function classifyAssetGeneration(assetId: string, rows: readonly ResolverRow[]): AssetGeneration {
  const partitions = rows.map(publicPartition)
  if (!rows.length) return { asset_id: assetId, state: 'unresolved', reason: 'no_chart_receipt', partitions }
  for (const row of rows) {
    const defect = partitionDefect(row)
    if (defect) return { asset_id: assetId, state: 'unresolved', reason: defect, partitions }
  }
  const rowsBuilds = new Set(rows.map((row) => row.rows_build_id))
  const receiptBuilds = new Set(rows.map((row) => row.receipt_build_id))
  const specs = new Set(rows.map((row) => row.output_digest_spec_sha256))
  if (rowsBuilds.size !== 1 || receiptBuilds.size !== 1 || specs.size !== 1) {
    return { asset_id: assetId, state: 'unresolved', reason: 'partition_generation_split', partitions }
  }
  const [first] = rows
  const rowsBuildId = first!.rows_build_id!
  const receiptBuildId = first!.receipt_build_id!
  return {
    asset_id: assetId,
    state: 'resolved',
    receipt_build_id: receiptBuildId,
    rows_build_id: rowsBuildId,
    rows_binding: rowsBuildId === receiptBuildId ? 'receipt_run_wrote_rows' : 'skip_no_delta_writer',
    output_digest_spec_sha256: first!.output_digest_spec_sha256!,
    observed_at: rows.map((row) => row.observed_at).sort().at(-1)!,
    partitions,
  }
}

export function chartServedGenerationFromRows(
  chartId: string,
  requestedAssetIds: readonly string[] | null,
  rawRows: readonly Record<string, unknown>[],
): ChartServedGeneration {
  const rows = rawRows.map(toRow)
  const byAsset = new Map<string, ResolverRow[]>()
  for (const assetId of requestedAssetIds ?? []) byAsset.set(assetId, [])
  for (const row of rows) byAsset.set(row.asset_id, [...(byAsset.get(row.asset_id) ?? []), row])
  const assets: Record<string, AssetGeneration> = {}
  for (const assetId of [...byAsset.keys()].sort()) assets[assetId] = classifyAssetGeneration(assetId, byAsset.get(assetId)!)
  const resolved = Object.values(assets).filter((asset): asset is ResolvedAssetGeneration => asset.state === 'resolved')
  const served_build_ids = [...new Set(resolved.map((asset) => asset.rows_build_id))].sort()
  const generation_hash = stableFingerprint({
    chart_id: chartId,
    source: 'per_asset_receipts',
    assets: Object.values(assets).map((asset) => asset.state === 'resolved'
      ? {
          asset_id: asset.asset_id,
          rows_build_id: asset.rows_build_id,
          receipt_build_id: asset.receipt_build_id,
          output_digest_spec_sha256: asset.output_digest_spec_sha256,
          receipt_versions: asset.partitions.map((partition) => `${partition.partition_key}:${partition.receipt_version}`),
        }
      : { asset_id: asset.asset_id, unresolved: asset.reason }),
  })
  return { chart_id: chartId, source: 'per_asset_receipts', generation_hash, assets, served_build_ids }
}

/**
 * Resolve the served generation of `assetIds` (or of every asset holding a chart receipt when
 * `assetIds` is null) for one chart. Query failures propagate: callers must fail closed.
 */
export async function resolveChartServedGeneration(
  chartId: string,
  assetIds: readonly string[] | null,
  query: ServedGenerationQueryExecutor = defaultQuery as unknown as ServedGenerationQueryExecutor,
): Promise<ChartServedGeneration> {
  const requested = assetIds === null ? null : [...new Set(assetIds)].sort()
  const { rows } = await query(RESOLVER_SQL, [chartId, requested])
  return chartServedGenerationFromRows(chartId, requested, rows)
}

/** Stable, textual identity for chart-level bindings (lifecycle tokens, overlay versions). */
export function servedGenerationIdentity(generation: ChartServedGeneration): string | null {
  return generation.served_build_ids.length ? `generation:${generation.generation_hash}` : null
}

export function resolvedRowsBuildId(generation: ChartServedGeneration, assetId: string): string | null {
  const asset = generation.assets[assetId]
  return asset?.state === 'resolved' ? asset.rows_build_id : null
}

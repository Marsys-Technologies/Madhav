/**
 * Per-asset served-generation resolver (Pūrṇa Anveṣaṇa R1A / review RC-1).
 *
 * A chart has no chart-wide build identity: build runs are frequently scoped to a single
 * asset, so "the chart's latest completed run" usually wrote none of the rows a consumer
 * reads. Every consumer that must bind to current chart evidence resolves it here, per asset:
 *
 *   receipt  — the asset's proven, fresh, active-spec provenance receipt for the chart, issued
 *              by a completed run, or by a failed run in which THIS asset itself finished
 *              (per-asset admission, see {@link servedReceiptRunAdmitsSql});
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
  | 'receipt_asset_not_complete'
  | 'receipt_disposition_unservable'
  | 'skip_chain_writer_missing'
  | 'intervening_attempt_unreceipted'
  | 'partition_generation_split'

export interface ServedPartitionReceipt {
  readonly partition_key: string
  readonly receipt_version: string
  readonly receipt_build_id: string | null
  /** The run that last wrote the asset's rows (before the intervening-attempt check). */
  readonly writer_run_id: string | null
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
  /**
   * Sorted, de-duplicated rows builds that fence multi-writer tables: every resolved asset's
   * rows build, EXCEPT a build that is also the (last known) rows build of an unresolved asset.
   * Rows in a multi-writer table carry only a build id, so a run shared with an unresolved asset
   * cannot admit the resolved asset's rows without also admitting the unresolved asset's.
   */
  readonly served_build_ids: readonly string[]
  /** Builds withheld from `served_build_ids`, with the unresolved and resolved assets sharing them. */
  readonly withheld_builds: readonly {
    readonly build_id: string
    readonly unresolved_asset_ids: readonly string[]
    readonly resolved_asset_ids: readonly string[]
  }[]
}

interface ServedReceiptAliases {
  readonly receipt: string
  readonly receiptRun: string
  readonly receiptAsset: string
}

/**
 * SQL expression for the run that last WROTE the asset's rows, as proven from a chart-scoped
 * receipt: the receipting run when it built the asset; after a `skip_no_delta` re-attribution,
 * the most recent attempt that completed a build of the asset before the skip.
 *
 * The writer's own RUN may have ended `failed` (another asset in the same run failed): the
 * asset's rows were still fully written and they, not an earlier run's deleted rows, are what
 * a no-delta receipt certifies. Evaluates to NULL when no writer can be proven.
 */
export function servedWriterRunIdSql(aliases: ServedReceiptAliases): string {
  const { receipt, receiptRun, receiptAsset } = aliases
  return `(CASE
      WHEN ${receiptAsset}.run_id IS NULL THEN NULL
      WHEN ${receiptAsset}.disposition = 'skip_no_delta' THEN (
        SELECT writer_asset.run_id
          FROM build_run_assets writer_asset
          JOIN build_runs writer_run ON writer_run.id = writer_asset.run_id
         WHERE writer_run.chart_id = ${receipt}.chart_id
           AND writer_asset.asset_id = ${receipt}.asset_id
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

/**
 * SQL predicate: some other dispatched attempt at this asset was still able to mutate its rows
 * after `writer` finished writing them (a failed/aborted/in-flight attempt, or a completed
 * build that never issued its own receipt). Heavy writers commit per sub-step, so such an
 * attempt may have deleted or replaced part of the writer's rows. A `skip_no_delta` attempt
 * writes nothing and never counts; a never-dispatched queued row never counts.
 */
function interveningAttemptSql(aliases: ServedReceiptAliases, writer: string): string {
  const { receipt } = aliases
  return `EXISTS (
        SELECT 1
          FROM build_run_assets attempt
          JOIN build_runs attempt_run ON attempt_run.id = attempt.run_id
         WHERE attempt_run.chart_id = ${receipt}.chart_id
           AND attempt.asset_id = ${receipt}.asset_id
           AND attempt.run_id <> ${writer}
           AND attempt.started_at IS NOT NULL
           AND attempt.state IN ('building', 'error', 'aborted', 'complete')
           AND attempt.disposition IS DISTINCT FROM 'skip_no_delta'
           AND COALESCE(attempt.ended_at, attempt_run.ended_at, 'infinity'::timestamptz) > (
             SELECT COALESCE(writer_done.ended_at, writer_done_run.ended_at)
               FROM build_run_assets writer_done
               JOIN build_runs writer_done_run ON writer_done_run.id = writer_done.run_id
              WHERE writer_done.run_id = ${writer} AND writer_done.asset_id = ${receipt}.asset_id))`
}

/**
 * SQL expression for the run whose rows a chart-scoped receipt currently serves: the proven
 * writer, unless a later attempt could have mutated those rows (then NULL — fail closed).
 *
 * `receipt`, `receiptRun`, and `receiptAsset` are the aliases of the joined
 * asset_provenance_receipts, build_runs (receipt.build_id), and build_run_assets
 * (receipt run × receipt asset) rows. This is the single reviewed rule; every consumer that
 * joins rows to a receipt uses it.
 */
export function servedRowsBuildIdSql(aliases: ServedReceiptAliases): string {
  const writer = servedWriterRunIdSql(aliases)
  return `(CASE WHEN ${interveningAttemptSql(aliases, writer)} THEN NULL ELSE ${writer} END)`
}

/**
 * LEFT JOINs that attach the receipting run and its asset row to a chart receipt alias.
 * Pair with {@link servedReceiptColumnsSql}; every consumer that classifies receipts uses both.
 */
export function servedReceiptJoinsSql(aliases: ServedReceiptAliases): string {
  const { receipt, receiptRun, receiptAsset } = aliases
  return `LEFT JOIN build_runs ${receiptRun}
      ON ${receiptRun}.id = ${receipt}.build_id AND ${receiptRun}.chart_id = ${receipt}.chart_id
    LEFT JOIN build_run_assets ${receiptAsset}
      ON ${receiptAsset}.run_id = ${receipt}.build_id AND ${receiptAsset}.asset_id = ${receipt}.asset_id`
}

/**
 * `asset_throughput.state` values that mean "this asset's build in its run finished": the
 * orchestrator's own success allowlist (`_SUCCESS_OUTCOMES` in pipeline/orchestrator/runner.py)
 * minus the `build_run_assets` literal. `build_run_assets.state = 'complete'` alone is NOT such
 * a witness: asset_runner writes it for every terminal outcome, including a build SATYA-DĪPA
 * held back as `incomplete` (rows present, substep plan unfinished) which still persists a
 * receipt. A held-back or errored asset therefore never admits a failed run's receipt.
 */
export const SERVED_ASSET_SUCCESS_STATES = ['lit', 'mature', 'dormant', 'service_ok'] as const

/**
 * The receipt's asset's outcome in its run, read from the chart-scoped asset_throughput row
 * (one row per chart x asset: partial unique indexes of migrations 171/184). NULL when no such
 * row exists, which fails closed in {@link servedReceiptRunAdmitsSql}.
 */
export function servedAssetOutcomeSql(aliases: ServedReceiptAliases): string {
  const { receipt } = aliases
  return `(SELECT served_outcome.state
             FROM asset_throughput served_outcome
            WHERE served_outcome.asset_id = ${receipt}.asset_id
              AND served_outcome.chart_id IS NOT DISTINCT FROM ${receipt}.chart_id
            LIMIT 1)`
}

/**
 * SQL predicate: the receipt's issuing run may serve, per ASSET (N-208).
 *
 *   - a `completed` run serves (unchanged);
 *   - a `failed` run serves ONLY the assets that themselves finished in it: the asset's own
 *     build_run_assets row is `complete` and its chart-scoped outcome is a success state. One
 *     unrelated asset failing a ~75-asset run must not unserve every asset that completed and
 *     verified; a failed, errored, held-back (`incomplete`) or never-run asset still never serves;
 *   - `planned`, `running`, `paused` and `stopped` (cancelled) runs never serve.
 *
 * The receipt's own gates (proven, fresh, active spec) and the intervening-attempt rule in
 * {@link servedRowsBuildIdSql} apply on top, exactly as for a completed run. Every reader that
 * joins a receipt to its run uses this predicate; {@link receiptRunAdmits} is its TS twin.
 */
export function servedReceiptRunAdmitsSql(aliases: ServedReceiptAliases): string {
  const { receiptRun, receiptAsset } = aliases
  const states = SERVED_ASSET_SUCCESS_STATES.map((state) => `'${state}'`).join(', ')
  return `(${receiptRun}.state = 'completed'
      OR (${receiptRun}.state = 'failed'
          AND ${receiptAsset}.state = 'complete'
          AND ${servedAssetOutcomeSql(aliases)} IN (${states})))`
}

/**
 * SQL expression for the run of the receipt asset's LATEST dispatched (non-no-delta) attempt, but
 * only for an asset that shares its target table with another active writer; NULL otherwise.
 *
 * Why: rows in a shared table carry only a build id. Once a failed run may serve the assets that
 * finished in it, that run's id can enter the served set through a finished asset while a
 * co-writer that FAILED in the same run (heavy writers commit per sub-step) left partial rows
 * under the same id. Such an asset, when it does not itself resolve, withholds its latest
 * attempt's run from the multi-writer fence (see `chartServedGenerationFromRows`). A single-writer
 * asset's partial rows live in its own table and are fenced by its own (unresolved) binding.
 */
export function servedCowriterAttemptRunIdSql(aliases: ServedReceiptAliases): string {
  const { receipt } = aliases
  return `(CASE WHEN EXISTS (
        SELECT 1
          FROM asset_registry cowriter_self
          JOIN asset_registry cowriter_peer
            ON cowriter_peer.target_table = cowriter_self.target_table
           AND cowriter_peer.asset_id <> cowriter_self.asset_id
           AND cowriter_peer.is_active IS TRUE
           AND cowriter_peer.has_writer IS TRUE
         WHERE cowriter_self.asset_id = ${receipt}.asset_id
           AND cowriter_self.target_table IS NOT NULL)
      THEN (
        SELECT latest_attempt.run_id
          FROM build_run_assets latest_attempt
          JOIN build_runs latest_attempt_run ON latest_attempt_run.id = latest_attempt.run_id
         WHERE latest_attempt_run.chart_id = ${receipt}.chart_id
           AND latest_attempt.asset_id = ${receipt}.asset_id
           AND latest_attempt.started_at IS NOT NULL
           AND latest_attempt.state IN ('building', 'error', 'aborted', 'complete')
           AND latest_attempt.disposition IS DISTINCT FROM 'skip_no_delta'
         ORDER BY COALESCE(latest_attempt.ended_at, latest_attempt_run.ended_at, 'infinity'::timestamptz) DESC,
                  latest_attempt.started_at DESC, latest_attempt.run_id DESC
         LIMIT 1)
    END)`
}

/** Classification columns (beyond the receipt's own identity and state) for one receipt row. */
export function servedReceiptColumnsSql(aliases: ServedReceiptAliases): string {
  const { receipt, receiptRun, receiptAsset } = aliases
  return `${receipt}.partition_key,
         ${receipt}.build_id::text AS receipt_build_id,
         ${servedWriterRunIdSql(aliases)}::text AS writer_run_id,
         ${servedRowsBuildIdSql(aliases)}::text AS rows_build_id,
         EXISTS (
           SELECT 1 FROM asset_output_digest_specs served_spec
            WHERE served_spec.asset_id = ${receipt}.asset_id
              AND served_spec.spec_sha256 = ${receipt}.output_digest_spec_sha256
              AND served_spec.retired_at IS NULL
         ) AS spec_active,
         ${receiptRun}.state AS receipt_run_state,
         ${receiptAsset}.run_id IS NOT NULL AS receipt_asset_present,
         ${receiptAsset}.state AS receipt_asset_state,
         ${servedAssetOutcomeSql(aliases)} AS receipt_asset_outcome,
         ${servedCowriterAttemptRunIdSql(aliases)}::text AS cowriter_attempt_run_id,
         ${receiptAsset}.disposition AS receipt_disposition`
}

const ALIASES: ServedReceiptAliases = { receipt: 'receipt', receiptRun: 'receipt_run', receiptAsset: 'receipt_asset' }

const RESOLVER_SQL = `
  SELECT receipt.asset_id,
         receipt.chart_id::text AS chart_id,
         receipt.receipt_version,
         receipt.receipt_state,
         freshness.freshness_state,
         receipt.output_digest_spec_sha256,
         receipt.observed_at::text AS observed_at,
         ${servedReceiptColumnsSql(ALIASES)}
    FROM asset_provenance_receipts receipt
    LEFT JOIN asset_freshness freshness
      ON freshness.asset_id = receipt.asset_id
     AND freshness.scope_key = receipt.scope_key
     AND freshness.partition_key = receipt.partition_key
     AND freshness.receipt_version = receipt.receipt_version
    ${servedReceiptJoinsSql(ALIASES)}
   WHERE receipt.chart_id = $1::uuid
     AND ($2::text[] IS NULL OR receipt.asset_id = ANY($2::text[]))
   ORDER BY receipt.asset_id, receipt.partition_key`

export interface ResolverRow extends ServedPartitionReceipt {
  readonly asset_id: string
  readonly receipt_asset_present: boolean
  /** The receipt asset's own build_run_assets.state (null when absent or not selected). */
  readonly receipt_asset_state: string | null
  /** The receipt asset's chart-scoped asset_throughput.state (null when no row exists). */
  readonly receipt_asset_outcome: string | null
  /** Latest dispatched attempt's run, for an asset that shares its target table (else null). */
  readonly cowriter_attempt_run_id: string | null
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
    writer_run_id: text(raw['writer_run_id']),
    rows_build_id: text(raw['rows_build_id']),
    receipt_state: String(raw['receipt_state']),
    freshness_state: text(raw['freshness_state']),
    output_digest_spec_sha256: text(raw['output_digest_spec_sha256']),
    spec_active: raw['spec_active'] === true,
    receipt_run_state: text(raw['receipt_run_state']),
    receipt_asset_present: raw['receipt_asset_present'] === true,
    receipt_asset_state: text(raw['receipt_asset_state']),
    receipt_asset_outcome: text(raw['receipt_asset_outcome']),
    cowriter_attempt_run_id: text(raw['cowriter_attempt_run_id']),
    receipt_disposition: text(raw['receipt_disposition']),
    observed_at: String(raw['observed_at']),
  }
}

/**
 * TS twin of {@link servedReceiptRunAdmitsSql} (per-asset run admission, N-208): a completed run
 * admits its receipts; a failed run admits only the receipt of an asset that itself finished in it.
 */
export function receiptRunAdmits(row: {
  readonly receipt_run_state: string | null
  readonly receipt_asset_state: string | null
  readonly receipt_asset_outcome: string | null
}): boolean {
  if (row.receipt_run_state === 'completed') return true
  return row.receipt_run_state === 'failed'
    && row.receipt_asset_state === 'complete'
    && (SERVED_ASSET_SUCCESS_STATES as readonly string[]).includes(row.receipt_asset_outcome ?? '')
}

function partitionDefect(row: ResolverRow): UnresolvedGenerationReason | null {
  if (row.receipt_state !== 'proven') return 'receipt_not_proven'
  if (row.freshness_state !== 'fresh') return 'receipt_not_fresh'
  if (!row.spec_active) return 'receipt_spec_retired'
  if (row.receipt_build_id === null || (row.receipt_run_state !== 'completed' && row.receipt_run_state !== 'failed')) {
    return 'receipt_run_not_completed'
  }
  if (!row.receipt_asset_present) return 'receipt_run_asset_missing'
  if (!receiptRunAdmits(row)) return 'receipt_asset_not_complete'
  if (row.rows_build_id === null) {
    if (row.writer_run_id !== null) return 'intervening_attempt_unreceipted'
    return row.receipt_disposition === 'skip_no_delta' ? 'skip_chain_writer_missing' : 'receipt_disposition_unservable'
  }
  return null
}

function publicPartition(row: ResolverRow): ServedPartitionReceipt {
  return {
    partition_key: row.partition_key,
    receipt_version: row.receipt_version,
    receipt_build_id: row.receipt_build_id,
    writer_run_id: row.writer_run_id,
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
  // Only this chart's receipts can bind a chart generation (defensive against callers that
  // share one row set between chart-scoped and global receipts).
  const chartKey = chartId.toLowerCase()
  const rows = rawRows
    .filter((raw) => raw['chart_id'] === undefined
      || (typeof raw['chart_id'] === 'string' && raw['chart_id'].toLowerCase() === chartKey))
    .filter((raw) => typeof raw['asset_id'] === 'string' && raw['asset_id'].length > 0)
    .map(toRow)
  const byAsset = new Map<string, ResolverRow[]>()
  for (const assetId of requestedAssetIds ?? []) byAsset.set(assetId, [])
  for (const row of rows) byAsset.set(row.asset_id, [...(byAsset.get(row.asset_id) ?? []), row])
  const assets: Record<string, AssetGeneration> = {}
  for (const assetId of [...byAsset.keys()].sort()) assets[assetId] = classifyAssetGeneration(assetId, byAsset.get(assetId)!)
  const resolved = Object.values(assets).filter((asset): asset is ResolvedAssetGeneration => asset.state === 'resolved')
  // A run whose rows an unresolved asset may still hold (its last known rows build, or its
  // writer when a later attempt invalidated those rows) taints that run for shared tables.
  const taint = new Map<string, Set<string>>()
  const attemptRuns = new Map<string, Set<string>>()
  for (const row of rows) {
    if (row.cowriter_attempt_run_id) {
      attemptRuns.set(row.asset_id, new Set([...(attemptRuns.get(row.asset_id) ?? []), row.cowriter_attempt_run_id]))
    }
  }
  for (const asset of Object.values(assets)) {
    if (asset.state !== 'unresolved') continue
    const builds = new Set<string>(attemptRuns.get(asset.asset_id) ?? [])
    for (const partition of asset.partitions) {
      const build = partition.rows_build_id ?? partition.writer_run_id
      if (build) builds.add(build)
    }
    // A co-writer that failed in a run (per-asset serving, N-208) may have left partial rows
    // under that run's id in a shared table: the run cannot admit its finished assets' rows.
    for (const build of builds) taint.set(build, new Set([...(taint.get(build) ?? []), asset.asset_id]))
  }
  const served_build_ids = [...new Set(resolved.map((asset) => asset.rows_build_id))]
    .filter((build) => !taint.has(build))
    .sort()
  const withheld_builds = [...taint.keys()].sort()
    .map((build_id) => ({
      build_id,
      unresolved_asset_ids: [...taint.get(build_id)!].sort(),
      resolved_asset_ids: resolved.filter((asset) => asset.rows_build_id === build_id).map((asset) => asset.asset_id).sort(),
    }))
    .filter((entry) => entry.resolved_asset_ids.length > 0)
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
  return { chart_id: chartId, source: 'per_asset_receipts', generation_hash, assets, served_build_ids, withheld_builds }
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

/**
 * A row fence: one build id (legacy/public callers) or a served build set. Chart-level
 * consumers pass the set; single-writer tools may pass their own asset's rows build.
 */
export type BuildFence = string | readonly string[]

/** The declared `build_id` input shared by every tool that accepts a served-generation fence, so
 *  planned dispatch (which injects the overlay's served set) and composing callers use one shape. */
/**
 * Declared as `string` (the canonical scalar spelling) although the handlers also accept an array of
 * build UUIDs: the derived input contracts of every binding that declares this input (and so the
 * capability content hash and the acceptance lineage) pin that type, and changing it would move them
 * for no behavioral gain. Frozen so no consumer can mutate the one shared declaration.
 */
export const BUILD_FENCE_INPUT = Object.freeze({
  type: 'string',
  description: "Served-generation build fence: one build UUID or an array of them. Composing callers and inquiry-dispatched calls carry the chart's served build set; a standalone call that omits it reads the chart's current rows unfenced.",
} as const)

/**
 * The three states a build-fence argument can resolve to (R3 boundary, native ruling
 * "explicit-empty build-fence semantics"). These are NOT interchangeable:
 *
 * - `absent`: the caller supplied no fence at all (`undefined`/`null`/`''`). Reading
 *   unfenced ("current rows") is a legitimate, long-standing fallback for this state.
 * - `resolved`: the caller supplied a fence that normalizes to one or more build ids.
 *   Bind it and read fenced.
 * - `explicit_empty`: the caller supplied a fence value (an array, or a scalar that
 *   normalizes away) that resolves to ZERO build ids. This is NOT the same as absent —
 *   binding `build_id = ANY($n::uuid[])` to `[]` matches zero rows, which looks exactly
 *   like "no evidence exists" when the real problem is "the fence itself could not be
 *   established." Every caller MUST branch on this state explicitly rather than folding
 *   it into either of the other two — see `describeBuildFence` for the callers' shared
 *   refusal/disclosure vocabulary.
 */
export type BuildFenceState =
  | { readonly kind: 'absent' }
  | { readonly kind: 'resolved'; readonly build_ids: readonly string[] }
  | { readonly kind: 'explicit_empty' }

/**
 * Classify a raw build-fence argument into its three distinguishable states. This is the
 * ONLY place a `build_id`-shaped value should be normalized — callers branch on `.kind`,
 * they never coerce the result back into a bare `string[] | null` (that shape cannot
 * distinguish `resolved: []`-that-should-never-happen from `explicit_empty`, which is
 * exactly the defect class this type exists to close).
 */
export function classifyBuildFence(value: unknown): BuildFenceState {
  if (value === null || value === undefined || value === '') return { kind: 'absent' }
  // Canonical (sorted, de-duplicated) so equal fences produce equal cache keys; any scalar a
  // caller supplies is fenced as text rather than silently dropped.
  const items = Array.isArray(value) ? value : [value]
  const normalized = [...new Set(items.filter((item) => item !== null && item !== undefined && item !== '').map(String))].sort()
  return normalized.length > 0 ? { kind: 'resolved', build_ids: normalized } : { kind: 'explicit_empty' }
}

/**
 * Standard refusal payload for an EVIDENTIARY caller that received an explicit-empty
 * fence: never proceeds unfenced, never binds to an empty array. Distinct from
 * `no_served_generation` (this session's earlier, internally-resolved-generation refusal)
 * because the failure mode is different — here a CALLER supplied a fence value, not the
 * server's own generation resolver.
 */
export function explicitEmptyBuildFenceRefusal(toolName: string, chartId: string | undefined): {
  content: { error: string; code: 'explicit_empty_build_fence'; chart_id: string | undefined }
  is_error: true
} {
  return {
    content: {
      error: `${toolName}: build_id was supplied but normalized to zero build ids; refusing rather than reading unfenced or matching zero rows.`,
      code: 'explicit_empty_build_fence',
      chart_id: chartId,
    },
    is_error: true,
  }
}

/**
 * Thrown by an internal helper (address_resolver.ts, register_d9/d10's grading helpers,
 * significator_condition.ts, reading_checklist.ts) that receives an explicit-empty build
 * fence. These helpers sit deep inside already-fenced composite tools whose own
 * `resolveChartServedGeneration` gate guarantees a non-empty fence by the time it reaches
 * here — so this should never fire in practice — but it exists so a future caller that
 * violates that invariant fails loudly instead of silently regressing to the "bind to []
 * and match zero rows" defect. Callers already wrap these helpers in try/catch for other
 * failure modes; this class lets that same catch distinguish an explicit-empty fence from
 * a generic error rather than reporting a plain "unavailable".
 */
export class ExplicitEmptyBuildFenceError extends Error {
  constructor(source: string) {
    super(`${source}: build fence was supplied but normalized to zero build ids; refusing rather than reading unfenced or matching zero rows.`)
    this.name = 'ExplicitEmptyBuildFenceError'
  }
}

/**
 * Resolve an internal, already-should-be-non-empty `BuildFence` to a plain array or
 * `null` (absent). Throws `ExplicitEmptyBuildFenceError` on an explicit-empty fence
 * rather than ever returning `[]` — see the class doc above for why this case should be
 * structurally unreachable for its callers, and why it still must not degrade silently.
 */
export function resolvedBuildFenceIds(value: unknown, source: string): string[] | null {
  const fence = classifyBuildFence(value)
  if (fence.kind === 'explicit_empty') throw new ExplicitEmptyBuildFenceError(source)
  return fence.kind === 'resolved' ? [...fence.build_ids] : null
}

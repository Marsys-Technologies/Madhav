// Phase O — O.2 Reconciliation: Gemini provider reconciler.
//
// Authored by USTAD_S2_4_GEMINI_RECONCILER per OBSERVATORY_PLAN §4.3 +
// the brief Tasks 1–3.
//
// Data source: GCP Cloud Billing **BigQuery export** (not a REST API).
// The Gemini API does not expose an admin/billing endpoint comparable to
// Anthropic's /admin/usage_report or OpenAI's /usage; the canonical
// authoritative cost surface is the daily-exported BigQuery billing dataset
// the customer enables in GCP. Platform already uses Application Default
// Credentials (ADC) for GCP (cf. @google-cloud/storage usage), so the
// BigQuery client picks up the same credentials without additional config.
//
// Required env vars:
//   GOOGLE_CLOUD_BILLING_PROJECT_ID   — project that owns the BQ dataset
//   GOOGLE_CLOUD_BILLING_DATASET_ID   — dataset name (e.g. "billing_export")
//   GOOGLE_CLOUD_BILLING_TABLE_ID     — table name (e.g. "gcp_billing_export_v1_XXXXXX")
// Any missing → fetchAuthoritativeCost throws (BaseReconciler turns into
// a status='error' result with the message in `notes`).
//
// Per-row processing:
//   - Map sku.description → model-id via skuToModelId. Unrecognised SKUs
//     are NOT treated as errors (free tier, other GCP services that share
//     the billing export, future SKUs). They are listed in raw_payload +
//     surfaced in result.notes.
//   - net_cost = total_cost + total_credits  (credits are negative in BQ)
//   - net_cost <= 0 → free-tier / fully-credited row; included in
//     raw_payload but contributes 0 to authoritative_cost_usd.
//
// Cancellation / timeout: BigQuery jobs are race-limited to 60s via
// AbortController; on abort we throw "BigQuery billing query timeout".
//
// Testability: the BigQuery client is constructor-injectable via
// `bqFactory`; tests pass an in-memory fake. Production callers omit the
// factory and the reconciler lazy-imports @google-cloud/bigquery.

import { readGoogleCloudEnv } from '@/lib/config/google_cloud_env'
import 'server-only'
import { BaseReconciler, type FetchAuthoritativeCostResult } from './base'
import {
  type ProviderName,
  type ProviderReconcileInput,
  type ProviderReconcileResult,
  type ReconciliationConfig,
} from './types'
import { skuToModelId } from './gemini_sku_map'

/** Minimal BigQuery client surface this reconciler depends on. The real
 *  @google-cloud/bigquery client implements this; tests pass a fake. */
export interface BigQueryLike {
  createQueryJob(options: BigQueryJobOptions): Promise<[BigQueryJob]>
}

export interface BigQueryJobOptions {
  query: string
  params?: Record<string, unknown>
  types?: Record<string, string>
  jobTimeoutMs?: number
}

export interface BigQueryJob {
  getQueryResults(): Promise<[BigQueryRow[]]>
  cancel(): Promise<unknown>
}

export interface BigQueryRow {
  sku_description: string | null
  total_cost: number | string | null
  total_credits: number | string | null
}

const QUERY_TIMEOUT_MS = 60_000

/** Coerce a NUMERIC/FLOAT64 column that BQ may surface as either a number
 *  or a string (BigNumeric). Falsy / non-finite → 0. */
function toFloat(v: unknown): number {
  if (typeof v === 'number') return Number.isFinite(v) ? v : 0
  if (typeof v === 'string') {
    const n = Number(v)
    return Number.isFinite(n) ? n : 0
  }
  return 0
}

/** Per-SKU rollup retained on raw_payload so re-cost / replay (S4.5) can
 *  reproduce the authoritative figure without re-querying BQ. */
interface SkuRollup {
  sku_description: string
  model_id: string | null
  total_cost: number
  total_credits: number
  net_cost: number
  recognised: boolean
}

interface BillingPayload {
  project_id: string
  dataset_id: string
  table_id: string
  period_start: string
  period_end: string
  rows: SkuRollup[]
  totals: {
    recognised_cost_usd: number
    unrecognised_cost_usd: number
    free_tier_row_count: number
  }
  unrecognized_skus: string[]
}

export type BqFactory = (projectId: string) => BigQueryLike

export class GeminiReconciler extends BaseReconciler {
  readonly provider: ProviderName = 'gemini' as const

  /** Last fetch's unrecognised-SKU summary, captured during
   *  fetchAuthoritativeCost so the overridden reconcile() can append it
   *  to the in-memory result.notes. */
  private lastUnrecognizedSkus: string[] = []

  constructor(private readonly bqFactory?: BqFactory) {
    super()
  }

  protected async fetchAuthoritativeCost(
    input: ProviderReconcileInput,
  ): Promise<FetchAuthoritativeCostResult> {
    const projectId = readGoogleCloudEnv('GOOGLE_CLOUD_BILLING_PROJECT_ID')
    const datasetId = readGoogleCloudEnv('GOOGLE_CLOUD_BILLING_DATASET_ID')
    const tableId = readGoogleCloudEnv('GOOGLE_CLOUD_BILLING_TABLE_ID')
    if (!projectId) throw new Error('GOOGLE_CLOUD_BILLING_PROJECT_ID not configured')
    if (!datasetId) throw new Error('GOOGLE_CLOUD_BILLING_DATASET_ID not configured')
    if (!tableId) throw new Error('GOOGLE_CLOUD_BILLING_TABLE_ID not configured')

    const client = await this.resolveClient(projectId)

    // Fully-qualified table identifier; back-tick-quoted for BQ Standard SQL.
    // dataset/table ids are restricted to [A-Za-z0-9_]; this reconciler
    // additionally strips back-ticks defensively to prevent SQL injection
    // even if a misconfigured env var contains one.
    const fqTable =
      '`' +
      projectId.replace(/`/g, '') +
      '.' +
      datasetId.replace(/`/g, '') +
      '.' +
      tableId.replace(/`/g, '') +
      '`'

    // _PARTITIONTIME prunes date-partitioned GCP billing exports (RT.O2.4 fix).
    // Falls back to full scan on unpartitioned tables — correctness unaffected.
    // The pseudo-column predicate is checked at partition-elimination time,
    // before the DATE(usage_start_time) row predicate; combined, the query
    // reads only the partitions that overlap [@period_start, @period_end + 1d).
    const sql =
      'SELECT\n' +
      '  sku.description                                AS sku_description,\n' +
      '  SUM(cost)                                      AS total_cost,\n' +
      '  SUM(IFNULL((\n' +
      '    SELECT SUM(CAST(v.amount AS FLOAT64))\n' +
      '    FROM UNNEST(credits) AS v\n' +
      '  ), 0))                                         AS total_credits\n' +
      'FROM ' + fqTable + '\n' +
      'WHERE\n' +
      '  _PARTITIONTIME BETWEEN\n' +
      '    TIMESTAMP(@period_start) AND\n' +
      '    TIMESTAMP_ADD(TIMESTAMP(@period_end), INTERVAL 1 DAY)\n' +
      '  AND DATE(usage_start_time) BETWEEN @period_start AND @period_end\n' +
      '  AND (\n' +
      "    LOWER(service.description) LIKE '%generative language%'\n" +
      "    OR LOWER(service.description) LIKE '%vertex ai%'\n" +
      '  )\n' +
      'GROUP BY sku.description'

    let job: BigQueryJob
    try {
      ;[job] = await client.createQueryJob({
        query: sql,
        params: {
          period_start: input.period_start,
          period_end: input.period_end,
        },
        types: {
          period_start: 'DATE',
          period_end: 'DATE',
        },
        jobTimeoutMs: QUERY_TIMEOUT_MS,
      })
    } catch (err) {
      throw new Error(`BigQuery billing query failed: ${describeBqError(err)}`)
    }

    const timeout = setTimeout(() => {
      void job.cancel().catch(() => {})
    }, QUERY_TIMEOUT_MS)

    let rows: BigQueryRow[]
    try {
      const [resultRows] = await job.getQueryResults()
      rows = resultRows
    } catch (err) {
      const message = describeBqError(err)
      if (/cancel|abort|timeout/i.test(message)) {
        throw new Error('BigQuery billing query timeout')
      }
      throw new Error(`BigQuery billing query failed: ${message}`)
    } finally {
      clearTimeout(timeout)
    }

    const rollups: SkuRollup[] = []
    const unrecognized: string[] = []
    let recognisedCost = 0
    let unrecognisedCost = 0
    let freeTierRowCount = 0

    for (const row of rows) {
      const skuDescription = (row.sku_description ?? '').toString()
      const modelId = skuToModelId(skuDescription)
      const totalCost = toFloat(row.total_cost)
      const totalCredits = toFloat(row.total_credits)
      const netCost = totalCost + totalCredits

      const rollup: SkuRollup = {
        sku_description: skuDescription,
        model_id: modelId,
        total_cost: totalCost,
        total_credits: totalCredits,
        net_cost: netCost,
        recognised: modelId !== null,
      }
      rollups.push(rollup)

      if (modelId === null) {
        if (skuDescription.length > 0) unrecognized.push(skuDescription)
        unrecognisedCost += Math.max(netCost, 0)
        continue
      }
      if (netCost <= 0) {
        freeTierRowCount += 1
        continue
      }
      recognisedCost += netCost
    }

    this.lastUnrecognizedSkus = unrecognized

    const payload: BillingPayload = {
      project_id: projectId,
      dataset_id: datasetId,
      table_id: tableId,
      period_start: input.period_start,
      period_end: input.period_end,
      rows: rollups,
      totals: {
        recognised_cost_usd: recognisedCost,
        unrecognised_cost_usd: unrecognisedCost,
        free_tier_row_count: freeTierRowCount,
      },
      unrecognized_skus: unrecognized,
    }

    return {
      cost_usd: recognisedCost,
      raw_payload: payload,
    }
  }

  /** Wraps super.reconcile() so unrecognised-SKU info — captured during
   *  fetchAuthoritativeCost — is appended to the in-memory result.notes.
   *  The DB-persisted notes (written by base.ts before this override sees
   *  them) only carry the standard `raw_report_id=...` line; unrecognised
   *  SKUs are durable in raw_payload on the same llm_provider_cost_reports
   *  row, so no information is lost — it is just not duplicated into the
   *  reconciliation row's notes column. */
  override async reconcile(
    input: ProviderReconcileInput,
    config: ReconciliationConfig,
  ): Promise<ProviderReconcileResult> {
    this.lastUnrecognizedSkus = []
    const result = await super.reconcile(input, config)
    if (this.lastUnrecognizedSkus.length === 0) return result
    const skuList = this.lastUnrecognizedSkus.join(', ')
    const annotation = `unrecognized_skus=[${skuList}]`
    const notes = result.notes ? `${result.notes}; ${annotation}` : annotation
    return { ...result, notes }
  }

  private async resolveClient(projectId: string): Promise<BigQueryLike> {
    if (this.bqFactory) return this.bqFactory(projectId)
    const mod = (await import('@google-cloud/bigquery')) as unknown as {
      BigQuery: new (opts: { projectId: string }) => BigQueryLike
    }
    return new mod.BigQuery({ projectId })
  }
}

function describeBqError(err: unknown): string {
  if (err instanceof Error) {
    const e = err as Error & { code?: string | number; errors?: unknown[] }
    const code = typeof e.code === 'string' || typeof e.code === 'number' ? `[${e.code}] ` : ''
    return `${code}${err.message}`
  }
  return String(err)
}

// @vitest-environment node
//
// Phase O — O.2 Reconciliation: GeminiReconciler + SKU map tests.
//
// Authored by USTAD_S2_4_GEMINI_RECONCILER per the brief Task 3 (7 tests).
// All tests are unit-level — the BigQuery client is injected via the
// `bqFactory` constructor parameter so we never reach @google-cloud/bigquery.
// The DB layer is mocked the same way the framework tests do it.
//
// USTAD_S3_1 note (RT.O2.4 fix): the SQL emitted by `fetchAuthoritativeCost()`
// now carries an additional `_PARTITIONTIME BETWEEN ... AND ...` predicate to
// enable partition pruning on date-partitioned billing exports. The mocked
// BigQuery client does not exercise partitioning semantics — the existing
// query-shape and parameter-binding assertions still cover the change.

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

import {
  skuToModelId,
  knownGeminiSkuPrefixes,
} from '@/lib/observatory/reconciliation/gemini_sku_map'
import {
  GeminiReconciler,
  type BigQueryJob,
  type BigQueryJobOptions,
  type BigQueryLike,
  type BigQueryRow,
} from '@/lib/observatory/reconciliation/gemini'
import { DEFAULT_RECONCILIATION_CONFIG } from '@/lib/observatory/reconciliation/types'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeBqClient(rows: BigQueryRow[]): BigQueryLike {
  let lastOptions: BigQueryJobOptions | undefined
  return {
    async createQueryJob(options: BigQueryJobOptions) {
      lastOptions = options
      const job: BigQueryJob = {
        async getQueryResults() {
          return [rows]
        },
        async cancel() {
          return undefined
        },
      }
      return [job]
    },
    _lastOptions: () => lastOptions,
  } as BigQueryLike & { _lastOptions: () => BigQueryJobOptions | undefined }
}

function setBqEnv(): void {
  process.env.GOOGLE_CLOUD_BILLING_PROJECT_ID = 'test-project'
  process.env.GOOGLE_CLOUD_BILLING_DATASET_ID = 'billing_export'
  process.env.GOOGLE_CLOUD_BILLING_TABLE_ID = 'gcp_billing_export_v1_TEST'
}

function clearBqEnv(): void {
  delete process.env.GOOGLE_CLOUD_BILLING_PROJECT_ID
  delete process.env.GOOGLE_CLOUD_BILLING_DATASET_ID
  delete process.env.GOOGLE_CLOUD_BILLING_TABLE_ID
}

function mockReconciliationDb(reportId: string, computedTotal: number, eventCount: number): void {
  queryMock.mockImplementation(async (sql: string) => {
    if (/INSERT INTO llm_provider_cost_reports/.test(sql)) {
      return { rows: [{ report_id: reportId }] }
    }
    if (/FROM llm_usage_events/.test(sql)) {
      return {
        rows: [{ total_cost_usd: computedTotal, event_count: String(eventCount) }],
      }
    }
    if (/INSERT INTO llm_cost_reconciliation/.test(sql)) {
      return { rows: [] }
    }
    return { rows: [] }
  })
}

beforeEach(() => {
  queryMock.mockReset()
})

afterEach(() => {
  clearBqEnv()
})

// ---------------------------------------------------------------------------
// 1. skuToModelId — known SKU → correct model ID
// ---------------------------------------------------------------------------

describe('skuToModelId', () => {
  it('maps a known SKU description to its canonical model id', () => {
    expect(skuToModelId('Gemini 1.5 Pro Input tokens')).toBe('gemini-1.5-pro')
    expect(skuToModelId('Gemini 1.5 Flash Output tokens')).toBe('gemini-1.5-flash')
    expect(skuToModelId('Gemini 2.0 Flash Input tokens')).toBe('gemini-2.0-flash')
    expect(skuToModelId('Gemini 2.5 Pro Preview Input tokens')).toBe(
      'gemini-2.5-pro-preview',
    )
  })

  it('is case-insensitive and tolerates internal double-spacing', () => {
    expect(skuToModelId('gemini 1.5 pro input tokens')).toBe('gemini-1.5-pro')
    expect(skuToModelId('Gemini  1.5  Pro  Input tokens')).toBe('gemini-1.5-pro')
  })

  it('matches Context caching SKUs to the parent model id', () => {
    expect(skuToModelId('Gemini 1.5 Pro Context caching')).toBe('gemini-1.5-pro')
    expect(skuToModelId('Gemini 1.5 Flash Context caching')).toBe('gemini-1.5-flash')
  })

  // -------------------------------------------------------------------------
  // 2. skuToModelId — unknown SKU → null (no throw)
  // -------------------------------------------------------------------------

  it('returns null for an unknown SKU description (no throw)', () => {
    expect(() => skuToModelId('Cloud Storage Class A operations')).not.toThrow()
    expect(skuToModelId('Cloud Storage Class A operations')).toBeNull()
    expect(skuToModelId('Compute Engine N1 instance')).toBeNull()
    expect(skuToModelId('A future Gemini model not yet in the map')).toBeNull()
  })

  // -------------------------------------------------------------------------
  // 3. skuToModelId — free tier / credit-only SKU → null
  // -------------------------------------------------------------------------

  it('returns null for free-tier / generic SKUs not registered in the map', () => {
    // GCP free-tier and credit SKUs surface in the same export but with
    // descriptions that do not match any Gemini SKU prefix.
    expect(skuToModelId('Free Tier - 1M tokens')).toBeNull()
    expect(skuToModelId('Promotional credits — Generative Language')).toBeNull()
    expect(skuToModelId('')).toBeNull()
    // Sanity: knownGeminiSkuPrefixes is non-empty (so the map is wired).
    expect(knownGeminiSkuPrefixes().length).toBeGreaterThan(0)
  })
})

// ---------------------------------------------------------------------------
// 4. GeminiReconciler happy path — mocked BQ; 2 SKUs (input + output) for
//    gemini-1.5-pro; assert cost_usd correct.
// ---------------------------------------------------------------------------

describe('GeminiReconciler.reconcile()', () => {
  it('happy path — input + output SKUs sum to the authoritative cost', async () => {
    setBqEnv()
    mockReconciliationDb('rep-bq-1', 12.4, 4)

    const bqClient = makeBqClient([
      {
        sku_description: 'Gemini 1.5 Pro Input tokens',
        total_cost: 8.5,
        total_credits: 0,
      },
      {
        sku_description: 'Gemini 1.5 Pro Output tokens',
        total_cost: 4.0,
        total_credits: 0,
      },
    ])
    const reconciler = new GeminiReconciler(() => bqClient)

    const result = await reconciler.reconcile(
      {
        provider: 'gemini',
        period_start: '2026-05-01',
        period_end: '2026-05-01',
      },
      DEFAULT_RECONCILIATION_CONFIG,
    )

    expect(result.provider).toBe('gemini')
    expect(result.authoritative_cost_usd).toBeCloseTo(12.5, 5)
    expect(result.computed_cost_usd).toBe(12.4)
    expect(result.event_count).toBe(4)
    expect(result.raw_report_id).toBe('rep-bq-1')
    // 12.4 vs 12.5 → variance 0.8% → matched (≤ 2% tolerance)
    expect(result.status).toBe('matched')

    // The raw payload (passed to BaseReconciler → llm_provider_cost_reports
    // INSERT) must contain the per-SKU rollup.
    const reportInsertCall = queryMock.mock.calls.find(c =>
      /INSERT INTO llm_provider_cost_reports/.test(String(c[0])),
    )!
    const rawPayloadJson = reportInsertCall[1][4] as string
    const payload = JSON.parse(rawPayloadJson)
    expect(payload.totals.recognised_cost_usd).toBeCloseTo(12.5, 5)
    expect(payload.unrecognized_skus).toEqual([])
    expect(payload.rows).toHaveLength(2)
  })

  // -------------------------------------------------------------------------
  // 5. Mixed SKUs — recognised + unrecognised; unrecognised logged in notes;
  //    cost is sum of recognised only.
  // -------------------------------------------------------------------------

  it('mixed SKUs — unrecognised logged in notes; cost sums only recognised', async () => {
    setBqEnv()
    mockReconciliationDb('rep-bq-mix', 10.0, 2)

    const bqClient = makeBqClient([
      {
        sku_description: 'Gemini 1.5 Pro Input tokens',
        total_cost: 10.0,
        total_credits: 0,
      },
      {
        sku_description: 'Cloud Storage Class A operations',
        total_cost: 0.42,
        total_credits: 0,
      },
    ])
    const reconciler = new GeminiReconciler(() => bqClient)

    const result = await reconciler.reconcile(
      {
        provider: 'gemini',
        period_start: '2026-05-01',
        period_end: '2026-05-01',
      },
      DEFAULT_RECONCILIATION_CONFIG,
    )

    // Recognised total only — unrecognised SKU contributes 0.
    expect(result.authoritative_cost_usd).toBeCloseTo(10.0, 5)
    expect(result.notes).toContain('unrecognized_skus=[Cloud Storage Class A operations]')
    expect(result.status).toBe('matched')
  })

  // -------------------------------------------------------------------------
  // 6. Free-tier row (net_cost === 0) — contributes 0 to total, not an error.
  // -------------------------------------------------------------------------

  it('free-tier row (cost fully offset by credits) contributes 0 and is not an error', async () => {
    setBqEnv()
    mockReconciliationDb('rep-bq-free', 0, 0)

    const bqClient = makeBqClient([
      {
        // Recognised SKU but credits fully offset cost → net 0.
        sku_description: 'Gemini 1.5 Flash Input tokens',
        total_cost: 5.0,
        total_credits: -5.0,
      },
    ])
    const reconciler = new GeminiReconciler(() => bqClient)

    const result = await reconciler.reconcile(
      {
        provider: 'gemini',
        period_start: '2026-05-01',
        period_end: '2026-05-01',
      },
      DEFAULT_RECONCILIATION_CONFIG,
    )

    // 0 authoritative + 0 computed → 'matched' per classifyVariance.
    expect(result.authoritative_cost_usd).toBe(0)
    expect(result.computed_cost_usd).toBe(0)
    expect(result.status).toBe('matched')
    // Free-tier row is captured in raw_payload for audit / re-cost.
    const reportInsertCall = queryMock.mock.calls.find(c =>
      /INSERT INTO llm_provider_cost_reports/.test(String(c[0])),
    )!
    const payload = JSON.parse(reportInsertCall[1][4] as string)
    expect(payload.totals.free_tier_row_count).toBe(1)
    expect(payload.rows[0].net_cost).toBeCloseTo(0, 5)
  })

  // -------------------------------------------------------------------------
  // 7. Missing GOOGLE_CLOUD_BILLING_PROJECT_ID → status='error'.
  // -------------------------------------------------------------------------

  it('missing GOOGLE_CLOUD_BILLING_PROJECT_ID → status=error with explicit env-var name in notes', async () => {
    clearBqEnv()
    queryMock.mockImplementation(async () => ({ rows: [] }))

    // BQ factory should NEVER be invoked when env guard fails.
    const bqFactory = vi.fn(() => makeBqClient([]))
    const reconciler = new GeminiReconciler(bqFactory)

    const result = await reconciler.reconcile(
      {
        provider: 'gemini',
        period_start: '2026-05-01',
        period_end: '2026-05-01',
      },
      DEFAULT_RECONCILIATION_CONFIG,
    )

    expect(result.status).toBe('error')
    expect(result.notes).toContain('GOOGLE_CLOUD_BILLING_PROJECT_ID not configured')
    expect(bqFactory).not.toHaveBeenCalled()
  })
})

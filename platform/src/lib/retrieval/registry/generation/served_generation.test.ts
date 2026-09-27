import { describe, expect, it, vi } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

import {
  chartServedGenerationFromRows,
  resolveChartServedGeneration,
  servedRowsBuildIdSql,
} from './served_generation'

const chartId = '482012f1-710e-4a25-994a-93821f5871aa'

function row(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    asset_id: 'ga_positions', partition_key: '__whole_asset__', receipt_version: 'v1',
    receipt_build_id: 'run-receipt', rows_build_id: 'run-receipt', receipt_state: 'proven',
    freshness_state: 'fresh', output_digest_spec_sha256: 'a'.repeat(64), spec_active: true,
    receipt_run_state: 'completed', receipt_asset_present: true, receipt_disposition: 'build',
    observed_at: '2026-09-07T02:00:00Z', ...overrides,
  }
}

describe('served generation classification', () => {
  it('refuses an asset whose partitions were served by different runs', () => {
    const generation = chartServedGenerationFromRows(chartId, ['ga_positions'], [
      row({ partition_key: 'lahiri', rows_build_id: 'run-a', receipt_build_id: 'run-a' }),
      row({ partition_key: 'raman', rows_build_id: 'run-b', receipt_build_id: 'run-b' }),
    ])
    expect(generation.assets['ga_positions']).toMatchObject({ state: 'unresolved', reason: 'partition_generation_split' })
    expect(generation.served_build_ids).toEqual([])
  })

  it('reports an unservable disposition distinctly from a broken skip chain', () => {
    const generation = chartServedGenerationFromRows(chartId, null, [
      row({ asset_id: 'ga_a', rows_build_id: null, receipt_disposition: 'withheld_protected' }),
      row({ asset_id: 'ga_b', rows_build_id: null, receipt_disposition: 'skip_no_delta' }),
      row({ asset_id: 'ga_c', receipt_asset_present: false, rows_build_id: null }),
    ])
    expect(generation.assets['ga_a']).toMatchObject({ reason: 'receipt_disposition_unservable' })
    expect(generation.assets['ga_b']).toMatchObject({ reason: 'skip_chain_writer_missing' })
    expect(generation.assets['ga_c']).toMatchObject({ reason: 'receipt_run_asset_missing' })
  })

  it('includes unresolved assets in the generation identity', () => {
    const resolvedOnly = chartServedGenerationFromRows(chartId, ['ga_positions'], [row()])
    const withGap = chartServedGenerationFromRows(chartId, ['ga_positions', 'ga_strength'], [row()])
    expect(withGap.served_build_ids).toEqual(resolvedOnly.served_build_ids)
    expect(withGap.generation_hash).not.toBe(resolvedOnly.generation_hash)
  })

  it('propagates query failure so callers fail closed', async () => {
    await expect(resolveChartServedGeneration(chartId, null, async () => { throw new Error('db down') }))
      .rejects.toThrow('db down')
  })

  it('exposes one reviewed rows-build rule that only trusts completed build dispositions', () => {
    const sql = servedRowsBuildIdSql({ receipt: 'r', receiptRun: 'rr', receiptAsset: 'ra' })
    expect(sql).toContain("WHEN ra.disposition = 'skip_no_delta'")
    expect(sql).toContain("writer_run.state = 'completed'")
    expect(sql).toContain("(writer_asset.disposition IS NULL OR writer_asset.disposition = 'build')")
    expect(sql).toContain("AND ra.state = 'complete' THEN r.build_id")
  })
})

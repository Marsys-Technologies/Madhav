import { describe, expect, it, vi } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

import {
  chartServedGenerationFromRows,
  classifyBuildFence,
  ExplicitEmptyBuildFenceError,
  explicitEmptyBuildFenceRefusal,
  resolveChartServedGeneration,
  resolvedBuildFenceIds,
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

  it('exposes one reviewed rows-build rule: completed build writes only, voided by a later attempt', () => {
    // Behaviour is proven against PostgreSQL in served_generation.db.test.ts; this guards the
    // rule's load-bearing clauses when that suite cannot run.
    const sql = servedRowsBuildIdSql({ receipt: 'r', receiptRun: 'rr', receiptAsset: 'ra' })
    expect(sql).toContain("WHEN ra.disposition = 'skip_no_delta'")
    expect(sql).toContain("writer_asset.state = 'complete'")
    expect(sql).not.toContain("writer_run.state = 'completed'")
    expect(sql).toContain("(writer_asset.disposition IS NULL OR writer_asset.disposition = 'build')")
    expect(sql).toContain("AND ra.state = 'complete' THEN r.build_id")
    expect(sql).toContain("attempt.disposition IS DISTINCT FROM 'skip_no_delta'")
  })

  it('withholds a shared run from the multi-writer fence and names both sides', () => {
    const generation = chartServedGenerationFromRows(chartId, null, [
      row({ asset_id: 'ga_structural', rows_build_id: 'run-shared', receipt_build_id: 'run-shared' }),
      row({ asset_id: 'ga_vichara', rows_build_id: 'run-shared', receipt_build_id: 'run-shared', freshness_state: 'stale' }),
      row({ asset_id: 'ga_dashas', rows_build_id: 'run-own', receipt_build_id: 'run-own' }),
      row({ asset_id: 'ga_strength', rows_build_id: null, writer_run_id: 'run-other', receipt_build_id: 'run-other' }),
    ])
    expect(generation.assets['ga_strength']).toMatchObject({ reason: 'intervening_attempt_unreceipted' })
    expect(generation.served_build_ids).toEqual(['run-own'])
    expect(generation.withheld_builds).toEqual([
      { build_id: 'run-shared', unresolved_asset_ids: ['ga_vichara'], resolved_asset_ids: ['ga_structural'] },
    ])
  })
})

// ── Explicit-empty build-fence semantics (R3 boundary, native ruling) ─────────────────────
//
// classifyBuildFence's three states must never collapse into each other: `absent` (no fence
// supplied — a legitimate "read unfenced" fallback) is not `explicit_empty` (a fence WAS
// supplied but normalized to zero build ids — must never read unfenced or bind to `[]` and
// match zero rows as if that were genuine absence), and neither is the ordinary `resolved`
// case.
describe('classifyBuildFence', () => {
  it('classifies an absent fence (undefined, null, empty string)', () => {
    expect(classifyBuildFence(undefined)).toEqual({ kind: 'absent' })
    expect(classifyBuildFence(null)).toEqual({ kind: 'absent' })
    expect(classifyBuildFence('')).toEqual({ kind: 'absent' })
  })

  it('classifies a scalar fence as resolved with one build id', () => {
    expect(classifyBuildFence('11111111-1111-4111-8111-111111111111'))
      .toEqual({ kind: 'resolved', build_ids: ['11111111-1111-4111-8111-111111111111'] })
  })

  it('canonicalizes a duplicate/noncanonical (unsorted, repeated) fence array', () => {
    const a = '22222222-2222-4222-8222-222222222222'
    const b = '11111111-1111-4111-8111-111111111111'
    expect(classifyBuildFence([a, b, a, b])).toEqual({ kind: 'resolved', build_ids: [b, a] })
  })

  it('classifies an explicit empty array as explicit_empty, never absent', () => {
    expect(classifyBuildFence([])).toEqual({ kind: 'explicit_empty' })
  })

  it('classifies an array that normalizes to empty (all null/undefined/empty-string items) as explicit_empty', () => {
    expect(classifyBuildFence([null, undefined, ''])).toEqual({ kind: 'explicit_empty' })
  })

  it('never returns a bare array-or-null shape that could be mistaken for the old buildFenceIds contract', () => {
    // Regression guard for the exact defect this type exists to close: `resolved` with an
    // empty array must be structurally impossible — explicit_empty is a distinct tag, not a
    // `resolved` state whose build_ids array happens to be empty.
    const explicit = classifyBuildFence([])
    if (explicit.kind === 'resolved') {
      expect((explicit as { build_ids: readonly string[] }).build_ids.length).toBeGreaterThan(0)
    }
    expect(explicit.kind).toBe('explicit_empty')
  })
})

describe('explicitEmptyBuildFenceRefusal', () => {
  it('returns a distinct, typed refusal — never a happy-path empty result', () => {
    const refusal = explicitEmptyBuildFenceRefusal('get_strength', chartId)
    expect(refusal.is_error).toBe(true)
    expect(refusal.content.code).toBe('explicit_empty_build_fence')
    expect(refusal.content.chart_id).toBe(chartId)
    expect(refusal.content.error).toContain('get_strength')
  })
})

describe('resolvedBuildFenceIds (internal, already-should-be-non-empty callers)', () => {
  it('passes through absent as null', () => {
    expect(resolvedBuildFenceIds(undefined, 'test')).toBeNull()
  })

  it('passes through a resolved fence as a plain array', () => {
    expect(resolvedBuildFenceIds(['b', 'a'], 'test')).toEqual(['a', 'b'])
  })

  it('throws ExplicitEmptyBuildFenceError on an explicit-empty fence rather than returning []', () => {
    expect(() => resolvedBuildFenceIds([], 'test.caller')).toThrow(ExplicitEmptyBuildFenceError)
    expect(() => resolvedBuildFenceIds([], 'test.caller')).toThrow(/test\.caller/)
  })
})

import { randomUUID } from 'node:crypto'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { Pool } from 'pg'
import { resolveChartServedGeneration, servedGenerationIdentity } from './served_generation'

// Localhost-only disposable schema: proves the resolver's real SQL against the production
// DDL for build_runs, build_run_assets, provenance receipts, freshness, and digest specs.
const DATABASE_URL = process.env.PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL
const run = DATABASE_URL ? describe : describe.skip
const schema = `purna_served_generation_${randomUUID().replaceAll('-', '')}`
const chartId = '482012f1-710e-4a25-994a-93821f5871aa'

const runPositions = '10000000-0000-4000-8000-000000000001' // builds ga_positions (rows A)
const runDashas = '10000000-0000-4000-8000-000000000002' // builds ga_dashas
const runSkip = '10000000-0000-4000-8000-000000000003' // skip_no_delta re-receipts ga_positions
const runLatest = '10000000-0000-4000-8000-000000000004' // latest completed run: bo_grounding only
const runFailed = '10000000-0000-4000-8000-000000000005' // failed run that receipted ga_vichara
const runOrphanSkip = '10000000-0000-4000-8000-000000000006' // skip with no earlier writer
const runRebuild = '10000000-0000-4000-8000-000000000007' // later rebuild of ga_positions

const spec = (n: number) => n.toString(16).padStart(64, '0')
const specs: Record<string, string> = {
  ga_positions: spec(1), ga_dashas: spec(2), bo_grounding: spec(3), ga_structural: spec(4),
  ga_vichara: spec(5), ga_strength: spec(6), ga_sensitive: spec(7),
}
const retiredStrengthSpec = spec(66)

function assertDisposableDatabase(url: string): void {
  const parsed = new URL(url)
  if (!['localhost', '127.0.0.1', '::1'].includes(parsed.hostname)) {
    throw new Error('PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL must target localhost')
  }
  if (!parsed.pathname.endsWith('/purna_overlay_test')) {
    throw new Error('PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL must target database purna_overlay_test')
  }
}

function migration(relativePath: string): string {
  return readFileSync(path.join(process.cwd(), relativePath), 'utf8')
}

run('served generation resolver against disposable PostgreSQL', () => {
  let admin: Pool
  let scoped: Pool
  const query = async (sql: string, params: unknown[] = []) => scoped.query(sql, params)

  async function buildRun(id: string, state: string, startedAt: string, endedAt: string | null) {
    await query(`
      INSERT INTO build_runs(id, chart_id, scope, action, state, plan, triggered_by, started_at, ended_at)
      VALUES ($1, $2, 'asset', 'build', $3, '{}'::jsonb, 'test', $4, $5)`, [id, chartId, state, startedAt, endedAt])
  }
  async function runAsset(runId: string, assetId: string, state: string, disposition: string | null, startedAt: string, endedAt: string | null) {
    await query(`
      INSERT INTO build_run_assets(run_id, asset_id, position, state, disposition, started_at, ended_at)
      VALUES ($1, $2, 0, $3, $4, $5, $6)`, [runId, assetId, state, disposition, startedAt, endedAt])
  }
  async function receipt(assetId: string, buildId: string, observedAt: string, options: {
    freshness?: string; state?: string; spec?: string; partition?: string
  } = {}) {
    const partition = options.partition ?? '__whole_asset__'
    await query(`
      INSERT INTO asset_provenance_receipts
        (asset_id, chart_id, partition_key, receipt_version, receipt_state, build_id, output_digest_spec_sha256, unknown_reasons, observed_at)
      VALUES ($1, $2, $3, 'v1', $4, $5, $6, '[]', $7)
      ON CONFLICT (asset_id, scope_key, partition_key) DO UPDATE
        SET build_id = EXCLUDED.build_id, observed_at = EXCLUDED.observed_at,
            receipt_state = EXCLUDED.receipt_state, output_digest_spec_sha256 = EXCLUDED.output_digest_spec_sha256`,
    [assetId, chartId, partition, options.state ?? 'proven', buildId, options.spec ?? specs[assetId], observedAt])
    await query(`
      INSERT INTO asset_freshness(asset_id, chart_id, partition_key, freshness_state, reasons, receipt_version, observed_at)
      VALUES ($1, $2, $3, $4, '[]', 'v1', $5)
      ON CONFLICT (asset_id, scope_key, partition_key) DO UPDATE
        SET freshness_state = EXCLUDED.freshness_state, observed_at = EXCLUDED.observed_at`,
    [assetId, chartId, partition, options.freshness ?? 'fresh', observedAt])
  }

  beforeAll(async () => {
    assertDisposableDatabase(DATABASE_URL!)
    admin = new Pool({ connectionString: DATABASE_URL!, max: 1 })
    await admin.query(`CREATE SCHEMA ${schema}`)
    scoped = new Pool({ connectionString: DATABASE_URL!, max: 1, options: `-c search_path=${schema}` })
    await query(`
      CREATE TABLE charts (
        id uuid PRIMARY KEY, birth_date date, birth_time time, birth_lat numeric, birth_lng numeric,
        birth_place text, timezone_id text, name text, subject_name text, preferred_name text
      );
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, depends_on jsonb, natural_key_partition text, health_probe text,
        integrity_check_sql text, target_floor integer, asset_kind text, asset_type text, scope text,
        has_writer boolean, is_active boolean, target_table text
      );
      CREATE TABLE asset_throughput (asset_id text PRIMARY KEY);
    `)
    const seededSpecAssets = [...migration('supabase/migrations/598_nirmana_output_digest_specs.sql')
      .matchAll(/'([a-z0-9_]+)'\s*,\s*'[a-f0-9]{64}'/g)].map((match) => match[1]!)
    await query('INSERT INTO asset_registry(asset_id) SELECT unnest($1::text[]) ON CONFLICT DO NOTHING',
      [[...new Set([...seededSpecAssets, ...Object.keys(specs)])]])
    await query(migration('supabase/migrations/171_build_runs.sql'))
    await query(migration('supabase/migrations/596_nirmana_provenance_receipts.sql'))
    await query(migration('supabase/migrations/598_nirmana_output_digest_specs.sql'))
    await query(migration('migrations/640_nirmana_owave_wp1_output_changed.sql'))
    await query(migration('migrations/641_nirmana_owave_wp2_disposition.sql'))
    await query('INSERT INTO charts(id, name) VALUES ($1, $2)', [chartId, 'Disposable Generation'])
    await query(`INSERT INTO asset_output_digest_specs(asset_id, spec_sha256, spec, reviewed_at, retired_at)
                 VALUES ('ga_strength', $1, '{}'::jsonb, '2026-09-01T00:00:00Z', '2026-09-19T00:00:00Z')`, [retiredStrengthSpec])
    for (const [assetId, sha] of Object.entries(specs)) {
      await query(`INSERT INTO asset_output_digest_specs(asset_id, spec_sha256, spec, reviewed_at)
                   VALUES ($1, $2, '{}'::jsonb, '2026-09-19T00:00:00Z')`, [assetId, sha])
    }

    await buildRun(runPositions, 'completed', '2026-09-07T01:00:00Z', '2026-09-07T02:00:00Z')
    await runAsset(runPositions, 'ga_positions', 'complete', 'build', '2026-09-07T01:00:00Z', '2026-09-07T02:00:00Z')
    await buildRun(runDashas, 'completed', '2026-09-08T01:00:00Z', '2026-09-08T02:00:00Z')
    await runAsset(runDashas, 'ga_dashas', 'complete', null, '2026-09-08T01:00:00Z', '2026-09-08T02:00:00Z')
    await receipt('ga_dashas', runDashas, '2026-09-08T02:00:00Z')
    await buildRun(runSkip, 'completed', '2026-09-10T01:00:00Z', '2026-09-10T02:00:00Z')
    await runAsset(runSkip, 'ga_positions', 'complete', 'skip_no_delta', '2026-09-10T01:00:00Z', '2026-09-10T01:05:00Z')
    await receipt('ga_positions', runSkip, '2026-09-10T01:05:00Z')
    await buildRun(runLatest, 'completed', '2026-09-12T01:00:00Z', '2026-09-12T02:00:00Z')
    await runAsset(runLatest, 'bo_grounding', 'complete', 'build', '2026-09-12T01:00:00Z', '2026-09-12T02:00:00Z')
    await receipt('bo_grounding', runLatest, '2026-09-12T02:00:00Z')
    await buildRun(runFailed, 'failed', '2026-09-11T01:00:00Z', '2026-09-11T02:00:00Z')
    await runAsset(runFailed, 'ga_vichara', 'complete', 'build', '2026-09-11T01:00:00Z', '2026-09-11T01:30:00Z')
    await receipt('ga_vichara', runFailed, '2026-09-11T01:30:00Z')
    await buildRun(runOrphanSkip, 'completed', '2026-09-09T01:00:00Z', '2026-09-09T02:00:00Z')
    await runAsset(runOrphanSkip, 'ga_sensitive', 'complete', 'skip_no_delta', '2026-09-09T01:00:00Z', '2026-09-09T01:05:00Z')
    await receipt('ga_sensitive', runOrphanSkip, '2026-09-09T01:05:00Z')
    await runAsset(runDashas, 'ga_structural', 'complete', 'build', '2026-09-08T01:00:00Z', '2026-09-08T02:00:00Z')
    await receipt('ga_structural', runDashas, '2026-09-08T02:00:00Z', { freshness: 'stale' })
    await runAsset(runDashas, 'ga_strength', 'complete', 'build', '2026-09-08T01:00:00Z', '2026-09-08T02:00:00Z')
    await receipt('ga_strength', runDashas, '2026-09-08T02:00:00Z', { spec: retiredStrengthSpec })
  }, 30_000)

  afterAll(async () => {
    await scoped?.end()
    if (admin) {
      await admin.query(`DROP SCHEMA IF EXISTS ${schema} CASCADE`)
      await admin.end()
    }
  })

  it('binds every asset to the run that wrote its rows, never the chart-wide latest completed run', async () => {
    const generation = await resolveChartServedGeneration(chartId, ['ga_positions', 'ga_dashas', 'bo_grounding'], query)

    expect(generation.assets['ga_positions']).toMatchObject({
      state: 'resolved', receipt_build_id: runSkip, rows_build_id: runPositions, rows_binding: 'skip_no_delta_writer',
    })
    expect(generation.assets['ga_dashas']).toMatchObject({
      state: 'resolved', receipt_build_id: runDashas, rows_build_id: runDashas, rows_binding: 'receipt_run_wrote_rows',
    })
    expect(generation.assets['bo_grounding']).toMatchObject({ state: 'resolved', rows_build_id: runLatest })
    expect(generation.served_build_ids).toEqual([runPositions, runDashas, runLatest].sort())
    expect(servedGenerationIdentity(generation)).toBe(`generation:${generation.generation_hash}`)
  })

  it('fails closed per asset with a typed reason instead of guessing', async () => {
    const generation = await resolveChartServedGeneration(chartId,
      ['ga_vichara', 'ga_sensitive', 'ga_structural', 'ga_strength', 'ga_sensitive_degree'], query)

    expect(generation.assets['ga_vichara']).toMatchObject({ state: 'unresolved', reason: 'receipt_run_not_completed' })
    expect(generation.assets['ga_sensitive']).toMatchObject({ state: 'unresolved', reason: 'skip_chain_writer_missing' })
    expect(generation.assets['ga_structural']).toMatchObject({ state: 'unresolved', reason: 'receipt_not_fresh' })
    expect(generation.assets['ga_strength']).toMatchObject({ state: 'unresolved', reason: 'receipt_spec_retired' })
    expect(generation.assets['ga_sensitive_degree']).toMatchObject({ state: 'unresolved', reason: 'no_chart_receipt' })
    expect(generation.served_build_ids).toEqual([])
    expect(servedGenerationIdentity(generation)).toBeNull()
  })

  it('resolves every chart receipt when no asset list is supplied', async () => {
    const generation = await resolveChartServedGeneration(chartId, null, query)
    expect(Object.keys(generation.assets)).toEqual([
      'bo_grounding', 'ga_dashas', 'ga_positions', 'ga_sensitive', 'ga_strength', 'ga_structural', 'ga_vichara',
    ])
    expect(generation.served_build_ids).toEqual([runPositions, runDashas, runLatest].sort())
  })

  it('changes generation identity when a rebuild supersedes the served rows', async () => {
    const before = await resolveChartServedGeneration(chartId, ['ga_positions', 'ga_dashas'], query)
    await buildRun(runRebuild, 'completed', '2026-09-13T01:00:00Z', '2026-09-13T02:00:00Z')
    await runAsset(runRebuild, 'ga_positions', 'complete', 'build', '2026-09-13T01:00:00Z', '2026-09-13T02:00:00Z')
    await receipt('ga_positions', runRebuild, '2026-09-13T02:00:00Z')
    try {
      const after = await resolveChartServedGeneration(chartId, ['ga_positions', 'ga_dashas'], query)
      expect(after.assets['ga_positions']).toMatchObject({ rows_build_id: runRebuild, rows_binding: 'receipt_run_wrote_rows' })
      expect(after.generation_hash).not.toBe(before.generation_hash)
    } finally {
      await receipt('ga_positions', runSkip, '2026-09-10T01:05:00Z')
      await query('DELETE FROM build_runs WHERE id = $1', [runRebuild])
    }
  })
})

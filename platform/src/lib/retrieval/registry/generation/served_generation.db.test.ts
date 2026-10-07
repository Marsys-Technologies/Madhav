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

  async function buildRun(id: string, state: string, startedAt: string, endedAt: string | null, chart = chartId) {
    await query(`
      INSERT INTO build_runs(id, chart_id, scope, action, state, plan, triggered_by, started_at, ended_at)
      VALUES ($1, $2, 'asset', 'build', $3, '{}'::jsonb, 'test', $4, $5)`, [id, chart, state, startedAt, endedAt])
  }
  async function runAsset(runId: string, assetId: string, state: string, disposition: string | null, startedAt: string, endedAt: string | null) {
    await query(`
      INSERT INTO build_run_assets(run_id, asset_id, position, state, disposition, started_at, ended_at)
      VALUES ($1, $2, 0, $3, $4, $5, $6)`, [runId, assetId, state, disposition, startedAt, endedAt])
  }
  async function receipt(assetId: string, buildId: string, observedAt: string, options: {
    freshness?: string; state?: string; spec?: string; partition?: string; chart?: string
  } = {}) {
    const chart = options.chart ?? chartId
    const partition = options.partition ?? '__whole_asset__'
    await query(`
      INSERT INTO asset_provenance_receipts
        (asset_id, chart_id, partition_key, receipt_version, receipt_state, build_id, output_digest_spec_sha256, unknown_reasons, observed_at)
      VALUES ($1, $2, $3, 'v1', $4, $5, $6, '[]', $7)
      ON CONFLICT (asset_id, scope_key, partition_key) DO UPDATE
        SET build_id = EXCLUDED.build_id, observed_at = EXCLUDED.observed_at,
            receipt_state = EXCLUDED.receipt_state, output_digest_spec_sha256 = EXCLUDED.output_digest_spec_sha256`,
    [assetId, chart, partition, options.state ?? 'proven', buildId, options.spec ?? specs[assetId], observedAt])
    await query(`
      INSERT INTO asset_freshness(asset_id, chart_id, partition_key, freshness_state, reasons, receipt_version, observed_at)
      VALUES ($1, $2, $3, $4, '[]', 'v1', $5)
      ON CONFLICT (asset_id, scope_key, partition_key) DO UPDATE
        SET freshness_state = EXCLUDED.freshness_state, observed_at = EXCLUDED.observed_at`,
    [assetId, chart, partition, options.freshness ?? 'fresh', observedAt])
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
      CREATE TABLE asset_throughput (chart_id uuid, asset_id text NOT NULL, state text);
      CREATE UNIQUE INDEX asset_throughput_per_chart_idx ON asset_throughput (chart_id, asset_id) WHERE chart_id IS NOT NULL;
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
    await query(migration('supabase/migrations/499_orchestrator_event_register.sql'))
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

    // A failed run's receipt serves only for an asset that itself finished (N-208). ga_vichara's own
    // asset row is complete but nothing records a success outcome for it, so it fails closed.
    expect(generation.assets['ga_vichara']).toMatchObject({ state: 'unresolved', reason: 'receipt_asset_not_complete' })
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
    // ga_structural (stale) and ga_strength (retired spec) still hold rows under runDashas, so
    // that run is withheld from the multi-writer fence even though ga_dashas itself resolves.
    expect(generation.assets['ga_dashas']).toMatchObject({ state: 'resolved', rows_build_id: runDashas })
    expect(generation.served_build_ids).toEqual([runPositions, runLatest].sort())
    expect(generation.withheld_builds).toEqual([
      { build_id: runDashas, unresolved_asset_ids: ['ga_strength', 'ga_structural'], resolved_asset_ids: ['ga_dashas'] },
    ])
  })

  // Review findings on the R1 boundary, each on its own disposable chart.
  const run = (n: number) => `20000000-0000-4000-8000-${String(n).padStart(12, '0')}`

  it('binds a no-delta receipt to the latest completed write even when that write\'s run failed (B1)', async () => {
    const chart = '30000000-0000-4000-8000-000000000001'
    await query('INSERT INTO charts(id, name) VALUES ($1, $2)', [chart, 'B1'])
    await buildRun(run(1), 'completed', '2026-09-01T01:00:00Z', '2026-09-01T02:00:00Z', chart)
    await runAsset(run(1), 'ga_positions', 'complete', 'build', '2026-09-01T01:00:00Z', '2026-09-01T02:00:00Z')
    // W1 rewrote ga_positions completely; another asset failed, so the run ended `failed`.
    await buildRun(run(2), 'failed', '2026-09-02T01:00:00Z', '2026-09-02T03:00:00Z', chart)
    await runAsset(run(2), 'ga_positions', 'complete', 'build', '2026-09-02T01:00:00Z', '2026-09-02T02:00:00Z')
    await buildRun(run(3), 'completed', '2026-09-03T01:00:00Z', '2026-09-03T02:00:00Z', chart)
    await runAsset(run(3), 'ga_positions', 'complete', 'skip_no_delta', '2026-09-03T01:00:00Z', '2026-09-03T01:05:00Z')
    await receipt('ga_positions', run(3), '2026-09-03T01:05:00Z', { chart })

    const generation = await resolveChartServedGeneration(chart, ['ga_positions'], query)
    expect(generation.assets['ga_positions']).toMatchObject({ state: 'resolved', rows_build_id: run(2), rows_binding: 'skip_no_delta_writer' })
  })

  it('refuses rows a later failed attempt may have partially rewritten, even after a no-delta re-receipt (M2)', async () => {
    const chart = '30000000-0000-4000-8000-000000000002'
    await query('INSERT INTO charts(id, name) VALUES ($1, $2)', [chart, 'M2'])
    await buildRun(run(11), 'completed', '2026-09-01T01:00:00Z', '2026-09-01T02:00:00Z', chart)
    await runAsset(run(11), 'ga_positions', 'complete', 'build', '2026-09-01T01:00:00Z', '2026-09-01T02:00:00Z')
    await buildRun(run(12), 'failed', '2026-09-02T01:00:00Z', '2026-09-02T02:00:00Z', chart)
    await runAsset(run(12), 'ga_positions', 'error', 'build', '2026-09-02T01:00:00Z', '2026-09-02T01:30:00Z')
    await buildRun(run(13), 'completed', '2026-09-03T01:00:00Z', '2026-09-03T02:00:00Z', chart)
    await runAsset(run(13), 'ga_positions', 'complete', 'skip_no_delta', '2026-09-03T01:00:00Z', '2026-09-03T01:05:00Z')
    await receipt('ga_positions', run(13), '2026-09-03T01:05:00Z', { chart })
    // A later completed build that never issued its own receipt replaced the receipted rows.
    await buildRun(run(14), 'completed', '2026-09-01T03:00:00Z', '2026-09-01T04:00:00Z', chart)
    await runAsset(run(14), 'ga_dashas', 'complete', 'build', '2026-09-01T03:00:00Z', '2026-09-01T03:30:00Z')
    await receipt('ga_dashas', run(14), '2026-09-01T03:30:00Z', { chart })
    await buildRun(run(15), 'completed', '2026-09-04T01:00:00Z', '2026-09-04T02:00:00Z', chart)
    await runAsset(run(15), 'ga_dashas', 'complete', 'build', '2026-09-04T01:00:00Z', '2026-09-04T01:30:00Z')

    const generation = await resolveChartServedGeneration(chart, ['ga_positions', 'ga_dashas'], query)
    expect(generation.assets['ga_positions']).toMatchObject({ state: 'unresolved', reason: 'intervening_attempt_unreceipted' })
    expect(generation.assets['ga_dashas']).toMatchObject({ state: 'unresolved', reason: 'intervening_attempt_unreceipted' })
  })

  it('withholds a run shared with an unresolved asset from the multi-writer fence (M1)', async () => {
    const chart = '30000000-0000-4000-8000-000000000003'
    await query('INSERT INTO charts(id, name) VALUES ($1, $2)', [chart, 'M1'])
    await buildRun(run(21), 'completed', '2026-09-01T01:00:00Z', '2026-09-01T02:00:00Z', chart)
    await runAsset(run(21), 'ga_structural', 'complete', 'build', '2026-09-01T01:00:00Z', '2026-09-01T01:30:00Z')
    await runAsset(run(21), 'ga_vichara', 'complete', 'build', '2026-09-01T01:30:00Z', '2026-09-01T02:00:00Z')
    await receipt('ga_structural', run(21), '2026-09-01T01:30:00Z', { chart })
    await receipt('ga_vichara', run(21), '2026-09-01T02:00:00Z', { chart, freshness: 'stale' })
    await buildRun(run(22), 'completed', '2026-09-02T01:00:00Z', '2026-09-02T02:00:00Z', chart)
    await runAsset(run(22), 'ga_dashas', 'complete', 'build', '2026-09-02T01:00:00Z', '2026-09-02T02:00:00Z')
    await receipt('ga_dashas', run(22), '2026-09-02T02:00:00Z', { chart })

    const generation = await resolveChartServedGeneration(chart, null, query)
    expect(generation.assets['ga_structural']).toMatchObject({ state: 'resolved', rows_build_id: run(21) })
    expect(generation.assets['ga_vichara']).toMatchObject({ state: 'unresolved', reason: 'receipt_not_fresh' })
    expect(generation.served_build_ids).toEqual([run(22)])
    expect(generation.withheld_builds).toEqual([
      { build_id: run(21), unresolved_asset_ids: ['ga_vichara'], resolved_asset_ids: ['ga_structural'] },
    ])
  })

  // ── Per-asset served fence (N-208): one failed asset must not unserve the run's finished assets ──
  describe('per-asset fence on a partially failed run', () => {
    const fchart = '40000000-0000-4000-8000-000000000001'
    const q = (n: number) => `50000000-0000-4000-8000-${String(n).padStart(12, '0')}`
    const outcome = (chart: string, assetId: string, state: string) =>
      query('INSERT INTO asset_throughput(chart_id, asset_id, state) VALUES ($1, $2, $3)', [chart, assetId, state])

    it('serves an asset that completed in a failed run, refuses its failed, held-back and unrecorded siblings', async () => {
      await query('INSERT INTO charts(id, name) VALUES ($1, $2)', [fchart, 'N208'])
      // Q: an earlier completed run built ga_dashas, which the failed pass then tried to rebuild.
      await buildRun(q(1), 'completed', '2026-09-01T01:00:00Z', '2026-09-01T02:00:00Z', fchart)
      await runAsset(q(1), 'ga_dashas', 'complete', 'build', '2026-09-01T01:00:00Z', '2026-09-01T02:00:00Z')
      await receipt('ga_dashas', q(1), '2026-09-01T02:00:00Z', { chart: fchart })
      await outcome(fchart, 'ga_dashas', 'error')
      // R: ONE run of the pass; it failed because ga_dashas errored.
      await buildRun(q(2), 'failed', '2026-09-05T01:00:00Z', '2026-09-05T05:00:00Z', fchart)
      await runAsset(q(2), 'ga_positions', 'complete', 'build', '2026-09-05T01:00:00Z', '2026-09-05T02:00:00Z')
      await receipt('ga_positions', q(2), '2026-09-05T02:00:00Z', { chart: fchart })
      await outcome(fchart, 'ga_positions', 'lit')
      await runAsset(q(2), 'ga_dashas', 'error', 'build', '2026-09-05T02:00:00Z', '2026-09-05T03:00:00Z')
      // build_run_assets says 'complete' for a build the orchestrator held back as 'incomplete'.
      await runAsset(q(2), 'ga_vichara', 'complete', 'build', '2026-09-05T03:00:00Z', '2026-09-05T04:00:00Z')
      await receipt('ga_vichara', q(2), '2026-09-05T04:00:00Z', { chart: fchart })
      await outcome(fchart, 'ga_vichara', 'incomplete')
      await runAsset(q(2), 'ga_strength', 'complete', 'build', '2026-09-05T03:00:00Z', '2026-09-05T04:30:00Z')
      await receipt('ga_strength', q(2), '2026-09-05T04:30:00Z', { chart: fchart })
      // no asset_throughput row at all for ga_strength: no recorded outcome, fail closed
      await runAsset(q(2), 'ga_structural', 'skipped', null, '2026-09-05T04:30:00Z', null)

      const generation = await resolveChartServedGeneration(fchart,
        ['ga_positions', 'ga_dashas', 'ga_vichara', 'ga_strength', 'ga_structural'], query)

      expect(generation.assets['ga_positions']).toMatchObject({
        state: 'resolved', receipt_build_id: q(2), rows_build_id: q(2), rows_binding: 'receipt_run_wrote_rows',
      })
      // the failed asset never serves: its R attempt may have rewritten the rows of its older receipt
      expect(generation.assets['ga_dashas']).toMatchObject({ state: 'unresolved', reason: 'intervening_attempt_unreceipted' })
      expect(generation.assets['ga_vichara']).toMatchObject({ state: 'unresolved', reason: 'receipt_asset_not_complete' })
      expect(generation.assets['ga_strength']).toMatchObject({ state: 'unresolved', reason: 'receipt_asset_not_complete' })
      expect(generation.assets['ga_structural']).toMatchObject({ state: 'unresolved', reason: 'no_chart_receipt' })
      // single-writer assets: their partial rows live in their own tables, so R is not withheld
      expect(generation.assets['ga_vichara']).toMatchObject({ partitions: [expect.objectContaining({ receipt_run_state: 'failed' })] })
    })

    const unservableStates = ['running', 'planned', 'paused', 'stopped']
    it.each(unservableStates)('never serves a receipt from a %s run, even for a finished asset', async (state) => {
      const index = unservableStates.indexOf(state)
      const chart = `40000000-0000-4000-8000-0000000001${String(index).padStart(2, '0')}`
      await query('INSERT INTO charts(id, name) VALUES ($1, $2)', [chart, `N208-${state}`])
      const run = q(100 + index)
      await buildRun(run, state, '2026-09-06T01:00:00Z', state === 'stopped' ? '2026-09-06T03:00:00Z' : null, chart)
      await runAsset(run, 'ga_positions', 'complete', 'build', '2026-09-06T01:00:00Z', '2026-09-06T02:00:00Z')
      await receipt('ga_positions', run, '2026-09-06T02:00:00Z', { chart })
      await outcome(chart, 'ga_positions', 'lit')
      const generation = await resolveChartServedGeneration(chart, ['ga_positions'], query)
      expect(generation.assets['ga_positions']).toMatchObject({ state: 'unresolved', reason: 'receipt_run_not_completed' })
      expect(generation.served_build_ids).toEqual([])
    })

    it('withholds a failed run from the shared-table fence when a co-writer failed in it, serves it when only a single-writer failed', async () => {
      const shared = '40000000-0000-4000-8000-000000000201'
      const lone = '40000000-0000-4000-8000-000000000202'
      await query(`UPDATE asset_registry SET target_table = 'shared_cowrite_t', has_writer = true, is_active = true
                    WHERE asset_id IN ('ga_structural', 'ga_sensitive')`)
      // the lone writer is itself an active writer of its own table: it must never count as its own co-writer
      await query(`UPDATE asset_registry SET target_table = 'lone_writer_t', has_writer = true, is_active = true
                    WHERE asset_id = 'ga_vichara'`)
      try {
        for (const [chart, label, failing] of [[shared, 'cowriter', 'ga_structural'], [lone, 'single', 'ga_vichara']] as const) {
          await query('INSERT INTO charts(id, name) VALUES ($1, $2)', [chart, label])
          const base = chart === shared ? 200 : 210
          await buildRun(q(base), 'completed', '2026-09-01T01:00:00Z', '2026-09-01T02:00:00Z', chart)
          await runAsset(q(base), failing, 'complete', 'build', '2026-09-01T01:00:00Z', '2026-09-01T02:00:00Z')
          await receipt(failing, q(base), '2026-09-01T02:00:00Z', { chart })
          await outcome(chart, failing, 'error')
          await buildRun(q(base + 1), 'failed', '2026-09-05T01:00:00Z', '2026-09-05T05:00:00Z', chart)
          await runAsset(q(base + 1), 'ga_positions', 'complete', 'build', '2026-09-05T01:00:00Z', '2026-09-05T02:00:00Z')
          await receipt('ga_positions', q(base + 1), '2026-09-05T02:00:00Z', { chart })
          await outcome(chart, 'ga_positions', 'lit')
          await runAsset(q(base + 1), failing, 'error', 'build', '2026-09-05T02:00:00Z', '2026-09-05T03:00:00Z')
        }
        const withCowriter = await resolveChartServedGeneration(shared, null, query)
        expect(withCowriter.assets['ga_positions']).toMatchObject({ state: 'resolved', rows_build_id: q(201) })
        expect(withCowriter.assets['ga_structural']).toMatchObject({ state: 'unresolved' })
        expect(withCowriter.served_build_ids).toEqual([])
        expect(withCowriter.withheld_builds).toEqual([
          { build_id: q(201), unresolved_asset_ids: ['ga_structural'], resolved_asset_ids: ['ga_positions'] },
        ])
        const withSingle = await resolveChartServedGeneration(lone, null, query)
        expect(withSingle.assets['ga_vichara']).toMatchObject({ state: 'unresolved' })
        expect(withSingle.served_build_ids).toEqual([q(211)])
      } finally {
        await query(`UPDATE asset_registry SET target_table = NULL WHERE asset_id IN ('ga_structural', 'ga_sensitive')`)
        await query(`UPDATE asset_registry SET target_table = NULL, has_writer = NULL, is_active = NULL WHERE asset_id = 'ga_vichara'`)
      }
    })

    it('withholds a failed run when a co-writer errored in it with NO chart receipt (first-ever build)', async () => {
      const chart = '40000000-0000-4000-8000-000000000301'
      await query(`UPDATE asset_registry SET target_table = 'shared_cowrite_t2', has_writer = true, is_active = true
                    WHERE asset_id IN ('ga_structural', 'ga_sensitive')`)
      try {
        await query('INSERT INTO charts(id, name) VALUES ($1, $2)', [chart, 'N208-nr'])
        await buildRun(q(301), 'failed', '2026-09-05T01:00:00Z', '2026-09-05T05:00:00Z', chart)
        await runAsset(q(301), 'ga_sensitive', 'complete', 'build', '2026-09-05T01:00:00Z', '2026-09-05T02:00:00Z')
        await receipt('ga_sensitive', q(301), '2026-09-05T02:00:00Z', { chart })
        await outcome(chart, 'ga_sensitive', 'lit')
        // ga_structural: first build on this chart, heavy writer committed some sub-steps, then errored; no receipt exists.
        await runAsset(q(301), 'ga_structural', 'error', 'build', '2026-09-05T02:00:00Z', '2026-09-05T03:00:00Z')
        await outcome(chart, 'ga_structural', 'error')

        const generation = await resolveChartServedGeneration(chart, ['ga_sensitive'], query)
        expect(generation.assets['ga_sensitive']).toMatchObject({ state: 'resolved', rows_build_id: q(301) })
        expect(generation.served_build_ids).toEqual([])
        expect(generation.withheld_builds).toEqual([
          { build_id: q(301), unresolved_asset_ids: ['ga_structural'], resolved_asset_ids: ['ga_sensitive'] },
        ])
        // a later successful attempt at the failed co-writer supersedes its partial rows: the run is served again
        await buildRun(q(302), 'completed', '2026-09-06T01:00:00Z', '2026-09-06T02:00:00Z', chart)
        await runAsset(q(302), 'ga_structural', 'complete', 'build', '2026-09-06T01:00:00Z', '2026-09-06T02:00:00Z')
        await receipt('ga_structural', q(302), '2026-09-06T02:00:00Z', { chart })
        await query(`UPDATE asset_throughput SET state = 'lit' WHERE chart_id = $1 AND asset_id = 'ga_structural'`, [chart])
        const recovered = await resolveChartServedGeneration(chart, ['ga_sensitive', 'ga_structural'], query)
        expect(recovered.served_build_ids).toEqual([q(301), q(302)])
      } finally {
        await query(`UPDATE asset_registry SET target_table = NULL WHERE asset_id IN ('ga_structural', 'ga_sensitive')`)
      }
    })

    it('keeps the failed run withheld while a retry has only STARTED; serves it once a retry FINISHES (D1)', async () => {
      const chart = '40000000-0000-4000-8000-000000000341'
      await query(`UPDATE asset_registry SET target_table = 'shared_cowrite_t3', has_writer = true, is_active = true
                    WHERE asset_id IN ('ga_structural', 'ga_sensitive')`)
      try {
        await query('INSERT INTO charts(id, name) VALUES ($1, $2)', [chart, 'N208-retry'])
        await buildRun(q(341), 'failed', '2026-09-05T01:00:00Z', '2026-09-05T05:00:00Z', chart)
        await runAsset(q(341), 'ga_sensitive', 'complete', 'build', '2026-09-05T01:00:00Z', '2026-09-05T02:00:00Z')
        await receipt('ga_sensitive', q(341), '2026-09-05T02:00:00Z', { chart })
        await outcome(chart, 'ga_sensitive', 'lit')
        await runAsset(q(341), 'ga_structural', 'error', 'build', '2026-09-05T02:00:00Z', '2026-09-05T03:00:00Z')
        await outcome(chart, 'ga_structural', 'error')
        const withheld = { build_id: q(341), unresolved_asset_ids: ['ga_structural'], resolved_asset_ids: ['ga_sensitive'] }

        let generation = await resolveChartServedGeneration(chart, ['ga_sensitive'], query)
        expect(generation.served_build_ids).toEqual([])
        expect(generation.withheld_builds).toEqual([withheld])

        // the retry is dispatched in a RUNNING run and is mid-build: it may not have replaced the partial rows yet
        await buildRun(q(342), 'running', '2026-09-06T01:00:00Z', null, chart)
        await runAsset(q(342), 'ga_structural', 'building', 'build', '2026-09-06T01:00:00Z', null)
        await query(`UPDATE asset_throughput SET state = 'building' WHERE chart_id = $1 AND asset_id = 'ga_structural'`, [chart])
        generation = await resolveChartServedGeneration(chart, ['ga_sensitive'], query)
        expect(generation.served_build_ids).toEqual([])
        expect(generation.withheld_builds).toEqual([withheld])

        // the retry errors out in its own failed run: both runs stay withheld
        await query(`UPDATE build_runs SET state = 'failed', ended_at = '2026-09-06T03:00:00Z' WHERE id = $1`, [q(342)])
        await query(`UPDATE build_run_assets SET state = 'error', ended_at = '2026-09-06T02:00:00Z' WHERE run_id = $1`, [q(342)])
        await query(`UPDATE asset_throughput SET state = 'error' WHERE chart_id = $1 AND asset_id = 'ga_structural'`, [chart])
        generation = await resolveChartServedGeneration(chart, ['ga_sensitive'], query)
        expect(generation.served_build_ids).toEqual([])

        // a retry that FINISHES supersedes the failed attempts: the run is served again
        await buildRun(q(343), 'completed', '2026-09-07T01:00:00Z', '2026-09-07T02:00:00Z', chart)
        await runAsset(q(343), 'ga_structural', 'complete', 'build', '2026-09-07T01:00:00Z', '2026-09-07T02:00:00Z')
        await receipt('ga_structural', q(343), '2026-09-07T02:00:00Z', { chart })
        await query(`UPDATE asset_throughput SET state = 'lit' WHERE chart_id = $1 AND asset_id = 'ga_structural'`, [chart])
        generation = await resolveChartServedGeneration(chart, ['ga_sensitive', 'ga_structural'], query)
        expect(generation.served_build_ids).toEqual([q(341), q(343)])
        expect(generation.withheld_builds).toEqual([])
      } finally {
        await query(`UPDATE asset_registry SET target_table = NULL WHERE asset_id IN ('ga_structural', 'ga_sensitive')`)
      }
    })

    it('reads the throughput outcome of the receipt\'s own chart only (no cross-chart bleed)', async () => {
      const a = '40000000-0000-4000-8000-000000000311'
      const b = '40000000-0000-4000-8000-000000000312'
      await query('INSERT INTO charts(id, name) VALUES ($1, $2), ($3, $4)', [a, 'N208-a', b, 'N208-b'])
      await buildRun(q(311), 'failed', '2026-09-05T01:00:00Z', '2026-09-05T05:00:00Z', a)
      await runAsset(q(311), 'ga_positions', 'complete', 'build', '2026-09-05T01:00:00Z', '2026-09-05T02:00:00Z')
      await receipt('ga_positions', q(311), '2026-09-05T02:00:00Z', { chart: a })
      await outcome(a, 'ga_positions', 'error')
      await outcome(b, 'ga_positions', 'lit')
      const generation = await resolveChartServedGeneration(a, ['ga_positions'], query)
      expect(generation.assets['ga_positions']).toMatchObject({ state: 'unresolved', reason: 'receipt_asset_not_complete' })
    })

    it('refuses a no-delta receipt in a failed run whose writer was held back, serves the same shape without the hold (F3)', async () => {
      const held = '40000000-0000-4000-8000-000000000321'
      const clean = '40000000-0000-4000-8000-000000000322'
      for (const [chart, base, rejected] of [[held, 321, true], [clean, 331, false]] as const) {
        await query('INSERT INTO charts(id, name) VALUES ($1, $2)', [chart, `N208-f3-${base}`])
        // W: a build that completed per build_run_assets (and persisted a receipt) but was held back as incomplete
        await buildRun(q(base), 'completed', '2026-09-01T01:00:00Z', '2026-09-01T02:00:00Z', chart)
        await runAsset(q(base), 'ga_positions', 'complete', 'build', '2026-09-01T01:00:00Z', '2026-09-01T02:00:00Z')
        if (rejected) {
          await query(`INSERT INTO orchestrator_event_register(event_type, chart_id, asset_id, run_id)
                       VALUES ('asset.noop_completion_rejected', $1, 'ga_positions', $2)`, [chart, q(base)])
        }
        // N: the next run re-attributed the receipt by skip_no_delta (restoring throughput to lit) and then failed
        await buildRun(q(base + 1), 'failed', '2026-09-05T01:00:00Z', '2026-09-05T05:00:00Z', chart)
        await runAsset(q(base + 1), 'ga_positions', 'complete', 'skip_no_delta', '2026-09-05T01:00:00Z', '2026-09-05T01:05:00Z')
        await receipt('ga_positions', q(base + 1), '2026-09-05T01:05:00Z', { chart })
        await outcome(chart, 'ga_positions', 'lit')
      }
      const withHold = await resolveChartServedGeneration(held, ['ga_positions'], query)
      expect(withHold.assets['ga_positions']).toMatchObject({ state: 'unresolved', reason: 'receipt_asset_not_complete' })
      const withoutHold = await resolveChartServedGeneration(clean, ['ga_positions'], query)
      expect(withoutHold.assets['ga_positions']).toMatchObject({ state: 'resolved', rows_build_id: q(331), rows_binding: 'skip_no_delta_writer' })
    })
  })

  it('matches the chart id case-insensitively', async () => {
    const generation = await resolveChartServedGeneration(chartId.toUpperCase(), ['ga_dashas'], query)
    expect(generation.assets['ga_dashas']).toMatchObject({ state: 'resolved' })
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

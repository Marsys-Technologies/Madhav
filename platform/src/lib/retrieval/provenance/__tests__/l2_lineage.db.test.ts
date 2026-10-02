/**
 * l2_lineage.db.test.ts — the N-91 lineage detector's REAL SQL against the production DDL
 * (asset_provenance_receipts + asset_output_digest_specs, migrations 171/596/598) on a disposable
 * localhost PostgreSQL. Skipped unless PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL is set (same guard
 * and DB name as generation/served_generation.db.test.ts: localhost + `purna_overlay_test` only;
 * everything runs inside a throw-away schema that is dropped afterwards).
 *
 * Proves what the pure-function tests cannot: the jsonb pin projection (`upstream_receipts` ->
 * `l1_pins`), the active-spec EXISTS join, the chart/chart-less receipt filter, and that a digest
 * flip on the L1 receipt flips the detector end to end (a real UPDATE, not a fixture).
 */
import { randomUUID } from 'node:crypto'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { Pool } from 'pg'
import { resolveL2Lineage } from '../l2_lineage'

const DATABASE_URL = process.env.PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL
const run = DATABASE_URL ? describe : describe.skip
const schema = `n91_l2_lineage_${randomUUID().replaceAll('-', '')}`
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const OTHER = '1c826d5a-0000-4000-8000-000000000000'

const hex = (n: number) => n.toString(16).padStart(64, '0')
const L1 = 'ga_n91_structural'
const L2 = 'bo_n91_laksana'
const L2_RETIRED = 'bo_n91_retired'
const L2_UNKNOWN = 'bo_n91_unknown'
const SPEC: Record<string, string> = { [L1]: hex(1), [L2]: hex(2), [L2_RETIRED]: hex(3), [L2_UNKNOWN]: hex(4) }
const RETIRED_SPEC = hex(33)
const T_L1 = '2026-09-07T08:37:20.895985Z'
const T_L2 = '2026-09-08T18:22:33Z'
const T_NEW = '2026-10-04T10:00:00Z'

function assertDisposableDatabase(url: string): void {
  const parsed = new URL(url)
  if (!['localhost', '127.0.0.1', '::1'].includes(parsed.hostname)) {
    throw new Error('PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL must target localhost')
  }
  if (!parsed.pathname.endsWith('/purna_overlay_test')) {
    throw new Error('PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL must target database purna_overlay_test')
  }
}
const migration = (rel: string) => readFileSync(path.join(process.cwd(), rel), 'utf8')

run('L2 lineage detector SQL against disposable PostgreSQL', () => {
  let admin: Pool
  let scoped: Pool
  const query = async (sql: string, params: unknown[] = []) => scoped.query(sql, params)

  async function receipt(asset: string, chart: string | null, o: {
    digest?: string | null; observedAt?: string; state?: string; spec?: string; pins?: unknown[]; partition?: string
  } = {}) {
    await query(`
      INSERT INTO asset_provenance_receipts
        (asset_id, chart_id, partition_key, receipt_version, receipt_state, output_digest,
         upstream_receipts, output_digest_spec_sha256, unknown_reasons, observed_at)
      VALUES ($1, $2, $3, 'v1', $4, $5, $6::jsonb, $7, '[]', $8)
      ON CONFLICT (asset_id, scope_key, partition_key) DO UPDATE
        SET output_digest = EXCLUDED.output_digest, observed_at = EXCLUDED.observed_at,
            receipt_state = EXCLUDED.receipt_state, upstream_receipts = EXCLUDED.upstream_receipts,
            output_digest_spec_sha256 = EXCLUDED.output_digest_spec_sha256`,
    [asset, chart, o.partition ?? '__whole_asset__', o.state ?? 'proven', o.digest === undefined ? 'D1' : o.digest,
      JSON.stringify(o.pins ?? []), o.spec ?? SPEC[asset] ?? null, o.observedAt ?? T_L1])
  }
  const pin = (digest: string | null, observed = T_L1) => ({ asset_id: L1, output_digest: digest, observed_at: observed, receipt_state: 'proven' })

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
    const seeded = [...migration('supabase/migrations/598_nirmana_output_digest_specs.sql')
      .matchAll(/'([a-z0-9_]+)'\s*,\s*'[a-f0-9]{64}'/g)].map((m) => m[1]!)
    await query('INSERT INTO asset_registry(asset_id) SELECT unnest($1::text[]) ON CONFLICT DO NOTHING',
      [[...new Set([...seeded, ...Object.keys(SPEC)])]])
    await query(migration('supabase/migrations/171_build_runs.sql'))
    await query(migration('supabase/migrations/596_nirmana_provenance_receipts.sql'))
    await query(migration('supabase/migrations/598_nirmana_output_digest_specs.sql'))
    await query('INSERT INTO charts(id, name) VALUES ($1, $2), ($3, $4)', [CHART, 'Disposable', OTHER, 'Other'])
    await query(`INSERT INTO asset_output_digest_specs(asset_id, spec_sha256, spec, reviewed_at, retired_at)
                 VALUES ($1, $2, '{}'::jsonb, '2026-09-01T00:00:00Z', '2026-09-19T00:00:00Z')`, [L2_RETIRED, RETIRED_SPEC])
    for (const [asset, sha] of Object.entries(SPEC)) {
      if (asset === L2_RETIRED) continue // its only ACTIVE spec is added below under a different sha
      await query(`INSERT INTO asset_output_digest_specs(asset_id, spec_sha256, spec, reviewed_at)
                   VALUES ($1, $2, '{}'::jsonb, '2026-09-19T00:00:00Z')`, [asset, sha])
    }
  }, 30_000)

  afterAll(async () => {
    await scoped?.end()
    if (admin) {
      await admin.query(`DROP SCHEMA IF EXISTS ${schema} CASCADE`)
      await admin.end()
    }
  })

  it('no L2 receipts -> not_applicable', async () => {
    await receipt(L1, CHART, { digest: 'D1' })
    const r = await resolveL2Lineage(CHART, query)
    expect(r.state).toBe('not_applicable')
  })

  it('L2 pin equals the current L1 digest -> current', async () => {
    await receipt(L2, CHART, { digest: 'L2OUT', observedAt: T_L2, pins: [pin('D1')] })
    const r = await resolveL2Lineage(CHART, query)
    expect(r).toMatchObject({ state: 'current', l2_receipts_in_scope: 1, l1_pins_checked: 1 })
  })

  it('a no-op L1 re-receipt (same digest, newer observed_at) stays current', async () => {
    await receipt(L1, CHART, { digest: 'D1', observedAt: T_NEW })
    expect((await resolveL2Lineage(CHART, query)).state).toBe('current')
  })

  it('a REAL L1 digest change flips the detector to stale, naming the L2 and L1 assets', async () => {
    await receipt(L1, CHART, { digest: 'D2', observedAt: T_NEW })
    const r = await resolveL2Lineage(CHART, query)
    expect(r.state).toBe('stale')
    expect(r.stale).toHaveLength(1)
    expect(r.stale[0]).toMatchObject({ l2_asset_id: L2, l1_asset_id: L1, pinned_output_digest: 'D1', current_output_digest: 'D2' })
    expect(r.stale[0]!.current_observed_at).toContain('2026-10-04')
  })

  it('legacy `unknown` and retired-spec L2 receipts are ignored (their stale pins do not count)', async () => {
    // fresh baseline: L2 is current again (re-pinned to D2), then add ignorable receipts pinning the OLD digest
    await receipt(L2, CHART, { digest: 'L2OUT', observedAt: T_NEW, pins: [pin('D2', T_NEW)] })
    await receipt(L2_UNKNOWN, CHART, { state: 'unknown', digest: null, pins: [pin('D1')] })
    await receipt(L2_RETIRED, CHART, { digest: 'X', spec: RETIRED_SPEC, pins: [pin('D1')] })
    const r = await resolveL2Lineage(CHART, query)
    expect(r.state).toBe('current')
    expect(r.l2_receipts_in_scope).toBe(1)
  })

  it('another chart\'s receipts never leak in', async () => {
    await receipt(L1, OTHER, { digest: 'ZZ' })
    await receipt(L2, OTHER, { digest: 'L2OUT', pins: [pin('OLD')] })
    expect((await resolveL2Lineage(CHART, query)).state).toBe('current')
    expect((await resolveL2Lineage(OTHER, query)).state).toBe('stale')
  })

  it('registry-current filter: a superseded partition (registry now declares another) and a deactivated asset cannot hold the flag TRUE', async () => {
    // The live L2 receipt (whole-asset partition) now carries a STALE pin (D1) ...
    await receipt(L2, CHART, { digest: 'L2OUT', observedAt: T_NEW, pins: [pin('D1')] })
    expect((await resolveL2Lineage(CHART, query)).state).toBe('stale')
    // ... the registry then re-declares the asset's partition and S-L2 writes the new partition (pins current).
    await query('UPDATE asset_registry SET natural_key_partition = $2 WHERE asset_id = $1', [L2, 'NEW PARTITION DECLARATION'])
    await receipt(L2, CHART, { digest: 'L2OUT', observedAt: T_NEW, pins: [pin('D2', T_NEW)], partition: 'NEW PARTITION DECLARATION' })
    const afterRename = await resolveL2Lineage(CHART, query)
    expect(afterRename.state).toBe('current') // the superseded whole-asset row (stale pin, never rewritten) is ignored
    expect(afterRename.l2_receipts_in_scope).toBe(1)
    // a retired asset (is_active false) with a stale pin is ignored too
    await receipt(L2, CHART, { digest: 'L2OUT', observedAt: T_NEW, pins: [pin('D1')], partition: 'NEW PARTITION DECLARATION' })
    expect((await resolveL2Lineage(CHART, query)).state).toBe('stale')
    await query('UPDATE asset_registry SET is_active = false WHERE asset_id = $1', [L2])
    expect((await resolveL2Lineage(CHART, query)).state).toBe('not_applicable')
    // restore for the following tests
    await query('UPDATE asset_registry SET is_active = true, natural_key_partition = NULL WHERE asset_id = $1', [L2])
    await query('DELETE FROM asset_provenance_receipts WHERE asset_id = $1 AND partition_key = $2', [L2, 'NEW PARTITION DECLARATION'])
    await receipt(L2, CHART, { digest: 'L2OUT', observedAt: T_NEW, pins: [pin('D2', T_NEW)] })
    expect((await resolveL2Lineage(CHART, query)).state).toBe('current')
  })

  it('a pinned L1 asset with no current receipt for the chart -> stale', async () => {
    await query('DELETE FROM asset_provenance_receipts WHERE asset_id = $1 AND chart_id = $2', [L1, CHART])
    const r = await resolveL2Lineage(CHART, query)
    expect(r.state).toBe('stale')
    expect(r.stale[0]).toMatchObject({ current_output_digest: null, current_observed_at: null })
  })

  it('an erroring query (unknown relation) fails closed -> unknown, never current', async () => {
    const r = await resolveL2Lineage(CHART, async () => { throw new Error('relation "asset_provenance_receipts" does not exist') })
    expect(r.state).toBe('unknown')
  })
})

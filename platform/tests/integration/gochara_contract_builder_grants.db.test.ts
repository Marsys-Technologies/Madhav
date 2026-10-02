// @vitest-environment node
/**
 * Pravāha A2.5/A5.3 (steward M20261001T180830-5166, 2026-10-01) — migration 1216
 * grants data_plane_builder the exact privileges the governed gochara writers
 * need on the 1153–1157 contract tables and the 1081 kala_gochara ledger
 * tables. Production state verified read-only before authoring: the builder
 * held NOTHING on any of the 18 tables, so every governed gochara write fails
 * with 'permission denied for table …' at the first DML.
 *
 * Proof shape (same as the 1211 audit-grant suite): a role literally named
 * `data_plane_builder` with only USAGE on schema public — representative writes
 * must FAIL before migration 1216 and SUCCEED after; the forbidden mutations
 * (DELETE on the insert-only global families, UPDATE on insert-if-absent
 * candidate rows, CREATE on schema public, any privilege on the DEFERRED
 * tables) must stay refused. The table DDL is executed from the REAL on-disk
 * migration files (1081, 1153–1157) and the grant migration from the REAL 1216
 * file (§N.8 — the detector measures the claim it asserts, not a hand-copied
 * proxy). The only stub is `charts(id)` — the FK parent the contract tables
 * reference, mirroring how the 1211 suite stubs asset_throughput.
 *
 * Requires a THROWAWAY database. Skipped unless
 * M1216_GOCHARA_GRANT_TEST_DATABASE_URL is set, and refuses anything not named
 * `m1216_gochara_grant_test` — this suite drops and recreates schema public and
 * must never touch production.
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres m1216_gochara_grant_test
 *   M1216_GOCHARA_GRANT_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/m1216_gochara_grant_test \
 *     npx vitest run tests/integration/gochara_contract_builder_grants.db.test.ts
 *
 * Wired into CI alongside the 1211 step (db-integration-tests,
 * .github/workflows/ci.yml) so the fails-before/succeeds-after proof re-verifies
 * on every PR.
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.M1216_GOCHARA_GRANT_TEST_DATABASE_URL

const MIG = (name: string) =>
  path.resolve(__dirname, '../../migrations', name)
const DDL_FILES = [
  '1081_nirmana_l3_gochara_ledger_coverage_publication.sql',
  '1153_gochara_sky_event_substrate.sql',
  '1154_gochara_rule_path_registry.sql',
  '1155_gochara_relationship_record.sql',
  '1156_gochara_eval_window.sql',
  '1157_gochara_av_polarity_declaration.sql',
]
const GRANT_MIGRATION_PATH = MIG('1216_gochara_contract_builder_grants.sql')

// The one chart the Gochara-5 contract governs (D-SCOPE, enforced inside
// ka_gochara_lock_chart) — the stub charts row must carry exactly this id.
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
// The mirror role carries the production role's real name so the REAL migration
// file (which GRANTs to `data_plane_builder` literally) applies against it —
// safe because this suite only ever runs on the disposable m1216 database.
const BUILDER_ROLE = 'data_plane_builder'

let pool: Pool

function read(file: string) {
  return fs.readFileSync(MIG(file), 'utf8')
}

async function asBuilder(sql: string, { withChartLock = false } = {}) {
  // A transaction AS the builder-mirror role. withChartLock takes the
  // Gochara-5 chart family key first — the lock order the contract triggers
  // require before any substrate write (steward ruling B / N13).
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(`SET LOCAL ROLE ${BUILDER_ROLE}`)
    if (withChartLock) {
      await client.query(`SELECT public.ka_gochara_lock_chart($1::uuid)`, [CHART])
    }
    const result = await client.query(sql)
    await client.query('COMMIT')
    return result
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}

const KALA_CONVENTION_INSERT = `
  INSERT INTO public.kala_gochara_convention
    (convention_id, zodiac, ayanamsha, sidereal_method, node_model, node_source,
     epoch_convention, time_scale, house_system, ephemeris_mode,
     ephemeris_backend, probe_retflag, method_version)
  VALUES
    ('sha256:m1216-test-convention', 'sidereal', 'lahiri', 'swiss_ephemeris',
     'mean', 'swiss_ephemeris', 'j2000', 'utc', 'whole_sign', 'swieph',
     'swieph', 258, '0.0.0-m1216-test')
`

const SKY_CONVENTION_INSERT = `
  INSERT INTO public.ka_gochara_sky_convention
    (convention_id, ephemeris_generation, ayanamsha, node_convention, grid,
     method_version, domain_start, domain_end)
  VALUES
    ('m1216-test-sky-convention', 'se1-2026-09', 'lahiri', 'mean_node',
     'noon_ut_daily', '0.0.0-m1216-test',
     '1900-01-01T00:00:00Z', '2100-01-01T00:00:00Z')
`

describe.skipIf(!TEST_DB_URL)('migration 1216 — gochara contract builder grants (A2.5/A5.3) — live DB', () => {
  beforeAll(async () => {
    if (!/m1216_gochara_grant_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'M1216_GOCHARA_GRANT_TEST_DATABASE_URL must point at a disposable database named ' +
          '`m1216_gochara_grant_test`. This suite drops and recreates schema public and ' +
          'must never run against production.'
      )
    }

    pool = new Pool({ connectionString: TEST_DB_URL })

    await pool.query(`DROP SCHEMA public CASCADE; CREATE SCHEMA public;`)

    // FK parent stub (the contract tables reference public.charts(id)) — the
    // same stub pattern the 1211 suite uses for asset_throughput. The runner's
    // tracker table is stubbed too: the 1153–1157 preflight blocks reference
    // _migrations_applied.filename, which PostgreSQL resolves at parse time
    // even under a to_regclass guard.
    await pool.query(`CREATE TABLE public.charts (id UUID PRIMARY KEY)`)
    await pool.query(`INSERT INTO public.charts (id) VALUES ($1)`, [CHART])
    await pool.query(`CREATE TABLE public._migrations_applied (filename TEXT PRIMARY KEY)`)

    // The REAL contract-table migrations, in runner order, each recorded in
    // the tracker stub exactly as the runner would (1154+ preflights require
    // their predecessors' tracker rows).
    for (const file of DDL_FILES) {
      await pool.query(read(file))
      await pool.query(`INSERT INTO public._migrations_applied (filename) VALUES ($1)`, [file])
    }

    // A role mirroring data_plane_builder's relevant production grants before
    // 1216: USAGE on schema public, NOTHING on any gochara contract table.
    await pool.query(`
      CREATE ROLE ${BUILDER_ROLE} NOLOGIN;
      GRANT USAGE ON SCHEMA public TO ${BUILDER_ROLE};
    `)
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`
      DROP SCHEMA public CASCADE;
      CREATE SCHEMA public;
      DROP ROLE IF EXISTS ${BUILDER_ROLE};
    `)
    await pool.end()
  })

  it('FAILS BEFORE: the builder cannot insert a kala convention row', async () => {
    await expect(asBuilder(KALA_CONVENTION_INSERT)).rejects.toThrow(
      /permission denied for table kala_gochara_convention/
    )
  })

  it('FAILS BEFORE: the builder cannot insert a sky convention row even holding the chart family key', async () => {
    await expect(asBuilder(SKY_CONVENTION_INSERT, { withChartLock: true })).rejects.toThrow(
      /permission denied for table ka_gochara_sky_convention/
    )
  })

  it('SUCCEEDS AFTER: the REAL 1216 file admits the governed write shapes', async () => {
    await pool.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))

    // Global insert-only family: insert-if-absent read + insert.
    await asBuilder(SKY_CONVENTION_INSERT, { withChartLock: true })
    // kala convention registration.
    await asBuilder(KALA_CONVENTION_INSERT)
    // v4_41 body-scoped delete-then-insert: the DELETE half must be permitted
    // (0 rows here — ACL is checked regardless of row count).
    await asBuilder(`DELETE FROM public.kala_gochara_contacts WHERE chart_id = '${CHART}' AND generation = '4.1'`)
    await asBuilder(`DELETE FROM public.kala_gochara_coverage WHERE chart_id = '${CHART}' AND generation = '4.1'`)
    // publish_candidate replaces the CANDIDATE row in place: UPDATE permitted.
    await asBuilder(`UPDATE public.kala_gochara_publication SET row_counts = row_counts WHERE false`)

    const sky = await pool.query<{ convention_id: string }>(`SELECT convention_id FROM public.ka_gochara_sky_convention`)
    expect(sky.rows.map((r) => r.convention_id)).toContain('m1216-test-sky-convention')
    const kala = await pool.query<{ convention_id: string }>(`SELECT convention_id FROM public.kala_gochara_convention`)
    expect(kala.rows.map((r) => r.convention_id)).toContain('sha256:m1216-test-convention')
  })

  it('idempotent: applying migration 1216 a second time is a no-op and writes still land', async () => {
    await pool.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))
    await asBuilder(
      `INSERT INTO public.kala_gochara_convention
         (convention_id, zodiac, ayanamsha, sidereal_method, node_model, node_source,
          epoch_convention, time_scale, house_system, ephemeris_mode, method_version)
       VALUES
         ('sha256:m1216-test-convention-2', 'sidereal', 'lahiri', 'swiss_ephemeris',
          'mean', 'swiss_ephemeris', 'j2000', 'utc', 'whole_sign', 'swieph',
          '0.0.0-m1216-test')`
    )
  })

  it('scope: the insert-only global families refuse DELETE and the candidate rows refuse UPDATE', async () => {
    await expect(asBuilder(`DELETE FROM public.ka_gochara_sky_event`)).rejects.toThrow(
      /permission denied for table ka_gochara_sky_event/
    )
    await expect(asBuilder(`UPDATE public.ka_gochara_contact SET coverage = coverage WHERE false`)).rejects.toThrow(
      /permission denied for table ka_gochara_contact/
    )
  })

  it('scope: the DEFERRED tables (no write path yet) stay ungranted, and no CREATE on schema public', async () => {
    const check = await pool.query<{
      eval_window_insert: boolean
      eval_window_record_insert: boolean
      av_decl_insert: boolean
      generation_seal_insert: boolean
      schema_create: boolean
    }>(
      `SELECT has_table_privilege($1, 'public.ka_gochara_eval_window', 'INSERT') AS eval_window_insert,
              has_table_privilege($1, 'public.ka_gochara_eval_window_record', 'INSERT') AS eval_window_record_insert,
              has_table_privilege($1, 'public.ka_gochara_av_polarity_declaration', 'INSERT') AS av_decl_insert,
              has_table_privilege($1, 'public.ka_gochara_generation_seal', 'INSERT') AS generation_seal_insert,
              has_schema_privilege($1, 'public', 'CREATE') AS schema_create`,
      [BUILDER_ROLE]
    )
    expect(check.rows[0]).toEqual({
      eval_window_insert: false,
      eval_window_record_insert: false,
      av_decl_insert: false,
      generation_seal_insert: false,
      schema_create: false,
    })
  })
})

// @vitest-environment node
/**
 * Pravāha C19 (steward M20261002T062943-356e, 2026-10-02) — migration 1239
 * RECORDS the existing production ACL: data_plane_builder holds
 * SELECT/INSERT/UPDATE/DELETE on public.kala_gochara_v2_build_state,
 * public.kala_moorti_nirnaya and public.kala_vedha_gochara (+ USAGE/SELECT
 * on the two BIGSERIAL identity sequences) in production (C18's report-only
 * gap list, verified read-only 2026-10-02), but no migration granted it, so
 * a fresh environment could never run the ka_gochara writer's build-state
 * upsert or the ka_moorti_nirnaya / ka_vedha_gochara overlay writers.
 *
 * Proof shape, mirroring the 1238 suite: a role created with EXACTLY
 * data_plane_builder's relevant grants (USAGE on schema public, NOTHING on
 * the three tables) — SELECT/INSERT must FAIL before migration 1239 and
 * SUCCEED after. The table DDL (migrations 525, 526 and 541, all under
 * supabase/migrations) and the grant migration (1239) are executed from
 * their REAL on-disk files (§N.8 — the detector measures the claim it
 * asserts, not a hand-copied proxy).
 *
 * Requires a THROWAWAY database. Skipped unless
 * M1239_OVERLAY_GRANT_TEST_DATABASE_URL is set, and refuses anything not
 * named `m1239_overlay_grant_test` — this suite creates and drops schema
 * objects and roles and must never touch production.
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres m1239_overlay_grant_test
 *   M1239_OVERLAY_GRANT_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/m1239_overlay_grant_test \
 *     npx vitest run tests/integration/gochara_overlay_builder_grant_record.db.test.ts
 *
 * Wired into CI alongside the C18/1238 step (db-integration-tests,
 * .github/workflows/ci.yml).
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.M1239_OVERLAY_GRANT_TEST_DATABASE_URL

const DDL_MIGRATION_PATHS = [
  path.resolve(__dirname, '../../supabase/migrations/525_kala_moorti_nirnaya.sql'),
  path.resolve(__dirname, '../../supabase/migrations/526_kala_vedha_gochara.sql'),
  path.resolve(__dirname, '../../supabase/migrations/541_kala_gochara_v2_build_state.sql'),
]
const GRANT_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../migrations/1239_overlay_builder_grant_record.sql'
)

// The mirror role carries the production role's real name so the REAL migration
// file (which GRANTs to `data_plane_builder` literally) applies against it —
// safe because this suite only ever runs on the disposable
// `m1239_overlay_grant_test`.
const BUILDER_ROLE = 'data_plane_builder'

const TABLES = ['kala_gochara_v2_build_state', 'kala_moorti_nirnaya', 'kala_vedha_gochara'] as const

// One minimal literal row per table (inserted and rolled back — the probe
// proves the privilege, it keeps no row).
const INSERTS: Record<(typeof TABLES)[number], string> = {
  kala_gochara_v2_build_state: `INSERT INTO public.kala_gochara_v2_build_state
      (chart_id, event_class, generation, class_fingerprint, grammar_version,
       arc_engine_version, horizon_start_date, horizon_end_date, horizon_status)
    VALUES ('00000000-0000-0000-0000-000000000c19', 'career_entry', '2.0',
            'fp', 'grammar_v1', 'arc_v1', '2026-01-01', '2029-01-01',
            'progressive_partial')`,
  kala_moorti_nirnaya: `INSERT INTO public.kala_moorti_nirnaya
      (chart_id, graha, target_sign_idx, target_sign_name, window_start, window_end,
       start_truncated, end_truncated, moorti_computed,
       janma_nakshatra_idx, janma_nakshatra_fact_id, formula_version)
    VALUES ('00000000-0000-0000-0000-000000000c19', 'Saturn', 0, 'Mesha',
            '2030-01-01', '2030-01-02', false, false, false, 0, 'fact-1', 'v1')`,
  kala_vedha_gochara: `INSERT INTO public.kala_vedha_gochara
      (chart_id, vedha_kind, graha, window_start, window_end,
       start_truncated, end_truncated, janma_reference_fact_id,
       classical_citation, uncited_extension, formula_version)
    VALUES ('00000000-0000-0000-0000-000000000c19', 'house_vedha', 'Saturn',
            '2030-01-01', '2030-01-02', false, false, 'fact-1', 'citation-1',
            false, 'v1')`,
}

let pool: Pool

async function builderRun(sql: string) {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(`SET LOCAL ROLE ${BUILDER_ROLE}`)
    await client.query(sql)
    await client.query('ROLLBACK')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}

// True when this suite created the mirror role itself (fresh CI cluster); when
// the role pre-exists in the local cluster (other disposable suites create it
// too), it is reused — scrubbed of privileges in THIS database only — and left
// in place at teardown, never dropped.
let roleCreatedBySuite = false

describe.skipIf(!TEST_DB_URL)('migration 1239 — overlay builder grant record (C19) — live DB', () => {
  beforeAll(async () => {
    if (!/m1239_overlay_grant_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'M1239_OVERLAY_GRANT_TEST_DATABASE_URL must point at a disposable database named ' +
          '`m1239_overlay_grant_test`. This suite creates and drops schema objects and roles ' +
          'and must never run against production.'
      )
    }

    pool = new Pool({ connectionString: TEST_DB_URL })

    await pool.query(`
      DROP TABLE IF EXISTS kala_gochara_v2_build_state CASCADE;
      DROP TABLE IF EXISTS kala_moorti_nirnaya CASCADE;
      DROP TABLE IF EXISTS kala_vedha_gochara CASCADE;
      DROP TABLE IF EXISTS asset_registry CASCADE;
    `)
    const roleCheck = await pool.query<{ exists: boolean }>(
      `SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${BUILDER_ROLE}') AS exists`
    )
    roleCreatedBySuite = !roleCheck.rows[0]!.exists
    if (roleCreatedBySuite) {
      await pool.query(`CREATE ROLE ${BUILDER_ROLE} NOLOGIN`)
    } else {
      // Scrub privileges held in THIS database so the before-state is exactly
      // "USAGE on schema public, nothing on the three tables".
      await pool.query(`
        REVOKE ALL ON ALL TABLES IN SCHEMA public FROM ${BUILDER_ROLE};
        REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM ${BUILDER_ROLE};
        REVOKE ALL ON SCHEMA public FROM ${BUILDER_ROLE};
      `)
    }

    // Minimal stub for the one relation the REAL 525/526/541 files touch
    // besides the audited tables (same convention as the 1237/1238 suites'
    // stubs); the three tables themselves are created by the REAL files.
    // asset_registry needs has_substeps/writer_timeout_seconds/asset_kind/
    // depends_on: the seed INSERTs/UPDATEs reference them.
    await pool.query(`
      CREATE TABLE IF NOT EXISTS asset_registry (
        asset_id TEXT PRIMARY KEY, layer TEXT, sort_order INTEGER,
        sanskrit_name TEXT, english_name TEXT, english_description TEXT,
        storage_type TEXT, target_table TEXT, count_sql TEXT, size_sql TEXT,
        target_floor INTEGER, scope TEXT, is_active BOOLEAN, has_writer BOOLEAN,
        has_substeps BOOLEAN, writer_timeout_seconds INTEGER,
        layer_name TEXT, layer_index TEXT, catalog_status TEXT, asset_kind TEXT,
        depends_on TEXT[]
      );
    `)
    for (const ddlPath of DDL_MIGRATION_PATHS) {
      await pool.query(fs.readFileSync(ddlPath, 'utf8'))
    }

    // A role with EXACTLY data_plane_builder's relevant grants for this path
    // before 1239: USAGE on schema public, NOTHING on the three tables.
    await pool.query(`GRANT USAGE ON SCHEMA public TO ${BUILDER_ROLE}`)
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`
      DROP TABLE IF EXISTS kala_gochara_v2_build_state CASCADE;
      DROP TABLE IF EXISTS kala_moorti_nirnaya CASCADE;
      DROP TABLE IF EXISTS kala_vedha_gochara CASCADE;
      DROP TABLE IF EXISTS asset_registry CASCADE;
      REVOKE ALL ON ALL TABLES IN SCHEMA public FROM ${BUILDER_ROLE};
      REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM ${BUILDER_ROLE};
      REVOKE ALL ON SCHEMA public FROM ${BUILDER_ROLE};
    `)
    if (roleCreatedBySuite) {
      await pool.query(`DROP ROLE ${BUILDER_ROLE}`)
    }
    await pool.end()
  })

  for (const table of TABLES) {
    it(`FAILS BEFORE: SELECT under the builder-mirror role is denied on ${table}`, async () => {
      await expect(builderRun(`SELECT count(*) FROM public.${table}`)).rejects.toThrow(
        new RegExp(`permission denied for table ${table}`)
      )
    })

    it(`FAILS BEFORE: INSERT under the builder-mirror role is denied on ${table}`, async () => {
      await expect(builderRun(INSERTS[table])).rejects.toThrow(
        new RegExp(`permission denied for table ${table}`)
      )
    })
  }

  it('SUCCEEDS AFTER: applying the REAL migration 1239 file lets SELECT, INSERT and DELETE land on all three tables', async () => {
    await pool.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))
    for (const table of TABLES) {
      await builderRun(`SELECT count(*) FROM public.${table}`)
      // INSERT also exercises the identity sequences (nextval needs USAGE).
      await builderRun(INSERTS[table])
      await builderRun(
        `DELETE FROM public.${table} WHERE chart_id = '00000000-0000-0000-0000-000000000c19'`
      )
    }
  })

  it('idempotent: applying migration 1239 a second time is a no-op and the ACLs still hold', async () => {
    await pool.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))
    for (const table of TABLES) {
      await builderRun(`SELECT count(*) FROM public.${table}`)
      await builderRun(INSERTS[table])
    }
  })

  it('scope: the grants match the recorded production ACLs exactly — arwd + sequence USAGE/SELECT, no CREATE, nothing wider', async () => {
    for (const table of TABLES) {
      const check = await pool.query<{
        sel: boolean; ins: boolean; upd: boolean; del: boolean
        trunc: boolean; ref: boolean; trig: boolean
      }>(
        `SELECT has_table_privilege($1, $2, 'SELECT') AS sel,
                has_table_privilege($1, $2, 'INSERT') AS ins,
                has_table_privilege($1, $2, 'UPDATE') AS upd,
                has_table_privilege($1, $2, 'DELETE') AS del,
                has_table_privilege($1, $2, 'TRUNCATE') AS trunc,
                has_table_privilege($1, $2, 'REFERENCES') AS ref,
                has_table_privilege($1, $2, 'TRIGGER') AS trig`,
        [BUILDER_ROLE, `public.${table}`]
      )
      expect(check.rows[0]).toEqual({
        sel: true, ins: true, upd: true, del: true,
        trunc: false, ref: false, trig: false,
      })
    }
    const seqCheck = await pool.query<{
      seq: string; usage: boolean; select: boolean; update: boolean
    }>(
      `SELECT s AS seq,
              has_sequence_privilege($1, s, 'USAGE') AS usage,
              has_sequence_privilege($1, s, 'SELECT') AS select,
              has_sequence_privilege($1, s, 'UPDATE') AS update
         FROM (VALUES ('public.kala_moorti_nirnaya_id_seq'),
                      ('public.kala_vedha_gochara_id_seq')) v(s)`,
      [BUILDER_ROLE]
    )
    for (const row of seqCheck.rows) {
      expect([row.usage, row.select, row.update]).toEqual([true, true, false])
    }
    const schemaCreate = await pool.query<{ c: boolean }>(
      `SELECT has_schema_privilege($1, 'public', 'CREATE') AS c`, [BUILDER_ROLE]
    )
    expect(schemaCreate.rows[0]!.c).toBe(false)
  })

  it('guarded: skips cleanly when the builder role does not exist', async () => {
    if (!roleCreatedBySuite) {
      // Shared local cluster: a pre-existing data_plane_builder may hold
      // privileges in other disposable databases and cannot be dropped here.
      // The role-absent guard is exercised in CI, where this suite owns the
      // role (fresh cluster).
      return
    }
    // On a role-less database the DO block must NOTICE and no-op, not error.
    await pool.query(`DROP OWNED BY ${BUILDER_ROLE} CASCADE`).catch(() => {})
    await pool.query(`
      REVOKE ALL ON ALL TABLES IN SCHEMA public FROM ${BUILDER_ROLE};
      REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM ${BUILDER_ROLE};
      REVOKE ALL ON SCHEMA public FROM ${BUILDER_ROLE};
      DROP ROLE ${BUILDER_ROLE};
    `)
    await expect(
      pool.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))
    ).resolves.toBeDefined()
    // restore the role for teardown symmetry (teardown drops what it created)
    await pool.query(`CREATE ROLE ${BUILDER_ROLE} NOLOGIN`)
  })
})

// @vitest-environment node
/**
 * Pravāha C18 (steward M20261002T052941-db54, 2026-10-02) — migration 1238
 * RECORDS the existing production ACL: data_plane_builder holds
 * SELECT/INSERT/UPDATE/DELETE on public.kala_gochara_windows_v2 (+ USAGE/SELECT
 * on its identity sequence) in production (C16 flag, verified read-only
 * 2026-10-02), but no migration granted it, so a fresh environment could
 * never run the registered ka_gochara writer (ka_gochara_v2_materialize,
 * generation '2.0') whose write target this table is.
 *
 * Proof shape, mirroring the 1237 suite: a role created with EXACTLY
 * data_plane_builder's relevant grants (USAGE on schema public, NOTHING on
 * kala_gochara_windows_v2) — SELECT/INSERT must FAIL before migration 1238
 * and SUCCEED after. Both the table DDL (migration 542, under
 * supabase/migrations) and the grant migration (1238) are executed from
 * their REAL on-disk files (§N.8 — the detector measures the claim it
 * asserts, not a hand-copied proxy).
 *
 * Requires a THROWAWAY database. Skipped unless
 * M1238_WINDOWS_V2_GRANT_TEST_DATABASE_URL is set, and refuses anything not
 * named `m1238_windows_v2_grant_test` — this suite creates and drops schema
 * objects and roles and must never touch production.
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres m1238_windows_v2_grant_test
 *   M1238_WINDOWS_V2_GRANT_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/m1238_windows_v2_grant_test \
 *     npx vitest run tests/integration/gochara_windows_v2_builder_grant_record.db.test.ts
 *
 * Wired into CI alongside the C16/1237 step (db-integration-tests,
 * .github/workflows/ci.yml).
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.M1238_WINDOWS_V2_GRANT_TEST_DATABASE_URL

const DDL_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../supabase/migrations/542_kala_gochara_windows_v2.sql'
)
const GRANT_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../migrations/1238_kala_gochara_windows_v2_builder_grant_record.sql'
)

// The mirror role carries the production role's real name so the REAL migration
// file (which GRANTs to `data_plane_builder` literally) applies against it —
// safe because this suite only ever runs on the disposable
// `m1238_windows_v2_grant_test`.
const BUILDER_ROLE = 'data_plane_builder'

let pool: Pool

async function builderSelect() {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(`SET LOCAL ROLE ${BUILDER_ROLE}`)
    await client.query(`SELECT count(*) FROM public.kala_gochara_windows_v2`)
    await client.query('COMMIT')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}

async function builderInsert() {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(`SET LOCAL ROLE ${BUILDER_ROLE}`)
    await client.query(
      `INSERT INTO public.kala_gochara_windows_v2
         (chart_id, event_class, temporal_shape, window_start, window_end, peak_date,
          signed_intensity, raw_intensity, valence, is_adverse)
       VALUES ('00000000-0000-0000-0000-000000000c18', 'career_entry', 'point',
               '2030-01-01', '2030-01-01', '2030-01-01', 0.5, 0.5, 'gain', false)`
    )
    // rolled back — the probe proves the privilege, it keeps no row
    await client.query('ROLLBACK')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}

async function builderDelete() {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(`SET LOCAL ROLE ${BUILDER_ROLE}`)
    await client.query(
      `DELETE FROM public.kala_gochara_windows_v2 WHERE chart_id = '00000000-0000-0000-0000-000000000c18'`
    )
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

describe.skipIf(!TEST_DB_URL)('migration 1238 — kala_gochara_windows_v2 builder grant record (C18) — live DB', () => {
  beforeAll(async () => {
    if (!/m1238_windows_v2_grant_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'M1238_WINDOWS_V2_GRANT_TEST_DATABASE_URL must point at a disposable database named ' +
          '`m1238_windows_v2_grant_test`. This suite creates and drops schema objects and roles ' +
          'and must never run against production.'
      )
    }

    pool = new Pool({ connectionString: TEST_DB_URL })

    await pool.query(`
      DROP TABLE IF EXISTS kala_gochara_windows_v2 CASCADE;
      DROP TABLE IF EXISTS kala_gochara_v2_build_state CASCADE;
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
      // "USAGE on schema public, nothing on kala_gochara_windows_v2".
      await pool.query(`
        REVOKE ALL ON ALL TABLES IN SCHEMA public FROM ${BUILDER_ROLE};
        REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM ${BUILDER_ROLE};
        REVOKE ALL ON SCHEMA public FROM ${BUILDER_ROLE};
      `)
    }

    // Minimal stubs for the two relations the REAL 542 file touches besides
    // the audited table (same convention as the 1225/1216/1231/1237 suites'
    // stubs); kala_gochara_windows_v2 itself is created by the REAL file.
    // asset_registry needs has_substeps/writer_timeout_seconds/depends_on:
    // 542's trailing INSERT/UPDATE references them; kala_gochara_v2_build_state
    // needs (chart_id, generation): 542's stale-bookkeeping DELETE scopes on
    // them.
    await pool.query(`
      CREATE TABLE IF NOT EXISTS asset_registry (
        asset_id TEXT PRIMARY KEY, layer TEXT, sort_order INTEGER,
        sanskrit_name TEXT, english_name TEXT, english_description TEXT,
        storage_type TEXT, target_table TEXT, count_sql TEXT, size_sql TEXT,
        target_floor INTEGER, scope TEXT, is_active BOOLEAN, has_writer BOOLEAN,
        has_substeps BOOLEAN, writer_timeout_seconds INTEGER,
        layer_name TEXT, layer_index TEXT, catalog_status TEXT,
        depends_on TEXT[]
      );
      CREATE TABLE IF NOT EXISTS kala_gochara_v2_build_state (
        chart_id UUID, generation TEXT
      );
    `)
    await pool.query(fs.readFileSync(DDL_MIGRATION_PATH, 'utf8'))

    // A role with EXACTLY data_plane_builder's relevant grants for this path
    // before 1238: USAGE on schema public, NOTHING on kala_gochara_windows_v2.
    await pool.query(`GRANT USAGE ON SCHEMA public TO ${BUILDER_ROLE}`)
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`
      DROP TABLE IF EXISTS kala_gochara_windows_v2 CASCADE;
      DROP TABLE IF EXISTS kala_gochara_v2_build_state CASCADE;
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

  it('FAILS BEFORE: SELECT under the builder-mirror role is denied on kala_gochara_windows_v2', async () => {
    await expect(builderSelect()).rejects.toThrow(
      /permission denied for table kala_gochara_windows_v2/
    )
  })

  it('FAILS BEFORE: INSERT under the builder-mirror role is denied on kala_gochara_windows_v2', async () => {
    await expect(builderInsert()).rejects.toThrow(
      /permission denied for table kala_gochara_windows_v2/
    )
  })

  it('SUCCEEDS AFTER: applying the REAL migration 1238 file lets SELECT, INSERT and DELETE land', async () => {
    await pool.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))
    await builderSelect()
    // INSERT also exercises the identity sequence (nextval needs USAGE).
    await builderInsert()
    await builderDelete()
  })

  it('idempotent: applying migration 1238 a second time is a no-op and the ACL still holds', async () => {
    await pool.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))
    await builderSelect()
    await builderInsert()
  })

  it('scope: the grant matches the recorded production ACL exactly — arwd + sequence USAGE/SELECT, no CREATE, nothing wider', async () => {
    const check = await pool.query<{
      sel: boolean; ins: boolean; upd: boolean; del: boolean
      trunc: boolean; ref: boolean; trig: boolean
      schema_create: boolean; seq_usage: boolean; seq_select: boolean; seq_update: boolean
    }>(
      `SELECT has_table_privilege($1, 'public.kala_gochara_windows_v2', 'SELECT') AS sel,
              has_table_privilege($1, 'public.kala_gochara_windows_v2', 'INSERT') AS ins,
              has_table_privilege($1, 'public.kala_gochara_windows_v2', 'UPDATE') AS upd,
              has_table_privilege($1, 'public.kala_gochara_windows_v2', 'DELETE') AS del,
              has_table_privilege($1, 'public.kala_gochara_windows_v2', 'TRUNCATE') AS trunc,
              has_table_privilege($1, 'public.kala_gochara_windows_v2', 'REFERENCES') AS ref,
              has_table_privilege($1, 'public.kala_gochara_windows_v2', 'TRIGGER') AS trig,
              has_schema_privilege($1, 'public', 'CREATE') AS schema_create,
              has_sequence_privilege($1, 'public.kala_gochara_windows_v2_id_seq', 'USAGE') AS seq_usage,
              has_sequence_privilege($1, 'public.kala_gochara_windows_v2_id_seq', 'SELECT') AS seq_select,
              has_sequence_privilege($1, 'public.kala_gochara_windows_v2_id_seq', 'UPDATE') AS seq_update`,
      [BUILDER_ROLE]
    )
    expect(check.rows[0]).toEqual({
      sel: true, ins: true, upd: true, del: true,
      trunc: false, ref: false, trig: false,
      schema_create: false, seq_usage: true, seq_select: true, seq_update: false,
    })
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

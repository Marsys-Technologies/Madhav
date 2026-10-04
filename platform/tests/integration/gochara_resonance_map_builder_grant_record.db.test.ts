// @vitest-environment node
/**
 * Pravāha C9 (steward M20261002T004019-3811, 2026-10-02) — migration 1231
 * RECORDS the existing production ACL: data_plane_builder holds
 * SELECT/INSERT/UPDATE/DELETE on public.gochara_resonance_map (+ USAGE/SELECT
 * on its identity sequence) in production (C7 finding, verified read-only
 * 2026-10-02), but no migration granted it, so a fresh environment could
 * never run ka_gochara_resonance.
 *
 * Proof shape, mirroring the 1225 suite: a role created with EXACTLY
 * data_plane_builder's relevant grants (USAGE on schema public, NOTHING on
 * gochara_resonance_map) — SELECT/INSERT must FAIL before migration 1231 and
 * SUCCEED after. Both the table DDL (migration 459) and the grant migration
 * (1231) are executed from their REAL on-disk files (§N.8 — the detector
 * measures the claim it asserts, not a hand-copied proxy).
 *
 * Requires a THROWAWAY database. Skipped unless
 * M1231_RESONANCE_MAP_GRANT_TEST_DATABASE_URL is set, and refuses anything not
 * named `m1231_resonance_map_grant_test` — this suite creates and drops schema
 * objects and roles and must never touch production.
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres m1231_resonance_map_grant_test
 *   M1231_RESONANCE_MAP_GRANT_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/m1231_resonance_map_grant_test \
 *     npx vitest run tests/integration/gochara_resonance_map_builder_grant_record.db.test.ts
 *
 * Wired into CI alongside the C3/1225 step (db-integration-tests,
 * .github/workflows/ci.yml).
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.M1231_RESONANCE_MAP_GRANT_TEST_DATABASE_URL

const DDL_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../migrations/459_gochara_resonance_map.sql'
)
const GRANT_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../migrations/1231_gochara_resonance_map_builder_grant_record.sql'
)

// The mirror role carries the production role's real name so the REAL migration
// file (which GRANTs to `data_plane_builder` literally) applies against it —
// safe because this suite only ever runs on the disposable
// `m1231_resonance_map_grant_test`.
const BUILDER_ROLE = 'data_plane_builder'

let pool: Pool

async function builderSelect() {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(`SET LOCAL ROLE ${BUILDER_ROLE}`)
    await client.query(`SELECT count(*) FROM public.gochara_resonance_map`)
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
      `INSERT INTO public.gochara_resonance_map
         (chart_id, event_class, target_type, target_ref, weight, uncited_extension)
       VALUES ('00000000-0000-0000-0000-0000000000c9', 'career_entry', 'karaka', 'Saturn', 0.5, true)`
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

// True when this suite created the mirror role itself (fresh CI cluster); when
// the role pre-exists in the local cluster (other disposable suites create it
// too), it is reused — scrubbed of privileges in THIS database only — and left
// in place at teardown, never dropped.
let roleCreatedBySuite = false

describe.skipIf(!TEST_DB_URL)('migration 1231 — gochara_resonance_map builder grant record (C9) — live DB', () => {
  beforeAll(async () => {
    if (!/m1231_resonance_map_grant_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'M1231_RESONANCE_MAP_GRANT_TEST_DATABASE_URL must point at a disposable database named ' +
          '`m1231_resonance_map_grant_test`. This suite creates and drops schema objects and roles ' +
          'and must never run against production.'
      )
    }

    pool = new Pool({ connectionString: TEST_DB_URL })

    await pool.query(`
      DROP TABLE IF EXISTS gochara_resonance_map CASCADE;
      DROP TABLE IF EXISTS bg_transit_rules CASCADE;
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
      // "USAGE on schema public, nothing on gochara_resonance_map".
      await pool.query(`
        REVOKE ALL ON ALL TABLES IN SCHEMA public FROM ${BUILDER_ROLE};
        REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM ${BUILDER_ROLE};
        REVOKE ALL ON SCHEMA public FROM ${BUILDER_ROLE};
      `)
    }

    // Minimal stubs for the two relations the REAL 459 file touches besides
    // the audited table (same convention as the 1225/1216 suites' stubs);
    // gochara_resonance_map itself is created by the REAL file.
    await pool.query(`
      CREATE TABLE IF NOT EXISTS bg_transit_rules (id INTEGER PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS asset_registry (
        asset_id TEXT PRIMARY KEY, layer TEXT, sort_order INTEGER,
        sanskrit_name TEXT, english_name TEXT, english_description TEXT,
        storage_type TEXT, target_table TEXT, count_sql TEXT, size_sql TEXT,
        target_floor INTEGER, scope TEXT, is_active BOOLEAN, has_writer BOOLEAN,
        layer_name TEXT, layer_index TEXT, catalog_status TEXT,
        depends_on TEXT[]
      );
    `)
    await pool.query(fs.readFileSync(DDL_MIGRATION_PATH, 'utf8'))

    // A role with EXACTLY data_plane_builder's relevant grants for this path
    // before 1231: USAGE on schema public, NOTHING on gochara_resonance_map.
    await pool.query(`GRANT USAGE ON SCHEMA public TO ${BUILDER_ROLE}`)
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`
      DROP TABLE IF EXISTS gochara_resonance_map CASCADE;
      DROP TABLE IF EXISTS bg_transit_rules CASCADE;
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

  it('FAILS BEFORE: SELECT under the builder-mirror role is denied on gochara_resonance_map', async () => {
    await expect(builderSelect()).rejects.toThrow(
      /permission denied for table gochara_resonance_map/
    )
  })

  it('FAILS BEFORE: INSERT under the builder-mirror role is denied on gochara_resonance_map', async () => {
    await expect(builderInsert()).rejects.toThrow(
      /permission denied for table gochara_resonance_map/
    )
  })

  it('SUCCEEDS AFTER: applying the REAL migration 1231 file lets SELECT and INSERT land', async () => {
    await pool.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))
    await builderSelect()
    // INSERT also exercises the identity sequence (nextval needs USAGE).
    await builderInsert()
  })

  it('idempotent: applying migration 1231 a second time is a no-op and the ACL still holds', async () => {
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
      `SELECT has_table_privilege($1, 'public.gochara_resonance_map', 'SELECT') AS sel,
              has_table_privilege($1, 'public.gochara_resonance_map', 'INSERT') AS ins,
              has_table_privilege($1, 'public.gochara_resonance_map', 'UPDATE') AS upd,
              has_table_privilege($1, 'public.gochara_resonance_map', 'DELETE') AS del,
              has_table_privilege($1, 'public.gochara_resonance_map', 'TRUNCATE') AS trunc,
              has_table_privilege($1, 'public.gochara_resonance_map', 'REFERENCES') AS ref,
              has_table_privilege($1, 'public.gochara_resonance_map', 'TRIGGER') AS trig,
              has_schema_privilege($1, 'public', 'CREATE') AS schema_create,
              has_sequence_privilege($1, 'public.gochara_resonance_map_id_seq', 'USAGE') AS seq_usage,
              has_sequence_privilege($1, 'public.gochara_resonance_map_id_seq', 'SELECT') AS seq_select,
              has_sequence_privilege($1, 'public.gochara_resonance_map_id_seq', 'UPDATE') AS seq_update`,
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

// @vitest-environment node
/**
 * Pravāha C3 PART A (steward M20261001T222338-763f, 2026-10-01) — migration
 * 1225 grant fix for the audited Gochara-family privilege gap: the v3 build
 * path reads bg_transit_av_gates (services/gochara_v3/context.py:444,
 * _fetch_all_av_gate_rows) but data_plane_builder held no SELECT on it
 * (BUILDER_PRIVILEGE_AUDIT_GOCHARA_v1_0.md, verified against production).
 *
 * Proof shape, mirroring the 1211 suite: a role created with EXACTLY
 * data_plane_builder's relevant grants (USAGE on schema public, NOTHING on
 * bg_transit_av_gates) — SELECT must FAIL before migration 1225 and SUCCEED
 * after. Both the table DDL (migration 397) and the grant migration (1225)
 * are executed from their REAL on-disk files (§N.8 — the detector measures
 * the claim it asserts, not a hand-copied proxy).
 *
 * Requires a THROWAWAY database. Skipped unless
 * M1225_AV_GATES_GRANT_TEST_DATABASE_URL is set, and refuses anything not
 * named `m1225_av_gates_grant_test` — this suite creates and drops schema
 * objects and roles and must never touch production.
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres m1225_av_gates_grant_test
 *   M1225_AV_GATES_GRANT_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/m1225_av_gates_grant_test \
 *     npx vitest run tests/integration/bg_transit_av_gates_builder_select_grant.db.test.ts
 *
 * Wired into CI alongside the B6.0/1211 step (db-integration-tests,
 * .github/workflows/ci.yml).
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.M1225_AV_GATES_GRANT_TEST_DATABASE_URL

const DDL_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../supabase/migrations/397_bg_transit_av_gates.sql'
)
const GRANT_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../migrations/1225_bg_transit_av_gates_builder_select_grant.sql'
)

// The mirror role carries the production role's real name so the REAL migration
// file (which GRANTs to `data_plane_builder` literally) applies against it —
// safe because this suite only ever runs on the disposable `m1225_av_gates_grant_test`.
const BUILDER_ROLE = 'data_plane_builder'

let pool: Pool

async function builderSelect() {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(`SET LOCAL ROLE ${BUILDER_ROLE}`)
    await client.query(`SELECT count(*) FROM public.bg_transit_av_gates`)
    await client.query('COMMIT')
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

describe.skipIf(!TEST_DB_URL)('migration 1225 — bg_transit_av_gates builder SELECT grant (C3) — live DB', () => {
  beforeAll(async () => {
    if (!/m1225_av_gates_grant_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'M1225_AV_GATES_GRANT_TEST_DATABASE_URL must point at a disposable database named ' +
          '`m1225_av_gates_grant_test`. This suite creates and drops schema objects and roles ' +
          'and must never run against production.'
      )
    }

    pool = new Pool({ connectionString: TEST_DB_URL })

    await pool.query(`
      DROP TABLE IF EXISTS bg_transit_av_gates CASCADE;
      DROP TABLE IF EXISTS bg_transit_rules CASCADE;
    `)
    const roleCheck = await pool.query<{ exists: boolean }>(
      `SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${BUILDER_ROLE}') AS exists`
    )
    roleCreatedBySuite = !roleCheck.rows[0]!.exists
    if (roleCreatedBySuite) {
      await pool.query(`CREATE ROLE ${BUILDER_ROLE} NOLOGIN`)
    } else {
      // Scrub privileges held in THIS database so the before-state is exactly
      // "USAGE on schema public, nothing on bg_transit_av_gates".
      await pool.query(`
        REVOKE ALL ON ALL TABLES IN SCHEMA public FROM ${BUILDER_ROLE};
        REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM ${BUILDER_ROLE};
        REVOKE ALL ON SCHEMA public FROM ${BUILDER_ROLE};
      `)
    }

    // The REAL DDL migration (397). Its §2/§3 touch bg_transit_rules, so a
    // minimal stub stands in for it (same convention as the 1216 suite's
    // charts(id) stub); the audited table itself is created by the REAL file.
    await pool.query(`
      CREATE TABLE IF NOT EXISTS bg_transit_rules (
        rule_type TEXT, graha TEXT, primary_house INTEGER, vedha_house INTEGER,
        phala TEXT, classical_citation TEXT, rule_notes TEXT
      );
      CREATE UNIQUE INDEX IF NOT EXISTS uq_bg_transit_rules_stub
        ON bg_transit_rules (graha, rule_type, primary_house);
    `)
    await pool.query(fs.readFileSync(DDL_MIGRATION_PATH, 'utf8'))

    // A role with EXACTLY data_plane_builder's relevant production grants for
    // this path: USAGE on schema public, NOTHING on bg_transit_av_gates.
    await pool.query(`GRANT USAGE ON SCHEMA public TO ${BUILDER_ROLE}`)
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`
      DROP TABLE IF EXISTS bg_transit_av_gates CASCADE;
      DROP TABLE IF EXISTS bg_transit_rules CASCADE;
      REVOKE ALL ON ALL TABLES IN SCHEMA public FROM ${BUILDER_ROLE};
      REVOKE ALL ON SCHEMA public FROM ${BUILDER_ROLE};
    `)
    if (roleCreatedBySuite) {
      await pool.query(`DROP ROLE ${BUILDER_ROLE}`)
    }
    await pool.end()
  })

  it('FAILS BEFORE: SELECT under the builder-mirror role is denied on bg_transit_av_gates', async () => {
    await expect(builderSelect()).rejects.toThrow(
      /permission denied for table bg_transit_av_gates/
    )
  })

  it('SUCCEEDS AFTER: applying the REAL migration 1225 file lets SELECT land', async () => {
    await pool.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))
    await builderSelect()
  })

  it('idempotent: applying migration 1225 a second time is a no-op and SELECT still works', async () => {
    await pool.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))
    await builderSelect()
  })

  it('scope: the grant widens nothing else — no INSERT/UPDATE/DELETE, no CREATE on schema public, no sequence USAGE', async () => {
    const check = await pool.query<{
      ins: boolean; upd: boolean; del: boolean; schema_create: boolean; seq_usage: boolean
    }>(
      `SELECT has_table_privilege($1, 'public.bg_transit_av_gates', 'INSERT') AS ins,
              has_table_privilege($1, 'public.bg_transit_av_gates', 'UPDATE') AS upd,
              has_table_privilege($1, 'public.bg_transit_av_gates', 'DELETE') AS del,
              has_schema_privilege($1, 'public', 'CREATE') AS schema_create,
              has_sequence_privilege($1, 'public.bg_transit_av_gates_id_seq', 'USAGE') AS seq_usage`,
      [BUILDER_ROLE]
    )
    expect(check.rows[0]).toEqual({
      ins: false, upd: false, del: false, schema_create: false, seq_usage: false,
    })
  })
})

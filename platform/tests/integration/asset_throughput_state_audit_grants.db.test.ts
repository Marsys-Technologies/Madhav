// @vitest-environment node
/**
 * Pravāha B6.0 (steward M20261001T160205-5005, native-approved 2026-10-01) —
 * migration 1211 grant fix for the production outage where every pipeline build
 * failed at the first asset_throughput state change: the F-152 AFTER trigger
 * (migration 586) inserts into asset_throughput_state_audit with the CALLER's
 * privileges (not SECURITY DEFINER), and data_plane_builder held no INSERT on
 * the audit table and no USAGE on its identity sequence.
 *
 * Proof shape, per the steward's instruction: a role created with EXACTLY
 * data_plane_builder's relevant grants (UPDATE on asset_throughput, USAGE on
 * schema public, NOTHING on the audit table or its sequence) — the state-change
 * UPDATE must FAIL before migration 1211 and SUCCEED after, with the audit row
 * recording that role as db_user. Both the trigger migration (586) and the
 * grant migration (1211) are executed from their REAL on-disk files (§N.8 —
 * the detector measures the claim it asserts, not a hand-copied proxy).
 *
 * Requires a THROWAWAY database. Skipped unless
 * M1211_AUDIT_GRANT_TEST_DATABASE_URL is set, and refuses anything not named
 * `m1211_audit_grant_test` — this suite creates and drops schema objects and
 * roles and must never touch production.
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres m1211_audit_grant_test
 *   M1211_AUDIT_GRANT_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/m1211_audit_grant_test \
 *     npx vitest run tests/integration/asset_throughput_state_audit_grants.db.test.ts
 *
 * Wired into CI alongside the F-152 step (db-integration-tests,
 * .github/workflows/ci.yml) so the fails-before/succeeds-after proof re-verifies
 * on every PR.
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.M1211_AUDIT_GRANT_TEST_DATABASE_URL

const TRIGGER_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../supabase/migrations/586_f152_asset_throughput_state_audit.sql'
)
const GRANT_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../migrations/1211_asset_throughput_state_audit_builder_grants.sql'
)

const CHART = '00000000-0000-4000-8000-0000000000ab'
const ASSET_ID = '_t_m1211_asset'
// The mirror role carries the production role's real name so the REAL migration
// file (which GRANTs to `data_plane_builder` literally) applies against it —
// safe because this suite only ever runs on the disposable `m1211_audit_grant_test`.
const BUILDER_ROLE = 'data_plane_builder'

let pool: Pool

async function builderUpdateState(state: string) {
  // A connection AS the builder-mirror role, so the trigger's insert runs with
  // exactly the caller's privileges — the production failure mode.
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(`SET LOCAL ROLE ${BUILDER_ROLE}`)
    await client.query(
      `UPDATE asset_throughput SET state = $3 WHERE chart_id = $1 AND asset_id = $2`,
      [CHART, ASSET_ID, state]
    )
    await client.query('COMMIT')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}

describe.skipIf(!TEST_DB_URL)('migration 1211 — asset_throughput_state_audit builder grants (B6.0) — live DB', () => {
  beforeAll(async () => {
    if (!/m1211_audit_grant_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'M1211_AUDIT_GRANT_TEST_DATABASE_URL must point at a disposable database named ' +
          '`m1211_audit_grant_test`. This suite creates and drops schema objects and roles ' +
          'and must never run against production.'
      )
    }

    pool = new Pool({ connectionString: TEST_DB_URL })

    await pool.query(`
      DROP TABLE IF EXISTS asset_throughput_state_audit, asset_throughput CASCADE;
      DROP FUNCTION IF EXISTS _record_asset_throughput_state_change() CASCADE;
      DO $cleanup$ BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${BUILDER_ROLE}') THEN
          EXECUTE 'REVOKE ALL ON SCHEMA public FROM ${BUILDER_ROLE}';
        END IF;
      END $cleanup$;
      DROP ROLE IF EXISTS ${BUILDER_ROLE};

      CREATE TABLE asset_throughput (
        chart_id       UUID,
        asset_id       TEXT NOT NULL,
        state          TEXT NOT NULL DEFAULT 'dormant'
          CHECK (state IN ('dormant','building','lit','stale','error')),
        last_error     TEXT,
        last_built_at  TIMESTAMPTZ
      );
    `)

    // The REAL trigger migration (586).
    await pool.query(fs.readFileSync(TRIGGER_MIGRATION_PATH, 'utf8'))

    // A role with EXACTLY data_plane_builder's relevant production grants,
    // verified read-only against production before this migration was authored:
    // UPDATE on asset_throughput = true, INSERT/SELECT on the audit table =
    // false, USAGE on the audit sequence = false.
    await pool.query(`
      CREATE ROLE ${BUILDER_ROLE} NOLOGIN;
      GRANT USAGE ON SCHEMA public TO ${BUILDER_ROLE};
      GRANT SELECT, INSERT, UPDATE, DELETE ON asset_throughput TO ${BUILDER_ROLE};
    `)

    await pool.query(
      `INSERT INTO asset_throughput (chart_id, asset_id, state) VALUES ($1, $2, 'lit')`,
      [CHART, ASSET_ID]
    )
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`
      DROP TABLE IF EXISTS asset_throughput_state_audit, asset_throughput CASCADE;
      DROP FUNCTION IF EXISTS _record_asset_throughput_state_change() CASCADE;
      REVOKE ALL ON SCHEMA public FROM ${BUILDER_ROLE};
      DROP ROLE IF EXISTS ${BUILDER_ROLE};
    `)
    await pool.end()
  })

  it('FAILS BEFORE: a state change under the builder-mirror role is denied on the audit table', async () => {
    await expect(builderUpdateState('stale')).rejects.toThrow(
      /permission denied for table asset_throughput_state_audit/
    )
    // The state change rolled back with its trigger insert — no partial write.
    const state = await pool.query<{ state: string }>(
      `SELECT state FROM asset_throughput WHERE chart_id = $1 AND asset_id = $2`,
      [CHART, ASSET_ID]
    )
    expect(state.rows[0]!.state).toBe('lit')
  })

  it('SUCCEEDS AFTER: applying the REAL migration 1211 file lets the state change land with its audit row', async () => {
    await pool.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))

    await builderUpdateState('stale')

    const audit = await pool.query(
      `SELECT chart_id, asset_id, old_state, new_state, db_user FROM asset_throughput_state_audit
       ORDER BY changed_at DESC, id DESC LIMIT 1`
    )
    expect(audit.rows[0]).toMatchObject({
      chart_id: CHART,
      asset_id: ASSET_ID,
      old_state: 'lit',
      new_state: 'stale',
      db_user: BUILDER_ROLE,
    })
  })

  it('idempotent: applying migration 1211 a second time is a no-op and the trigger path still works', async () => {
    await pool.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))
    await builderUpdateState('error')
    const audit = await pool.query<{ new_state: string }>(
      `SELECT new_state FROM asset_throughput_state_audit ORDER BY changed_at DESC, id DESC LIMIT 1`
    )
    expect(audit.rows[0]!.new_state).toBe('error')
  })

  it('scope: the grant widens nothing else — no SELECT on the audit table, no CREATE on schema public', async () => {
    const check = await pool.query<{ audit_select: boolean; schema_create: boolean }>(
      `SELECT has_table_privilege($1, 'public.asset_throughput_state_audit', 'SELECT') AS audit_select,
              has_schema_privilege($1, 'public', 'CREATE') AS schema_create`,
      [BUILDER_ROLE]
    )
    expect(check.rows[0]!.audit_select).toBe(false)
    expect(check.rows[0]!.schema_create).toBe(false)
  })
})

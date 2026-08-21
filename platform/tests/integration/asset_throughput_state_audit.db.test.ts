// @vitest-environment node
/**
 * PARIŚEṢA-V4 F-152 — asset_throughput_state_audit trigger, LIVE-DB test.
 *
 * Executes the REAL migration file (586) against a REAL throwaway Postgres, so
 * the AFTER UPDATE OF state trigger is proven end-to-end against its own
 * on-disk SQL rather than a hand-copied re-implementation that could silently
 * drift from what actually ships (CLAUDE.md §N.8 — a detector must measure the
 * claim it asserts, not a proxy for it). Mirrors
 * tests/integration/build_protected_assets_sweep_guard.db.test.ts's pattern.
 *
 * Requires a THROWAWAY database. It is skipped unless
 * F152_AUDIT_TEST_DATABASE_URL is set, and it refuses to run against anything
 * that is not obviously disposable (see the guard in beforeAll) — this suite
 * CREATEs and DROPs schema objects and must never touch production.
 *
 *   initdb -D /tmp/pgdata -U postgres --auth=trust
 *   pg_ctl -D /tmp/pgdata -o "-p 55432 -k '' -c listen_addresses=127.0.0.1" start
 *   createdb -h 127.0.0.1 -p 55432 -U postgres f152_audit_test
 *   F152_AUDIT_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/f152_audit_test \
 *     npx vitest run tests/integration/asset_throughput_state_audit.db.test.ts
 *
 * Wired into CI as well — see the "F-152" step in db-integration-tests
 * (.github/workflows/ci.yml) — so the fire/no-fire proof this migration's PR
 * required is not merely opt-in-and-may-never-run, it re-verifies on every PR.
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { Pool } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.F152_AUDIT_TEST_DATABASE_URL

const MIGRATION_PATH = path.resolve(
  __dirname,
  '../../supabase/migrations/586_f152_asset_throughput_state_audit.sql'
)

// Fixture chart_id. Same fixture-UUID idiom as the other .db.test.ts files in
// this directory — a `-00aa` block that can never collide with a real chart_id.
const CHART = '00000000-0000-4000-8000-0000000000aa'
const ASSET_ID = '_t_f152_asset'

let pool: Pool

async function latestAuditRow() {
  const res = await pool.query(
    `SELECT * FROM asset_throughput_state_audit ORDER BY changed_at DESC, id DESC LIMIT 1`
  )
  return res.rows[0] ?? null
}

async function auditRowCount(): Promise<number> {
  const res = await pool.query<{ count: string }>(
    'SELECT COUNT(*)::text AS count FROM asset_throughput_state_audit'
  )
  return parseInt(res.rows[0]!.count, 10)
}

describe.skipIf(!TEST_DB_URL)('asset_throughput_state_audit trigger (F-152) — live DB', () => {
  beforeAll(async () => {
    // Refuse to run anywhere that is not plainly a throwaway.
    if (!/f152_audit_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'F152_AUDIT_TEST_DATABASE_URL must point at a disposable database named ' +
          '`f152_audit_test`. This suite creates and drops schema objects and ' +
          'must never run against production.'
      )
    }

    pool = new Pool({ connectionString: TEST_DB_URL })

    // Minimal faithful asset_throughput — the columns + CHECK migration 171
    // declares, enough for the trigger under test (which reads only
    // OLD.state / NEW.state / NEW.chart_id / NEW.asset_id) to attach and fire
    // for real. No FK to charts(id)/asset_registry — the trigger never
    // touches either.
    await pool.query(`
      DROP TABLE IF EXISTS asset_throughput_state_audit, asset_throughput CASCADE;
      DROP FUNCTION IF EXISTS _record_asset_throughput_state_change() CASCADE;

      CREATE TABLE asset_throughput (
        chart_id       UUID,
        asset_id       TEXT NOT NULL,
        state          TEXT NOT NULL DEFAULT 'dormant'
          CHECK (state IN ('dormant','building','lit','stale','error')),
        last_error     TEXT,
        last_built_at  TIMESTAMPTZ
      );
      CREATE UNIQUE INDEX ON asset_throughput
        (COALESCE(chart_id, '00000000-0000-0000-0000-000000000000'::uuid), asset_id);
    `)

    // Execute the REAL migration file — the trigger function/trigger/table
    // under test are the exact ones that will ship, not a re-implementation.
    const migrationSql = fs.readFileSync(MIGRATION_PATH, 'utf8')
    await pool.query(migrationSql)

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
    `)
    await pool.end()
  })

  beforeEach(async () => {
    // Reset the fixture row to a known state, then clear the audit table (the
    // reset UPDATE may itself fire the trigger — clearing AFTER it is what
    // guarantees every test starts from a clean slate regardless of which
    // state the previous test left the row in).
    await pool.query(
      `UPDATE asset_throughput SET state = 'lit' WHERE chart_id = $1 AND asset_id = $2`,
      [CHART, ASSET_ID]
    )
    await pool.query('TRUNCATE asset_throughput_state_audit RESTART IDENTITY')
  })

  it('FIRES: an UPDATE that changes state writes exactly one audit row', async () => {
    await pool.query(
      `UPDATE asset_throughput SET state = 'stale' WHERE chart_id = $1 AND asset_id = $2 AND state = 'lit'`,
      [CHART, ASSET_ID]
    )

    const row = await latestAuditRow()
    expect(row, 'the trigger must have written a row').not.toBeNull()
    expect(row!.chart_id).toBe(CHART)
    expect(row!.asset_id).toBe(ASSET_ID)
    expect(row!.old_state).toBe('lit')
    expect(row!.new_state).toBe('stale')
    expect(row!.changed_at).toBeTruthy()
    expect(await auditRowCount()).toBe(1)
  })

  it('captures db_user, application_name, and the marsys.triggered_by GUC', async () => {
    const client = await pool.connect()
    try {
      await client.query('BEGIN')
      await client.query("SET LOCAL application_name = 'f152_test_app'")
      await client.query("SET LOCAL marsys.triggered_by = 'asset_runner'")
      await client.query(
        `UPDATE asset_throughput SET state = 'error' WHERE chart_id = $1 AND asset_id = $2 AND state = 'lit'`,
        [CHART, ASSET_ID]
      )
      await client.query('COMMIT')
    } finally {
      client.release()
    }

    const row = await latestAuditRow()
    expect(row).not.toBeNull()
    expect(row!.application_name).toBe('f152_test_app')
    expect(row!.triggered_by).toBe('asset_runner')
    expect(row!.db_user).toBeTruthy()
  })

  it('DOES NOT FIRE: an UPDATE that leaves state unchanged writes no audit row', async () => {
    // Negative control #1 — the ruling's mandatory non-firing case: a write
    // that touches a DIFFERENT column entirely.
    await pool.query(
      `UPDATE asset_throughput SET last_error = 'unrelated column touched' WHERE chart_id = $1 AND asset_id = $2`,
      [CHART, ASSET_ID]
    )
    expect(await auditRowCount()).toBe(0)
  })

  it('DOES NOT FIRE: an UPDATE that sets state to the SAME value writes no audit row', async () => {
    // Negative control #2 — WHEN (OLD.state IS DISTINCT FROM NEW.state) must
    // suppress a same-value SET state = 'lit' just as it does the untouched case.
    await pool.query(
      `UPDATE asset_throughput SET state = 'lit' WHERE chart_id = $1 AND asset_id = $2`,
      [CHART, ASSET_ID]
    )
    expect(await auditRowCount()).toBe(0)
  })

  it('triggered_by is NULL when the GUC was never set (a direct psql-style UPDATE)', async () => {
    await pool.query(
      `UPDATE asset_throughput SET state = 'building' WHERE chart_id = $1 AND asset_id = $2 AND state = 'lit'`,
      [CHART, ASSET_ID]
    )
    const row = await latestAuditRow()
    expect(row).not.toBeNull()
    expect(row!.triggered_by).toBeNull()
  })
})

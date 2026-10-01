// @vitest-environment node
/**
 * Suvarna R-25 (SS ruling, value 1800) — migration 1218 raises
 * asset_registry.writer_timeout_seconds 600 -> 1800 for bo_grounding and
 * bo_laksana_rerank ONLY.
 *
 * Proof shape: the REAL migration file is executed (inside BEGIN/COMMIT, the way
 * platform/scripts/migrate.ts runs it) against a fixture asset_registry that
 * carries the REAL nirmana_registry_receipt_invalidation trigger (extracted from
 * migration 596), so "the trigger does not fire" is measured, not assumed (§N.8).
 * Scenarios: live-like (both at 600), replay, one target already 1800 / one at a
 * deliberate other value (left alone, NOTICE), one target missing (raises),
 * neither present (no-op), plus two fail-closed controls whose fixture triggers
 * perturb the registry mid-migration.
 *
 * Requires a THROWAWAY database. Skipped unless M1218_TIMEOUT_TEST_DATABASE_URL is
 * set, and refuses anything not named `m1218_timeout_test` — this suite creates and
 * drops tables and functions and must never touch production.
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres m1218_timeout_test
 *   M1218_TIMEOUT_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/m1218_timeout_test \
 *     npx vitest run tests/integration/suvarna_bodha_writer_timeouts_1218.db.test.ts
 *
 * Not yet wired into CI: the provision-DB-then-run steps (same pattern as the 1211 grant
 * test) return as a follow-up PR after #2845 merges. Until then it skips cleanly when the
 * env var is unset and is run by hand against a throwaway database.
 */
import { describe, it, expect, beforeAll, beforeEach, afterAll } from 'vitest'
import { Pool } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.M1218_TIMEOUT_TEST_DATABASE_URL

const MIGRATION_PATH = path.resolve(__dirname, '../../migrations/1218_suvarna_bodha_writer_timeouts.sql')
const TRIGGER_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../supabase/migrations/596_nirmana_provenance_receipts.sql',
)

const TARGETS = ['bo_grounding', 'bo_laksana_rerank'] as const

let pool: Pool

/** The real trigger function + trigger, sliced verbatim from migration 596. */
function realRegistryTriggerSql(): string {
  const sql = fs.readFileSync(TRIGGER_MIGRATION_PATH, 'utf8')
  const start = sql.indexOf('CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts()')
  const endMarker = 'EXECUTE FUNCTION nirmana_invalidate_registry_receipts();'
  const end = sql.indexOf(endMarker)
  if (start < 0 || end < 0) throw new Error('registry receipt invalidation trigger not found in migration 596')
  return sql.slice(start, end + endMarker.length)
}

async function resetFixture(rows: Array<[string, number]>) {
  await pool.query(`
    DROP TRIGGER IF EXISTS t_m1218_perturb ON asset_registry;
    DROP FUNCTION IF EXISTS t_m1218_perturb() CASCADE;
    TRUNCATE asset_registry, asset_freshness;
  `)
  for (const [assetId, timeout] of rows) {
    await pool.query(
      `INSERT INTO asset_registry (asset_id, writer_timeout_seconds, depends_on, scope, is_active, has_writer, target_table)
       VALUES ($1, $2, ARRAY['x'], 'per_chart', true, true, 't_' || $1)`,
      [assetId, timeout],
    )
    await pool.query(`INSERT INTO asset_freshness (asset_id, freshness_state) VALUES ($1, 'fresh')`, [assetId])
  }
}

const LIVE_LIKE: Array<[string, number]> = [
  ['bo_grounding', 600],
  ['bo_laksana_rerank', 600],
  ['bo_laksana', 10800],
  ['bo_arudha', 600],
  ['ka_gochara', 1800],
  ['ka_kshetra', 86400],
]

async function snapshot() {
  const registry = await pool.query<{ r: Record<string, unknown> }>(
    `SELECT to_jsonb(r) AS r FROM asset_registry r ORDER BY asset_id`,
  )
  const freshness = await pool.query<{ f: Record<string, unknown> }>(
    `SELECT to_jsonb(f) AS f FROM asset_freshness f ORDER BY asset_id`,
  )
  return { registry: registry.rows.map((x) => x.r), freshness: freshness.rows.map((x) => x.f) }
}

async function timeouts(): Promise<Record<string, number>> {
  const res = await pool.query<{ asset_id: string; writer_timeout_seconds: number }>(
    `SELECT asset_id, writer_timeout_seconds FROM asset_registry ORDER BY asset_id`,
  )
  return Object.fromEntries(res.rows.map((r) => [r.asset_id, r.writer_timeout_seconds]))
}

/** Runs the REAL migration file the way migrate.ts does (BEGIN; <file>; COMMIT) and returns NOTICEs. */
async function applyMigration(): Promise<string[]> {
  const sql = fs.readFileSync(MIGRATION_PATH, 'utf8')
  const notices: string[] = []
  const client = await pool.connect()
  client.on('notice', (n) => notices.push(n.message))
  try {
    await client.query('BEGIN')
    await client.query(sql)
    await client.query('COMMIT')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.removeAllListeners('notice')
    client.release()
  }
  return notices
}

describe.skipIf(!TEST_DB_URL)('migration 1218 — bodha writer timeouts 600 -> 1800 — live DB', () => {
  beforeAll(async () => {
    if (!/m1218_timeout_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'M1218_TIMEOUT_TEST_DATABASE_URL must point at a disposable database named ' +
          '`m1218_timeout_test`. This suite creates and drops tables and functions and must ' +
          'never run against production.',
      )
    }
    pool = new Pool({ connectionString: TEST_DB_URL })
    await pool.query(`
      DROP TABLE IF EXISTS asset_freshness, asset_registry CASCADE;
      DROP FUNCTION IF EXISTS nirmana_invalidate_registry_receipts() CASCADE;

      -- Fixture asset_registry: the real column the migration edits, plus the columns the real
      -- receipt-invalidation trigger watches.
      CREATE TABLE asset_registry (
        asset_id               TEXT PRIMARY KEY,
        writer_timeout_seconds INTEGER NOT NULL DEFAULT 600,
        depends_on             TEXT[],
        natural_key_partition  TEXT,
        health_probe           JSONB,
        integrity_check_sql    TEXT,
        target_floor           INTEGER,
        asset_kind             TEXT,
        asset_type             TEXT,
        scope                  TEXT,
        has_writer             BOOLEAN,
        is_active              BOOLEAN,
        target_table           TEXT
      );
      CREATE TABLE asset_freshness (
        asset_id        TEXT NOT NULL,
        freshness_state TEXT NOT NULL,
        reasons         JSONB NOT NULL DEFAULT '[]'::jsonb,
        observed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
      );
    `)
    await pool.query(realRegistryTriggerSql())
  })

  beforeEach(async () => {
    await resetFixture(LIVE_LIKE)
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`
      DROP TRIGGER IF EXISTS t_m1218_perturb ON asset_registry;
      DROP FUNCTION IF EXISTS t_m1218_perturb() CASCADE;
      DROP TABLE IF EXISTS asset_freshness, asset_registry CASCADE;
      DROP FUNCTION IF EXISTS nirmana_invalidate_registry_receipts() CASCADE;
    `)
    await pool.end()
  })

  it('control: the real trigger IS live in the fixture (it fires on a watched column)', async () => {
    await pool.query(`UPDATE asset_registry SET is_active = false WHERE asset_id = 'bo_arudha'`)
    const stale = await pool.query(`SELECT freshness_state FROM asset_freshness WHERE asset_id = 'bo_arudha'`)
    expect(stale.rows[0]!.freshness_state).toBe('stale')
  })

  it('live-like: both targets at 600 move to 1800, nothing else moves, the trigger does not fire', async () => {
    const before = await snapshot()
    const notices = await applyMigration()
    const after = await timeouts()
    expect(after).toEqual({
      bo_arudha: 600,
      bo_grounding: 1800,
      bo_laksana: 10800,
      bo_laksana_rerank: 1800,
      ka_gochara: 1800,
      ka_kshetra: 86400,
    })
    expect(notices.filter((m) => m.startsWith('1218:'))).toEqual([])

    // Every column of every row is identical except writer_timeout_seconds of the two targets, and
    // asset_freshness is byte-identical (no row marked stale by the invalidation trigger).
    const now = await snapshot()
    const expectedRegistry = before.registry.map((row) =>
      TARGETS.includes(row.asset_id as (typeof TARGETS)[number])
        ? { ...row, writer_timeout_seconds: 1800 }
        : row,
    )
    expect(now.registry).toEqual(expectedRegistry)
    expect(now.freshness).toEqual(before.freshness)
  })

  it('replay: a second apply changes nothing and says it left the targets alone', async () => {
    await applyMigration()
    const afterFirst = await snapshot()
    const notices = await applyMigration()
    expect(await snapshot()).toEqual(afterFirst)
    expect(notices.some((m) => m.includes('1218: a target row was not at 600'))).toBe(true)
  })

  it('one target already at 1800: the other still moves, the 1800 one is left alone, NOTICE', async () => {
    await resetFixture(LIVE_LIKE.map(([id, t]) => [id, id === 'bo_grounding' ? 1800 : t] as [string, number]))
    const notices = await applyMigration()
    const after = await timeouts()
    expect(after.bo_grounding).toBe(1800)
    expect(after.bo_laksana_rerank).toBe(1800)
    expect(notices.some((m) => m.includes('1218: a target row was not at 600'))).toBe(true)
  })

  it('one target at a deliberate other value is never overwritten; the migration still succeeds with a NOTICE', async () => {
    await resetFixture(LIVE_LIKE.map(([id, t]) => [id, id === 'bo_grounding' ? 7200 : t] as [string, number]))
    const notices = await applyMigration()
    const after = await timeouts()
    expect(after.bo_grounding).toBe(7200)
    expect(after.bo_laksana_rerank).toBe(1800)
    expect(notices.some((m) => m.includes('1218: a target row was not at 600'))).toBe(true)
  })

  it('one target missing: raises (Guard 1) and rolls back, leaving the registry untouched', async () => {
    await resetFixture(LIVE_LIKE.filter(([id]) => id !== 'bo_grounding'))
    const before = await snapshot()
    await expect(applyMigration()).rejects.toThrow(
      /1218: expected both or neither of bo_grounding\/bo_laksana_rerank in asset_registry, found 1/,
    )
    expect(await snapshot()).toEqual(before)
  })

  it('neither target present (fresh bootstrap): a no-op that succeeds', async () => {
    await resetFixture(LIVE_LIKE.filter(([id]) => !TARGETS.includes(id as (typeof TARGETS)[number])))
    const before = await snapshot()
    const notices = await applyMigration()
    expect(await snapshot()).toEqual(before)
    expect(notices.filter((m) => m.startsWith('1218:'))).toEqual([])
  })

  it('fail-closed: a hidden side effect that moves a THIRD row raises on the changed-row count and rolls back', async () => {
    await pool.query(`
      CREATE FUNCTION t_m1218_perturb() RETURNS trigger LANGUAGE plpgsql AS $f$
      BEGIN
        UPDATE asset_registry SET writer_timeout_seconds = 1 WHERE asset_id = 'ka_gochara';
        RETURN NEW;
      END $f$;
      CREATE TRIGGER t_m1218_perturb AFTER UPDATE ON asset_registry
        FOR EACH ROW WHEN (NEW.asset_id = 'bo_grounding') EXECUTE FUNCTION t_m1218_perturb();
    `)
    const before = await snapshot()
    await expect(applyMigration()).rejects.toThrow(
      /1218: 3 asset_registry row\(s\) changed writer_timeout_seconds, expected exactly 2/,
    )
    expect(await snapshot()).toEqual(before)
  })

  it('fail-closed: a change to a NON-target row is reported by name even when the changed-row count balances', async () => {
    // bo_grounding at 600 (entitled change), bo_laksana_rerank at a deliberate 7200 (excluded):
    // expected = 1. The fixture trigger SUPPRESSES bo_grounding's update and instead sets another row
    // to 1800, so actual = 1 and the count check balances; only the non-target clause of the stray
    // check can name the offending row (the later "not at 1800" check would raise a different message).
    await resetFixture(LIVE_LIKE.map(([id, t]) => [id, id === 'bo_laksana_rerank' ? 7200 : t] as [string, number]))
    await pool.query(`
      CREATE FUNCTION t_m1218_perturb() RETURNS trigger LANGUAGE plpgsql AS $f$
      BEGIN
        UPDATE asset_registry SET writer_timeout_seconds = 1800 WHERE asset_id = 'bo_arudha';
        RETURN NULL;
      END $f$;
      CREATE TRIGGER t_m1218_perturb BEFORE UPDATE ON asset_registry
        FOR EACH ROW WHEN (NEW.asset_id = 'bo_grounding') EXECUTE FUNCTION t_m1218_perturb();
    `)
    const before = await snapshot()
    await expect(applyMigration()).rejects.toThrow(/1218: unexpected writer_timeout_seconds change on: bo_arudha/)
    expect(await snapshot()).toEqual(before)
  })

  it('fail-closed: a target that was at 600 but silently stayed at 600 is named even when counts and strays balance', async () => {
    // bo_grounding at 600 (entitled change), bo_laksana_rerank at a deliberate 7200 (excluded):
    // expected = 1. The fixture trigger SUPPRESSES bo_grounding's update and moves bo_laksana_rerank
    // to 1800 instead: actual = 1 (balances), the changed row is a target reading 1800 (no stray), so
    // only the "not at 1800 after update" check can catch that bo_grounding never moved.
    await resetFixture(LIVE_LIKE.map(([id, t]) => [id, id === 'bo_laksana_rerank' ? 7200 : t] as [string, number]))
    await pool.query(`
      CREATE FUNCTION t_m1218_perturb() RETURNS trigger LANGUAGE plpgsql AS $f$
      BEGIN
        UPDATE asset_registry SET writer_timeout_seconds = 1800 WHERE asset_id = 'bo_laksana_rerank';
        RETURN NULL;
      END $f$;
      CREATE TRIGGER t_m1218_perturb BEFORE UPDATE ON asset_registry
        FOR EACH ROW WHEN (NEW.asset_id = 'bo_grounding') EXECUTE FUNCTION t_m1218_perturb();
    `)
    const before = await snapshot()
    await expect(applyMigration()).rejects.toThrow(/1218: target row\(s\) not at 1800 after update: bo_grounding=600/)
    expect(await snapshot()).toEqual(before)
  })
})

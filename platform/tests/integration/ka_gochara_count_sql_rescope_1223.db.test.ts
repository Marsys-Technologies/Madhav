// @vitest-environment node
/**
 * Pravāha TASK C1 (steward M20261001T212520-1e31, 2026-10-01) — migration 1223
 * re-scopes asset_registry.count_sql for asset_id='ka_gochara' from the 1091
 * text (generation '4.0', a burned label) to '4.1'. Decision note:
 * 00_ARCHITECTURE/briefs/pravaha/decisions/KA_GOCHARA_COCKPIT_COUNT_NOTE_v1_0.md.
 *
 * Proof shape: a minimal real asset_registry row carrying EXACTLY the text 1091
 * wrote; the REAL on-disk 1223 file is executed against it (§N.8 — the detector
 * measures the claim it asserts). Assertions: before = '4.0' text, after =
 * '4.1' text, second run is a no-op, an unrecognised prior text raises and
 * changes nothing, a missing row raises.
 *
 * Requires a THROWAWAY database. Skipped unless
 * M1223_KA_GOCHARA_RESCOPE_TEST_DATABASE_URL is set, and refuses anything not
 * named `m1223_ka_gochara_rescope_test` — this suite creates and drops schema
 * objects and must never touch production.
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres m1223_ka_gochara_rescope_test
 *   M1223_KA_GOCHARA_RESCOPE_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/m1223_ka_gochara_rescope_test \
 *     npx vitest run tests/integration/ka_gochara_count_sql_rescope_1223.db.test.ts
 *
 * Wired into CI alongside the B6.0/1211 step (db-integration-tests,
 * .github/workflows/ci.yml).
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.M1223_KA_GOCHARA_RESCOPE_TEST_DATABASE_URL

const MIGRATION_PATH = path.resolve(
  __dirname,
  '../../migrations/1223_a26_ka_gochara_count_sql_rescope_41.sql'
)

const C_1091 =
  "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'"
const C_41 =
  "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='4.1'"

let pool: Pool

async function seed(countSql: string | null) {
  await pool.query(`DELETE FROM asset_registry`)
  if (countSql !== null) {
    await pool.query(
      `INSERT INTO asset_registry (asset_id, target_table, count_sql)
       VALUES ('ka_gochara', 'kala_gochara_windows', $1)`,
      [countSql]
    )
  }
}

async function currentCountSql(): Promise<string | undefined> {
  const r = await pool.query<{ count_sql: string }>(
    `SELECT count_sql FROM asset_registry WHERE asset_id = 'ka_gochara'`
  )
  return r.rows[0]?.count_sql
}

async function applyMigration(): Promise<void> {
  await pool.query(fs.readFileSync(MIGRATION_PATH, 'utf8'))
}

describe.skipIf(!TEST_DB_URL)('migration 1223 — ka_gochara count_sql re-scope 4.0 → 4.1 — live DB', () => {
  beforeAll(async () => {
    if (!/m1223_ka_gochara_rescope_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'M1223_KA_GOCHARA_RESCOPE_TEST_DATABASE_URL must point at a disposable database named ' +
          '`m1223_ka_gochara_rescope_test`. This suite creates and drops schema objects ' +
          'and must never run against production.'
      )
    }

    pool = new Pool({ connectionString: TEST_DB_URL })

    await pool.query(`DROP TABLE IF EXISTS asset_registry CASCADE`)
    await pool.query(`
      CREATE TABLE asset_registry (
        asset_id     text PRIMARY KEY,
        target_table text,
        count_sql    text
      )
    `)
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`DROP TABLE IF EXISTS asset_registry CASCADE`)
    await pool.end()
  })

  it("BEFORE: the seeded row carries exactly the '4.0' text migration 1091 wrote", async () => {
    await seed(C_1091)
    expect(await currentCountSql()).toBe(C_1091)
  })

  it("AFTER: applying the REAL 1223 file re-scopes the row to the '4.1' text", async () => {
    await applyMigration()
    expect(await currentCountSql()).toBe(C_41)
  })

  it('IDEMPOTENT: a second application is a no-op', async () => {
    await applyMigration()
    expect(await currentCountSql()).toBe(C_41)
  })

  it('FAILS CLOSED: an unrecognised prior count_sql raises and leaves the row untouched', async () => {
    const foreign =
      "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='9.9'"
    await seed(foreign)
    await expect(applyMigration()).rejects.toThrow(/unexpected ka_gochara count_sql/)
    expect(await currentCountSql()).toBe(foreign)
  })

  it('FAILS CLOSED: a missing ka_gochara row raises', async () => {
    await seed(null)
    await expect(applyMigration()).rejects.toThrow(/row for ka_gochara not found/)
    expect(await currentCountSql()).toBeUndefined()
  })
})

/**
 * Migration 1230 — ka_gochara's registry row describes what its REGISTERED WRITER writes.
 * Disposable-database evidence (no mocks below the SQL):
 *
 *   1. The migration FILE itself is applied (never re-implemented): the row becomes the restored
 *      target_table / count_sql / integrity contract / clear_tables; replay is a no-op; an
 *      unexpected prior state and a snapshot that differs from what it would write both RAISE.
 *   2. count_sql counts the rows the writer writes — the relation and generation are READ OUT OF
 *      THE WRITER MODULE'S OWN SOURCE (TABLE / GENERATION_V2), never restated.
 *   3. The restored integrity contract is NOT vacuous where rows exist: it reads TRUE on a
 *      consistent written chart and FALSE the moment one served row has no build-state parent.
 *      (It is a global consistency contract with no chart parameter, so on a database with no
 *      writer rows at all it holds vacuously — the presence signal is count_sql = 0, asserted below.)
 *   4. The REAL EXPLICIT_CLEAR_OPS['ka_gochara'] statements are executed: exactly the writer's rows
 *      (windows_v2 '2.0' + its build-state, for that chart) disappear; the century asset's g3_*
 *      rows in the same relation, another chart's writer rows, the protected v1 / '3.0' windows,
 *      and the '4.0' ledger / authority rows all survive.
 *
 * SKIPPED unless `E1230_DB_TEST=1` AND `E1230_DATABASE_URL` is set — this DROPs and CREATEs tables
 * named like production's, so it must run against a THROWAWAY database and never the shared one:
 *
 *   createdb e1230_scratch
 *   E1230_DB_TEST=1 E1230_DATABASE_URL=postgres://postgres@127.0.0.1:5599/e1230_scratch \
 *     npx vitest run src/lib/cockpit/__tests__/ka_gochara_registry_revert_1230.db.test.ts
 *
 * Talks to `pg` directly (not `@/lib/db/client`) so it cannot inherit a DATABASE_URL that points at
 * anything real. THIS IS NOT AN APPLY: nothing here, or in migration 1230, runs against production.
 */
import { readFileSync } from 'node:fs'
import path from 'node:path'

import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest'
import { Pool } from 'pg'

import { EXPLICIT_CLEAR_OPS } from '../assetClearSpec'

const DB_URL = process.env.E1230_DATABASE_URL
const ENABLED = process.env.E1230_DB_TEST === '1' && !!DB_URL

const MIGRATION = path.resolve(__dirname, '../../../../migrations/1230_ka_gochara_registry_revert_1091_pin.sql')
const WRITER = path.resolve(__dirname, '../../../../python-sidecar/pipeline/orchestrator/writers/ka_gochara.py')
const MATERIALIZE = path.resolve(__dirname, '../../../../python-sidecar/services/w2g/materialize.py')

function pyConstant(file: string, name: string): string {
  const m = readFileSync(file, 'utf8').match(new RegExp(`^${name}\\s*=\\s*"([A-Za-z0-9_.]+)"`, 'm'))
  if (!m) throw new Error(`no ${name} = "..." constant in ${file}`)
  return m[1]
}

const TABLE = pyConstant(WRITER, 'TABLE')
const BUILD_STATE = pyConstant(WRITER, 'BUILD_STATE_TABLE')
const GEN = pyConstant(MATERIALIZE, 'GENERATION_V2')

const CHART_A = '482012f1-710e-4a25-994a-93821f5871aa'
const CHART_B = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

// What 1091 left behind. The integrity text is a fixture carrying 1091's marker (the migration's
// prior-state guard keys on it); the 6.8 KB pre-1091 contract the migration restores is the REAL one.
const PRIOR_INTEGRITY = `-- ka_gochara integrity contract (WP10 re-pin, plan §6.3). Scoped to generation '4.0' (fixture)\nSELECT true AS integrity_passed`
const PRIOR_COUNT_SQL = "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'"

const DDL = `
DROP TABLE IF EXISTS asset_registry, kala_gochara_cutover_step05_snapshot, ${TABLE}, ${BUILD_STATE},
  gochara_resonance_map, kala_gochara_windows, kala_gochara_contacts, kala_gochara_authority CASCADE;
CREATE TABLE asset_registry (
  asset_id text PRIMARY KEY, target_table text, count_sql text, integrity_check_sql text,
  clear_tables text[], depends_on text[]);
CREATE TABLE ${TABLE} (
  id bigserial PRIMARY KEY, chart_id uuid NOT NULL, event_class text NOT NULL,
  window_start date NOT NULL, window_end date NOT NULL, peak_date date NOT NULL,
  generation text NOT NULL, era_slice_key text, milestone_id text, resolution text);
CREATE TABLE ${BUILD_STATE} (
  chart_id uuid NOT NULL, event_class text NOT NULL, generation text NOT NULL,
  class_fingerprint text, rows_written integer NOT NULL DEFAULT 0, skipped_reason text,
  horizon_start_date date, horizon_end_date date,
  PRIMARY KEY (chart_id, event_class, generation));
CREATE TABLE gochara_resonance_map (chart_id uuid NOT NULL, event_class text NOT NULL);
CREATE TABLE kala_gochara_windows (
  id bigserial PRIMARY KEY, chart_id uuid NOT NULL, event_class text NOT NULL,
  window_start date NOT NULL, window_end date NOT NULL, peak_date date NOT NULL, generation text NOT NULL);
CREATE TABLE kala_gochara_contacts (chart_id uuid NOT NULL, generation text NOT NULL);
CREATE TABLE kala_gochara_authority (chart_id uuid PRIMARY KEY, authoritative_generation text NOT NULL);
`

let pool: Pool

async function q(sql: string, params?: unknown[]) {
  return pool.query(sql, params)
}

async function seedRegistry1091() {
  await q('DELETE FROM asset_registry')
  await q(
    `INSERT INTO asset_registry (asset_id, target_table, count_sql, integrity_check_sql, clear_tables, depends_on)
     VALUES ('ka_gochara', 'kala_gochara_windows', $1, $2,
             ARRAY['kala_gochara_windows','kala_gochara_contacts','kala_gochara_coverage'],
             ARRAY['bg_ephemeris','ga_yoga'])`,
    [PRIOR_COUNT_SQL, PRIOR_INTEGRITY],
  )
}

/** One consistent written chart: `n` rows of `event_class` + the build-state parent that matches. */
async function writeChart(chart: string, eventClass: string, n: number) {
  for (let i = 0; i < n; i++) {
    await q(
      `INSERT INTO ${TABLE} (chart_id, event_class, window_start, window_end, peak_date, generation)
       VALUES ($1, $2, '2026-03-01', '2026-03-31', '2026-03-15', $3)`,
      [chart, eventClass, GEN],
    )
  }
  await q(
    `INSERT INTO ${BUILD_STATE} (chart_id, event_class, generation, class_fingerprint, rows_written,
                                 horizon_start_date, horizon_end_date)
     VALUES ($1, $2, $3, 'fp', $4, '2025-01-01', '2028-12-31')`,
    [chart, eventClass, GEN, n],
  )
  await q('INSERT INTO gochara_resonance_map (chart_id, event_class) VALUES ($1, $2)', [chart, eventClass])
  // the irreplaceable v1 corpus (conjunct (h)): strictly larger than the writer's layer for the chart
  for (let i = 0; i < n + 5; i++) {
    await q(
      `INSERT INTO kala_gochara_windows (chart_id, event_class, window_start, window_end, peak_date, generation)
       VALUES ($1, $2, '2000-01-01', '2000-01-31', '2000-01-15', 'v1')`,
      [chart, eventClass],
    )
  }
}

async function applyMigration() {
  await q(readFileSync(MIGRATION, 'utf8'))
}

async function registry() {
  return (await q(
    `SELECT target_table, count_sql, integrity_check_sql, clear_tables, depends_on
       FROM asset_registry WHERE asset_id = 'ka_gochara'`,
  )).rows[0]
}

describe.skipIf(!ENABLED)('migration 1230 — ka_gochara registry row = the registered writer\'s surface (disposable PG)', () => {
  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL, max: 2 })
    await q(DDL)
  })
  afterAll(async () => {
    await pool?.end()
  })
  beforeEach(async () => {
    await q(`TRUNCATE ${TABLE}, ${BUILD_STATE}, gochara_resonance_map, kala_gochara_windows,
                      kala_gochara_contacts, kala_gochara_authority`)
    await q('DROP TABLE IF EXISTS kala_gochara_cutover_step05_snapshot')
    await seedRegistry1091()
  })

  describe('the migration file itself', () => {
    it('restores target_table / count_sql / integrity contract / clear_tables and leaves depends_on alone', async () => {
      await applyMigration()
      const r = await registry()
      expect(r.target_table).toBe(TABLE)
      expect(r.count_sql).toBe(`SELECT COUNT(*) FROM ${TABLE} WHERE chart_id=$1 AND generation='${GEN}'`)
      expect(r.clear_tables).toBeNull()
      expect(r.integrity_check_sql).toContain('ka_gochara integrity contract (D-CND-03')
      expect(r.integrity_check_sql).not.toContain('WP10 re-pin')
      expect(r.depends_on).toEqual(['bg_ephemeris', 'ga_yoga'])
    })

    it('replay is a no-op', async () => {
      await applyMigration()
      const first = await registry()
      await applyMigration()
      expect(await registry()).toEqual(first)
    })

    it('raises on an unexpected prior state and changes nothing', async () => {
      await q(`UPDATE asset_registry SET count_sql = 'SELECT 1' WHERE asset_id = 'ka_gochara'`)
      await expect(applyMigration()).rejects.toThrow(/1230: unexpected prior state/)
      expect((await registry()).count_sql).toBe('SELECT 1')
    })

    it('raises when there is no ka_gochara row (never guesses)', async () => {
      await q('DELETE FROM asset_registry')
      await expect(applyMigration()).rejects.toThrow(/no ka_gochara row/)
    })

    it('where the pre-1091 snapshot exists it must equal what the migration would write — else it raises', async () => {
      // a snapshot whose count_sql differs from the migration's embedded text
      await q(`CREATE TABLE kala_gochara_cutover_step05_snapshot (
                 asset_id text PRIMARY KEY, count_sql text, clear_tables text, integrity_check_sql text, depends_on text[])`)
      await q(`INSERT INTO kala_gochara_cutover_step05_snapshot VALUES ('ka_gochara', 'SELECT 42', NULL, 'x', NULL)`)
      await expect(applyMigration()).rejects.toThrow(/snapshot does not equal/)
      expect((await registry()).target_table).toBe('kala_gochara_windows')   // untouched
    })

    it('a matching snapshot passes: the migration verifies "restore from the snapshot" rather than trusting it', async () => {
      await applyMigration()                                  // writes the intended values
      const intended = await registry()
      await seedRegistry1091()                                // back to 1091's state
      await q(`CREATE TABLE kala_gochara_cutover_step05_snapshot (
                 asset_id text PRIMARY KEY, count_sql text, clear_tables text, integrity_check_sql text, depends_on text[])`)
      await q(`INSERT INTO kala_gochara_cutover_step05_snapshot VALUES ('ka_gochara', $1, NULL, $2, NULL)`,
        [intended.count_sql, intended.integrity_check_sql])
      await applyMigration()
      expect(await registry()).toEqual(intended)
    })
  })

  describe('the restored row against rows the writer actually writes', () => {
    it('count_sql counts exactly the writer\'s rows (relation + generation read from the writer source)', async () => {
      await applyMigration()
      const { count_sql } = await registry()
      await writeChart(CHART_A, 'marriage', 3)
      await writeChart(CHART_B, 'career_entry', 2)
      // the century asset writes the SAME relation under other generations — not counted
      await q(
        `INSERT INTO ${TABLE} (chart_id, event_class, window_start, window_end, peak_date, generation)
         VALUES ($1, 'marriage', '2026-03-01', '2026-03-31', '2026-03-15', 'g3_utkarsha')`, [CHART_A])
      expect(Number((await q(count_sql, [CHART_A])).rows[0].count)).toBe(3)
      expect(Number((await q(count_sql, [CHART_B])).rows[0].count)).toBe(2)
    })

    it('a chart the writer never wrote reads 0 (the cockpit-truth presence signal)', async () => {
      await applyMigration()
      const { count_sql } = await registry()
      await writeChart(CHART_B, 'career_entry', 2)
      expect(Number((await q(count_sql, [CHART_A])).rows[0].count)).toBe(0)
    })

    it('the restored integrity contract reads TRUE on a consistent written chart and FALSE on a real violation', async () => {
      await applyMigration()
      const { integrity_check_sql } = await registry()
      await writeChart(CHART_A, 'marriage', 3)
      expect((await q(integrity_check_sql)).rows[0].integrity_passed).toBe(true)

      // one served row of a class that has NO build-state parent: conjunct (a) must read false
      await q(
        `INSERT INTO ${TABLE} (chart_id, event_class, window_start, window_end, peak_date, generation)
         VALUES ($1, 'surgery', '2026-03-01', '2026-03-31', '2026-03-15', $2)`, [CHART_A, GEN])
      await q('INSERT INTO gochara_resonance_map (chart_id, event_class) VALUES ($1, $2)', [CHART_A, 'surgery'])
      expect((await q(integrity_check_sql)).rows[0].integrity_passed).toBe(false)
    })

    it('a build-state counter that does not equal the rows actually present reads FALSE (conjunct (b))', async () => {
      await applyMigration()
      const { integrity_check_sql } = await registry()
      await writeChart(CHART_A, 'marriage', 3)
      await q(`UPDATE ${BUILD_STATE} SET rows_written = 99 WHERE chart_id = $1`, [CHART_A])
      expect((await q(integrity_check_sql)).rows[0].integrity_passed).toBe(false)
    })
  })

  describe('the REAL EXPLICIT_CLEAR_OPS[\'ka_gochara\'] against real rows', () => {
    it('removes exactly the writer\'s rows for that chart — nothing else in the gochara family', async () => {
      await writeChart(CHART_A, 'marriage', 3)
      await writeChart(CHART_B, 'career_entry', 2)
      await q(
        `INSERT INTO ${TABLE} (chart_id, event_class, window_start, window_end, peak_date, generation)
         VALUES ($1, 'marriage', '2026-03-01', '2026-03-31', '2026-03-15', 'g3_utkarsha')`, [CHART_A])
      await q(`INSERT INTO kala_gochara_windows (chart_id, event_class, window_start, window_end, peak_date, generation)
               VALUES ($1, 'marriage', '2026-03-01', '2026-03-31', '2026-03-15', '3.0')`, [CHART_A])
      await q(`INSERT INTO kala_gochara_contacts (chart_id, generation) VALUES ($1, '4.0')`, [CHART_A])
      await q(`INSERT INTO kala_gochara_authority (chart_id, authoritative_generation) VALUES ($1, '3.0')`, [CHART_A])

      const before = {
        windows: Number((await q(`SELECT count(*) FROM ${TABLE}`)).rows[0].count),
        protectedWindows: Number((await q(`SELECT count(*) FROM kala_gochara_windows WHERE chart_id = $1`, [CHART_A])).rows[0].count),
      }

      const ops = EXPLICIT_CLEAR_OPS['ka_gochara']!
      for (const op of ops) await q(op.sql, [CHART_A])

      const writerRows = (c: string) => q(`SELECT count(*) FROM ${TABLE} WHERE chart_id = $1 AND generation = $2`, [c, GEN])
      const stateRows = (c: string) => q(`SELECT count(*) FROM ${BUILD_STATE} WHERE chart_id = $1 AND generation = $2`, [c, GEN])
      // gone: chart A's writer rows and its bookkeeping
      expect(Number((await writerRows(CHART_A)).rows[0].count)).toBe(0)
      expect(Number((await stateRows(CHART_A)).rows[0].count)).toBe(0)
      // survive: chart B's writer rows + bookkeeping, the century asset's g3_ row, the protected corpus, the ledger, the authority
      expect(Number((await writerRows(CHART_B)).rows[0].count)).toBe(2)
      expect(Number((await stateRows(CHART_B)).rows[0].count)).toBe(1)
      expect(Number((await q(`SELECT count(*) FROM ${TABLE} WHERE generation = 'g3_utkarsha'`)).rows[0].count)).toBe(1)
      expect(Number((await q(`SELECT count(*) FROM kala_gochara_windows WHERE chart_id = $1`, [CHART_A])).rows[0].count))
        .toBe(before.protectedWindows)
      expect(Number((await q(`SELECT count(*) FROM kala_gochara_contacts WHERE chart_id = $1`, [CHART_A])).rows[0].count)).toBe(1)
      expect(Number((await q(`SELECT count(*) FROM kala_gochara_authority WHERE chart_id = $1`, [CHART_A])).rows[0].count)).toBe(1)
      expect(Number((await q(`SELECT count(*) FROM ${TABLE}`)).rows[0].count)).toBe(before.windows - 3)
    })

    it('after the Clear, count_sql reads 0 for the chart and the writer\'s delta-skip state is gone with it', async () => {
      await applyMigration()
      const { count_sql } = await registry()
      await writeChart(CHART_A, 'marriage', 3)
      for (const op of EXPLICIT_CLEAR_OPS['ka_gochara']!) await q(op.sql, [CHART_A])
      expect(Number((await q(count_sql, [CHART_A])).rows[0].count)).toBe(0)
      // no class_fingerprint left behind: a rebuild cannot take the "unchanged fingerprint — skip" branch
      expect(Number((await q(`SELECT count(*) FROM ${BUILD_STATE} WHERE chart_id = $1`, [CHART_A])).rows[0].count)).toBe(0)
    })
  })
})

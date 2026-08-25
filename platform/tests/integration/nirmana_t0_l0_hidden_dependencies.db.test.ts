// @vitest-environment node
/** Real-Postgres replay tests for migration 599's fail-closed DAG correction. */
import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest'
import { Pool } from 'pg'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const TEST_DB_URL = process.env.NIRMANA_T0_DAG_TEST_DATABASE_URL
const run = TEST_DB_URL ? describe : describe.skip
const MIGRATION_599 = resolve(
  __dirname,
  '../../migrations/599_nirmana_t0_l0_hidden_dependencies.sql',
)

const consumers = [
  'bg_gochara_arcs',
  'bg_kp_sublord_division',
  'bg_parihara_rules',
]
const sources = [
  'bg_ephemeris',
  'bg_nakshatra',
  'bg_doshas',
  'bg_texts',
]

run('migration 599 L0 hidden dependency correction', () => {
  let pool: Pool

  beforeAll(() => {
    const parsed = new URL(TEST_DB_URL!)
    if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
      || parsed.pathname !== '/nirmana_t0_dag_test') {
      throw new Error(
        'NIRMANA_T0_DAG_TEST_DATABASE_URL must point to the exact local '
        + 'nirmana_t0_dag_test database',
      )
    }
    pool = new Pool({ connectionString: TEST_DB_URL })
  })

  beforeEach(async () => {
    await pool.query(`
      DROP TABLE IF EXISTS asset_registry CASCADE;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY,
        catalog_status text NOT NULL,
        is_active boolean NOT NULL,
        depends_on text[] NOT NULL DEFAULT ARRAY[]::text[]
      );
    `)
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query('DROP TABLE IF EXISTS asset_registry CASCADE')
    await pool.end()
  })

  async function insertAssets(assetIds: string[]) {
    for (const assetId of assetIds) {
      await pool.query(
        `INSERT INTO asset_registry (asset_id, catalog_status, is_active)
         VALUES ($1, 'CURRENT', true)`,
        [assetId],
      )
    }
  }

  async function applyMigration() {
    const client = await pool.connect()
    try {
      await client.query(readFileSync(MIGRATION_599, 'utf8'))
    } catch (error) {
      await client.query('ROLLBACK')
      throw error
    } finally {
      client.release()
    }
  }

  it('rejects a missing source authority before mutating any consumer', async () => {
    await insertAssets([...consumers, 'bg_ephemeris', 'bg_nakshatra', 'bg_doshas'])

    await expect(applyMigration()).rejects.toThrow(/bg_texts|source authorit/i)
    const { rows } = await pool.query(
      `SELECT asset_id, depends_on FROM asset_registry
        WHERE asset_id = ANY($1::text[]) ORDER BY asset_id`,
      [consumers],
    )
    expect(rows).toEqual(consumers.slice().sort().map(asset_id => ({ asset_id, depends_on: [] })))
  })

  it('rejects a reverse dependency that would create a cycle and rolls back', async () => {
    await insertAssets([...consumers, ...sources])
    await pool.query(
      `UPDATE asset_registry SET depends_on = ARRAY['bg_gochara_arcs']::text[]
        WHERE asset_id = 'bg_ephemeris'`,
    )

    await expect(applyMigration()).rejects.toThrow(/cycle/i)
    const { rows } = await pool.query(
      `SELECT depends_on FROM asset_registry WHERE asset_id = 'bg_gochara_arcs'`,
    )
    expect(rows[0].depends_on).toEqual([])
  })

  it('rejects a source authority whose nullable status is unknown and rolls back', async () => {
    await insertAssets([...consumers, ...sources])
    await pool.query(
      `ALTER TABLE asset_registry ALTER COLUMN catalog_status DROP NOT NULL;
       UPDATE asset_registry SET catalog_status = NULL WHERE asset_id = 'bg_texts'`,
    )

    await expect(applyMigration()).rejects.toThrow(/bg_texts|source authorit/i)
    const { rows } = await pool.query(
      `SELECT depends_on FROM asset_registry WHERE asset_id = 'bg_parihara_rules'`,
    )
    expect(rows[0].depends_on).toEqual([])
  })

  it('applies the exact edges and accepts an exact retry', async () => {
    await insertAssets([...consumers, ...sources])

    await applyMigration()
    await applyMigration()

    const { rows } = await pool.query(
      `SELECT asset_id, depends_on FROM asset_registry
        WHERE asset_id = ANY($1::text[]) ORDER BY asset_id`,
      [consumers],
    )
    expect(rows).toEqual([
      { asset_id: 'bg_gochara_arcs', depends_on: ['bg_ephemeris'] },
      { asset_id: 'bg_kp_sublord_division', depends_on: ['bg_nakshatra'] },
      { asset_id: 'bg_parihara_rules', depends_on: ['bg_doshas', 'bg_texts'] },
    ])
  })
})

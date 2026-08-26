// @vitest-environment node
/** Real-Postgres guards for migration 601's compendium digest partition. */
import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest'
import { Pool } from 'pg'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const TEST_DB_URL = process.env.NIRMANA_L0_DIGEST_TEST_DATABASE_URL
const run = TEST_DB_URL ? describe : describe.skip
const MIGRATION_601 = resolve(
  __dirname,
  '../../supabase/migrations/601_nirmana_l0_wave1_wave2_output_digest_specs.sql',
)
const assets = [
  'bg_compendium_index',
  'bg_concordance',
  'bg_dasha_systems',
  'bg_doshas',
  'bg_gochara_arcs',
  'bg_kp_sublord_division',
  'bg_rules',
  'bg_text_index',
  'bg_vidhi_floors',
  'bg_yogas',
]

run('migration 601 compendium digest scopes', () => {
  let pool: Pool

  beforeAll(() => {
    const parsed = new URL(TEST_DB_URL!)
    if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
      || parsed.pathname !== '/nirmana_l0_digest_test') {
      throw new Error(
        'NIRMANA_L0_DIGEST_TEST_DATABASE_URL must point to the exact local '
        + 'nirmana_l0_digest_test database',
      )
    }
    pool = new Pool({ connectionString: TEST_DB_URL })
  })

  beforeEach(async () => {
    await pool.query(`
      DROP TABLE IF EXISTS asset_output_digest_specs CASCADE;
      DROP TABLE IF EXISTS asset_registry CASCADE;
      DROP TABLE IF EXISTS brahma_compendium_index CASCADE;
      CREATE TABLE asset_registry (asset_id text PRIMARY KEY);
      CREATE TABLE asset_output_digest_specs (
        asset_id text NOT NULL REFERENCES asset_registry(asset_id),
        spec_sha256 text NOT NULL,
        spec jsonb NOT NULL,
        reviewed_at timestamptz NOT NULL DEFAULT now(),
        retired_at timestamptz,
        PRIMARY KEY (asset_id, spec_sha256)
      );
      CREATE TABLE brahma_compendium_index (
        index_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        text_id text NOT NULL,
        chapter_num integer,
        topic_id text
      );
    `)
    for (const assetId of assets) {
      await pool.query('INSERT INTO asset_registry (asset_id) VALUES ($1)', [assetId])
    }
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`
      DROP TABLE IF EXISTS asset_output_digest_specs CASCADE;
      DROP TABLE IF EXISTS asset_registry CASCADE;
      DROP TABLE IF EXISTS brahma_compendium_index CASCADE;
    `)
    await pool.end()
  })

  async function applyMigration() {
    const client = await pool.connect()
    try {
      await client.query('BEGIN')
      await client.query(readFileSync(MIGRATION_601, 'utf8'))
      await client.query('COMMIT')
    } catch (error) {
      await client.query('ROLLBACK')
      throw error
    } finally {
      client.release()
    }
  }

  it.each([
    { chapter_num: null, topic_id: null, shape: 'both NULL' },
    { chapter_num: 1, topic_id: 'dasha', shape: 'both non-NULL' },
  ])('rejects an existing $shape row before registering any digest spec', async (row) => {
    await pool.query(
      `INSERT INTO brahma_compendium_index (text_id, chapter_num, topic_id)
       VALUES ('bphs', $1, $2)`,
      [row.chapter_num, row.topic_id],
    )

    await expect(applyMigration()).rejects.toThrow(/digest scope|exactly one/i)
    const { rows } = await pool.query('SELECT count(*)::int AS count FROM asset_output_digest_specs')
    expect(rows[0].count).toBe(0)
  })

  it('accepts both valid shapes, applies idempotently, and enforces the XOR afterward', async () => {
    await pool.query(`
      INSERT INTO brahma_compendium_index (text_id, chapter_num, topic_id)
      VALUES ('bphs', 1, NULL), ('bphs', NULL, 'dasha')
    `)

    await applyMigration()
    await applyMigration()

    const { rows } = await pool.query('SELECT count(*)::int AS count FROM asset_output_digest_specs')
    expect(rows[0].count).toBe(10)
    await expect(pool.query(
      `INSERT INTO brahma_compendium_index (text_id, chapter_num, topic_id)
       VALUES ('saravali', NULL, NULL)`,
    )).rejects.toThrow(/digest_scope_xor|check constraint/i)
    await expect(pool.query(
      `INSERT INTO brahma_compendium_index (text_id, chapter_num, topic_id)
       VALUES ('saravali', 2, 'yoga')`,
    )).rejects.toThrow(/digest_scope_xor|check constraint/i)
  })
})

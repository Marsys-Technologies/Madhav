import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/617_nirmana_l0_text_index_integrity_contract.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const TEST_DATABASE_URL = process.env.NIRMANA_L0_TEXT_INDEX_TEST_DATABASE_URL
const PRODUCTION_DIGEST = '19964c1f91e149f4a136632af0f1e3c88b28e213f1bb4e45de98fcf395a94e21'
const CANONICAL_EXPLANATION = '361 distinct topic_tag values is the achieved deterministic-classifier coverage ratified by migrations 196 and 231. Raise this floor only with an evidence-backed classifier or corpus expansion; never fabricate assignments to meet the former aspirational 400.'
const LEGACY_EXPLANATION = 'Distinct topic_tag count from embedded chunks. Floor 400 = topic-vocabulary coverage target; not scaled with chunk count (vocabulary size is independent of corpus depth). Per design §2.2.'

describe('migration 617 — text-index integrity contract', () => {
  it('is runner-owned, fail-closed, and aligned with the registry seed', () => {
    expect(migration).not.toBe('')
    expect(migration).toContain(PRODUCTION_DIGEST)
    expect(migration).toContain('migration 617 refuses unknown bg_text_index registry contract')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
    expect(ASSETS.find(asset => asset.asset_id === 'bg_text_index')).toMatchObject({
      sort_order: 5,
      target_table: 'classical_text_chunks',
      target_floor: 361,
      volume_explanation: CANONICAL_EXPLANATION,
      depends_on: ['bg_texts'],
    })
  })
})

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_text_index_integrity_test') {
    throw new Error(
      'NIRMANA_L0_TEXT_INDEX_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_text_index_integrity_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 617 — real PostgreSQL behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      DROP TABLE IF EXISTS classical_text_chunks,reference_topic_tags,asset_registry CASCADE;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, layer text, sort_order integer, scope text,
        asset_kind text, catalog_status text, is_active boolean, has_writer boolean,
        target_table text, count_sql text, target_floor bigint, depends_on text[],
        natural_key_partition text, data_disposition text, integrity_check_sql text,
        english_description text, volume_explanation text
      );
      CREATE TABLE reference_topic_tags (canonical_id text PRIMARY KEY);
      CREATE TABLE classical_text_chunks (
        chunk_id text PRIMARY KEY, content_en text, embedding text, topic_tag text
      );
      INSERT INTO reference_topic_tags(canonical_id)
      SELECT 'topic_' || lpad(i::text,3,'0') FROM generate_series(1,361) AS i;
      INSERT INTO classical_text_chunks(chunk_id,content_en,embedding,topic_tag)
      SELECT 'chunk_' || lpad(i::text,5,'0'), 'fixture content ' || i, '[0]',
             CASE WHEN i <= 7010
                  THEN 'topic_' || lpad((((i-1) % 361)+1)::text,3,'0')
                  ELSE NULL END
      FROM generate_series(1,10651) AS i;
      INSERT INTO asset_registry
        (asset_id,layer,sort_order,scope,asset_kind,catalog_status,is_active,
         has_writer,target_table,count_sql,target_floor,depends_on,
         natural_key_partition,data_disposition,integrity_check_sql,
         english_description,volume_explanation)
      VALUES
        ('bg_text_index','brahmagyan',5,'global','data','CURRENT',true,true,
         'classical_text_chunks',
         'SELECT count(DISTINCT topic_tag) AS count FROM classical_text_chunks WHERE embedding IS NOT NULL AND topic_tag IS NOT NULL',
         361,ARRAY['bg_texts']::text[],NULL,NULL,NULL,
         'Measurement of retrieval index health — distinct topic tags across embedded + indexed chunks. Retrieval tools point at bg_texts; this asset reports the index coverage metric.',
         '${CANONICAL_EXPLANATION}');
    `)
    return client
  }

  async function migrationForFixture(client: Client): Promise<string> {
    const digest = await client.query<{ digest: string }>(`
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(chunk_id,topic_tag)::text,
        E'\\n' ORDER BY chunk_id COLLATE "C"
      ),''),'UTF8')),'hex') AS digest
      FROM classical_text_chunks
    `)
    return migration.replaceAll(PRODUCTION_DIGEST, digest.rows[0].digest)
  }

  async function detector(client: Client): Promise<boolean> {
    const contract = await client.query<{ integrity_check_sql: string }>(
      `SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_text_index'`,
    )
    const observed = await client.query(contract.rows[0].integrity_check_sql)
    return observed.rowCount === 1 && Object.values(observed.rows[0])[0] === true
  }

  it('installs, replays, and accepts the exact full-partition digest', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)
      const registry = await client.query(
        `SELECT target_floor,volume_explanation,natural_key_partition,
                data_disposition,integrity_check_sql IS NOT NULL AS has_integrity
         FROM asset_registry WHERE asset_id='bg_text_index'`,
      )
      expect(registry.rows[0]).toEqual({
        target_floor: '361',
        volume_explanation: CANONICAL_EXPLANATION,
        natural_key_partition: 'classical_text_chunks.chunk_id; value=topic_tag',
        data_disposition: null,
        has_integrity: true,
      })
    } finally {
      await client.end()
    }
  })

  it('fires on count-preserving tag drift, unknown tags, and accretion', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      const corruptions = [
        `UPDATE classical_text_chunks SET topic_tag='topic_002' WHERE chunk_id='chunk_00001'`,
        `UPDATE classical_text_chunks SET topic_tag='not_in_vocabulary' WHERE chunk_id='chunk_00001'`,
        `INSERT INTO classical_text_chunks VALUES ('rogue','rogue','[0]',NULL)`,
      ]
      await client.query('BEGIN')
      for (const corruption of corruptions) {
        await client.query('SAVEPOINT corruption')
        await client.query(corruption)
        expect(await detector(client)).toBe(false)
        await client.query('ROLLBACK TO SAVEPOINT corruption')
      }
      await client.query('ROLLBACK')
    } finally {
      await client.end()
    }
  })

  it('accepts the exact legacy floor state and rejects unknown registry drift', async () => {
    const client = await connectPrepared()
    try {
      await client.query(
        `UPDATE asset_registry SET target_floor=400,volume_explanation=$1
         WHERE asset_id='bg_text_index'`,
        [LEGACY_EXPLANATION],
      )
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)

      await client.query(`UPDATE asset_registry SET target_floor=1 WHERE asset_id='bg_text_index'`)
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'migration 617 refuses unknown bg_text_index registry contract',
      )
      const observed = await client.query(
        `SELECT target_floor,integrity_check_sql IS NOT NULL AS has_integrity
         FROM asset_registry WHERE asset_id='bg_text_index'`,
      )
      expect(observed.rows[0]).toEqual({ target_floor: '1', has_integrity: true })
    } finally {
      await client.end()
    }
  })
})

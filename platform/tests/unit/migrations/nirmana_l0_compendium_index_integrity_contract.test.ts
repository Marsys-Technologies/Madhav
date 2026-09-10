import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'
import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/623_nirmana_l0_compendium_index_integrity_contract.sql',
)
const migration = fs.readFileSync(migrationPath, 'utf8')
const url = process.env.NIRMANA_L0_COMPENDIUM_TEST_DATABASE_URL
const chapterDigest = '6994a142e5c6d1832cbeba82070ff444495dc83211d57331175505e74f70c2e9'
const topicDigest = '093884a730b1743cf6e04d9b838f7bacd6741ee7111daa6522c655e1fa0d4c19'
const explanation = '9,571 deterministic index rows from the production source corpus: 7,969 per-text chapter projections + 1,602 valid per-text topic projections. Rebuild adds 33 Muhurta Chintamani topic identities and refreshes 68 stale mechanical summaries.'
const partition = 'brahma_compendium_index.(text_id,chapter_num WHERE topic_id IS NULL; text_id,topic_id WHERE chapter_num IS NULL)'

describe('migration 623 — compendium index integrity', () => {
  it('is fail-closed and seed-aligned', () => {
    expect(migration).toContain(chapterDigest)
    expect(migration).toContain(topicDigest)
    expect(migration).toContain(partition)
    expect(migration).toContain('migration 623 refuses unknown bg_compendium_index registry contract')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(ASSETS.find(asset => asset.asset_id === 'bg_compendium_index')).toMatchObject({
      target_floor: 9571,
      volume_explanation: explanation,
    })
  })
})

if (url) {
  const parsed = new URL(url)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_compendium_integrity_test') {
    throw new Error('unsafe compendium test database')
  }
}

describe.skipIf(!url)('migration 623 — real PostgreSQL', () => {
  async function prepare() {
    const client = new Client({ connectionString: url })
    await client.connect()
    await client.query(`
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      DROP TABLE IF EXISTS brahma_compendium_index, asset_registry CASCADE;
      CREATE TABLE asset_registry(
        asset_id text primary key, layer text, sort_order int, scope text,
        asset_kind text, catalog_status text, is_active bool, has_writer bool,
        target_table text, count_sql text, target_floor bigint, depends_on text[],
        natural_key_partition text, data_disposition text, integrity_check_sql text,
        english_description text, volume_explanation text
      );
      CREATE TABLE brahma_compendium_index(
        index_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        text_id text NOT NULL, chapter_num int, chapter_title_en text,
        chapter_title_sa text, topic_id text, verse_start int, verse_end int,
        chunk_ids bigint[], summary_text text, significance text,
        classical_significance_score numeric,
        CONSTRAINT brahma_compendium_index_digest_scope_xor
          CHECK ((chapter_num IS NULL) <> (topic_id IS NULL))
      );
      INSERT INTO brahma_compendium_index(
        text_id, chapter_num, verse_start, verse_end, chunk_ids, summary_text,
        significance, classical_significance_score
      )
      SELECT 'text_' || lpad((i % 15)::text, 2, '0'), i, 1, 2, ARRAY[]::bigint[],
             'chapter ' || i, 'chapter significance ' || i, 0.02
      FROM generate_series(1, 7969) AS i;
      INSERT INTO brahma_compendium_index(
        text_id, topic_id, verse_start, verse_end, chunk_ids, summary_text,
        significance, classical_significance_score
      )
      SELECT 'text_' || lpad((i % 15)::text, 2, '0'), 'topic_' || lpad(i::text, 4, '0'),
             1, 2, ARRAY[]::bigint[], 'topic ' || i, 'topic significance ' || i, 0.02
      FROM generate_series(1, 1602) AS i;
      INSERT INTO asset_registry VALUES(
        'bg_compendium_index', 'brahmagyan', 12, 'global', 'data', 'CURRENT',
        true, true, 'brahma_compendium_index',
        'SELECT count(*) FROM brahma_compendium_index', 9571,
        ARRAY['bg_texts','bg_reference'], NULL, NULL, NULL,
        'Cross-reference index over the 15 classical texts — chapter summaries, topic-coverage map, significance scores',
        $explanation$${explanation}$explanation$
      );
    `)
    return client
  }

  async function fixtureMigration(client: Client) {
    const chapter = await client.query(`
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(text_id,chapter_num,chapter_title_en,chapter_title_sa,
          topic_id,verse_start,verse_end,chunk_ids,summary_text,significance,
          classical_significance_score)::text,E'\\n'
        ORDER BY text_id COLLATE "C",chapter_num),''),'UTF8')),'hex') AS digest
      FROM brahma_compendium_index WHERE topic_id IS NULL
    `)
    const topic = await client.query(`
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(text_id,chapter_num,chapter_title_en,chapter_title_sa,
          topic_id,verse_start,verse_end,chunk_ids,summary_text,significance,
          classical_significance_score)::text,E'\\n'
        ORDER BY text_id COLLATE "C",topic_id COLLATE "C"),''),'UTF8')),'hex') AS digest
      FROM brahma_compendium_index WHERE chapter_num IS NULL
    `)
    return migration
      .replaceAll(chapterDigest, chapter.rows[0].digest)
      .replaceAll(topicDigest, topic.rows[0].digest)
  }

  async function detector(client: Client) {
    const registry = await client.query(
      "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_compendium_index'",
    )
    const result = await client.query(registry.rows[0].integrity_check_sql)
    return Object.values(result.rows[0])[0] === true
  }

  it('installs idempotently and catches semantic drift', async () => {
    const client = await prepare()
    try {
      const sql = await fixtureMigration(client)
      await client.query(sql)
      await client.query(sql)
      expect(await detector(client)).toBe(true)
      await client.query("UPDATE brahma_compendium_index SET summary_text='drift' WHERE index_id=1")
      expect(await detector(client)).toBe(false)
    } finally {
      await client.end()
    }
  })

  it('accepts the live legacy contract and rejects unknown registry drift', async () => {
    const client = await prepare()
    try {
      await client.query(`
        UPDATE asset_registry
        SET target_floor=9538,
            volume_explanation='9,538 index entries = honest count from actual build. Per design §3.12.'
      `)
      const sql = await fixtureMigration(client)
      await client.query(sql)
      expect(await detector(client)).toBe(true)
      await client.query('UPDATE asset_registry SET target_floor=1')
      await expect(client.query(sql)).rejects.toThrow('migration 623 refuses unknown')
    } finally {
      await client.end()
    }
  })
})

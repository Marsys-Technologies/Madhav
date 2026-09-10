import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/619_nirmana_l0_concordance_integrity_contract.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const TEST_DATABASE_URL = process.env.NIRMANA_L0_CONCORDANCE_TEST_DATABASE_URL
const PRODUCTION_DIGEST = '9e2837388c783be0dc57361e52d8de344b2b041f9bb5e9eb39fa4b67412f5893'
const CANONICAL_EXPLANATION = '721 deterministic topic×school concordance rows from the frozen 10,651-chunk topic index and canonical 3,002-rule projection. The convergent rebuild repairs stale pointers and includes lord_1st_in_11th, whose tagged chunks existed in production while its historical concordance row was absent.'
const LEGACY_EXPLANATION = '800 = topic×school concordance rows. Cross-product metric: cardinality is topic_count × school_count, not chunk-proportional. Chunk-pointer index per (topic, school); synthesis at L1+ query-time.'
const CANONICAL_DEPENDENCIES = ['bg_texts', 'bg_text_index', 'bg_reference', 'bg_rules']

describe('migration 619 — concordance integrity contract', () => {
  it('is runner-owned, fail-closed, and aligned with the convergent seed contract', () => {
    expect(migration).not.toBe('')
    expect(migration).toContain(PRODUCTION_DIGEST)
    expect(migration).toContain('migration 619 refuses unknown bg_concordance registry contract')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
    expect(ASSETS.find(asset => asset.asset_id === 'bg_concordance')).toMatchObject({
      sort_order: 8,
      target_table: 'classical_attributions',
      target_floor: 721,
      volume_explanation: CANONICAL_EXPLANATION,
      depends_on: CANONICAL_DEPENDENCIES,
    })
  })
})

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_concordance_integrity_test') {
    throw new Error(
      'NIRMANA_L0_CONCORDANCE_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_concordance_integrity_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 619 — real PostgreSQL behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      DROP TABLE IF EXISTS classical_attributions,sutravali_rules,
        classical_text_chunks,reference_topic_tags,asset_registry CASCADE;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, layer text, sort_order integer, scope text,
        asset_kind text, catalog_status text, is_active boolean, has_writer boolean,
        target_table text, count_sql text, target_floor bigint, depends_on text[],
        natural_key_partition text, data_disposition text, integrity_check_sql text,
        english_description text, volume_explanation text
      );
      CREATE TABLE reference_topic_tags (
        canonical_id text PRIMARY KEY,name text NOT NULL,category text NOT NULL
      );
      CREATE TABLE classical_text_chunks (
        chunk_id text PRIMARY KEY,text_id text NOT NULL,topic_tag text
      );
      CREATE TABLE sutravali_rules (rule_id uuid PRIMARY KEY,text_id text NOT NULL);
      CREATE TABLE classical_attributions (
        topic_id text NOT NULL,topic_canonical_name text NOT NULL,
        topic_category text NOT NULL,school text NOT NULL,
        source_text_ids text[] NOT NULL,source_chunk_ids bigint[] NOT NULL,
        rule_ids uuid[] NOT NULL,match_method text NOT NULL,
        match_confidence numeric(4,3) NOT NULL,
        PRIMARY KEY(topic_id,school)
      );
      INSERT INTO reference_topic_tags
      SELECT 'topic_' || lpad(i::text,3,'0'),'Topic ' || i,'fixture_category'
      FROM generate_series(1,361) AS i;
      INSERT INTO sutravali_rules VALUES
        ('00000000-0000-0000-0000-000000000001','text_parashari'),
        ('00000000-0000-0000-0000-000000000002','text_phaladeepika'),
        ('00000000-0000-0000-0000-000000000003','text_jaimini'),
        ('00000000-0000-0000-0000-000000000004','text_nadi');
      INSERT INTO classical_attributions
      SELECT topic.canonical_id,topic.name,topic.category,school.name,
             ARRAY[school.text_id]::text[],ARRAY[]::bigint[],
             ARRAY[school.rule_id]::uuid[],'topic_tag',0.200
      FROM reference_topic_tags AS topic
      CROSS JOIN (VALUES
        ('parashari','text_parashari','00000000-0000-0000-0000-000000000001'::uuid,361),
        ('phaladeepika','text_phaladeepika','00000000-0000-0000-0000-000000000002'::uuid,180),
        ('jaimini','text_jaimini','00000000-0000-0000-0000-000000000003'::uuid,100),
        ('nadi','text_nadi','00000000-0000-0000-0000-000000000004'::uuid,80)
      ) AS school(name,text_id,rule_id,topic_limit)
      WHERE substring(topic.canonical_id FROM '[0-9]+$')::integer <= school.topic_limit;
      INSERT INTO classical_text_chunks
      SELECT 'chunk_' || row_number() OVER (ORDER BY topic_id,school),
             source_text_ids[1],topic_id
      FROM classical_attributions;
      INSERT INTO asset_registry
        (asset_id,layer,sort_order,scope,asset_kind,catalog_status,is_active,
         has_writer,target_table,count_sql,target_floor,depends_on,
         natural_key_partition,data_disposition,integrity_check_sql,
         english_description,volume_explanation)
      VALUES
        ('bg_concordance','brahmagyan',8,'global','data','CURRENT',true,true,
         'classical_attributions','SELECT count(*) FROM classical_attributions',721,
         ARRAY['bg_texts','bg_text_index','bg_reference','bg_rules']::text[],
         NULL,NULL,NULL,
         'Cross-school chunk-pointer index per (topic, school) — chunk refs for L1+ synthesis at query-time',
         '${CANONICAL_EXPLANATION}');
    `)
    return client
  }

  async function migrationForFixture(client: Client): Promise<string> {
    const digest = await client.query<{ digest: string }>(`
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(topic_id,topic_canonical_name,topic_category,school,
          source_text_ids,source_chunk_ids,rule_ids,match_method,match_confidence)::text,
        E'\\n' ORDER BY topic_id COLLATE "C",school COLLATE "C"
      ),''),'UTF8')),'hex') AS digest
      FROM classical_attributions
    `)
    return migration.replaceAll(PRODUCTION_DIGEST, digest.rows[0].digest)
  }

  async function detector(client: Client): Promise<boolean> {
    const contract = await client.query<{ integrity_check_sql: string }>(
      `SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_concordance'`,
    )
    const observed = await client.query(contract.rows[0].integrity_check_sql)
    return observed.rowCount === 1 && Object.values(observed.rows[0])[0] === true
  }

  it('installs, replays, and accepts the exact canonical projection', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)
      const registry = await client.query(
        `SELECT target_floor,volume_explanation,depends_on,natural_key_partition,
                data_disposition,integrity_check_sql IS NOT NULL AS has_integrity
         FROM asset_registry WHERE asset_id='bg_concordance'`,
      )
      expect(registry.rows[0]).toEqual({
        target_floor: '721',
        volume_explanation: CANONICAL_EXPLANATION,
        depends_on: CANONICAL_DEPENDENCIES,
        natural_key_partition: 'classical_attributions.(topic_id,school)',
        data_disposition: null,
        has_integrity: true,
      })
    } finally {
      await client.end()
    }
  })

  it('fires on semantic drift, broken source pointers, and accretion', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      const corruptions = [
        `UPDATE classical_attributions SET topic_canonical_name='drift'
         WHERE topic_id='topic_001' AND school='parashari'`,
        `UPDATE classical_attributions SET source_text_ids=ARRAY['missing_text']
         WHERE topic_id='topic_001' AND school='parashari'`,
        `UPDATE classical_attributions
         SET rule_ids=ARRAY['ffffffff-ffff-ffff-ffff-ffffffffffff'::uuid]
         WHERE topic_id='topic_001' AND school='parashari'`,
        `INSERT INTO classical_attributions
         SELECT 'rogue','rogue','rogue','rogue',ARRAY['text_parashari'],
                ARRAY[]::bigint[],ARRAY['00000000-0000-0000-0000-000000000001'::uuid],
                'topic_tag',0.200`,
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

  it('normalizes the live legacy state and rejects unknown registry drift', async () => {
    const client = await connectPrepared()
    try {
      await client.query(
        `UPDATE asset_registry
         SET target_floor=800,volume_explanation=$1,depends_on=ARRAY['bg_rules']::text[]
         WHERE asset_id='bg_concordance'`,
        [LEGACY_EXPLANATION],
      )
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)

      await client.query(`UPDATE asset_registry SET target_floor=1 WHERE asset_id='bg_concordance'`)
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'migration 619 refuses unknown bg_concordance registry contract',
      )
      const observed = await client.query(
        `SELECT target_floor,integrity_check_sql IS NOT NULL AS has_integrity
         FROM asset_registry WHERE asset_id='bg_concordance'`,
      )
      expect(observed.rows[0]).toEqual({ target_floor: '1', has_integrity: true })
    } finally {
      await client.end()
    }
  })
})

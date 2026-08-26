import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/618_nirmana_l0_rules_integrity_contract.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const TEST_DATABASE_URL = process.env.NIRMANA_L0_RULES_TEST_DATABASE_URL
const PRODUCTION_DIGEST = '87b697041c73359e12daf8258cfdd6e85a38eb5c63fa39865e42f5b46e610dbd'
const CANONICAL_EXPLANATION = '3,002 deterministic regex-extracted rules from the frozen 10,651-chunk corpus after canonicalizing Pattern 27 planet order and duplicate suppression across Python hash seeds.'
const LEGACY_EXPLANATION = '2,912 rules = honest count from actual build against 10,651-chunk corpus.'

describe('migration 618 — rules integrity contract', () => {
  it('is runner-owned, fail-closed, and aligned with the deterministic seed contract', () => {
    expect(migration).not.toBe('')
    expect(migration).toContain(PRODUCTION_DIGEST)
    expect(migration).toContain('migration 618 refuses unknown bg_rules registry contract')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
    expect(ASSETS.find(asset => asset.asset_id === 'bg_rules')).toMatchObject({
      sort_order: 6,
      target_table: 'sutravali_rules',
      target_floor: 3002,
      volume_explanation: CANONICAL_EXPLANATION,
      depends_on: ['bg_texts'],
    })
  })
})

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_rules_integrity_test') {
    throw new Error(
      'NIRMANA_L0_RULES_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_rules_integrity_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 618 — real PostgreSQL behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      DROP TABLE IF EXISTS sutravali_rules,brahma_dasha_systems,
        brahma_yoga_catalog,classical_text_chunks,asset_registry CASCADE;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, layer text, sort_order integer, scope text,
        asset_kind text, catalog_status text, is_active boolean, has_writer boolean,
        target_table text, count_sql text, target_floor bigint, depends_on text[],
        natural_key_partition text, data_disposition text, integrity_check_sql text,
        english_description text, volume_explanation text
      );
      CREATE TABLE classical_text_chunks (chunk_id text PRIMARY KEY,text_id text NOT NULL);
      CREATE TABLE brahma_yoga_catalog (canonical_id text PRIMARY KEY);
      CREATE TABLE brahma_dasha_systems (canonical_id text PRIMARY KEY);
      CREATE TABLE sutravali_rules (
        rule_id uuid PRIMARY KEY,text_id text NOT NULL,verse_ref text NOT NULL,
        antecedent_jsonb jsonb NOT NULL,predicate_jsonb jsonb NOT NULL,
        prediction_jsonb jsonb NOT NULL,confidence numeric(4,3) NOT NULL,
        extracted_by text NOT NULL,extraction_pass_log jsonb NOT NULL,
        quality_score numeric(4,3),yoga_canonical_id text,
        dasha_system_id text,transit_marker boolean
      );
      INSERT INTO classical_text_chunks VALUES ('chunk-1','fixture_text');
      INSERT INTO brahma_yoga_catalog VALUES ('fixture_yoga');
      INSERT INTO sutravali_rules
        (rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
         prediction_jsonb,confidence,extracted_by,extraction_pass_log,
         quality_score,yoga_canonical_id,dasha_system_id,transit_marker)
      SELECT md5(i::text)::uuid,'fixture_text','V' || i,
             jsonb_build_array(jsonb_build_object('planet','sun','house',(i % 12)+1)),
             jsonb_build_object('type','fixture'),
             jsonb_build_object('result','fixture ' || i),
             0.800,'python_regex_v2',
             jsonb_build_array(jsonb_build_object('pattern','fixture','chunk_id','chunk-1')),
             0.800,CASE WHEN i <= 17 THEN 'fixture_yoga' ELSE NULL END,
             NULL,i <= 25
      FROM generate_series(1,3002) AS i;
      INSERT INTO asset_registry
        (asset_id,layer,sort_order,scope,asset_kind,catalog_status,is_active,
         has_writer,target_table,count_sql,target_floor,depends_on,
         natural_key_partition,data_disposition,integrity_check_sql,
         english_description,volume_explanation)
      VALUES
        ('bg_rules','brahmagyan',6,'global','data','CURRENT',true,true,
         'sutravali_rules','SELECT count(*) FROM sutravali_rules',3002,
         ARRAY['bg_texts']::text[],NULL,NULL,NULL,
         'Classical rules extracted from text chunks via Python regex patterns — verse-traceable',
         '${CANONICAL_EXPLANATION}');
    `)
    return client
  }

  async function migrationForFixture(client: Client): Promise<string> {
    const digest = await client.query<{ digest: string }>(`
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
          prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
          yoga_canonical_id,dasha_system_id,transit_marker)::text,
        E'\\n' ORDER BY rule_id::text COLLATE "C"
      ),''),'UTF8')),'hex') AS digest
      FROM sutravali_rules
    `)
    return migration.replaceAll(PRODUCTION_DIGEST, digest.rows[0].digest)
  }

  async function detector(client: Client): Promise<boolean> {
    const contract = await client.query<{ integrity_check_sql: string }>(
      `SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_rules'`,
    )
    const observed = await client.query(contract.rows[0].integrity_check_sql)
    return observed.rowCount === 1 && Object.values(observed.rows[0])[0] === true
  }

  it('installs, replays, and accepts the exact deterministic rule corpus', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)
      const registry = await client.query(
        `SELECT target_floor,volume_explanation,natural_key_partition,
                data_disposition,integrity_check_sql IS NOT NULL AS has_integrity
         FROM asset_registry WHERE asset_id='bg_rules'`,
      )
      expect(registry.rows[0]).toEqual({
        target_floor: '3002',
        volume_explanation: CANONICAL_EXPLANATION,
        natural_key_partition: 'sutravali_rules.rule_id',
        data_disposition: null,
        has_integrity: true,
      })
    } finally {
      await client.end()
    }
  })

  it('fires on semantic drift, broken references, and accretion', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      const corruptions = [
        `UPDATE sutravali_rules SET prediction_jsonb='{"result":"drift"}' WHERE verse_ref='V1'`,
        `UPDATE sutravali_rules SET extracted_by='manual' WHERE verse_ref='V1'`,
        `UPDATE sutravali_rules SET yoga_canonical_id='missing' WHERE verse_ref='V1'`,
        `INSERT INTO sutravali_rules SELECT gen_random_uuid(),text_id,verse_ref,
           antecedent_jsonb,predicate_jsonb,prediction_jsonb,confidence,extracted_by,
           extraction_pass_log,quality_score,yoga_canonical_id,dasha_system_id,transit_marker
         FROM sutravali_rules LIMIT 1`,
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

  it('normalizes the legacy floor and rejects unknown registry drift', async () => {
    const client = await connectPrepared()
    try {
      await client.query(
        `UPDATE asset_registry SET target_floor=2912,volume_explanation=$1
         WHERE asset_id='bg_rules'`,
        [LEGACY_EXPLANATION],
      )
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)

      await client.query(`UPDATE asset_registry SET target_floor=1 WHERE asset_id='bg_rules'`)
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'migration 618 refuses unknown bg_rules registry contract',
      )
      const observed = await client.query(
        `SELECT target_floor,integrity_check_sql IS NOT NULL AS has_integrity
         FROM asset_registry WHERE asset_id='bg_rules'`,
      )
      expect(observed.rows[0]).toEqual({ target_floor: '1', has_integrity: true })
    } finally {
      await client.end()
    }
  })
})

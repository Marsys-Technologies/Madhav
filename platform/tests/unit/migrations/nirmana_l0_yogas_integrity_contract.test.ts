import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/620_nirmana_l0_yogas_integrity_contract.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const TEST_DATABASE_URL = process.env.NIRMANA_L0_YOGAS_TEST_DATABASE_URL
const CATALOG_DIGEST = '4d4cd60f7cffe728f2d01c3146f9bf54279e5c747973ab60b2e69b7921023fa8'
const ONTOLOGY_DIGEST = '7af1d138c492bd16bbca93b06faab6b3ff781d87aa91f8573fce6378f968fdab'
const REFERENCE_DIGEST = '1c79af1127b8e624e12c95afecf09e73f23546fe87272f5dff8146ed30d6f564'
const CANONICAL_EXPLANATION = '699 owned rows = 233 deterministic yoga definitions × 3 reconciled projections (catalog + yoga ontology partition + reference_yogas). Source definition count is 144 inline core + 4 detector-registry identities + 85 corpus-extracted rows.'
const CANONICAL_COUNT_SQL = `SELECT
  (SELECT count(*) FROM brahma_yoga_catalog) +
  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'yoga') +
  (SELECT count(*) FROM reference_yogas) AS count`
const CURRENT_EXPLANATION = '784 owned rows = 233 deterministic yoga definitions × 3 reconciled projections plus 85 typed UUID source-chunk links for the corpus-extracted definitions.'
const CURRENT_COUNT_SQL = `SELECT
  (SELECT count(*) FROM brahma_yoga_catalog) +
  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'yoga') +
  (SELECT count(*) FROM reference_yogas) +
  (SELECT count(*) FROM brahma_yoga_source_chunks) AS count`
const LEGACY_EXPLANATION = 'Catalog of named yoga patterns from BPHS / Saravali / Phaladeepika / Jaimini per design §3.9. Floor 250 (contingent on 8,193-chunk extraction yield; corrects seed value of 200).'

describe('migration 620 — yoga integrity contract', () => {
  it('is runner-owned, fail-closed, and aligned with the convergent seed contract', () => {
    expect(migration).not.toBe('')
    expect(migration).toContain(CATALOG_DIGEST)
    expect(migration).toContain(ONTOLOGY_DIGEST)
    expect(migration).toContain(REFERENCE_DIGEST)
    expect(migration).toContain('migration 620 refuses unknown bg_yogas registry contract')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
    expect(ASSETS.find(asset => asset.asset_id === 'bg_yogas')).toMatchObject({
      sort_order: 9,
      target_table: 'brahma_yoga_catalog',
      target_floor: 784,
      count_sql: CURRENT_COUNT_SQL,
      volume_explanation: CURRENT_EXPLANATION,
      depends_on: ['bg_texts', 'bg_ontology'],
    })
  })
})

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_yogas_integrity_test') {
    throw new Error(
      'NIRMANA_L0_YOGAS_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_yogas_integrity_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 620 — real PostgreSQL behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      DROP TABLE IF EXISTS reference_yogas,brahma_ontology,
        brahma_yoga_catalog,asset_registry CASCADE;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY,layer text,sort_order integer,scope text,
        asset_kind text,catalog_status text,is_active boolean,has_writer boolean,
        target_table text,count_sql text,target_floor bigint,depends_on text[],
        natural_key_partition text,data_disposition text,integrity_check_sql text,
        english_description text,volume_explanation text
      );
      CREATE TABLE brahma_yoga_catalog (
        canonical_id text PRIMARY KEY,name_sa text NOT NULL,name_en text NOT NULL,
        category text NOT NULL,formation_rule_jsonb jsonb NOT NULL,
        formation_text text NOT NULL,significations_jsonb jsonb NOT NULL,
        significations_text text NOT NULL,cancellation_conditions jsonb,
        classical_citations jsonb,source_chunk_ids bigint[],school text NOT NULL,
        rare boolean NOT NULL,computed_strength_formula text,bhanga_rules_jsonb jsonb,
        partial_formation_threshold numeric,strength_formula_ref text,result_class text
      );
      CREATE TABLE brahma_ontology (
        entity_class text NOT NULL,canonical_id text NOT NULL,
        canonical_name_en text NOT NULL,canonical_name_sa text,synonyms text[] NOT NULL,
        description text,source_citation text NOT NULL,
        PRIMARY KEY(entity_class,canonical_id)
      );
      CREATE TABLE reference_yogas (
        canonical_id text PRIMARY KEY,name_en text NOT NULL,category text NOT NULL
      );
      INSERT INTO brahma_yoga_catalog
      SELECT 'yoga_' || lpad(i::text,3,'0'),'Yoga ' || i,'Yoga ' || i,'other',
             jsonb_build_object('requires',i),'Formation ' || i,
             jsonb_build_object('gives',i),'Signification ' || i,'{}'::jsonb,
             jsonb_build_array(jsonb_build_object('text_id','fixture')),
             ARRAY[]::bigint[],'parashari',false,NULL,NULL,NULL,NULL,NULL
      FROM generate_series(1,229) AS i;
      INSERT INTO brahma_yoga_catalog VALUES
        ('dhana_yoga_house_lords','Dhana','Dhana','dhana','{}','Dhana','{}','Dhana','{}','[]','{}','parashari',false,NULL,NULL,NULL,NULL,NULL),
        ('raja_yoga_kendra_trikona','Raja','Raja','raja','{}','Raja','{}','Raja','{}','[]','{}','parashari',false,NULL,NULL,NULL,NULL,NULL),
        ('sarasvati_yoga','Sarasvati','Sarasvati','other','{}','Sarasvati','{}','Sarasvati','{}','[]','{}','parashari',false,NULL,NULL,NULL,NULL,NULL),
        ('vipareeta_raja_yoga','Vipareeta','Vipareeta','raja','{}','Vipareeta','{}','Vipareeta','{}','[]','{}','parashari',false,NULL,NULL,NULL,NULL,NULL);
      INSERT INTO brahma_ontology
      SELECT 'yoga',canonical_id,name_en,name_sa,ARRAY[name_en],
             left(significations_text,150),'fixture' FROM brahma_yoga_catalog;
      INSERT INTO reference_yogas
      SELECT canonical_id,name_en,category FROM brahma_yoga_catalog;
      INSERT INTO asset_registry
        (asset_id,layer,sort_order,scope,asset_kind,catalog_status,is_active,
         has_writer,target_table,count_sql,target_floor,depends_on,
         natural_key_partition,data_disposition,integrity_check_sql,
         english_description,volume_explanation)
      VALUES
        ('bg_yogas','brahmagyan',9,'global','data','CURRENT',true,true,
         'brahma_yoga_catalog',$count$${CANONICAL_COUNT_SQL}$count$,699,
         ARRAY['bg_ontology']::text[],NULL,NULL,NULL,
         'Classical yoga definitions — formation rules, significations, classical citations',
         '${CANONICAL_EXPLANATION}');
    `)
    return client
  }

  async function migrationForFixture(client: Client): Promise<string> {
    const catalog = await client.query<{ digest: string }>(`
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,
          formation_text,significations_jsonb,significations_text,
          cancellation_conditions,classical_citations,source_chunk_ids,school,rare,
          computed_strength_formula,bhanga_rules_jsonb,partial_formation_threshold,
          strength_formula_ref,result_class)::text,
        E'\\n' ORDER BY canonical_id COLLATE "C"
      ),''),'UTF8')),'hex') AS digest FROM brahma_yoga_catalog
    `)
    const ontology = await client.query<{ digest: string }>(`
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(entity_class,canonical_id,canonical_name_en,
          canonical_name_sa,synonyms,description,source_citation)::text,
        E'\\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"
      ),''),'UTF8')),'hex') AS digest FROM brahma_ontology WHERE entity_class='yoga'
    `)
    const reference = await client.query<{ digest: string }>(`
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(canonical_id,name_en,category)::text,
        E'\\n' ORDER BY canonical_id COLLATE "C"
      ),''),'UTF8')),'hex') AS digest FROM reference_yogas
    `)
    return migration
      .replaceAll(CATALOG_DIGEST, catalog.rows[0].digest)
      .replaceAll(ONTOLOGY_DIGEST, ontology.rows[0].digest)
      .replaceAll(REFERENCE_DIGEST, reference.rows[0].digest)
  }

  async function detector(client: Client): Promise<boolean> {
    const contract = await client.query<{ integrity_check_sql: string }>(
      `SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_yogas'`,
    )
    const observed = await client.query(contract.rows[0].integrity_check_sql)
    return observed.rowCount === 1 && Object.values(observed.rows[0])[0] === true
  }

  it('installs, replays, and accepts the exact three-projection corpus', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)
      const registry = await client.query(
        `SELECT target_floor,natural_key_partition,data_disposition,
                integrity_check_sql IS NOT NULL AS has_integrity
         FROM asset_registry WHERE asset_id='bg_yogas'`,
      )
      expect(registry.rows[0]).toEqual({
        target_floor: '699',
        natural_key_partition: 'brahma_yoga_catalog.canonical_id; brahma_ontology.(entity_class=yoga,canonical_id); reference_yogas.canonical_id',
        data_disposition: null,
        has_integrity: true,
      })
    } finally {
      await client.end()
    }
  })

  it('fires on projection drift, missing detector identity, and accretion', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      const corruptions = [
        `UPDATE brahma_yoga_catalog SET formation_text='drift' WHERE canonical_id='yoga_001'`,
        `DELETE FROM brahma_ontology WHERE canonical_id='sarasvati_yoga'`,
        `UPDATE reference_yogas SET category='drift' WHERE canonical_id='yoga_001'`,
        `INSERT INTO reference_yogas VALUES ('rogue','rogue','rogue')`,
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

  it('normalizes the live legacy floor and rejects unknown registry drift', async () => {
    const client = await connectPrepared()
    try {
      await client.query(
        `UPDATE asset_registry SET target_floor=250,volume_explanation=$1
         WHERE asset_id='bg_yogas'`,
        [LEGACY_EXPLANATION],
      )
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)

      await client.query(`UPDATE asset_registry SET target_floor=1 WHERE asset_id='bg_yogas'`)
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'migration 620 refuses unknown bg_yogas registry contract',
      )
    } finally {
      await client.end()
    }
  })
})

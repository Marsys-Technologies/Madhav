import { createHash } from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/630_nirmana_l0_wave1_correctness_contract.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''

const OLD_YOGA_SPEC = '8a8b0f591ae397fc52198d1753e7858906dd3f30e2bef4e6cbdd33950dc57469'
const NEW_YOGA_SPEC = '6d5ecdfe2f6b7e094d48c9d4863e783018f4a3ffb2121a0b69006ad5cb01ae7c'
const TEST_DATABASE_URL = process.env.NIRMANA_L0_WAVE1_TEST_DATABASE_URL
const LEGACY_INTEGRITY = 'SELECT true'
const LEGACY_INTEGRITY_DIGEST = createHash('sha256').update(LEGACY_INTEGRITY).digest('hex')
const YOGA_COUNT_SQL = migration.match(
  /yoga_count_sql constant text := \$count\$(.*?)\$count\$/s,
)?.[1]
const VIDHI_COUNT_SQL = migration.match(
  /vidhi_count_sql constant text := \$count\$(.*?)\$count\$/s,
)?.[1]
const REGISTRY_IDS = [
  'bg_text_index',
  'bg_rules',
  'bg_yogas',
  'bg_kp_sublord_division',
  'bg_gochara_arcs',
  'bg_vidhi_floors',
  'bg_gochara_citation_resolution',
]
const OLD_YOGA_SPEC_JSON = migration.match(
  /old_spec constant jsonb :=\s*'([^']+)'::jsonb;/,
)?.[1]

describe('migration 630 — Nirmana L0 wave-1 correctness contract', () => {
  it('is runner-owned, fail-closed, and installs typed yoga provenance', () => {
    expect(migration).not.toBe('')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
    expect(migration).toContain('CREATE TABLE IF NOT EXISTS brahma_yoga_source_chunks')
    expect(migration).toContain('source_chunk_id UUID NOT NULL')
    expect(migration).toContain('REFERENCES classical_text_chunks(id)')
    expect(migration).toContain('migration 630 refuses unknown')
  })

  it('corrects only evidence-backed dependency edges in the bootstrap registry', () => {
    expect(ASSETS.find(asset => asset.asset_id === 'bg_text_index')?.depends_on)
      .toEqual(['bg_texts', 'bg_reference'])
    expect(ASSETS.find(asset => asset.asset_id === 'bg_rules')?.depends_on)
      .toEqual(['bg_texts', 'bg_yogas', 'bg_dasha_systems'])
    expect(ASSETS.find(asset => asset.asset_id === 'bg_yogas')?.depends_on)
      .toEqual(['bg_texts', 'bg_ontology'])
  })

  it('retires but retains the legacy yoga digest spec and binds the typed links', () => {
    expect(migration).toContain(OLD_YOGA_SPEC)
    expect(migration).toContain(NEW_YOGA_SPEC)
    expect(migration).toContain('brahma_yoga_source_chunks')
    expect(migration).toContain('failed to retain exact retired yoga predecessor')
  })

  it('marks the same-chapter Vakra guess unresolved and installs exact postflights', () => {
    expect(migration).toContain("'CORPUS_GAP:bphs_ch27_vakra'")
    expect(migration).toContain("'VAKRA_RETROGRADE_BPHS_27'")
    expect(migration).toContain("'unresolved'")
    expect(migration).toContain('4e65ee68012bd20dd2b328a5c31da24fbd1670a6129a0b8aab0eaf5c539a7721')
    expect(migration).toContain('count(*) = 249')
    expect(migration).toContain('count(*) = 34553')
    expect(migration).toContain('count(*) = 14 FROM vidhi_intent_floors')
    expect(migration).toContain('count(*) = 409 FROM vidhi_floor_items')
  })
})

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_wave1_test') {
    throw new Error(
      'NIRMANA_L0_WAVE1_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_wave1_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 630 — real PostgreSQL behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      DROP TABLE IF EXISTS brahma_yoga_source_chunks,asset_output_digest_specs,
        bg_gochara_citation_resolution,classical_text_chunks,
        brahma_yoga_catalog,brahma_ontology,reference_yogas,
        bg_kp_sublord_division,bg_gochara_arcs,vidhi_floor_items,
        vidhi_intent_floors,vidhi_primitives,asset_registry CASCADE;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY,layer text,sort_order integer,scope text,
        asset_kind text,catalog_status text,is_active boolean,has_writer boolean,
        target_table text,count_sql text,target_floor bigint,depends_on text[],
        natural_key_partition text,data_disposition text,integrity_check_sql text,
        english_description text,volume_explanation text
      );
      CREATE TABLE brahma_yoga_catalog (canonical_id text PRIMARY KEY);
      CREATE TABLE classical_text_chunks (id uuid PRIMARY KEY,chunk_id text UNIQUE);
      CREATE TABLE brahma_ontology (
        entity_class text NOT NULL,canonical_id text NOT NULL,
        canonical_name_en text,canonical_name_sa text,synonyms text,
        description text,source_citation text,
        PRIMARY KEY(entity_class,canonical_id)
      );
      CREATE TABLE reference_yogas (
        canonical_id text PRIMARY KEY,name_en text,category text
      );
      CREATE TABLE bg_kp_sublord_division (
        table_version text,division_index integer,start_longitude_deg numeric,
        end_longitude_deg numeric,source_citation text
      );
      CREATE TABLE bg_gochara_arcs (
        substrate_version text,body text,arc_fingerprint text,engine_version text,
        ayanamsha_id text,arc_index integer
      );
      CREATE TABLE vidhi_intent_floors (intent text PRIMARY KEY);
      CREATE TABLE vidhi_primitives (primitive_id text PRIMARY KEY);
      CREATE TABLE vidhi_floor_items (
        intent text,item_order integer,primitive_id text
      );
      CREATE TABLE bg_gochara_citation_resolution (
        citation_string text NOT NULL,chunk_id text NOT NULL,text_id text,
        verse_ref text,status text NOT NULL,source_citation text,
        constant_name text,note text,
        created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY(citation_string,chunk_id)
      );
      CREATE TABLE asset_output_digest_specs (
        asset_id text NOT NULL,spec_sha256 text NOT NULL,spec jsonb NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),retired_at timestamptz,
        PRIMARY KEY(asset_id,spec_sha256)
      );
      CREATE UNIQUE INDEX asset_output_digest_specs_one_current
        ON asset_output_digest_specs(asset_id) WHERE retired_at IS NULL;
    `)
    await client.query(
      `INSERT INTO bg_gochara_citation_resolution
         (citation_string,chunk_id,text_id,verse_ref,status,source_citation,
          constant_name,note)
       VALUES(
         $1,'bphs_ch27_v001','bphs','CH27:V1-V3','resolved',
         'BPHS Ch.27 v1-3 (chunk bphs_ch27_v001) — the cheshta bala / vakra (retrograde) doctrine that VAKRA_RETROGRADE_BPHS_27 cites is in BPHS Ch.27.',
         'VAKRA_RETROGRADE_BPHS_27',
         'citations.py constant VAKRA_RETROGRADE_BPHS_27. Chunk bphs_ch27_v001 confirmed in l0_texts.py SEED_CHUNKS (chapter 27, verse_start 1). Honest disclosure: the SEED_CHUNKS content for this chunk covers karakas (the chapter''s primary topic); the cheshta-bala/vakra doctrine is in the same chapter per l0_reference.py citation ''BPHS Ch.27''.'
       )`,
      ['BPHS Ch.27 — Vakra (retrogression; cheshta bala)'],
    )
    await client.query(`
      INSERT INTO asset_registry
        (asset_id,has_writer,target_table,count_sql,target_floor,depends_on,
         integrity_check_sql)
      VALUES
        ('bg_text_index',true,'classical_text_chunks','SELECT count(*)',361,
          ARRAY['bg_texts']::text[],$1),
        ('bg_rules',true,'sutravali_rules','SELECT count(*)',3002,
          ARRAY['bg_texts']::text[],$1),
        ('bg_yogas',true,'brahma_yoga_catalog',$2,699,
          ARRAY['bg_ontology']::text[],$1),
        ('bg_kp_sublord_division',true,'bg_kp_sublord_division','SELECT count(*)',249,
          ARRAY[]::text[],NULL),
        ('bg_gochara_arcs',true,'bg_gochara_arcs','SELECT count(*)',34553,
          ARRAY[]::text[],NULL),
        ('bg_vidhi_floors',true,'vidhi_floor_items',
          '(SELECT COUNT(*) FROM vidhi_floor_items)',11,ARRAY[]::text[],NULL),
        ('bg_gochara_citation_resolution',false,
          'bg_gochara_citation_resolution','SELECT count(*)',4,
          ARRAY[]::text[],NULL)
    `, [LEGACY_INTEGRITY, `SELECT
  (SELECT count(*) FROM brahma_yoga_catalog) +
  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'yoga') +
  (SELECT count(*) FROM reference_yogas) AS count`])
    expect(OLD_YOGA_SPEC_JSON).toBeDefined()
    await client.query(
      `INSERT INTO asset_output_digest_specs(asset_id,spec_sha256,spec)
       VALUES('bg_yogas',$1,$2::jsonb)`,
      [OLD_YOGA_SPEC, OLD_YOGA_SPEC_JSON],
    )
    return client
  }

  async function registryMetadataDigests(client: Client): Promise<Record<string, string>> {
    const result = await client.query<{ asset_id: string, metadata_sha: string }>(`
      SELECT asset_id,encode(sha256(convert_to(jsonb_build_array(
        layer,sort_order,scope,asset_kind,catalog_status,is_active,has_writer,
        target_table,count_sql,target_floor,depends_on,english_description,
        volume_explanation,natural_key_partition,data_disposition
      )::text,'UTF8')),'hex') AS metadata_sha
      FROM asset_registry WHERE asset_id=ANY($1::text[])
    `, [REGISTRY_IDS])
    return Object.fromEntries(result.rows.map(row => [row.asset_id, row.metadata_sha]))
  }

  async function migrationForFixture(client: Client): Promise<string> {
    expect(YOGA_COUNT_SQL).toBeDefined()
    expect(VIDHI_COUNT_SQL).toBeDefined()
    const before = await registryMetadataDigests(client)
    await client.query('BEGIN')
    try {
      await client.query(`
        UPDATE asset_registry SET
          depends_on=CASE asset_id
            WHEN 'bg_text_index' THEN ARRAY['bg_texts','bg_reference']::text[]
            WHEN 'bg_rules' THEN ARRAY['bg_texts','bg_yogas','bg_dasha_systems']::text[]
            WHEN 'bg_yogas' THEN ARRAY['bg_texts','bg_ontology']::text[]
            ELSE depends_on
          END,
          target_floor=CASE asset_id
            WHEN 'bg_yogas' THEN 784 WHEN 'bg_vidhi_floors' THEN 423
            WHEN 'bg_gochara_citation_resolution' THEN 14 ELSE target_floor
          END,
          count_sql=CASE asset_id
            WHEN 'bg_yogas' THEN $2
            WHEN 'bg_vidhi_floors' THEN $3
            ELSE count_sql
          END,
          volume_explanation=CASE asset_id
            WHEN 'bg_yogas' THEN '784 owned rows = 233 deterministic yoga definitions × 3 reconciled projections plus 85 typed UUID source-chunk links for the corpus-extracted definitions.'
            WHEN 'bg_vidhi_floors' THEN '423 owned rows = 14 current intent floors + 409 ordered floor items from the canonical Vidhi registry.'
            WHEN 'bg_gochara_citation_resolution' THEN '14 governed citation mappings: 3 exact resolved chunk links and 11 honest corpus gaps. Same-chapter proximity is never treated as source evidence.'
            ELSE volume_explanation
          END,
          natural_key_partition=CASE asset_id
            WHEN 'bg_yogas' THEN 'brahma_yoga_catalog.canonical_id; brahma_ontology.(entity_class=yoga,canonical_id); reference_yogas.canonical_id; brahma_yoga_source_chunks.(canonical_id,source_chunk_id)'
            WHEN 'bg_kp_sublord_division' THEN 'bg_kp_sublord_division.(table_version,division_index)'
            WHEN 'bg_gochara_arcs' THEN 'bg_gochara_arcs.(substrate_version,body,arc_index)'
            WHEN 'bg_vidhi_floors' THEN 'vidhi_intent_floors.intent; vidhi_floor_items.(intent,item_order)'
            WHEN 'bg_gochara_citation_resolution' THEN 'bg_gochara_citation_resolution.(citation_string,chunk_id)'
            ELSE natural_key_partition
          END,
          data_disposition=CASE WHEN asset_id='bg_gochara_citation_resolution'
            THEN 'RETAINED_AS_CAPITAL' ELSE data_disposition END
        WHERE asset_id=ANY($1::text[])
      `, [REGISTRY_IDS, YOGA_COUNT_SQL, VIDHI_COUNT_SQL])
      const after = await registryMetadataDigests(client)
      let fixtureMigration = migration
        .replace(/metadata_sha IN \(\s*'30dc390e0f00f34958df69d63cd8d9c0192bc3dd023d508cea228ce40150ac94',\s*'b85b9e75f8a0a55bdeb5d3159ebb62d1efdca505f51af61b1e6eb2087e2c43f2'/, `metadata_sha IN ('${before.bg_text_index}','${before.bg_text_index}'`)
        .replace(/metadata_sha IN \(\s*'449fb76fb56a4301a53dfc896baef9a3d5ecf2b434a127aceb3fedcf80f1fc8a',\s*'638a4b891bc41c30f87c40c11f2126d7f8e39e2d3d8c4ced8b1afa470a416dd0'/, `metadata_sha IN ('${before.bg_rules}','${before.bg_rules}'`)
        .replace(/metadata_sha='6f6d27090e3cd6ec4f21a19c7fe7f22c72124c63b2b2ee351234c027fe524f5e'/, `metadata_sha='${before.bg_yogas}'`)
        .replace(/metadata_sha='f4adc4d444334af48a831ed9dbdceec3adab5ba27013c6c53db3a2f61771410a'/, `metadata_sha='${before.bg_yogas}'`)
        .replace(/metadata_sha='942be622a1dfb96b2128554374492b3da3fd376f918dc928e9ae06c62343d82d'/, `metadata_sha='${before.bg_kp_sublord_division}'`)
        .replace(/metadata_sha='4e4524584a3860747707aef35a9ee5bc02693fd1512211ebcbd47c6ccb2fef50'/, `metadata_sha='${before.bg_kp_sublord_division}'`)
        .replace(/metadata_sha='f42756b2a497cf804628d94fa1a96b02846917e5ac083efb70081ff157ada5c6'/, `metadata_sha='${before.bg_gochara_arcs}'`)
        .replace(/metadata_sha='6bc7ed2f54cd008566c98987edcdf337f57dcccd443ee88a8367b10906dc07fc'/, `metadata_sha='${before.bg_gochara_arcs}'`)
        .replace(/metadata_sha='667012f44b7a3f32cb15b341c428ae603d196f037324b2d4df7ea7271bba8c40'/, `metadata_sha='${before.bg_vidhi_floors}'`)
        .replace(/metadata_sha='78ca618f910577c6a5da76cbf2efb8bcabf3841369c2caab1623e084a4a00706'/, `metadata_sha='${before.bg_vidhi_floors}'`)
        .replace(/metadata_sha='a36cf55e4e879f31b7874c7367975b589b35cc74d8b63afac152f82e08fd2ad9'/, `metadata_sha='${before.bg_gochara_citation_resolution}'`)
        .replace(/metadata_sha='9189699f8f72f40c9bff35e030be10beea517fa3dbe86f51ae08ab24ad1f7139'/, `metadata_sha='${before.bg_gochara_citation_resolution}'`)
      for (const assetId of REGISTRY_IDS) {
        const expected = after[assetId]
        fixtureMigration = fixtureMigration.replace(
          new RegExp(`\\(\\s*'${assetId}',\\s*'[0-9a-f]{64}',`),
          `('${assetId}','${expected}',`,
        )
        expect(fixtureMigration).toContain(`('${assetId}','${expected}',`)
      }
      return fixtureMigration
      .replaceAll('93446a84cceda0809a1e58c2d703329a26f9141242d17dc5a3046ab1184a1ed0',
        LEGACY_INTEGRITY_DIGEST)
      .replaceAll('bbc85c5f1ee64688e2fd932c5ff6563ae829cf7e9e03c43e42609d85b916de6f',
        LEGACY_INTEGRITY_DIGEST)
      .replaceAll('49c26b8c2514a2bcc47fcdf882732bdbaf4a017e11bfbac1da62d49789834554',
        LEGACY_INTEGRITY_DIGEST)
    } finally {
      await client.query('ROLLBACK')
    }
  }

  it('installs and replays the exact registry, citation, and digest transition', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      await client.query(await migrationForFixture(client))
      const registry = await client.query(
        `SELECT asset_id,target_floor,depends_on,integrity_check_sql IS NOT NULL AS exact
         FROM asset_registry
         WHERE asset_id IN ('bg_text_index','bg_rules','bg_yogas','bg_vidhi_floors')
         ORDER BY asset_id`,
      )
      expect(registry.rows).toEqual([
        { asset_id: 'bg_rules', target_floor: '3002', depends_on: ['bg_texts', 'bg_yogas', 'bg_dasha_systems'], exact: true },
        { asset_id: 'bg_text_index', target_floor: '361', depends_on: ['bg_texts', 'bg_reference'], exact: true },
        { asset_id: 'bg_vidhi_floors', target_floor: '423', depends_on: [], exact: true },
        { asset_id: 'bg_yogas', target_floor: '784', depends_on: ['bg_texts', 'bg_ontology'], exact: true },
      ])
      const vakra = await client.query(
        `SELECT chunk_id,status FROM bg_gochara_citation_resolution
         WHERE constant_name='VAKRA_RETROGRADE_BPHS_27'`,
      )
      expect(vakra.rows).toEqual([{
        chunk_id: 'CORPUS_GAP:bphs_ch27_vakra',
        status: 'unresolved',
      }])
      const specs = await client.query(
        `SELECT spec_sha256,retired_at IS NULL AS current
         FROM asset_output_digest_specs WHERE asset_id='bg_yogas'
         ORDER BY spec_sha256`,
      )
      expect(specs.rows).toEqual([
        { spec_sha256: NEW_YOGA_SPEC, current: true },
        { spec_sha256: OLD_YOGA_SPEC, current: false },
      ])
    } finally {
      await client.end()
    }
  })

  it('fails closed and rolls back when a dependency contract is unknown', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(
        `UPDATE asset_registry SET depends_on=ARRAY['rogue']::text[]
         WHERE asset_id='bg_rules'`,
      )
      await client.query('BEGIN')
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'migration 630 refuses unknown bg_rules registry contract',
      )
      await client.query('ROLLBACK')
      const typedTable = await client.query(
        `SELECT to_regclass('brahma_yoga_source_chunks') AS relation`,
      )
      expect(typedTable.rows[0].relation).toBeNull()
      const vakra = await client.query(
        `SELECT chunk_id,status FROM bg_gochara_citation_resolution
         WHERE constant_name='VAKRA_RETROGRADE_BPHS_27'`,
      )
      expect(vakra.rows).toEqual([{ chunk_id: 'bphs_ch27_v001', status: 'resolved' }])
    } finally {
      await client.end()
    }
  })
})

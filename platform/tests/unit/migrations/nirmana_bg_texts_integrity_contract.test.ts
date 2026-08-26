import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'
import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/610_nirmana_bg_texts_integrity_contract.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const TEST_DATABASE_URL = process.env.NIRMANA_BG_TEXTS_INTEGRITY_TEST_DATABASE_URL

const OLD_COUNT_SQL = `SELECT
  (SELECT count(*) FROM classical_texts) +
  (SELECT count(*) FROM classical_text_chunks) AS count`
const OLD_EXPLANATION = '10,651 chunks across 13 classical texts (deterministic rebuild from GCS PDFs, pinned text-multilingual-embedding-002). Complete corpus; honest count from actual build.'
const TRANSLATION_PROVENANCE = 'machine_translation_supervised_2026-08; commissioned per SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE CONFIRMATIONS; source edition per translator field'
const CANONICAL_INPUTS = {
  corpus_texts: 15,
  source_objects: 20,
  chunk_count: 10651,
  embedding_model: 'text-multilingual-embedding-002',
  source_manifest: 'platform/python-sidecar/brahmagyan/bg_texts_source_manifest_v1.json',
  source_manifest_sha256: 'bfcf536e16fb219d5f6faf1f01b6bd6a3a89830a96c997afb71d46eff32d1c36',
  corpus_identity_sha256: '44b067b48544af32df4b2f4d8b13cc7c269aa029e236a0af3d2e8d7347d7d30e',
  corpus_content_sha256: 'b81fb9c098847ecafc2072fd49d706f1a6bb811ab3fcc169d8753010ea6e17e2',
}
const CANONICAL_EXPLANATION = '10,651 preserved chunks across 15 canonical texts. Twenty immutable GCS source-object generations are pinned by bg_texts_source_manifest_v1.json (SHA-256 bfcf536e16fb219d5f6faf1f01b6bd6a3a89830a96c997afb71d46eff32d1c36); metadata-only repair is the accepted disposition and destructive full rebuild is quarantined until staged per-text replacement exists.'
const AUDITED_IDENTITY_SHA256 = '44b067b48544af32df4b2f4d8b13cc7c269aa029e236a0af3d2e8d7347d7d30e'
const AUDITED_CONTENT_SHA256 = 'b81fb9c098847ecafc2072fd49d706f1a6bb811ab3fcc169d8753010ea6e17e2'

describe('migration 610 — bg_texts integrity contract', () => {
  it('is runner-owned and pins the source-manifest identity', () => {
    const texts = ASSETS.find(asset => asset.asset_id === 'bg_texts')
    expect(texts?.count_sql).toBe('SELECT count(*) FROM classical_text_chunks')
    expect(texts?.target_floor).toBe(10651)
    expect(texts?.expected_volume_inputs).toMatchObject({
      corpus_texts: 15,
      source_objects: 20,
      chunk_count: 10651,
      source_manifest_sha256: 'bfcf536e16fb219d5f6faf1f01b6bd6a3a89830a96c997afb71d46eff32d1c36',
      corpus_identity_sha256: AUDITED_IDENTITY_SHA256,
      corpus_content_sha256: AUDITED_CONTENT_SHA256,
    })
    expect(migration).toContain('bfcf536e16fb219d5f6faf1f01b6bd6a3a89830a96c997afb71d46eff32d1c36')
    expect(migration).toContain('migration 610 refuses unknown bg_texts registry contract')
    expect(migration).toContain('nirmana_bg_texts_integrity_baselines')
    expect(migration).toContain(AUDITED_IDENTITY_SHA256)
    expect(migration).toContain(AUDITED_CONTENT_SHA256)
    expect(migration).toContain('migration 610 refuses unaudited bg_texts corpus baseline')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
  })
})

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_bg_texts_integrity_test') {
    throw new Error(
      'NIRMANA_BG_TEXTS_INTEGRITY_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_bg_texts_integrity_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 610 — real Postgres behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      DROP TABLE IF EXISTS nirmana_bg_texts_integrity_baselines,
        classical_text_chunks, classical_texts, asset_registry CASCADE;
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, layer text, sort_order integer, scope text,
        asset_kind text, catalog_status text, is_active boolean, has_writer boolean,
        target_table text, count_sql text, target_floor bigint,
        expected_volume_inputs jsonb, volume_explanation text, depends_on text[],
        natural_key_partition text, data_disposition text, integrity_check_sql text
      );
      CREATE TABLE classical_texts (
        text_id text PRIMARY KEY, title_en text, title_sa text, author text,
        school text, tradition text, tier smallint, license text,
        license_cleared boolean, total_chapters smallint, total_verses integer,
        source_edition text
      );
      CREATE TABLE classical_text_chunks (
        text_id text, chunk_id text PRIMARY KEY, verse_ref text, chapter integer,
        verse_start integer, verse_end integer, content_sa text, content_en text,
        source_citation text, translator text, tradition_school text,
        embedding text, content_sha256 text, translation_status text,
        translation_provenance text, low_confidence_flag boolean DEFAULT false
      );
    `)
    await client.query(`
      INSERT INTO asset_registry VALUES (
        'bg_texts','brahmagyan',3,'global','data','CURRENT',true,true,
        'classical_text_chunks',$1,10651,
        '{"corpus_texts":13,"embedding_model":"text-multilingual-embedding-002","actual_build_date":"2026-06-09"}',
        $2,ARRAY[]::text[],NULL,NULL,NULL
      )
    `, [OLD_COUNT_SQL, OLD_EXPLANATION])

    execFileSync('python3', ['-c', [
      'import os, psycopg',
      'from brahmagyan.l0_texts import TEXTS',
      'conn=psycopg.connect(os.environ["NIRMANA_BG_TEXTS_INTEGRITY_TEST_DATABASE_URL"])',
      'cur=conn.cursor()',
      'sql="INSERT INTO classical_texts VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"',
      '[cur.execute(sql,(t["text_id"],t["title_en"],t.get("title_sa"),t.get("author"),t["school"],t["tradition"],t["tier"],t["license"],t.get("license_cleared",True),t.get("total_chapters"),t.get("total_verses"),t.get("source_edition"))) for t in TEXTS]',
      'conn.commit(); conn.close()',
    ].join('; ')], {
      cwd: path.resolve(process.cwd(), 'python-sidecar'),
      env: { ...process.env, NIRMANA_BG_TEXTS_INTEGRITY_TEST_DATABASE_URL: TEST_DATABASE_URL! },
      stdio: 'pipe',
    })
    await client.query(`
      INSERT INTO classical_texts VALUES (
        'jaimini_sutram','Legacy Jaimini Sutram',NULL,'Legacy','legacy',
        'legacy',3,'legacy',true,NULL,NULL,'legacy preserved row'
      )
    `)

    await client.query(`
      WITH counts(text_id, n) AS (VALUES
        ('bhrigu_nandi_nadi',608),('bphs',1459),('bphs_jaimini',264),
        ('brihat_jataka',607),('brihat_samhita',1171),('hora_sara',460),
        ('jataka_parijata',704),('muhurta_chintamani',274),
        ('nadi_navamsa_patel',1850),('phaladeepika',564),('saravali',471),
        ('sarvartha_chintamani',342),('tajaka_neelakanthi',290),
        ('uttara_kalamrita',289),('yavana_jataka',1298)
      ), rows AS (
        SELECT text_id, n, generate_series(1,n) AS i FROM counts
      ), content AS (
        SELECT *, 'source content ' || text_id || ' ' || i AS body FROM rows
      )
      INSERT INTO classical_text_chunks
        (text_id,chunk_id,verse_ref,chapter,verse_start,verse_end,content_sa,
         content_en,source_citation,translator,tradition_school,embedding,
         content_sha256,translation_status,translation_provenance,low_confidence_flag)
      SELECT text_id, text_id || '_pg' || lpad(i::text,4,'0') || '_c01',
             'PG' || i || ':C1', i, 1, 1, NULL, body, '[HIGH] fixture',
             'fixture edition','vedic:fixture','[0]',
             encode(sha256(convert_to(text_id || '::' || body,'UTF8')),'hex'),
             NULL,NULL,false
      FROM content;
    `)
    await client.query(`
      WITH translated AS (
        SELECT chunk_id,row_number() OVER (ORDER BY chunk_id) AS rn
        FROM classical_text_chunks
        WHERE text_id='muhurta_chintamani'
        ORDER BY chunk_id LIMIT 88
      )
      UPDATE classical_text_chunks chunk
      SET content_en='supervised translation ' || translated.rn,
          translation_status='machine_translated_supervised',
          translation_provenance=$1,
          low_confidence_flag=(translated.rn <= 78)
      FROM translated WHERE chunk.chunk_id=translated.chunk_id;
    `, [TRANSLATION_PROVENANCE])
    return client
  }

  async function detector(client: Client): Promise<boolean> {
    const contract = await client.query<{ integrity_check_sql: string }>(
      `SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_texts'`,
    )
    const result = await client.query(contract.rows[0].integrity_check_sql)
    return result.rowCount === 1 && Object.values(result.rows[0])[0] === true
  }

  async function migrationWithFixtureBaseline(client: Client): Promise<string> {
    const digests = await client.query<{
      identity_sha256: string
      content_sha256: string
    }>(`
      SELECT
        encode(sha256(convert_to(COALESCE(string_agg(
          jsonb_build_array(text_id,chunk_id,verse_ref,chapter,verse_start,verse_end)::text,
          E'\\n' ORDER BY text_id COLLATE "C", chunk_id COLLATE "C"
        ),''),'UTF8')),'hex') AS identity_sha256,
        encode(sha256(convert_to(COALESCE(string_agg(
          jsonb_build_array(text_id,chunk_id,content_sa,content_en,source_citation,
            translator,tradition_school,content_sha256,md5(embedding::text),
            translation_status,translation_provenance,low_confidence_flag)::text,
          E'\\n' ORDER BY text_id COLLATE "C", chunk_id COLLATE "C"
        ),''),'UTF8')),'hex') AS content_sha256
      FROM classical_text_chunks
    `)
    return migration
      .replace(
        `audited_identity_sha256 constant text :=\n    '${AUDITED_IDENTITY_SHA256}'`,
        `audited_identity_sha256 constant text :=\n    '${digests.rows[0].identity_sha256}'`,
      )
      .replace(
        `audited_content_sha256 constant text :=\n    '${AUDITED_CONTENT_SHA256}'`,
        `audited_content_sha256 constant text :=\n    '${digests.rows[0].content_sha256}'`,
      )
  }

  it('installs, replays, and accepts exact source metadata plus the preserved chunk corpus', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationWithFixtureBaseline(client)
      await client.query(fixtureMigration)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)
      const baseline = await client.query(`
        SELECT length(identity_sha256) AS identity_length,
               length(content_sha256) AS content_length, row_count
        FROM nirmana_bg_texts_integrity_baselines
        WHERE contract_revision='bg-texts-integrity-v1'
      `)
      expect(baseline.rows).toEqual([{
        identity_length: 64, content_length: 64, row_count: '10651',
      }])
    } finally {
      await client.end()
    }
  })

  it('fires on metadata drift, count-preserving key/content corruption, and translation drift', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationWithFixtureBaseline(client)
      await client.query(fixtureMigration)
      const corruptions = [
        "UPDATE classical_texts SET tradition='drift' WHERE text_id='bphs'",
        "UPDATE classical_text_chunks SET chunk_id='bogus_chunk' WHERE chunk_id=(SELECT min(chunk_id) FROM classical_text_chunks)",
        "UPDATE classical_text_chunks SET chunk_id=text_id || '_pg9999_c01' WHERE chunk_id=(SELECT min(chunk_id) FROM classical_text_chunks)",
        "UPDATE classical_text_chunks SET content_en='corrupt' WHERE chunk_id=(SELECT min(chunk_id) FROM classical_text_chunks WHERE text_id='bphs')",
        "UPDATE classical_text_chunks SET content_en='corrupt supervised translation' WHERE chunk_id=(SELECT min(chunk_id) FROM classical_text_chunks WHERE translation_status='machine_translated_supervised')",
        "UPDATE classical_text_chunks SET content_sha256=NULL WHERE chunk_id=(SELECT min(chunk_id) FROM classical_text_chunks WHERE translation_status='machine_translated_supervised')",
        "UPDATE classical_text_chunks SET translation_provenance='drift' WHERE translation_status='machine_translated_supervised'",
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

  it('rejects registry drift atomically without installing a detector', async () => {
    const client = await connectPrepared()
    try {
      await client.query(`UPDATE asset_registry SET target_floor=1 WHERE asset_id='bg_texts'`)
      await expect(client.query(migration)).rejects.toThrow(
        'migration 610 refuses unknown bg_texts registry contract',
      )
      const row = await client.query(
        `SELECT integrity_check_sql,count_sql FROM asset_registry WHERE asset_id='bg_texts'`,
      )
      expect(row.rows).toEqual([{ integrity_check_sql: null, count_sql: OLD_COUNT_SQL }])
      const baselineTable = await client.query(`
        SELECT to_regclass('nirmana_bg_texts_integrity_baselines') AS relation
      `)
      expect(baselineTable.rows).toEqual([{ relation: null }])
    } finally {
      await client.end()
    }
  })

  it('accepts the exact canonical seed state before installing runtime fields', async () => {
    const client = await connectPrepared()
    try {
      await client.query(`
        UPDATE asset_registry
        SET count_sql='SELECT count(*) FROM classical_text_chunks',
            expected_volume_inputs=$1::jsonb,
            volume_explanation=$2
        WHERE asset_id='bg_texts'
      `, [JSON.stringify(CANONICAL_INPUTS), CANONICAL_EXPLANATION])
      const fixtureMigration = await migrationWithFixtureBaseline(client)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)
    } finally {
      await client.end()
    }
  })

  it('rejects a structurally valid but unaudited corpus before first baseline', async () => {
    const client = await connectPrepared()
    try {
      await expect(client.query(migration)).rejects.toThrow(
        'migration 610 refuses unaudited bg_texts corpus baseline',
      )
      await client.query(`
        UPDATE classical_text_chunks
        SET content_en='tampered before baseline'
        WHERE chunk_id=(
          SELECT min(chunk_id) FROM classical_text_chunks
          WHERE translation_status='machine_translated_supervised'
        )
      `)
      await expect(client.query(migration)).rejects.toThrow(
        'migration 610 refuses unaudited bg_texts corpus baseline',
      )
      const baselineTable = await client.query(`
        SELECT to_regclass('nirmana_bg_texts_integrity_baselines') AS relation
      `)
      expect(baselineTable.rows).toEqual([{ relation: null }])
    } finally {
      await client.end()
    }
  })
})

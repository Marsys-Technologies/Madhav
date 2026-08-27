import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'supabase/migrations/631_nirmana_l0_gochara_citation_chunk_repair.sql'),
  'utf8',
)

describe('migration 631 — absent Graha Drishti corpus disposition', () => {
  it('preserves the immutable corpus and fails closed to two explicit gaps', () => {
    expect(migration).not.toMatch(/INSERT\s+INTO\s+classical_text_chunks/i)
    expect(migration).not.toMatch(/UPDATE\s+classical_text_chunks/i)
    expect(migration).not.toMatch(/DELETE\s+FROM\s+classical_text_chunks/i)
    expect(migration).toContain("migration 631 refuses to alter a corpus that already contains bphs_ch26_v001")
    expect(migration).toContain("'CORPUS_GAP:bphs_ch26_graha_drishti'")
    expect(migration).toContain("'CORPUS_GAP:bphs_ch26_graha_drishti_rasi'")
    expect(migration).toContain("status = 'unresolved'")
    expect(migration).toContain("migration 631 refuses unknown Graha Drishti citation state")
  })

  it('pins the revised exact 14-row contract instead of weakening it', () => {
    expect(migration).toContain("count(*) FILTER (WHERE status='resolved') = 1")
    expect(migration).toContain("count(*) FILTER (WHERE status='unresolved') = 13")
    expect(migration).toContain('f87cfce86ed03e45c166977d4ded62a0a530b6ea8844c4e22f6d5340b9b961be')
    expect(migration).toContain('6ea8c824cd9e51b258d58eea7814491372027d7356c207f62d18eb76477f5b3b')
    expect(migration).toContain("migration 631 citation-integrity contract postflight failed")
    expect(migration).toContain('EXECUTE citation_check INTO integrity_ok')
    expect(migration).toContain("migration 631 citation-integrity detector postflight failed")
    expect(migration).toContain("integrity_check_sql=citation_check")
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
  })
})

const TEST_DATABASE_URL = process.env.NIRMANA_L0_GOCHARA_CITATION_TEST_DATABASE_URL
const OLD_CONTRACT_HASH = '6ea8c824cd9e51b258d58eea7814491372027d7356c207f62d18eb76477f5b3b'
const PRODUCTION_FINAL_DIGEST = 'f87cfce86ed03e45c166977d4ded62a0a530b6ea8844c4e22f6d5340b9b961be'
const FINAL_EXPLANATION = '14 governed citation mappings: 1 exact resolved chunk link and 13 honest corpus gaps. Same-chapter proximity is never treated as source evidence.'

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_gochara_citation_test') {
    throw new Error(
      'NIRMANA_L0_GOCHARA_CITATION_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_gochara_citation_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 631 — real PostgreSQL behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      CREATE TEMP TABLE classical_text_chunks (chunk_id text PRIMARY KEY);
      CREATE TEMP TABLE bg_gochara_citation_resolution (
        citation_string text NOT NULL, chunk_id text NOT NULL, text_id text NOT NULL,
        verse_ref text NOT NULL, status text NOT NULL, source_citation text NOT NULL,
        constant_name text PRIMARY KEY, note text NOT NULL
      );
      CREATE TEMP TABLE asset_registry (
        asset_id text PRIMARY KEY, target_floor bigint NOT NULL,
        natural_key_partition text NOT NULL, data_disposition text NOT NULL,
        integrity_check_sql text NOT NULL, volume_explanation text NOT NULL
      );
      INSERT INTO classical_text_chunks(chunk_id)
      SELECT 'fixture_chunk_' || lpad(i::text, 5, '0') FROM generate_series(1, 10650) AS i;
      INSERT INTO classical_text_chunks(chunk_id) VALUES ('resolved_chunk');
      INSERT INTO bg_gochara_citation_resolution
        (citation_string,chunk_id,text_id,verse_ref,status,source_citation,constant_name,note)
      VALUES
        ('graha_drishti','bphs_ch26_v001','bphs','CH26:V1-V4','resolved','legacy','GRAHA_DRISHTI_BPHS_26','legacy'),
        ('graha_drishti_rasi','bphs_ch26_v001','bphs','CH26:V1-V4','resolved','legacy','GRAHA_DRISHTI_RASI_BPHS_26','legacy'),
        ('resolved_fixture','resolved_chunk','fixture','V1','resolved','fixture','RESOLVED_FIXTURE','fixture');
      INSERT INTO bg_gochara_citation_resolution
        (citation_string,chunk_id,text_id,verse_ref,status,source_citation,constant_name,note)
      SELECT 'gap_' || i, 'CORPUS_GAP:fixture_' || i, 'fixture', 'V' || i,
             'unresolved', 'fixture gap', 'GAP_FIXTURE_' || lpad(i::text, 2, '0'), 'fixture gap'
      FROM generate_series(1, 11) AS i;
      INSERT INTO asset_registry
        (asset_id,target_floor,natural_key_partition,data_disposition,integrity_check_sql,volume_explanation)
      VALUES
        ('bg_gochara_citation_resolution',14,
         'bg_gochara_citation_resolution.(citation_string,chunk_id)',
         'RETAINED_AS_CAPITAL','SELECT false','legacy explanation');
    `)
    return client
  }

  async function citationDigest(client: Client): Promise<string> {
    const result = await client.query<{ digest: string }>(`
      SELECT encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(citation_string,chunk_id,text_id,verse_ref,status,
          source_citation,constant_name,note)::text,
        E'\\n' ORDER BY citation_string COLLATE "C",chunk_id COLLATE "C"
      ),''),'UTF8')),'hex') AS digest
      FROM bg_gochara_citation_resolution
    `)
    return result.rows[0].digest
  }

  async function setExpectedFinalRows(client: Client): Promise<void> {
    await client.query(`
      UPDATE bg_gochara_citation_resolution
      SET chunk_id = CASE constant_name
            WHEN 'GRAHA_DRISHTI_BPHS_26' THEN 'CORPUS_GAP:bphs_ch26_graha_drishti'
            WHEN 'GRAHA_DRISHTI_RASI_BPHS_26' THEN 'CORPUS_GAP:bphs_ch26_graha_drishti_rasi'
          END,
          verse_ref = 'CH26 exact graha-drishti passage not ingested',
          status = 'unresolved',
          source_citation = CASE constant_name
            WHEN 'GRAHA_DRISHTI_BPHS_26' THEN
              'BPHS Ch.26 Graha Drishti citation; the exact passage is absent from the current immutable classical_text_chunks corpus.'
            WHEN 'GRAHA_DRISHTI_RASI_BPHS_26' THEN
              'BPHS Ch.26 Graha Drishti rasi-rendering citation; the exact passage is absent from the current immutable classical_text_chunks corpus.'
          END,
          note = CASE constant_name
            WHEN 'GRAHA_DRISHTI_BPHS_26' THEN
              'The prior bphs_ch26_v001 mapping is absent from the immutable corpus; this citation remains an explicit corpus gap until canonical ingestion restores the exact passage.'
            WHEN 'GRAHA_DRISHTI_RASI_BPHS_26' THEN
              'The prior bphs_ch26_v001 mapping is absent from the immutable corpus; this rasi-rendering citation remains an explicit corpus gap until canonical ingestion restores the exact passage.'
          END
      WHERE constant_name IN ('GRAHA_DRISHTI_BPHS_26','GRAHA_DRISHTI_RASI_BPHS_26')
    `)
  }

  async function migrationForFixture(client: Client): Promise<string> {
    const oldHash = await client.query<{ digest: string }>(`
      SELECT encode(sha256(convert_to(integrity_check_sql,'UTF8')),'hex') AS digest
      FROM asset_registry WHERE asset_id='bg_gochara_citation_resolution'
    `)
    await client.query('BEGIN')
    await setExpectedFinalRows(client)
    const finalDigest = await citationDigest(client)
    await client.query('ROLLBACK')
    return migration
      .replaceAll(OLD_CONTRACT_HASH, oldHash.rows[0].digest)
      .replaceAll(PRODUCTION_FINAL_DIGEST, finalDigest)
  }

  async function detector(client: Client): Promise<boolean> {
    const registry = await client.query<{ integrity_check_sql: string }>(
      "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_gochara_citation_resolution'",
    )
    const observed = await client.query(registry.rows[0].integrity_check_sql)
    return observed.rowCount === 1 && Object.values(observed.rows[0])[0] === true
  }

  it('applies, executes the detector, replays, and preserves the frozen corpus count', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      const corpusBefore = await client.query('SELECT count(*)::int AS count FROM classical_text_chunks')
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)
      const corpusAfter = await client.query('SELECT count(*)::int AS count FROM classical_text_chunks')
      expect(corpusBefore.rows[0].count).toBe(10651)
      expect(corpusAfter.rows[0].count).toBe(10651)
      const registry = await client.query(
        "SELECT volume_explanation FROM asset_registry WHERE asset_id='bg_gochara_citation_resolution'",
      )
      expect(registry.rows[0].volume_explanation).toBe(FINAL_EXPLANATION)
    } finally {
      await client.end()
    }
  })

  it('rolls back the correction when the executable postflight detector finds unrelated drift', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query("UPDATE bg_gochara_citation_resolution SET note='drift' WHERE constant_name='GAP_FIXTURE_01'")
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'migration 631 citation-integrity detector postflight failed',
      )
      const rows = await client.query(
        "SELECT count(*)::int AS count FROM bg_gochara_citation_resolution WHERE chunk_id='bphs_ch26_v001'",
      )
      expect(rows.rows[0].count).toBe(2)
    } finally {
      await client.end()
    }
  })
})

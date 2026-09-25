import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'migrations/1123_l0_rules_link_accountability.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const migration618Path = path.resolve(
  process.cwd(),
  'supabase/migrations/618_nirmana_l0_rules_integrity_contract.sql',
)
const migration618 = fs.existsSync(migration618Path) ? fs.readFileSync(migration618Path, 'utf8') : ''
const TEST_DATABASE_URL = process.env.L0_RULES_LINK_ACCOUNTABILITY_TEST_DATABASE_URL
const OLD_DIGEST = '87b697041c73359e12daf8258cfdd6e85a38eb5c63fa39865e42f5b46e610dbd'
const NEW_DIGEST = 'f1d56d0cebf7ce2ad270ba1145cda20cae4c10f2ec3fb1ea01bc6b999feee098'

// The 36 replay-verified movable rows: pre-migration yoga link state.
const SURVIVORS: Array<[string, string]> = [
  ['0d20caf8-c33d-54a2-90d6-9790cc2d2ede', 'katanidhi'],
  ['7905eb4d-8285-5f03-8cc1-60cd1e9e2cbb', 'katanidhi'],
  ['2bdd08a1-ec92-59e8-9dd9-1fd88d0df15f', 'durudhura'],
  ['afee174d-6de3-581d-833d-5ee0d8c37043', 'durudhura'],
  ['a5d58ce9-5331-5db4-a803-41d9530e45fc', 'sunapha'],
  ['8a3a3c17-088a-5b7f-8e3d-06a28a08dae5', 'ubhayachari'],
]
const KILLED: Array<[string, string]> = [
  ['3e246a11-6b8a-5576-a6b2-7d993a3baed5', 'parijata'],
  ['4b88b9ce-660c-5390-b2eb-d1b89f5ce11d', 'parijata'],
  ['5eef209c-5fe7-5381-b7bf-6eca70b19ba6', 'parijata'],
  ['7c864547-1a80-5b97-b791-fd2b7ece8591', 'parijata'],
  ['a051d0c0-5742-5668-a242-b93f4cdb1394', 'parijata'],
  ['cb0680b1-faa2-528e-b136-4d1a4d0c70d8', 'parijata'],
  ['231e2146-4355-5815-b625-49765cb2ab4d', 'particular'],
  ['1717de42-8638-5a63-ab85-decf304c18f1', 'raja'],
  ['7ede2ed9-ceec-5fe5-910f-242b2face906', 'sunapha'],
  ['11041661-1c3e-581f-a3d8-a8954ab142c0', 'neecha_bhanga'],
  ['eaf960d9-5570-5971-9203-3ec0f5e837c5', 'durudhura'],
]
const UNLINKED_PRE = [
  '06c2785e-beb4-57a8-96de-4fffd65ed99c',
  '18d94b9c-ba24-535e-a15d-b3536ec11961',
  '279ef8e4-c644-54bc-9184-5b38a3e00750',
  '323ca1f7-cc18-5c2b-9d23-8209057e8760',
  '507743d5-d230-5437-bab0-25b2d05a4a48',
  '5ba828bd-c255-519f-98ae-fc3dded5420e',
  '7083157a-c410-5948-86f5-1a3ee599aa94',
  '896aa3e6-a7c2-5fc1-8e99-5531031c2e8c',
  '9b1f56eb-ff3c-581e-b7c9-ffe10b735897',
  'ab652951-edf7-5df9-b4f0-7a1d2efba9f4',
  'b478cab5-b282-5fd0-a798-6c8160f5a2cd',
  'c02a76d6-a82a-521c-8e02-a618de09824e',
  'cd76ab0c-ea5a-533d-bc02-2bbe4117a392',
  'cf36fd63-ba97-5ead-ad17-de9054fc051f',
  'd20f3f23-fd31-58e8-9b8e-644166269982',
  'da42245d-7445-5c9b-a8f7-7cc05a573423',
  'eb716479-c887-5e7a-a532-1788e13e5066',
  'f18e6d6b-60b0-5687-93e4-2ee19c640055',
  'faecc6eb-f6e1-5dfb-9c79-2930f6d6dae5',
]

const OLD_DIGEST_SQL = `
  SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
      prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
      yoga_canonical_id,dasha_system_id,transit_marker)::text,
    E'\\n' ORDER BY rule_id::text COLLATE "C"
  ),''),'UTF8')),'hex') AS digest
  FROM sutravali_rules
`
const NEW_DIGEST_SQL = `
  SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
      prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
      yoga_canonical_id,unlinked_reason,dasha_system_id,transit_marker)::text,
    E'\\n' ORDER BY rule_id::text COLLATE "C"
  ),''),'UTF8')),'hex') AS digest
  FROM sutravali_rules
`

describe('migration 1123 — rules link accountability', () => {
  it('is fail-closed, replay-pinned, and consistent with the 618 contract it succeeds', () => {
    expect(migration).not.toBe('')
    expect(migration).toContain(OLD_DIGEST)
    expect(migration).toContain(NEW_DIGEST)
    expect(migration).toContain('migration 1123 refuses unknown sutravali_rules starting state')
    expect(migration).toContain('migration 1123 refuses unknown bg_rules registry contract')
    expect(migration).toContain('migration 1123 refuses drifted post-migration state')
    expect(migration).toContain('sutravali_rules_unlinked_reason_vocab')
    expect(migration).toContain('sutravali_rules_unlinked_reason_link_xor')
    expect(migration).toContain("'no_concept_reference_in_window'")
    expect(migration).toContain("'ambiguous_reference'")
    expect(migration).toContain("'reference_not_in_catalog'")
    expect(migration).toContain('yoga_canonical_id,unlinked_reason,dasha_system_id')
    expect(migration).toContain('yoga_canonical_id IS NOT NULL) = 7')
    expect(migration).toMatch(/^BEGIN;/m)
    expect(migration).toMatch(/^COMMIT;/m)
    expect(migration).toContain('HELD')
    // The backfill covers exactly the 36 replay-verified rows.
    for (const [ruleId] of [...SURVIVORS, ...KILLED]) {
      expect(migration).toContain(ruleId)
    }
    for (const ruleId of UNLINKED_PRE) {
      expect(migration).toContain(ruleId)
    }
    // Applied migrations are never edited: 618 still carries its own pin.
    expect(migration618).toContain(OLD_DIGEST)
    expect(migration618).toContain('yoga_canonical_id IS NOT NULL) = 17')
    // The seed's bg_rules entry is unchanged by this packet.
    expect(ASSETS.find(asset => asset.asset_id === 'bg_rules')).toMatchObject({
      target_table: 'sutravali_rules',
      target_floor: 3002,
      depends_on: ['bg_texts', 'bg_yogas', 'bg_dasha_systems'],
    })
  })
})

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/l0_rules_link_accountability_test') {
    throw new Error(
      'L0_RULES_LINK_ACCOUNTABILITY_TEST_DATABASE_URL must point to the exact local '
      + 'l0_rules_link_accountability_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 1123 — real PostgreSQL behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      DROP TABLE IF EXISTS sutravali_rules,brahma_dasha_systems,
        brahma_yoga_catalog,classical_text_chunks,asset_registry,
        brahma_ontology,brahma_remedy_corpus CASCADE;
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
      CREATE TABLE brahma_ontology (
        canonical_id text NOT NULL, entity_class text NOT NULL, synonyms text[],
        PRIMARY KEY (canonical_id, entity_class)
      );
      CREATE TABLE brahma_remedy_corpus (
        remedy_id text PRIMARY KEY, source_canonical_id text, source_citation text
      );
      CREATE TABLE sutravali_rules (
        rule_id uuid PRIMARY KEY,text_id text NOT NULL,verse_ref text NOT NULL,
        antecedent_jsonb jsonb NOT NULL,predicate_jsonb jsonb NOT NULL,
        prediction_jsonb jsonb NOT NULL,confidence numeric(4,3) NOT NULL,
        extracted_by text NOT NULL,extraction_pass_log jsonb NOT NULL,
        quality_score numeric(4,3),yoga_canonical_id text,
        dasha_system_id text,transit_marker boolean
      );
      INSERT INTO classical_text_chunks VALUES ('chunk-1','fixture_text');
      INSERT INTO brahma_yoga_catalog VALUES
        ('katanidhi'),('durudhura'),('sunapha'),('ubhayachari'),
        ('parijata'),('particular'),('raja'),('neecha_bhanga');
      INSERT INTO brahma_ontology VALUES
        ('bphs','text',ARRAY['Brihat Parashara Hora Shastra']),
        ('phaladeepika','text',ARRAY['Phala Deepika']),
        ('tajaka_neelakanthi','text',ARRAY['Tajaka Neelakanthi']);
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
             0.800,NULL,NULL,i <= 25
      FROM generate_series(1,2966) AS i;
      INSERT INTO brahma_remedy_corpus
        SELECT 'b' || i,'BPHS','BPHS ch. ' || i FROM generate_series(1,193) AS i;
      INSERT INTO brahma_remedy_corpus
        SELECT 'p' || i,'Phaladeepika','Phaladeepika ch. ' || i FROM generate_series(1,11) AS i;
      INSERT INTO brahma_remedy_corpus
        SELECT 't' || i,'Tajaka','Tajaka ch. ' || i FROM generate_series(1,3) AS i;
      INSERT INTO brahma_remedy_corpus VALUES ('j1','bphs_jaimini','Jaimini Sutram, ch. 1');
      INSERT INTO brahma_remedy_corpus
        SELECT 'c' || i,'classical_tradition',
               CASE WHEN i = 1 THEN 'Muhurta Chintamani, classical Jyotish muhurta text'
                    ELSE 'classical tradition reference ' || i END
        FROM generate_series(1,80) AS i;
    `)
    const movable = [...SURVIVORS, ...KILLED, ...UNLINKED_PRE.map(id => [id, null] as [string, string | null])]
    const values = movable
      .map(([id, yoga], n) => `('${id}','R${n + 1}',${yoga === null ? 'NULL' : `'${yoga}'`})`)
      .join(',')
    await client.query(`
      INSERT INTO sutravali_rules
        (rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
         prediction_jsonb,confidence,extracted_by,extraction_pass_log,
         quality_score,yoga_canonical_id,dasha_system_id,transit_marker)
      SELECT v.rule_id::uuid,'fixture_text',v.verse_ref,
             jsonb_build_array(jsonb_build_object('planet','moon','house',1)),
             jsonb_build_object('type','fixture'),
             jsonb_build_object('result','movable'),
             0.800,'python_regex_v2',
             jsonb_build_array(jsonb_build_object('pattern','fixture','chunk_id','chunk-1','yoga_ambiguous',v.yoga IS NULL)),
             0.800,v.yoga,NULL,false
      FROM (VALUES ${values}) AS v(rule_id, verse_ref, yoga)
    `)
    return client
  }

  async function migrationForFixture(client: Client): Promise<string> {
    const oldObserved = await client.query<{ digest: string }>(OLD_DIGEST_SQL)
    const fixtureOld = oldObserved.rows[0].digest
    // Simulate the post-migration state inside a rolled-back transaction to
    // learn the fixture's new digest, reusing the migration's own backfill
    // VALUES so there is one source of truth for the 36 rows.
    const valuesBlock = migration.match(
      /FROM \(VALUES\n([\s\S]*?)\n {4}\) AS v\(rule_id, final_yoga, final_reason\)/,
    )
    if (!valuesBlock) throw new Error('migration 1123 backfill VALUES block not found')
    await client.query('BEGIN')
    await client.query(`ALTER TABLE sutravali_rules ADD COLUMN unlinked_reason text`)
    await client.query(`
      UPDATE sutravali_rules AS rule
      SET yoga_canonical_id = v.final_yoga, unlinked_reason = v.final_reason
      FROM (VALUES
${valuesBlock[1]}
    ) AS v(rule_id, final_yoga, final_reason)
      WHERE rule.rule_id = v.rule_id::uuid
    `)
    await client.query(`
      UPDATE sutravali_rules SET unlinked_reason = 'no_concept_reference_in_window'
      WHERE unlinked_reason IS NULL AND yoga_canonical_id IS NULL
    `)
    const newObserved = await client.query<{ digest: string }>(NEW_DIGEST_SQL)
    const fixtureNew = newObserved.rows[0].digest
    await client.query('ROLLBACK')
    // The registry row must carry the 618 contract with the fixture digest so
    // the migration's old_contract guard matches.
    // The stored contract is the full text between the $check$ markers,
    // including the leading and trailing newlines.
    const oldContract = migration618.match(/\$check\$([\s\S]*?)\$check\$/)
    if (!oldContract) throw new Error('618 contract block not found')
    await client.query(
      `INSERT INTO asset_registry
        (asset_id,layer,sort_order,scope,asset_kind,catalog_status,is_active,
         has_writer,target_table,count_sql,target_floor,depends_on,
         natural_key_partition,data_disposition,integrity_check_sql,
         english_description,volume_explanation)
       VALUES
        ('bg_rules','brahmagyan',6,'global','data','CURRENT',true,true,
         'sutravali_rules','SELECT count(*) FROM sutravali_rules',3002,
         ARRAY['bg_texts','bg_yogas','bg_dasha_systems']::text[],
         'sutravali_rules.rule_id',NULL,$1,
         'Classical rules extracted from text chunks via Python regex patterns — verse-traceable',
         'fixture')`,
      [oldContract[1].replaceAll(OLD_DIGEST, fixtureOld)],
    )
    return migration.replaceAll(OLD_DIGEST, fixtureOld).replaceAll(NEW_DIGEST, fixtureNew)
  }

  async function detector(client: Client): Promise<boolean> {
    const contract = await client.query<{ integrity_check_sql: string }>(
      `SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_rules'`,
    )
    const observed = await client.query(contract.rows[0].integrity_check_sql)
    return observed.rowCount === 1 && Object.values(observed.rows[0])[0] === true
  }

  it('applies, verifies the replay outcome, and re-applies as a no-op', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)
      // Second application takes the state-B path and changes nothing.
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)

      const spot = await client.query(
        `SELECT rule_id::text, yoga_canonical_id, unlinked_reason
         FROM sutravali_rules
         WHERE rule_id IN ('cf36fd63-ba97-5ead-ad17-de9054fc051f',
                           '3e246a11-6b8a-5576-a6b2-7d993a3baed5',
                           '06c2785e-beb4-57a8-96de-4fffd65ed99c',
                           '896aa3e6-a7c2-5fc1-8e99-5531031c2e8c',
                           '0d20caf8-c33d-54a2-90d6-9790cc2d2ede')
         ORDER BY rule_id::text`,
      )
      expect(spot.rows).toEqual([
        { rule_id: '06c2785e-beb4-57a8-96de-4fffd65ed99c', yoga_canonical_id: null, unlinked_reason: 'ambiguous_reference' },
        { rule_id: '0d20caf8-c33d-54a2-90d6-9790cc2d2ede', yoga_canonical_id: 'katanidhi', unlinked_reason: null },
        { rule_id: '3e246a11-6b8a-5576-a6b2-7d993a3baed5', yoga_canonical_id: null, unlinked_reason: 'no_concept_reference_in_window' },
        { rule_id: '896aa3e6-a7c2-5fc1-8e99-5531031c2e8c', yoga_canonical_id: null, unlinked_reason: 'reference_not_in_catalog' },
        { rule_id: 'cf36fd63-ba97-5ead-ad17-de9054fc051f', yoga_canonical_id: 'sunapha', unlinked_reason: null },
      ])

      const constraints = await client.query(
        `SELECT constraint_name FROM information_schema.table_constraints
         WHERE table_name = 'sutravali_rules' AND constraint_type = 'CHECK'
           AND constraint_name LIKE 'sutravali_rules_unlinked_reason_%'
         ORDER BY 1`,
      )
      expect(constraints.rows.map(row => row.constraint_name)).toEqual([
        'sutravali_rules_unlinked_reason_link_xor',
        'sutravali_rules_unlinked_reason_vocab',
      ])

      const remedy = await client.query(
        `SELECT source_canonical_id, count(*)::int AS n FROM brahma_remedy_corpus
         GROUP BY 1 ORDER BY 1`,
      )
      expect(remedy.rows).toEqual([
        { source_canonical_id: 'bphs', n: 193 },
        { source_canonical_id: 'classical_tradition', n: 79 },
        { source_canonical_id: 'jaimini_sutram', n: 1 },
        { source_canonical_id: 'muhurta_chintamani', n: 1 },
        { source_canonical_id: 'phaladeepika', n: 11 },
        { source_canonical_id: 'tajaka_neelakanthi', n: 3 },
      ])

      const synonyms = await client.query(
        `SELECT canonical_id, synonyms FROM brahma_ontology WHERE entity_class = 'text' ORDER BY 1`,
      )
      expect(synonyms.rows).toEqual([
        { canonical_id: 'bphs', synonyms: ['Brihat Parashara Hora Shastra', 'BPHS'] },
        { canonical_id: 'phaladeepika', synonyms: ['Phala Deepika', 'Phaladeepika'] },
        { canonical_id: 'tajaka_neelakanthi', synonyms: ['Tajaka Neelakanthi', 'Tajaka'] },
      ])
    } finally {
      await client.end()
    }
  })

  it('refuses an unknown sutravali_rules starting state', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(
        `UPDATE sutravali_rules SET prediction_jsonb='{"result":"tampered"}' WHERE verse_ref='V1'`,
      )
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'migration 1123 refuses unknown sutravali_rules starting state',
      )
    } finally {
      await client.end()
    }
  })

  it('detector fires on drift; constraints fire on accounting violations', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      expect(await detector(client)).toBe(true)

      // Accounting violations are rejected structurally, not by the detector.
      await expect(client.query(
        `UPDATE sutravali_rules SET unlinked_reason = NULL
         WHERE rule_id = '06c2785e-beb4-57a8-96de-4fffd65ed99c'`,
      )).rejects.toThrow('sutravali_rules_unlinked_reason_link_xor')
      await expect(client.query(
        `UPDATE sutravali_rules SET unlinked_reason = 'invented_reason'
         WHERE rule_id = '06c2785e-beb4-57a8-96de-4fffd65ed99c'`,
      )).rejects.toThrow('sutravali_rules_unlinked_reason_vocab')
      await expect(client.query(
        `UPDATE sutravali_rules SET yoga_canonical_id = 'sunapha'
         WHERE rule_id = '06c2785e-beb4-57a8-96de-4fffd65ed99c'`,
      )).rejects.toThrow('sutravali_rules_unlinked_reason_link_xor')

      // Detector-visible drift, each falsifying the contract.
      const corruptions = [
        `UPDATE sutravali_rules SET prediction_jsonb='{"result":"drift"}' WHERE verse_ref='V1'`,
        `UPDATE sutravali_rules SET extracted_by='manual' WHERE verse_ref='V1'`,
        `UPDATE sutravali_rules SET unlinked_reason='ambiguous_reference'
           WHERE verse_ref='V30' AND unlinked_reason='no_concept_reference_in_window'`,
        `INSERT INTO sutravali_rules
           (rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
            prediction_jsonb,confidence,extracted_by,extraction_pass_log,
            quality_score,yoga_canonical_id,dasha_system_id,transit_marker,unlinked_reason)
         SELECT gen_random_uuid(),text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
           prediction_jsonb,confidence,extracted_by,extraction_pass_log,
           quality_score,NULL,NULL,false,'no_concept_reference_in_window'
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
      expect(await detector(client)).toBe(true)
    } finally {
      await client.end()
    }
  })

  it('re-application refuses post-migration drift', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)

      await client.query(
        `UPDATE brahma_remedy_corpus SET source_canonical_id = 'BPHS' WHERE remedy_id = 'b1'`,
      )
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'migration 1123 postflight: remedy source drift present',
      )
      // The migration's own BEGIN leaves the connection in an aborted
      // transaction after a refusal; roll back before continuing.
      await client.query('ROLLBACK')
      await client.query(
        `UPDATE brahma_remedy_corpus SET source_canonical_id = 'bphs' WHERE remedy_id = 'b1'`,
      )

      await client.query(
        `UPDATE sutravali_rules SET prediction_jsonb='{"result":"drift"}' WHERE verse_ref='V1'`,
      )
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'migration 1123 refuses drifted post-migration state',
      )
      await client.query('ROLLBACK')
    } finally {
      await client.end()
    }
  })
})

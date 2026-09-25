import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'migrations/1124_nirmana_l0_provenance_completion.sql',
)
const migration = fs.existsSync(migrationPath) ? fs.readFileSync(migrationPath, 'utf8') : ''
const TEST_DATABASE_URL = process.env.L0_PROVENANCE_COMPLETION_TEST_DATABASE_URL
const RULES_DIGEST = 'f1d56d0cebf7ce2ad270ba1145cda20cae4c10f2ec3fb1ea01bc6b999feee098'

// The 1123 digest vector — 1124 re-verifies it and adds columns OUTSIDE it.
const RULES_DIGEST_SQL = `
  SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
      prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
      yoga_canonical_id,unlinked_reason,dasha_system_id,transit_marker)::text,
    E'\\n' ORDER BY rule_id::text COLLATE "C"
  ),''),'UTF8')),'hex') AS digest
  FROM sutravali_rules
`

describe('migration 1124 — L0 provenance completion', () => {
  it('is fail-closed, pre-state-pinned, and carries the measured guards', () => {
    expect(migration).not.toBe('')
    expect(migration).toMatch(/^BEGIN;/m)
    expect(migration).toMatch(/^COMMIT;/m)
    expect(migration).toContain('HELD')
    // Apply-order dependency on 1123 and the 1123 digest pin.
    expect(migration).toContain(RULES_DIGEST)
    expect(migration).toContain('apply migration 1123 first')
    expect(migration).toContain('yoga_canonical_id,unlinked_reason,dasha_system_id')
    // Fail-closed guards.
    expect(migration).toContain('migration 1124 refuses: a required table is absent')
    expect(migration).toContain('migration 1124 refuses: a measured pre-flight count deviates from the 2026-09-25 production measurement')
    expect(migration).toContain('migration 1124 refuses: license-cleared rule(s) without a chunk witness exist — investigate before labeling')
    expect(migration).toContain('migration 1124 refuses unknown sutravali_rules state')
    expect(migration).toContain("migration 1124 refuses: bg_vidhi_floors description is neither the 642 pre-state nor this migration''s post-state")
    // Measured rowcount assertions.
    expect(migration).toContain('migration 1124 expected 3002 rules joined to classical_texts')
    expect(migration).toContain('migration 1124 expected 70 transit rules mapped')
    expect(migration).toContain('migration 1124 expected 60 parihara rules joined')
    expect(migration).toContain('migration 1124 expected 10 primitive source_refs')
    expect(migration).toContain('migration 1124 expected 8 floor source_refs')
    expect(migration).toContain('migration 1124 expected 409 floor items inherited')
    // Postflights.
    expect(migration).toContain('migration 1124 postflight: sutravali_rules provenance incomplete')
    expect(migration).toContain('migration 1124 postflight: bg_transit_rules school mismatch')
    expect(migration).toContain('migration 1124 postflight: bg_parihara_rules school mismatch')
    expect(migration).toContain('migration 1124 postflight: vidhi provenance mismatch')
    expect(migration).toContain('migration 1124 postflight registry mismatch')
    // DP §4.3 vocabulary constraint with all five states.
    expect(migration).toContain('sutravali_rules_qualification_state_vocab')
    for (const state of ['QUALIFIED_EXECUTABLE', 'UNQUALIFIED_SOURCE', 'READABLE_NOT_EXECUTABLE', 'UNSUPPORTED_SCOPE', 'METHOD_INAPPLICABLE']) {
      expect(migration).toContain(`'${state}'`)
    }
    // The 642 defect repair: pinned pre-state and truthful post-state.
    expect(migration).toContain('12/14 intent floors are writer-tagged [MANDATORY] (settled)')
    expect(migration).toContain('1/14 intent floors is writer-tagged [MANDATORY] (spirituality_deepdive)')
    // The UNSOURCED guard is load-bearing (citation text names Phaladipika).
    expect(migration).toContain("r.classical_citation NOT ILIKE 'UNSOURCED%'")
    // The seed carries the same truthful text so a reseed cannot reinstall the defect.
    const floors = ASSETS.find(asset => asset.asset_id === 'bg_vidhi_floors')
    expect(floors?.english_description).toContain('1/14 intent floors is writer-tagged [MANDATORY] (spirituality_deepdive)')
    expect(floors?.english_description).not.toContain('12/14')
  })
})

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/l0_provenance_completion_test') {
    throw new Error(
      'L0_PROVENANCE_COMPLETION_TEST_DATABASE_URL must point to the exact local '
      + 'l0_provenance_completion_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 1124 — real PostgreSQL behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      CREATE EXTENSION IF NOT EXISTS pgcrypto;
      DROP TABLE IF EXISTS sutravali_rules,bg_transit_rules,bg_parihara_rules,
        vidhi_primitives,vidhi_intent_floors,vidhi_floor_items,
        classical_texts,classical_text_chunks,brahma_dosha_catalog,
        asset_registry CASCADE;
      CREATE TABLE asset_registry (asset_id text PRIMARY KEY, english_description text);
      CREATE TABLE classical_texts (
        text_id text PRIMARY KEY, school text, license_cleared boolean NOT NULL
      );
      CREATE TABLE classical_text_chunks (
        chunk_id text PRIMARY KEY, text_id text NOT NULL, verse_ref text NOT NULL
      );
      CREATE TABLE brahma_dosha_catalog (canonical_id text PRIMARY KEY, school text);
      CREATE TABLE sutravali_rules (
        rule_id uuid PRIMARY KEY,text_id text NOT NULL,verse_ref text NOT NULL,
        antecedent_jsonb jsonb NOT NULL,predicate_jsonb jsonb NOT NULL,
        prediction_jsonb jsonb NOT NULL,confidence numeric(4,3) NOT NULL,
        extracted_by text NOT NULL,extraction_pass_log jsonb NOT NULL,
        quality_score numeric(4,3),yoga_canonical_id text,
        unlinked_reason text,dasha_system_id text,transit_marker boolean
      );
      CREATE TABLE bg_transit_rules (
        transit_id text PRIMARY KEY, classical_citation text NOT NULL
      );
      CREATE TABLE bg_parihara_rules (
        parihara_id text PRIMARY KEY, dosha_canonical_id text NOT NULL
      );
      CREATE TABLE vidhi_primitives (primitive_id text PRIMARY KEY);
      CREATE TABLE vidhi_intent_floors (intent text PRIMARY KEY);
      CREATE TABLE vidhi_floor_items (item_id text PRIMARY KEY, intent text NOT NULL);

      -- Fixture texts carry SENTINEL schools so a citation mis-map is visible
      -- in the assertions below (fixtures are not provenance truth).
      INSERT INTO classical_texts VALUES
        ('fixture_text','parashari',true),
        ('bphs','fixture_bphs',true),
        ('phaladeepika','fixture_phala',true),
        ('saravali','fixture_saravali',true),
        ('jataka_parijata','fixture_jataka',true),
        ('uttara_kalamrita','fixture_uttara',true);
      INSERT INTO classical_text_chunks
        SELECT 'c' || i,'fixture_text','V' || i FROM generate_series(1,3002) AS i;
      INSERT INTO sutravali_rules
        (rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
         prediction_jsonb,confidence,extracted_by,extraction_pass_log,
         quality_score,yoga_canonical_id,unlinked_reason,dasha_system_id,transit_marker)
      SELECT md5(i::text)::uuid,'fixture_text','V' || i,
             jsonb_build_array(jsonb_build_object('planet','sun','house',(i % 12)+1)),
             jsonb_build_object('type','fixture'),
             jsonb_build_object('result','fixture ' || i),
             0.800,'python_regex_v2',
             jsonb_build_array(jsonb_build_object('pattern','fixture','chunk_id','c' || i)),
             0.800,NULL,'no_concept_reference_in_window',NULL,i <= 25
      FROM generate_series(1,3002) AS i;

      -- 76 transit rows: 19 BPHS + 51 Phaladipika/Phaladeepika variants
      -- (incl. §double-gochara composites naming BPHS secondarily) + 6
      -- UNSOURCED rows whose own text names Phaladipika (guard must win).
      INSERT INTO bg_transit_rules
        SELECT 'b' || i,'BPHS Ch.29 (Gochara Phala — Transit Results)'
        FROM generate_series(1,19) AS i;
      INSERT INTO bg_transit_rules
        SELECT 'p' || i,'Phaladipika Adh. XXVI, Sloka ' || i
               || ' — phaladeepika:PG322:C1 (Sastri trans. 1950)'
        FROM generate_series(1,25) AS i;
      INSERT INTO bg_transit_rules
        SELECT 'd' || i,'Phaladeepika ch.26 §double-gochara (BPHS Ch.29; Saravali) ' || i
        FROM generate_series(1,26) AS i;
      INSERT INTO bg_transit_rules
        SELECT 'u' || i,'UNSOURCED — Rahu/Ketu vedha long-form note (cf. Phaladipika) ' || i
        FROM generate_series(1,6) AS i;

      INSERT INTO brahma_dosha_catalog
        SELECT 'dosha_' || i,'parashari' FROM generate_series(1,60) AS i;
      INSERT INTO bg_parihara_rules
        SELECT 'parihara_' || i,'dosha_' || i FROM generate_series(1,60) AS i;

      INSERT INTO vidhi_primitives
        SELECT pid FROM (VALUES
          ('medical_read'),('sensitive_degree_check'),('ahead_read'),('elect_read'),
          ('explain_read'),('now_read'),('priority_read'),('ritual_read'),
          ('story_read'),('upaya_read')
        ) AS v(pid);
      INSERT INTO vidhi_primitives
        SELECT 'primitive_' || i FROM generate_series(11,60) AS i;
      INSERT INTO vidhi_intent_floors
        SELECT intent FROM (VALUES
          ('wealth_deepdive'),('career_deepdive'),('spirituality_deepdive'),
          ('education_deepdive'),('progeny_deepdive'),('undertaking_election'),
          ('biography_narrative'),('ritual_yajna'),('general_synthesis'),
          ('health_deepdive'),('marriage_deepdive'),('panoramic'),
          ('retrieval_only'),('structure_read')
        ) AS v(intent);
      INSERT INTO vidhi_floor_items
        SELECT intent || '_' || n, intent
        FROM (VALUES
          ('wealth_deepdive',43),('career_deepdive',39),('spirituality_deepdive',35),
          ('education_deepdive',34),('progeny_deepdive',30),('undertaking_election',33),
          ('biography_narrative',33),('ritual_yajna',33),('general_synthesis',32),
          ('health_deepdive',43),('marriage_deepdive',39),('panoramic',8),
          ('retrieval_only',1),('structure_read',6)
        ) AS v(intent, n_items)
        CROSS JOIN LATERAL generate_series(1, v.n_items) AS n;
    `)
    // The registry row must carry the exact 642 pre-state text so the pinned
    // swap matches. The migration is the one source of truth for that text.
    const oldDescription = migration.match(
      /floors_old_description constant text :=\n    '([\s\S]*?)';/,
    )
    if (!oldDescription) throw new Error('migration 1124 floors_old_description not found')
    await client.query(
      `INSERT INTO asset_registry VALUES ('bg_vidhi_floors', $1)`,
      [oldDescription[1]],
    )
    return client
  }

  async function migrationForFixture(client: Client): Promise<string> {
    const observed = await client.query<{ digest: string }>(RULES_DIGEST_SQL)
    return migration.replaceAll(RULES_DIGEST, observed.rows[0].digest)
  }

  it('applies, backfills the measured states, and re-applies as a verifying no-op', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)

      const rules = await client.query(
        `SELECT school, qualification_state, count(*)::int AS n
         FROM sutravali_rules GROUP BY 1, 2`,
      )
      expect(rules.rows).toEqual([
        { school: 'parashari', qualification_state: 'QUALIFIED_EXECUTABLE', n: 3002 },
      ])

      // Sentinel schools prove the citation map: 19 BPHS, 51 phalad (incl. the
      // §double-gochara composites that name BPHS secondarily), 6 UNSOURCED NULL.
      const transit = await client.query(
        `SELECT school, count(*)::int AS n FROM bg_transit_rules GROUP BY 1 ORDER BY 1 NULLS LAST`,
      )
      expect(transit.rows).toEqual([
        { school: 'fixture_bphs', n: 19 },
        { school: 'fixture_phala', n: 51 },
        { school: null, n: 6 },
      ])
      const unsourcedNull = await client.query(
        `SELECT count(*)::int AS n FROM bg_transit_rules
         WHERE classical_citation ILIKE 'UNSOURCED%' AND school IS NULL`,
      )
      expect(unsourcedNull.rows[0].n).toBe(6)

      const parihara = await client.query(
        `SELECT school, count(*)::int AS n FROM bg_parihara_rules GROUP BY 1`,
      )
      expect(parihara.rows).toEqual([{ school: 'parashari', n: 60 }])

      const provenance = await client.query(
        `SELECT
           (SELECT count(*)::int FROM vidhi_primitives WHERE source_ref IS NOT NULL) AS primitives,
           (SELECT count(*)::int FROM vidhi_intent_floors WHERE source_ref IS NOT NULL) AS floors,
           (SELECT count(*)::int FROM vidhi_floor_items WHERE source_ref IS NOT NULL) AS items,
           (SELECT count(*)::int FROM vidhi_floor_items
            WHERE source_authority = 'src/lib/vidhi/registry_data.ts') AS item_authority`,
      )
      expect(provenance.rows[0]).toEqual({
        primitives: 10, floors: 8, items: 280, item_authority: 409,
      })
      // Floor items inherit their INTENT's ref, not a guess.
      const inherited = await client.query(
        `SELECT i.source_ref IS NOT DISTINCT FROM f.source_ref AS matches, count(*)::int AS n
         FROM vidhi_floor_items i JOIN vidhi_intent_floors f ON f.intent = i.intent
         GROUP BY 1`,
      )
      expect(inherited.rows).toEqual([{ matches: true, n: 409 }])

      const description = await client.query(
        `SELECT english_description FROM asset_registry WHERE asset_id = 'bg_vidhi_floors'`,
      )
      expect(description.rows[0].english_description).toContain(
        '1/14 intent floors is writer-tagged [MANDATORY] (spirituality_deepdive)',
      )

      const constraints = await client.query(
        `SELECT constraint_name FROM information_schema.table_constraints
         WHERE table_name = 'sutravali_rules' AND constraint_type = 'CHECK'
           AND constraint_name = 'sutravali_rules_qualification_state_vocab'`,
      )
      expect(constraints.rowCount).toBe(1)

      // The vocabulary constraint enforces structurally.
      await expect(client.query(
        `UPDATE sutravali_rules SET qualification_state = 'INVENTED_STATE' WHERE verse_ref = 'V1'`,
      )).rejects.toThrow('sutravali_rules_qualification_state_vocab')

      // Re-application takes the state-B path and changes nothing.
      await client.query(fixtureMigration)
      const after = await client.query(
        `SELECT
           (SELECT count(*)::int FROM sutravali_rules
            WHERE qualification_state = 'QUALIFIED_EXECUTABLE') AS rules,
           (SELECT count(*)::int FROM bg_transit_rules WHERE school IS NOT NULL) AS transit,
           (SELECT count(*)::int FROM vidhi_floor_items WHERE source_ref IS NOT NULL) AS items`,
      )
      expect(after.rows[0]).toEqual({ rules: 3002, transit: 70, items: 280 })
    } finally {
      await client.end()
    }
  })

  it('refuses an unknown sutravali_rules state (digest mismatch)', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(
        `UPDATE sutravali_rules SET prediction_jsonb='{"result":"tampered"}' WHERE verse_ref='V1'`,
      )
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'migration 1124 refuses unknown sutravali_rules state',
      )
    } finally {
      await client.end()
    }
  })

  it('refuses a license-cleared rule without a chunk witness', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(`DELETE FROM classical_text_chunks WHERE verse_ref = 'V7'`)
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'license-cleared rule(s) without a chunk witness exist',
      )
    } finally {
      await client.end()
    }
  })

  it('refuses a deviating measured pre-flight count', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(`DELETE FROM bg_transit_rules WHERE transit_id = 'b1'`)
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'a measured pre-flight count deviates',
      )
    } finally {
      await client.end()
    }
  })

  it('re-application refuses a moved-on bg_vidhi_floors description', async () => {
    const client = await connectPrepared()
    try {
      const fixtureMigration = await migrationForFixture(client)
      await client.query(fixtureMigration)
      await client.query(
        `UPDATE asset_registry SET english_description = 'moved on by another session'
         WHERE asset_id = 'bg_vidhi_floors'`,
      )
      await expect(client.query(fixtureMigration)).rejects.toThrow(
        'bg_vidhi_floors description is neither the 642 pre-state',
      )
      // The migration's own BEGIN leaves the connection in an aborted
      // transaction after a refusal.
      await client.query('ROLLBACK')
    } finally {
      await client.end()
    }
  })
})

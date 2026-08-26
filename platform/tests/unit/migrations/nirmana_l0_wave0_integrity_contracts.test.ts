import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migrationPath = path.resolve(
  process.cwd(),
  'supabase/migrations/606_nirmana_l0_wave0_integrity_contracts.sql',
)
const migration = fs.readFileSync(migrationPath, 'utf8')
const ASSET_IDS = [
  'bg_cohort',
  'bg_ontology',
  'bg_ephemeris',
  'bg_nakshatra',
  'bg_dignity_reference',
] as const
const ONTOLOGY_EXPLANATION = '737 achieved ontology rows in the authoritative production corpus; closed classical sets are enforced by integrity SQL while extensible classes may grow.'

describe('migration 606 — L0 wave-0 integrity contracts', () => {
  it('stores one executable boolean contract per reviewed asset and leaves transactions to the runner', () => {
    for (const assetId of ASSET_IDS) {
      expect(migration).toContain(`asset_id = '${assetId}'`)
      expect(migration).toContain(`migration 606 refuses unknown ${assetId} registry contract`)
    }
    expect(migration.match(/CONSTANT TEXT := \$check\$/g)).toHaveLength(5)
    expect(migration).toContain('COUNT(*) = 2721 AND COUNT(DISTINCT matrix_type) = 12')
    expect(migration).toContain('COUNT(md.synthetic_id) NOT IN (9,10)')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
  })

  it('keeps the canonical ontology seed aligned with the achieved floor', () => {
    const ontology = ASSETS.find((asset) => asset.asset_id === 'bg_ontology')
    expect(ontology?.target_floor).toBe(737)
    expect(ontology?.volume_explanation).toBe(ONTOLOGY_EXPLANATION)
  })
})

const TEST_DATABASE_URL = process.env.NIRMANA_L0_WAVE0_INTEGRITY_TEST_DATABASE_URL

if (TEST_DATABASE_URL) {
  const parsed = new URL(TEST_DATABASE_URL)
  if (!['localhost', '127.0.0.1'].includes(parsed.hostname)
    || parsed.pathname !== '/nirmana_l0_wave0_integrity_test') {
    throw new Error(
      'NIRMANA_L0_WAVE0_INTEGRITY_TEST_DATABASE_URL must point to the exact local '
      + 'nirmana_l0_wave0_integrity_test database',
    )
  }
}

describe.skipIf(!TEST_DATABASE_URL)('migration 606 — real Postgres behavior', () => {
  async function connectPrepared(): Promise<Client> {
    const client = new Client({ connectionString: TEST_DATABASE_URL })
    await client.connect()
    await client.query(`
      CREATE TEMP TABLE asset_registry (
        asset_id text PRIMARY KEY,
        layer text,
        sort_order integer,
        scope text,
        asset_kind text,
        catalog_status text,
        is_active boolean,
        has_writer boolean,
        target_table text,
        count_sql text,
        target_floor bigint,
        volume_explanation text,
        integrity_check_sql text
      );
      INSERT INTO asset_registry
        (asset_id, layer, sort_order, scope, asset_kind, catalog_status,
         is_active, has_writer, target_table, count_sql, target_floor,
         volume_explanation, integrity_check_sql)
      VALUES
        ('bg_cohort','brahmagyan',20,'global','data','CURRENT',true,true,
         'bg_synthetic_cohort','SELECT COUNT(*) FROM bg_synthetic_cohort',10000,
         '10,000 synthetic birth charts, uniform-random over 1900-2099, fixed RNG seed. See bg_cohort.py module docstring for full sampling methodology.',NULL),
        ('bg_ontology','brahmagyan',4,'global','data','CURRENT',true,true,
         'brahma_ontology','SELECT count(*) FROM brahma_ontology',623,
         'Static vocabulary — count established at seed; used by resolve_entity retrieval tool',NULL),
        ('bg_ephemeris','brahmagyan',1,'global','data','CURRENT',true,true,
         'ephemeris_daily','SELECT count(*) FROM ephemeris_daily',825084,
         'ephemeris fixture',NULL),
        ('bg_nakshatra','brahmagyan',15,'global','data','CURRENT',true,true,
         'reference_nakshatra',
         'SELECT (SELECT COUNT(*) FROM reference_nakshatra) + (SELECT COUNT(*) FROM reference_nakshatra_pada) + (SELECT COUNT(*) FROM reference_nakshatra_matrix) AS count',
         2857,'nakshatra fixture',NULL),
        ('bg_dignity_reference','brahmagyan',66,'global','data','CURRENT',true,true,
         'bg_dignity_reference',
         'SELECT (SELECT COUNT(*) FROM bg_dignity_reference) + (SELECT COUNT(*) FROM bg_avastha_schemes) + (SELECT COUNT(*) FROM bg_combustion_orbs) + (SELECT COUNT(*) FROM bg_graha_naisargika_friendship) + (SELECT COUNT(*) FROM bg_motion_state_thresholds) AS count',
         151,'dignity fixture',NULL);
    `)
    return client
  }

  async function installHealthyFixtures(client: Client): Promise<void> {
    await client.query(`
      CREATE TEMP TABLE bg_synthetic_cohort (synthetic_id integer, positions jsonb);
      INSERT INTO bg_synthetic_cohort
      SELECT synthetic_id, jsonb_build_object(
        'Sun', pos, 'Moon', pos, 'Mars', pos, 'Mercury', pos, 'Jupiter', pos,
        'Venus', pos, 'Saturn', pos, 'Rahu', pos, 'Ketu', pos, 'Lagna', pos)
      FROM generate_series(1,10000) synthetic_id
      CROSS JOIN (SELECT '{"sign_id":1,"nakshatra_id":1,"nakshatra_pada":1}'::jsonb AS pos) seed;
      CREATE TEMP TABLE bg_synthetic_cohort_md (
        synthetic_id integer, md_index integer, start_age_years numeric, end_age_years numeric
      );
      INSERT INTO bg_synthetic_cohort_md
      SELECT synthetic_id, md_index, (md_index - 1) * 12, md_index * 12
      FROM generate_series(1,10000) synthetic_id
      CROSS JOIN generate_series(1,10) md_index;

      CREATE TEMP TABLE brahma_ontology (
        entity_class text, canonical_id text, canonical_name_en text, source_citation text
      );
      INSERT INTO brahma_ontology
      SELECT 'nakshatra', 'nak_' || LPAD(ordinality::text,2,'0') || '_' || name, name, 'source'
      FROM unnest(ARRAY[
        'ashwini','bharani','krittika','rohini','mrigasira','ardra','punarvasu','pushya','ashlesha',
        'magha','purva_phalguni','uttara_phalguni','hasta','chitra','swati','vishakha','anuradha',
        'jyeshtha','moola','purva_ashadha','uttara_ashadha','shravana','dhanishtha','shatabhisha',
        'purva_bhadrapada','uttara_bhadrapada','revati'
      ]) WITH ORDINALITY AS expected(name,ordinality);
      INSERT INTO brahma_ontology
      SELECT 'sign', name, name, 'source' FROM unnest(ARRAY[
        'aquarius','aries','cancer','capricorn','gemini','leo','libra','pisces','sagittarius','scorpio','taurus','virgo'
      ]) name;
      INSERT INTO brahma_ontology
      SELECT 'house', 'house_' || LPAD(id::text,2,'0'), 'house' || id, 'source' FROM generate_series(1,12) id;
      INSERT INTO brahma_ontology
      SELECT 'planet', name, name, 'source' FROM unnest(ARRAY[
        'ascendant','jupiter','ketu','mars','mercury','midheaven','moon','rahu','saturn','sun','venus'
      ]) name;
      INSERT INTO brahma_ontology
      SELECT 'concept', 'concept-' || id, 'concept' || id, 'source' FROM generate_series(1,675) id;

      CREATE TEMP TABLE ephemeris_daily AS
      SELECT day::date AS date, body, 'tropical'::text AS ayanamsha_id, 1::numeric AS tropical_longitude
      FROM generate_series(DATE '1900-01-01', DATE '2150-12-31', INTERVAL '1 day') day
      CROSS JOIN unnest(ARRAY['Jupiter','Ketu','Mars','Mercury','Moon','Rahu','Saturn','Sun','Venus']) body;

      CREATE TEMP TABLE reference_nakshatra (nakshatra_id integer, is_panchaka boolean, is_abhijit boolean);
      INSERT INTO reference_nakshatra
      SELECT id, id BETWEEN 23 AND 27, id = 28 FROM generate_series(1,28) id;
      CREATE TEMP TABLE reference_nakshatra_pada (nakshatra_id integer, pada_number integer);
      INSERT INTO reference_nakshatra_pada
      SELECT nakshatra_id, pada_number FROM generate_series(1,27) nakshatra_id CROSS JOIN generate_series(1,4) pada_number;
      CREATE TEMP TABLE reference_nakshatra_matrix (matrix_type text, from_key text, to_key text);
      INSERT INTO reference_nakshatra_matrix SELECT 'gana_kuta',from_key,to_key
        FROM unnest(ARRAY['Deva','Manushya','Rakshasa']) from_key CROSS JOIN unnest(ARRAY['Deva','Manushya','Rakshasa']) to_key;
      INSERT INTO reference_nakshatra_matrix SELECT 'nadi_kuta',from_key,to_key
        FROM unnest(ARRAY['Adi','Madhya','Antya']) from_key CROSS JOIN unnest(ARRAY['Adi','Madhya','Antya']) to_key;
      INSERT INTO reference_nakshatra_matrix SELECT 'yoni_kuta',from_key,to_key
        FROM unnest(ARRAY['Horse','Elephant','Goat','Serpent','Dog','Cat','Rat','Cow','Buffalo','Tiger','Hare','Mongoose','Monkey','Lion']) from_key
        CROSS JOIN unnest(ARRAY['Horse','Elephant','Goat','Serpent','Dog','Cat','Rat','Cow','Buffalo','Tiger','Hare','Mongoose','Monkey','Lion']) to_key;
      INSERT INTO reference_nakshatra_matrix SELECT 'varna_kuta',from_key,to_key
        FROM unnest(ARRAY['Brahmin','Kshatriya','Vaishya','Shudra','Farmer','Butcher','Mleccha']) from_key
        CROSS JOIN unnest(ARRAY['Brahmin','Kshatriya','Vaishya','Shudra','Farmer','Butcher','Mleccha']) to_key;
      INSERT INTO reference_nakshatra_matrix SELECT 'graha_maitri_kuta',from_key,to_key
        FROM unnest(ARRAY['sun','moon','mars','mercury','jupiter','venus','saturn']) from_key
        CROSS JOIN unnest(ARRAY['sun','moon','mars','mercury','jupiter','venus','saturn']) to_key;
      INSERT INTO reference_nakshatra_matrix SELECT 'vashya_kuta',from_key,to_key
        FROM unnest(ARRAY['Dwipada','Chaturpada','Jalasheela','Keeta','Vanachara']) from_key
        CROSS JOIN unnest(ARRAY['Dwipada','Chaturpada','Jalasheela','Keeta','Vanachara']) to_key;
      INSERT INTO reference_nakshatra_matrix SELECT matrix_type,from_key::text,to_key::text
        FROM unnest(ARRAY['tara_kuta','mahendra','stree_deergha']) matrix_type
        CROSS JOIN generate_series(1,27) from_key CROSS JOIN generate_series(1,27) to_key;
      INSERT INTO reference_nakshatra_matrix SELECT 'bhakoot_kuta',from_key::text,to_key::text
        FROM generate_series(1,12) from_key CROSS JOIN generate_series(1,12) to_key;
      INSERT INTO reference_nakshatra_matrix(matrix_type,from_key,to_key) VALUES
        ('rajju','1','Kantha_Avaroha'),('rajju','2','Padha_Aroha'),('rajju','3','Kati_Aroha'),
        ('rajju','4','Nabhi_Aroha'),('rajju','5','Kantha_Aroha'),('rajju','6','Padha_Avaroha'),
        ('rajju','7','Kati_Avaroha'),('rajju','8','Nabhi_Avaroha'),('rajju','9','Kantha_Aroha'),
        ('rajju','10','Shira'),('rajju','11','Padha_Avaroha'),('rajju','12','Kati_Avaroha'),
        ('rajju','13','Nabhi_Avaroha'),('rajju','14','Nabhi_Aroha'),('rajju','15','Kati_Aroha'),
        ('rajju','16','Padha_Aroha'),('rajju','17','Shira'),('rajju','18','Kantha_Aroha'),
        ('rajju','19','Nabhi_Aroha'),('rajju','20','Kati_Aroha'),('rajju','21','Padha_Aroha'),
        ('rajju','22','Kantha_Avaroha'),('rajju','23','Shira'),('rajju','24','Kantha_Avaroha'),
        ('rajju','25','Nabhi_Avaroha'),('rajju','26','Kati_Avaroha'),('rajju','27','Padha_Avaroha');
      INSERT INTO reference_nakshatra_matrix(matrix_type,from_key,to_key) VALUES
        ('vedha','1','16'),('vedha','2','15'),('vedha','3','14'),('vedha','4','13'),
        ('vedha','5','12'),('vedha','6','11'),('vedha','7','10'),('vedha','8','9'),
        ('vedha','9','8'),('vedha','10','7'),('vedha','11','6'),('vedha','12','5'),
        ('vedha','13','4'),('vedha','14','3'),('vedha','15','2'),('vedha','16','1'),
        ('vedha','17','27'),('vedha','18','26'),('vedha','19','25'),('vedha','20','24'),
        ('vedha','21','23'),('vedha','23','21'),('vedha','24','20'),('vedha','25','19'),
        ('vedha','26','18'),('vedha','27','17');

      CREATE TEMP TABLE bg_dignity_reference (graha text);
      INSERT INTO bg_dignity_reference SELECT graha FROM unnest(ARRAY['Jupiter','Ketu','Mars','Mercury','Moon','Rahu','Saturn','Sun','Venus']) graha;
      CREATE TEMP TABLE bg_graha_naisargika_friendship (graha text, other_graha text, relation text);
      INSERT INTO bg_graha_naisargika_friendship
      SELECT graha, other_graha, 'neutral'
      FROM unnest(ARRAY['Jupiter','Ketu','Mars','Mercury','Moon','Rahu','Saturn','Sun','Venus']) graha
      CROSS JOIN unnest(ARRAY['Jupiter','Ketu','Mars','Mercury','Moon','Rahu','Saturn','Sun','Venus']) other_graha
      WHERE graha <> other_graha;
      CREATE TEMP TABLE bg_avastha_schemes (scheme_name text, state_name text);
      INSERT INTO bg_avastha_schemes VALUES
        ('baladi','bala'),('baladi','kumara'),('baladi','mrita'),('baladi','vriddha'),('baladi','yuva'),
        ('deeptaadi','deepta'),('deeptaadi','dina'),('deeptaadi','khala'),('deeptaadi','mudita'),
        ('deeptaadi','peedit'),('deeptaadi','shakta'),('deeptaadi','shanta'),('deeptaadi','swastha'),('deeptaadi','vikala'),
        ('jagradadi','jagrata'),('jagradadi','sushupti'),('jagradadi','svapna'),
        ('lajjitaadi','garvita'),('lajjitaadi','kshobhita'),('lajjitaadi','kshudhita'),
        ('lajjitaadi','lajjita'),('lajjitaadi','mudita'),('lajjitaadi','trishita'),
        ('sayanadi','agama'),('sayanadi','agamana'),('sayanadi','bhojanaprapta'),('sayanadi','deeptamsa'),
        ('sayanadi','gamana'),('sayanadi','kautuka'),('sayanadi','netrapani'),('sayanadi','nidraksita'),
        ('sayanadi','prakasana'),('sayanadi','sabha'),('sayanadi','sayana'),('sayanadi','upavesana');
      CREATE TEMP TABLE bg_motion_state_thresholds (graha text, motion_state text);
      INSERT INTO bg_motion_state_thresholds VALUES
        ('Jupiter','anuvakra'),('Jupiter','atichara'),('Jupiter','sama'),('Jupiter','vakra'),
        ('Ketu','vakra'),
        ('Mars','anuvakra'),('Mars','atichara'),('Mars','manda'),('Mars','sama'),('Mars','vakra'),
        ('Mercury','anuvakra'),('Mercury','atichara'),('Mercury','sama'),('Mercury','vakra'),
        ('Moon','atichara'),('Moon','sama'),('Rahu','vakra'),
        ('Saturn','anuvakra'),('Saturn','atichara'),('Saturn','sama'),('Saturn','vakra'),
        ('Sun','atichara'),('Sun','sama'),
        ('Venus','anuvakra'),('Venus','atichara'),('Venus','sama'),('Venus','vakra');
      CREATE TEMP TABLE bg_combustion_orbs (graha text);
      INSERT INTO bg_combustion_orbs SELECT graha FROM unnest(ARRAY['Jupiter','Ketu','Mars','Mercury','Moon','Rahu','Saturn','Venus']) graha;
    `)
  }

  async function detector(client: Client, assetId: string): Promise<boolean> {
    const contract = await client.query<{ integrity_check_sql: string }>(
      'SELECT integrity_check_sql FROM asset_registry WHERE asset_id = $1',
      [assetId],
    )
    const result = await client.query(contract.rows[0].integrity_check_sql)
    return Object.values(result.rows[0])[0] === true
  }

  it('installs and replays exact contracts, and every healthy detector returns one truthy row', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await client.query(migration)
      await installHealthyFixtures(client)
      for (const assetId of ASSET_IDS) expect(await detector(client, assetId)).toBe(true)
      const ontology = await client.query(
        `SELECT target_floor, volume_explanation FROM asset_registry WHERE asset_id = 'bg_ontology'`,
      )
      expect(ontology.rows).toEqual([{ target_floor: '737', volume_explanation: ONTOLOGY_EXPLANATION }])
    } finally {
      await client.end()
    }
  }, 30_000)

  it('makes each detector fire on a representative structural corruption', async () => {
    const client = await connectPrepared()
    try {
      await client.query(migration)
      await installHealthyFixtures(client)
      const corruptions = [
        ['bg_cohort', 'DELETE FROM bg_synthetic_cohort_md WHERE synthetic_id = 1 AND md_index IN (9,10)'],
        ['bg_cohort', 'UPDATE bg_synthetic_cohort SET synthetic_id = 10001 WHERE synthetic_id = 1; UPDATE bg_synthetic_cohort_md SET synthetic_id = 10001 WHERE synthetic_id = 1'],
        ['bg_cohort', "UPDATE bg_synthetic_cohort SET positions = positions - 'Lagna' WHERE synthetic_id = 1"],
        ['bg_cohort', "UPDATE bg_synthetic_cohort SET positions = jsonb_set(positions, '{Sun}', 'null'::jsonb) WHERE synthetic_id = 1"],
        ['bg_cohort', "UPDATE bg_synthetic_cohort SET positions = jsonb_set(positions, '{Sun}', (positions->'Sun') - 'sign_id') WHERE synthetic_id = 1"],
        ['bg_ontology', "UPDATE brahma_ontology SET canonical_id = 'unexpected_nakshatra' WHERE canonical_id = 'nak_01_ashwini'"],
        ['bg_ephemeris', "DELETE FROM ephemeris_daily WHERE date = DATE '1900-01-01' AND body = 'Sun'"],
        ['bg_nakshatra', "UPDATE reference_nakshatra_matrix SET from_key='99' WHERE matrix_type='tara_kuta' AND from_key='1' AND to_key='1'"],
        ['bg_dignity_reference', "UPDATE bg_dignity_reference SET graha = 'Pluto' WHERE graha = 'Sun'"],
        ['bg_dignity_reference', "UPDATE bg_graha_naisargika_friendship SET other_graha = 'Pluto' WHERE ctid IN (SELECT ctid FROM bg_graha_naisargika_friendship LIMIT 1)"],
        ['bg_dignity_reference', "UPDATE bg_motion_state_thresholds SET motion_state = 'unexpected' WHERE graha = 'Sun' AND motion_state = 'sama'"],
        ['bg_dignity_reference', "UPDATE bg_avastha_schemes SET state_name = 'unexpected' WHERE scheme_name = 'baladi' AND state_name = 'bala'"],
        ['bg_dignity_reference', "UPDATE bg_combustion_orbs SET graha = 'Sun' WHERE graha = 'Venus'"],
      ] as const
      await client.query('BEGIN')
      for (const [assetId, corruption] of corruptions) {
        await client.query('SAVEPOINT detector_corruption')
        await client.query(corruption)
        expect(await detector(client, assetId)).toBe(false)
        await client.query('ROLLBACK TO SAVEPOINT detector_corruption')
      }
      await client.query('ROLLBACK')
    } finally {
      await client.end()
    }
  }, 30_000)

  it('rejects unknown registry drift without partially installing contracts', async () => {
    const client = await connectPrepared()
    try {
      await client.query("UPDATE asset_registry SET sort_order = 999 WHERE asset_id = 'bg_ontology'")
      await expect(client.query(migration)).rejects.toThrow(
        'migration 606 refuses unknown bg_ontology registry contract',
      )
      const result = await client.query(
        'SELECT count(*)::int AS count FROM asset_registry WHERE integrity_check_sql IS NOT NULL',
      )
      expect(result.rows).toEqual([{ count: 0 }])
    } finally {
      await client.end()
    }
  })
})

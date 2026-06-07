-- Brahmagyan naming reconciliation — drop legacy long-form rows, install 8 canonical bg_* rows.
-- Phase 1 of BRAHMAGYAN_NAMING_RECONCILIATION_v1_0
-- Reversible via the down-migration at the bottom.
BEGIN;

-- Step 0: Remove asset_coefficients rows referencing legacy brahmagyan IDs
-- (will be re-inserted with canonical IDs after the new asset_registry rows are in)
DELETE FROM asset_coefficients
  WHERE upstream_asset_id LIKE 'brahmagyan.%' OR downstream_asset_id LIKE 'brahmagyan.%';

-- Step 1: Remove legacy entries (long-form IDs + dropped concepts)
DELETE FROM asset_registry WHERE layer = 'brahmagyan' AND asset_id IN (
  'brahmagyan.kalapancanga',
  'brahmagyan.sarani',
  'brahmagyan.sutravali',
  'brahmagyan.samanvaya',
  'brahmagyan.sensitive_point_catalog',
  'brahmagyan.shastra',
  'brahmagyan.upaya_kosha',
  'brahmagyan.panchanga_almanac',
  'brahmagyan.text_index'
);

-- Step 2: Install 8 canonical bg_* rows
INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, target_table, count_sql, size_sql, target_floor, expected_volume_formula, volume_explanation, depends_on, scope, is_active) VALUES
  ('bg_ephemeris', 'brahmagyan', 1, 'Graha-sphuṭa', 'Ephemeris (Graha Sphuṭa)',
   'Swiss Ephemeris DE441 — raw astronomical positions for all grahas',
   'postgres_table', 'ephemeris_daily',
   'SELECT count(*) FROM ephemeris_daily',
   'SELECT pg_total_relation_size(''ephemeris_daily'')',
   29200, 'GRAHAS * DATE_RANGE_DAYS',
   '9 grahas × date-range days — structural, no upstream dependency',
   ARRAY[]::text[], 'global', true),

  ('bg_reference', 'brahmagyan', 2, 'Sāraṇī', 'Reference Library',
   'Five reference tables: planets, nakshatras, signs, aspects, vargas — classical constants',
   'postgres_table', 'reference_nakshatras',
   'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_nakshatras) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) AS count',
   'SELECT pg_total_relation_size(''reference_nakshatras'')',
   NULL, NULL,
   'Sum of 5 reference table row counts — established at seed; static thereafter',
   ARRAY[]::text[], 'global', true),

  ('bg_texts', 'brahmagyan', 3, 'Śāstrapāṭha', 'Classical Texts',
   'Indexed verse chunks from BPHS, Jaimini Sutram, KP Reader, Tajaka, Phaladeepika, etc.',
   'postgres_table', 'classical_text_chunks',
   'SELECT count(*) FROM classical_text_chunks',
   'SELECT pg_total_relation_size(''classical_text_chunks'')',
   NULL, NULL,
   'Empirical writer output from text ingestion (Stream C); first ingest establishes the count',
   ARRAY[]::text[], 'global', true),

  ('bg_ontology', 'brahmagyan', 4, 'Nāmasaṃgraha', 'Ontology',
   'Canonical entity vocabulary — grahas, signs, houses, nakshatras, dashas, domains + synonyms',
   'postgres_table', 'brahma_ontology',
   'SELECT count(*) FROM brahma_ontology',
   'SELECT pg_total_relation_size(''brahma_ontology'')',
   NULL, NULL,
   'Static vocabulary — count established at seed; used by resolve_entity retrieval tool',
   ARRAY[]::text[], 'global', true),

  ('bg_text_index', 'brahmagyan', 5, 'Śabdakośa', 'Text Index',
   'Embedded subset of classical_text_chunks for hybrid retrieval (vector + lexical + rerank)',
   'postgres_table', 'classical_text_chunks',
   'SELECT count(*) FROM classical_text_chunks WHERE embedding IS NOT NULL',
   'SELECT pg_total_relation_size(''classical_text_chunks'')',
   NULL, NULL,
   'Subset of bg_texts where embedding column is populated — count grows with ingestion',
   ARRAY['bg_texts']::text[], 'global', true),

  ('bg_rules', 'brahmagyan', 6, 'Sūtravālī', 'Rule Base',
   'Classical rules extracted from text chunks via Python regex patterns — verse-traceable',
   'postgres_table', 'sutravali_rules',
   'SELECT count(*) FROM sutravali_rules',
   'SELECT pg_total_relation_size(''sutravali_rules'')',
   NULL, NULL,
   'Empirical writer output from Stream D (regex extraction); count grows with pattern library',
   ARRAY['bg_texts']::text[], 'global', true),

  ('bg_remedies', 'brahmagyan', 7, 'Upāya-kośa', 'Remedy Corpus',
   'Classical remedies: mantras, gemstones, charity, vrata, yantras, puja, tantric, ayurvedic, vastu, behavioral',
   'postgres_table', 'brahma_remedy_corpus',
   'SELECT count(*) FROM brahma_remedy_corpus',
   'SELECT pg_total_relation_size(''brahma_remedy_corpus'')',
   NULL, NULL,
   'YAML-curated corpus loaded via Python; grows with native authoring',
   ARRAY[]::text[], 'global', true),

  ('bg_concordance', 'brahmagyan', 8, 'Samanvaya', 'Concordance',
   'Cross-school agreement/divergence index (BPHS vs Jaimini vs Tajaka vs KP per topic) — DORMANT placeholder',
   'postgres_table', 'classical_attributions',
   'SELECT count(*) FROM classical_attributions',
   'SELECT pg_total_relation_size(''classical_attributions'')',
   NULL, NULL,
   'Future build — registered as dormant. The classical_attributions table is a stub until cross-school divergence work begins.',
   ARRAY['bg_texts']::text[], 'global', true);

-- Step 3: Re-insert asset_coefficients with canonical IDs (where target assets exist)
-- brahmagyan.sutravali → bodha.laksana  becomes  bg_rules → bodha.laksana
-- brahmagyan.kalapancanga → kala.kalasutra  becomes  bg_ephemeris → kala.kalasutra
-- brahmagyan.sutravali → brahmagyan.samanvaya  becomes  bg_rules → bg_concordance
INSERT INTO asset_coefficients (coefficient_name, description, upstream_asset_id, downstream_asset_id)
SELECT 'SIGNAL_PER_RULE',
       'Signals produced per classical rule per ayanamsha set (measured first build)',
       'bg_rules', 'bodha.laksana'
WHERE EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'bodha.laksana')
ON CONFLICT (coefficient_name) DO NOTHING;

INSERT INTO asset_coefficients (coefficient_name, description, upstream_asset_id, downstream_asset_id)
SELECT 'TRANSITS_PER_DAY',
       'Major-aspect transit events per calendar day across the ephemeris range (measured first build)',
       'bg_ephemeris', 'kala.kalasutra'
WHERE EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'kala.kalasutra')
ON CONFLICT (coefficient_name) DO NOTHING;

INSERT INTO asset_coefficients (coefficient_name, description, upstream_asset_id, downstream_asset_id)
VALUES ('CONCORDANCE_DENSITY',
        'Concordance attribution topics per classical rule (measured first build)',
        'bg_rules', 'bg_concordance')
ON CONFLICT (coefficient_name) DO NOTHING;

COMMIT;

-- Down migration (manual; preserves prior state for rollback)
-- DELETE FROM asset_registry WHERE layer='brahmagyan' AND asset_id LIKE 'bg_%';
-- (Then re-run the prior seed script to restore long-form entries.)

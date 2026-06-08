-- L0 Phase α: asset_registry updates per design §1, §2.2, §3.2
-- (L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md v1.1)
BEGIN;

-- §2.2 — Fix bg_text_index count_sql to measure topic-tag coverage (not embedded chunk count)
-- Retrieval tools point at bg_texts; bg_text_index reports the index coverage metric.
UPDATE asset_registry SET
  count_sql = 'SELECT count(DISTINCT topic_tag) AS count FROM classical_text_chunks WHERE embedding IS NOT NULL AND topic_tag IS NOT NULL',
  english_description = 'Measurement of retrieval index health — distinct topic tags across embedded + indexed chunks. Retrieval tools point at bg_texts; this asset reports the index coverage metric.',
  volume_explanation = 'Distinct topic_tag count from embedded chunks. Per design §2.2: retrieval tools never reference bg_text_index directly; they go through bg_texts.'
WHERE asset_id = 'bg_text_index';

-- §3.2 — Update bg_reference count_sql to sum all 15 reference_* tables
-- (was: 5 original tables; now: original 5 + 7 standalone + 3 pointer tables = 15)
UPDATE asset_registry SET
  count_sql = 'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_nakshatras) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) + (SELECT count(*) FROM reference_yogas) + (SELECT count(*) FROM reference_doshas) + (SELECT count(*) FROM reference_dasha_systems) AS count',
  english_description = 'The holy grail of L0 — structured properties of every classical Jyotish concept across 15 specialized typed tables.',
  volume_explanation = 'Sum of 15 reference_* tables (per design §3.2). Each table is normalized + typed; ontology resolves names, reference holds properties.'
WHERE asset_id = 'bg_reference';

-- Register 4 new L0 assets
INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, target_table, count_sql, size_sql, target_floor, expected_volume_formula, expected_volume_inputs, volume_explanation, depends_on, scope, is_active, estimated_seconds)
VALUES
  ('bg_yogas', 'brahmagyan', 9,
   'Yoga-saṃgraha', 'Yoga Catalog',
   'Classical yoga definitions — formation rules, significations, classical citations',
   'postgres_table', 'brahma_yoga_catalog',
   'SELECT count(*) FROM brahma_yoga_catalog',
   'SELECT pg_total_relation_size(''brahma_yoga_catalog'')',
   200, NULL, NULL,
   'Catalog of named yoga patterns from BPHS / Saravali / Phaladeepika / Jaimini per design §3.9',
   ARRAY['bg_ontology']::text[], 'global', true, NULL),

  ('bg_dasha_systems', 'brahmagyan', 10,
   'Daśā-paddhati', 'Dasha Systems',
   'Classical dasha system definitions — sequence rules, computation methods, conditions for use',
   'postgres_table', 'brahma_dasha_systems',
   'SELECT count(*) FROM brahma_dasha_systems',
   'SELECT pg_total_relation_size(''brahma_dasha_systems'')',
   15, NULL, NULL,
   '15-20 named dasha systems (Vimshottari, Yogini, Chara, Kalachakra, etc.) per design §3.10',
   ARRAY['bg_ontology']::text[], 'global', true, NULL),

  ('bg_doshas', 'brahmagyan', 11,
   'Doṣa-kośa', 'Dosha Catalog',
   'Classical dosha definitions — formation rules, effects, severity, cancellation conditions',
   'postgres_table', 'brahma_dosha_catalog',
   'SELECT count(*) FROM brahma_dosha_catalog',
   'SELECT pg_total_relation_size(''brahma_dosha_catalog'')',
   50, NULL, NULL,
   'Catalog of named dosha patterns (Manglik, Kala-sarpa, Kemadruma, etc.) per design §3.11',
   ARRAY['bg_ontology']::text[], 'global', true, NULL),

  ('bg_compendium_index', 'brahmagyan', 12,
   'Anukrama', 'Compendium Index',
   'Cross-reference index over the 15 classical texts — chapter summaries, topic-coverage map, significance scores',
   'postgres_table', 'brahma_compendium_index',
   'SELECT count(*) FROM brahma_compendium_index',
   'SELECT pg_total_relation_size(''brahma_compendium_index'')',
   3000, NULL, NULL,
   '~3,000-5,000 index rows: per-text-per-chapter + per-text-per-topic-tag per design §3.12',
   ARRAY['bg_texts','reference_topic_tags']::text[], 'global', true, NULL);

COMMIT;

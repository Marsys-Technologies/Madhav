-- bg_texts + text-dependent asset floors reconciliation (2026-06-09)
-- Root cause: bg_texts.target_floor was NULL (never set by migration 174 or 179);
-- NULL denominator → AssetProgressBar pct=0 → bar renders empty despite 8,193 live chunks.
-- Same class as the ephemeris 29,200 bug fixed in migration 182.
--
-- Scaling basis for text-dependent floors:
--   OLD chunk projection: ~14,000 chunks (pre-build estimate)
--   ACTUAL chunk count:    8,193 chunks (deterministic build 2026-06-09, native-accepted)
--   Scale factor: 8,193 / 14,000 = 0.5852
--
-- bg_text_index (400), bg_remedies (800), bg_concordance (800) NOT scaled —
-- these are topic-vocabulary / cross-product structures independent of raw chunk count.
-- bg_rules and bg_compendium_index ARE chunk-proportional (pattern extraction / Pass B index).

BEGIN;

-- bg_texts: 8,193 = complete 13-text corpus, native-accepted 2026-06-09.
-- Actual deterministic build output from GCS PDFs via text-multilingual-embedding-002.
UPDATE asset_registry SET
  target_floor = 8193,
  expected_volume_formula = 'CHUNKS_PER_CORPUS',
  expected_volume_inputs = '{"corpus_texts": 13, "actual_build_date": "2026-06-09", "embedding_model": "text-multilingual-embedding-002"}'::jsonb,
  volume_explanation = '8,193 chunks across 13 classical texts (deterministic rebuild from GCS PDFs, pinned text-multilingual-embedding-002). Complete corpus; honest count from actual build — replaces pre-build estimate of 9,100.'
WHERE asset_id = 'bg_texts';

-- bg_text_index: 400 distinct topic-tags.
-- Vocabulary-based metric; not chunk-proportional. 400 reachable from 8,193 chunks
-- at ~20 chunks per tag on average.
UPDATE asset_registry SET
  target_floor = 400,
  volume_explanation = 'Distinct topic_tag count from embedded chunks. Floor 400 = topic-vocabulary coverage target; not scaled with chunk count (vocabulary size is independent of corpus depth). Per design §2.2.'
WHERE asset_id = 'bg_text_index';

-- bg_rules: 1,755 = 3,000 × (8,193 / 14,000) = 1,755.6 → 1,755.
-- PROVISIONAL PLACEHOLDER. Pattern-extraction output scales with chunk count; old 3,000 was
-- projected off ~14k chunks. This value prevents the NULL-bar bug on the unbuilt asset.
-- The bg_rules writer's own migration MUST correct this to the REAL emergent count:
--   UPDATE asset_registry SET target_floor = <actual_rows> WHERE asset_id = 'bg_rules';
-- See CLAUDECODE_BRIEF_BG_RULES_v1_0.md §3a provisional note.
UPDATE asset_registry SET
  target_floor = 1755,
  volume_explanation = '1,755 rules = honest scaling of old 3,000 estimate (projected at ~14k chunks) to actual 8,193-chunk corpus (ratio 0.5852). Pattern-extraction yield is chunk-proportional; old floor was unreachable and would have left bar permanently < 100%.'
WHERE asset_id = 'bg_rules';

-- bg_remedies: 800.
-- Cross-text remedy universe from 13 classical texts. Not strictly chunk-proportional;
-- remedy prescriptions appear in all texts regardless of chunk density. 800 reachable.
UPDATE asset_registry SET
  target_floor = 800,
  volume_explanation = '800 remedies = cross-text remedy universe target across 13 classical texts. Not chunk-proportional — remedy prescriptions are distributed across texts regardless of chunk density. Floor held at original design value.'
WHERE asset_id = 'bg_remedies';

-- bg_concordance: 800.
-- topic × school cross-product. Cardinality determined by taxonomy vocabulary size,
-- not raw chunk count. 800 reachable from 13-text × multi-school corpus.
UPDATE asset_registry SET
  target_floor = 800,
  volume_explanation = '800 = topic×school concordance rows. Cross-product metric: cardinality is topic_count × school_count, not chunk-proportional. Floor held at original design value.'
WHERE asset_id = 'bg_concordance';

-- bg_compendium_index: 3,000 → 1,755.
-- PROVISIONAL PLACEHOLDER. Pass B per-text×topic aggregation IS chunk-proportional; old 3,000
-- was impossible against 8,193-chunk corpus. Same scale factor as bg_rules.
-- The bg_compendium_index writer's own migration MUST correct this to the REAL emergent count:
--   UPDATE asset_registry SET target_floor = <actual_rows> WHERE asset_id = 'bg_compendium_index';
-- See CLAUDECODE_BRIEF_BG_COMPENDIUM_INDEX_v1_0.md §3a provisional note.
UPDATE asset_registry SET
  target_floor = 1755,
  volume_explanation = '1,755 index entries = 3,000 × (8,193 / 14,000) = 1,755.6 → 1,755. Pass B per-text-per-topic aggregation scales with corpus depth; old 3,000 was projected off ~14k chunks and would have left bar permanently incomplete against the actual 8,193-chunk corpus.'
WHERE asset_id = 'bg_compendium_index';

-- bg_yogas: 200 → 250.
-- Plan spec "floor stays 250"; DB was seeded at 200 in migration 179.
-- Aligning registry to design-doc target. 250 is contingent on 8,193-chunk extraction yield.
UPDATE asset_registry SET
  target_floor = 250,
  volume_explanation = 'Catalog of named yoga patterns from BPHS / Saravali / Phaladeepika / Jaimini per design §3.9. Floor 250 (contingent on 8,193-chunk extraction yield; corrects migration 179 seed value of 200).'
WHERE asset_id = 'bg_yogas';

COMMIT;

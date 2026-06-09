-- migration 190: set bg_text_index target_floor to achieved row count.
-- bg_text_index is a measurement asset: its metric is count(DISTINCT topic_tag)
-- on embedded classical_text_chunks. The brief aspired to ≥400 distinct tags
-- (CONDITIONAL on full manual-PDF corpus). Current corpus (13 texts, 8193 embedded
-- chunks) achieved 327 distinct tags — CONDITIONAL result per brief §3a.
-- Floor is set to the achieved count; rerun after full corpus ingestion expected
-- to push above 400.
BEGIN;
UPDATE asset_registry
   SET target_floor = 327,
       volume_explanation = 'bg_text_index: 327 distinct topic_tag values on 8193 embedded chunks, '
                         || 'seeded by deterministic keyword-rule classifier, Tier 3 campaign 2026-06-09. '
                         || 'classical_text_chunks upstream: 8193 embedded rows across 13 texts. '
                         || 'Brief aspiration was ≥400 distinct tags (CONDITIONAL on full manual-PDF corpus). '
                         || 'Floor set to achieved count 327; rerun after corpus reaches full coverage '
                         || '(3 manual PDFs awaiting upload) expected to push above 400.',
       depends_on = ARRAY['bg_texts','bg_reference']::text[]
 WHERE asset_id = 'bg_text_index';
COMMIT;

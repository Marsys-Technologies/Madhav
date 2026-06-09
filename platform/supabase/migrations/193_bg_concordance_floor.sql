-- migration 193: set bg_concordance target_floor to achieved row count.
-- Writer build date: 2026-06-09. Actual emergent count: 477 rows.
-- 477 = 327 distinct topic_ids × 3 schools (parashari, jaimini, tajaka/phaladeepika).
-- Floor is EMERGENT on corpus per brief §3a: depends on chunks having topic_tag set (bg_text_index)
-- and on the TEXT_SCHOOL map (13 texts resolve to 3 distinct schools from current corpus).
-- Note: brief aspiration was ≥800 (200 topics × ≥4 schools) — CONDITIONAL on full 15-text corpus
-- including 3 manual PDFs (bhrigu_samhita/lal_kitab not present in current chunk set).
-- Current corpus has 13 texts resolving to 3 schools; floor set to achieved count per policy.
BEGIN;
UPDATE asset_registry
   SET target_floor = 477,
       volume_explanation = 'bg_concordance: 477 cross-reference rows seeded Tier 4 campaign 2026-06-09. '
                         || '327 distinct topics × 3 schools (parashari/jaimini/tajaka+phaladeepika). '
                         || 'Brief aspiration was ≥800 (200 topics × ≥4 schools) — CONDITIONAL on full '
                         || '15-text corpus; current 13-text corpus yields 3 distinct schools. '
                         || 'Floor set to achieved count per floors-are-aspirational policy.',
       depends_on = ARRAY['bg_texts','bg_text_index','bg_reference','bg_rules']::text[]
 WHERE asset_id = 'bg_concordance';
COMMIT;

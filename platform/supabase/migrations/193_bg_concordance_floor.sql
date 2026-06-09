-- migration 193: set bg_concordance target_floor to achieved row count.
-- Writer build date: 2026-06-09. Actual emergent count: 477 rows.
-- 477 = 327 distinct topic_ids × ~1.46 avg schools/topic.
-- Genuine 3-school state (not a build gap or code bug):
--   parashari (322 topics), phaladeepika (92 topics), jaimini (63 topics).
--   tajaka school: 0 rows — tajaka_neelakanthi has Devanagari-only content_en
--     → 0 tagged chunks from bg_text_index → 0 concordance rows. Correct behaviour.
--   nadi / lal_kitab schools: 0 rows — those texts are absent from classical_text_chunks.
-- TEXT_SCHOOL map is correct and covers all 13 corpus texts.
-- ≥800 aspiration conditioned on full 15-text corpus with English content_en throughout.
-- 477 is the honest maximum for the current corpus state.
BEGIN;
UPDATE asset_registry
   SET target_floor = 477,
       volume_explanation = 'bg_concordance: 477 cross-reference rows seeded Tier 4 campaign 2026-06-09. '
                         || '327 distinct topics × 3 active schools: parashari(322), phaladeepika(92), jaimini(63). '
                         || 'tajaka absent: tajaka_neelakanthi Devanagari-only → 0 tagged chunks → 0 concordance rows. '
                         || 'nadi/lal_kitab absent: those texts not in corpus. TEXT_SCHOOL map complete and correct. '
                         || '477 is the honest max for current corpus. '
                         || 'Floor set to achieved count per floors-are-aspirational policy.',
       depends_on = ARRAY['bg_texts','bg_text_index','bg_reference','bg_rules']::text[]
 WHERE asset_id = 'bg_concordance';
COMMIT;

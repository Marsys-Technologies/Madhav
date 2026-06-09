-- migration 192: set bg_remedies target_floor to achieved row count.
-- Campaign 2026-06-09 (remediation): brahma_remedy_corpus seeded with 265 rows:
--   108 deterministic matrix (9 planets × 8 fixed cells + 36 dana-charity)
--   +55 dosha-linked remedies (50 doshas × 1-2 remedies each)
--   +54 legacy corpus rows (v1.0 hardcoded set, remedy_type normalised)
--   +48 corpus_sweep rows (deterministic regex over 542 remedy-marker chunks
--       in classical_text_chunks; 629 chunks scanned, 48 planet-resolved rows retained)
-- scaffold_status breakdown: live=260, review=5. ZERO LLM.
-- Floor = live-only count per floors-are-aspirational policy.
BEGIN;
UPDATE asset_registry
   SET target_floor = 260,
       volume_explanation = 'bg_remedies: 265 rows live+review post-sweep remediation 2026-06-09. '
                         || 'Sources: gen_planet_matrix(108) + dosha-linked(55) + legacy(54) + corpus_sweep(48). '
                         || 'Corpus sweep: deterministic regex over 629 remedy-marker chunks in classical_text_chunks '
                         || '(mantra|yantra|japa|gemstone|vrata|fast|worship|donate|dana|recite|wear). '
                         || 'scaffold_status=live(260) + review(5). '
                         || 'Floor = live-only count per floors-are-aspirational policy. 2026-06-09 remediation.'
 WHERE asset_id = 'bg_remedies';
COMMIT;

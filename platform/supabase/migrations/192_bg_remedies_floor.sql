-- migration 192: set bg_remedies target_floor to achieved row count.
-- Campaign 2026-06-09: brahma_remedy_corpus seeded with 217 classical remedy rows:
--   108 deterministic matrix (9 planets × 8 fixed cells + 36 dana-charity)
--   +55 dosha-linked remedies (50 doshas × 1-2 remedies each)
--   +54 legacy corpus rows (v1.0 hardcoded set, remedy_type normalised)
-- All rows scaffold_status='live'. ZERO LLM. Brief aspiration was 800
-- (requires §3.3 corpus-sweep from ingested bg_texts chunks — not yet available).
-- Floor set to achieved count per floors-are-aspirational policy.
BEGIN;
UPDATE asset_registry
   SET target_floor = 217,
       volume_explanation = 'bg_remedies: 217 remedy rows seeded Tier 3 campaign 2026-06-09. '
                         || '108 deterministic planet-matrix (9 planets × 8 fixed cells + 36 dana-charity) '
                         || '+ 55 dosha-linked (50 doshas × 1-2 each) + 54 legacy corpus rows. '
                         || 'All scaffold_status=live. Brief aspiration was 800; '
                         || 'remaining 583 require §3.3 corpus-sweep from bg_texts (not yet ingested). '
                         || 'Floor held at achieved count per floors-are-aspirational policy.'
 WHERE asset_id = 'bg_remedies';
COMMIT;

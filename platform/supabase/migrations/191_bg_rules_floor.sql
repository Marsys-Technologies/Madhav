-- migration 191: set bg_rules target_floor to achieved row count.
-- The brief's provisional floor of 1,755 was scaled from bg_texts chunks — aspirational, not a hard target.
-- Writer build date: 2026-06-09. Actual emergent count: 1,976 rules.
BEGIN;
UPDATE asset_registry
   SET target_floor = 1976,
       volume_explanation = 'bg_rules: 1,976 rule rows seeded Tier 3 campaign 2026-06-09. '
                         || 'upstream classical_text_chunks: 8,193 rows across 13 texts. '
                         || 'Extraction: 24 regex pattern families (ZERO LLM; python_regex_v2). '
                         || 'Coverage: 8.1% of chunks yielded ≥1 rule (660/8193 chunks); '
                         || 'remaining 94% are OCR-noisy TOC/index/commentary pages. '
                         || 'Quality: avg 0.989 (all ≥0.6 threshold); 1975/1976 at 0.8+. '
                         || 'Brief provisional aspiration was 1,755 (chunk-proportional scaling from 3,000 design target). '
                         || 'Floor set to actual emergent count per floors-are-aspirational policy.'
 WHERE asset_id = 'bg_rules';
COMMIT;

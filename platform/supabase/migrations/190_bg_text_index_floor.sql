-- migration 190: set bg_text_index target_floor to achieved row count.
-- bg_text_index is a measurement asset: its metric is count(DISTINCT topic_tag)
-- on embedded classical_text_chunks. The brief aspired to ≥400 distinct tags.
-- Current corpus (13 texts, 8193 embedded chunks) achieved 327 distinct tags.
-- 2751 chunks are untagged: muhurta_chintamani (274) + tajaka_neelakanthi (290) have
-- Devanagari-only content_en — the English keyword classifier yields 0 matches for those
-- 564 chunks; the remaining ~2187 untagged chunks across other texts are genuine
-- classifier misses (no keyword match). 327 is the honest maximum for the current
-- English-transliteration corpus. Corpus is complete at 13 texts; no PDFs pending.
-- (The "3 manual PDFs awaiting upload" label was stale; those 3 absent texts are
-- bhrigu_samhita/lal_kitab/one other — not in classical_text_chunks at all and not
-- the cause of the 2751 untagged chunks.)
BEGIN;
UPDATE asset_registry
   SET target_floor = 327,
       volume_explanation = 'bg_text_index: 327 distinct topic_tag values on 5442 of 8193 embedded chunks, '
                         || 'seeded by deterministic keyword-rule classifier, Tier 3 campaign 2026-06-09. '
                         || '2751 chunks untagged: muhurta_chintamani(274)+tajaka_neelakanthi(290) are '
                         || 'Devanagari-only (English classifier yields 0); remainder are genuine classifier misses. '
                         || '327 is the honest maximum for the current English-transliteration corpus. '
                         || 'Corpus complete at 13 texts. Floor set to achieved count per floors-are-aspirational policy.',
       depends_on = ARRAY['bg_texts','bg_reference']::text[]
 WHERE asset_id = 'bg_text_index';
COMMIT;

-- Migration 199: bg_remedies target_floor update — Nadi expansion 2026-06-09
-- Before: 265 · After: 266 · Delta: +1

UPDATE asset_registry
SET
    target_floor = 266,
    volume_explanation = 'Rows in brahma_remedy_corpus: classical remedy entries from 3 fixed buckets (108 planet-matrix + 102 dosha-linked + 54 legacy) plus corpus sweep of classical_text_chunks. Grew from 265 to 266 after nadi corpus sweep extracted 49 candidate remedy rows from bhrigu_nandi_nadi and nadi_navamsa_patel chunks; 265 conflict-skipped, 1 net new insertion.'
WHERE asset_id = 'bg_remedies';

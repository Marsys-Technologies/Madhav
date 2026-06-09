-- Migration 196: bg_text_index target_floor update — Nadi expansion 2026-06-09
-- Before: 327 · After: 361 · Delta: +34

UPDATE asset_registry
SET
    target_floor = 361,
    volume_explanation = 'Distinct topic_tag values present on embedded classical_text_chunks. Grew from 327 to 361 after classifying 1,493 new chunks from bhrigu_nandi_nadi (608) and nadi_navamsa_patel (1,850); 3,716 nadi chunks had no keyword match and remain NULL topic_tag.'
WHERE asset_id = 'bg_text_index';

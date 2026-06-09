-- Migration 200: bg_compendium_index target_floor update — Nadi expansion 2026-06-09
-- Before: 7025 · After: 9538 · Delta: +2513

UPDATE asset_registry
SET
    target_floor = 9538,
    volume_explanation = 'Rows in brahma_compendium_index: per-text×chapter (Pass A) + per-text×topic_tag (Pass B) navigational index. Grew from 7,025 to 9,538 after adding 2,174 chapter-level rows and 339 topic-level rows for bhrigu_nandi_nadi and nadi_navamsa_patel; 5,795+1,230 existing rows skipped (ON CONFLICT DO NOTHING).'
WHERE asset_id = 'bg_compendium_index';

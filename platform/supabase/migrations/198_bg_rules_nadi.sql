-- Migration 198: bg_rules target_floor update — Nadi expansion 2026-06-09
-- Before: 1976 · After: 2912 · Delta: +936

UPDATE asset_registry
SET
    target_floor = 2912,
    volume_explanation = 'Rows in sutravali_rules: deterministic regex-extracted rules from classical_text_chunks (3.4% coverage — most chunks are narrative, not aphoristic). Grew from 1,976 to 2,912 after processing all 10,651 chunks including bhrigu_nandi_nadi (608) and nadi_navamsa_patel (1,850); 936 new rules inserted with 1,976 conflict-skipped (existing rules untouched).'
WHERE asset_id = 'bg_rules';

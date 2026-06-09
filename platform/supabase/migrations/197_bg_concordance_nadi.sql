-- Migration 197: bg_concordance target_floor update — Nadi expansion 2026-06-09
-- Before: 477 · After: 720 · Delta: +243

UPDATE asset_registry
SET
    target_floor = 720,
    volume_explanation = 'Rows in classical_attributions: one per (topic_id × school) pair where the corpus has ≥1 classified chunk. Grew from 477 to 720 after the nadi school dimension was added for bhrigu_nandi_nadi and nadi_navamsa_patel, contributing 243 new (topic × nadi) rows across 361 distinct topics.'
WHERE asset_id = 'bg_concordance';

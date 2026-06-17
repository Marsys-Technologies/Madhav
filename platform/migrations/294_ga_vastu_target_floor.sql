-- 294_ga_vastu_target_floor.sql
-- =============================================================================
-- Correct ga_vastu_planet_direction_map target_floor from 45 to 40.
-- Ketu has no classical Vastu direction mapping and is intentionally excluded
-- by the writer (per ga_vastu_writer.py comment "Ketu may be skipped").
-- Actual production count: 8 grahas × 5 ayanamshas = 40 rows.
-- Per §N.4: target_floor = achieved count after build (floors aspirational).
-- Idempotent: UPDATE is safe to re-run.
-- =============================================================================

BEGIN;
UPDATE asset_registry SET target_floor = 40 WHERE asset_id = 'ga_vastu_planet_direction_map';
COMMIT;

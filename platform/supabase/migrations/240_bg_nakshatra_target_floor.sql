-- 240_bg_nakshatra_target_floor.sql
-- =============================================================================
-- Set target_floor for bg_nakshatra to the achieved count from first prod build.
-- Applied after Step 6 of Task 12 integration run (2026-06-17).
-- Actual counts: reference_nakshatra=28, reference_nakshatra_pada=108,
--                reference_nakshatra_matrix=2721, total=2857.
-- Idempotent: UPDATE is safe to re-run.
-- =============================================================================

BEGIN;
UPDATE asset_registry SET target_floor = 2857 WHERE asset_id = 'bg_nakshatra';
COMMIT;

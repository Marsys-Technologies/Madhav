-- =============================================================================
-- 293_ga_nakshatra_target_floor.sql
-- Set target_floor for ga_nakshatra after first build.
-- Achieved row count (native chart, lahiri_chitrapaksha × 5 ayanamshas + cross): 1802
-- Applied surgically — never via deploy.yml.
-- =============================================================================

BEGIN;
UPDATE asset_registry SET target_floor = 1802 WHERE asset_id = 'ga_nakshatra';
COMMIT;

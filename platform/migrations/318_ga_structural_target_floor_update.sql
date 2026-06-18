-- Migration 318: Update ga_structural target_floor to match post-remediation achieved row count.
-- Pre-remediation value was 74034 (stale from pre-Phase-2 build).
-- Post-remediation rebuild of chart 482012f1 produced 77821 rows (all 14 depth categories present).
-- Seed already updated to 77821; this migration syncs the live asset_registry row.

UPDATE asset_registry
SET target_floor = 77821
WHERE asset_id = 'ga_structural';

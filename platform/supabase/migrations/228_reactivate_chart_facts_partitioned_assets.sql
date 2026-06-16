-- Migration 228: reactivate 4 chart_facts-partitioned ga_ assets
--
-- Root cause: asset_registry_seed.ts pre-flight marked any asset with
-- target_table=NULL as is_active=false when the seed was re-applied (likely
-- during the PROGRESSBAR_RECONCILE or post-ga8-structural re-run on 2026-06-15).
-- These four assets intentionally have target_table=NULL — they write to the
-- shared chart_facts table and are probed via their count_sql filter. The seed
-- bug is fixed in the same PR (null target_table no longer overrides is_active).
--
-- Verify after apply:
--   SELECT asset_id, is_active, target_table
--   FROM asset_registry
--   WHERE asset_id IN ('ga_strength','ga_sensitive','ga_sade_sati','ga_structural');
-- Expected: all is_active=true, target_table=NULL (correct — shared chart_facts).

UPDATE asset_registry
SET is_active = true
WHERE asset_id IN ('ga_strength', 'ga_sensitive', 'ga_sade_sati', 'ga_structural')
  AND is_active = false;

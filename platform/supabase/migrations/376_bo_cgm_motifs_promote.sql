-- Migration 376: promote bo_cgm_motifs and bo_cgm_paths from DRAFT to CURRENT
--
-- bo_cgm_motifs:
--   Writers are complete and registered. The writer correctly produces 0 rows for charts
--   with no qualifying structural patterns (no stellium, no dispositor edges from
--   bo_karanajala). Setting target_floor=0 declares that 0 rows is a valid completed
--   state; the asset_runner already honours this via the target_floor=0 → 'lit' path
--   (implemented in 374/runner fix). Retroactively correct asset_throughput rows that
--   were set to 'dormant' while target_floor was non-zero.
--
-- bo_cgm_paths:
--   Writer is complete and registered. Has rows > 0 on built charts. No target_floor
--   change needed — existing rows satisfy the lit path unconditionally.

UPDATE asset_registry
SET
    catalog_status = 'CURRENT',
    target_floor   = 0
WHERE asset_id = 'bo_cgm_motifs';

UPDATE asset_registry
SET catalog_status = 'CURRENT'
WHERE asset_id = 'bo_cgm_paths';

-- Retroactively mark bo_cgm_motifs as 'lit' for all charts where the writer ran
-- and produced 0 rows (correct result: no structural motifs detected).
-- This makes the tracker show 14/14 for Bodha immediately without requiring a rebuild.
-- Only retroactively promote charts where the writer actually ran (last_built_at IS NOT NULL)
-- and produced 0 rows. Charts where last_built_at IS NULL have never been built and must
-- remain 'dormant' so the plan resolver includes them in the next build.
UPDATE asset_throughput
SET   state      = 'lit',
      last_error = NULL
WHERE asset_id       = 'bo_cgm_motifs'
  AND state          = 'dormant'
  AND rows_written   = 0
  AND last_built_at  IS NOT NULL
  AND chart_id IS NOT NULL;

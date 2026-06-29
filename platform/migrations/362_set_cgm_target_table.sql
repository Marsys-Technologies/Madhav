-- Migration 362: set target_table for bo_cgm_motifs and bo_cgm_paths
-- Both assets had target_table=NULL from initial registration.
-- The DB tables (bodha_cgm_motifs, bodha_cgm_paths) already exist.
-- target_table is used by the stats route and drift_detector for row-count checks.
UPDATE asset_registry
SET target_table = 'bodha_cgm_motifs'
WHERE asset_id = 'bo_cgm_motifs'
  AND target_table IS NULL;

UPDATE asset_registry
SET target_table = 'bodha_cgm_paths'
WHERE asset_id = 'bo_cgm_paths'
  AND target_table IS NULL;

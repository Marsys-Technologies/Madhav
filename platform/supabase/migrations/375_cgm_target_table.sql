-- Migration 375: set target_table for bo_cgm_motifs and bo_cgm_paths
-- Both assets had target_table=null from initial registration.
-- DB tables (bodha_cgm_motifs, bodha_cgm_paths) were created in migration 226.
UPDATE asset_registry
SET target_table = 'bodha_cgm_motifs'
WHERE asset_id = 'bo_cgm_motifs';

UPDATE asset_registry
SET target_table = 'bodha_cgm_paths'
WHERE asset_id = 'bo_cgm_paths';

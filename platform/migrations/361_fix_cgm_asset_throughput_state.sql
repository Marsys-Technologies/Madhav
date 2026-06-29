-- Migration 361: correct asset_throughput state for bo_cgm_motifs and bo_cgm_paths
-- Both assets completed with 0 rows but were marked 'lit' (pre-Task-15 bug: asset_runner
-- wrote 'lit' unconditionally regardless of rows_written). Reset to 'dormant' so
-- action='build' correctly picks them up for rebuild. Scoped to rows with
-- rows_written=0 (or NULL) to avoid touching future correct builds.
UPDATE asset_throughput
SET state = 'dormant'
WHERE asset_id IN ('bo_cgm_motifs', 'bo_cgm_paths')
  AND state = 'lit'
  AND (rows_written = 0 OR rows_written IS NULL)
  AND chart_id IS NOT NULL;

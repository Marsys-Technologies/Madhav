-- Migration 374: correct asset_throughput state for CGM assets
-- bo_cgm_motifs and bo_cgm_paths completed with 0 rows but were marked 'lit'
-- (pre-fix bug: asset_runner wrote state='lit' unconditionally even when rows_written=0).
-- Reset to 'dormant' so action='build' correctly picks them up for rebuild.
-- Scoped to rows with 0 actual rows to avoid touching charts where these assets
-- legitimately produced rows in a correct future build.
UPDATE asset_throughput
SET state = 'dormant'
WHERE asset_id IN ('bo_cgm_motifs', 'bo_cgm_paths')
  AND state = 'lit'
  AND (rows_written = 0 OR rows_written IS NULL)
  AND chart_id IS NOT NULL;

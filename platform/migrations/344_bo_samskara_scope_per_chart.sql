-- Migration 344: fix bo_samskara scope global→per_chart
-- Created: 2026-06-26

BEGIN;

UPDATE asset_registry
SET scope = 'per_chart'
WHERE asset_id = 'bo_samskara';

COMMIT;

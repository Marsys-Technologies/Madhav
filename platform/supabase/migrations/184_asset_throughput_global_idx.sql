-- migration 184: NULL-safe partial unique index for global (chart_id IS NULL) assets
-- in asset_throughput.
--
-- The existing constraint  asset_throughput_chart_asset_key (chart_id, asset_id)
-- WHERE chart_id IS NOT NULL  covers per-chart rows but does NOT cover global rows
-- where chart_id IS NULL — two rows can share (NULL, asset_id) without triggering
-- the partial unique constraint.
--
-- This index adds the matching partial index for the NULL side so that the
-- asset_runner INSERT ... ON CONFLICT (asset_id) WHERE chart_id IS NULL
-- lands on a real unique index rather than doing a full-table scan / no-op.
--
-- Must be applied BEFORE the global build runs any L0 asset writer.

BEGIN;

CREATE UNIQUE INDEX IF NOT EXISTS asset_throughput_global_idx
    ON asset_throughput(asset_id)
    WHERE chart_id IS NULL;

COMMIT;

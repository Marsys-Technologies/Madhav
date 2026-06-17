-- FIX 6 (P1-C): Insert missing global throughput record for bg_compendium_index
-- Existing record is per-chart (chart_id = 482012f1-...) but no global record exists.
-- bg_compendium_index is a global asset (scope='global') and needs chart_id IS NULL record.
-- Actual row count: 9538 (verified against brahma_compendium_index table)

INSERT INTO asset_throughput (asset_id, chart_id, state, rows_written, expected_rows, last_built_at)
VALUES ('bg_compendium_index', NULL, 'lit', 9538, 9538, NOW())
ON CONFLICT (asset_id) WHERE chart_id IS NULL
DO UPDATE SET state = 'lit', rows_written = 9538, expected_rows = 9538, last_built_at = NOW();

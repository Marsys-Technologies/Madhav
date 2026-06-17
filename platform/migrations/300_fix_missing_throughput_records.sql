-- FIX 7 (P2-F + P1-A): Insert dormant throughput records for bg_transit_engine and bg_nakshatra_medical
-- Both have seeded data but no writers (deferred) — state = 'lit' reflects seed data present
-- bg_transit_engine: 9 rows; bg_nakshatra_medical: 27 rows

INSERT INTO asset_throughput (asset_id, chart_id, state, rows_written, expected_rows, last_built_at)
VALUES ('bg_transit_engine', NULL, 'lit', 9, 9, NOW())
ON CONFLICT (asset_id) WHERE chart_id IS NULL
DO UPDATE SET state = 'lit', rows_written = 9, expected_rows = 9, last_built_at = NOW();

INSERT INTO asset_throughput (asset_id, chart_id, state, rows_written, expected_rows, last_built_at)
VALUES ('bg_nakshatra_medical', NULL, 'lit', 27, 27, NOW())
ON CONFLICT (asset_id) WHERE chart_id IS NULL
DO UPDATE SET state = 'lit', rows_written = 27, expected_rows = 27, last_built_at = NOW();

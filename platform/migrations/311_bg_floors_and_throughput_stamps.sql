-- Migration 311: bg_reference / bg_ontology / bg_nakshatra — target_floors + throughput stamps
-- ─────────────────────────────────────────────────────────────────────────────
-- BUG 1: These three L0 global assets have target_floor=NULL since initial seeding.
--   bg_reference and bg_ontology were never given a floor (the earlier L0 floor
--   touch-up missed them). bg_nakshatra was seeded with 2857 in seed.ts but no
--   migration applied that value to the DB. Floors set to measured prod counts
--   for chart 482012f1 as of 2026-06-18.
--
-- BUG 2: Same three assets have last_built_at=NULL in asset_throughput — they were
--   built at seed/initial-deploy time but never received a throughput stamp.
--   The cockpit reads asset_throughput.last_built_at for build_state_stale; NULL
--   causes build_state_stale=true even when rows are present.
--
-- Pattern: global L0 assets use chart_id=NULL.
--   Unique constraint: asset_throughput_global_idx UNIQUE (asset_id) WHERE chart_id IS NULL
-- ─────────────────────────────────────────────────────────────────────────────

-- BUG 1: target_floors
UPDATE asset_registry SET target_floor = 1485 WHERE asset_id = 'bg_reference';
UPDATE asset_registry SET target_floor = 623  WHERE asset_id = 'bg_ontology';
UPDATE asset_registry SET target_floor = 2857 WHERE asset_id = 'bg_nakshatra';

-- BUG 2: throughput stamps (global L0 — chart_id IS NULL)
INSERT INTO asset_throughput (asset_id, chart_id, state, rows_written, expected_rows, last_built_at)
VALUES ('bg_reference', NULL, 'lit', 1485, 1485, NOW())
ON CONFLICT (asset_id) WHERE chart_id IS NULL
DO UPDATE SET state = 'lit', rows_written = 1485, expected_rows = 1485, last_built_at = NOW();

INSERT INTO asset_throughput (asset_id, chart_id, state, rows_written, expected_rows, last_built_at)
VALUES ('bg_ontology', NULL, 'lit', 623, 623, NOW())
ON CONFLICT (asset_id) WHERE chart_id IS NULL
DO UPDATE SET state = 'lit', rows_written = 623, expected_rows = 623, last_built_at = NOW();

INSERT INTO asset_throughput (asset_id, chart_id, state, rows_written, expected_rows, last_built_at)
VALUES ('bg_nakshatra', NULL, 'lit', 2857, 2857, NOW())
ON CONFLICT (asset_id) WHERE chart_id IS NULL
DO UPDATE SET state = 'lit', rows_written = 2857, expected_rows = 2857, last_built_at = NOW();

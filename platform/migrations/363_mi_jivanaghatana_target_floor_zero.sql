-- Migration 363: set target_floor = 0 for mi_jivanaghatana
--
-- mi_jivanaghatana (Life event log held-out) reads from life_events table.
-- When no life events have been logged yet, the writer intentionally returns
-- 0 rows. Without target_floor = 0, the orchestrator keeps state = 'dormant'
-- for a 0-row per-chart writer, which causes the entire downstream DAG
-- (mi_bhavisya → mi_pramana → mi_gunanaka → mi_adhilepa → ...) to fail
-- with DEP-ASSERT errors.
--
-- Setting target_floor = 0 tells the orchestrator that 0 rows is a valid
-- completed state for this asset (cf. asset_runner.py zero_rows_is_complete).

UPDATE asset_registry
SET target_floor = 0
WHERE asset_id = 'mi_jivanaghatana';

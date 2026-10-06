-- v5_small_test_registry_row_readback.sql  (READ ONLY)
-- The production asset_registry row of ka_gochara_v5, with every field the dispatch and the teardown validate (their EXPECTED_REGISTRY_ROW).
-- Run it as the steward before the dispatch; compare it with the expected values below. The last five columns are the ones asset_runner.py
-- reads to decide HOW the asset is run (a probe or integrity check plus rebuild_on_probe_fail = true makes a passing probe skip the writer).
-- expected: scope per_chart, is_active false, has_writer true, has_substeps true, writer_timeout_seconds 28800,
--           depends_on {ga_positions,ga_dashas}, target_table ka_gochara_eval_window, target_floor 0, estimated_seconds NULL,
--           asset_kind data, asset_type data, health_probe NULL, integrity_check_sql NULL, rebuild_on_probe_fail false.
SELECT asset_id, scope, is_active, has_writer, has_substeps, writer_timeout_seconds, depends_on, target_table, count_sql, target_floor,
       estimated_seconds, asset_kind, asset_type, health_probe, integrity_check_sql, rebuild_on_probe_fail
FROM asset_registry
WHERE asset_id = 'ka_gochara_v5';

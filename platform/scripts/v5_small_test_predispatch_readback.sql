-- v5_small_test_predispatch_readback.sql  (READ ONLY — run as the steward BEFORE the dispatch dry run; send the output to the tracker)
-- Every fact the real runner and the dispatch need on production, found while tracing the runner end to end (Stream A, EPHE-RULING).
-- Nothing here writes. Expected values are in the comments; any difference is a reason to stop and report, not to fix by hand.
BEGIN READ ONLY;

-- 1. THE REGISTRY ROW of ka_gochara_v5: must be INACTIVE and in the migration-1304 shape (PR 3101 applied), with plain data routing.
--    expected: scope per_chart, is_active f, has_writer t, has_substeps t, writer_timeout_seconds 7200, depends_on {ga_positions,ga_dashas},
--    target_table ka_gochara_eval_window, target_floor 0, estimated_seconds NULL, asset_kind data, asset_type data, health_probe NULL,
--    integrity_check_sql NULL, rebuild_on_probe_fail f, catalog_status CURRENT.
SELECT asset_id, scope, is_active, has_writer, has_substeps, writer_timeout_seconds, depends_on, target_table, count_sql, target_floor,
       estimated_seconds, asset_kind, asset_type, health_probe, integrity_check_sql, rebuild_on_probe_fail, catalog_status
FROM asset_registry WHERE asset_id = 'ka_gochara_v5';

-- 2. THE DECLARED DEPENDENCIES must be LIT for the canonical chart (the runner never dispatches the asset otherwise: it marks it blocked),
--    and their freshness must be 'fresh' (the writer-entry dependency assertion requires it for data dependencies).
--    expected: one row each for ga_positions and ga_dashas: throughput_state lit (or service_ok), freshness_state fresh.
SELECT d.asset_id,
       (SELECT t.state FROM asset_throughput t WHERE t.asset_id = d.asset_id AND t.chart_id = '482012f1-710e-4a25-994a-93821f5871aa') AS throughput_state,
       (SELECT f.freshness_state FROM asset_freshness f WHERE f.asset_id = d.asset_id AND f.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
         ORDER BY f.observed_at DESC LIMIT 1) AS freshness_state
FROM unnest(ARRAY['ga_positions', 'ga_dashas']) AS d(asset_id);

-- 3. THE CHART has the birth data the runner reads (public.charts; the runner refuses with 'missing required birth fields' otherwise).
--    expected: all six columns non-null.
SELECT birth_date, birth_time, birth_lat, birth_lng, timezone_id, birth_place
FROM charts WHERE id = '482012f1-710e-4a25-994a-93821f5871aa' OR chart_id = '482012f1-710e-4a25-994a-93821f5871aa';

-- 4. NOTHING of the small test exists yet and nothing is active on the chart (the dispatch refuses otherwise; a clean start is required).
--    expected: every count 0.
SELECT (SELECT count(*) FROM build_runs WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND state IN ('planned', 'running', 'paused')) AS active_runs,
       (SELECT count(*) FROM build_runs WHERE triggered_by = 'gochara-v5-small-test') AS small_test_runs,
       (SELECT count(*) FROM asset_provenance_receipts WHERE asset_id = 'ka_gochara_v5') AS receipts,
       (SELECT count(*) FROM asset_freshness WHERE asset_id = 'ka_gochara_v5') AS freshness_rows,
       (SELECT count(*) FROM kala_gochara_publication WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND generation = '5.0') AS manifests_5_0,
       (SELECT count(*) FROM ka_gochara_search_input_snapshot WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND generation = '5.0') AS snapshots_5_0,
       (SELECT count(*) FROM ka_gochara_contact WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND generation = '5.0') AS contacts_5_0;

-- 5. THE CONCURRENCY CAP: the runner defers (exit 3) when 6 or more OTHER runs are 'running'. expected: well under 6.
SELECT count(*) AS running_runs_anywhere FROM build_runs WHERE state = 'running';

-- 6. THE WRITER-GAP PREFLIGHT: every asset id registered in the Python codebase (except the two sub-assets) needs an asset_registry row with
--    has_writer = true, or the runner fails the run before it starts. The id list comes from the code, so generate the query from the
--    checkout the job image was built from:
--      cd platform/python-sidecar && python3 -c "from pipeline.orchestrator.writers import WRITER_REGISTRY, discover_all; discover_all(); \
--      ids = sorted(set(WRITER_REGISTRY) - {'bg_nakshatra_medical','bg_transit_engine'}); \
--      print(\"SELECT i AS writer_gap FROM unnest(ARRAY[\" + ','.join(repr(x) for x in ids) + \"]) AS i WHERE NOT EXISTS (SELECT 1 FROM asset_registry r WHERE r.asset_id = i AND r.has_writer);\")"
--    run the printed statement here. expected: zero rows.

-- 7. THE ROLE the dispatch runs as (data_plane_builder suffices): run this connected AS that role. expected: every column t.
SELECT has_table_privilege(current_user, 'public.build_runs', 'INSERT') AS build_runs_insert,
       has_table_privilege(current_user, 'public.build_run_assets', 'INSERT') AS build_run_assets_insert,
       has_table_privilege(current_user, 'public.asset_throughput', 'INSERT') AS throughput_insert,
       has_table_privilege(current_user, 'public.asset_throughput', 'UPDATE') AS throughput_update,
       has_table_privilege(current_user, 'public.asset_registry', 'SELECT') AS registry_select,
       has_function_privilege(current_user, 'public.ka_gochara_lock_chart(uuid)', 'EXECUTE') AS lock_execute;

COMMIT;

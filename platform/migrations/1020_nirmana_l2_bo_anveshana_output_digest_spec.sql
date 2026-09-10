-- 1020_nirmana_l2_bo_anveshana_output_digest_spec.sql
--
-- NIRMANA v2.5 -- L2 (Bodha) W4 EXECUTE. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Authors bo_anveshana's output-digest specification -- the final blocker on
-- its path to asset_frozen. Without a spec, compute_output_digest() returns
-- (None, None) for this asset, so its asset_provenance_receipts row is stuck
-- at receipt_state='unknown' with unknown_reasons including
-- "output_digest_spec_unavailable" / "output_digest_unavailable" even though
-- code_digest is populated correctly and the build (run_id
-- 2c14e35a-07da-47b9-8f5d-1b6fad1af458) completed cleanly. Same D-CND-27
-- per-asset-authoring-gap class as bo_sudarshana (migration 896),
-- ga_positions (875), mi_vistara/mi_jivanaghatana/mi_kula (820-822),
-- bo_upaya (1012), ph_nimitta (1014/1015), ka_gochara (1018).
--
-- bo_anveshana (python-sidecar/pipeline/orchestrator/writers/bo_anveshana.py)
-- is the SOLE writer of both bodha_discoveries and bodha_anomalies
-- (bo_chart_gestalt and ph_nimitta only SELECT from bodha_discoveries as
-- downstream consumers -- confirmed by grep, no INSERT/UPDATE/DELETE in
-- either file). Idempotency is a straight per-chart delete-then-insert with
-- no further partition (`DELETE FROM bodha_discoveries WHERE chart_id = %s`,
-- same for bodha_anomalies -- all 5 canonical ayanamshas' rows share the
-- table), so unlike bo_sudarshana/bo_upaya this spec needs no where_in
-- narrowing beyond the canonical chart_id -- the writer already owns 100% of
-- both tables' content for that chart.
--
-- Two components, one per table (well under FUNC_MAX_ARGS batching threshold
-- of 45 value_columns -- bodha_discoveries has 28, bodha_anomalies has 12,
-- neither needs output_digest.py's _component_statement batching):
--   - bodha_discoveries: key_columns=["discovery_id"] (its registered PK).
--     value_columns = every real content column from migration 325's
--     CREATE TABLE except build_id (arbitrary per-run UUID) and computed_at
--     (row-insert timestamp) -- the same bookkeeping-exclusion class every
--     prior spec migration in this series documents. Includes
--     novelty_class_id even though the writer's current INSERT list never
--     sets it (always NULL) -- it is a real declared content column, not
--     bookkeeping, and a future writer change populating it must be visible
--     to the digest without a second migration.
--   - bodha_anomalies: key_columns=["anomaly_id"] (its registered PK).
--     value_columns = every real content column except build_id/computed_at,
--     same exclusion class.
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented:
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                      # == the literal below
--   print(_validate_spec('bo_anveshana', spec, sha))    # passes the server's own validator
--   "
-- Additionally end-to-end rehearsed live (read-only, rollback-only
-- transaction: INSERT the spec row, call the real
-- compute_output_digest(cur, asset_id='bo_anveshana') against production,
-- then ROLLBACK) to prove the where_equals filters and both component
-- queries actually execute against live data before this migration lands --
-- not just that the spec shape validates offline. Result:
-- output_digest=63bc446e0f2d3637d940a887a2049a63e938f9f8b505de04aa7fcc304b8e10f9
-- over 1161 bodha_discoveries rows + 3276 bodha_anomalies rows for the
-- canonical chart (confirmed via direct SELECT count(*) with the same
-- where_equals predicate on each table), zero NULL-key rows (
-- compute_output_digest's own preflight would have raised), transaction
-- rolled back, 0 rows left behind (independently re-verified via a fresh
-- SELECT count(*) afterward).

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bo_anveshana',
  '4debaff16035da221a7c234b5fc7cd8d819d680d5f44cf615cfaac7f56215885',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bodha_discoveries","relation":"bodha_discoveries","key_columns":["discovery_id"],"value_columns":["discovery_id","chart_id","ayanamsha_id","discovery_class","discovery_subsystem","non_obviousness_score","consequence_score","composite_discovery_rank","constituent_refs_jsonb","reasoning_chain_jsonb","why_an_acharya_misses_it","affected_domains_array","epistemic_jsonb","meaningfulness_basis","corroborating_methods_array","corroboration_count","surface_reading","depth_reading","surface_depth_delta","hypothesis_text","falsifier_jsonb","calibration_hook","novelty_class","novelty_class_id","cross_subsystem_root","cross_subsystem_refs_jsonb","provenance","engine_version"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}},{"name":"bodha_anomalies","relation":"bodha_anomalies","key_columns":["anomaly_id"],"value_columns":["anomaly_id","chart_id","ayanamsha_id","anomaly_type","discovery_subsystem","subject_ref_jsonb","anomaly_metric","anomaly_value","chart_baseline_value","sigma_from_baseline","meaningfulness_gate_result","engine_version"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

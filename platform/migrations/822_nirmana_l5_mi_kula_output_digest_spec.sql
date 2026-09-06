-- 822_nirmana_l5_mi_kula_output_digest_spec.sql
--
-- NIRMANA v2.1 -- L5 (Mimamsa) W4 EXECUTE.
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Authors mi_kula's output-digest specification, following the same per-layer
-- spec-authoring pattern L5 already used for mi_vistara (821) and
-- mi_jivanaghatana (820) under adjudication #1840's recommendation:
-- compute_output_digest() deliberately returns (None, None) for any asset
-- with no registered spec, which makes accepted_rebuild_observed
-- structurally unreachable for that asset. mi_kula's W4 dispatch already
-- ran successfully (run_id 343fe4fa-5979-4cb3-a5f3-a1600304fd28, verified
-- live in job logs + DB: 15 rows, asset_throughput.state='lit'), but its
-- receipt is stuck at receipt_state='unknown' with no spec to resolve
-- against.
--
-- Shape follows the mi_vistara/mi_jivanaghatana precedent exactly: one
-- component per digested relation (mi_kula writes two tables), key_columns
-- forming each table's real unique key, value_columns naming every content
-- column. created_at/updated_at excluded from mimamsa_signal_families as
-- pipeline-execution bookkeeping, not ledger content (same exclusion the
-- mi_vistara spec's own comment documents for its table's timestamp
-- columns); mimamsa_negative_controls has no such columns to exclude.
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented:
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                 # == the literal below
--   print(_validate_spec('mi_kula', spec, sha))    # passes the server's own validator
--   "

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'mi_kula',
  '6daaaafbe5ea0b5d1905f4b4381a098f486117f27f48183464dafd657c6ccf37',
  '{"components":[{"key_columns":["family_id"],"name":"mimamsa_signal_families","relation":"mimamsa_signal_families","value_columns":["family_id","display_name","layman_name","family_class","evidence_tier","soundness_basis","binding_kind","default_state","prior_weight","calibration_status","citation_refs","binding_spec","data_source_pin","apply_point","interaction_value","interaction_status","is_active","formula_version"]},{"key_columns":["control_id"],"name":"mimamsa_negative_controls","relation":"mimamsa_negative_controls","value_columns":["control_id","known_false_basis","citation_refs","binding_spec","expected_score","tolerance","last_harness_score","last_harness_status","formula_version"]}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

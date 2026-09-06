-- 812_nirmana_l5_mi_vistara_output_digest_spec.sql
--
-- NIRMANA v2.1 -- L5 (Mimamsa) W4 EXECUTE.
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Authors mi_vistara's output-digest specification -- the first non-L0 entry in
-- asset_output_digest_specs. Filed as adjudication #1840 (Conductor): the table
-- had 37 rows, every one bg_*, so compute_output_digest() deliberately returns
-- (None, None) for every L1-L5 asset and NirmanaRebuildEvidenceSchema.output_digest
-- (non-nullable) makes accepted_rebuild_observed/asset_frozen structurally
-- unreachable campaign-wide for anything outside L0. #1840 recommends per-layer
-- spec authoring (mirrors the #1715 receipt-spine generalisation); this is L5's
-- first contribution under that recommendation, scoped to the one asset this
-- session has already built (canary 1, run_id e45e343b-f9cd-4167-aeb5-061cab5ef6b2,
-- 2026-09-05, verified live in job logs + DB).
--
-- Shape follows the existing bg_* precedent (598/601_nirmana_output_digest_specs)
-- exactly: one component per digested relation, key_columns forming a real unique
-- key, value_columns naming every content column. mimamsa_export_log has a single
-- natural key (export_id, TEXT PK) and no orchestrator-bookkeeping columns to
-- exclude -- every column here is real ledger content, including exported_at
-- (the delivery timestamp is the export event's own business data, not pipeline
-- execution metadata like build_id/created_at, which this table has none of).
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented:
--   python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                    # == the literal below
--   print(_validate_spec('mi_vistara', spec, sha))    # passes the server's own validator
--   "

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'mi_vistara',
  '8190fd70f68867e2279025a0bd8dc304a658be48e4b6bde6c2582e929f0ae0c9',
  '{"components":[{"key_columns":["export_id"],"name":"mimamsa_export_log","relation":"mimamsa_export_log","value_columns":["export_id","chart_id","exported_at","export_format","recipient_ref","included_insight_ids","contribution_state","calibration_mode","disclosures_attached","payload_hash","lel_version","export_formula_version"]}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

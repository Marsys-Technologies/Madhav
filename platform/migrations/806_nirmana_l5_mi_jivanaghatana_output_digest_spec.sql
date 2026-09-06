-- 806_nirmana_l5_mi_jivanaghatana_output_digest_spec.sql
--
-- NIRMANA v2.1 -- L5 (Mimamsa) W4 EXECUTE.
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Authors mi_jivanaghatana's output-digest specification, the second non-L0
-- entry in asset_output_digest_specs (mi_vistara was the first, migration 692:
-- 692_nirmana_l5_mi_vistara_output_digest_spec.sql). Same #1840 gap: without a
-- spec, compute_output_digest() returns (None, None) for this asset, storing
-- receipt_state='unknown' with unknown_reasons ["output_digest_spec_unavailable",
-- "output_digest_unavailable"] (confirmed live 2026-09-06) and making
-- accepted_rebuild_observed/asset_frozen structurally unreachable.
--
-- mi_jivanaghatana writes mimamsa_event_provenance, PER-CHART scope (unlike
-- mi_vistara's global scope) -- confirmed live: asset_registry.scope='per_chart'
-- for this asset. Its real primary key is (chart_id, event_id)
-- (mimamsa_event_provenance_pkey, confirmed live via pg_indexes), so key_columns
-- matches that exactly. Because the table is multi-tenant (holds every chart's
-- provenance rows, not just the campaign's one canonical chart), the component
-- carries where_equals: {chart_id: <canonical chart_id>} -- the same reviewed-
-- filter mechanism bg_dasha_systems/bg_doshas/bg_class_priors already use for
-- their own ontology/prior-table scoping, applied here to scope the digest to
-- exactly the rows asset_provenance_receipts.chart_id will bind against
-- (confirmed live: the existing 'unknown' receipt for this asset already
-- carries chart_id=482012f1-710e-4a25-994a-93821f5871aa, the canonical chart).
--
-- value_columns names every real content column from the writer
-- (platform/python-sidecar/pipeline/orchestrator/writers/mi_jivanaghatana.py
-- INSERT_SQL) and excludes exactly one pipeline-bookkeeping column,
-- created_at (row-insert timestamp, not business data -- the same exclusion
-- rule mi_vistara's migration documented, applied here since this table
-- actually has one to exclude).
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented:
--   python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec, compute_output_digest
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                         # == the literal below
--   print(_validate_spec('mi_jivanaghatana', spec, sha))   # passes the server's own validator
--   "
-- Additionally end-to-end rehearsed live (read-only, rollback-only transaction:
-- INSERT the row, call the real compute_output_digest(cur, asset_id=...)
-- against production, then ROLLBACK) to prove the where_equals uuid filter and
-- the full component SQL actually execute against live data before this
-- migration lands -- not just that the spec shape validates offline. Result:
-- digest=3f63c772d268d264a9f1dacef4838d0f1e2527445409b44442ea525d5b1775b1
-- over the 63 live rows for the canonical chart (matches the canary build's
-- known row count), zero NULL-key rows, transaction rolled back, 0 rows left
-- behind (independently re-verified via a fresh SELECT count(*) afterward).

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'mi_jivanaghatana',
  '04134d9db426b9033220460b613d8c0c235e23c8252752241440ffecdaa0ee30',
  '{"components":[{"key_columns":["chart_id","event_id"],"name":"mimamsa_event_provenance","relation":"mimamsa_event_provenance","value_columns":["chart_id","event_id","shaped_predictor","shaped_predictor_refs","disclosure_timing","disclosure_date","event_date","domain_primary","domain_secondary","event_magnitude","held_out","admissible_clean","admissibility_reason","partition_seed_version","lel_version","provenance_formula_ver","lel_file_sha","lel_source","event_class_id"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}}],"version":"nirmana-output-digest-spec-v1"}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

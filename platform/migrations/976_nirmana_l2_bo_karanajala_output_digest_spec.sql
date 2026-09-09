-- 976_nirmana_l2_bo_karanajala_output_digest_spec.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Authors bo_karanajala's output-digest specification, discovered missing
-- during its first-ever campaign dispatch (build_run 47e920e8-54a6-4f98-
-- 9949-7eb59a4acff1, 2026-09-09 01:56:55Z, wave 2 under t1-2026-09-08-
-- be255ffe -- migration 950/966's writer-identity fix, PR #2482, deployed
-- ~942997643097c102c7ba90b4396225bb26962c33). Without a spec,
-- compute_output_digest() returns (None, None) for this asset and its
-- asset_provenance_receipts row lands with receipt_state='unknown' --
-- the same D-CND-27 per-asset-authoring gap already closed for
-- bo_sudarshana (896), bo_nakshatra_semantic/bo_special_lagna/
-- bo_vargottama_dhana (905/906/907), bo_bimba, bo_drishti (941),
-- bo_pramana_mapa (948), bo_laksana_rerank (939).
--
-- bo_karanajala's target_table is bodha_cgm_edges (asset_registry.
-- target_table), and it is the SOLE writer of that table: grepped every
-- writer under pipeline/orchestrator/writers/*.py referencing
-- "bodha_cgm_edges" for INSERT/UPDATE statements -- only
-- bo_karanajala.py's own INSERT (line 65) touches it; bo_anveshana,
-- bo_cgm_paths, bo_cgm_motifs, bo_drishti, bo_pramana_mapa,
-- bo_yantra_mechanism, ph_phaladesa only SELECT from it. So the spec
-- scopes to the FULL table for the canonical chart (chart_id where_equals
-- only, no where_in partition needed -- unlike bo_bimba's shared
-- bodha_cgm_nodes scoping).
--
-- key_columns = ["edge_id"], bodha_cgm_edges' registered primary key.
-- value_columns is every real content column from information_schema.
-- columns for bodha_cgm_edges EXCEPT build_id and computed_at (per-build
-- administrative metadata, excluded in every prior spec migration
-- including bo_bimba's template -- 43 total columns, 41 in value_columns).
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented, then rehearsed end-to-end against
-- live prod inside a ROLLED-BACK transaction (INSERT spec -> real
-- compute_output_digest() call -> confirmed a digest hex string returns,
-- no exception -> ROLLBACK):
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec, compute_output_digest
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                            # == the literal below
--   _validate_spec('bo_karanajala', spec, sha)                # passes the server's own validator
--   # then inside a rolled-back transaction: compute_output_digest() returned
--   # ('9ba68fbd030037dda70ed07b134b1bdef6e62d2000c9e52b4e2c6f6e78725214',
--   #  '2d474e10daf4319b71b664cde18c51dab74d8227a7092b488a28bf36aa25ddfb')
--   "
--
-- Live-verified against the canonical chart (482012f1-710e-4a25-994a-
-- 93821f5871aa) 2026-09-09 ~02:00 UTC (post this cycle's bo_karanajala
-- rebuild): bodha_cgm_edges has 849 rows for this chart, 0 with edge_id
-- NULL, 849 distinct edge_id (key-preflight clean).
--
-- Post-apply verification (N.4 -- never trust a silent no-op): expect
-- INSERT 0 1, then
--   SELECT asset_id FROM asset_output_digest_specs
--    WHERE asset_id = 'bo_karanajala' AND retired_at IS NULL  -- expect 1 row

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bo_karanajala',
  '2d474e10daf4319b71b664cde18c51dab74d8227a7092b488a28bf36aa25ddfb',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bodha_cgm_edges","relation":"bodha_cgm_edges","key_columns":["edge_id"],"value_columns":["edge_id","chart_id","ayanamsha_id","snapshot_type","edge_type","from_node_id","to_node_id","direction","computed_strength","weight_formula_version","intrinsic_strength","valence","affected_domains","directionality","weight_varga_source","relationship_basis","is_cross_subsystem","subsystem_from","subsystem_to","cross_subsystem_mapping_ref","edge_properties_jsonb","relationship_class","semantic_path_class","active_duration_class","active_dasha_periods_jsonb","underlying_msr_signal_ids_array","cross_system_consensus_count","cancelled_flag","cancelled_by_jsonb","cross_ayanamsha_edge_stability_score","present_in_traditions_array","edge_betweenness","in_shortest_path_count","graph_compute_library","graph_compute_library_version","verification_pass_status","citation_ref","citation_human","engine_version","constituent_fact_ids_array","constituent_ga_vichara_ids_array"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

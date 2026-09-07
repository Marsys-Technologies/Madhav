-- 896_nirmana_l2_bo_sudarshana_output_digest_spec.sql
--
-- NIRMANA v2.1 -- L2 (Bodha) W4 EXECUTE. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Authors bo_sudarshana's output-digest specification -- the final blocker on
-- its path to asset_frozen, per adjudication #2291's ruling (2026-09-07,
-- authorized). Without a spec, compute_output_digest() returns (None, None)
-- for this asset, so its asset_freshness row is stuck at
-- freshness_state='unknown' with reasons including
-- "output_digest_spec_unavailable" / "output_digest_unavailable" even after
-- the W4 dispatch (#1770's ruled scoped exception) and natural_key_partition
-- fix (migration 880) both landed -- the same D-CND-27 per-asset-authoring
-- gap #1840 already established for mi_vistara/mi_jivanaghatana/mi_kula
-- (migrations 820/821/822) and ga_positions (migration 875, the template
-- this migration follows).
--
-- The blocker that delayed this migration: bodha_msr_signals has 82 real
-- content columns (85 total minus build_id/computed_at, the same two
-- bookkeeping exclusions ga_positions' own migration 875 used) -> 164
-- jsonb_build_object args, over PostgreSQL's FUNC_MAX_ARGS=100 ceiling.
-- Filed as #2291, ruled authorized to batch value_columns into <=45-column
-- jsonb_build_object(...) calls concatenated via || within the same
-- component/scope (output_digest.py's _component_statement(), PR #2320,
-- merged 2026-09-07T14:46:26Z) -- no spec-schema or _validate_spec change.
--
-- bo_sudarshana writes to the SHARED table bodha_msr_signals (target_table
-- for 7 co-writers: bo_laksana, bo_laksana_rerank, bo_special_lagna,
-- bo_sudarshana, bo_arudha, bo_nakshatra_semantic, bo_vargottama_dhana), so
-- the digest -- like migration 880's natural_key_partition fix -- must scope
-- to exactly bo_sudarshana's own declared slice, not the whole table:
-- chart_id = the canonical chart (where_equals) AND signal_type_class =
-- 'sudarshana_agreement' (where_in) -- the exact same predicate migration 880
-- verified is bo_sudarshana's sole, exclusive ownership boundary
-- (sudarshana_emitter.py's single SIGNAL_TYPE_CLASS constant).
--
-- key_columns = ["signal_id"], bodha_msr_signals' actual registered primary
-- key. value_columns names every real content column EXCEPT build_id
-- (arbitrary per-run UUID, no business content -- including it would make
-- the digest differ on every rebuild even when nothing computed actually
-- changed) and computed_at (row-insert timestamp) -- the same exclusion
-- class migrations 820/821/822/875 all documented.
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions (post-#2320-merge, batched code path), never hand-reimplemented:
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                      # == the literal below
--   print(_validate_spec('bo_sudarshana', spec, sha))   # passes the server's own validator
--   "
-- Additionally end-to-end rehearsed live (read-only, rollback-only
-- transaction: INSERT the spec row, call the real batched
-- compute_output_digest(cur, asset_id='bo_sudarshana') against production,
-- then ROLLBACK) to prove the where_equals/where_in filters and the
-- 2-call-batched jsonb_build_object SQL actually execute against live data
-- before this migration lands -- not just that the spec shape validates
-- offline. Result:
-- digest=07564d1ac20be59e61156edfd3bae50bddd2952d704f4666fd24c2692c08aab1
-- over 45 live rows for the canonical chart (confirmed via a direct
-- SELECT count(*) with the same where_equals/where_in predicate), zero
-- NULL-key rows (compute_output_digest's own preflight would have raised),
-- transaction rolled back, 0 rows left behind (independently re-verified via
-- a fresh SELECT count(*) afterward).

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bo_sudarshana',
  '2bb3d8e7da4146315135f72bdb5c0a4f5d1bc35d6d98aeab0cf074f9fe072f9b',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bodha_msr_signals","relation":"bodha_msr_signals","key_columns":["signal_id"],"value_columns":["signal_id","chart_id","ayanamsha_id","signal_type_id","signal_type_class","signal_tradition","fact_kind","source_l1_asset","source_subsystem","signal_summary_text","signal_headline_text","classical_sources_jsonb","varga_id","varga_provenance_jsonb","epistemic_tier","epistemic_jsonb","salience_conditioned_by_jsonb","signature_tier","valence","lel_origin","configuration_jsonb","constituent_facts_array","constituent_signals_array","classical_sources_array","source_corroboration_count_by_text","source_corroboration_count_by_verse","orb_tightness","shadbala_norm","dignity_score","deterministic_strength","verification_certainty","divisional_corroboration_count","dasha_activation_proximity_score","house_weight_multiplier","ashtakavarga_support_multiplier","aspect_modifier","vargottama_amplification","argala_modifier","neechabhanga_modifier","cancellation_modifier","computed_salience","salience_formula_version","salience_confidence_interval_jsonb","domains_affected_array","domain_salience_jsonb","shared_factor_keys_jsonb","cross_domain_shared_factor_count","graph_edge_pattern_jsonb","graph_node_strength_contribution_jsonb","relationship_classification","graha_weakness_indicators_jsonb","remedy_hooks_array","recurring_pattern_marker","top_k_salience_rank","system_convergence_count","signature_class","contradicts_signals_array","active_duration_class","active_dasha_periods_jsonb","activation_predicted_dates_jsonb","predicted_outcome_class","cross_ayanamsha_consistency_score","strength_normalized_to_chart_max","pada_precision_flag","cross_system_consensus_count","channel_render_priority_jsonb","verification_pass_status","verification_method","citation_ref","citation_human","engine_version","salience_pctl_in_class","salience_inputs_complete","salience_robustness","aggregation_member","bala_gate","functional_context_score","verification_rescale","present_but_enfeebled","class_prior","ratification_factor","valence_source"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_in":{"signal_type_class":["sudarshana_agreement"]}}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

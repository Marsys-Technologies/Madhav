-- 905_nirmana_l2_bo_nakshatra_semantic_output_digest_spec.sql
--
-- NIRMANA v2.5 -- L2 (Bodha) W4 pre-dispatch. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Authors bo_nakshatra_semantic's output-digest specification, ahead of its
-- W4 dispatch under the #1770 EXTENSION RULING (D-NATIVE-12, 2026-09-07
-- 20:41:01Z): bo_sudarshana proved the canary remedy end-to-end, and the
-- ruling extended the same remedy to the three other E-gate-open
-- bodha_msr_signals co-writers -- bo_nakshatra_semantic, bo_special_lagna,
-- bo_vargottama_dhana. Without a spec, compute_output_digest() returns
-- (None, None) for this asset, so its asset_freshness row is stuck at
-- freshness_state='unknown' -- the exact same D-CND-27 per-asset-authoring
-- gap #1840/#2291 established for mi_vistara/mi_jivanaghatana/mi_kula
-- (migrations 820/821/822), ga_positions (875) and bo_sudarshana (896,
-- this migration's direct template).
--
-- bo_nakshatra_semantic writes to the SHARED table bodha_msr_signals (7
-- co-writers total: bo_laksana, bo_laksana_rerank, bo_special_lagna,
-- bo_sudarshana, bo_arudha, bo_nakshatra_semantic, bo_vargottama_dhana), so
-- the digest scopes to exactly this writer's own declared slice, not the
-- whole table: chart_id = the canonical chart (where_equals) AND
-- signal_type_class = 'nakshatra_semantic' (where_in) -- the single
-- SIGNAL_TYPE_CLASS constant nakshatra_semantic_emitter.py declares
-- (platform/python-sidecar/bodha_writers/nakshatra_semantic_emitter.py:47).
--
-- key_columns = ["signal_id"], bodha_msr_signals' registered primary key.
-- value_columns is the identical 83-column list migration 896 used (every
-- real content column except build_id and computed_at) -- table-invariant
-- across co-writers, re-verified live against the current
-- information_schema.columns for bodha_msr_signals before authoring this
-- migration (unchanged since 896).
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented:
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                            # == the literal below
--   print(_validate_spec('bo_nakshatra_semantic', spec, sha)) # passes the server's own validator
--   "
-- Additionally rehearsed read-only against production (no INSERT/UPDATE):
-- the component's own key-preflight predicate
-- (chart_id = canonical AND signal_type_class = ANY('{nakshatra_semantic}')
-- AND signal_id IS NULL) returns 0 rows, and the same predicate without the
-- NULL check returns exactly 45 rows -- matching the #1770 extension
-- ruling's own disclosed estimate (~45) for this asset's scoped-DELETE
-- exposure, well within the ruling's STOP-condition order-of-magnitude
-- bound.

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bo_nakshatra_semantic',
  '719fca93e28d13485a60bf12a54bbaf2b990fa9fe0573c68af6d2da2a5d94749',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bodha_msr_signals","relation":"bodha_msr_signals","key_columns":["signal_id"],"value_columns":["signal_id","chart_id","ayanamsha_id","signal_type_id","signal_type_class","signal_tradition","fact_kind","source_l1_asset","source_subsystem","signal_summary_text","signal_headline_text","classical_sources_jsonb","varga_id","varga_provenance_jsonb","epistemic_tier","epistemic_jsonb","salience_conditioned_by_jsonb","signature_tier","valence","lel_origin","configuration_jsonb","constituent_facts_array","constituent_signals_array","classical_sources_array","source_corroboration_count_by_text","source_corroboration_count_by_verse","orb_tightness","shadbala_norm","dignity_score","deterministic_strength","verification_certainty","divisional_corroboration_count","dasha_activation_proximity_score","house_weight_multiplier","ashtakavarga_support_multiplier","aspect_modifier","vargottama_amplification","argala_modifier","neechabhanga_modifier","cancellation_modifier","computed_salience","salience_formula_version","salience_confidence_interval_jsonb","domains_affected_array","domain_salience_jsonb","shared_factor_keys_jsonb","cross_domain_shared_factor_count","graph_edge_pattern_jsonb","graph_node_strength_contribution_jsonb","relationship_classification","graha_weakness_indicators_jsonb","remedy_hooks_array","recurring_pattern_marker","top_k_salience_rank","system_convergence_count","signature_class","contradicts_signals_array","active_duration_class","active_dasha_periods_jsonb","activation_predicted_dates_jsonb","predicted_outcome_class","cross_ayanamsha_consistency_score","strength_normalized_to_chart_max","pada_precision_flag","cross_system_consensus_count","channel_render_priority_jsonb","verification_pass_status","verification_method","citation_ref","citation_human","engine_version","salience_pctl_in_class","salience_inputs_complete","salience_robustness","aggregation_member","bala_gate","functional_context_score","verification_rescale","present_but_enfeebled","class_prior","ratification_factor","valence_source"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_in":{"signal_type_class":["nakshatra_semantic"]}}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

-- 903_nirmana_l2_bo_special_lagna_output_digest_spec.sql
--
-- NIRMANA v2.5 -- L2 (Bodha) W4 pre-dispatch. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 902 (bo_nakshatra_semantic) -- see that file for the
-- full rationale (#1770 EXTENSION RULING, D-NATIVE-12, 2026-09-07 20:41:01Z;
-- template 896/bo_sudarshana; D-CND-27 gap class). This migration authors
-- bo_special_lagna's output-digest specification.
--
-- bo_special_lagna writes to the SHARED table bodha_msr_signals, scoped to
-- exactly its own declared slice: chart_id = the canonical chart
-- (where_equals) AND signal_type_class = 'special_lagna' (where_in) -- the
-- single SIGNAL_TYPE_CLASS constant special_lagna_emitter.py declares
-- (platform/python-sidecar/bodha_writers/special_lagna_emitter.py:40).
--
-- key_columns / value_columns are identical to 896/902 (table-invariant,
-- re-verified live against information_schema.columns before authoring).
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented:
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                      # == the literal below
--   print(_validate_spec('bo_special_lagna', spec, sha)) # passes the server's own validator
--   "
-- Rehearsed read-only against production: the component's key-preflight
-- predicate (chart_id = canonical AND signal_type_class = ANY('{special_lagna}')
-- AND signal_id IS NULL) returns 0 rows; the same predicate without the NULL
-- check returns exactly 20 rows. The #1770 extension ruling's own comment
-- estimated "~10" for this asset -- 20 is 2x, not an order of magnitude,
-- and stays well inside the ruling's STOP-condition bound (measured
-- per-asset exposure, not the estimate, is what --acknowledge-destroys will
-- disclose at dispatch).

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bo_special_lagna',
  '228a25b0bad46791d4cda508dae64da1d6fb2ef7d08a5c4f92afc5ec5163d0a5',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bodha_msr_signals","relation":"bodha_msr_signals","key_columns":["signal_id"],"value_columns":["signal_id","chart_id","ayanamsha_id","signal_type_id","signal_type_class","signal_tradition","fact_kind","source_l1_asset","source_subsystem","signal_summary_text","signal_headline_text","classical_sources_jsonb","varga_id","varga_provenance_jsonb","epistemic_tier","epistemic_jsonb","salience_conditioned_by_jsonb","signature_tier","valence","lel_origin","configuration_jsonb","constituent_facts_array","constituent_signals_array","classical_sources_array","source_corroboration_count_by_text","source_corroboration_count_by_verse","orb_tightness","shadbala_norm","dignity_score","deterministic_strength","verification_certainty","divisional_corroboration_count","dasha_activation_proximity_score","house_weight_multiplier","ashtakavarga_support_multiplier","aspect_modifier","vargottama_amplification","argala_modifier","neechabhanga_modifier","cancellation_modifier","computed_salience","salience_formula_version","salience_confidence_interval_jsonb","domains_affected_array","domain_salience_jsonb","shared_factor_keys_jsonb","cross_domain_shared_factor_count","graph_edge_pattern_jsonb","graph_node_strength_contribution_jsonb","relationship_classification","graha_weakness_indicators_jsonb","remedy_hooks_array","recurring_pattern_marker","top_k_salience_rank","system_convergence_count","signature_class","contradicts_signals_array","active_duration_class","active_dasha_periods_jsonb","activation_predicted_dates_jsonb","predicted_outcome_class","cross_ayanamsha_consistency_score","strength_normalized_to_chart_max","pada_precision_flag","cross_system_consensus_count","channel_render_priority_jsonb","verification_pass_status","verification_method","citation_ref","citation_human","engine_version","salience_pctl_in_class","salience_inputs_complete","salience_robustness","aggregation_member","bala_gate","functional_context_score","verification_rescale","present_but_enfeebled","class_prior","ratification_factor","valence_source"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_in":{"signal_type_class":["special_lagna"]}}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

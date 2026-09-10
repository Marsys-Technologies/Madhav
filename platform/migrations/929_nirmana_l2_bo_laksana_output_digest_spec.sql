-- 929_nirmana_l2_bo_laksana_output_digest_spec.sql
--
-- NIRMANA v2.5 -- L2 (Bodha) W4 post-dispatch. Transaction ownership belongs
-- to platform/scripts/migrate.ts.
--
-- Sibling migration to 896/905-907/926 (D-CND-27 per-asset-authoring gap
-- class, #1840/#2291). Authors bo_laksana's output-digest specification.
-- bo_laksana's own build_run 7c8f2195-5953-4008-8347-e4c99b515a15 (cycle
-- 2026-09-08 ~15:32-15:34Z, THE BIG ONE per RESOLUTION_L2 priority 3,
-- #1770/#2447 WP-6 protocol) completed successfully (50,678 live rows in
-- bodha_msr_signals for the canonical chart) but its
-- asset_provenance_receipts row landed receipt_state='unknown' with reasons
-- ["output_digest_spec_unavailable", "output_digest_unavailable",
-- "partition_digest_unavailable", "partition_undeclared"] -- bo_laksana was
-- never given a spec, unlike its four bodha_msr_signals co-writer siblings
-- (bo_arudha, bo_nakshatra_semantic, bo_special_lagna, bo_vargottama_dhana)
-- that already carry one. Without a spec, compute_output_digest() returns
-- (None, None), and accepted_rebuild_observed/asset_frozen cannot proceed.
--
-- bo_laksana owns 15 of bodha_msr_signals' 19 signal_type_class values --
-- verified directly against the orchestrator writer's own declared allowlist
-- (BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES,
-- pipeline/orchestrator/writers/bo_laksana.py:145-160): yoga, dosha,
-- sade_sati, panchanga, karaka_alignment, tradition_specific, parivartana,
-- configuration, varga_pattern, annual, medical, vastu, composite_state,
-- varga_ratification_divergence, bhavat_bhavam_amplifier. Confirmed live on
-- the canonical chart (482012f1-710e-4a25-994a-93821f5871aa) post-rebuild:
-- 50,529 rows across exactly these 15 classes, 0 with signal_id IS NULL
-- (key-preflight predicate clean), no other bo_* asset's registered spec
-- declares any of these 15 classes (checked live against
-- asset_output_digest_specs -- zero overlap).
--
-- key_columns = ["signal_id"]. value_columns is the identical table-invariant
-- list migrations 896/905-907/926 used, re-verified live against the current
-- information_schema.columns for bodha_msr_signals before authoring this
-- migration: 84 live columns, 82 in the spec, excluded set exactly
-- {build_id, computed_at} (unchanged).
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented (where_in values must be unique and
-- sorted -- _validate_spec enforces this and rejects an unsorted list; the
-- literal below is alphabetically sorted per that requirement):
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                              # == the literal below
--   print(_validate_spec('bo_laksana', spec, sha))              # passes the server's own validator
--   "

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bo_laksana',
  '39827b99bf58466909220fdc1e9d58e84031aae51cf2dc8e1ec0ad5d78258d47',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bodha_msr_signals","relation":"bodha_msr_signals","key_columns":["signal_id"],"value_columns":["signal_id","chart_id","ayanamsha_id","signal_type_id","signal_type_class","signal_tradition","fact_kind","source_l1_asset","source_subsystem","signal_summary_text","signal_headline_text","classical_sources_jsonb","varga_id","varga_provenance_jsonb","epistemic_tier","epistemic_jsonb","salience_conditioned_by_jsonb","signature_tier","valence","lel_origin","configuration_jsonb","constituent_facts_array","constituent_signals_array","classical_sources_array","source_corroboration_count_by_text","source_corroboration_count_by_verse","orb_tightness","shadbala_norm","dignity_score","deterministic_strength","verification_certainty","divisional_corroboration_count","dasha_activation_proximity_score","house_weight_multiplier","ashtakavarga_support_multiplier","aspect_modifier","vargottama_amplification","argala_modifier","neechabhanga_modifier","cancellation_modifier","computed_salience","salience_formula_version","salience_confidence_interval_jsonb","domains_affected_array","domain_salience_jsonb","shared_factor_keys_jsonb","cross_domain_shared_factor_count","graph_edge_pattern_jsonb","graph_node_strength_contribution_jsonb","relationship_classification","graha_weakness_indicators_jsonb","remedy_hooks_array","recurring_pattern_marker","top_k_salience_rank","system_convergence_count","signature_class","contradicts_signals_array","active_duration_class","active_dasha_periods_jsonb","activation_predicted_dates_jsonb","predicted_outcome_class","cross_ayanamsha_consistency_score","strength_normalized_to_chart_max","pada_precision_flag","cross_system_consensus_count","channel_render_priority_jsonb","verification_pass_status","verification_method","citation_ref","citation_human","engine_version","salience_pctl_in_class","salience_inputs_complete","salience_robustness","aggregation_member","bala_gate","functional_context_score","verification_rescale","present_but_enfeebled","class_prior","ratification_factor","valence_source"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_in":{"signal_type_class":["annual","bhavat_bhavam_amplifier","composite_state","configuration","dosha","karaka_alignment","medical","panchanga","parivartana","sade_sati","tradition_specific","varga_pattern","varga_ratification_divergence","vastu","yoga"]}}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

-- 926_nirmana_l2_bo_arudha_output_digest_spec.sql
--
-- NIRMANA v2.5 -- L2 (Bodha) W4 pre-dispatch. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 905/906/907 (template 896/bo_sudarshana; D-CND-27
-- per-asset-authoring gap class, #1840/#2291). Authors bo_arudha's
-- output-digest specification ahead of its W4 dispatch under RESOLUTION_L2
-- v3 priority 1 (Conductor-directed recovery, 2026-09-08: bo_arudha is
-- ancestor-clear with ZERO campaign events -- never W1/W2-recorded, which is
-- different from ineligible). Without a spec, compute_output_digest() returns
-- (None, None) for this asset, its asset_provenance_receipts row cannot carry
-- output_digest/output_digest_spec_sha256, and its asset_freshness row cannot
-- reach freshness_state='fresh' -- the exact failure class 896/905-907 fixed
-- for its four bodha_msr_signals co-writer siblings.
--
-- bo_arudha writes to the SHARED table bodha_msr_signals (7 co-writers), so
-- the digest scopes to exactly this writer's own declared slice: chart_id =
-- the canonical chart (where_equals) AND signal_type_class = 'arudha'
-- (where_in) -- the single SIGNAL_TYPE_CLASS constant arudha_emitter.py
-- declares (platform/python-sidecar/bodha_writers/arudha_emitter.py:42),
-- matching the orchestrator writer's own allowlist
-- (BO_ARUDHA_OWNED_SIGNAL_TYPE_CLASSES = ["arudha"],
-- pipeline/orchestrator/writers/bo_arudha.py:39).
--
-- key_columns = ["signal_id"], bodha_msr_signals' registered primary key.
-- value_columns is the identical list migrations 896/905-907 used --
-- table-invariant across co-writers, re-verified live against the current
-- information_schema.columns for bodha_msr_signals before authoring this
-- migration: 84 live columns, 82 in the spec, excluded set exactly
-- {build_id, computed_at} (unchanged since 896).
--
-- spec_sha256 computed and independently re-verified via the REAL server
-- functions, never hand-reimplemented:
--   cd platform/python-sidecar && python3 -c "
--   from pipeline.orchestrator.provenance import canonical_digest
--   from pipeline.orchestrator.output_digest import _validate_spec
--   spec = {...}  # exact object below
--   print(canonical_digest(spec))                            # == the literal below
--   print(_validate_spec('bo_arudha', spec, sha))             # passes the server's own validator
--   "
-- Rehearsed read-only against production: the component's key-preflight
-- predicate (chart_id = canonical AND signal_type_class = 'arudha' AND
-- signal_id IS NULL) returns 0 rows; the same predicate without the NULL
-- check returns 25 rows (5 ayanamshas x 5 arudha signals), all under this
-- single class, no co-writer collision.

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'bo_arudha',
  '913370b3192fbdc4b09ae882e1572c2b35ecd63afae2c8ae920cbb66fb3a38a9',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bodha_msr_signals","relation":"bodha_msr_signals","key_columns":["signal_id"],"value_columns":["signal_id","chart_id","ayanamsha_id","signal_type_id","signal_type_class","signal_tradition","fact_kind","source_l1_asset","source_subsystem","signal_summary_text","signal_headline_text","classical_sources_jsonb","varga_id","varga_provenance_jsonb","epistemic_tier","epistemic_jsonb","salience_conditioned_by_jsonb","signature_tier","valence","lel_origin","configuration_jsonb","constituent_facts_array","constituent_signals_array","classical_sources_array","source_corroboration_count_by_text","source_corroboration_count_by_verse","orb_tightness","shadbala_norm","dignity_score","deterministic_strength","verification_certainty","divisional_corroboration_count","dasha_activation_proximity_score","house_weight_multiplier","ashtakavarga_support_multiplier","aspect_modifier","vargottama_amplification","argala_modifier","neechabhanga_modifier","cancellation_modifier","computed_salience","salience_formula_version","salience_confidence_interval_jsonb","domains_affected_array","domain_salience_jsonb","shared_factor_keys_jsonb","cross_domain_shared_factor_count","graph_edge_pattern_jsonb","graph_node_strength_contribution_jsonb","relationship_classification","graha_weakness_indicators_jsonb","remedy_hooks_array","recurring_pattern_marker","top_k_salience_rank","system_convergence_count","signature_class","contradicts_signals_array","active_duration_class","active_dasha_periods_jsonb","activation_predicted_dates_jsonb","predicted_outcome_class","cross_ayanamsha_consistency_score","strength_normalized_to_chart_max","pada_precision_flag","cross_system_consensus_count","channel_render_priority_jsonb","verification_pass_status","verification_method","citation_ref","citation_human","engine_version","salience_pctl_in_class","salience_inputs_complete","salience_robustness","aggregation_member","bala_gate","functional_context_score","verification_rescale","present_but_enfeebled","class_prior","ratification_factor","valence_source"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_in":{"signal_type_class":["arudha"]}}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

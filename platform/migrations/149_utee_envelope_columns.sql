-- Migration 149: UTEE Envelope Column Additions
-- UTEE = Unified Temporal Event Envelope
-- Adds standardized UTEE columns to all 7 temporal event tables:
--   A15 (l1_time_synchronicity), A16 (l1_phase_locked_anchors),
--   A18 (l1_vedha_extended), A19 (l1_bhrigu_bindu_transits),
--   A20 (l1_tajik_varsha_year_lords), A21 (l1_graha_aspects_lifetime),
--   A22 (l1_varsha_digest)
-- All statements idempotent (DO $$ BEGIN ... EXCEPTION WHEN duplicate_column THEN NULL; END $$)
-- Stream D — UTEE-S1 [BUILD-ORCH-STREAM-D-UTEE-S1]
-- Per: TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md §1.C

-- ============================================================
-- A15: l1_time_synchronicity
-- Existing columns (from migration 145):
--   sync_id, chart_id, window_start, window_end, cluster_intensity,
--   systems_active, key_dates, divergence_flag, divergence_detail,
--   convergence_score, embedding, narrative, classical_citation, created_at
-- ============================================================

DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN severity_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN confidence_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN confidence_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN expected_outcome_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN outcome_ontology_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN outcome_ontology_definition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN falsifiability_statement TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN falsifier_date_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN cross_ayanamsha_stability_score NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN per_tradition_variant_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN feeder_event_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN m6_outcome_tracking_placeholder_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
-- Bridge FK arrays
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN inside_a15_cluster_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN associated_synchronicity_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_time_synchronicity ADD COLUMN channel_render_priority_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;

-- ============================================================
-- A16: l1_phase_locked_anchors
-- Existing columns (from migration 146):
--   anchor_id, chart_id, anchor_label, window_start, window_end,
--   anchor_type, cluster_intensity, g29_rules_fired, systems_active,
--   primary_outcome, alternative_scenario, falsifiability_test,
--   causal_prior_anchor, confidence_score, embedding, classical_citation, created_at
-- ============================================================

DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN severity_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN severity_decomposition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN confidence_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN cross_ayanamsha_stability_score NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN per_tradition_variant_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN inside_a15_cluster_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN mitigated_by_vedha_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN seeded_by_bhrigu_hit_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN varsha_year_lord_context_id UUID; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN feeder_event_kinds_array TEXT[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN channel_render_priority_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN m6_outcome_tracking_placeholder_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN expected_outcome_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN outcome_ontology_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN outcome_ontology_definition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN confidence_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_phase_locked_anchors ADD COLUMN feeder_event_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;

-- ============================================================
-- A18: l1_vedha_extended
-- Existing columns (from migration 144):
--   vedha_id, vedha_system, source_nakshatra, obstructing_element,
--   obstruction_type, severity, cancellation_rule, classical_citation,
--   notes, created_at
-- (no temporal window columns exist — add full UTEE set)
-- ============================================================

DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN event_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN event_window_start_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN event_window_end_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN severity_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN severity_decomposition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN confidence_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN confidence_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN expected_outcome_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN outcome_ontology_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN outcome_ontology_definition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN falsifiability_statement TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN falsifier_date_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN cross_ayanamsha_stability_score NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN per_tradition_variant_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN applicable_tradition_ids_array TEXT[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN inside_a15_cluster_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN active_during_a15_cluster_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN associated_synchronicity_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN mitigates_anchor_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN channel_render_priority_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN temporal_event_embedding_vec vector(768); EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_vedha_extended ADD COLUMN m6_outcome_tracking_placeholder_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;

-- ============================================================
-- A19: l1_bhrigu_bindu_transits
-- Existing columns (from migration 142):
--   transit_id, chart_id, graha, hit_iso, bb_longitude_deg,
--   graha_longitude_deg, orb_deg, transit_type, strength_score,
--   classical_citation, created_at
-- (no temporal window or UTEE columns — add full UTEE set)
-- ============================================================

DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN event_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN event_window_start_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN event_window_end_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN severity_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN severity_decomposition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN confidence_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN confidence_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN expected_outcome_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN outcome_ontology_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN outcome_ontology_definition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN falsifiability_statement TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN falsifier_date_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN cross_ayanamsha_stability_score NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN inside_a15_cluster_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN associated_synchronicity_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN seeds_anchor_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN amplifies_event_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN channel_render_priority_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN temporal_event_embedding_vec vector(768); EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_bhrigu_bindu_transits ADD COLUMN m6_outcome_tracking_placeholder_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;

-- ============================================================
-- A20: l1_tajik_varsha_year_lords
-- Existing columns (from migration 148):
--   varsha_id, chart_id, ayanamsha_id, build_id, varsha_year,
--   varsha_start_iso, varsha_end_iso, age_at_varsha, year_lord,
--   year_lord_method, muntha_sign, muntha_house, hadda_lord,
--   hadda_degree_start, hadda_degree_end, applicable_tajik_yogas_array,
--   varsha_lagna, muntha_context_jsonb, hadda_context_jsonb,
--   verification_pass_status, citation_ref, citation_human, computed_at
-- (varsha_start_iso / varsha_end_iso serve as temporal window; add UTEE columns)
-- ============================================================

DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN event_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN event_window_start_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN event_window_end_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN severity_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN severity_decomposition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN confidence_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN confidence_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN expected_outcome_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN outcome_ontology_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN outcome_ontology_definition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN falsifiability_statement TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN falsifier_date_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN cross_ayanamsha_stability_score NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN per_tradition_variant_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN inside_a15_cluster_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN associated_synchronicity_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN seeds_anchor_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN amplifies_event_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN channel_render_priority_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN temporal_event_embedding_vec vector(768); EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_tajik_varsha_year_lords ADD COLUMN m6_outcome_tracking_placeholder_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;

-- ============================================================
-- A21: l1_graha_aspects_lifetime
-- Existing columns (from migration 143):
--   aspect_id, chart_id, natal_graha, transit_graha, aspect_type,
--   aspect_system, exact_date, natal_graha_lon, transit_graha_lon,
--   aspect_degree, orb_deg, is_applying, classical_citation, created_at
-- (exact_date is the key date; no UTEE columns — add full set)
-- ============================================================

DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN event_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN event_window_start_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN event_window_end_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN severity_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN severity_decomposition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN confidence_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN confidence_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN expected_outcome_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN outcome_ontology_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN outcome_ontology_definition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN falsifiability_statement TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN falsifier_date_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN cross_ayanamsha_stability_score NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN per_tradition_variant_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN inside_a15_cluster_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN associated_synchronicity_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN seeds_anchor_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN channel_render_priority_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN temporal_event_embedding_vec vector(768); EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_graha_aspects_lifetime ADD COLUMN m6_outcome_tracking_placeholder_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;

-- ============================================================
-- A22: l1_varsha_digest
-- Existing columns (from migration 147):
--   digest_id, chart_id, varsha_year, vimshottari_md, vimshottari_ad,
--   bb_hit_count, anchor_count, anchor_labels, sync_window_count,
--   peak_cluster_intensity, vedha_count, sade_sati_status,
--   year_theme, confidence_score, embedding, created_at
-- (no UTEE columns — add full set)
-- ============================================================

DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN event_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN event_window_start_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN event_window_end_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN severity_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN severity_decomposition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN confidence_normalized_0_1 NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN confidence_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN expected_outcome_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN outcome_ontology_class TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN outcome_ontology_definition_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN falsifiability_statement TEXT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN falsifier_date_iso TIMESTAMPTZ; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN cross_ayanamsha_stability_score NUMERIC; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN per_tradition_variant_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN inside_a15_cluster_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN associated_synchronicity_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN seeds_anchor_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN amplifies_event_ids_array UUID[]; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN channel_render_priority_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN temporal_event_embedding_vec vector(768); EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE l1_varsha_digest ADD COLUMN m6_outcome_tracking_placeholder_jsonb JSONB; EXCEPTION WHEN duplicate_column THEN NULL; END $$;

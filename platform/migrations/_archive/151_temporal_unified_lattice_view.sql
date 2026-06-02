-- Migration 151: vw_temporal_unified_lattice — META-ζ Temporal Unified Lattice
-- UTEE-S3 [BUILD-ORCH-STREAM-D-UTEE-S3]
-- Range-query view UNIONing all 7 temporal event sources in UTEE shape.
-- Per: TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md §3.B
--
-- Column sources per table (actual names from migrations 142-149):
--   A15 l1_time_synchronicity    : PK=sync_id(BIGSERIAL); no ayanamsha_id/build_id;
--                                   date cols=window_start/window_end (DATE); no event_iso added
--   A16 l1_phase_locked_anchors  : PK=anchor_id(BIGSERIAL); no ayanamsha_id/build_id;
--                                   date cols=window_start/window_end (DATE); no event_iso added
--   A18 l1_vedha_extended        : PK=vedha_id(BIGSERIAL); no chart_id/ayanamsha_id/build_id;
--                                   event_iso/event_window_start_iso/event_window_end_iso added by 149
--   A19 l1_bhrigu_bindu_transits : PK=transit_id(BIGSERIAL); has chart_id; no ayanamsha_id/build_id;
--                                   event_iso/event_window_start_iso/event_window_end_iso added by 149
--   A20 l1_tajik_varsha_year_lords: PK=varsha_id(UUID); has chart_id/ayanamsha_id/build_id(UUID);
--                                   varsha_start_iso/varsha_end_iso native; event_iso added by 149
--   A21 l1_graha_aspects_lifetime: PK=aspect_id(BIGSERIAL); has chart_id; no ayanamsha_id/build_id;
--                                   event_iso/event_window_start_iso/event_window_end_iso added by 149
--   A22 l1_varsha_digest         : PK=digest_id(BIGSERIAL); has chart_id; no ayanamsha_id/build_id;
--                                   event_iso/event_window_start_iso/event_window_end_iso added by 149
--
-- All 7 subqueries return IDENTICAL column list and types (32 columns).
-- NULLs are surfaced gracefully via COALESCE where required; no subquery will error
-- if UTEE columns are NULL (backfill not yet run).

CREATE OR REPLACE VIEW vw_temporal_unified_lattice AS

  -- ── A15: Time-Synchronicity windows ─────────────────────────────────────────
  -- window_start/window_end are DATE; cast to TIMESTAMPTZ for uniform event_iso.
  -- No event_iso column added by migration 149 — derive from window_start.
  -- No ayanamsha_id or build_id on this table.
  SELECT
    'A15'::TEXT                                             AS source_asset,
    sync_id::TEXT                                          AS source_row_id,
    chart_id                                               AS chart_id,
    NULL::TEXT                                             AS ayanamsha_id,
    NULL::TEXT                                             AS build_id,
    window_start::TIMESTAMPTZ                              AS event_iso,
    window_start::TIMESTAMPTZ                              AS event_window_start_iso,
    window_end::TIMESTAMPTZ                                AS event_window_end_iso,
    COALESCE(severity_normalized_0_1, 0.5)                 AS severity_normalized_0_1,
    NULL::JSONB                                            AS severity_decomposition_jsonb,
    COALESCE(confidence_normalized_0_1, 0.5)               AS confidence_normalized_0_1,
    COALESCE(confidence_class, 'medium')                   AS confidence_class,
    expected_outcome_class                                 AS expected_outcome_class,
    outcome_ontology_class                                 AS outcome_ontology_class,
    outcome_ontology_definition_jsonb                      AS outcome_ontology_definition_jsonb,
    falsifiability_statement                               AS falsifiability_statement,
    falsifier_date_iso                                     AS falsifier_date_iso,
    cross_ayanamsha_stability_score                        AS cross_ayanamsha_stability_score,
    per_tradition_variant_jsonb                            AS per_tradition_variant_jsonb,
    inside_a15_cluster_ids_array                           AS inside_a15_cluster_ids_array,
    associated_synchronicity_ids_array                     AS associated_synchronicity_ids_array,
    feeder_event_ids_array                                 AS feeder_event_ids_array,
    NULL::UUID[]                                           AS mitigates_event_ids_array,
    NULL::UUID[]                                           AS amplifies_event_ids_array,
    NULL::UUID[]                                           AS seeds_anchor_ids_array,
    NULL::UUID[]                                           AS mitigated_by_vedha_ids_array,
    channel_render_priority_jsonb                          AS channel_render_priority_jsonb,
    NULL::vector(768)                                      AS temporal_event_embedding_vec,
    m6_outcome_tracking_placeholder_jsonb                  AS m6_outcome_tracking_placeholder_jsonb,
    NULL::TEXT                                             AS citation_ref,
    classical_citation                                     AS citation_human,
    created_at                                             AS computed_at
  FROM l1_time_synchronicity

  UNION ALL

  -- ── A16: Phase-Locked Anchors ────────────────────────────────────────────────
  -- window_start/window_end are DATE; cast to TIMESTAMPTZ.
  -- No event_iso added by migration 149. No ayanamsha_id or build_id.
  -- Has severity_decomposition_jsonb (added by 149), mitigated_by_vedha_ids_array (added by 149).
  SELECT
    'A16'::TEXT                                             AS source_asset,
    anchor_id::TEXT                                        AS source_row_id,
    chart_id                                               AS chart_id,
    NULL::TEXT                                             AS ayanamsha_id,
    NULL::TEXT                                             AS build_id,
    window_start::TIMESTAMPTZ                              AS event_iso,
    window_start::TIMESTAMPTZ                              AS event_window_start_iso,
    window_end::TIMESTAMPTZ                                AS event_window_end_iso,
    COALESCE(severity_normalized_0_1, 0.5)                 AS severity_normalized_0_1,
    severity_decomposition_jsonb                           AS severity_decomposition_jsonb,
    COALESCE(confidence_normalized_0_1, confidence_score, 0.5) AS confidence_normalized_0_1,
    COALESCE(confidence_class, 'medium')                   AS confidence_class,
    expected_outcome_class                                 AS expected_outcome_class,
    outcome_ontology_class                                 AS outcome_ontology_class,
    outcome_ontology_definition_jsonb                      AS outcome_ontology_definition_jsonb,
    falsifiability_test                                    AS falsifiability_statement,
    NULL::TIMESTAMPTZ                                      AS falsifier_date_iso,
    cross_ayanamsha_stability_score                        AS cross_ayanamsha_stability_score,
    per_tradition_variant_jsonb                            AS per_tradition_variant_jsonb,
    inside_a15_cluster_ids_array                           AS inside_a15_cluster_ids_array,
    NULL::UUID[]                                           AS associated_synchronicity_ids_array,
    feeder_event_ids_array                                 AS feeder_event_ids_array,
    NULL::UUID[]                                           AS mitigates_event_ids_array,
    NULL::UUID[]                                           AS amplifies_event_ids_array,
    NULL::UUID[]                                           AS seeds_anchor_ids_array,
    mitigated_by_vedha_ids_array                           AS mitigated_by_vedha_ids_array,
    channel_render_priority_jsonb                          AS channel_render_priority_jsonb,
    embedding                                              AS temporal_event_embedding_vec,
    m6_outcome_tracking_placeholder_jsonb                  AS m6_outcome_tracking_placeholder_jsonb,
    NULL::TEXT                                             AS citation_ref,
    classical_citation                                     AS citation_human,
    created_at                                             AS computed_at
  FROM l1_phase_locked_anchors

  UNION ALL

  -- ── A18: Vedha Extended ──────────────────────────────────────────────────────
  -- No chart_id, ayanamsha_id, or build_id on this table.
  -- event_iso/event_window_start_iso/event_window_end_iso added by migration 149 (may be NULL).
  -- Has mitigates_anchor_ids_array (maps to mitigates_event_ids_array in view).
  -- Has temporal_event_embedding_vec (added by 149).
  SELECT
    'A18'::TEXT                                             AS source_asset,
    vedha_id::TEXT                                         AS source_row_id,
    NULL::UUID                                             AS chart_id,
    NULL::TEXT                                             AS ayanamsha_id,
    NULL::TEXT                                             AS build_id,
    event_iso                                              AS event_iso,
    event_window_start_iso                                 AS event_window_start_iso,
    event_window_end_iso                                   AS event_window_end_iso,
    COALESCE(severity_normalized_0_1, 0.5)                 AS severity_normalized_0_1,
    severity_decomposition_jsonb                           AS severity_decomposition_jsonb,
    COALESCE(confidence_normalized_0_1, 0.5)               AS confidence_normalized_0_1,
    COALESCE(confidence_class, 'medium')                   AS confidence_class,
    expected_outcome_class                                 AS expected_outcome_class,
    outcome_ontology_class                                 AS outcome_ontology_class,
    outcome_ontology_definition_jsonb                      AS outcome_ontology_definition_jsonb,
    falsifiability_statement                               AS falsifiability_statement,
    falsifier_date_iso                                     AS falsifier_date_iso,
    cross_ayanamsha_stability_score                        AS cross_ayanamsha_stability_score,
    per_tradition_variant_jsonb                            AS per_tradition_variant_jsonb,
    inside_a15_cluster_ids_array                           AS inside_a15_cluster_ids_array,
    associated_synchronicity_ids_array                     AS associated_synchronicity_ids_array,
    NULL::UUID[]                                           AS feeder_event_ids_array,
    mitigates_anchor_ids_array                             AS mitigates_event_ids_array,
    NULL::UUID[]                                           AS amplifies_event_ids_array,
    NULL::UUID[]                                           AS seeds_anchor_ids_array,
    NULL::UUID[]                                           AS mitigated_by_vedha_ids_array,
    channel_render_priority_jsonb                          AS channel_render_priority_jsonb,
    temporal_event_embedding_vec                           AS temporal_event_embedding_vec,
    m6_outcome_tracking_placeholder_jsonb                  AS m6_outcome_tracking_placeholder_jsonb,
    NULL::TEXT                                             AS citation_ref,
    classical_citation                                     AS citation_human,
    created_at                                             AS computed_at
  FROM l1_vedha_extended

  UNION ALL

  -- ── A19: Bhrigu Bindu Transits ───────────────────────────────────────────────
  -- Has chart_id. No ayanamsha_id or build_id.
  -- event_iso/event_window_start_iso/event_window_end_iso added by migration 149.
  -- Fallback for event_iso: hit_iso (DATE) cast to TIMESTAMPTZ.
  -- Has seeds_anchor_ids_array + amplifies_event_ids_array (added by 149).
  -- Has temporal_event_embedding_vec (added by 149).
  SELECT
    'A19'::TEXT                                             AS source_asset,
    transit_id::TEXT                                       AS source_row_id,
    chart_id                                               AS chart_id,
    NULL::TEXT                                             AS ayanamsha_id,
    NULL::TEXT                                             AS build_id,
    COALESCE(event_iso, hit_iso::TIMESTAMPTZ)              AS event_iso,
    COALESCE(event_window_start_iso, hit_iso::TIMESTAMPTZ) AS event_window_start_iso,
    event_window_end_iso                                   AS event_window_end_iso,
    COALESCE(severity_normalized_0_1, 0.5)                 AS severity_normalized_0_1,
    severity_decomposition_jsonb                           AS severity_decomposition_jsonb,
    COALESCE(confidence_normalized_0_1, 0.5)               AS confidence_normalized_0_1,
    COALESCE(confidence_class, 'medium')                   AS confidence_class,
    expected_outcome_class                                 AS expected_outcome_class,
    outcome_ontology_class                                 AS outcome_ontology_class,
    outcome_ontology_definition_jsonb                      AS outcome_ontology_definition_jsonb,
    falsifiability_statement                               AS falsifiability_statement,
    falsifier_date_iso                                     AS falsifier_date_iso,
    cross_ayanamsha_stability_score                        AS cross_ayanamsha_stability_score,
    NULL::JSONB                                            AS per_tradition_variant_jsonb,
    inside_a15_cluster_ids_array                           AS inside_a15_cluster_ids_array,
    associated_synchronicity_ids_array                     AS associated_synchronicity_ids_array,
    NULL::UUID[]                                           AS feeder_event_ids_array,
    NULL::UUID[]                                           AS mitigates_event_ids_array,
    amplifies_event_ids_array                              AS amplifies_event_ids_array,
    seeds_anchor_ids_array                                 AS seeds_anchor_ids_array,
    NULL::UUID[]                                           AS mitigated_by_vedha_ids_array,
    channel_render_priority_jsonb                          AS channel_render_priority_jsonb,
    temporal_event_embedding_vec                           AS temporal_event_embedding_vec,
    m6_outcome_tracking_placeholder_jsonb                  AS m6_outcome_tracking_placeholder_jsonb,
    NULL::TEXT                                             AS citation_ref,
    classical_citation                                     AS citation_human,
    created_at                                             AS computed_at
  FROM l1_bhrigu_bindu_transits

  UNION ALL

  -- ── A20: Tajik Varsha Year Lords ─────────────────────────────────────────────
  -- Has chart_id, ayanamsha_id, build_id (UUID — cast to TEXT).
  -- varsha_start_iso/varsha_end_iso are native TIMESTAMPTZ; event_iso also added by 149.
  -- Has citation_ref + citation_human + computed_at natively.
  -- Has seeds_anchor_ids_array + amplifies_event_ids_array (added by 149).
  -- Has temporal_event_embedding_vec (added by 149).
  SELECT
    'A20'::TEXT                                             AS source_asset,
    varsha_id::TEXT                                        AS source_row_id,
    chart_id                                               AS chart_id,
    ayanamsha_id                                           AS ayanamsha_id,
    build_id::TEXT                                         AS build_id,
    COALESCE(event_iso, varsha_start_iso)                  AS event_iso,
    COALESCE(event_window_start_iso, varsha_start_iso)     AS event_window_start_iso,
    COALESCE(event_window_end_iso, varsha_end_iso)         AS event_window_end_iso,
    COALESCE(severity_normalized_0_1, 0.5)                 AS severity_normalized_0_1,
    severity_decomposition_jsonb                           AS severity_decomposition_jsonb,
    COALESCE(confidence_normalized_0_1, 0.5)               AS confidence_normalized_0_1,
    COALESCE(confidence_class, 'medium')                   AS confidence_class,
    expected_outcome_class                                 AS expected_outcome_class,
    outcome_ontology_class                                 AS outcome_ontology_class,
    outcome_ontology_definition_jsonb                      AS outcome_ontology_definition_jsonb,
    falsifiability_statement                               AS falsifiability_statement,
    falsifier_date_iso                                     AS falsifier_date_iso,
    cross_ayanamsha_stability_score                        AS cross_ayanamsha_stability_score,
    per_tradition_variant_jsonb                            AS per_tradition_variant_jsonb,
    inside_a15_cluster_ids_array                           AS inside_a15_cluster_ids_array,
    associated_synchronicity_ids_array                     AS associated_synchronicity_ids_array,
    NULL::UUID[]                                           AS feeder_event_ids_array,
    NULL::UUID[]                                           AS mitigates_event_ids_array,
    amplifies_event_ids_array                              AS amplifies_event_ids_array,
    seeds_anchor_ids_array                                 AS seeds_anchor_ids_array,
    NULL::UUID[]                                           AS mitigated_by_vedha_ids_array,
    channel_render_priority_jsonb                          AS channel_render_priority_jsonb,
    temporal_event_embedding_vec                           AS temporal_event_embedding_vec,
    m6_outcome_tracking_placeholder_jsonb                  AS m6_outcome_tracking_placeholder_jsonb,
    citation_ref                                           AS citation_ref,
    citation_human                                         AS citation_human,
    computed_at                                            AS computed_at
  FROM l1_tajik_varsha_year_lords

  UNION ALL

  -- ── A21: Graha Aspects Lifetime ──────────────────────────────────────────────
  -- Has chart_id. No ayanamsha_id or build_id.
  -- event_iso added by migration 149; fallback to exact_date (DATE) cast.
  -- Has seeds_anchor_ids_array (added by 149).
  -- Has temporal_event_embedding_vec (added by 149).
  -- No per_tradition_variant_jsonb added by 149 — confirmed: A21 149 block omits it.
  SELECT
    'A21'::TEXT                                             AS source_asset,
    aspect_id::TEXT                                        AS source_row_id,
    chart_id                                               AS chart_id,
    NULL::TEXT                                             AS ayanamsha_id,
    NULL::TEXT                                             AS build_id,
    COALESCE(event_iso, exact_date::TIMESTAMPTZ)           AS event_iso,
    COALESCE(event_window_start_iso, exact_date::TIMESTAMPTZ) AS event_window_start_iso,
    event_window_end_iso                                   AS event_window_end_iso,
    COALESCE(severity_normalized_0_1, 0.5)                 AS severity_normalized_0_1,
    severity_decomposition_jsonb                           AS severity_decomposition_jsonb,
    COALESCE(confidence_normalized_0_1, 0.5)               AS confidence_normalized_0_1,
    COALESCE(confidence_class, 'medium')                   AS confidence_class,
    expected_outcome_class                                 AS expected_outcome_class,
    outcome_ontology_class                                 AS outcome_ontology_class,
    outcome_ontology_definition_jsonb                      AS outcome_ontology_definition_jsonb,
    falsifiability_statement                               AS falsifiability_statement,
    falsifier_date_iso                                     AS falsifier_date_iso,
    cross_ayanamsha_stability_score                        AS cross_ayanamsha_stability_score,
    per_tradition_variant_jsonb                            AS per_tradition_variant_jsonb,
    inside_a15_cluster_ids_array                           AS inside_a15_cluster_ids_array,
    associated_synchronicity_ids_array                     AS associated_synchronicity_ids_array,
    NULL::UUID[]                                           AS feeder_event_ids_array,
    NULL::UUID[]                                           AS mitigates_event_ids_array,
    NULL::UUID[]                                           AS amplifies_event_ids_array,
    seeds_anchor_ids_array                                 AS seeds_anchor_ids_array,
    NULL::UUID[]                                           AS mitigated_by_vedha_ids_array,
    channel_render_priority_jsonb                          AS channel_render_priority_jsonb,
    temporal_event_embedding_vec                           AS temporal_event_embedding_vec,
    m6_outcome_tracking_placeholder_jsonb                  AS m6_outcome_tracking_placeholder_jsonb,
    NULL::TEXT                                             AS citation_ref,
    classical_citation                                     AS citation_human,
    created_at                                             AS computed_at
  FROM l1_graha_aspects_lifetime

  UNION ALL

  -- ── A22: Varsha Digest ───────────────────────────────────────────────────────
  -- Has chart_id. No ayanamsha_id or build_id.
  -- event_iso/event_window_start_iso/event_window_end_iso added by migration 149.
  -- Has seeds_anchor_ids_array + amplifies_event_ids_array (added by 149).
  -- Has temporal_event_embedding_vec (added by 149).
  -- A22 149 block does NOT add per_tradition_variant_jsonb.
  SELECT
    'A22'::TEXT                                             AS source_asset,
    digest_id::TEXT                                        AS source_row_id,
    chart_id                                               AS chart_id,
    NULL::TEXT                                             AS ayanamsha_id,
    NULL::TEXT                                             AS build_id,
    event_iso                                              AS event_iso,
    event_window_start_iso                                 AS event_window_start_iso,
    event_window_end_iso                                   AS event_window_end_iso,
    COALESCE(severity_normalized_0_1, 0.5)                 AS severity_normalized_0_1,
    severity_decomposition_jsonb                           AS severity_decomposition_jsonb,
    COALESCE(confidence_normalized_0_1, confidence_score, 0.5) AS confidence_normalized_0_1,
    COALESCE(confidence_class, 'medium')                   AS confidence_class,
    expected_outcome_class                                 AS expected_outcome_class,
    outcome_ontology_class                                 AS outcome_ontology_class,
    outcome_ontology_definition_jsonb                      AS outcome_ontology_definition_jsonb,
    falsifiability_statement                               AS falsifiability_statement,
    falsifier_date_iso                                     AS falsifier_date_iso,
    cross_ayanamsha_stability_score                        AS cross_ayanamsha_stability_score,
    per_tradition_variant_jsonb                            AS per_tradition_variant_jsonb,
    inside_a15_cluster_ids_array                           AS inside_a15_cluster_ids_array,
    associated_synchronicity_ids_array                     AS associated_synchronicity_ids_array,
    NULL::UUID[]                                           AS feeder_event_ids_array,
    NULL::UUID[]                                           AS mitigates_event_ids_array,
    amplifies_event_ids_array                              AS amplifies_event_ids_array,
    seeds_anchor_ids_array                                 AS seeds_anchor_ids_array,
    NULL::UUID[]                                           AS mitigated_by_vedha_ids_array,
    channel_render_priority_jsonb                          AS channel_render_priority_jsonb,
    temporal_event_embedding_vec                           AS temporal_event_embedding_vec,
    m6_outcome_tracking_placeholder_jsonb                  AS m6_outcome_tracking_placeholder_jsonb,
    NULL::TEXT                                             AS citation_ref,
    NULL::TEXT                                             AS citation_human,
    created_at                                             AS computed_at
  FROM l1_varsha_digest;

-- Range queries use event_iso; each underlying table has its native date column indexed
-- via migrations 142-148. UTEE-backfill (migration 149) populates event_iso columns;
-- until backfill runs, A15/A16 use window_start cast, others use hit_iso/exact_date cast.
-- No materialization needed; predicate pushdown handles range queries efficiently.
COMMENT ON VIEW vw_temporal_unified_lattice IS
  'META-ζ: UTEE-shape range-query surface across A15-A22 temporal event tables. '
  'Query with WHERE event_iso BETWEEN start AND end AND chart_id = <id>. '
  'Source assets: A15=time_synchronicity, A16=phase_locked_anchors, '
  'A18=vedha_extended, A19=bhrigu_bindu_transits, A20=tajik_varsha_year_lords, '
  'A21=graha_aspects_lifetime, A22=varsha_digest. '
  'UTEE-S3 [BUILD-ORCH-STREAM-D-UTEE-S3]';

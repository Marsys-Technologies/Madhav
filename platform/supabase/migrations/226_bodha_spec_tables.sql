-- 226_bodha_spec_tables.sql
-- L2 Bodha Phase-0 (P0.1): create the full-spec bodha_* tables (renamed from l25_* per campaign §3.1).
-- All ~23 tables (MSR, CDLM×5, CGM×5+paths, RM×6, embeddings, scorecard, convergence,
-- contradictions) + all spec-required indexes + 8 materialized views (A10×3 + A11×5).
-- Also creates global signal_type_registry (G52, P0.2).
--
-- Prerequisites: pgvector extension (already present since migration 081).
-- Does NOT touch platform/migrations/ l25_* tables — those are a separate migration tree
-- disposition handled by L2_BODHA_P0_1_LEGACY_TABLE_DISPOSITION_v1_0.md.

BEGIN;

-- ────────────────────────────────────────────────────────────────────────────
-- G52  signal_type_registry  (global — no chart_id; P0.2)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE signal_type_registry (
  signal_type_id                      TEXT PRIMARY KEY,
  signal_type_class                   TEXT NOT NULL,   -- 'yoga'|'dosha'|'composite_state'|'parivartana'|'karaka_alignment'|'dasha_triggered'|'sade_sati'|'panchaka'|'transit_overlay'|'tradition_specific'|'varga_pattern'|'synthetic'
  signal_tradition                    TEXT NOT NULL,   -- 'parashari'|'jaimini'|'tajik'|'kp'|'lal_kitab'|'nadi_bhrigu'|'maharsi'|'multi'
  activation_predicate_text           TEXT,
  activation_predicate_jsonb          JSONB NOT NULL,
  constituent_facts_pattern_jsonb     JSONB,
  classical_sources_array             TEXT[] NOT NULL,
  classical_citations_jsonb           JSONB,
  default_domains_affected_array      TEXT[] NOT NULL,
  salience_formula_overrides_jsonb    JSONB,
  default_remedy_hooks_array          TEXT[],
  predicted_outcome_class             TEXT,
  since_engine_version                TEXT NOT NULL
);

CREATE INDEX str_class_tradition_idx ON signal_type_registry (signal_type_class, signal_tradition);
CREATE INDEX str_domains_gin_idx     ON signal_type_registry USING gin (default_domains_affected_array);

-- ────────────────────────────────────────────────────────────────────────────
-- A10  bodha_msr_signals  (~50 cols; A10 §3; renamed from l25_msr_signals)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_msr_signals (
  -- Identity
  signal_id                                   UUID PRIMARY KEY,
  chart_id                                    UUID NOT NULL,
  ayanamsha_id                                TEXT NOT NULL,
  build_id                                    UUID NOT NULL,

  -- Classification
  signal_type_id                              TEXT NOT NULL,
  signal_type_class                           TEXT NOT NULL,
  signal_tradition                            TEXT NOT NULL,

  -- Structured configuration
  configuration_jsonb                         JSONB NOT NULL,
  constituent_facts_array                     TEXT[] NOT NULL,
  constituent_signals_array                   UUID[],

  -- Classical sourcing
  classical_sources_array                     TEXT[],
  source_corroboration_count_by_text          INT,
  source_corroboration_count_by_verse         INT,

  -- Salience formula v1 — decomposed inputs
  orb_tightness                               NUMERIC,
  shadbala_norm                               NUMERIC,
  dignity_score                               NUMERIC,
  deterministic_strength                      NUMERIC NOT NULL,
  verification_certainty                      NUMERIC NOT NULL,
  divisional_corroboration_count              INT,
  dasha_activation_proximity_score            NUMERIC,
  house_weight_multiplier                     NUMERIC,
  ashtakavarga_support_multiplier             NUMERIC,
  aspect_modifier                             NUMERIC,
  vargottama_amplification                    NUMERIC,
  argala_modifier                             NUMERIC,
  neechabhanga_modifier                       NUMERIC,
  cancellation_modifier                       NUMERIC,
  computed_salience                           NUMERIC NOT NULL,
  salience_formula_version                    TEXT NOT NULL,

  -- Salience confidence interval
  salience_confidence_interval_jsonb          JSONB,

  -- Domain + cross-domain
  domains_affected_array                      TEXT[] NOT NULL,
  domain_salience_jsonb                       JSONB NOT NULL,
  shared_factor_keys_jsonb                    JSONB,
  cross_domain_shared_factor_count            INT,

  -- Graph hooks (for bo_bimba / bo_karanajala)
  graph_edge_pattern_jsonb                    JSONB,
  graph_node_strength_contribution_jsonb      JSONB,
  relationship_classification                 TEXT,

  -- Resonance map hooks (for bo_upaya)
  graha_weakness_indicators_jsonb             JSONB,
  remedy_hooks_array                          TEXT[],
  recurring_pattern_marker                    TEXT,

  -- UCN digest hooks (for bo_samvada)
  top_k_salience_rank                         INT,
  system_convergence_count                    INT,
  signature_class                             TEXT,

  -- Contradictions
  contradicts_signals_array                   UUID[],

  -- Active periods
  active_duration_class                       TEXT NOT NULL,
  active_dasha_periods_jsonb                  JSONB,
  activation_predicted_dates_jsonb            JSONB,
  predicted_outcome_class                     TEXT,

  -- Cross-ayanamsha
  cross_ayanamsha_consistency_score           NUMERIC,

  -- Strength normalization
  strength_normalized_to_chart_max            NUMERIC,

  -- Precision flags
  pada_precision_flag                         BOOLEAN,
  cross_system_consensus_count                INT,

  -- Multi-channel retrieval
  channel_render_priority_jsonb               JSONB,

  -- Verification + provenance
  verification_pass_status                    TEXT NOT NULL,
  verification_method                         TEXT,
  citation_ref                                TEXT NOT NULL,
  citation_human                              TEXT NOT NULL,
  computed_at                                 TIMESTAMPTZ NOT NULL,
  engine_version                              TEXT NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, signal_type_id, build_id, configuration_jsonb)
);

CREATE INDEX msr_chart_aya_idx           ON bodha_msr_signals (chart_id, ayanamsha_id);
CREATE INDEX msr_signal_type_idx         ON bodha_msr_signals (signal_type_id);
CREATE INDEX msr_signal_class_idx        ON bodha_msr_signals (signal_type_class, signal_tradition);
CREATE INDEX msr_salience_rank_idx       ON bodha_msr_signals (chart_id, ayanamsha_id, computed_salience DESC);
CREATE INDEX msr_domains_gin_idx         ON bodha_msr_signals USING gin (domains_affected_array);
CREATE INDEX msr_constituent_facts_gin   ON bodha_msr_signals USING gin (constituent_facts_array);
CREATE INDEX msr_top_k_rank_idx          ON bodha_msr_signals (chart_id, ayanamsha_id, top_k_salience_rank);
CREATE INDEX msr_signature_class_idx     ON bodha_msr_signals (signature_class) WHERE signature_class IS NOT NULL;
CREATE INDEX msr_recurring_pattern_idx   ON bodha_msr_signals (recurring_pattern_marker) WHERE recurring_pattern_marker IS NOT NULL;

-- ────────────────────────────────────────────────────────────────────────────
-- §13.1  bodha_contradictions  (first-class contradiction-pair rows)
-- Owned by bo_karanajala (graph); consumed by bo_sangati (CDLM convergence).
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_contradictions (
  contradiction_id         UUID PRIMARY KEY,
  chart_id                 UUID NOT NULL,
  ayanamsha_id             TEXT NOT NULL,
  build_id                 UUID NOT NULL,
  signal_a_id              UUID NOT NULL REFERENCES bodha_msr_signals(signal_id),
  signal_b_id              UUID NOT NULL REFERENCES bodha_msr_signals(signal_id),
  tension_basis_jsonb      JSONB NOT NULL,   -- structured: what the signals disagree on
  tension_class            TEXT NOT NULL,    -- 'yoga_vs_dosha'|'lord_vs_karaka'|'multi_ayanamsha_divergence'|'tradition_conflict'|'strength_vs_placement'
  domains_affected_array   TEXT[] NOT NULL,
  combined_salience        NUMERIC NOT NULL, -- sum of both signal saliencies
  resolution_hint_jsonb    JSONB,            -- classical-source-based resolution heuristics
  verification_pass_status TEXT NOT NULL,
  citation_ref             TEXT NOT NULL,
  citation_human           TEXT NOT NULL,
  computed_at              TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, signal_a_id, signal_b_id)
);

CREATE INDEX contradictions_chart_idx    ON bodha_contradictions (chart_id, ayanamsha_id);
CREATE INDEX contradictions_domains_gin  ON bodha_contradictions USING gin (domains_affected_array);

-- ────────────────────────────────────────────────────────────────────────────
-- A11  bodha_cdlm_cells  (main CDLM fact table; A11 Table 1)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_cdlm_cells (
  cell_id                                         UUID PRIMARY KEY,
  chart_id                                        UUID NOT NULL,
  ayanamsha_id                                    TEXT NOT NULL,
  build_id                                        UUID NOT NULL,

  snapshot_type                                   TEXT NOT NULL,
  dynamic_system_id                               TEXT,
  dynamic_maha_lord                               TEXT,
  dynamic_antar_lord                              TEXT,
  dynamic_window_start_iso                        TIMESTAMPTZ,
  dynamic_window_end_iso                          TIMESTAMPTZ,
  tradition_view_id                               TEXT,

  domain_row                                      TEXT NOT NULL,
  domain_col                                      TEXT NOT NULL,
  subdomain_row                                   TEXT,
  subdomain_col                                   TEXT,

  shared_signal_count                             INT NOT NULL,
  shared_factor_count                             INT NOT NULL,
  unique_signals_row_domain                       INT NOT NULL,
  unique_signals_col_domain                       INT NOT NULL,

  shared_signal_salience_sum                      NUMERIC NOT NULL,
  shared_signal_max_salience                      NUMERIC,
  positive_contribution                           NUMERIC NOT NULL,
  negative_contribution                           NUMERIC NOT NULL,
  net_linkage_strength                            NUMERIC NOT NULL,
  computed_linkage_strength                       NUMERIC NOT NULL,
  linkage_formula_version                         TEXT NOT NULL,

  contradicting_signal_pairs_count                INT NOT NULL,
  contradicting_signal_pairs_jsonb                JSONB,
  cross_domain_contradiction_flag                 BOOLEAN NOT NULL,

  shared_factor_keys_jsonb                        JSONB,
  shared_signal_ids_array                         UUID[],
  shared_signals_by_tradition_jsonb               JSONB,
  shared_signals_high_convergence_count           INT,
  recurring_pattern_markers_array                 TEXT[],

  cross_ayanamsha_cell_stability_score            NUMERIC,
  top_k_rank_in_snapshot                          INT,

  asymmetric_linkage_flag                         BOOLEAN NOT NULL,
  asymmetry_score                                 NUMERIC,

  -- CGM enrichment
  cgm_subgraph_cluster_id                         TEXT,
  cgm_bridge_edge_seeds_jsonb                     JSONB,
  cgm_domain_super_node_strength_contribution_jsonb JSONB,
  cgm_antagonist_edge_seeds_jsonb                 JSONB,

  -- RM enrichment
  cell_remedy_priority_rank                       INT,
  weakest_constituent_graha_jsonb                 JSONB,
  pattern_remedy_theme_jsonb                      JSONB,
  cell_remedy_hooks_array                         TEXT[],

  -- UCN enrichment
  dominant_linkage_rank_in_chart                  INT,
  domain_relationship_class                       TEXT,
  narrative_thread_seed                           JSONB,

  -- M6 prospective
  predicted_activation_dasha_windows_jsonb        JSONB,
  cell_evolution_gradient_score                   NUMERIC,

  channel_render_priority_jsonb                   JSONB,
  phase_aligned_pattern_marker                    TEXT,

  msr_salience_version_used                       TEXT NOT NULL,
  verification_pass_status                        TEXT NOT NULL,
  citation_ref                                    TEXT NOT NULL,
  citation_human                                  TEXT NOT NULL,
  computed_at                                     TIMESTAMPTZ NOT NULL,
  engine_version                                  TEXT NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, dynamic_system_id, dynamic_maha_lord,
          dynamic_antar_lord, tradition_view_id, domain_row, domain_col, subdomain_row, subdomain_col)
);

CREATE INDEX cdlm_chart_aya_idx             ON bodha_cdlm_cells (chart_id, ayanamsha_id);
CREATE INDEX cdlm_snapshot_type_idx         ON bodha_cdlm_cells (chart_id, ayanamsha_id, snapshot_type);
CREATE INDEX cdlm_dynamic_lookup_idx        ON bodha_cdlm_cells (chart_id, ayanamsha_id, dynamic_system_id, dynamic_window_start_iso, dynamic_window_end_iso);
CREATE INDEX cdlm_tradition_idx             ON bodha_cdlm_cells (chart_id, ayanamsha_id, tradition_view_id) WHERE tradition_view_id IS NOT NULL;
CREATE INDEX cdlm_top_rank_idx              ON bodha_cdlm_cells (chart_id, ayanamsha_id, snapshot_type, top_k_rank_in_snapshot);
CREATE INDEX cdlm_dominant_chart_rank_idx   ON bodha_cdlm_cells (chart_id, ayanamsha_id, dominant_linkage_rank_in_chart);
CREATE INDEX cdlm_pattern_markers_gin       ON bodha_cdlm_cells USING gin (recurring_pattern_markers_array);
CREATE INDEX cdlm_remedy_hooks_gin          ON bodha_cdlm_cells USING gin (cell_remedy_hooks_array);
CREATE INDEX cdlm_contradiction_idx         ON bodha_cdlm_cells (chart_id, ayanamsha_id) WHERE cross_domain_contradiction_flag = true;

-- ────────────────────────────────────────────────────────────────────────────
-- A11  bodha_cdlm_domain_rollups  (per-domain aggregations; A11 Table 2)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_cdlm_domain_rollups (
  rollup_id                           UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  dynamic_system_id                   TEXT,
  dynamic_maha_lord                   TEXT,
  dynamic_antar_lord                  TEXT,
  tradition_view_id                   TEXT,
  domain                              TEXT NOT NULL,
  total_inbound_linkage               NUMERIC NOT NULL,
  total_outbound_linkage              NUMERIC NOT NULL,
  diagonal_density                    NUMERIC NOT NULL,
  signal_count_for_domain             INT NOT NULL,
  top_3_linked_domains_jsonb          JSONB,
  contradiction_density               NUMERIC,
  pattern_markers_for_domain_array    TEXT[],
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, dynamic_system_id,
          dynamic_maha_lord, dynamic_antar_lord, tradition_view_id, domain)
);

CREATE INDEX cdlm_rollups_chart_idx ON bodha_cdlm_domain_rollups (chart_id, ayanamsha_id, snapshot_type);

-- ────────────────────────────────────────────────────────────────────────────
-- A11  bodha_cdlm_chart_summary  (per-chart-per-snapshot meta; A11 Table 3)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_cdlm_chart_summary (
  summary_id                          UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  dynamic_system_id                   TEXT,
  dynamic_maha_lord                   TEXT,
  dynamic_antar_lord                  TEXT,
  tradition_view_id                   TEXT,
  chart_typology_class                TEXT,
  pattern_cluster_markers_jsonb       JSONB,
  total_chart_linkage                 NUMERIC,
  contradiction_density               NUMERIC,
  house_to_domain_strength_jsonb      JSONB,
  karaka_to_domain_strength_jsonb     JSONB,
  dominant_3_domains_array            TEXT[],
  weakest_3_domains_array             TEXT[],
  bridge_link_count                   INT,
  asymmetric_link_count               INT,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, dynamic_system_id,
          dynamic_maha_lord, dynamic_antar_lord, tradition_view_id)
);

CREATE INDEX cdlm_summary_chart_idx ON bodha_cdlm_chart_summary (chart_id, ayanamsha_id, snapshot_type);

-- ────────────────────────────────────────────────────────────────────────────
-- A11  bodha_cdlm_pattern_clusters  (first-class detected patterns; A11 Table 4)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_cdlm_pattern_clusters (
  pattern_id                          UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  dynamic_system_id                   TEXT,
  dynamic_maha_lord                   TEXT,
  dynamic_antar_lord                  TEXT,
  tradition_view_id                   TEXT,
  pattern_marker_type                 TEXT NOT NULL,
  involved_domains_array              TEXT[] NOT NULL,
  cluster_strength_total              NUMERIC NOT NULL,
  involved_cells_array                UUID[] NOT NULL,
  involved_signals_array              UUID[] NOT NULL,
  contradicts_other_patterns_array    UUID[],
  remedy_theme_jsonb                  JSONB,
  cgm_subgraph_cluster_seed           JSONB,
  classical_archetype_match           TEXT,
  predicted_outcome_class             TEXT,
  active_dasha_windows_jsonb          JSONB,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL
);

CREATE INDEX cdlm_clusters_chart_idx      ON bodha_cdlm_pattern_clusters (chart_id, ayanamsha_id, snapshot_type);
CREATE INDEX cdlm_clusters_domains_gin    ON bodha_cdlm_pattern_clusters USING gin (involved_domains_array);

-- ────────────────────────────────────────────────────────────────────────────
-- A11  bodha_cdlm_evolution_gradients  (time-series for dynamic cells; A11 Table 5)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_cdlm_evolution_gradients (
  gradient_id                         UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  dynamic_system_id                   TEXT NOT NULL,
  tradition_view_id                   TEXT,
  domain_row                          TEXT NOT NULL,
  domain_col                          TEXT NOT NULL,
  evolution_class                     TEXT NOT NULL,  -- 'steepening'|'weakening'|'stable'|'oscillating'
  gradient_score                      NUMERIC,
  trend_iso_window_array              JSONB,
  peak_period_lord                    TEXT,
  peak_period_iso                     TIMESTAMPTZ,
  trough_period_iso                   TIMESTAMPTZ,
  predicted_next_peak_iso             TIMESTAMPTZ,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, dynamic_system_id, tradition_view_id, domain_row, domain_col)
);

CREATE INDEX cdlm_gradients_chart_idx ON bodha_cdlm_evolution_gradients (chart_id, ayanamsha_id, dynamic_system_id);

-- ────────────────────────────────────────────────────────────────────────────
-- §13.1  bodha_convergence  (per-domain convergence-density; first-class artifact)
-- Owned by bo_sangati; represents N independent L1 signals converging per domain.
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_convergence (
  convergence_id               UUID PRIMARY KEY,
  chart_id                     UUID NOT NULL,
  ayanamsha_id                 TEXT NOT NULL,
  build_id                     UUID NOT NULL,
  domain                       TEXT NOT NULL,
  snapshot_type                TEXT NOT NULL,  -- 'static_natal' | 'dynamic_maha_antar'
  dynamic_system_id            TEXT,
  dynamic_maha_lord            TEXT,
  dynamic_antar_lord           TEXT,
  convergence_count            INT NOT NULL,         -- N independent signals on this domain
  convergence_score            NUMERIC NOT NULL,     -- per convergence_formula_v1
  convergence_formula_version  TEXT NOT NULL,
  cross_tradition_count        INT NOT NULL,         -- how many distinct traditions contribute
  top_signal_ids_array         UUID[] NOT NULL,      -- ranked by salience, references bodha_msr_signals
  tradition_breakdown_jsonb    JSONB NOT NULL,        -- {tradition: count, ...}
  salience_weighted_sum        NUMERIC NOT NULL,
  salience_max                 NUMERIC NOT NULL,
  contradiction_count          INT NOT NULL,          -- contradictions within this domain's signal pool
  verification_pass_status     TEXT NOT NULL,
  citation_ref                 TEXT NOT NULL,
  citation_human               TEXT NOT NULL,
  computed_at                  TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, domain, snapshot_type, dynamic_system_id,
          dynamic_maha_lord, dynamic_antar_lord)
);

CREATE INDEX convergence_chart_idx     ON bodha_convergence (chart_id, ayanamsha_id, domain);
CREATE INDEX convergence_score_idx     ON bodha_convergence (chart_id, ayanamsha_id, convergence_score DESC);

-- ────────────────────────────────────────────────────────────────────────────
-- A12  bodha_cgm_nodes  (graph nodes; A12 Table 1; bo_bimba owns this)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_cgm_nodes (
  node_id                             UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  node_type                           TEXT NOT NULL,
  node_subject                        TEXT NOT NULL,
  node_label_human                    TEXT NOT NULL,
  position_in_chart_jsonb             JSONB,
  strength_score                      NUMERIC,
  dignity_state                       TEXT,
  -- igraph-computed flat columns (written at build time)
  degree_in                           INT NOT NULL,
  degree_out                          INT NOT NULL,
  betweenness_centrality              NUMERIC,
  eigenvector_centrality              NUMERIC,
  pagerank_score                      NUMERIC,
  clustering_coefficient              NUMERIC,
  closeness_centrality                NUMERIC,
  harmonic_centrality                 NUMERIC,
  core_number                         INT,
  -- Domain + cluster
  primary_domain                      TEXT,
  domain_affiliations_jsonb           JSONB,
  cluster_membership_array            TEXT[],
  cgm_subgraph_cluster_id             TEXT,
  -- Configuration specifics
  msr_signal_id                       UUID,
  configuration_constituents_array    UUID[],
  configuration_lifecycle_state       TEXT,
  -- Hub identification
  hub_flag                            BOOLEAN NOT NULL,
  hub_score                           NUMERIC,
  hub_edge_types_array                TEXT[],
  -- Tradition + cross-ayanamsha
  present_in_traditions_array         TEXT[],
  cross_ayanamsha_presence_score      NUMERIC,
  -- pgvector
  node_embedding_vec                  VECTOR(768),
  -- Ephemeris audit
  ephemeris_audit_jsonb               JSONB,
  -- Provenance
  msr_salience_version_used           TEXT,
  cdlm_version_used                   TEXT,
  graph_compute_library               TEXT NOT NULL,
  graph_compute_library_version       TEXT NOT NULL,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL,
  engine_version                      TEXT NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, node_type, node_subject)
);

CREATE INDEX cgm_nodes_chart_aya_idx    ON bodha_cgm_nodes (chart_id, ayanamsha_id);
CREATE INDEX cgm_nodes_snapshot_idx     ON bodha_cgm_nodes (chart_id, ayanamsha_id, snapshot_type);
CREATE INDEX cgm_nodes_hub_idx          ON bodha_cgm_nodes (chart_id, ayanamsha_id) WHERE hub_flag = true;
CREATE INDEX cgm_nodes_pagerank_idx     ON bodha_cgm_nodes (chart_id, ayanamsha_id, pagerank_score DESC);
CREATE INDEX cgm_nodes_traditions_gin   ON bodha_cgm_nodes USING gin (present_in_traditions_array);
CREATE INDEX cgm_nodes_embedding_hnsw   ON bodha_cgm_nodes USING hnsw (node_embedding_vec vector_cosine_ops);

-- ────────────────────────────────────────────────────────────────────────────
-- A12  bodha_cgm_edges  (graph edges; A12 Table 2; bo_karanajala owns this)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_cgm_edges (
  edge_id                             UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  edge_type                           TEXT NOT NULL,
  from_node_id                        UUID NOT NULL,
  to_node_id                          UUID NOT NULL,
  direction                           TEXT NOT NULL,
  computed_strength                   NUMERIC NOT NULL,
  weight_formula_version              TEXT NOT NULL,
  edge_properties_jsonb               JSONB,
  relationship_class                  TEXT,
  semantic_path_class                 TEXT,
  active_duration_class               TEXT,
  active_dasha_periods_jsonb          JSONB,
  underlying_msr_signal_ids_array     UUID[],
  cross_system_consensus_count        INT,
  cancelled_flag                      BOOLEAN NOT NULL,
  cancelled_by_jsonb                  JSONB,
  cross_ayanamsha_edge_stability_score NUMERIC,
  present_in_traditions_array         TEXT[],
  -- igraph-computed at write time
  edge_betweenness                    NUMERIC,
  in_shortest_path_count              INT,
  graph_compute_library               TEXT NOT NULL,
  graph_compute_library_version       TEXT NOT NULL,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL,
  engine_version                      TEXT NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, edge_type, from_node_id, to_node_id)
);

CREATE INDEX cgm_edges_chart_aya_idx    ON bodha_cgm_edges (chart_id, ayanamsha_id);
CREATE INDEX cgm_edges_snapshot_idx     ON bodha_cgm_edges (chart_id, ayanamsha_id, snapshot_type);
CREATE INDEX cgm_edges_from_idx         ON bodha_cgm_edges (from_node_id);
CREATE INDEX cgm_edges_to_idx           ON bodha_cgm_edges (to_node_id);
CREATE INDEX cgm_edges_type_idx         ON bodha_cgm_edges (chart_id, ayanamsha_id, edge_type);
CREATE INDEX cgm_edges_msr_gin          ON bodha_cgm_edges USING gin (underlying_msr_signal_ids_array);

-- ────────────────────────────────────────────────────────────────────────────
-- A12  bodha_cgm_sub_graphs  (A12 Table 3; bo_karanajala)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_cgm_sub_graphs (
  subgraph_id                         UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  subgraph_type                       TEXT NOT NULL,
  subgraph_label                      TEXT NOT NULL,
  node_ids_array                      UUID[] NOT NULL,
  edge_ids_array                      UUID[] NOT NULL,
  subgraph_density                    NUMERIC,
  subgraph_centroid_node_id           UUID,
  representative_path_jsonb           JSONB,
  classical_archetype_match           TEXT,
  graphml_export_jsonb                JSONB,
  gexf_export_jsonb                   JSONB,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL
);

CREATE INDEX cgm_sub_graphs_chart_idx ON bodha_cgm_sub_graphs (chart_id, ayanamsha_id, subgraph_type);

-- ────────────────────────────────────────────────────────────────────────────
-- A12  bodha_cgm_motifs  (A12 Table 4; bo_karanajala)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_cgm_motifs (
  motif_id                            UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  motif_name                          TEXT NOT NULL,
  motif_class                         TEXT NOT NULL,
  involved_node_ids_array             UUID[] NOT NULL,
  involved_edge_ids_array             UUID[] NOT NULL,
  motif_strength                      NUMERIC NOT NULL,
  classical_citation_id               TEXT,
  fingerprint_hash                    TEXT NOT NULL,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL
);

CREATE INDEX cgm_motifs_chart_idx       ON bodha_cgm_motifs (chart_id, ayanamsha_id);
CREATE INDEX cgm_motifs_name_idx        ON bodha_cgm_motifs (motif_name);
CREATE INDEX cgm_motifs_fingerprint_idx ON bodha_cgm_motifs (fingerprint_hash);

-- ────────────────────────────────────────────────────────────────────────────
-- A12  bodha_cgm_chart_topology_summary  (A12 Table 5; bo_karanajala)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_cgm_chart_topology_summary (
  summary_id                          UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  total_nodes                         INT,
  total_edges                         INT,
  top_5_hub_nodes_jsonb               JSONB,
  top_5_central_nodes_jsonb           JSONB,
  triangle_count                      INT,
  strongly_connected_components_count INT,
  graph_diameter                      INT,
  graph_density                       NUMERIC,
  isolated_node_ids_array             UUID[],
  dispositor_cycle_jsonb              JSONB,
  hub_dominance_score                 NUMERIC,
  fragmentation_score                 NUMERIC,
  graph_fingerprint_hash              TEXT,
  chart_topology_embedding_vec        VECTOR(768),
  per_graha_story_arc_jsonb           JSONB,
  graphml_full_export_jsonb           JSONB,
  gexf_full_export_jsonb              JSONB,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type)
);

CREATE INDEX cgm_topology_chart_idx        ON bodha_cgm_chart_topology_summary (chart_id, ayanamsha_id, snapshot_type);
CREATE INDEX cgm_topology_fingerprint_idx  ON bodha_cgm_chart_topology_summary (graph_fingerprint_hash);
CREATE INDEX cgm_topology_embedding_hnsw   ON bodha_cgm_chart_topology_summary USING hnsw (chart_topology_embedding_vec vector_cosine_ops);

-- ────────────────────────────────────────────────────────────────────────────
-- §13.1  bodha_cgm_paths  (final-dispositor chains + path analysis; bo_karanajala)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_cgm_paths (
  path_id                             UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  path_type                           TEXT NOT NULL,  -- 'dispositor_chain'|'significator_path'|'final_dispositor_convergence'
  from_node_id                        UUID NOT NULL,
  to_node_id                          UUID NOT NULL,
  path_node_ids_array                 UUID[] NOT NULL,  -- ordered path
  path_edge_ids_array                 UUID[] NOT NULL,
  path_length                         INT NOT NULL,
  path_strength                       NUMERIC NOT NULL,   -- product of edge strengths
  is_final_dispositor                 BOOLEAN NOT NULL,   -- true = terminates at a self-dispositing node
  convergence_count                   INT NOT NULL,        -- number of chains that converge to this terminus
  centrality_formula_version          TEXT NOT NULL,
  path_label_human                    TEXT,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, path_type, from_node_id, to_node_id)
);

CREATE INDEX cgm_paths_chart_idx         ON bodha_cgm_paths (chart_id, ayanamsha_id, path_type);
CREATE INDEX cgm_paths_final_disp_idx    ON bodha_cgm_paths (chart_id, ayanamsha_id) WHERE is_final_dispositor = true;
CREATE INDEX cgm_paths_convergence_idx   ON bodha_cgm_paths (chart_id, ayanamsha_id, convergence_count DESC);

-- ────────────────────────────────────────────────────────────────────────────
-- A13  bodha_rm_resonances  (per-graha resonance targets; A13 Table 1)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_rm_resonances (
  resonance_id                        UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  graha                               TEXT NOT NULL,
  resonance_score                     NUMERIC NOT NULL,
  resonance_score_formula_version     TEXT NOT NULL,
  weakness_score                      NUMERIC,
  contradiction_factor                NUMERIC,
  domain_burden                       NUMERIC,
  motif_burden                        NUMERIC,
  is_yoga_karaka_flag                 BOOLEAN,
  is_chara_karaka_role                TEXT,
  weakest_rank_in_chart               INT,
  remedy_priority_class               TEXT,
  associated_doshas_array             TEXT[],
  associated_motifs_array             UUID[],
  associated_cdlm_cells_array         UUID[],
  ephemeris_audit_jsonb               JSONB,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, graha)
);

CREATE INDEX rm_resonances_chart_idx    ON bodha_rm_resonances (chart_id, ayanamsha_id);
CREATE INDEX rm_resonances_rank_idx     ON bodha_rm_resonances (chart_id, ayanamsha_id, weakest_rank_in_chart);
CREATE INDEX rm_resonances_doshas_gin   ON bodha_rm_resonances USING gin (associated_doshas_array);

-- ────────────────────────────────────────────────────────────────────────────
-- A13  bodha_rm_remedy_prescriptions  (A13 Table 2)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_rm_remedy_prescriptions (
  prescription_id                             UUID PRIMARY KEY,
  chart_id                                    UUID NOT NULL,
  ayanamsha_id                                TEXT NOT NULL,
  build_id                                    UUID NOT NULL,
  snapshot_type                               TEXT NOT NULL,
  target_graha                                TEXT NOT NULL,
  target_resonance_id                         UUID NOT NULL REFERENCES bodha_rm_resonances(resonance_id),
  -- Tradition
  tradition                                   TEXT NOT NULL,
  sub_tradition                               TEXT,
  -- Remedy category
  remedy_category                             TEXT NOT NULL,
  remedy_id_g27                               TEXT NOT NULL,
  remedy_label_human                          TEXT NOT NULL,
  prescription_detail_jsonb                   JSONB NOT NULL,
  -- Strength
  classical_strength_rating                   TEXT,
  classical_source_citation_id               TEXT NOT NULL,
  classical_source_text_jsonb                 JSONB,
  -- Targeting
  targets_motif_id                            UUID,
  targets_cell_id                             UUID,
  targets_dosha_class                         TEXT,
  resonance_match_score                       NUMERIC,
  match_score_formula_version                 TEXT,
  -- Compatibility
  counter_indications_array                   TEXT[],
  incompatible_with_prescription_ids_array    UUID[],
  prerequisite_prescription_ids_array         UUID[],
  -- Feasibility
  feasibility_score                           NUMERIC,
  estimated_cost_inr_range_jsonb              JSONB,
  estimated_time_minutes_daily                NUMERIC,
  ritual_complexity_class                     TEXT,
  -- Acharya review
  requires_acharya_review_flag                BOOLEAN NOT NULL,
  acharya_review_reason_array                 TEXT[],
  -- Cross-tradition convergence
  cross_tradition_corroboration_count         INT,
  cross_tradition_corroborating_traditions_array TEXT[],
  -- Phase sequencing
  phase_sequence_class                        TEXT,
  phase_duration_days                         INT,
  count_prescription_jsonb                    JSONB,
  -- Substitute gem
  substitute_options_jsonb                    JSONB,
  -- Yantra
  yantra_geometry_jsonb                       JSONB,
  pranapratishtha_required_flag               BOOLEAN,
  -- Pilgrimage
  pilgrimage_site_jsonb                       JSONB,
  pilgrimage_priority_rank                    INT,
  -- Chronobiology
  recommended_hora_lord_array                 TEXT[],
  recommended_choghadiya_window_array         TEXT[],
  initiation_lunar_phase_recommendation_array TEXT[],
  recommended_facing_direction                TEXT,
  -- M6 outcome tracking
  outcome_tracking_placeholder_jsonb          JSONB,
  -- pgvector
  prescription_embedding_vec                  VECTOR(768),
  verification_pass_status                    TEXT NOT NULL,
  citation_ref                                TEXT NOT NULL,
  citation_human                              TEXT NOT NULL,
  computed_at                                 TIMESTAMPTZ NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, target_graha, tradition,
          sub_tradition, remedy_category, remedy_id_g27)
);

CREATE INDEX rm_prescriptions_chart_idx       ON bodha_rm_remedy_prescriptions (chart_id, ayanamsha_id);
CREATE INDEX rm_prescriptions_target_idx      ON bodha_rm_remedy_prescriptions (chart_id, ayanamsha_id, target_graha);
CREATE INDEX rm_prescriptions_tradition_idx   ON bodha_rm_remedy_prescriptions (chart_id, ayanamsha_id, tradition);
CREATE INDEX rm_prescriptions_category_idx    ON bodha_rm_remedy_prescriptions (chart_id, ayanamsha_id, remedy_category);
CREATE INDEX rm_prescriptions_match_score_idx ON bodha_rm_remedy_prescriptions (chart_id, ayanamsha_id, resonance_match_score DESC);
CREATE INDEX rm_prescriptions_review_idx      ON bodha_rm_remedy_prescriptions (chart_id, ayanamsha_id) WHERE requires_acharya_review_flag = true;
CREATE INDEX rm_prescriptions_counter_gin     ON bodha_rm_remedy_prescriptions USING gin (counter_indications_array);
CREATE INDEX rm_prescriptions_embedding_hnsw  ON bodha_rm_remedy_prescriptions USING hnsw (prescription_embedding_vec vector_cosine_ops);

-- ────────────────────────────────────────────────────────────────────────────
-- A13  bodha_rm_dasha_windowed_prescriptions  (A13 Table 3)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_rm_dasha_windowed_prescriptions (
  window_prescription_id              UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  base_prescription_id                UUID NOT NULL REFERENCES bodha_rm_remedy_prescriptions(prescription_id),
  dasha_system                        TEXT NOT NULL,
  dasha_level                         TEXT NOT NULL,
  dasha_lord                          TEXT NOT NULL,
  window_start_iso                    TIMESTAMPTZ NOT NULL,
  window_end_iso                      TIMESTAMPTZ NOT NULL,
  window_intensity_multiplier         NUMERIC,
  schedule_jsonb                      JSONB,
  phase_within_window                 TEXT,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT,
  citation_human                      TEXT,
  computed_at                         TIMESTAMPTZ NOT NULL
);

CREATE INDEX rm_windowed_chart_idx  ON bodha_rm_dasha_windowed_prescriptions (chart_id, ayanamsha_id, dasha_system);
CREATE INDEX rm_windowed_time_idx   ON bodha_rm_dasha_windowed_prescriptions (chart_id, ayanamsha_id, window_start_iso, window_end_iso);

-- ────────────────────────────────────────────────────────────────────────────
-- A13  bodha_rm_dosha_remedy_bundles  (A13 Table 4)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_rm_dosha_remedy_bundles (
  bundle_id                           UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  dosha_class                         TEXT NOT NULL,
  active_flag                         BOOLEAN NOT NULL,
  intensity_score                     NUMERIC,
  cancellation_count                  INT,
  prescription_ids_in_bundle_array    UUID[] NOT NULL,
  bundle_summary_jsonb                JSONB,
  classical_source_citation_id        TEXT NOT NULL,
  active_dasha_windows_jsonb          JSONB,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, dosha_class)
);

CREATE INDEX rm_dosha_bundles_chart_idx  ON bodha_rm_dosha_remedy_bundles (chart_id, ayanamsha_id);
CREATE INDEX rm_dosha_bundles_active_idx ON bodha_rm_dosha_remedy_bundles (chart_id, ayanamsha_id) WHERE active_flag = true;

-- ────────────────────────────────────────────────────────────────────────────
-- A13  bodha_rm_pattern_remedies  (A13 Table 5)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_rm_pattern_remedies (
  pattern_remedy_id                   UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  source_kind                         TEXT NOT NULL,  -- 'cdlm_pattern_cluster'|'cgm_motif'
  source_id                           UUID NOT NULL,
  remedy_theme                        TEXT NOT NULL,
  prescription_ids_array              UUID[] NOT NULL,
  theme_strength                      NUMERIC,
  cross_tradition_unanimity_score     NUMERIC,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT,
  citation_human                      TEXT,
  computed_at                         TIMESTAMPTZ NOT NULL
);

CREATE INDEX rm_pattern_remedies_chart_idx ON bodha_rm_pattern_remedies (chart_id, ayanamsha_id, source_kind);

-- ────────────────────────────────────────────────────────────────────────────
-- A13  bodha_rm_chart_summary  (A13 Table 6; chart-level priority profile)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_rm_chart_summary (
  summary_id                          UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  top_3_resonance_targets_jsonb       JSONB,
  top_10_priority_prescriptions_jsonb JSONB,
  recommended_intensity_class         TEXT,
  recommended_remedy_phase_sequence_jsonb JSONB,
  total_active_dosha_count            INT,
  primary_dosha_class                 TEXT,
  cross_tradition_convergence_jsonb   JSONB,
  remedy_chart_typology               TEXT,
  chart_remedy_embedding_vec          VECTOR(768),
  acharya_review_required_count       INT,
  feasibility_assessment_jsonb        JSONB,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT,
  citation_human                      TEXT,
  computed_at                         TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type)
);

CREATE INDEX rm_chart_summary_idx ON bodha_rm_chart_summary (chart_id, ayanamsha_id);

-- ────────────────────────────────────────────────────────────────────────────
-- bo_samskara  bodha_signal_embeddings  (1:1 with MSR signals; pgvector)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE bodha_signal_embeddings (
  embedding_id                        UUID PRIMARY KEY,
  signal_id                           UUID NOT NULL REFERENCES bodha_msr_signals(signal_id),
  chart_id                            UUID NOT NULL,  -- denormalized for efficient count_sql
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  embedding_vec                       VECTOR(768) NOT NULL,
  embedding_model                     TEXT NOT NULL,
  embedding_model_version             TEXT NOT NULL,
  embedding_input_summary             TEXT,           -- truncated text used as embedding input
  computed_at                         TIMESTAMPTZ NOT NULL,
  UNIQUE (signal_id)
);

CREATE INDEX bse_chart_idx          ON bodha_signal_embeddings (chart_id, ayanamsha_id);
CREATE INDEX bse_embedding_hnsw     ON bodha_signal_embeddings USING hnsw (embedding_vec vector_cosine_ops);

-- ────────────────────────────────────────────────────────────────────────────
-- bo_pramana_mapa  synthesis_quality_scorecard  (global; no chart_id filter)
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE synthesis_quality_scorecard (
  scorecard_id                        UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  build_id                            UUID NOT NULL,
  scored_at                           TIMESTAMPTZ NOT NULL,
  -- Per-asset row counts
  msr_signal_count                    INT,
  cdlm_cell_count                     INT,
  cgm_node_count                      INT,
  cgm_edge_count                      INT,
  rm_resonance_count                  INT,
  rm_prescription_count               INT,
  embedding_count                     INT,
  convergence_count                   INT,
  contradiction_count                 INT,
  -- Quality gates
  divergent_flagged_count             INT NOT NULL DEFAULT 0,
  two_pass_verified_pct               NUMERIC,
  documented_approximation_pct        NUMERIC,
  msr_no_threshold_drop_flag          BOOLEAN,   -- true = weak tail present
  msr_citation_ref_coverage_pct       NUMERIC,
  -- Formula versions in use
  salience_formula_version            TEXT,
  linkage_formula_version             TEXT,
  resonance_formula_version           TEXT,
  convergence_formula_version         TEXT,
  centrality_formula_version          TEXT,
  -- Trap checks
  trap1_authority_inversion_count     INT NOT NULL DEFAULT 0,  -- should be 0
  trap2_narration_leak_count          INT NOT NULL DEFAULT 0,  -- should be 0
  notes                               TEXT
);

CREATE INDEX scorecard_chart_idx ON synthesis_quality_scorecard (chart_id, scored_at DESC);

-- ────────────────────────────────────────────────────────────────────────────
-- A10 §11 Materialized Views (3; natal-fixed; refresh at build close)
-- ────────────────────────────────────────────────────────────────────────────

CREATE MATERIALIZED VIEW mv_msr_top_signals_per_chart AS
  SELECT chart_id, ayanamsha_id, signal_id, signal_type_id, signal_type_class, signal_tradition,
         computed_salience, top_k_salience_rank, signature_class, domains_affected_array,
         verification_pass_status
  FROM bodha_msr_signals
  WHERE top_k_salience_rank <= 100
WITH NO DATA;

CREATE UNIQUE INDEX mv_msr_top_signals_pk ON mv_msr_top_signals_per_chart (chart_id, ayanamsha_id, signal_id);
CREATE INDEX mv_msr_top_signals_rank_idx  ON mv_msr_top_signals_per_chart (chart_id, ayanamsha_id, top_k_salience_rank);

CREATE MATERIALIZED VIEW mv_msr_recurring_patterns_per_chart AS
  SELECT chart_id, ayanamsha_id, recurring_pattern_marker,
         count(*) AS signal_count,
         sum(computed_salience) AS total_salience,
         max(computed_salience) AS max_salience
  FROM bodha_msr_signals
  WHERE recurring_pattern_marker IS NOT NULL
  GROUP BY chart_id, ayanamsha_id, recurring_pattern_marker
WITH NO DATA;

CREATE UNIQUE INDEX mv_msr_patterns_pk ON mv_msr_recurring_patterns_per_chart (chart_id, ayanamsha_id, recurring_pattern_marker);

CREATE MATERIALIZED VIEW mv_msr_domain_summary AS
  SELECT chart_id, ayanamsha_id, domain,
         count(*) AS signal_count,
         sum(salience) AS total_domain_salience,
         max(salience) AS max_domain_salience
  FROM bodha_msr_signals,
       LATERAL jsonb_each_text(domain_salience_jsonb) AS d(domain, salience_text),
       LATERAL (SELECT d.salience_text::NUMERIC AS salience) AS s
  GROUP BY chart_id, ayanamsha_id, domain
WITH NO DATA;

CREATE UNIQUE INDEX mv_msr_domain_summary_pk ON mv_msr_domain_summary (chart_id, ayanamsha_id, domain);

-- ────────────────────────────────────────────────────────────────────────────
-- A11 §4 Materialized Views (5; natal-fixed)
-- ────────────────────────────────────────────────────────────────────────────

CREATE MATERIALIZED VIEW mv_cdlm_static_summary AS
  SELECT c.chart_id, c.ayanamsha_id,
         c.domain_row, c.domain_col, c.computed_linkage_strength,
         c.shared_signal_count, c.cross_domain_contradiction_flag,
         c.dominant_linkage_rank_in_chart, c.domain_relationship_class,
         s.chart_typology_class, s.dominant_3_domains_array, s.weakest_3_domains_array
  FROM bodha_cdlm_cells c
  JOIN bodha_cdlm_chart_summary s
    ON s.chart_id = c.chart_id
   AND s.ayanamsha_id = c.ayanamsha_id
   AND s.snapshot_type = c.snapshot_type
  WHERE c.snapshot_type = 'static_natal_9x9'
WITH NO DATA;

CREATE UNIQUE INDEX mv_cdlm_static_pk ON mv_cdlm_static_summary (chart_id, ayanamsha_id, domain_row, domain_col);

CREATE MATERIALIZED VIEW mv_cdlm_top_K_links_per_chart AS
  SELECT chart_id, ayanamsha_id, cell_id, domain_row, domain_col,
         snapshot_type, computed_linkage_strength, dominant_linkage_rank_in_chart
  FROM bodha_cdlm_cells
  WHERE dominant_linkage_rank_in_chart <= 20
WITH NO DATA;

CREATE UNIQUE INDEX mv_cdlm_top_k_pk ON mv_cdlm_top_K_links_per_chart (chart_id, ayanamsha_id, cell_id);

CREATE MATERIALIZED VIEW mv_cdlm_per_tradition_summary AS
  SELECT chart_id, ayanamsha_id, tradition_view_id, domain_row, domain_col,
         computed_linkage_strength, shared_signal_count
  FROM bodha_cdlm_cells
  WHERE tradition_view_id IS NOT NULL AND snapshot_type LIKE 'static_tradition_%'
WITH NO DATA;

CREATE UNIQUE INDEX mv_cdlm_tradition_pk ON mv_cdlm_per_tradition_summary (chart_id, ayanamsha_id, tradition_view_id, domain_row, domain_col);

CREATE MATERIALIZED VIEW mv_cdlm_dasha_window_lookup AS
  SELECT chart_id, ayanamsha_id, dynamic_system_id,
         dynamic_maha_lord, dynamic_antar_lord,
         dynamic_window_start_iso, dynamic_window_end_iso,
         domain_row, domain_col, computed_linkage_strength, top_k_rank_in_snapshot
  FROM bodha_cdlm_cells
  WHERE snapshot_type = 'dynamic_maha_antar'
WITH NO DATA;

CREATE INDEX mv_cdlm_dasha_window_idx ON mv_cdlm_dasha_window_lookup (chart_id, ayanamsha_id, dynamic_system_id, dynamic_window_start_iso, dynamic_window_end_iso);

CREATE MATERIALIZED VIEW mv_cdlm_pattern_summary AS
  SELECT chart_id, ayanamsha_id, pattern_id, pattern_marker_type,
         involved_domains_array, cluster_strength_total, remedy_theme_jsonb
  FROM bodha_cdlm_pattern_clusters
WITH NO DATA;

CREATE UNIQUE INDEX mv_cdlm_pattern_pk ON mv_cdlm_pattern_summary (chart_id, ayanamsha_id, pattern_id);

COMMIT;

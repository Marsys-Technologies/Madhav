-- Migration 325: L2 Bodha — Enriched Schema (DROP old + CREATE enriched tables)
--
-- Context: The old bodha_* tables (bodha_signals, bodha_graph, bodha_graph_edges,
-- bodha_graph_staging, bodha_remediation, bodha_remediation_staging, bodha_resonance,
-- bodha_signal_embeddings, bodha_domain_links) are the pre-226 schema, EMPTY, and being
-- replaced by the full enriched L2 contract designed in L2_BODHA_SCHEMA_REDESIGN_v1_0.md.
-- Migration 226 (supabase/migrations/226_bodha_spec_tables.sql) was NEVER applied — this
-- migration supersedes it by creating all tables with the enriched schema + new asset tables.
--
-- Disposition classifier:
--   bodha_signals: live reader in consult/route.ts — REPOINTED to bodha_msr_signals before
--                  this migration (commit includes that fix). Table is EMPTY (never built).
--   bodha_graph, bodha_graph_edges: brahma_pipeline.py non-fatal try/except only. EMPTY.
--   bodha_graph_staging, bodha_remediation, bodha_remediation_staging, bodha_resonance,
--   bodha_domain_links, bodha_signal_embeddings: brahma_pipeline.py non-fatal only. EMPTY.
-- All old tables EMPTY — confirmed pre-DROP. No data risk.
--
-- Creates:
--   22 tables: bodha_msr_signals (enriched) + contradictions + 5 CDLM + convergence +
--              5 CGM + cgm_paths + 6 RM + signal_embeddings + scorecard +
--              question_lenses + chart_gestalt + discoveries + anomalies
--   1 view: vw_chart_digest
--   8 materialized views (natal-fixed; WITH NO DATA)
--   asset_registry entries for all 10 bo_* assets
--
-- Migration 325 (prod target: post-323 → to be applied before L2 writers run)

BEGIN;

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 1 — DROP OLD BODHA TABLES (all empty; disposition confirmed)
-- ═══════════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS bodha_remediation_staging CASCADE;
DROP TABLE IF EXISTS bodha_graph_staging CASCADE;
DROP TABLE IF EXISTS bodha_remediation CASCADE;
DROP TABLE IF EXISTS bodha_resonance CASCADE;
DROP TABLE IF EXISTS bodha_domain_links CASCADE;
DROP TABLE IF EXISTS bodha_graph_edges CASCADE;
DROP TABLE IF EXISTS bodha_graph CASCADE;
DROP TABLE IF EXISTS bodha_signal_embeddings CASCADE;
DROP TABLE IF EXISTS bodha_signals CASCADE;
-- synthesis_quality_scorecard pre-exists in prod (created by earlier partial DDL)
DROP TABLE IF EXISTS synthesis_quality_scorecard CASCADE;

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 2 — bo_laksana: bodha_msr_signals (enriched; supersedes 226 §A10)
-- Cross-cutting spine columns on every signal: fact_kind / source_l1_asset /
-- source_subsystem / signal_summary_text / signal_headline_text /
-- classical_sources_jsonb / epistemic_tier / epistemic_jsonb /
-- salience_conditioned_by_jsonb / signature_tier / valence / lel_origin / varga_id
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE bodha_msr_signals (
  -- Identity
  signal_id                                   UUID PRIMARY KEY,
  chart_id                                    UUID NOT NULL,
  ayanamsha_id                                TEXT NOT NULL,
  build_id                                    UUID NOT NULL,

  -- Classification
  signal_type_id                              TEXT NOT NULL,
  signal_type_class                           TEXT NOT NULL,   -- widened: relationship/magnitude/position/time_window/birth_moment/configuration/medical/vastu/prashna/annual/dasha_period
  signal_tradition                            TEXT NOT NULL,

  -- ── Cross-cutting spine (enriched beyond 226) ────────────────────────────
  fact_kind                                   TEXT NOT NULL,   -- relationship|magnitude|position|time_window|birth_moment|configuration|medical|vastu|prashna|annual|dasha_period|absence
  source_l1_asset                             TEXT NOT NULL,   -- which of the 14 ga_* assets emitted this
  source_subsystem                            TEXT NOT NULL,   -- structural|nakshatra|strength_ashtakavarga|medical|vastu|yoga|tajaka|sade_sati|panchanga|varga|sensitive|dasha
  signal_summary_text                         TEXT,            -- lossless deterministic NL (every config key); embedding input for bo_samskara
  signal_headline_text                        TEXT,            -- short deterministic sentence for display/retrieval
  classical_sources_jsonb                     JSONB,           -- {catalog_ids[], rule_ids[], text_chunk_ids[], citations[]} — structured L0 bridge
  varga_id                                    TEXT,            -- which varga the signal lives in (e.g. D1, D9, D10)
  varga_provenance_jsonb                      JSONB,           -- weight + varga-source breakdown
  epistemic_tier                              TEXT,            -- two_pass_verified | documented_approximation (carried from L1)
  epistemic_jsonb                             JSONB,           -- {tradition_agreement_state, ayanamsha_fragility, computation_vs_interpretation, calibration_hook}
  salience_conditioned_by_jsonb               JSONB,           -- [{signal_id, effect: amplifies|damps, basis}]
  signature_tier                              TEXT,            -- chart_defining|major|supporting|background
  valence                                     TEXT,            -- benefic|malefic|mixed|neutral
  lel_origin                                  BOOLEAN NOT NULL DEFAULT false,  -- LEL discipline: true if derived from LEL-gated data

  -- Structured configuration
  configuration_jsonb                         JSONB NOT NULL,
  constituent_facts_array                     TEXT[] NOT NULL,  -- L1 fact_ids (read from fact_value_jsonb.constituent_fact_ids for ga_structural)
  constituent_signals_array                   UUID[],

  -- Classical sourcing (legacy flat; kept for backward compat; prefer classical_sources_jsonb)
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
  dasha_activation_proximity_score            NUMERIC,          -- L3-fill hook: bo_laksana writes NULL
  house_weight_multiplier                     NUMERIC,
  ashtakavarga_support_multiplier             NUMERIC,
  aspect_modifier                             NUMERIC,
  vargottama_amplification                    NUMERIC,
  argala_modifier                             NUMERIC,
  neechabhanga_modifier                       NUMERIC,
  cancellation_modifier                       NUMERIC,
  computed_salience                           NUMERIC NOT NULL,
  salience_formula_version                    TEXT NOT NULL,
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

  -- Digest hooks (for bo_samvada)
  top_k_salience_rank                         INT,
  system_convergence_count                    INT,
  signature_class                             TEXT,            -- static structural fingerprint (NOT transit-matching key)

  -- Contradictions
  contradicts_signals_array                   UUID[],

  -- Active periods — L3-fill hooks (bo_laksana writes NULL)
  active_duration_class                       TEXT NOT NULL,
  active_dasha_periods_jsonb                  JSONB,           -- L3-fill hook
  activation_predicted_dates_jsonb            JSONB,           -- L3-fill hook
  predicted_outcome_class                     TEXT,

  -- Cross-ayanamsha
  cross_ayanamsha_consistency_score           NUMERIC,         -- 0–5 (how many of 5 ayanamshas the signal holds in)

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

-- S2: chart_id leads every index
-- S5: fact_kind, source_l1_asset, source_subsystem, valence, signature_tier, varga_id must be indexed columns
CREATE INDEX msr_chart_aya_idx           ON bodha_msr_signals (chart_id, ayanamsha_id);
CREATE INDEX msr_signal_type_idx         ON bodha_msr_signals (signal_type_id);
CREATE INDEX msr_signal_class_idx        ON bodha_msr_signals (signal_type_class, signal_tradition);
CREATE INDEX msr_salience_rank_idx       ON bodha_msr_signals (chart_id, ayanamsha_id, computed_salience DESC);
CREATE INDEX msr_domains_gin_idx         ON bodha_msr_signals USING gin (domains_affected_array);
CREATE INDEX msr_constituent_facts_gin   ON bodha_msr_signals USING gin (constituent_facts_array);
CREATE INDEX msr_top_k_rank_idx          ON bodha_msr_signals (chart_id, ayanamsha_id, top_k_salience_rank);
CREATE INDEX msr_signature_class_idx     ON bodha_msr_signals (signature_class) WHERE signature_class IS NOT NULL;
CREATE INDEX msr_recurring_pattern_idx   ON bodha_msr_signals (recurring_pattern_marker) WHERE recurring_pattern_marker IS NOT NULL;
-- Enriched spine indexes (S5)
CREATE INDEX msr_fact_kind_idx           ON bodha_msr_signals (chart_id, fact_kind);
CREATE INDEX msr_source_l1_asset_idx     ON bodha_msr_signals (chart_id, source_l1_asset);
CREATE INDEX msr_source_subsystem_idx    ON bodha_msr_signals (chart_id, source_subsystem);
CREATE INDEX msr_valence_idx             ON bodha_msr_signals (chart_id, valence) WHERE valence IS NOT NULL;
CREATE INDEX msr_signature_tier_idx      ON bodha_msr_signals (chart_id, signature_tier) WHERE signature_tier IS NOT NULL;
CREATE INDEX msr_varga_id_idx            ON bodha_msr_signals (chart_id, varga_id) WHERE varga_id IS NOT NULL;
CREATE INDEX msr_lel_origin_idx          ON bodha_msr_signals (chart_id, lel_origin) WHERE lel_origin = true;
CREATE INDEX msr_remedy_hooks_gin        ON bodha_msr_signals USING gin (remedy_hooks_array);

-- ═══════════════════════════════════════════════════════════════════════════════
-- bodha_contradictions (owned by bo_karanajala; supersedes 226 §13.1)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE bodha_contradictions (
  contradiction_id         UUID PRIMARY KEY,
  chart_id                 UUID NOT NULL,
  ayanamsha_id             TEXT NOT NULL,
  build_id                 UUID NOT NULL,
  signal_a_id              UUID NOT NULL REFERENCES bodha_msr_signals(signal_id),
  signal_b_id              UUID NOT NULL REFERENCES bodha_msr_signals(signal_id),
  tension_basis_jsonb      JSONB NOT NULL,
  tension_class            TEXT NOT NULL,
  domains_affected_array   TEXT[] NOT NULL,
  combined_salience        NUMERIC NOT NULL,
  resolution_hint_jsonb    JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref             TEXT NOT NULL,
  citation_human           TEXT NOT NULL,
  computed_at              TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, signal_a_id, signal_b_id)
);

CREATE INDEX contradictions_chart_idx    ON bodha_contradictions (chart_id, ayanamsha_id);
CREATE INDEX contradictions_domains_gin  ON bodha_contradictions USING gin (domains_affected_array);

-- ═══════════════════════════════════════════════════════════════════════════════
-- CDLM tables (bo_sangati) — 5 tables + convergence; from 226 §A11
-- ═══════════════════════════════════════════════════════════════════════════════

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
  -- CGM enrichment hooks
  cgm_subgraph_cluster_id                         TEXT,
  cgm_bridge_edge_seeds_jsonb                     JSONB,
  cgm_domain_super_node_strength_contribution_jsonb JSONB,
  cgm_antagonist_edge_seeds_jsonb                 JSONB,
  -- RM enrichment hooks
  cell_remedy_priority_rank                       INT,
  weakest_constituent_graha_jsonb                 JSONB,
  pattern_remedy_theme_jsonb                      JSONB,
  cell_remedy_hooks_array                         TEXT[],
  -- UCN/gestalt hooks
  dominant_linkage_rank_in_chart                  INT,
  domain_relationship_class                       TEXT,
  narrative_thread_seed                           JSONB,
  -- L3 hooks (bo_sangati writes NULL)
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

CREATE TABLE bodha_cdlm_evolution_gradients (
  gradient_id                         UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  dynamic_system_id                   TEXT NOT NULL,
  tradition_view_id                   TEXT,
  domain_row                          TEXT NOT NULL,
  domain_col                          TEXT NOT NULL,
  evolution_class                     TEXT NOT NULL,
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

CREATE TABLE bodha_convergence (
  convergence_id               UUID PRIMARY KEY,
  chart_id                     UUID NOT NULL,
  ayanamsha_id                 TEXT NOT NULL,
  build_id                     UUID NOT NULL,
  domain                       TEXT NOT NULL,
  snapshot_type                TEXT NOT NULL,
  dynamic_system_id            TEXT,
  dynamic_maha_lord            TEXT,
  dynamic_antar_lord           TEXT,
  convergence_count            INT NOT NULL,
  convergence_score            NUMERIC NOT NULL,
  convergence_formula_version  TEXT NOT NULL,
  cross_tradition_count        INT NOT NULL,
  top_signal_ids_array         UUID[] NOT NULL,
  tradition_breakdown_jsonb    JSONB NOT NULL,
  salience_weighted_sum        NUMERIC NOT NULL,
  salience_max                 NUMERIC NOT NULL,
  contradiction_count          INT NOT NULL,
  classical_sources_jsonb      JSONB,           -- enriched: L0 citations for the convergence itself
  verification_pass_status     TEXT NOT NULL,
  citation_ref                 TEXT NOT NULL,
  citation_human               TEXT NOT NULL,
  computed_at                  TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, domain, snapshot_type, dynamic_system_id,
          dynamic_maha_lord, dynamic_antar_lord)
);

CREATE INDEX convergence_chart_idx     ON bodha_convergence (chart_id, ayanamsha_id, domain);
CREATE INDEX convergence_score_idx     ON bodha_convergence (chart_id, ayanamsha_id, convergence_score DESC);

-- ═══════════════════════════════════════════════════════════════════════════════
-- CGM tables (bo_bimba + bo_karanajala) — 5 tables + paths; from 226 §A12
-- bodha_cgm_edges enriched with full value-vector (S5: intrinsic_strength/valence/
-- affected_domains/directionality/weight_varga_source/relationship_basis)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE bodha_cgm_nodes (
  node_id                             UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  node_type                           TEXT NOT NULL,   -- widened: graha|house|sign|nakshatra|special_point|config|composite
  node_subject                        TEXT NOT NULL,
  node_label_human                    TEXT NOT NULL,
  position_in_chart_jsonb             JSONB,
  strength_score                      NUMERIC,
  dignity_state                       TEXT,
  source_subsystem                    TEXT,            -- enriched: which subsystem this node belongs to
  -- igraph-computed centrality (S4: all flat)
  degree_in                           INT NOT NULL,
  degree_out                          INT NOT NULL,
  betweenness_centrality              NUMERIC,
  eigenvector_centrality              NUMERIC,
  pagerank_score                      NUMERIC,
  clustering_coefficient              NUMERIC,
  closeness_centrality                NUMERIC,
  harmonic_centrality                 NUMERIC,
  core_number                         INT,
  articulation_point_flag             BOOLEAN NOT NULL DEFAULT false,  -- S4: structural hole detection
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
  -- pgvector (S3: HNSW)
  node_embedding_vec                  VECTOR(768),
  -- Provenance
  ephemeris_audit_jsonb               JSONB,
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
CREATE INDEX cgm_nodes_subsystem_idx    ON bodha_cgm_nodes (chart_id, source_subsystem) WHERE source_subsystem IS NOT NULL;
CREATE INDEX cgm_nodes_embedding_hnsw   ON bodha_cgm_nodes USING hnsw (node_embedding_vec vector_cosine_ops);

CREATE TABLE bodha_cgm_edges (
  edge_id                             UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  edge_type                           TEXT NOT NULL,
  from_node_id                        UUID NOT NULL,
  to_node_id                          UUID NOT NULL,
  direction                           TEXT NOT NULL,       -- directed|mutual
  computed_strength                   NUMERIC NOT NULL,
  weight_formula_version              TEXT NOT NULL,
  -- Full edge value-vector (enriched beyond 226 — S5 first-class columns)
  intrinsic_strength                  NUMERIC,             -- classical strength of the aspect/relationship itself
  valence                             TEXT,                -- benefic|malefic|mixed|neutral
  affected_domains                    TEXT[],              -- life domains this edge bears on
  directionality                      TEXT,                -- directed|mutual (first-class; mirrors direction for clarity)
  weight_varga_source                 TEXT,                -- which varga/evidence this weight comes from
  relationship_basis                  TEXT,                -- the classical rule: aspect|conjunction|lordship|dispositor|nakshatra_lord|argala|occupancy|significator
  -- Cross-subsystem edge support
  is_cross_subsystem                  BOOLEAN NOT NULL DEFAULT false,
  subsystem_from                      TEXT,                -- source subsystem for §XS edges
  subsystem_to                        TEXT,                -- target subsystem for §XS edges
  cross_subsystem_mapping_ref         TEXT,                -- L0 mapping table + row_id that grounds this edge
  -- Standard edge properties
  edge_properties_jsonb               JSONB,
  relationship_class                  TEXT,
  semantic_path_class                 TEXT,
  active_duration_class               TEXT,
  active_dasha_periods_jsonb          JSONB,               -- L3-fill hook
  underlying_msr_signal_ids_array     UUID[],
  cross_system_consensus_count        INT,
  cancelled_flag                      BOOLEAN NOT NULL,
  cancelled_by_jsonb                  JSONB,
  cross_ayanamsha_edge_stability_score NUMERIC,
  present_in_traditions_array         TEXT[],
  -- igraph-computed
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
CREATE INDEX cgm_edges_valence_idx      ON bodha_cgm_edges (chart_id, valence) WHERE valence IS NOT NULL;
CREATE INDEX cgm_edges_affected_gin     ON bodha_cgm_edges USING gin (affected_domains);
CREATE INDEX cgm_edges_xsub_idx         ON bodha_cgm_edges (chart_id, is_cross_subsystem) WHERE is_cross_subsystem = true;

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

CREATE TABLE bodha_cgm_paths (
  path_id                             UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  snapshot_type                       TEXT NOT NULL,
  path_type                           TEXT NOT NULL,
  from_node_id                        UUID NOT NULL,
  to_node_id                          UUID NOT NULL,
  path_node_ids_array                 UUID[] NOT NULL,
  path_edge_ids_array                 UUID[] NOT NULL,
  path_length                         INT NOT NULL,
  path_strength                       NUMERIC NOT NULL,
  is_final_dispositor                 BOOLEAN NOT NULL,
  convergence_count                   INT NOT NULL,
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

-- ═══════════════════════════════════════════════════════════════════════════════
-- RM tables (bo_upaya) — 6 tables; from 226 §A13
-- Enriched: classical_sources_jsonb on prescriptions + dosha_bundles (multi-source L0 bridge)
-- ═══════════════════════════════════════════════════════════════════════════════

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

CREATE TABLE bodha_rm_remedy_prescriptions (
  prescription_id                             UUID PRIMARY KEY,
  chart_id                                    UUID NOT NULL,
  ayanamsha_id                                TEXT NOT NULL,
  build_id                                    UUID NOT NULL,
  snapshot_type                               TEXT NOT NULL,
  target_graha                                TEXT NOT NULL,
  target_resonance_id                         UUID NOT NULL REFERENCES bodha_rm_resonances(resonance_id),
  tradition                                   TEXT NOT NULL,
  sub_tradition                               TEXT,
  remedy_category                             TEXT NOT NULL,
  remedy_id_g27                               TEXT NOT NULL,
  remedy_label_human                          TEXT NOT NULL,
  prescription_detail_jsonb                   JSONB NOT NULL,
  classical_strength_rating                   TEXT,
  -- Enriched: structured multi-source L0 citation (replaces single classical_source_citation_id)
  classical_sources_jsonb                     JSONB NOT NULL,  -- {catalog_ids[], rule_ids[], text_chunk_ids[], citations[]}
  classical_source_text_jsonb                 JSONB,
  targets_motif_id                            UUID,
  targets_cell_id                             UUID,
  targets_dosha_class                         TEXT,
  resonance_match_score                       NUMERIC,
  match_score_formula_version                 TEXT,
  counter_indications_array                   TEXT[],
  incompatible_with_prescription_ids_array    UUID[],
  prerequisite_prescription_ids_array         UUID[],
  feasibility_score                           NUMERIC,
  estimated_cost_inr_range_jsonb              JSONB,
  estimated_time_minutes_daily                NUMERIC,
  ritual_complexity_class                     TEXT,
  requires_acharya_review_flag                BOOLEAN NOT NULL,
  acharya_review_reason_array                 TEXT[],
  cross_tradition_corroboration_count         INT,
  cross_tradition_corroborating_traditions_array TEXT[],
  phase_sequence_class                        TEXT,
  phase_duration_days                         INT,
  count_prescription_jsonb                    JSONB,
  substitute_options_jsonb                    JSONB,
  yantra_geometry_jsonb                       JSONB,
  pranapratishtha_required_flag               BOOLEAN,
  pilgrimage_site_jsonb                       JSONB,
  pilgrimage_priority_rank                    INT,
  recommended_hora_lord_array                 TEXT[],
  recommended_choghadiya_window_array         TEXT[],
  initiation_lunar_phase_recommendation_array TEXT[],
  recommended_facing_direction                TEXT,
  outcome_tracking_placeholder_jsonb          JSONB,
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
  classical_sources_jsonb             JSONB,   -- enriched: replaces single classical_source_citation_id
  active_dasha_windows_jsonb          JSONB,
  verification_pass_status            TEXT NOT NULL,
  citation_ref                        TEXT NOT NULL,
  citation_human                      TEXT NOT NULL,
  computed_at                         TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, dosha_class)
);

CREATE INDEX rm_dosha_bundles_chart_idx  ON bodha_rm_dosha_remedy_bundles (chart_id, ayanamsha_id);
CREATE INDEX rm_dosha_bundles_active_idx ON bodha_rm_dosha_remedy_bundles (chart_id, ayanamsha_id) WHERE active_flag = true;

CREATE TABLE bodha_rm_pattern_remedies (
  pattern_remedy_id                   UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  source_kind                         TEXT NOT NULL,
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
CREATE INDEX rm_chart_summary_embedding_hnsw ON bodha_rm_chart_summary USING hnsw (chart_remedy_embedding_vec vector_cosine_ops);

-- ═══════════════════════════════════════════════════════════════════════════════
-- bo_samskara: bodha_signal_embeddings (1:1 with MSR; real Vertex embeddings)
-- Enriched: embedding_model default = text-multilingual-embedding-002 (seed fix)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE bodha_signal_embeddings (
  embedding_id                        UUID PRIMARY KEY,
  signal_id                           UUID NOT NULL REFERENCES bodha_msr_signals(signal_id),
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  embedding_vec                       VECTOR(768) NOT NULL,
  embedding_model                     TEXT NOT NULL DEFAULT 'text-multilingual-embedding-002',  -- SEED FIX: real model pinned
  embedding_model_version             TEXT NOT NULL,
  embedding_input_summary             TEXT,
  computed_at                         TIMESTAMPTZ NOT NULL,
  UNIQUE (signal_id)
);

CREATE INDEX bse_chart_idx          ON bodha_signal_embeddings (chart_id, ayanamsha_id);
CREATE INDEX bse_embedding_hnsw     ON bodha_signal_embeddings USING hnsw (embedding_vec vector_cosine_ops);

-- ═══════════════════════════════════════════════════════════════════════════════
-- bo_pramana_mapa: synthesis_quality_scorecard (enriched with Trap-1 audit cols)
-- ═══════════════════════════════════════════════════════════════════════════════

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
  msr_no_threshold_drop_flag          BOOLEAN,
  msr_citation_ref_coverage_pct       NUMERIC,
  -- Formula versions
  salience_formula_version            TEXT,
  linkage_formula_version             TEXT,
  resonance_formula_version           TEXT,
  convergence_formula_version         TEXT,
  centrality_formula_version          TEXT,
  -- Trap checks (original)
  trap1_authority_inversion_count     INT NOT NULL DEFAULT 0,
  trap2_narration_leak_count          INT NOT NULL DEFAULT 0,
  -- Enriched: Trap-1 audit (constituent_facts resolution + 14-asset coverage)
  unresolved_constituent_facts_count  INT NOT NULL DEFAULT 0,  -- should be 0
  l1_assets_projected_count           INT,                     -- should be 14
  l1_assets_projected_array           TEXT[],                  -- which of the 14 were projected
  -- Judgment integrity gates (bo_pramana_mapa §E)
  lel_zero_leak_pass                  BOOLEAN,
  no_pre_answer_pass                  BOOLEAN,
  pillars_meet_reachability_pass      BOOLEAN,
  ledger_independence_pass            BOOLEAN,
  discovery_not_fabricated_pass       BOOLEAN,
  notes                               TEXT
);

CREATE INDEX scorecard_chart_idx ON synthesis_quality_scorecard (chart_id, scored_at DESC);

-- ═══════════════════════════════════════════════════════════════════════════════
-- NEW TABLES — bo_drishti, bo_samvada, bo_anveshana
-- ═══════════════════════════════════════════════════════════════════════════════

-- bo_drishti: bodha_question_lenses (question-lens table; template + wildcard graph-sweep)
CREATE TABLE bodha_question_lenses (
  lens_id                             UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  question_type                       TEXT NOT NULL,   -- career|wealth|marriage|health|character|spirituality|education|progeny|longevity|...
  template_element_ids_jsonb          JSONB NOT NULL,  -- {houses[], lords[], vargas[], karakas[], yoga_signal_ids[], ledger_id, pivot_ids[], central_dynamic_ids[]}
  wildcard_element_ids_jsonb          JSONB NOT NULL,  -- [{signal_id, salience, reach_path_id, non_template_significant: true}, ...]
  all_relevant_ranked_jsonb           JSONB NOT NULL,  -- full ranked union (template ∪ wildcard), no cap, ranks-never-caps
  lens_template_version               TEXT NOT NULL,
  lens_formula_version                TEXT NOT NULL,
  points_only_assertion               BOOLEAN NOT NULL DEFAULT true,  -- structural audit: must be true; audited by bo_pramana_mapa
  verification_pass_status            TEXT,
  citation_ref                        TEXT,
  computed_at                         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  engine_version                      TEXT NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, question_type)
);

CREATE INDEX ql_chart_idx             ON bodha_question_lenses (chart_id);
CREATE INDEX ql_chart_question_idx    ON bodha_question_lenses (chart_id, question_type);
CREATE INDEX ql_chart_aya_q_idx       ON bodha_question_lenses (chart_id, ayanamsha_id, question_type);
CREATE INDEX ql_wildcard_gin          ON bodha_question_lenses USING gin (wildcard_element_ids_jsonb);
CREATE INDEX ql_ranked_gin            ON bodha_question_lenses USING gin (all_relevant_ranked_jsonb);

-- bo_samvada: bodha_chart_gestalt (thin-writer; pointer-only; no verdicts stored)
CREATE TABLE bodha_chart_gestalt (
  gestalt_id                          UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  gestalt_formula_version             TEXT NOT NULL,
  defining_threads_jsonb              JSONB NOT NULL,  -- signature_tier=chart_defining signals, ranked — pointers only
  central_dynamics_ids                UUID[],          -- CDLM §C2 cross-domain synergy + tension ids
  pivot_ids                           UUID[],          -- CDLM §C3 pivot factor ids
  center_of_gravity_node_ids          UUID[],          -- top-centrality node ids + final-dispositor from CGM
  domain_verdict_map_jsonb            JSONB NOT NULL,  -- {domain → {ledger_id, verdict_class, confidence}} — pointer-only; no stored verdicts
  headline_jsonb                      JSONB NOT NULL,  -- defining strength: top signature thread + strongest domain verdict, as pointers
  watch_list_jsonb                    JSONB NOT NULL,  -- defining vulnerabilities: strongest afflictions + weakest-domain + pivot risk, as pointers
  central_question_jsonb              JSONB NOT NULL,  -- defining antagonistic axis: two poles + linking mechanism, as pointers
  headline_confidence                 NUMERIC(5,4),
  headline_epistemic_jsonb            JSONB,           -- ayanamsha robustness (Move 3 inheritance)
  outliers_jsonb                      JSONB,           -- non_template_significant outliers from bo_drishti
  contested_areas_jsonb               JSONB,           -- domains where evidence is genuinely balanced
  zoom_spine_jsonb                    JSONB NOT NULL,  -- layered navigation: gestalt→domain ledger→signals→L1 fact_ids + L0 citations
  computed_at                         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  engine_version                      TEXT NOT NULL,
  UNIQUE (chart_id, ayanamsha_id)
);

CREATE INDEX cg_chart_idx            ON bodha_chart_gestalt (chart_id);
CREATE INDEX cg_chart_aya_idx        ON bodha_chart_gestalt (chart_id, ayanamsha_id);
CREATE INDEX cg_domain_verdict_gin   ON bodha_chart_gestalt USING gin (domain_verdict_map_jsonb);
CREATE INDEX cg_zoom_spine_gin       ON bodha_chart_gestalt USING gin (zoom_spine_jsonb);
CREATE INDEX cg_outliers_gin         ON bodha_chart_gestalt USING gin (outliers_jsonb);

-- bo_anveshana: bodha_discoveries (passed meaningfulness gate; the crown jewels)
CREATE TABLE bodha_discoveries (
  discovery_id                        UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  discovery_class                     TEXT NOT NULL,   -- latent_insight|structural_hole|community_binder|motif_anomaly|embedding_outlier|distributional_anomaly|pivot_consequence
  discovery_subsystem                 TEXT,            -- structural|nakshatra|strength|medical|vastu|yoga|tajaka|sade_sati|panchanga|divisional; NULL for cross-subsystem
  non_obviousness_score               NUMERIC NOT NULL,
  consequence_score                   NUMERIC NOT NULL,
  composite_discovery_rank            NUMERIC NOT NULL,
  constituent_refs_jsonb              JSONB NOT NULL,  -- signal/node/path/fact ids; REFERENCES only, never invents
  reasoning_chain_jsonb               JSONB NOT NULL,  -- deterministic chain; every step a real edge/path/relationship
  why_an_acharya_misses_it            TEXT NOT NULL,   -- deterministic reason: buried in D24 / low surface salience / etc.
  affected_domains_array              TEXT[],
  epistemic_jsonb                     JSONB,           -- confidence + ayanamsha-fragility (Move 3)
  meaningfulness_basis                TEXT,            -- classical form this discovery corresponds to (D2 gate)
  corroborating_methods_array         TEXT[],
  corroboration_count                 SMALLINT NOT NULL DEFAULT 1,
  surface_reading                     TEXT,            -- D4
  depth_reading                       TEXT,            -- D4
  surface_depth_delta                 TEXT,            -- D4: the discovery itself
  hypothesis_text                     TEXT,            -- D5
  falsifier_jsonb                     JSONB,           -- D5
  calibration_hook                    JSONB,           -- D5: empty at L2; L4/L5 fill
  novelty_class                       TEXT,            -- D6: chart_unique|instance_of_known_class
  novelty_class_id                    TEXT,
  cross_subsystem_root                BOOLEAN NOT NULL DEFAULT false,  -- TRUE for §S.2 discoveries (ranked highest)
  cross_subsystem_refs_jsonb          JSONB,
  provenance                          JSONB,
  computed_at                         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  engine_version                      TEXT NOT NULL
);

CREATE INDEX disc_chart_idx              ON bodha_discoveries (chart_id);
CREATE INDEX disc_chart_aya_idx          ON bodha_discoveries (chart_id, ayanamsha_id);
CREATE INDEX disc_rank_idx               ON bodha_discoveries (chart_id, composite_discovery_rank DESC);
CREATE INDEX disc_class_idx              ON bodha_discoveries (chart_id, discovery_class);
CREATE INDEX disc_subsystem_idx          ON bodha_discoveries (chart_id, discovery_subsystem);
CREATE INDEX disc_xsub_idx               ON bodha_discoveries (chart_id, cross_subsystem_root) WHERE cross_subsystem_root = true;
CREATE INDEX disc_constituent_gin        ON bodha_discoveries USING gin (constituent_refs_jsonb);
CREATE INDEX disc_domains_gin            ON bodha_discoveries USING gin (affected_domains_array);
CREATE INDEX disc_methods_gin            ON bodha_discoveries USING gin (corroborating_methods_array);

-- bo_anveshana: bodha_anomalies (failed meaningfulness gate; retained for research)
CREATE TABLE bodha_anomalies (
  anomaly_id                          UUID PRIMARY KEY,
  chart_id                            UUID NOT NULL,
  ayanamsha_id                        TEXT NOT NULL,
  build_id                            UUID NOT NULL,
  anomaly_type                        TEXT NOT NULL,   -- distributional|graph-structural|embedding|etc.
  discovery_subsystem                 TEXT,
  subject_ref_jsonb                   JSONB NOT NULL,
  anomaly_metric                      TEXT,
  anomaly_value                       NUMERIC,
  chart_baseline_value                NUMERIC,
  sigma_from_baseline                 NUMERIC,
  meaningfulness_gate_result          TEXT NOT NULL DEFAULT 'FAILED',
  computed_at                         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  engine_version                      TEXT NOT NULL
);

CREATE INDEX anom_chart_idx           ON bodha_anomalies (chart_id);
CREATE INDEX anom_type_idx            ON bodha_anomalies (chart_id, anomaly_type);
CREATE INDEX anom_subsystem_idx       ON bodha_anomalies (chart_id, discovery_subsystem);
CREATE INDEX anom_sigma_idx           ON bodha_anomalies (chart_id, sigma_from_baseline DESC);

-- ═══════════════════════════════════════════════════════════════════════════════
-- bo_samvada: vw_chart_digest (read-side view; no per-chart table)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW vw_chart_digest AS
SELECT
  cg.chart_id,
  cg.ayanamsha_id,
  cg.build_id,
  -- Gestalt (bo_samvada)
  cg.headline_jsonb,
  cg.watch_list_jsonb,
  cg.central_question_jsonb,
  cg.domain_verdict_map_jsonb,
  cg.defining_threads_jsonb,
  cg.zoom_spine_jsonb,
  cg.headline_confidence,
  -- CDLM summary (bo_sangati)
  cs.chart_typology_class,
  cs.dominant_3_domains_array,
  cs.weakest_3_domains_array,
  cs.total_chart_linkage,
  cs.contradiction_density,
  -- CGM topology (bo_karanajala)
  ct.total_nodes,
  ct.total_edges,
  ct.top_5_hub_nodes_jsonb,
  ct.top_5_central_nodes_jsonb,
  ct.graph_density,
  -- RM summary (bo_upaya)
  rs.top_3_resonance_targets_jsonb,
  rs.top_10_priority_prescriptions_jsonb,
  rs.remedy_chart_typology,
  rs.total_active_dosha_count
FROM bodha_chart_gestalt cg
LEFT JOIN bodha_cdlm_chart_summary cs
  ON cs.chart_id = cg.chart_id
  AND cs.ayanamsha_id = cg.ayanamsha_id
  AND cs.snapshot_type = 'static_natal_9x9'
LEFT JOIN bodha_cgm_chart_topology_summary ct
  ON ct.chart_id = cg.chart_id
  AND ct.ayanamsha_id = cg.ayanamsha_id
  AND ct.snapshot_type = 'natal'
LEFT JOIN bodha_rm_chart_summary rs
  ON rs.chart_id = cg.chart_id
  AND rs.ayanamsha_id = cg.ayanamsha_id
  AND rs.snapshot_type = 'static_natal';

-- ═══════════════════════════════════════════════════════════════════════════════
-- MATERIALIZED VIEWS (8; natal-fixed; WITH NO DATA; refresh after build)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE MATERIALIZED VIEW mv_msr_top_signals_per_chart AS
  SELECT chart_id, ayanamsha_id, signal_id, signal_type_id, signal_type_class, signal_tradition,
         fact_kind, source_l1_asset, source_subsystem, valence, signature_tier,
         computed_salience, top_k_salience_rank, signature_class, domains_affected_array,
         signal_headline_text, verification_pass_status
  FROM bodha_msr_signals
  WHERE top_k_salience_rank <= 100
WITH NO DATA;

CREATE UNIQUE INDEX mv_msr_top_signals_pk ON mv_msr_top_signals_per_chart (chart_id, ayanamsha_id, signal_id);
CREATE INDEX mv_msr_top_signals_rank_idx  ON mv_msr_top_signals_per_chart (chart_id, ayanamsha_id, top_k_salience_rank);
CREATE INDEX mv_msr_top_signals_kind_idx  ON mv_msr_top_signals_per_chart (chart_id, fact_kind);

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

-- Fixed mv_msr_domain_summary (226 had a bug: alias 'salience' from lateral but then referenced it as column)
CREATE MATERIALIZED VIEW mv_msr_domain_summary AS
  SELECT s.chart_id, s.ayanamsha_id, d.domain,
         count(*) AS signal_count,
         sum(d.domain_salience::NUMERIC) AS total_domain_salience,
         max(d.domain_salience::NUMERIC) AS max_domain_salience
  FROM bodha_msr_signals s,
       LATERAL jsonb_each_text(s.domain_salience_jsonb) AS d(domain, domain_salience)
  GROUP BY s.chart_id, s.ayanamsha_id, d.domain
WITH NO DATA;

CREATE UNIQUE INDEX mv_msr_domain_summary_pk ON mv_msr_domain_summary (chart_id, ayanamsha_id, domain);

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

-- ═══════════════════════════════════════════════════════════════════════════════
-- ASSET REGISTRY — update existing 8 bo_* assets + INSERT 2 new ones
-- Column schema: asset_id, layer, sort_order, sanskrit_name, english_name,
--   english_description, storage_type, target_table, count_sql, target_floor,
--   catalog_status, layer_name
-- ═══════════════════════════════════════════════════════════════════════════════

-- Fix count_sql for bo_samskara (was missing chart_id filter) and bo_pramana_mapa
UPDATE asset_registry SET
  count_sql = 'SELECT count(*) FROM bodha_signal_embeddings WHERE chart_id = $1'
WHERE asset_id = 'bo_samskara';

UPDATE asset_registry SET
  count_sql = 'SELECT count(*) FROM synthesis_quality_scorecard WHERE chart_id = $1'
WHERE asset_id = 'bo_pramana_mapa';

-- Insert the 2 missing new assets (bo_drishti sort_order=9; bo_anveshana sort_order=10)
INSERT INTO asset_registry
  (asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
   storage_type, scope, target_table, count_sql, target_floor, catalog_status, layer_name)
VALUES
  (
    'bo_drishti',
    'bodha', 9, 'Dṛṣṭi', 'Question Lenses',
    'Question-lens table: template + wildcard graph-sweep + ranks-never-caps, per question domain.',
    'postgres_table', 'per_chart', 'bodha_question_lenses',
    'SELECT count(*) FROM bodha_question_lenses WHERE chart_id = $1',
    0, 'DRAFT', 'Bodha'
  ),
  (
    'bo_anveshana',
    'bodha', 10, 'Anveṣaṇa', 'Discovery Engine',
    'Discovery engine: non-obviousness + graph-mining + embedding outliers + bodha_discoveries + anomalies.',
    'postgres_table', 'per_chart', 'bodha_discoveries',
    'SELECT (SELECT count(*) FROM bodha_discoveries WHERE chart_id = $1) + (SELECT count(*) FROM bodha_anomalies WHERE chart_id = $1) AS count',
    0, 'DRAFT', 'Bodha'
  )
ON CONFLICT (asset_id) DO UPDATE SET
  english_name        = EXCLUDED.english_name,
  english_description = EXCLUDED.english_description,
  count_sql           = EXCLUDED.count_sql,
  catalog_status      = EXCLUDED.catalog_status;

COMMIT;

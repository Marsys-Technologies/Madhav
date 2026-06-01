-- Migration 153: META-β/γ/δ/ε — Pattern Catalog + Divergence Ledger + Negative Space Map + Derivation Graph
-- Implements: META_ENHANCEMENTS_SPEC_v1_0.md §2-§5
-- All DDL idempotent (IF NOT EXISTS). All tables follow ON CONFLICT DO NOTHING at write time.

-- ============================================================
-- META-β: l25_pattern_catalog (Π-CATALOG)
-- Every named pattern across the stack in one queryable catalog.
-- ============================================================
CREATE TABLE IF NOT EXISTS l25_pattern_catalog (
  pattern_catalog_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id UUID NOT NULL,
  ayanamsha_id TEXT NOT NULL,
  build_id UUID,

  pattern_kind TEXT NOT NULL,
  -- enum: 'yoga' | 'dosha' | 'cdlm_pattern_cluster' | 'cgm_motif' | 'cgm_sub_graph' |
  --       'magnification' | 'anti_magnification' | 'near_miss_yoga' | 'synchronicity' |
  --       'phase_locked_anchor' | 'classical_archetype' | 'sade_sati_phase' |
  --       'time_convergence_cluster' | 'spiritual_progress_marker' |
  --       'karmic_signature_component' | 'negative_space'
  pattern_name TEXT NOT NULL,
  pattern_strength NUMERIC CHECK (pattern_strength >= 0 AND pattern_strength <= 1),
  active_flag BOOLEAN NOT NULL DEFAULT true,
  active_window_iso_array JSONB,

  source_asset TEXT NOT NULL,
  source_row_id TEXT NOT NULL,

  cross_pattern_link_ids_array UUID[],
  reinforced_by_pattern_ids_array UUID[],
  contradicted_by_pattern_ids_array UUID[],

  classical_source TEXT,
  classical_citation TEXT,

  verification_pass_status TEXT NOT NULL DEFAULT 'unverified',
  citation_ref TEXT NOT NULL DEFAULT 'META_ENHANCEMENTS_SPEC_v1_0.md §2',
  citation_human TEXT NOT NULL DEFAULT 'Pattern Catalog — cross-asset unified',
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE(chart_id, ayanamsha_id, source_asset, source_row_id, pattern_name)
);

CREATE INDEX IF NOT EXISTS pc_chart_aya_idx ON l25_pattern_catalog (chart_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS pc_kind_idx ON l25_pattern_catalog (chart_id, ayanamsha_id, pattern_kind);
CREATE INDEX IF NOT EXISTS pc_active_idx ON l25_pattern_catalog (chart_id, ayanamsha_id) WHERE active_flag = true;

-- ============================================================
-- META-γ: l25_divergence_ledger (Δ-LEDGER)
-- Cross-system disagreement audit trail.
-- ============================================================
CREATE TABLE IF NOT EXISTS l25_divergence_ledger (
  divergence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id UUID NOT NULL,
  ayanamsha_id TEXT NOT NULL,
  build_id UUID,

  divergence_class TEXT NOT NULL,
  -- 'ayanamsha_positional_disagreement' | 'tradition_interpretation_disagreement' |
  -- 'cross_system_temporal' | 'cross_channel_magnification' | 'cross_rule_prediction'
  system_a TEXT NOT NULL,
  system_b TEXT NOT NULL,
  asset_a TEXT NOT NULL,
  asset_b TEXT NOT NULL,
  row_id_a TEXT NOT NULL,
  row_id_b TEXT NOT NULL,
  claim_a TEXT NOT NULL,
  claim_b TEXT NOT NULL,

  divergence_severity TEXT NOT NULL CHECK (divergence_severity IN ('critical','significant','moderate','minor')),
  resolution_status TEXT NOT NULL DEFAULT 'open' CHECK (resolution_status IN ('open','resolved','acknowledged')),
  resolution_note TEXT,
  classical_precedent TEXT,

  verified BOOLEAN NOT NULL DEFAULT false,
  verification_pass_status TEXT NOT NULL DEFAULT 'unverified',
  citation_ref TEXT NOT NULL DEFAULT 'META_ENHANCEMENTS_SPEC_v1_0.md §3',
  citation_human TEXT NOT NULL DEFAULT 'Cross-system divergence detector',
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS dl_chart_aya_idx ON l25_divergence_ledger (chart_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS dl_severity_idx ON l25_divergence_ledger (chart_id, divergence_severity);
CREATE INDEX IF NOT EXISTS dl_status_idx ON l25_divergence_ledger (resolution_status) WHERE resolution_status = 'open';

-- ============================================================
-- META-δ: l25_negative_space_map (Ω-SPACE)
-- Absence-as-feature diagnostic map.
-- ============================================================
CREATE TABLE IF NOT EXISTS l25_negative_space_map (
  absence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id UUID NOT NULL,
  ayanamsha_id TEXT NOT NULL,
  build_id UUID,

  absence_class TEXT NOT NULL,
  -- 'missing_benefic_in_kendra' | 'no_exalted_planets' | 'missing_raj_yoga' |
  -- 'missing_temporal_anchor' | 'no_panchamahapurusha' | 'no_chara_karaka_in_kendra' | etc.
  absent_feature TEXT NOT NULL,
  asset_context TEXT NOT NULL,
  absence_significance TEXT NOT NULL CHECK (absence_significance IN ('high','medium','low')),

  expected_if_present TEXT,
  classical_pattern_violated TEXT,
  acharya_interpretation_cue TEXT,

  verified BOOLEAN NOT NULL DEFAULT false,
  verification_pass_status TEXT NOT NULL DEFAULT 'unverified',
  citation_ref TEXT NOT NULL DEFAULT 'META_ENHANCEMENTS_SPEC_v1_0.md §4',
  citation_human TEXT NOT NULL DEFAULT 'Negative space map — absence as feature',
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE(chart_id, ayanamsha_id, absence_class, absent_feature)
);

CREATE INDEX IF NOT EXISTS ns_chart_aya_idx ON l25_negative_space_map (chart_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS ns_significance_idx ON l25_negative_space_map (chart_id, ayanamsha_id, absence_significance);

-- ============================================================
-- META-ε: l25_derivation_graph_nodes (Φ-TRAIL nodes)
-- L1→L2.5 claim DAG — nodes.
-- ============================================================
CREATE TABLE IF NOT EXISTS l25_derivation_graph_nodes (
  node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id UUID NOT NULL,
  ayanamsha_id TEXT NOT NULL,
  build_id UUID,

  node_kind TEXT NOT NULL CHECK (node_kind IN ('l1_fact','l25_claim','mcp_tool_output','external_input')),
  node_label TEXT NOT NULL,
  source_table TEXT,
  source_row_id TEXT,
  claim_text TEXT,
  confidence NUMERIC CHECK (confidence >= 0 AND confidence <= 1),

  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE(chart_id, ayanamsha_id, node_kind, source_table, source_row_id)
);

CREATE INDEX IF NOT EXISTS dg_nodes_chart_idx ON l25_derivation_graph_nodes (chart_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS dg_nodes_kind_idx ON l25_derivation_graph_nodes (node_kind);

-- ============================================================
-- META-ε: l25_derivation_graph_edges (Φ-TRAIL edges)
-- L1→L2.5 claim DAG — edges.
-- ============================================================
CREATE TABLE IF NOT EXISTS l25_derivation_graph_edges (
  edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id UUID NOT NULL,
  ayanamsha_id TEXT NOT NULL,
  build_id UUID,

  source_node_id UUID NOT NULL REFERENCES l25_derivation_graph_nodes(node_id) ON DELETE CASCADE,
  target_node_id UUID NOT NULL REFERENCES l25_derivation_graph_nodes(node_id) ON DELETE CASCADE,
  edge_kind TEXT NOT NULL CHECK (edge_kind IN ('derives_from','contradicts','reinforces','depends_on')),
  derivation_rule TEXT,
  confidence_delta NUMERIC,

  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE(source_node_id, target_node_id, edge_kind)
);

CREATE INDEX IF NOT EXISTS dg_edges_chart_idx ON l25_derivation_graph_edges (chart_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS dg_edges_source_idx ON l25_derivation_graph_edges (source_node_id);
CREATE INDEX IF NOT EXISTS dg_edges_target_idx ON l25_derivation_graph_edges (target_node_id);

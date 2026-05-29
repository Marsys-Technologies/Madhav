-- Migration 137: L2.5 synthesis tables (A3-S4)
-- Creates 6 l25_* tables for L2.5 synthesis outputs per A3 spec §7.
-- L2.5 synthesis outputs do NOT live in chart_facts; they live here.
-- All CREATE TABLE / INDEX statements are idempotent (IF NOT EXISTS).

-- L2.5 Table 1: MSR signals
CREATE TABLE IF NOT EXISTS l25_msr_signals (
  signal_id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id                 UUID NOT NULL,
  ayanamsha_id             TEXT NOT NULL,
  build_id                 UUID NOT NULL,
  configuration            TEXT NOT NULL,
  constituent_facts_array  TEXT[] NOT NULL DEFAULT '{}',
  classical_sources        TEXT[] DEFAULT '{}',
  deterministic_strength   NUMERIC,
  verification_certainty   NUMERIC,
  computed_salience        NUMERIC,
  salience_formula_version TEXT,
  domains_affected         TEXT[] DEFAULT '{}',
  computed_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS l25_msr_chart_aya_idx ON l25_msr_signals (chart_id, ayanamsha_id);

-- L2.5 Table 2: CDLM cells
CREATE TABLE IF NOT EXISTS l25_cdlm_cells (
  cell_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id         UUID NOT NULL,
  ayanamsha_id     TEXT NOT NULL,
  build_id         UUID NOT NULL,
  domain_a         TEXT NOT NULL,
  domain_b         TEXT NOT NULL,
  shared_factor_count INT NOT NULL DEFAULT 0,
  linkage_strength NUMERIC,
  computed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS l25_cdlm_chart_aya_idx ON l25_cdlm_cells (chart_id, ayanamsha_id);
CREATE UNIQUE INDEX IF NOT EXISTS l25_cdlm_unique_cell ON l25_cdlm_cells (chart_id, ayanamsha_id, build_id, domain_a, domain_b);

-- L2.5 Table 3: CGM nodes
CREATE TABLE IF NOT EXISTS l25_cgm_nodes (
  node_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id         UUID NOT NULL,
  ayanamsha_id     TEXT NOT NULL,
  build_id         UUID NOT NULL,
  node_type        TEXT NOT NULL,
  node_label       TEXT NOT NULL,
  weight           NUMERIC,
  computed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS l25_cgm_nodes_chart_aya_idx ON l25_cgm_nodes (chart_id, ayanamsha_id);

-- L2.5 Table 4: CGM edges
CREATE TABLE IF NOT EXISTS l25_cgm_edges (
  edge_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id         UUID NOT NULL,
  ayanamsha_id     TEXT NOT NULL,
  build_id         UUID NOT NULL,
  source_node_id   UUID REFERENCES l25_cgm_nodes(node_id),
  target_node_id   UUID REFERENCES l25_cgm_nodes(node_id),
  edge_type        TEXT NOT NULL,
  weight           NUMERIC,
  computed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS l25_cgm_edges_chart_aya_idx ON l25_cgm_edges (chart_id, ayanamsha_id);

-- L2.5 Table 5: RM resonances
CREATE TABLE IF NOT EXISTS l25_rm_resonances (
  resonance_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id         UUID NOT NULL,
  ayanamsha_id     TEXT NOT NULL,
  build_id         UUID NOT NULL,
  graha            TEXT NOT NULL,
  remedy_type      TEXT NOT NULL,
  remedy_ref       TEXT NOT NULL,
  resonance_score  NUMERIC,
  computed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS l25_rm_chart_aya_idx ON l25_rm_resonances (chart_id, ayanamsha_id);

-- L2.5 Table 6: UCN digests
CREATE TABLE IF NOT EXISTS l25_ucn_digests (
  digest_id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id                 UUID NOT NULL,
  ayanamsha_id             TEXT NOT NULL,
  build_id                 UUID NOT NULL,
  top_k_configurations     JSONB,
  dominant_grahas          TEXT[] DEFAULT '{}',
  weakest_grahas           TEXT[] DEFAULT '{}',
  system_convergence_counts JSONB,
  computed_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS l25_ucn_chart_aya_idx ON l25_ucn_digests (chart_id, ayanamsha_id);
CREATE UNIQUE INDEX IF NOT EXISTS l25_ucn_unique ON l25_ucn_digests (chart_id, ayanamsha_id, build_id);

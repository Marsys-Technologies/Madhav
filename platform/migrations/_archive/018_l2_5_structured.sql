BEGIN;

-- ── L2.5 MSR Signals (499 rows expected from MSR_v3_0) ──────────────────────
CREATE TABLE IF NOT EXISTS l25_msr_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id TEXT UNIQUE NOT NULL,
  signal_number INTEGER NOT NULL,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  valence TEXT NOT NULL,
  weight NUMERIC,
  planets_involved TEXT[],
  houses_involved INTEGER[],
  signs_involved TEXT[],
  description TEXT NOT NULL,
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  provenance JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_l25_msr_category_valence ON l25_msr_signals(category, valence);
CREATE INDEX IF NOT EXISTS idx_l25_msr_planets ON l25_msr_signals USING GIN(planets_involved);
CREATE INDEX IF NOT EXISTS idx_l25_msr_houses ON l25_msr_signals USING GIN(houses_involved);
CREATE TABLE IF NOT EXISTS l25_msr_signals_staging (LIKE l25_msr_signals INCLUDING ALL);

-- ── L2.5 UCN Sections ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS l25_ucn_sections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  section_id TEXT UNIQUE NOT NULL,
  parent_section_id TEXT,
  domain TEXT,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  derived_from_signals TEXT[],
  source_lines TEXT,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id)
);
CREATE INDEX IF NOT EXISTS idx_l25_ucn_domain ON l25_ucn_sections(domain);
CREATE INDEX IF NOT EXISTS idx_l25_ucn_signals ON l25_ucn_sections USING GIN(derived_from_signals);
CREATE TABLE IF NOT EXISTS l25_ucn_sections_staging (LIKE l25_ucn_sections INCLUDING ALL);

-- ── L2.5 CDLM Links (9 domains × 9 = 81 cells) ──────────────────────────────
CREATE TABLE IF NOT EXISTS l25_cdlm_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  link_id TEXT UNIQUE NOT NULL,
  from_domain TEXT NOT NULL,
  to_domain TEXT NOT NULL,
  link_type TEXT NOT NULL,
  strength TEXT NOT NULL,
  source_signals TEXT[],
  notes TEXT,
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  UNIQUE(from_domain, to_domain)
);
CREATE INDEX IF NOT EXISTS idx_l25_cdlm_from ON l25_cdlm_links(from_domain);
CREATE INDEX IF NOT EXISTS idx_l25_cdlm_to ON l25_cdlm_links(to_domain);
CREATE TABLE IF NOT EXISTS l25_cdlm_links_staging (LIKE l25_cdlm_links INCLUDING ALL);

-- ── L2.5 CGM Nodes ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS l25_cgm_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id TEXT UNIQUE NOT NULL,
  node_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  properties JSONB NOT NULL,
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id)
);
CREATE INDEX IF NOT EXISTS idx_l25_cgm_nodes_type ON l25_cgm_nodes(node_type);
CREATE TABLE IF NOT EXISTS l25_cgm_nodes_staging (LIKE l25_cgm_nodes INCLUDING ALL);

-- ── L2.5 CGM Edges ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS l25_cgm_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  edge_id TEXT UNIQUE NOT NULL,
  source_node_id TEXT NOT NULL,
  target_node_id TEXT NOT NULL,
  edge_type TEXT NOT NULL,
  strength NUMERIC,
  notes TEXT,
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id)
);
CREATE INDEX IF NOT EXISTS idx_l25_cgm_edges_source ON l25_cgm_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_l25_cgm_edges_target ON l25_cgm_edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_l25_cgm_edges_type ON l25_cgm_edges(edge_type);
CREATE TABLE IF NOT EXISTS l25_cgm_edges_staging (LIKE l25_cgm_edges INCLUDING ALL);

-- ── L2.5 RM Resonances ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS l25_rm_resonances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resonance_id TEXT UNIQUE NOT NULL,
  signal_a_id TEXT NOT NULL,
  signal_b_id TEXT NOT NULL,
  resonance_type TEXT NOT NULL,
  strength TEXT NOT NULL,
  theme TEXT,
  notes TEXT,
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  UNIQUE(signal_a_id, signal_b_id, resonance_type)
);
CREATE INDEX IF NOT EXISTS idx_l25_rm_signal_a ON l25_rm_resonances(signal_a_id);
CREATE INDEX IF NOT EXISTS idx_l25_rm_signal_b ON l25_rm_resonances(signal_b_id);
CREATE TABLE IF NOT EXISTS l25_rm_resonances_staging (LIKE l25_rm_resonances INCLUDING ALL);

COMMIT;

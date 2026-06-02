BEGIN;

-- Pattern Register
CREATE TABLE IF NOT EXISTS pattern_register (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pattern_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  domain TEXT,
  evidence JSONB NOT NULL,
  source_signal_ids TEXT[],
  source_fact_ids TEXT[],
  confidence NUMERIC NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  discovered_at TIMESTAMPTZ NOT NULL,
  discovered_in_build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','superseded','rejected'))
);
CREATE INDEX idx_pattern_domain ON pattern_register(domain);
CREATE INDEX idx_pattern_confidence ON pattern_register(confidence DESC);
CREATE INDEX idx_pattern_status ON pattern_register(status);
CREATE INDEX idx_pattern_signals ON pattern_register USING GIN(source_signal_ids);
CREATE TABLE IF NOT EXISTS pattern_register_staging (LIKE pattern_register INCLUDING ALL);

-- Resonance Register (L3 — higher abstraction than L2.5's RM)
CREATE TABLE IF NOT EXISTS resonance_register (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resonance_id TEXT UNIQUE NOT NULL,
  theme TEXT NOT NULL,
  description TEXT NOT NULL,
  signal_ids TEXT[] NOT NULL,
  pattern_ids TEXT[],
  domains TEXT[],
  confidence NUMERIC NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  discovered_at TIMESTAMPTZ NOT NULL,
  discovered_in_build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  status TEXT NOT NULL DEFAULT 'active'
);
CREATE INDEX idx_resonance_theme ON resonance_register(theme);
CREATE INDEX idx_resonance_signals ON resonance_register USING GIN(signal_ids);
CREATE INDEX idx_resonance_domains ON resonance_register USING GIN(domains);
CREATE TABLE IF NOT EXISTS resonance_register_staging (LIKE resonance_register INCLUDING ALL);

-- Cluster Register
CREATE TABLE IF NOT EXISTS cluster_register (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cluster_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  theme TEXT NOT NULL,
  description TEXT NOT NULL,
  member_signal_ids TEXT[] NOT NULL,
  member_fact_ids TEXT[],
  member_event_ids TEXT[],
  domain TEXT,
  confidence NUMERIC NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  discovered_at TIMESTAMPTZ NOT NULL,
  discovered_in_build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  status TEXT NOT NULL DEFAULT 'active'
);
CREATE INDEX idx_cluster_theme ON cluster_register(theme);
CREATE INDEX idx_cluster_domain ON cluster_register(domain);
CREATE INDEX idx_cluster_signals ON cluster_register USING GIN(member_signal_ids);
CREATE TABLE IF NOT EXISTS cluster_register_staging (LIKE cluster_register INCLUDING ALL);

-- Contradiction Register
CREATE TABLE IF NOT EXISTS contradiction_register (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contradiction_id TEXT UNIQUE NOT NULL,
  statement_a TEXT NOT NULL,
  statement_b TEXT NOT NULL,
  conflict_type TEXT NOT NULL,
  evidence JSONB NOT NULL,
  source_signal_ids TEXT[],
  source_fact_ids TEXT[],
  resolution_status TEXT NOT NULL CHECK (resolution_status IN ('unresolved','accepted','dismissed','reframed')),
  resolution_notes TEXT,
  domain TEXT,
  confidence NUMERIC NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  discovered_at TIMESTAMPTZ NOT NULL,
  discovered_in_build_id TEXT NOT NULL REFERENCES build_manifests(build_id)
);
CREATE INDEX idx_contradiction_status ON contradiction_register(resolution_status);
CREATE INDEX idx_contradiction_domain ON contradiction_register(domain);
CREATE INDEX idx_contradiction_signals ON contradiction_register USING GIN(source_signal_ids);
CREATE TABLE IF NOT EXISTS contradiction_register_staging (LIKE contradiction_register INCLUDING ALL);

COMMIT;

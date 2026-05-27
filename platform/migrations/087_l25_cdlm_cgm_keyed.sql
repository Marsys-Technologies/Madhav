-- 087_l25_cdlm_cgm_keyed.sql
-- Unit 2a — add (chart_id, ayanamsha_id) keying + shared-factor structural
-- linkage for CDLM and CGM.
--
-- Deterministic CDLM is a SHARED-FACTOR graph: two domains are linked by
-- shared planetary involvement, shared house involvement, or shared
-- sign-lord. CGM is the structural graph of nodes (grahas, houses, vargas,
-- panchanga elements) and the deterministic edges between them (lordship,
-- aspect, occupancy, conjunction).
--
-- ROLLBACK: see end of file.

BEGIN;

-- ─── 1. l25_cdlm_links: chart_id + ayanamsha_id + shared_factors ──────────────
ALTER TABLE l25_cdlm_links
  ADD COLUMN IF NOT EXISTS chart_id        TEXT REFERENCES charts(chart_id),
  ADD COLUMN IF NOT EXISTS ayanamsha_id    TEXT,
  ADD COLUMN IF NOT EXISTS engine_version  TEXT,
  -- Deterministic shared-factor decomposition (Gemini keeper — structural).
  -- shared_planets / shared_houses / shared_signs hold the actual factor
  -- elements; cardinality hints live in shared_factor_count.
  ADD COLUMN IF NOT EXISTS shared_planets       TEXT[],
  ADD COLUMN IF NOT EXISTS shared_houses        INTEGER[],
  ADD COLUMN IF NOT EXISTS shared_signs         TEXT[],
  ADD COLUMN IF NOT EXISTS shared_factor_count  INTEGER;

-- Drop the legacy UNIQUE(from_domain, to_domain) — for engine rows uniqueness
-- becomes (from, to, chart_id, ayanamsha_id).
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'l25_cdlm_links_from_domain_to_domain_key'
  ) THEN
    ALTER TABLE l25_cdlm_links
      DROP CONSTRAINT l25_cdlm_links_from_domain_to_domain_key;
  END IF;
END$$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_l25_cdlm_engine
  ON l25_cdlm_links(from_domain, to_domain, chart_id, ayanamsha_id)
  WHERE chart_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_l25_cdlm_legacy
  ON l25_cdlm_links(from_domain, to_domain)
  WHERE chart_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_l25_cdlm_chart_ayan
  ON l25_cdlm_links(chart_id, ayanamsha_id);

ALTER TABLE l25_cdlm_links_staging
  ADD COLUMN IF NOT EXISTS chart_id        TEXT,
  ADD COLUMN IF NOT EXISTS ayanamsha_id    TEXT,
  ADD COLUMN IF NOT EXISTS engine_version  TEXT,
  ADD COLUMN IF NOT EXISTS shared_planets       TEXT[],
  ADD COLUMN IF NOT EXISTS shared_houses        INTEGER[],
  ADD COLUMN IF NOT EXISTS shared_signs         TEXT[],
  ADD COLUMN IF NOT EXISTS shared_factor_count  INTEGER;

-- ─── 2. l25_cgm_nodes: chart_id + ayanamsha_id ────────────────────────────────
ALTER TABLE l25_cgm_nodes
  ADD COLUMN IF NOT EXISTS chart_id        TEXT REFERENCES charts(chart_id),
  ADD COLUMN IF NOT EXISTS ayanamsha_id    TEXT,
  ADD COLUMN IF NOT EXISTS engine_version  TEXT;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'l25_cgm_nodes_node_id_key'
  ) THEN
    ALTER TABLE l25_cgm_nodes DROP CONSTRAINT l25_cgm_nodes_node_id_key;
  END IF;
END$$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_l25_cgm_nodes_engine
  ON l25_cgm_nodes(node_id, chart_id, ayanamsha_id)
  WHERE chart_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_l25_cgm_nodes_legacy
  ON l25_cgm_nodes(node_id)
  WHERE chart_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_l25_cgm_nodes_chart_ayan
  ON l25_cgm_nodes(chart_id, ayanamsha_id);

ALTER TABLE l25_cgm_nodes_staging
  ADD COLUMN IF NOT EXISTS chart_id        TEXT,
  ADD COLUMN IF NOT EXISTS ayanamsha_id    TEXT,
  ADD COLUMN IF NOT EXISTS engine_version  TEXT;

-- ─── 3. l25_cgm_edges: chart_id + ayanamsha_id ────────────────────────────────
ALTER TABLE l25_cgm_edges
  ADD COLUMN IF NOT EXISTS chart_id        TEXT REFERENCES charts(chart_id),
  ADD COLUMN IF NOT EXISTS ayanamsha_id    TEXT,
  ADD COLUMN IF NOT EXISTS engine_version  TEXT;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'l25_cgm_edges_edge_id_key'
  ) THEN
    ALTER TABLE l25_cgm_edges DROP CONSTRAINT l25_cgm_edges_edge_id_key;
  END IF;
END$$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_l25_cgm_edges_engine
  ON l25_cgm_edges(edge_id, chart_id, ayanamsha_id)
  WHERE chart_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_l25_cgm_edges_legacy
  ON l25_cgm_edges(edge_id)
  WHERE chart_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_l25_cgm_edges_chart_ayan
  ON l25_cgm_edges(chart_id, ayanamsha_id);

ALTER TABLE l25_cgm_edges_staging
  ADD COLUMN IF NOT EXISTS chart_id        TEXT,
  ADD COLUMN IF NOT EXISTS ayanamsha_id    TEXT,
  ADD COLUMN IF NOT EXISTS engine_version  TEXT;

COMMIT;

-- ROLLBACK
-- BEGIN;
-- ALTER TABLE l25_cgm_edges
--   DROP COLUMN IF EXISTS chart_id, DROP COLUMN IF EXISTS ayanamsha_id, DROP COLUMN IF EXISTS engine_version;
-- ALTER TABLE l25_cgm_nodes
--   DROP COLUMN IF EXISTS chart_id, DROP COLUMN IF EXISTS ayanamsha_id, DROP COLUMN IF EXISTS engine_version;
-- ALTER TABLE l25_cdlm_links
--   DROP COLUMN IF EXISTS chart_id, DROP COLUMN IF EXISTS ayanamsha_id, DROP COLUMN IF EXISTS engine_version,
--   DROP COLUMN IF EXISTS shared_planets, DROP COLUMN IF EXISTS shared_houses,
--   DROP COLUMN IF EXISTS shared_signs, DROP COLUMN IF EXISTS shared_factor_count;
-- COMMIT;

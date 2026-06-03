-- Migration 002: chart_sensitive_points table + query_sensitive_points view
-- BRAHMA GA-1-6 — ganita.sensitive_points asset
-- Idempotent: yes (CREATE TABLE IF NOT EXISTS, CREATE INDEX IF NOT EXISTS)
--
-- This migration adds:
--   1. chart_sensitive_points — dedicated table for sensitive points per chart+ayanamsha
--   2. Indexes for efficient query_sensitive_points tool access
--   3. A convenience view v_sensitive_points_summary for the MCP tool
--
-- Data source: chart_facts (categories: upagraha, special_lagna, saham, arudha)
-- Written by: bootstrap_chart_facts_sensitive_points.ts (BRAHMA GA-1-6)
-- Tools: query_sensitive_points(chart_id, ayanamsha) → sensitive points
--
-- Note: The primary store remains chart_facts (category IN upagraha/special_lagna/saham/arudha).
-- This table is a typed projection for O(1) point lookups by name/category.

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. chart_sensitive_points — typed sensitive-point store
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS chart_sensitive_points (
  id              BIGSERIAL    PRIMARY KEY,
  chart_id        UUID         NOT NULL,              -- FK to charts.id (enforced at app level)
  point_name      TEXT         NOT NULL,              -- e.g. 'Gulika', 'Hora Lagna', 'Punya', 'AL'
  point_category  TEXT         NOT NULL               -- 'upagraha' | 'special_lagna' | 'saham' | 'arudha'
                  CHECK (point_category IN ('upagraha', 'special_lagna', 'saham', 'arudha')),
  ayanamsha_id    TEXT         NOT NULL               -- 'lahiri' | 'true_chitra' | 'kp' | 'raman' | 'surya_siddhanta' | 'INVARIANT'
                  DEFAULT 'INVARIANT',
  fact_id         TEXT         NOT NULL,              -- mirrors chart_facts.fact_id (e.g. 'UPG.GULIKA')
  longitude       TEXT,                               -- e.g. 'Gemini 13°57′' (text position)
  sign            TEXT,                               -- zodiac sign name
  house           INTEGER      CHECK (house BETWEEN 1 AND 12),
  nakshatra       TEXT,
  source_citation TEXT         NOT NULL,              -- e.g. 'FORENSIC_v8_0_§11.1 row 1'
  metadata        JSONB,                              -- additional fields (type, meaning, note, tenants, etc.)
  build_id        TEXT         NOT NULL,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE chart_sensitive_points IS
  'Typed projection of chart_facts sensitive-point categories (upagraha, special_lagna, saham, arudha). '
  'Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §11–§13. JH authoritative for v8.0 corrections. '
  'BRAHMA GA-1-6 / ganita.sensitive_points.';

COMMENT ON COLUMN chart_sensitive_points.ayanamsha_id IS
  'INVARIANT for position-independent points (upagraha, special_lagna, saham, arudha computed from '
  'birth chart positions). Will be chart-specific ayanamsha when engine-computed per ayanamsha.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Indexes
-- ─────────────────────────────────────────────────────────────────────────────

-- Primary lookup: all sensitive points for a given chart
CREATE INDEX IF NOT EXISTS idx_csp_chart_id
  ON chart_sensitive_points (chart_id);

-- Category-filtered lookup (e.g. all upagrahas for a chart)
CREATE INDEX IF NOT EXISTS idx_csp_chart_category
  ON chart_sensitive_points (chart_id, point_category);

-- Direct fact_id lookup (mirrors chart_facts)
CREATE UNIQUE INDEX IF NOT EXISTS idx_csp_chart_fact_id
  ON chart_sensitive_points (chart_id, fact_id, ayanamsha_id);

-- Point name lookup (e.g. find 'Gulika' across all charts)
CREATE INDEX IF NOT EXISTS idx_csp_point_name
  ON chart_sensitive_points (point_name);

-- Sign-based lookup
CREATE INDEX IF NOT EXISTS idx_csp_sign
  ON chart_sensitive_points (chart_id, sign);

-- House-based lookup
CREATE INDEX IF NOT EXISTS idx_csp_house
  ON chart_sensitive_points (chart_id, house);

-- JSONB metadata GIN index (for metadata->>'type', metadata->>'meaning', etc.)
CREATE INDEX IF NOT EXISTS idx_csp_metadata_gin
  ON chart_sensitive_points USING GIN (metadata);

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Convenience view: v_sensitive_points_summary
--    Aggregates chart_facts rows into the canonical sensitive_points shape.
--    Used by query_sensitive_points tool as a fallback when chart_sensitive_points
--    has not been populated for a chart (FORENSIC native chart always ingested).
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW v_sensitive_points_summary AS
  SELECT
    fact_id,
    category                         AS point_category,
    divisional_chart,
    value_text                       AS longitude,
    value_json->>'name'              AS point_name,
    value_json->>'sign'              AS sign,
    (value_json->>'house')::INT      AS house,
    value_json->>'nakshatra'         AS nakshatra,
    value_json->>'type'              AS upg_type,
    value_json->>'meaning'           AS saham_meaning,
    value_json->>'note'              AS correction_note,
    source_section                   AS source_citation,
    build_id
  FROM chart_facts
  WHERE category IN ('upagraha', 'special_lagna', 'saham', 'arudha')
  ORDER BY category ASC, fact_id ASC;

COMMENT ON VIEW v_sensitive_points_summary IS
  'Convenience view over chart_facts for sensitive points. '
  'Covers upagraha, special_lagna, saham, arudha categories. '
  'FORENSIC v8.0 native chart values (JH authoritative). '
  'Used by query_sensitive_points tool. BRAHMA GA-1-6.';

COMMIT;

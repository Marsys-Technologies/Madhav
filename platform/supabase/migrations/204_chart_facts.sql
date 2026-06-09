-- Migration 204: CREATE chart_facts table
-- Source: GA3_CHART_FACTS_SPEC_v1_0.md §1 (v1.2, native-confirmed 2026-06-09)
-- chart_facts was absent since the 2026-06-03 Brahma infra wipe (DROP SCHEMA CASCADE).
-- GA5 (sensitive points), GA8 (structural strength), GA9 (Sade Sati) write into this table.
-- Per: L1_GANITA_BUILD_CAMPAIGN_v1_0.md §C.2 · STORAGE_SUBSTRATE_REARCHITECTURE_v1_0.md §L
-- Atomic-grain rule: every queryable sub-value = its own row; JSONB for irreducible composites only.

BEGIN;

CREATE TABLE IF NOT EXISTS chart_facts (
  fact_id                  TEXT PRIMARY KEY,
  chart_id                 UUID NOT NULL,
  ayanamsha_id             TEXT NOT NULL,
  build_id                 UUID NOT NULL,
  fact_category            TEXT NOT NULL,
  fact_subject             TEXT NOT NULL,
  fact_key                 TEXT NOT NULL,
  fact_value_text          TEXT,
  fact_value_num           NUMERIC,
  fact_value_jsonb         JSONB,
  unit                     TEXT,
  citation_ref             TEXT NOT NULL,
  citation_human           TEXT NOT NULL,
  source_calculation       TEXT NOT NULL,
  verification_pass_status TEXT NOT NULL,
  engine_version           TEXT NOT NULL,
  salience_formula_ver     TEXT,
  computed_at              TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
);

-- Retrieval indexes (query patterns: chart+category, chart+subject, chart+ayanamsha)
CREATE INDEX IF NOT EXISTS chart_facts_chart_id_idx
  ON chart_facts (chart_id);

CREATE INDEX IF NOT EXISTS chart_facts_category_idx
  ON chart_facts (chart_id, fact_category);

CREATE INDEX IF NOT EXISTS chart_facts_subject_idx
  ON chart_facts (chart_id, fact_subject);

CREATE INDEX IF NOT EXISTS chart_facts_ayanamsha_idx
  ON chart_facts (chart_id, ayanamsha_id);

CREATE INDEX IF NOT EXISTS chart_facts_build_idx
  ON chart_facts (build_id);

COMMIT;

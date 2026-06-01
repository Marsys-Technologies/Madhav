-- Migration 029 — KARN-W2-R2-CHART-FACTS-ETL
-- Predecessor: KARN-W1-R1-PHASE-ALPHA Audit 1 (chart_facts schema confirmed sufficient)
-- Purpose: Auxiliary indexes to accelerate chart_facts_query tool (W4-R3).
-- Schema changes: none (existing schema supports all new category values via category + value_json).

BEGIN;

CREATE INDEX IF NOT EXISTS chart_facts_category_divchart_idx
  ON chart_facts(category, divisional_chart) WHERE is_stale = false;

CREATE INDEX IF NOT EXISTS chart_facts_source_section_idx
  ON chart_facts(source_section) WHERE is_stale = false;

CREATE INDEX IF NOT EXISTS chart_facts_value_json_gin
  ON chart_facts USING GIN (value_json);

COMMIT;

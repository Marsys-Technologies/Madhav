-- Phase 14C Stream A: chart_facts and chart_facts_staging
-- Flexible key-value-with-context store for natal chart, KP cusps, sahams, yogas, special lagnas.
-- fact_id scheme: PLN.JUP.LON_DEG | CUSP.07.STAR_LORD | SAHAM.PUNYA | YOGA.GAJAKESARI
BEGIN;

CREATE TABLE IF NOT EXISTS chart_facts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fact_id TEXT UNIQUE NOT NULL,
  category TEXT NOT NULL,              -- 'planet'|'house'|'cusp'|'saham'|'yoga'|'special_lagna'|'dasha_balance'
  divisional_chart TEXT NOT NULL DEFAULT 'D1',  -- 'D1'|'D9'|'D10'|'D60'|'D7'|'D12'|... (28 standard varga)
  value_text TEXT,
  value_number NUMERIC,
  value_json JSONB,
  source_section TEXT NOT NULL,        -- '§4.1 row 12' | '§12.1' | '§26'
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  provenance JSONB NOT NULL,           -- {source_uri, source_version, source_hash, extracted_at, extraction_method}
  is_stale BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chart_facts_category ON chart_facts(category, divisional_chart);
CREATE INDEX IF NOT EXISTS idx_chart_facts_fact_id ON chart_facts(fact_id);

CREATE TABLE IF NOT EXISTS chart_facts_staging (LIKE chart_facts INCLUDING ALL);

COMMIT;

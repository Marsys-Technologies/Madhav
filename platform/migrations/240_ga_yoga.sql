-- Migration 240: ga_yoga — per-chart yoga firing table + asset_registry entry
-- Yoga Subsystem Gate-1 — 2026-06-17

CREATE TABLE IF NOT EXISTS ga_yoga_firings (
    id SERIAL PRIMARY KEY,
    chart_id UUID NOT NULL,
    build_id UUID,
    ayanamsha_id TEXT NOT NULL,
    yoga_canonical_id TEXT NOT NULL,
    fired BOOLEAN NOT NULL DEFAULT TRUE,
    -- Constituent decomposition (L1-authority discipline)
    constituent_fact_ids JSONB,
    constituent_planets JSONB,
    constituent_houses JSONB,
    -- Computed structure
    strength NUMERIC,
    strength_formula_version TEXT,
    partial_formation_pct NUMERIC,
    is_partial BOOLEAN DEFAULT FALSE,
    bhanga_active BOOLEAN DEFAULT FALSE,
    bhanga_rule_fired TEXT,
    family_ids JSONB,
    activation_dasha_periods JSONB,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (chart_id, ayanamsha_id, yoga_canonical_id)
);

CREATE INDEX IF NOT EXISTS idx_ga_yoga_firings_chart_ayanamsha
    ON ga_yoga_firings(chart_id, ayanamsha_id);

CREATE INDEX IF NOT EXISTS idx_ga_yoga_firings_yoga
    ON ga_yoga_firings(yoga_canonical_id);

-- Asset registry entry — uses the full column set observed in migration 174
INSERT INTO asset_registry (
    asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql, target_floor,
    expected_volume_formula, volume_explanation, depends_on, scope, is_active
) VALUES (
    'ga_yoga',
    'ganita',
    28,
    'Yoga Pradipanam',
    'Yoga Firings (ga_yoga)',
    'Per-chart yoga firing records — deterministic classical-rule evaluation across 5 ayanamshas',
    'postgres_table',
    'ga_yoga_firings',
    'SELECT COUNT(*) FROM ga_yoga_firings WHERE chart_id = $1::uuid',
    'SELECT pg_total_relation_size(''ga_yoga_firings'')',
    50,
    'YOGAS_IN_CATALOG × AYANAMSHAS_COUNT',
    'Sum of fired yogas across 5 ayanamshas for a given chart',
    ARRAY['ga_structural', 'ga_dashas']::text[],
    'per_chart',
    true
) ON CONFLICT (asset_id) DO UPDATE SET
    english_name = EXCLUDED.english_name,
    english_description = EXCLUDED.english_description,
    depends_on = EXCLUDED.depends_on,
    count_sql = EXCLUDED.count_sql,
    target_floor = EXCLUDED.target_floor,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active;

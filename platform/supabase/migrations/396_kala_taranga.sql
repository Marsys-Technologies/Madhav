-- Migration 396: kala_taranga — Activation Waveform — BA-P5A Step 3
-- Monthly convolution of dasha × transit × promise, stored 1950–2100.
-- Fine grain (daily/hourly) = SERVICE computation, never stored here.
-- Writer: ka_taranga. DAG: ka_avadhi → ka_taranga.

BEGIN;

CREATE TABLE IF NOT EXISTS kala_taranga (
    taranga_id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id        UUID        NOT NULL,
    month           DATE        NOT NULL,
    scope_kind      TEXT        NOT NULL CHECK (scope_kind IN ('domain', 'event_class')),
    scope_id        TEXT        NOT NULL,
    activation      NUMERIC(8,6),
    components      JSONB,
    formula_version TEXT        NOT NULL DEFAULT 'v1.0',
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(chart_id, month, scope_kind, scope_id)
);

COMMENT ON TABLE kala_taranga IS
  'BA-P5A: Activation Waveform — monthly activation score per (chart, scope_kind, scope_id). '
  'scope_kind ∈ {domain, event_class}. scope_id = domain name or event_class_id. '
  'activation: composite [0,1] score from dasha×transit×promise convolution. '
  'components JSONB: {dasha_contribution, transit_contribution, promise_contribution, formula_note}. '
  'Range 1950–2100 (monthly grain). Fine-grain (daily/hourly) is service computation, NOT stored. '
  'Writer: ka_taranga. DAG upstream: ka_avadhi.';

COMMENT ON COLUMN kala_taranga.components IS
  'dasha_contribution: [0,1] — period lord match for scope_id. '
  'transit_contribution: [0,1] — kala_convergence windows overlapping this month. '
  'promise_contribution: [0,1] — bodha_pratijna grade/status for scope_id. '
  'formula_note: version tag for the convolution formula.';

COMMENT ON COLUMN kala_taranga.month IS
  'First day of the calendar month. Grain = 1 month (28–31 days). '
  'Daily/hourly granularity is served on-demand, not stored.';

CREATE INDEX IF NOT EXISTS idx_kala_taranga_chart_scope ON kala_taranga(chart_id, scope_kind, scope_id);
CREATE INDEX IF NOT EXISTS idx_kala_taranga_chart_month ON kala_taranga(chart_id, month);
CREATE INDEX IF NOT EXISTS idx_kala_taranga_activation ON kala_taranga(chart_id, activation DESC NULLS LAST);

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer,
    layer_name, layer_index, catalog_status
) VALUES (
    'ka_taranga',
    'kala',
    33,
    'Taraṅga',
    'Activation Waveform',
    'Monthly activation waveform (1950–2100): convolution of dasha × transit × promise for each '
    'domain and event class. Known Sade-Sati years show elevated obstruction-adjusted activation. '
    'Fine-grain (daily/hourly) = service computation, not stored. Writer: ka_taranga after ka_avadhi.',
    'postgres_table', 'kala_taranga',
    'SELECT COUNT(*) FROM kala_taranga WHERE chart_id=$1',
    NULL,
    0, 'per_chart', true, true,
    'Kala', 3, 'CURRENT'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql    = EXCLUDED.count_sql,
    target_table = EXCLUDED.target_table,
    has_writer   = EXCLUDED.has_writer,
    sort_order   = EXCLUDED.sort_order,
    english_description = EXCLUDED.english_description;

UPDATE asset_registry SET depends_on = ARRAY['ka_avadhi', 'bo_pratijna']::text[]
WHERE asset_id = 'ka_taranga';

COMMIT;

-- Migration 395: kala_avadhi — Period Dossiers — BA-P5A Step 2
-- Per-dasha-period dossier: lord condition, activated pratijna IDs, sublord modulation.
-- Powers Q1 "how will my Ketu dasha be" and similar period-arc readings.
-- Dossier lord_condition_fact_refs: refs to chart_facts only — never restated computed values (trap-1).
-- Writer: ka_avadhi. DAG: ka_yojaka → ka_avadhi.

BEGIN;

CREATE TABLE IF NOT EXISTS kala_avadhi (
    avadhi_id       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id        UUID        NOT NULL,
    system_id       TEXT        NOT NULL,
    level_n         INT         NOT NULL CHECK (level_n IN (1, 2, 3)),
    lord_graha      TEXT        NOT NULL,
    period_start    DATE        NOT NULL,
    period_end      DATE        NOT NULL,
    dossier         JSONB,
    quality         JSONB,
    citations       TEXT[]      DEFAULT '{}',
    formula_version TEXT        NOT NULL DEFAULT 'v1.0',
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(chart_id, system_id, level_n, period_start)
);

COMMENT ON TABLE kala_avadhi IS
  'BA-P5A: Period Dossiers — one row per (chart, dasha-system, level, period_start). '
  'system_id ∈ {vimshottari,yogini,ashtottari,chara,naisargika,mudda,kalachakra}. '
  'level_n: 1=MD, 2=AD, 3=PD. '
  'dossier JSONB: {lord_condition_fact_refs, activated_pratijna_ids, sublord_modulation}. '
  'lord_condition_fact_refs: array of chart_facts fact_ids (refs only — never restated values). '
  'activated_pratijna_ids: bodha_pratijna IDs whose domain matches this lord. '
  'Writer: ka_avadhi. DAG upstream: ka_yojaka.';

COMMENT ON COLUMN kala_avadhi.dossier IS
  'lord_condition_fact_refs: [{fact_id, fact_subject, fact_key, role}] — chart_facts refs. '
  'activated_pratijna_ids: [uuid] — bodha_pratijna rows activated by this period. '
  'sublord_modulation: {graha, strength_factor, modulation_note}.';

CREATE INDEX IF NOT EXISTS idx_kala_avadhi_chart ON kala_avadhi(chart_id, system_id);
CREATE INDEX IF NOT EXISTS idx_kala_avadhi_period ON kala_avadhi(chart_id, period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_kala_avadhi_lord ON kala_avadhi(chart_id, lord_graha);

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer,
    layer_name, layer_index, catalog_status
) VALUES (
    'ka_avadhi',
    'kala',
    32,
    'Avadhī',
    'Period Dossiers',
    'Per-dasha-period dossiers: for each chart, dasha system, MD/AD/PD level, stores lord condition '
    '(refs to chart_facts), activated promise-register IDs (from bodha_pratijna), and sublord modulation. '
    'Powers "how will my Ketu dasha be" readings. Writer: ka_avadhi after ka_yojaka.',
    'postgres_table', 'kala_avadhi',
    'SELECT COUNT(*) FROM kala_avadhi WHERE chart_id=$1',
    NULL,
    0, 'per_chart', true, true,
    'Kala', 3, 'CURRENT'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql    = EXCLUDED.count_sql,
    target_table = EXCLUDED.target_table,
    has_writer   = EXCLUDED.has_writer,
    sort_order   = EXCLUDED.sort_order,
    english_description = EXCLUDED.english_description;

INSERT INTO asset_dag (from_asset_id, to_asset_id, edge_type, notes)
VALUES ('ka_yojaka', 'ka_avadhi', 'depends_on',
        'ka_avadhi reads kala_activation_predicates + bodha_pratijna for pratijna linkage')
ON CONFLICT DO NOTHING;

COMMIT;

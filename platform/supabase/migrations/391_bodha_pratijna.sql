-- Migration 391: bodha_pratijna — Promise Register — BA-P3B Step 3
-- The per-event-class promise verdict table. Reads bodha_msr_signals + brahma_event_ontology.
-- base-rate priors are placeholders here (JL-009 carry-forward; surfaced to native at P5B).

BEGIN;

CREATE TABLE IF NOT EXISTS bodha_pratijna (
    pratijna_id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                 UUID        NOT NULL,
    ayanamsha_id             TEXT        NOT NULL,
    build_id                 UUID,
    event_class_id           TEXT        NOT NULL REFERENCES brahma_event_ontology(event_class_id),
    status                   TEXT        NOT NULL CHECK (status IN ('promised','denied','conditional')),
    grade                    NUMERIC(5,3),
    supporting_signal_ids    UUID[]      DEFAULT '{}',
    contradicting_signal_ids UUID[]      DEFAULT '{}',
    varga_confirmation       JSONB,
    derivation               JSONB,
    formula_version          TEXT        NOT NULL DEFAULT 'v1.0',
    computed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    engine_version           TEXT,
    UNIQUE(chart_id, ayanamsha_id, event_class_id)
);

CREATE INDEX IF NOT EXISTS idx_bodha_pratijna_chart
    ON bodha_pratijna(chart_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS idx_bodha_pratijna_status
    ON bodha_pratijna(chart_id, status);
CREATE INDEX IF NOT EXISTS idx_bodha_pratijna_event_class
    ON bodha_pratijna(event_class_id);

COMMENT ON TABLE bodha_pratijna IS
  'BA-P3B: Promise Register — per-event-class verdict (promised/denied/conditional) for each chart/ayanamsha. '
  'grade [0–10]: 0=strongly denied, 10=strongly promised. '
  'Reads bodha_msr_signals salience + valence; keys to brahma_event_ontology. '
  'base-rate priors consumed at L4/P5B (JL-009 carry-forward — surfaced to native before anchor freeze). '
  'Writer: bo_pratijna. DAG: bo_laksana → bo_pratijna.';

-- ── asset_registry row ───────────────────────────────────────────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer,
    layer_name, layer_index, catalog_status
) VALUES (
    'bo_pratijna',
    'bodha',
    18,
    'Pratijñā',
    'Promise Register',
    'Per-event-class promise registry: promised/denied/conditional verdicts with grade, '
    'supporting and contradicting signal IDs, varga confirmation, derivation audit trail. '
    'Written by bo_pratijna after bo_laksana. Downstream: P5B ph_nimitta uses grade as promise_lift.',
    'postgres_table', 'bodha_pratijna',
    'SELECT COUNT(*) FROM bodha_pratijna WHERE chart_id=$1',
    NULL,
    0, 'per_chart', true, true,
    'Bodha', 2, 'CURRENT'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql     = EXCLUDED.count_sql,
    target_table  = EXCLUDED.target_table,
    has_writer    = EXCLUDED.has_writer,
    sort_order    = EXCLUDED.sort_order,
    english_description = EXCLUDED.english_description;

-- ── DAG edge ─────────────────────────────────────────────────────────────────

INSERT INTO asset_dag (from_asset_id, to_asset_id, edge_type, notes)
VALUES ('bo_laksana', 'bo_pratijna', 'depends_on',
        'Promise register reads bodha_msr_signals for signal salience and valence')
ON CONFLICT DO NOTHING;

COMMIT;

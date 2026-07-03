-- Migration 392: bodha_triangulation — Multi-tradition concordance — BA-P3B Step 3
-- Extends bo_sangati: Parashari/Jaimini/KP/Tajika tradition stacks per question_class.
-- Consumed by P4 verdict assembly (tradition_concordance field).

BEGIN;

CREATE TABLE IF NOT EXISTS bodha_triangulation (
    triangulation_id    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id            UUID        NOT NULL,
    ayanamsha_id        TEXT        NOT NULL,
    build_id            UUID,
    question_class      TEXT        NOT NULL,
    tradition           TEXT        NOT NULL CHECK (tradition IN ('parashari','jaimini','kp','tajika')),
    verdict_inputs      JSONB,
    concordance_score   NUMERIC(6,4),
    signal_ids          UUID[]      DEFAULT '{}',
    formula_version     TEXT        NOT NULL DEFAULT 'v1.0',
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    engine_version      TEXT,
    UNIQUE(chart_id, ayanamsha_id, question_class, tradition)
);

CREATE INDEX IF NOT EXISTS idx_bodha_triangulation_chart
    ON bodha_triangulation(chart_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS idx_bodha_triangulation_tradition
    ON bodha_triangulation(tradition);
CREATE INDEX IF NOT EXISTS idx_bodha_triangulation_question
    ON bodha_triangulation(question_class);

COMMENT ON TABLE bodha_triangulation IS
  'BA-P3B: Multi-tradition concordance per (chart, ayanamsha, question_class, tradition). '
  'tradition ∈ {parashari, jaimini, kp, tajika}. '
  'concordance_score: mean salience of top-5 signals from that tradition signals pool. '
  'Writer: bo_sangati (EXT). Consumed by P4 verdict tradition_concordance assembly. '
  'DAG: bo_laksana → bo_sangati → bodha_triangulation.';

-- ── DAG edge update for bo_sangati (already registered; no new asset_registry row) ──

INSERT INTO asset_dag (from_asset_id, to_asset_id, edge_type, notes)
VALUES ('bo_sangati', 'bo_pratijna', 'depends_on',
        'bo_pratijna reads bodha_triangulation tradition concordance for varga_confirmation')
ON CONFLICT DO NOTHING;

COMMIT;

-- brahma_mimamsa_mi_5_5.sql
-- BRAHMA MI-5-5: mimamsa.research — L5 Mīmāṃsā cross-corpus OLAP export log
--
-- Contract (BRAHMA L5 Mīmāṃsā):
--   table:   mimamsa_export_log
--            (export_id UUID, export_at TIMESTAMPTZ, table_name TEXT,
--             row_count INT, gcs_path TEXT, source_citation TEXT NOT NULL)
--   purpose: Audit trail for every Parquet → GCS → BigQuery export run
--   dataset: brahma_l5_olap (BigQuery, pre-provisioned)
--   constraint: source_citation NON-NULL enforced at DB level
--   leakage guard: life_events rows must carry 'life_events_calibration' prefix
--                  (calibration only — never prediction generation)
--
-- Source artifacts:
--   chart_facts      — L1 natal facts (FORENSIC_ASTROLOGICAL_DATA_v8_0)
--   bodha_signals    — L2 MSR signal states (573 signals, BRAHMA-BO-2-4)
--   life_events      — L1 LEL calibration intake (LIFE_EVENT_LOG_v1_2.md, v1.7)
--
-- Native: Abhisek Mohanty, 1984-02-05 — chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
--
-- ROLLBACK: DROP TABLE IF EXISTS mimamsa_export_log;
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Table ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS mimamsa_export_log (
    export_id       UUID        NOT NULL DEFAULT gen_random_uuid(),
    export_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    table_name      TEXT        NOT NULL,
    row_count       INTEGER     NOT NULL DEFAULT 0 CHECK (row_count >= 0),
    gcs_path        TEXT        NOT NULL DEFAULT '',
    source_citation TEXT        NOT NULL,           -- NON-NULL contract: always cite L1 provenance

    CONSTRAINT mimamsa_export_log_pk PRIMARY KEY (export_id),

    -- Leakage guard: any life_events export must use calibration prefix
    CONSTRAINT lel_calibration_only CHECK (
        table_name NOT LIKE 'life_events%'
        OR table_name LIKE 'life_events_calibration%'
    )
);

COMMENT ON TABLE mimamsa_export_log IS
    'BRAHMA MI-5-5: L5 Mīmāṃsā — audit trail for cross-corpus OLAP exports '
    '(chart_facts + bodha_signals → Parquet → GCS → BigQuery brahma_l5_olap). '
    'source_citation is NOT NULL; every row cites FORENSIC_v8_0 + artifact lineage. '
    'life_events intake: CALIBRATION ONLY (leakage guard enforced by DB constraint).';

COMMENT ON COLUMN mimamsa_export_log.export_id IS
    'UUID primary key — generated per export run.';

COMMENT ON COLUMN mimamsa_export_log.export_at IS
    'UTC timestamp of export execution.';

COMMENT ON COLUMN mimamsa_export_log.table_name IS
    'Source table exported: chart_facts | bodha_signals | life_events_calibration.';

COMMENT ON COLUMN mimamsa_export_log.row_count IS
    'Number of rows written to the GCS Parquet file (source_citation non-null filter applied).';

COMMENT ON COLUMN mimamsa_export_log.gcs_path IS
    'Full GCS URI: gs://bucket/brahma/l5/mimamsa/{table}/{timestamp}/{table}.parquet';

COMMENT ON COLUMN mimamsa_export_log.source_citation IS
    'NON-NULL provenance chain — must cite L1 canonical artifact: '
    'FORENSIC_ASTROLOGICAL_DATA_v8_0.md | LIFE_EVENT_LOG_v1_2.md | BRAHMA MI-5-5';

-- ── Indexes ───────────────────────────────────────────────────────────────────

-- Lookup by table name (for per-table export history)
CREATE INDEX IF NOT EXISTS idx_mimamsa_export_log_table_name
    ON mimamsa_export_log (table_name);

-- Time-series queries
CREATE INDEX IF NOT EXISTS idx_mimamsa_export_log_export_at
    ON mimamsa_export_log (export_at DESC);

-- ── Staging table (idempotent swap pattern per project convention) ─────────────

CREATE TABLE IF NOT EXISTS mimamsa_export_log_staging
    (LIKE mimamsa_export_log INCLUDING ALL);

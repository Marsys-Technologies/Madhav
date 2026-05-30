-- Migration 145: l1_time_synchronicity — convergence window table for A15
-- Stream C — A15 [BUILD-ORCH-STREAM-C-A15-S1]
-- Idempotent: CREATE TABLE IF NOT EXISTS, CREATE EXTENSION IF NOT EXISTS

-- Ensure pgvector extension is available
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS l1_time_synchronicity (
    sync_id             BIGSERIAL   PRIMARY KEY,
    chart_id            UUID        NOT NULL,
    window_start        DATE        NOT NULL,
    window_end          DATE        NOT NULL,
    cluster_intensity   INT         NOT NULL,   -- count of systems converging (3-9)
    systems_active      TEXT[]      NOT NULL,   -- array of system names
    key_dates           JSONB       NOT NULL,   -- {system_name: date, ...}
    divergence_flag     BOOLEAN     NOT NULL DEFAULT false,  -- true if systems DISAGREE
    divergence_detail   TEXT,                               -- description of disagreement
    convergence_score   FLOAT       NOT NULL DEFAULT 0.0,   -- 0.0-1.0
    embedding           vector(768),                         -- pgvector embedding (NULL until Vertex AI step)
    narrative           TEXT,                               -- plain-language description
    classical_citation  TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ts_chart_idx      ON l1_time_synchronicity(chart_id);
CREATE INDEX IF NOT EXISTS ts_window_idx     ON l1_time_synchronicity(window_start, window_end);
CREATE INDEX IF NOT EXISTS ts_intensity_idx  ON l1_time_synchronicity(cluster_intensity);
CREATE UNIQUE INDEX IF NOT EXISTS ts_unique_idx
    ON l1_time_synchronicity(chart_id, window_start, window_end);

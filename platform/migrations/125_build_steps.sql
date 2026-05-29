-- Migration 125: build_steps table
-- MARSYS-JIS Multi-Ayanamsha Build Orchestrator
-- Tracks per-ayanamsha per-category pipeline steps within a build

CREATE TABLE IF NOT EXISTS build_steps (
    step_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_id      UUID NOT NULL REFERENCES builds(build_id) ON DELETE CASCADE,
    ayanamsha_id  TEXT NOT NULL,
    category      TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'queued'
                  CHECK (status IN ('queued','running','complete','failed','skipped')),
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ,
    error_msg     TEXT,
    row_count     INTEGER,
    duration_ms   INTEGER,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS build_steps_build_idx ON build_steps(build_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS build_steps_status_idx ON build_steps(status)
    WHERE status IN ('queued','running');
CREATE INDEX IF NOT EXISTS build_steps_category_idx ON build_steps(category);

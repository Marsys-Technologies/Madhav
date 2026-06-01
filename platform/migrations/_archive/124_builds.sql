-- Migration 124: builds table
-- MARSYS-JIS Multi-Ayanamsha Build Orchestrator
-- Tracks per-chart build runs

CREATE TABLE IF NOT EXISTS builds (
  build_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id              UUID NOT NULL REFERENCES charts(chart_id) ON DELETE CASCADE,
  triggered_by_uid      TEXT NOT NULL,
  triggered_by_role     TEXT NOT NULL CHECK (triggered_by_role IN ('super_admin', 'guest')),
  engine_version        TEXT NOT NULL DEFAULT 'natal_engine/0.2.0',
  ayanamshas            JSONB NOT NULL DEFAULT '["lahiri","true_chitra","kp","raman","surya_siddhanta"]',
  salience_formula_ver  TEXT NOT NULL DEFAULT 'v1',
  status                TEXT NOT NULL CHECK (status IN ('queued','running','complete','failed','cancelled','cancelling')),
  queued_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at            TIMESTAMPTZ,
  finished_at           TIMESTAMPTZ,
  cancelled_at          TIMESTAMPTZ,
  failed_at             TIMESTAMPTZ,
  error_summary         TEXT,
  log_gcs_uri           TEXT,
  asset_artifacts_uri   TEXT,
  cloud_run_job_exec    TEXT
);

CREATE INDEX IF NOT EXISTS builds_chart_idx ON builds (chart_id, queued_at DESC);
CREATE INDEX IF NOT EXISTS builds_status_idx ON builds (status) WHERE status IN ('queued','running','cancelling');

-- Staging mirror
CREATE TABLE IF NOT EXISTS builds_staging (LIKE builds INCLUDING ALL);

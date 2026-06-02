-- 084_runtime_config.sql
-- Stream C / Unit 2d — Command Center runtime gate control plane.
-- Holds runtime overrides for gates declared in src/lib/gates/gate_registry.ts.
-- Bootstrap defaults live in env/code; this table records any super-admin override.
--
-- value is JSONB so we can store booleans, numbers, strings and small objects
-- uniformly. value_type carries the canonical type hint so the reader can
-- coerce without re-consulting the registry on every read.
--
-- Scope:
--   * global    — single row per key, chart_id IS NULL
--   * per_chart — one row per (key, chart_id)
-- Uniqueness across both modes is enforced by the composite expression index.

CREATE TABLE IF NOT EXISTS runtime_config (
  id          BIGSERIAL PRIMARY KEY,
  key         TEXT        NOT NULL,
  value       JSONB       NOT NULL,
  value_type  TEXT        NOT NULL CHECK (value_type IN ('boolean','number','string','json')),
  scope       TEXT        NOT NULL DEFAULT 'global' CHECK (scope IN ('global','per_chart')),
  chart_id    TEXT,
  updated_by  TEXT        NOT NULL,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS runtime_config_key_chart_uq
  ON runtime_config (key, COALESCE(chart_id, '__global__'));

COMMENT ON TABLE runtime_config IS
  'Stream C / Unit 2d — DB-backed control plane for gate_registry overrides. Env/code defaults apply if no row.';

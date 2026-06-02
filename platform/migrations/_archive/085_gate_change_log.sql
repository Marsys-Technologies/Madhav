-- 085_gate_change_log.sql
-- Stream C / Unit 2d — append-only audit log for every gate_registry edit.
-- Captured by configService.setGate; never edited outside that path.

CREATE TABLE IF NOT EXISTS gate_change_log (
  id          BIGSERIAL PRIMARY KEY,
  gate_key    TEXT        NOT NULL,
  chart_id    TEXT,                              -- nullable for global-scope gates
  old_value   JSONB,                             -- null on first write
  new_value   JSONB        NOT NULL,
  changed_by  TEXT         NOT NULL,             -- principal Firebase uid
  changed_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
  reason      TEXT                               -- free-form, optional
);

CREATE INDEX IF NOT EXISTS gate_change_log_gate_key_changed_at_idx
  ON gate_change_log (gate_key, changed_at DESC);

COMMENT ON TABLE gate_change_log IS
  'Stream C / Unit 2d — append-only audit trail for runtime_config edits via Command Center.';

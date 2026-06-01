BEGIN;

CREATE TABLE IF NOT EXISTS audit_events (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id         UUID        NOT NULL,
  query_plan_id    UUID,
  query_text       TEXT,
  query_class      TEXT,
  user_id          TEXT,
  chart_id         UUID,
  conversation_id  UUID,
  tool_bundles     JSONB,
  latency_ms       INTEGER,
  audit_status     TEXT        NOT NULL DEFAULT 'ok',
  audit_warnings   JSONB,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_events_query_id    ON audit_events(query_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at  ON audit_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_user_id     ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_query_class ON audit_events(query_class);

COMMIT;

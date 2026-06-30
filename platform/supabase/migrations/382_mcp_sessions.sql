-- 382_mcp_sessions.sql
-- M3: MCP session state store.
--
-- A session is chart-agnostic-capable: a session may exist before a chart is
-- chosen (active_chart_id is NULLABLE). Statelessness preserved — no in-process
-- session is held; every POST /mcp looks up the row, mutates, and writes back.
--
-- Keyed by (user_uid, session_key) so a user can maintain multiple client sessions
-- (e.g. Claude Desktop + ChatGPT connector) without collision.
--
-- state_json is a small per-session JSONB scratchpad for ephemeral metadata
-- (e.g. last advisory, client name). NOT used for conversation messages — that
-- is handled by the conversations/conversation_messages tables when needed.
--
-- Rollback: DROP TABLE IF EXISTS mcp_sessions;

CREATE TABLE IF NOT EXISTS mcp_sessions (
  session_id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_uid        TEXT        NOT NULL,
  session_key     TEXT        NOT NULL,             -- client-supplied opaque key (e.g. device-id or thread-id)
  active_chart_id UUID        REFERENCES charts(id) ON DELETE SET NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  state_json      JSONB       NOT NULL DEFAULT '{}'
);

-- Unique per (user, client session key) — enforces one row per client session.
CREATE UNIQUE INDEX IF NOT EXISTS idx_mcp_sessions_user_key
  ON mcp_sessions(user_uid, session_key);

-- Fast lookup by user (list_my_sessions, recall_session).
CREATE INDEX IF NOT EXISTS idx_mcp_sessions_user_uid
  ON mcp_sessions(user_uid);

-- Fast lookup by active_chart_id (entitlement re-check on chart access revocation).
CREATE INDEX IF NOT EXISTS idx_mcp_sessions_active_chart
  ON mcp_sessions(active_chart_id)
  WHERE active_chart_id IS NOT NULL;

COMMENT ON TABLE mcp_sessions IS
  'Per-user MCP session state. Stateless-request model: looked up, mutated, written back per POST /mcp. '
  'No in-process session held. M3 — MCP elevation arc.';

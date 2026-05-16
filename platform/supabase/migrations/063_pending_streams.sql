-- γ7: Stream resume after disconnect
-- Stores partial synthesis output so clients can recover mid-stream text
-- after an abrupt disconnect (tab close, network partition, browser crash).
--
-- The Cloud Scheduler reaper (§M.4) prunes expired rows:
--   DELETE FROM pending_streams WHERE expires_at < now()
-- Default TTL: 30 minutes.
--
-- NOT APPLIED automatically — apply via §M.3 manual intervention.

CREATE TABLE IF NOT EXISTS pending_streams (
  query_id        TEXT PRIMARY KEY,
  conversation_id TEXT,
  accumulated_text TEXT NOT NULL DEFAULT '',
  last_event_seq  BIGINT NOT NULL DEFAULT 0,
  expires_at      TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pending_streams_expires_at
  ON pending_streams (expires_at);

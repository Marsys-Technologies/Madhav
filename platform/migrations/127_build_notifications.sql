-- Migration 127: build_notifications — SSE event log for real-time build progress
-- MARSYS-JIS Multi-Ayanamsha Build Orchestrator [BUILD-ORCH-B-04]

CREATE TABLE IF NOT EXISTS build_notifications (
    notif_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_id      UUID NOT NULL REFERENCES builds(build_id) ON DELETE CASCADE,
    event_type    TEXT NOT NULL
                  CHECK (event_type IN (
                    'build_queued','build_started','step_started','step_complete',
                    'step_failed','build_complete','build_failed','build_cancelled'
                  )),
    payload       JSONB NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at  TIMESTAMPTZ,
    subscriber_id TEXT        -- optional: which client received this
);

CREATE INDEX IF NOT EXISTS build_notif_build_idx ON build_notifications(build_id, created_at DESC);
CREATE INDEX IF NOT EXISTS build_notif_undelivered_idx ON build_notifications(build_id)
    WHERE delivered_at IS NULL;

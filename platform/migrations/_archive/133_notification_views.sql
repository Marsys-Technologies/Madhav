-- Migration 133: notification_views — server-side tracking of seen build notifications
-- MARSYS-JIS Multi-Ayanamsha Build Orchestrator [BUILD-ORCH-I-03]

CREATE TABLE IF NOT EXISTS notification_views (
    view_id       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    build_id      UUID        NOT NULL REFERENCES builds(build_id) ON DELETE CASCADE,
    user_id       TEXT        NOT NULL,  -- Firebase UID
    viewed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source        TEXT        CHECK (source IN ('toast','dashboard','email','push')),
    CONSTRAINT nv_unique_per_user UNIQUE (build_id, user_id)
);

CREATE INDEX IF NOT EXISTS nv_user_idx ON notification_views(user_id, viewed_at DESC);
CREATE INDEX IF NOT EXISTS nv_build_idx ON notification_views(build_id);

COMMENT ON TABLE notification_views IS 'Server-side tracking of build notifications seen by each user. Replaces localStorage approach from I-02 when migrated.';

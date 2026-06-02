-- Migration 126: engine_versions + build_engine_versions
-- Tracks which swisseph/algorithm version produced each build.
-- MARSYS-JIS Multi-Ayanamsha Build Orchestrator [BUILD-ORCH-B-03]

CREATE TABLE IF NOT EXISTS engine_versions (
    version_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engine_name   TEXT NOT NULL,           -- e.g. 'swisseph', 'natal_engine'
    version_str   TEXT NOT NULL,           -- e.g. '2.10.03', '1.4.2'
    git_sha       TEXT,                    -- git SHA of natal_engine at build time
    swisseph_ver  TEXT,                    -- swisseph C library version
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (engine_name, version_str)
);

CREATE TABLE IF NOT EXISTS build_engine_versions (
    build_id      UUID NOT NULL REFERENCES builds(build_id) ON DELETE CASCADE,
    version_id    UUID NOT NULL REFERENCES engine_versions(version_id),
    PRIMARY KEY (build_id, version_id)
);

CREATE INDEX IF NOT EXISTS bev_version_idx ON build_engine_versions(version_id);

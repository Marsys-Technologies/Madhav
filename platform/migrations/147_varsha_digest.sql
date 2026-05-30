-- Migration 147: Per-Varsha Yearly Digest
-- Stream C — A22 [BUILD-ORCH-STREAM-C-A22-S1]
-- Fully idempotent (CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS)

CREATE TABLE IF NOT EXISTS l1_varsha_digest (
    digest_id               BIGSERIAL   PRIMARY KEY,
    chart_id                UUID        NOT NULL,
    varsha_year             INT         NOT NULL,   -- e.g. 2026
    vimshottari_md          TEXT        NOT NULL,   -- main dasha lord name
    vimshottari_ad          TEXT,                   -- antardasha lord (may cross year boundary)
    bb_hit_count            INT         NOT NULL DEFAULT 0,
    anchor_count            INT         NOT NULL DEFAULT 0,
    anchor_labels           TEXT[]      NOT NULL DEFAULT '{}',
    sync_window_count       INT         NOT NULL DEFAULT 0,
    peak_cluster_intensity  INT,
    vedha_count             INT         NOT NULL DEFAULT 0,
    sade_sati_status        TEXT        NOT NULL
                                CHECK (sade_sati_status IN (
                                    'active','approaching','leaving','inactive'
                                )),
    year_theme              TEXT,                   -- one-sentence digest
    confidence_score        FLOAT       NOT NULL DEFAULT 0.5,
    embedding               vector(768),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS vd_unique_idx
    ON l1_varsha_digest(chart_id, varsha_year);
CREATE INDEX IF NOT EXISTS vd_chart_idx ON l1_varsha_digest(chart_id);
CREATE INDEX IF NOT EXISTS vd_year_idx  ON l1_varsha_digest(varsha_year);

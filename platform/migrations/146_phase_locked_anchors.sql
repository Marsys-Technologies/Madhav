-- Migration 146: Phase-Locked Anchors
-- Stream C — A16 [BUILD-ORCH-STREAM-C-A16-S1]
-- Fully idempotent (CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS)

CREATE TABLE IF NOT EXISTS l1_phase_locked_anchors (
    anchor_id           BIGSERIAL   PRIMARY KEY,
    chart_id            UUID        NOT NULL,
    anchor_label        TEXT        NOT NULL,    -- human-readable label e.g. "Mercury→Ketu MD change 2036"
    window_start        DATE        NOT NULL,
    window_end          DATE        NOT NULL,
    anchor_type         TEXT        NOT NULL
                            CHECK (anchor_type IN (
                                'dasha_change','dasha_synergy','transit_peak',
                                'vedha_cluster','bb_activation','tajik_peak','multi_system'
                            )),
    cluster_intensity   INT         NOT NULL,
    g29_rules_fired     TEXT[]      NOT NULL DEFAULT '{}',  -- rule_ids from g29_timing_rules
    systems_active      TEXT[]      NOT NULL DEFAULT '{}',
    primary_outcome     TEXT        NOT NULL,   -- main predicted theme
    alternative_scenario TEXT,                  -- contrarian scenario
    falsifiability_test TEXT        NOT NULL,   -- how to test in 1-2 sentences
    causal_prior_anchor BIGINT,                 -- FK to prior anchor (self-referential)
    confidence_score    FLOAT       NOT NULL DEFAULT 0.5,  -- 0.0-1.0
    embedding           vector(768),
    classical_citation  TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS pla_chart_idx    ON l1_phase_locked_anchors(chart_id);
CREATE INDEX IF NOT EXISTS pla_window_idx   ON l1_phase_locked_anchors(window_start, window_end);
CREATE INDEX IF NOT EXISTS pla_type_idx     ON l1_phase_locked_anchors(anchor_type);
CREATE UNIQUE INDEX IF NOT EXISTS pla_unique_idx
    ON l1_phase_locked_anchors(chart_id, window_start, anchor_label);

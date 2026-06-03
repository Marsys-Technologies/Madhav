-- brahma_bo_2-8.sql — bodha_* table schema for BO-2-8 holistic_bundle aggregation
--
-- Creates the four L2 Bodha subsystem tables that holistic_bundle aggregates over:
--   bodha_signals      (MSR — Multidimensional Signal Register)
--   bodha_graph_edges  (CGM — Chart Graph Model)
--   bodha_domain_links (CDLM — Cross-Domain Linkage Matrix)
--   bodha_resonance    (RM — Resonance Map)
--
-- These tables are populated by Wave-1 (bodha.signals + bodha.graph writers).
-- holistic_bundle (BO-2-8) is a pure read-aggregation layer — it adds NO new tables,
-- only depends on these four. This migration creates them idempotently so that:
--   (a) Wave-1 writers can upsert into them.
--   (b) BO-2-8 can query them without waiting for a separate migration.
--
-- BRAHMA-BO-2-8

-- ── bodha_signals (MSR) ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bodha_signals (
    signal_id       TEXT        NOT NULL,
    chart_id        UUID        NOT NULL,
    domain          TEXT        NOT NULL,         -- e.g. 'career', 'health', 'relationships'
    valence         TEXT        NOT NULL,         -- 'positive' | 'negative' | 'neutral' | 'mixed'
    confidence      NUMERIC(5,4),                -- 0.0000–1.0000 calibrated confidence
    salience        NUMERIC(5,4),                -- 0.0000–1.0000 relative salience
    state           TEXT,                        -- 'lit' | 'ripening' | 'dormant'
    signal_text     TEXT        NOT NULL,        -- human-readable signal description
    source_citation TEXT,                        -- FORENSIC/LEL citation ref
    graha_refs      TEXT[],                      -- planetary references
    house_refs      INTEGER[],                   -- house references (1–12)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (signal_id, chart_id)
);

CREATE INDEX IF NOT EXISTS bodha_signals_chart_id_idx
    ON bodha_signals (chart_id);

CREATE INDEX IF NOT EXISTS bodha_signals_domain_chart_idx
    ON bodha_signals (chart_id, domain);

CREATE INDEX IF NOT EXISTS bodha_signals_salience_idx
    ON bodha_signals (chart_id, salience DESC NULLS LAST);

-- ── bodha_graph_edges (CGM) ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bodha_graph_edges (
    edge_id         TEXT        NOT NULL,
    chart_id        UUID        NOT NULL,
    from_signal_id  TEXT        NOT NULL,        -- references bodha_signals.signal_id
    to_signal_id    TEXT        NOT NULL,        -- references bodha_signals.signal_id
    edge_type       TEXT        NOT NULL,        -- 'reinforce' | 'contradict' | 'modulate' | 'amplify'
    weight          NUMERIC(5,4),                -- 0.0000–1.0000 edge weight
    label           TEXT,                        -- optional human label
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (edge_id, chart_id)
);

CREATE INDEX IF NOT EXISTS bodha_graph_edges_chart_id_idx
    ON bodha_graph_edges (chart_id);

CREATE INDEX IF NOT EXISTS bodha_graph_edges_from_signal_idx
    ON bodha_graph_edges (chart_id, from_signal_id);

CREATE INDEX IF NOT EXISTS bodha_graph_edges_to_signal_idx
    ON bodha_graph_edges (chart_id, to_signal_id);

-- ── bodha_domain_links (CDLM) ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bodha_domain_links (
    link_id         TEXT        NOT NULL,
    chart_id        UUID        NOT NULL,
    from_domain     TEXT        NOT NULL,        -- source domain
    to_domain       TEXT        NOT NULL,        -- target domain
    link_type       TEXT        NOT NULL,        -- 'cross_domain' | 'karaka_bridge' | 'house_overlap'
    signal_ids      TEXT[],                      -- participating signal IDs
    strength        NUMERIC(5,4),                -- 0.0000–1.0000 linkage strength
    note            TEXT,                        -- interpretation note
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (link_id, chart_id)
);

CREATE INDEX IF NOT EXISTS bodha_domain_links_chart_id_idx
    ON bodha_domain_links (chart_id);

CREATE INDEX IF NOT EXISTS bodha_domain_links_domains_idx
    ON bodha_domain_links (chart_id, from_domain, to_domain);

-- ── bodha_resonance (RM) ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bodha_resonance (
    resonance_id    TEXT        NOT NULL,
    chart_id        UUID        NOT NULL,
    theme           TEXT        NOT NULL,        -- thematic pattern name
    signal_ids      TEXT[],                      -- constituent signal IDs
    resonance_type  TEXT        NOT NULL,        -- 'harmonic' | 'tension' | 'unresolved'
    amplitude       NUMERIC(5,4),                -- 0.0000–1.0000 resonance strength
    note            TEXT,                        -- interpretation note
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (resonance_id, chart_id)
);

CREATE INDEX IF NOT EXISTS bodha_resonance_chart_id_idx
    ON bodha_resonance (chart_id);

CREATE INDEX IF NOT EXISTS bodha_resonance_theme_idx
    ON bodha_resonance (chart_id, theme);

-- ── holistic_bundle view (optional convenience projection) ───────────────────
--
-- A materialised-view candidate for future caching. Left as a regular view for now.

CREATE OR REPLACE VIEW bodha_holistic_bundle_summary AS
SELECT
    s.chart_id,
    COUNT(DISTINCT s.signal_id)                             AS signal_count,
    COUNT(DISTINCT ge.edge_id)                              AS graph_edge_count,
    COUNT(DISTINCT dl.link_id)                              AS domain_link_count,
    COUNT(DISTINCT r.resonance_id)                          AS resonance_count,
    COUNT(DISTINCT s.signal_id) > 0                         AS b11_floor_passed,
    MAX(GREATEST(s.created_at, COALESCE(ge.created_at, s.created_at),
                 COALESCE(dl.created_at, s.created_at),
                 COALESCE(r.created_at, s.created_at)))    AS last_updated_at
FROM bodha_signals s
LEFT JOIN bodha_graph_edges ge ON ge.chart_id = s.chart_id
LEFT JOIN bodha_domain_links dl ON dl.chart_id = s.chart_id
LEFT JOIN bodha_resonance r     ON r.chart_id = s.chart_id
GROUP BY s.chart_id;

COMMENT ON TABLE bodha_signals IS
    'L2 Bodha — MSR (Multidimensional Signal Register). One row per signal per chart. '
    'Populated by Wave-1 bodha.signals writer. Queried by holistic_bundle (BO-2-8).';

COMMENT ON TABLE bodha_graph_edges IS
    'L2 Bodha — CGM (Chart Graph Model). Valenced edges between signals. '
    'Populated by Wave-1 bodha.graph writer. Queried by holistic_bundle (BO-2-8).';

COMMENT ON TABLE bodha_domain_links IS
    'L2 Bodha — CDLM (Cross-Domain Linkage Matrix). Cross-domain linkages. '
    'Populated by Wave-1 bodha.domain_links writer. Queried by holistic_bundle (BO-2-8).';

COMMENT ON TABLE bodha_resonance IS
    'L2 Bodha — RM (Resonance Map). Thematic resonance elements. '
    'Populated by Wave-1 bodha.resonance writer. Queried by holistic_bundle (BO-2-8).';

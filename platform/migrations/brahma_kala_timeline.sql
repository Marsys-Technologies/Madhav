-- brahma_kala_timeline.sql — Brahma L3 Kāla — kala.timeline (KA-3-1)
-- Asset:   kala.timeline
-- Tool:    timeline_query(chart_id, date_range) → deterministic dasha×transit alignment series
-- Table:   kala_timeline
-- Layer:   L3 Kāla (depends on L1 ganita.dashas via chart_facts dasha_vimshottari
--                   + L1 ganita.positions via ephemeris_daily
--                   + L2 bodha.signals via msr_signals/bodha_signals)
--
-- CONTRACT (BRAHMA L3 Kāla KA-3-1):
--   owns:   deterministic dasha×transit alignment series over native life range
--   tool:   timeline_query(chart_id, date_range)
--   table:  kala_timeline
--   acceptance:
--     - Saturn MD rows present for range 1991-08-21 → 2010-08-21
--     - Mercury MD rows present for range 2010-08-21 → 2027-08-21
--     - source_citation NOT NULL on all rows
--     - deterministic: same date always returns same row
--
-- Source:  PyJHora/SwissEph DE441 + Brahma-L1 (FORENSIC §5.1 Vimshottari)
-- Native:  Abhisek Mohanty, 1984-02-05, 10:43 IST Bhubaneswar
--          chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS kala_timeline;
--   DROP INDEX IF EXISTS idx_kala_timeline_chart_date;
--   DROP INDEX IF EXISTS idx_kala_timeline_mahadasha;
--   DROP INDEX IF EXISTS idx_kala_timeline_signal_activations;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — Core table ───────────────────────────────────────────────────────────
--
-- One row per (chart_id, date) with the active dasha state and any transit
-- highlights computed for that date. Signal activations are optional JSONB
-- populated only for dates that cross a dasha boundary or notable transit.
--
-- Design decisions:
--  - date granularity: daily (one row per calendar date)
--  - transit_highlights: top-N transit events from ephemeris_daily for that date
--    (NULL when ephemeris_daily table has no row for this date)
--  - signal_activations: bodha.signals that are "lit" given the dasha×transit state
--    (NULL when bodha tables are empty — graceful degradation)
--  - source_citation: non-null, references the primary data source

CREATE TABLE IF NOT EXISTS kala_timeline (
    id                   UUID        NOT NULL DEFAULT gen_random_uuid(),
    chart_id             UUID        NOT NULL,
    date                 DATE        NOT NULL,
    active_mahadasha     TEXT        NOT NULL,
    active_antardasha    TEXT        NOT NULL,
    -- JSONB: {planet, event_type, longitude, retrograde} array — top transit events
    transit_highlights   JSONB       NOT NULL DEFAULT '[]'::jsonb,
    -- JSONB: [{signal_id, domain, valence, confidence}] — activated bodha signals
    signal_activations   JSONB       NOT NULL DEFAULT '[]'::jsonb,
    -- Non-null per KA-3-1 contract
    source_citation      TEXT        NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT kala_timeline_pkey PRIMARY KEY (id),
    CONSTRAINT kala_timeline_chart_date_unique UNIQUE (chart_id, date)
);

COMMENT ON TABLE kala_timeline IS
    'L3 Kāla KA-3-1 — daily dasha×transit alignment rows per chart. '
    'Source: PyJHora/SwissEph DE441 + Brahma-L1 (FORENSIC §5.1).';

COMMENT ON COLUMN kala_timeline.active_mahadasha IS
    'Vimshottari Mahadasha lord active on this date (e.g. "Saturn", "Mercury").';
COMMENT ON COLUMN kala_timeline.active_antardasha IS
    'Vimshottari Antardasha lord active on this date (e.g. "Jupiter", "Ketu").';
COMMENT ON COLUMN kala_timeline.transit_highlights IS
    'Array of top transit events from ephemeris_daily for this date. '
    'Empty array when ephemeris_daily has no coverage for this date.';
COMMENT ON COLUMN kala_timeline.signal_activations IS
    'bodha.signals activated by this date''s dasha×transit state. '
    'Empty array when bodha tables are empty (graceful degradation).';
COMMENT ON COLUMN kala_timeline.source_citation IS
    'Non-null data provenance. Canonical value: '
    '"PyJHora/SwissEph DE441 + Brahma-L1".';

-- ── §2 — Indexes ──────────────────────────────────────────────────────────────

-- Primary lookup: chart_id + date range query (timeline_query tool path)
CREATE INDEX IF NOT EXISTS idx_kala_timeline_chart_date
    ON kala_timeline (chart_id, date);

-- Dasha-based filtering (e.g. "all Saturn MD dates")
CREATE INDEX IF NOT EXISTS idx_kala_timeline_mahadasha
    ON kala_timeline (chart_id, active_mahadasha, date);

-- GIN index for JSONB signal activation lookups
CREATE INDEX IF NOT EXISTS idx_kala_timeline_signal_activations
    ON kala_timeline USING gin (signal_activations);

COMMIT;

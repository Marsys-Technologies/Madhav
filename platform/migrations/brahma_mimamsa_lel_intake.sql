-- brahma_mimamsa_lel_intake.sql — Brahma L5 Mīmāṃsā — mimamsa.lel_intake (MI-5-1)
-- Asset:   mimamsa.lel_intake
-- Owns:    Life Event Log ingestion — 57 LEL events + chart-state index
-- Depends: (no FK hard-requirement; chart_id is a soft reference to native chart)
--
-- CONTRACT (BRAHMA L5 Mīmāṃsā — MI-5-1):
--   table: life_events
--     event_id       UUID PRIMARY KEY
--     event_date     DATE             — best available date (proxy date for year-approx)
--     event_type     TEXT             — category from LEL §3 schema
--     description    TEXT             — factual description (L1 Facts Layer content)
--     domain         TEXT             — category/subcategory compound label
--     outcome_observed TEXT           — retrodictive_match.predicted_by_chart value
--     source_citation TEXT NOT NULL   — provenance mandate (B.3)
--
--   table: event_chart_state_index
--     event_id           UUID NOT NULL — FK → life_events(event_id)
--     dasha_active       TEXT          — Vimshottari MD lord at event
--     antardasha_active  TEXT          — Vimshottari AD lord at event
--     key_transits       JSONB         — key transit notes from chart_state_at_event
--     convergence_score  FLOAT         — derived from retrodictive_match quality
--     source_citation    TEXT NOT NULL — provenance mandate (B.3)
--
--   Tool: lel_query(domain?, date_range?) → {events:[...], provenance_envelope}
--
-- NO LEAKAGE:
--   life_events is a calibration corpus ONLY.
--   It MUST NOT feed into prediction generation pipelines.
--   Prediction generation reads from chart_facts + MSR signals only.
--   Calibration reads life_events to score past-prediction accuracy.
--
-- Source:
--   LIFE_EVENT_LOG_v1_2.md (native-disclosed, 57 events v1.7, confidence 0.89)
--   chart_facts (rendered via forensic_render.ts; FORENSIC v8.0 chart data, §5.1 — md archived at 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS event_chart_state_index;
--   DROP TABLE IF EXISTS life_events;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — life_events table ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS life_events (
    event_id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    event_date        DATE         NOT NULL,
    event_type        TEXT         NOT NULL,
    description       TEXT         NOT NULL,
    domain            TEXT         NOT NULL,
    outcome_observed  TEXT,
    source_citation   TEXT         NOT NULL,
    ingested_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT life_events_source_citation_nonempty
        CHECK (source_citation <> '')
);

COMMENT ON TABLE life_events IS
'MI-5-1 mimamsa.lel_intake: 57 life events for native Abhisek Mohanty '
'(LIFE_EVENT_LOG_v1_2.md v1.7, confidence 0.89). '
'L5 Mīmāṃsā calibration corpus — MUST NOT feed into prediction generation. '
'Use only for calibration scoring of past predictions. '
'source_citation NON-NULL enforced — B.3 provenance mandate. '
'Native chart: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar. '
'BRAHMA-MI-5-1 | mimamsa.lel_intake';

COMMENT ON COLUMN life_events.event_id IS
'UUID primary key — stable identifier for downstream calibration references.';

COMMENT ON COLUMN life_events.event_date IS
'Best available date. For year-approx events, proxy date (YYYY-07-01) is used '
'per established convention (matching LEL computed_proxy_date convention).';

COMMENT ON COLUMN life_events.event_type IS
'LEL category field: career, education, relationship, family, health, '
'travel, residential, spiritual, creative, loss, finance, other, psychological.';

COMMENT ON COLUMN life_events.description IS
'Factual description from LEL §3. L1 Facts Layer content only — no interpretation.';

COMMENT ON COLUMN life_events.domain IS
'Compound domain label: category/subcategory from LEL schema. '
'e.g. "career/first_job_joined", "family/marriage", "loss/parent_passing".';

COMMENT ON COLUMN life_events.outcome_observed IS
'Retrodictive match quality: "yes" | "partial" | "no" | "unexamined" | "pending". '
'Sourced from LEL retrodictive_match.predicted_by_chart field. '
'NULL = chart_state not yet examined for this event.';

COMMENT ON COLUMN life_events.source_citation IS
'Non-null provenance: "LIFE_EVENT_LOG_v1_2.md (native-disclosed)". '
'B.3 mandate: every row carries full provenance chain.';

-- ── §2 — event_chart_state_index table ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS event_chart_state_index (
    id                 BIGSERIAL    PRIMARY KEY,
    event_id           UUID         NOT NULL,
    dasha_active       TEXT,
    antardasha_active  TEXT,
    key_transits       JSONB        NOT NULL DEFAULT '[]'::JSONB,
    convergence_score  FLOAT
                       CHECK (convergence_score IS NULL
                              OR (convergence_score >= 0.0 AND convergence_score <= 1.0)),
    source_citation    TEXT         NOT NULL,
    indexed_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT event_chart_state_index_event_fk
        FOREIGN KEY (event_id) REFERENCES life_events(event_id)
        ON DELETE CASCADE,

    CONSTRAINT event_chart_state_index_unique
        UNIQUE (event_id),

    CONSTRAINT event_chart_state_index_citation_nonempty
        CHECK (source_citation <> '')
);

COMMENT ON TABLE event_chart_state_index IS
'MI-5-1 chart-state index: Vimshottari dasha + transit context at each LEL event. '
'One row per event (1-to-1 with life_events). '
'convergence_score in [0.0, 1.0]: derived from retrodictive_match quality '
'(yes=1.0, partial=0.5, no=0.0, unexamined/pending=NULL). '
'key_transits: JSONB array of transit notes from LEL chart_state_at_event. '
'source_citation NON-NULL enforced — B.3 provenance mandate. '
'BRAHMA-MI-5-1 | mimamsa.lel_intake';

COMMENT ON COLUMN event_chart_state_index.dasha_active IS
'Vimshottari Maha Dasha lord at event date. '
'Source: chart_facts (rendered via forensic_render.ts; FORENSIC v8.0 chart data, §5.1 — md archived at 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) via LEL chart_state_at_event.';

COMMENT ON COLUMN event_chart_state_index.antardasha_active IS
'Vimshottari Antar Dasha lord at event date. '
'Source: FORENSIC §5.1 via LEL chart_state_at_event.';

COMMENT ON COLUMN event_chart_state_index.key_transits IS
'JSONB array of key transit notes. '
'Sourced from LEL chart_state_at_event.transits_of_note. '
'May be empty array [] for events with pending_computation status.';

COMMENT ON COLUMN event_chart_state_index.convergence_score IS
'Signal convergence quality: NULL (unexamined/pending), 0.0 (no match), '
'0.5 (partial match), 1.0 (yes match). '
'Derived from LEL retrodictive_match.predicted_by_chart. '
'CHECK: 0.0 <= convergence_score <= 1.0 when non-null.';

-- ── §3 — Indexes ──────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS life_events_event_date_idx
    ON life_events (event_date);

CREATE INDEX IF NOT EXISTS life_events_event_type_idx
    ON life_events (event_type);

CREATE INDEX IF NOT EXISTS life_events_domain_idx
    ON life_events (domain);

CREATE INDEX IF NOT EXISTS life_events_outcome_idx
    ON life_events (outcome_observed);

CREATE INDEX IF NOT EXISTS event_chart_state_event_id_idx
    ON event_chart_state_index (event_id);

CREATE INDEX IF NOT EXISTS event_chart_state_dasha_idx
    ON event_chart_state_index (dasha_active, antardasha_active);

CREATE INDEX IF NOT EXISTS event_chart_state_convergence_idx
    ON event_chart_state_index (convergence_score);

-- ── §4 — lel_query SQL function ───────────────────────────────────────────────
--
-- Tool-layer entry point: returns events filtered by domain and/or date range.
-- Returns JSONB with provenance_envelope for MCP compliance.

CREATE OR REPLACE FUNCTION lel_query(
    p_domain      TEXT    DEFAULT NULL,
    p_date_start  DATE    DEFAULT NULL,
    p_date_end    DATE    DEFAULT NULL,
    p_limit       INT     DEFAULT 100
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_events      JSONB;
    v_total_count BIGINT;
    v_result      JSONB;
BEGIN
    SELECT COUNT(*)
    INTO   v_total_count
    FROM   life_events le
    WHERE  (p_domain IS NULL OR le.domain ILIKE '%' || p_domain || '%' OR le.event_type ILIKE '%' || p_domain || '%')
      AND  (p_date_start IS NULL OR le.event_date >= p_date_start)
      AND  (p_date_end   IS NULL OR le.event_date <= p_date_end);

    SELECT jsonb_agg(
        jsonb_build_object(
            'event_id',         le.event_id,
            'event_date',       le.event_date,
            'event_type',       le.event_type,
            'description',      le.description,
            'domain',           le.domain,
            'outcome_observed', le.outcome_observed,
            'dasha_active',     cs.dasha_active,
            'antardasha_active', cs.antardasha_active,
            'key_transits',     cs.key_transits,
            'convergence_score', cs.convergence_score,
            'source_citation',  le.source_citation
        )
        ORDER BY le.event_date
    )
    INTO v_events
    FROM life_events le
    LEFT JOIN event_chart_state_index cs ON cs.event_id = le.event_id
    WHERE (p_domain IS NULL OR le.domain ILIKE '%' || p_domain || '%' OR le.event_type ILIKE '%' || p_domain || '%')
      AND (p_date_start IS NULL OR le.event_date >= p_date_start)
      AND (p_date_end   IS NULL OR le.event_date <= p_date_end)
    LIMIT p_limit;

    v_result := jsonb_build_object(
        'events',           COALESCE(v_events, '[]'::JSONB),
        'total_count',      v_total_count,
        'filter_applied',   jsonb_build_object(
            'domain',       p_domain,
            'date_start',   p_date_start,
            'date_end',     p_date_end,
            'limit',        p_limit
        ),
        'provenance_envelope', jsonb_build_object(
            'source',           'mimamsa.lel_intake',
            'asset',            'MI-5-1',
            'lel_version',      'LIFE_EVENT_LOG_v1_2.md v1.7',
            'total_events',     57,
            'confidence',       0.89,
            'source_citation',  'LIFE_EVENT_LOG_v1_2.md (native-disclosed)',
            'no_leakage_note',  'life_events is calibration corpus only — must not feed prediction generation',
            'b3_compliant',     true
        )
    );

    RETURN v_result;
END;
$$;

COMMENT ON FUNCTION lel_query(TEXT, DATE, DATE, INT) IS
'MI-5-1 tool entry point: query LEL events by domain and/or date range. '
'Args: p_domain (ILIKE filter on domain/event_type), p_date_start, p_date_end, p_limit. '
'Returns: {events:[{event_id, event_date, event_type, description, domain, '
'outcome_observed, dasha_active, antardasha_active, key_transits, convergence_score, '
'source_citation}], total_count, filter_applied, provenance_envelope}. '
'NO LEAKAGE: life_events is calibration corpus only. '
'BRAHMA-MI-5-1 | mimamsa.lel_intake';

-- ── §5 — Calibration summary view ────────────────────────────────────────────
--
-- Convenience view: retrodictive match distribution for the corpus.

CREATE OR REPLACE VIEW mimamsa_calibration_summary AS
SELECT
    outcome_observed,
    COUNT(*)                                       AS event_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM life_events
GROUP BY outcome_observed
ORDER BY event_count DESC;

COMMENT ON VIEW mimamsa_calibration_summary IS
'MI-5-1 calibration summary: distribution of retrodictive match outcomes. '
'Shows: outcome_observed, event_count, pct across all ingested LEL events. '
'BRAHMA-MI-5-1 | mimamsa.lel_intake';

COMMIT;

-- ── Notes ─────────────────────────────────────────────────────────────────────
--
-- Population:
--   python -m brahmagyan.mimamsa.lel_intake seed
--   This inserts all 57 LEL events into life_events + event_chart_state_index.
--
-- MCP tool: platform-mcp/src/tools/mimamsa_lel_intake.ts
--
-- Python engine: platform/python-sidecar/brahmagyan/mimamsa/lel_intake.py
--
-- Acceptance gate (MI-5-1):
--   SELECT COUNT(*) FROM life_events;                → must return 57
--   SELECT COUNT(*) FROM event_chart_state_index;    → must return 57
--   SELECT COUNT(*) FROM life_events WHERE source_citation IS NULL OR source_citation = ''; → must return 0
--   SELECT lel_query(NULL, NULL, NULL, 10);          → must return events array with provenance_envelope
--   SELECT lel_query('career', NULL, NULL, 100);     → must return career events
--   SELECT lel_query(NULL, '2020-01-01', '2026-12-31', 100); → must return recent events

-- Migration 267: ga_transit_anchors — per-chart Gochara reference anchor table
-- Transit/Gochara Subsystem Gate-1 — 2026-06-17
--
-- Stores natal position anchors needed for transit calculation:
--   - Which sign each graha occupies natally (for sign-ingress triggers)
--   - Natal house from Moon (1–12, for classical Gochara counting)
--   - Natal absolute degree (for exact degree-based transit triggers)
--
-- One row per (chart_id, ayanamsha_id, graha) — 9 grahas × 5 ayanamshas = 45 rows per chart.
-- L1 idempotency: DELETE WHERE (chart_id, ayanamsha_id) then INSERT.
--
-- Depends on: ga_positions (sidereal longitudes), ga_structural (house placements)
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS ga_transit_anchors;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

CREATE TABLE IF NOT EXISTS ga_transit_anchors (
    id                        SERIAL PRIMARY KEY,
    chart_id                  UUID        NOT NULL,
    build_id                  TEXT        NOT NULL,
    ayanamsha_id              TEXT        NOT NULL,
    graha                     TEXT        NOT NULL,     -- canonical lowercase graha name
    natal_sign                TEXT        NOT NULL,     -- sign name e.g. 'aquarius'
    natal_house_from_moon     INTEGER     NOT NULL
                              CHECK (natal_house_from_moon BETWEEN 1 AND 12),
    natal_degree_absolute     DOUBLE PRECISION NOT NULL,  -- 0–360 sidereal longitude
    computed_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ga_transit_anchors_natural_key
        UNIQUE (chart_id, ayanamsha_id, graha)
);

CREATE INDEX IF NOT EXISTS idx_ga_transit_anchors_chart
    ON ga_transit_anchors (chart_id, ayanamsha_id);

CREATE INDEX IF NOT EXISTS idx_ga_transit_anchors_graha
    ON ga_transit_anchors (chart_id, graha);

COMMENT ON TABLE ga_transit_anchors IS
    'L1 Gaṇita: Natal position anchors for Gochara (transit) calculation. '
    'natal_house_from_moon is the classical counting from natal Moon sign (1 = own sign). '
    'One row per (chart, ayanamsha, graha). Depends on ga_positions + ga_structural.';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS ga_transit_anchors;
--   COMMIT;
-- =============================================================================

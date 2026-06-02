-- Migration 142: Bhrigu Bindu lifetime transit table
-- Stream C — A19 [BUILD-ORCH-STREAM-C-A19-S1]
-- Stores dates when each graha transits within ±1° of the native's Bhrigu Bindu
-- (Moon-Rahu midpoint, sidereal Lahiri) from 2026 to 2060.

CREATE TABLE IF NOT EXISTS l1_bhrigu_bindu_transits (
    transit_id          BIGSERIAL   PRIMARY KEY,
    chart_id            UUID        NOT NULL,
    graha               TEXT        NOT NULL
                            CHECK (graha IN (
                                'sun','moon','mars','mercury','jupiter',
                                'venus','saturn','rahu','ketu'
                            )),
    hit_iso             DATE        NOT NULL,       -- date of exact transit
    bb_longitude_deg    FLOAT       NOT NULL,       -- BB degree in sidereal zodiac (Lahiri)
    graha_longitude_deg FLOAT       NOT NULL,       -- graha's longitude on hit_iso
    orb_deg             FLOAT       NOT NULL,       -- distance from BB (0.0 to 1.0)
    transit_type        TEXT        NOT NULL
                            CHECK (transit_type IN ('exact','applying','separating')),
    strength_score      FLOAT,                      -- 0.0-1.0; 1.0 = exact hit
    classical_citation  TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS bb_transits_chart_idx ON l1_bhrigu_bindu_transits(chart_id);
CREATE INDEX IF NOT EXISTS bb_transits_graha_idx ON l1_bhrigu_bindu_transits(graha);
CREATE INDEX IF NOT EXISTS bb_transits_hit_idx   ON l1_bhrigu_bindu_transits(hit_iso);

CREATE UNIQUE INDEX IF NOT EXISTS bb_transits_unique_idx
    ON l1_bhrigu_bindu_transits(chart_id, graha, hit_iso);

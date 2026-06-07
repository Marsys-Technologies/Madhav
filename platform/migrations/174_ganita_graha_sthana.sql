-- Migration 174: ganita_graha_sthana — PyJHora per-chart natal positions
-- Stream G deliverable (BRAHMA-G-1): dedicated table for graha_sthana asset
-- Engine: PyJHora (native decision: PyJHora IS the JH logic)
-- Source: pyjhora_adapter.compute.compute_chart()

CREATE TABLE IF NOT EXISTS ganita_graha_sthana (
    id                  BIGSERIAL PRIMARY KEY,
    chart_id            UUID NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
    build_id            TEXT NOT NULL,
    ayanamsha_id        TEXT NOT NULL DEFAULT 'lahiri',
    planet              TEXT NOT NULL,          -- Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|Lagna
    longitude_deg       NUMERIC(12, 6) NOT NULL, -- sidereal longitude 0–360°
    sign                TEXT,                   -- Aries|Taurus|...|Pisces
    sign_id             SMALLINT,               -- 1–12
    nakshatra           TEXT,                   -- Ashwini|Bharani|...|Revati
    nakshatra_id        SMALLINT,               -- 1–27
    nakshatra_pada      SMALLINT,               -- 1–4
    house               SMALLINT,               -- whole-sign house 1–12
    is_retrograde       BOOLEAN NOT NULL DEFAULT FALSE,
    speed_dps           NUMERIC(12, 6),         -- degrees per day (negative = retrograde)
    source_citation     TEXT DEFAULT 'pyjhora/lahiri',
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_ganita_graha_sthana_chart_ayan_planet
        UNIQUE (chart_id, ayanamsha_id, planet)
);

-- Index for chart-level queries
CREATE INDEX IF NOT EXISTS idx_ganita_graha_sthana_chart_id
    ON ganita_graha_sthana (chart_id);

-- Index for build provenance
CREATE INDEX IF NOT EXISTS idx_ganita_graha_sthana_build_id
    ON ganita_graha_sthana (build_id);

-- Index for per-sign queries (e.g. "all charts with Sun in Capricorn")
CREATE INDEX IF NOT EXISTS idx_ganita_graha_sthana_planet_sign
    ON ganita_graha_sthana (planet, sign_id);

COMMENT ON TABLE ganita_graha_sthana IS
    'L1 Gaṇita: per-chart natal graha positions computed by PyJHora. '
    'Stream G (BRAHMA-G-1). One row per chart × ayanamsha × planet/lagna. '
    'Engine: PyJHora 4.8.6 via pyjhora_adapter. '
    'Falls back to ganita_positions if this table is absent.';

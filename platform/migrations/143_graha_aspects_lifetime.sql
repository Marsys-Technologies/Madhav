-- Migration 143: l1_graha_aspects_lifetime
-- Per-graha next-exact-aspect lifetime table (Parashari + classical + Tajik)
-- A21 [BUILD-ORCH-STREAM-C-A21-S1]

CREATE TABLE IF NOT EXISTS l1_graha_aspects_lifetime (
    aspect_id          BIGSERIAL   PRIMARY KEY,
    chart_id           UUID        NOT NULL,
    natal_graha        TEXT        NOT NULL,
    transit_graha      TEXT        NOT NULL,
    aspect_type        TEXT        NOT NULL,   -- conjunction/sextile/square/trine/opposition/
                                               -- parashari_4th/parashari_8th/parashari_5th/
                                               -- parashari_9th/parashari_3rd/parashari_10th/
                                               -- tajik_ithasala/tajik_ishrafa/tajik_trine/tajik_sextile
    aspect_system      TEXT        NOT NULL
                           CHECK (aspect_system IN ('parashari','classical','tajik')),
    exact_date         DATE        NOT NULL,
    natal_graha_lon    FLOAT       NOT NULL,
    transit_graha_lon  FLOAT       NOT NULL,
    aspect_degree      FLOAT       NOT NULL,   -- the target angle (0/60/90/120/180 etc)
    orb_deg            FLOAT       NOT NULL,   -- how close to exact (0.0 = exact)
    is_applying        BOOLEAN,                -- true = applying, false = separating, null = unknown
    classical_citation TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS gal_chart_idx         ON l1_graha_aspects_lifetime(chart_id);
CREATE INDEX IF NOT EXISTS gal_natal_graha_idx   ON l1_graha_aspects_lifetime(natal_graha);
CREATE INDEX IF NOT EXISTS gal_transit_graha_idx ON l1_graha_aspects_lifetime(transit_graha);
CREATE INDEX IF NOT EXISTS gal_exact_date_idx    ON l1_graha_aspects_lifetime(exact_date);
CREATE UNIQUE INDEX IF NOT EXISTS gal_unique_idx
    ON l1_graha_aspects_lifetime(chart_id, natal_graha, transit_graha, aspect_type, exact_date);

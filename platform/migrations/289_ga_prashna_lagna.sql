-- migration 289 — ga_prashna_lagna
-- ga_prashna_lagna: Prashna-Lagna computed by each method, per ayanamsha.
-- L1 table: per prashna chart_id × ayanamsha × method.
BEGIN;
CREATE TABLE IF NOT EXISTS ga_prashna_lagna (
    id              SERIAL PRIMARY KEY,
    chart_id        UUID NOT NULL,        -- references prashna_charts(chart_id)
    ayanamsha_id    TEXT NOT NULL,
    lagna_method    TEXT NOT NULL,        -- e.g. 'tajik_moment_lagna', 'kp_249', etc.
    lagna_rashi     TEXT NOT NULL,        -- sign name (Aries, Taurus, etc.)
    lagna_degree    FLOAT,               -- degrees within sign (0-30)
    kp_sub_lord     TEXT,               -- for kp_249 method: the sublord planet name
    is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
    classical_citation TEXT NOT NULL,
    UNIQUE (chart_id, ayanamsha_id, lagna_method)
);
COMMIT;

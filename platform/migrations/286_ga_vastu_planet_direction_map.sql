-- Migration 286: ga_vastu_planet_direction_map (L1 per-chart Astrovastu table)
-- Astrovastu subsystem Gate-1: maps each graha to its classical Vastu direction
-- with condition score from ga_condition_composite and direction_impact label.
-- Idempotency: L1 pattern — DELETE (chart_id, ayanamsha_id) then INSERT in writer.

BEGIN;

CREATE TABLE IF NOT EXISTS ga_vastu_planet_direction_map (
    id                  SERIAL PRIMARY KEY,
    chart_id            UUID NOT NULL,
    ayanamsha_id        TEXT NOT NULL,
    graha               TEXT NOT NULL,
    direction           TEXT NOT NULL,
    condition_score     NUMERIC,
    dignity_d1          TEXT,
    direction_impact    TEXT NOT NULL,
    indication_tier     TEXT NOT NULL DEFAULT 'traditional_vastu',
    classical_citation  TEXT NOT NULL,
    computed_at         TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (chart_id, ayanamsha_id, graha)
);

CREATE INDEX IF NOT EXISTS idx_ga_vastu_map_chart
    ON ga_vastu_planet_direction_map(chart_id, ayanamsha_id);

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS ga_vastu_planet_direction_map;
--   COMMIT;
-- =============================================================================

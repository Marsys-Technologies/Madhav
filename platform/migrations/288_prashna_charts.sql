-- migration 288 — prashna_charts schema table
-- Creates the prashna_charts infrastructure table (the horary chart entry point).
-- This is NOT an asset — it's a schema table that links chart_id to question metadata.
-- Prashna chart: a chart cast for the moment a question is asked.
-- The chart_id references the charts table (the prashna chart IS a chart with its
-- question-moment as the birth time).
BEGIN;
CREATE TABLE IF NOT EXISTS prashna_charts (
    chart_id            UUID PRIMARY KEY,  -- FK to charts(id) conceptually (no FK to avoid circular deps)
    question_text       TEXT NOT NULL,
    question_class      TEXT NOT NULL,     -- 'marriage','career','litigation_legal','lost_object',
                                          --  'health_illness','finance_wealth','travel_journey',
                                          --  'property_land','children_progeny','death_longevity',
                                          --  'spiritual_religious','enemy_conflict'
    querent_natal_chart_id UUID,          -- optional: querent's natal chart for Chandra method
    prashna_lagna_method TEXT NOT NULL DEFAULT 'tajik_moment_lagna',
                                          -- 'tajik_moment_lagna','kp_249','aarudha_based',
                                          -- 'chandra_lagna','swara_based'
    kp_number           INT,              -- 1-249 (for kp_249 method)
    querent_direction   TEXT,             -- 'east','north','west','south' (for aarudha_based)
    active_nostril      TEXT,             -- 'right','left' (for swara_based)
    question_instant    TIMESTAMPTZ NOT NULL,  -- UTC datetime of the question
    question_lat        FLOAT,
    question_lon        FLOAT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
COMMIT;

-- migration 290 — ga_prashna_judgment
-- ga_prashna_judgment: The horary judgment per prashna chart per ayanamsha.
-- One row per chart_id × ayanamsha_id — the primary Tajik verdict.
BEGIN;
CREATE TABLE IF NOT EXISTS ga_prashna_judgment (
    id                      SERIAL PRIMARY KEY,
    chart_id                UUID NOT NULL,
    ayanamsha_id            TEXT NOT NULL,
    question_class          TEXT NOT NULL,
    querent_significator    TEXT NOT NULL,   -- planet name (Moon or lagna lord)
    quesited_significator   TEXT NOT NULL,   -- planet name (karaka or house lord)
    querent_longitude       FLOAT,           -- tropical/sidereal longitude degrees 0-360
    quesited_longitude      FLOAT,
    longitudinal_gap        FLOAT,           -- absolute degree gap between them
    is_applying             BOOLEAN,         -- true=Ithasala, false=Eesarpha/separating
    tajik_yoga              TEXT,            -- 'ithasala','eesarpha','nakta','yamaya','kambula',
                                             --  'gairi_kambula','rudda', etc.
    judgment_text           TEXT NOT NULL,   -- 'YES','NO','PAST','UNCERTAIN'
    fructification_value    FLOAT,           -- the computed degree gap
    fructification_unit     TEXT,            -- 'hours','days','months','years'
    fructification_rule_id  TEXT,            -- references bg_prashna_fructification_rules.rule_id
    lagna_rashi             TEXT,            -- sign rising in prashna chart (for timing matrix)
    classical_citation      TEXT NOT NULL,
    UNIQUE (chart_id, ayanamsha_id)
);
COMMIT;

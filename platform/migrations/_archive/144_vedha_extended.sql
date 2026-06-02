-- Migration 144: Extended Vedha (Obstruction) Reference Table
-- Stream C [BUILD-ORCH-STREAM-C-A18-S1]
-- Idempotent: CREATE TABLE IF NOT EXISTS with unique index conflict handling
--
-- Covers 6 vedha systems:
--   1. sarvatobhadra  — 28 SBC nakshatra vedha pairs (mirrors l1_sarvatobhadra_vedha)
--   2. sapta_shalaka  — Tara-based 7-spoke obstruction relationships
--   3. tajik_year_lord — Annual chart year-lord vedha to natal planets
--   4. dasha_sub_lord  — Sub-period lord vedha obstructions per dasha system
--   5. transit_chakra  — Transit graha vedha via Kota Chakra ring analysis
--   6. argala          — Planetary argala/pratargala (intervention/counter-intervention)

CREATE TABLE IF NOT EXISTS l1_vedha_extended (
    vedha_id            BIGSERIAL   PRIMARY KEY,
    vedha_system        TEXT        NOT NULL
                            CHECK (vedha_system IN (
                                'sarvatobhadra','sapta_shalaka','tajik_year_lord',
                                'dasha_sub_lord','transit_chakra','argala'
                            )),
    source_nakshatra    TEXT        NOT NULL,   -- the natal nakshatra being obstructed
    obstructing_element TEXT        NOT NULL,   -- nakshatra, planet, or period that obstructs
    obstruction_type    TEXT        NOT NULL,   -- vedha / argala / pratargala / viprit_argala
    severity            TEXT        NOT NULL
                            CHECK (severity IN ('strong','moderate','weak','cancellation')),
    cancellation_rule   TEXT,                   -- if severity=cancellation, describe the rule
    classical_citation  TEXT,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS vedha_ext_system_idx ON l1_vedha_extended(vedha_system);
CREATE INDEX IF NOT EXISTS vedha_ext_source_idx ON l1_vedha_extended(source_nakshatra);
CREATE UNIQUE INDEX IF NOT EXISTS vedha_ext_unique_idx
    ON l1_vedha_extended(vedha_system, source_nakshatra, obstructing_element, obstruction_type);

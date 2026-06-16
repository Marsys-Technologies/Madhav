-- Migration 266: Transit/Gochara Subsystem Gate-1 — bg_transit_engine + bg_transit_rules
-- L0 Brahmagyan static reference tables for classical Gochara (transit) rules.
-- Chart-agnostic global reference data only.
--
-- Sources:
--   BPHS Ch.22 — Graha Gati (planetary motion parameters)
--   BPHS Ch.29 — Gochara Phala (transit results)
--   Phaladeepika Ch.26 — Gochara Vedha
--
-- ROLLBACK:
--   DELETE FROM asset_registry WHERE asset_id IN ('bg_transit_engine','bg_transit_rules');
--   DROP TABLE IF EXISTS bg_transit_rules;
--   DROP TABLE IF EXISTS bg_transit_engine;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — bg_transit_engine ────────────────────────────────────────────────────
-- One row per graha; average daily motion and period data.

CREATE TABLE IF NOT EXISTS bg_transit_engine (
    id                    SERIAL PRIMARY KEY,
    graha                 TEXT NOT NULL UNIQUE,          -- canonical lowercase graha name
    avg_daily_motion_deg  DOUBLE PRECISION NOT NULL,     -- degrees per day (negative = retrograde-biased)
    zodiac_period_days    DOUBLE PRECISION NOT NULL,     -- full zodiac traversal in days
    sign_residence_days   DOUBLE PRECISION NOT NULL,     -- average days per sign
    classical_citation    TEXT NOT NULL                  -- mandatory source citation
);

COMMENT ON TABLE bg_transit_engine IS
    'L0 Brahmagyan: Average graha motion parameters. '
    'Source: BPHS Ch.22. One row per graha. Classical attested values only.';

-- ── §2 — bg_transit_rules ────────────────────────────────────────────────────
-- Classical Gochara rules: favourable, unfavourable, and vedha obstruction data.

CREATE TABLE IF NOT EXISTS bg_transit_rules (
    id                 SERIAL PRIMARY KEY,
    rule_type          TEXT NOT NULL
                       CHECK (rule_type IN ('favourable', 'unfavourable', 'vedha')),
    graha              TEXT NOT NULL,                    -- canonical lowercase graha name
    primary_house      INTEGER NOT NULL
                       CHECK (primary_house BETWEEN 1 AND 12),
    vedha_house        INTEGER
                       CHECK (vedha_house BETWEEN 1 AND 12),
    phala              TEXT NOT NULL,                    -- brief result description
    classical_citation TEXT NOT NULL,                    -- mandatory source citation
    rule_notes         TEXT,                             -- vedha exceptions, nuances
    CONSTRAINT bg_transit_rules_graha_type_house_unique
        UNIQUE (graha, rule_type, primary_house)
);

COMMENT ON TABLE bg_transit_rules IS
    'L0 Brahmagyan: Classical Gochara (transit) rules from BPHS Ch.29 and Phaladeepika Ch.26. '
    'primary_house is counted from natal Moon. vedha_house is the house whose transit '
    'nullifies the primary house result. All rows carry mandatory classical_citation.';

CREATE INDEX IF NOT EXISTS idx_bg_transit_rules_graha
    ON bg_transit_rules (graha);

CREATE INDEX IF NOT EXISTS idx_bg_transit_rules_type
    ON bg_transit_rules (rule_type);

-- ── §3 — asset_registry entries ──────────────────────────────────────────────

INSERT INTO asset_registry (asset_id, display_name, layer, scope, asset_type, depends_on,
    count_sql, target_floor, sort_order, has_substeps)
VALUES (
    'bg_transit_engine',
    'Transit Engine Parameters (bg_transit_engine)',
    'L0',
    'global',
    'brahmagyan',
    ARRAY[]::TEXT[],
    '(SELECT COUNT(*) FROM bg_transit_engine)',
    9,
    61,
    false
) ON CONFLICT (asset_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    count_sql    = EXCLUDED.count_sql,
    target_floor = EXCLUDED.target_floor;

INSERT INTO asset_registry (asset_id, display_name, layer, scope, asset_type, depends_on,
    count_sql, target_floor, sort_order, has_substeps)
VALUES (
    'bg_transit_rules',
    'Classical Gochara Rules (bg_transit_rules)',
    'L0',
    'global',
    'brahmagyan',
    ARRAY[]::TEXT[],
    '(SELECT COUNT(*) FROM bg_transit_rules)',
    37,
    62,
    false
) ON CONFLICT (asset_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    count_sql    = EXCLUDED.count_sql,
    target_floor = EXCLUDED.target_floor;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id IN ('bg_transit_engine','bg_transit_rules');
--   DROP TABLE IF EXISTS bg_transit_rules;
--   DROP TABLE IF EXISTS bg_transit_engine;
--   COMMIT;
-- =============================================================================

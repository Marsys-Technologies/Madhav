-- Migration 140: Sarvatobhadra Chakra Global Reference Table
-- Stream C [BUILD-ORCH-STREAM-C-A17-S1]
-- Idempotent: CREATE TABLE IF NOT EXISTS with inline CHECK constraints

-- Table 1: 28 nakshatra positions in the 9x9 SBC grid
CREATE TABLE IF NOT EXISTS l1_sarvatobhadra_positions (
    nakshatra_id      INT         NOT NULL,  -- 1-28 (27 standard + Abhijit)
    nakshatra_name    TEXT        NOT NULL,
    grid_row          INT         NOT NULL   CHECK (grid_row BETWEEN 0 AND 8),
    grid_col          INT         NOT NULL   CHECK (grid_col BETWEEN 0 AND 8),
    side              TEXT        NOT NULL   CHECK (side IN ('north','south','east','west')),
    ruling_vowel      TEXT,                  -- Sanskrit vowel association (empty if unknown)
    ruling_consonant  TEXT,                  -- Sanskrit consonant association (empty if unknown)
    PRIMARY KEY (nakshatra_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS sbc_grid_cell_idx
    ON l1_sarvatobhadra_positions(grid_row, grid_col);

-- Table 2: Vedha (obstruction) pairs — diametrically opposite nakshatras
CREATE TABLE IF NOT EXISTS l1_sarvatobhadra_vedha (
    vedha_id             SERIAL      PRIMARY KEY,
    nakshatra_1_id       INT         NOT NULL REFERENCES l1_sarvatobhadra_positions(nakshatra_id),
    nakshatra_1_name     TEXT        NOT NULL,
    nakshatra_2_id       INT         NOT NULL REFERENCES l1_sarvatobhadra_positions(nakshatra_id),
    nakshatra_2_name     TEXT        NOT NULL,
    vedha_axis           TEXT        NOT NULL
                             CHECK (vedha_axis IN ('north-south','east-west','diagonal')),
    classical_citation   TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS sbc_vedha_pair_idx
    ON l1_sarvatobhadra_vedha(
        LEAST(nakshatra_1_id, nakshatra_2_id),
        GREATEST(nakshatra_1_id, nakshatra_2_id)
    );

COMMENT ON TABLE l1_sarvatobhadra_positions IS
    'A17 Sarvatobhadra Chakra: 28 nakshatra positions in the classical 9×9 grid '
    '(27 standard nakshatras + Abhijit). Source: Muhurta Chintamani, Jyotish Sara Sangraha. '
    '[BUILD-ORCH-STREAM-C-A17-S1]';

COMMENT ON TABLE l1_sarvatobhadra_vedha IS
    'A17 Sarvatobhadra Chakra: 14 vedha (obstruction) pairs — nakshatras diametrically '
    'opposite in the 9×9 grid that obstruct each other in muhurta and transit analysis. '
    'Source: Muhurta Chintamani. [BUILD-ORCH-STREAM-C-A17-S1]';

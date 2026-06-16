-- 238_bg_nakshatra_tables.sql
-- =============================================================================
-- bg_nakshatra — L0 Global Nakshatra Reference
-- Three-grain split: per-nakshatra (27 + Abhijit 28th), per-pada (108),
-- relational matrices. FK'd. ON CONFLICT idempotency (L0 pattern).
--
-- reference_nakshatras (from bg_reference) is deprecated in place —
-- bg_nakshatra becomes the sole authority for nakshatra attributes.
--
-- Per §N.3 (L0 idempotency): ON CONFLICT DO NOTHING throughout.
-- Per §N.1: asset id = 'bg_nakshatra', scope = global.
-- Applied surgically via Cloud SQL Auth Proxy — never via deploy.yml.
-- =============================================================================

BEGIN;

-- ── GRAIN 1: per-nakshatra (27 + Abhijit) ─────────────────────────────────

CREATE TABLE IF NOT EXISTS reference_nakshatra (
    nakshatra_id             SMALLINT      PRIMARY KEY,   -- 1-27; Abhijit=28
    -- Identity
    name_sa_iast             TEXT          NOT NULL,      -- IAST transliteration
    name_sa_devanagari       TEXT          NOT NULL,      -- Devanagari script
    name_en                  TEXT          NOT NULL,      -- canonical English
    alt_names                TEXT[]        NOT NULL DEFAULT '{}',

    -- Span
    start_longitude          NUMERIC(9,5)  NOT NULL,      -- tropical 0.00–360.00
    end_longitude            NUMERIC(9,5)  NOT NULL,
    span_degrees             NUMERIC(7,5)  NOT NULL DEFAULT 13.33333,
    rashis_spanned           TEXT[]        NOT NULL,
    degree_in_rashi_ranges   JSONB         NOT NULL DEFAULT '[]',

    -- Rulership
    vimshottari_lord         TEXT          NOT NULL,
    presiding_deity          TEXT          NOT NULL,
    secondary_deities        TEXT[]        NOT NULL DEFAULT '{}',
    ruling_planet            TEXT,

    -- Compatibility / nature axes
    gana                     TEXT          NOT NULL,      -- 'Deva' | 'Manushya' | 'Rakshasa'
    nadi                     TEXT,                        -- 'Adi' | 'Madhya' | 'Antya' (NULL for Abhijit)
    yoni_en                  TEXT,                        -- English animal name (NULL for Abhijit)
    yoni_sa                  TEXT,                        -- Sanskrit name (NULL for Abhijit)
    yoni_sex                 CHAR(1),                     -- 'M' | 'F' (NULL for Abhijit)
    varna                    TEXT          NOT NULL,
    tatva                    TEXT          NOT NULL,      -- 'Agni'|'Prithvi'|'Vayu'|'Jala'|'Akasha'
    guna                     TEXT          NOT NULL,
    pakshi                   TEXT,
    nakshatra_gender         TEXT          NOT NULL,

    -- Muhurta classification
    muhurta_type             TEXT          NOT NULL,
    disha                    TEXT,
    favorable_acts           TEXT[]        NOT NULL DEFAULT '{}',
    prohibited_acts          TEXT[]        NOT NULL DEFAULT '{}',

    -- Symbolism + theology
    symbol                   TEXT,
    shakti                   TEXT,
    basis_above              TEXT,
    basis_below              TEXT,
    net_result               TEXT,
    motivation               TEXT          NOT NULL,      -- 'dharma'|'artha'|'kama'|'moksha'
    body_part                TEXT,

    -- Longevity / maturity
    paramayus                TEXT,
    naisargika_maturity_age  SMALLINT,
    deity_domain             TEXT,

    -- Group membership flags
    is_gandanta              BOOLEAN       NOT NULL DEFAULT FALSE,
    is_mula_sangya           BOOLEAN       NOT NULL DEFAULT FALSE,
    is_panchaka              BOOLEAN       NOT NULL DEFAULT FALSE,
    is_abhijit               BOOLEAN       NOT NULL DEFAULT FALSE,

    -- Provenance
    tradition_scope          TEXT          NOT NULL DEFAULT 'classical',
    classical_source         TEXT          NOT NULL,
    build_id                 TEXT,
    created_at               TIMESTAMPTZ   NOT NULL DEFAULT now()
);

COMMENT ON TABLE reference_nakshatra IS
    'bg_nakshatra grain 1: per-nakshatra enriched attributes (27 + Abhijit). '
    'Authority for static nakshatra data; ga_nakshatra references, never restates. '
    'Supersedes the thin reference_nakshatras table from bg_reference.';

-- ── GRAIN 2: per-pada (108) ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS reference_nakshatra_pada (
    pada_id              SMALLINT      PRIMARY KEY,   -- 1-108 global sequence
    nakshatra_id         SMALLINT      NOT NULL REFERENCES reference_nakshatra(nakshatra_id),
    pada_number          SMALLINT      NOT NULL,      -- 1-4 within nakshatra
    absolute_pada        SMALLINT      NOT NULL,

    -- Span
    start_longitude      NUMERIC(9,5)  NOT NULL,
    end_longitude        NUMERIC(9,5)  NOT NULL,

    -- Navamsa cross-map
    pada_navamsa_sign    TEXT          NOT NULL,
    pada_lord            TEXT          NOT NULL,

    -- Sound / akshara
    pada_akshara         TEXT          NOT NULL,
    bija_sound           TEXT,
    mantra_prefix        TEXT,

    -- Interpretation seeds
    pada_deity_nuance    TEXT,
    element_shading      TEXT,
    dosha_shading        TEXT,

    -- Provenance
    tradition_scope      TEXT          NOT NULL DEFAULT 'classical',
    classical_source     TEXT          NOT NULL,
    build_id             TEXT,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),

    UNIQUE (nakshatra_id, pada_number)
);

COMMENT ON TABLE reference_nakshatra_pada IS
    'bg_nakshatra grain 2: per-pada (108) attributes including navamsa cross-map and aksharas.';

-- ── GRAIN 3: relational matrices ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS reference_nakshatra_matrix (
    id               SERIAL        PRIMARY KEY,
    matrix_type      TEXT          NOT NULL,
    from_key         TEXT          NOT NULL,
    to_key           TEXT          NOT NULL,
    relation_value   TEXT          NOT NULL,
    guna_points      NUMERIC(4,2),
    max_points       NUMERIC(4,2),
    notes            TEXT,

    tradition_scope  TEXT          NOT NULL DEFAULT 'classical',
    classical_source TEXT          NOT NULL,
    build_id         TEXT,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT now(),

    UNIQUE (matrix_type, from_key, to_key)
);

COMMENT ON TABLE reference_nakshatra_matrix IS
    'bg_nakshatra grain 3: all relational matrices — 8 Ashtakuta kuta tables '
    '+ rajju/vedha/mahendra/stree_deergha/vashya timing substrate.';

-- ── Indexes ───────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_ref_nak_gana     ON reference_nakshatra (gana);
CREATE INDEX IF NOT EXISTS idx_ref_nak_nadi     ON reference_nakshatra (nadi);
CREATE INDEX IF NOT EXISTS idx_ref_nak_lord     ON reference_nakshatra (vimshottari_lord);
CREATE INDEX IF NOT EXISTS idx_ref_nak_pada_nak ON reference_nakshatra_pada (nakshatra_id);
CREATE INDEX IF NOT EXISTS idx_ref_nak_mat_type ON reference_nakshatra_matrix (matrix_type);

COMMIT;

-- L0 Phase α: 10 new reference_* tables per design §3.2
-- (L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md v1.1)
BEGIN;

CREATE TABLE IF NOT EXISTS reference_houses (
  house_num                  INT PRIMARY KEY CHECK (house_num >= 1 AND house_num <= 12),
  name_sa                    TEXT NOT NULL,
  name_en                    TEXT NOT NULL,
  category                   TEXT NOT NULL CHECK (category IN ('kendra','panapara','apoklima','dusthana','upachaya','trika','trikona')),
  natural_significations     JSONB NOT NULL,
  karakas                    JSONB NOT NULL,
  classical_doctrine_jsonb   JSONB NOT NULL,
  source_citation            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reference_strength_systems (
  strength_id              TEXT PRIMARY KEY,
  name_sa                  TEXT NOT NULL,
  name_en                  TEXT NOT NULL,
  category                 TEXT NOT NULL CHECK (category IN ('shadbala','ashtakavarga','bhava_bala','other')),
  formula_text             TEXT NOT NULL,
  max_value                NUMERIC,
  units                    TEXT,
  classical_interpretation TEXT,
  source_citation          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reference_karakas (
  karaka_id                  TEXT PRIMARY KEY,
  name_sa                    TEXT NOT NULL,
  name_en                    TEXT NOT NULL,
  karaka_type                TEXT NOT NULL CHECK (karaka_type IN ('sthira_planet','sthira_house','chara_jaimini')),
  applies_to                 TEXT,
  classical_significations   JSONB NOT NULL,
  source_citation            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reference_upagrahas (
  upagraha_id         TEXT PRIMARY KEY,
  name_sa             TEXT NOT NULL,
  name_en             TEXT NOT NULL,
  parent_planet       TEXT,
  computation_method  TEXT NOT NULL,
  significations      JSONB NOT NULL,
  source_citation     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reference_constants (
  constant_id         TEXT PRIMARY KEY,
  name                TEXT NOT NULL,
  value_numeric       NUMERIC,
  value_text          TEXT,
  unit                TEXT,
  category            TEXT NOT NULL,
  source_citation     TEXT NOT NULL,
  classical_context   TEXT
);

CREATE TABLE IF NOT EXISTS reference_topic_tags (
  canonical_id    TEXT PRIMARY KEY,
  name            TEXT NOT NULL,
  category        TEXT NOT NULL,
  description     TEXT,
  example_chunks  JSONB
);

CREATE TABLE IF NOT EXISTS reference_glossary (
  term_id            TEXT PRIMARY KEY,
  term_sa            TEXT NOT NULL,
  term_en            TEXT,
  definition         TEXT NOT NULL,
  category           TEXT,
  classical_citation TEXT NOT NULL,
  related_concepts   TEXT[]
);

-- Pointer tables (lightweight index into the major content catalogs)
CREATE TABLE IF NOT EXISTS reference_yogas (
  canonical_id TEXT PRIMARY KEY,
  name_en      TEXT NOT NULL,
  category     TEXT NOT NULL,
  CONSTRAINT fk_ref_yoga FOREIGN KEY (canonical_id)
    REFERENCES brahma_yoga_catalog(canonical_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reference_doshas (
  canonical_id TEXT PRIMARY KEY,
  name_en      TEXT NOT NULL,
  category     TEXT NOT NULL,
  CONSTRAINT fk_ref_dosha FOREIGN KEY (canonical_id)
    REFERENCES brahma_dosha_catalog(canonical_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reference_dasha_systems (
  canonical_id TEXT PRIMARY KEY,
  name_en      TEXT NOT NULL,
  school       TEXT NOT NULL,
  CONSTRAINT fk_ref_dasha_sys FOREIGN KEY (canonical_id)
    REFERENCES brahma_dasha_systems(canonical_id) ON DELETE CASCADE
);

COMMIT;

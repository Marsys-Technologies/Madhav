-- ws2_l0_reference.sql
-- BRAHMA WS-2 L0 Brahmagyan: Classical Reference Library tables
--
-- Contract (L0_CONTRACT_REGISTRY_SEED §C 0.2):
--   brahmagyan.reference: fixed classical lookup data — same for every chart
--   All rows carry source_citation; no Python-constant residue
--
-- Volume floor: all tables populated (9 planet rows, 27 nakshatra rows,
--   12 sign rows, 16 varga rows, classical aspect rows)
--
-- Gate: row-count per table >= floor; source_citation non-null; tool smoke
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS reference_vargas CASCADE;
--   DROP TABLE IF EXISTS reference_aspects CASCADE;
--   DROP TABLE IF EXISTS reference_signs CASCADE;
--   DROP TABLE IF EXISTS reference_nakshatras CASCADE;
--   DROP TABLE IF EXISTS reference_planets CASCADE;
-- ─────────────────────────────────────────────────────────────────────────────

-- ── reference_planets ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reference_planets (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  planet_id         TEXT        NOT NULL UNIQUE,  -- 'sun','moon','mars',etc.
  canonical_name_en TEXT        NOT NULL,
  canonical_name_sa TEXT        NOT NULL,
  exaltation_sign   SMALLINT    CHECK (exaltation_sign BETWEEN 1 AND 12),
  exaltation_degree NUMERIC(5,2),
  debilitation_sign SMALLINT    CHECK (debilitation_sign BETWEEN 1 AND 12),
  mooltrikona_sign  SMALLINT    CHECK (mooltrikona_sign BETWEEN 1 AND 12),
  own_signs         SMALLINT[]  NOT NULL DEFAULT '{}',  -- array of sign IDs 1-12
  natural_benefic   BOOLEAN     NOT NULL,
  karak_domains     TEXT[]      NOT NULL DEFAULT '{}',
  dasha_years       NUMERIC(4,1),  -- Vimshottari years (null for non-dasha bodies)
  source_citation   TEXT        NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE reference_planets IS
  'BRAHMA L0 Brahmagyan: classical planetary attributes per BPHS. '
  'Exaltation/debilitation/mooltrikona/own-signs per Parashari tradition. '
  'Gate: BG-0-2. WS-2 depth build.';

-- ── reference_nakshatras ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reference_nakshatras (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  nakshatra_id      SMALLINT    NOT NULL UNIQUE CHECK (nakshatra_id BETWEEN 1 AND 27),
  canonical_name_en TEXT        NOT NULL,
  canonical_name_sa TEXT        NOT NULL,
  lord              TEXT        NOT NULL,   -- ruling planet
  deity             TEXT        NOT NULL,
  nature            TEXT        NOT NULL,   -- 'movable','fixed','dual','fierce','soft'
  guna              TEXT        NOT NULL,   -- 'sattvic','rajasic','tamasic'
  start_degree      NUMERIC(6,3) NOT NULL,  -- sidereal start from 0°Aries
  end_degree        NUMERIC(6,3) NOT NULL,
  pada_lords        TEXT[]      NOT NULL DEFAULT '{}',  -- 4 pada lords
  body_part         TEXT,
  source_citation   TEXT        NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE reference_nakshatras IS
  'BRAHMA L0 Brahmagyan: 27-nakshatra attributes (lord/deity/nature/guna/padas). '
  'Per BPHS + Taittiriya Aranyaka tradition. Gate: BG-0-2. WS-2.';

-- ── reference_signs ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reference_signs (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  sign_id           SMALLINT    NOT NULL UNIQUE CHECK (sign_id BETWEEN 1 AND 12),
  canonical_name_en TEXT        NOT NULL,
  canonical_name_sa TEXT        NOT NULL,
  lord              TEXT        NOT NULL,
  element           TEXT        NOT NULL,   -- 'fire','earth','air','water'
  modality          TEXT        NOT NULL,   -- 'movable','fixed','dual'
  natural_house     SMALLINT    NOT NULL CHECK (natural_house BETWEEN 1 AND 12),
  is_odd            BOOLEAN     NOT NULL,   -- odd=male, even=female
  is_biped          BOOLEAN     NOT NULL,
  significations    TEXT[]      NOT NULL DEFAULT '{}',
  source_citation   TEXT        NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE reference_signs IS
  'BRAHMA L0 Brahmagyan: 12 zodiac sign attributes per BPHS. '
  'Element/modality/lord/significations. Gate: BG-0-2. WS-2.';

-- ── reference_aspects ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reference_aspects (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  planet_id         TEXT        NOT NULL,
  aspect_house      SMALLINT    NOT NULL CHECK (aspect_house BETWEEN 1 AND 12),
  aspect_strength   TEXT        NOT NULL,  -- 'full','three-quarter','half','quarter'
  strength_value    NUMERIC(3,2) NOT NULL, -- 1.0/0.75/0.5/0.25
  is_special        BOOLEAN     NOT NULL DEFAULT FALSE,
  notes             TEXT,
  source_citation   TEXT        NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (planet_id, aspect_house)
);

COMMENT ON TABLE reference_aspects IS
  'BRAHMA L0 Brahmagyan: planetary aspect rules per BPHS (graha drishti). '
  'All planets aspect 7th house fully; Mars/Jupiter/Saturn have special aspects. '
  'Gate: BG-0-2. WS-2.';

-- ── reference_vargas ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reference_vargas (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  varga_id          TEXT        NOT NULL UNIQUE,  -- 'D1','D2','D3'...
  varga_number      SMALLINT    NOT NULL,
  canonical_name_en TEXT        NOT NULL,
  canonical_name_sa TEXT        NOT NULL,
  division_count    SMALLINT    NOT NULL,  -- how many parts each sign divides into
  primary_signification TEXT    NOT NULL,
  secondary_signification TEXT,
  source_citation   TEXT        NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE reference_vargas IS
  'BRAHMA L0 Brahmagyan: 16 shodasha varga divisional chart definitions per BPHS. '
  'D1 through D60 with significations. Gate: BG-0-2. WS-2.';

-- ── indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_ref_planets_planet_id
  ON reference_planets (planet_id);

CREATE INDEX IF NOT EXISTS idx_ref_nakshatras_nakshatra_id
  ON reference_nakshatras (nakshatra_id);

CREATE INDEX IF NOT EXISTS idx_ref_signs_sign_id
  ON reference_signs (sign_id);

CREATE INDEX IF NOT EXISTS idx_ref_aspects_planet
  ON reference_aspects (planet_id);

CREATE INDEX IF NOT EXISTS idx_ref_vargas_varga_id
  ON reference_vargas (varga_id);

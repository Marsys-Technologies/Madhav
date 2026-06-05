-- ws2_l0_remedy_corpus.sql
-- BRAHMA WS-2 L0 Brahmagyan: Classical remedy (upaya) corpus
--
-- Contract (L0_CONTRACT_REGISTRY_SEED §C 0.7):
--   brahmagyan.remedy_corpus: classical upaya prescriptions from BPHS/Phala Deepika
--   Each row: planet + domain + remedy_type + prescription + source_citation
--   All rows carry source_citation; no LLM generation
--
-- Volume floor: >= 50 classical upaya rows
-- Gate: COUNT(*) >= 50; all rows have source_citation; Saturn career query returns >= 1 row
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS brahma_remedy_corpus CASCADE;
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS brahma_remedy_corpus (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  remedy_id        TEXT        NOT NULL UNIQUE,   -- stable slug, e.g. 'sat_career_mantra_01'
  planet           TEXT        NOT NULL,           -- 'Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'
  domain           TEXT        NOT NULL,           -- 'career','health','marriage','wealth','education','spirituality','general'
  remedy_type      TEXT        NOT NULL,           -- 'mantra','gemstone','charity','ritual','dietary','yantra','fasting'
  prescription_text TEXT       NOT NULL,           -- full classical prescription text
  mantra_text      TEXT,                           -- specific mantra if remedy_type=mantra
  gemstone         TEXT,                           -- gemstone name if remedy_type=gemstone
  charity_action   TEXT,                           -- charity action if remedy_type=charity
  day_of_week      TEXT,                           -- auspicious day for the remedy (optional)
  color_associated TEXT,                           -- associated color (optional)
  confidence       NUMERIC(3,2) NOT NULL DEFAULT 0.85 CHECK (confidence BETWEEN 0 AND 1),
  source_canonical_id TEXT NOT NULL,              -- 'BPHS', 'Phaladeepika', 'Tajaka'
  source_citation  TEXT        NOT NULL,           -- full citation string
  classical_ref    TEXT,                           -- e.g. 'BPHS Ch.88 V.12'
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE brahma_remedy_corpus IS
  'BRAHMA L0 Brahmagyan: classical upaya (remedy) prescriptions from BPHS, Phala Deepika, '
  'and Tajaka Neelakanthi. Sourced from public-domain translations. '
  'Volume floor: >= 50 rows. Gate: BG-0-9. WS-2 depth build.';

CREATE INDEX IF NOT EXISTS idx_remedy_planet ON brahma_remedy_corpus (planet);
CREATE INDEX IF NOT EXISTS idx_remedy_domain ON brahma_remedy_corpus (domain);
CREATE INDEX IF NOT EXISTS idx_remedy_type ON brahma_remedy_corpus (remedy_type);
CREATE INDEX IF NOT EXISTS idx_remedy_planet_domain ON brahma_remedy_corpus (planet, domain);
CREATE INDEX IF NOT EXISTS idx_remedy_source ON brahma_remedy_corpus (source_canonical_id);

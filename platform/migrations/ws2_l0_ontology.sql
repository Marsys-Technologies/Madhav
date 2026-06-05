-- ws2_l0_ontology.sql
-- BRAHMA WS-2 L0 Brahmagyan: Ontology / Controlled Vocabulary
--
-- Contract (L0_CONTRACT_REGISTRY_SEED §C 0.5):
--   brahmagyan.ontology: controlled vocabulary (canonical entities + stable IDs + synonyms)
--   resolves terms across languages; entity_class grouping
--
-- Volume floor: >= 100 entities across all classes
-- Gate: resolve('Shani') → Saturn canonical form; 27 nakshatras resolve
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS brahma_ontology CASCADE;
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS brahma_ontology (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_class      TEXT        NOT NULL,   -- 'planet','nakshatra','sign','house','dasha_system','domain','concept'
  canonical_id      TEXT        NOT NULL,   -- stable slug, e.g. 'saturn','purva_bhadrapada'
  canonical_name_en TEXT        NOT NULL,
  canonical_name_sa TEXT,
  synonyms          TEXT[]      NOT NULL DEFAULT '{}',  -- all aliases (English + transliterated Sanskrit)
  description       TEXT,
  source_citation   TEXT        NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT brahma_ontology_canonical_unique UNIQUE (entity_class, canonical_id)
);

CREATE INDEX IF NOT EXISTS idx_brahma_ontology_class
  ON brahma_ontology (entity_class);

CREATE INDEX IF NOT EXISTS idx_brahma_ontology_canonical
  ON brahma_ontology (canonical_id);

-- GIN index for synonym array search
CREATE INDEX IF NOT EXISTS idx_brahma_ontology_synonyms
  ON brahma_ontology USING gin (synonyms);

COMMENT ON TABLE brahma_ontology IS
  'BRAHMA L0 Brahmagyan: controlled vocabulary for classical Jyotish entities. '
  'Canonical IDs (slugs) + multi-language synonyms for term resolution across '
  'classical texts, analysis outputs, and UI surfaces. '
  'Gate: BG-0-5. WS-2 depth build.';

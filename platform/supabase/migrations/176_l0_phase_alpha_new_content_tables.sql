-- L0 Phase α: 4 new content tables for bg_yogas, bg_dasha_systems, bg_doshas, bg_compendium_index
-- Per design §3.9, §3.10, §3.11, §3.12 (L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md)
-- v1.1: deterministic-only — no LLM provenance columns (no derived_by, no llm_prompt_hash)
BEGIN;

-- §3.9 — Yoga catalog
CREATE TABLE IF NOT EXISTS brahma_yoga_catalog (
  canonical_id            TEXT PRIMARY KEY,
  name_sa                 TEXT NOT NULL,
  name_en                 TEXT NOT NULL,
  category                TEXT NOT NULL CHECK (category IN ('raja','dhana','pancha_mahapurusha','aristha','sannyasa','other')),
  formation_rule_jsonb    JSONB NOT NULL,
  formation_text          TEXT NOT NULL,
  significations_jsonb    JSONB NOT NULL DEFAULT '{}'::jsonb,
  significations_text     TEXT NOT NULL,
  cancellation_conditions JSONB,
  classical_citations     JSONB,
  source_chunk_ids        BIGINT[] DEFAULT ARRAY[]::BIGINT[],
  school                  TEXT NOT NULL,
  rare                    BOOLEAN NOT NULL DEFAULT false,
  computed_strength_formula TEXT,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_yoga_category ON brahma_yoga_catalog(category);
CREATE INDEX IF NOT EXISTS idx_yoga_school   ON brahma_yoga_catalog(school);
CREATE INDEX IF NOT EXISTS idx_yoga_formation ON brahma_yoga_catalog USING gin(formation_rule_jsonb);
COMMENT ON TABLE brahma_yoga_catalog IS
  'L0 bg_yogas — classical yoga definitions per design §3.9 (deterministic-only; no LLM provenance columns per v1.1)';

-- §3.10 — Dasha systems
CREATE TABLE IF NOT EXISTS brahma_dasha_systems (
  canonical_id          TEXT PRIMARY KEY,
  name_sa               TEXT NOT NULL,
  name_en               TEXT NOT NULL,
  total_cycle_years     NUMERIC NOT NULL,
  base_unit             TEXT NOT NULL CHECK (base_unit IN ('nakshatra_lord','sign_lord','special')),
  sequence_jsonb        JSONB NOT NULL,
  computation_method    TEXT NOT NULL,
  computation_pseudocode TEXT NOT NULL,
  conditions_for_use    TEXT,
  school                TEXT NOT NULL,
  classical_citations   JSONB,
  source_chunk_ids      BIGINT[] DEFAULT ARRAY[]::BIGINT[],
  python_impl_module    TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_dasha_school ON brahma_dasha_systems(school);
COMMENT ON TABLE brahma_dasha_systems IS
  'L0 bg_dasha_systems — classical dasha system definitions per design §3.10 (deterministic-only)';

-- §3.11 — Dosha catalog
CREATE TABLE IF NOT EXISTS brahma_dosha_catalog (
  canonical_id            TEXT PRIMARY KEY,
  name_sa                 TEXT NOT NULL,
  name_en                 TEXT NOT NULL,
  category                TEXT NOT NULL CHECK (category IN ('graha_placement','rashi_combination','nakshatra_compatibility','tithi','other')),
  formation_rule_jsonb    JSONB NOT NULL,
  formation_text          TEXT NOT NULL,
  effects_text            TEXT NOT NULL,
  severity_grades         JSONB,
  cancellation_conditions JSONB,
  classical_citations     JSONB,
  source_chunk_ids        BIGINT[] DEFAULT ARRAY[]::BIGINT[],
  associated_remedies     UUID[] DEFAULT ARRAY[]::UUID[],
  school                  TEXT NOT NULL,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_dosha_category ON brahma_dosha_catalog(category);
CREATE INDEX IF NOT EXISTS idx_dosha_school   ON brahma_dosha_catalog(school);
COMMENT ON TABLE brahma_dosha_catalog IS
  'L0 bg_doshas — classical dosha definitions per design §3.11 (deterministic-only)';

-- §3.12 — Compendium index
CREATE TABLE IF NOT EXISTS brahma_compendium_index (
  index_id                      BIGSERIAL PRIMARY KEY,
  text_id                       TEXT NOT NULL,
  chapter_num                   INT,
  chapter_title_en              TEXT,
  chapter_title_sa              TEXT,
  topic_id                      TEXT,
  verse_start                   INT,
  verse_end                     INT,
  chunk_ids                     BIGINT[] DEFAULT ARRAY[]::BIGINT[],
  summary_text                  TEXT,  -- mechanical first-N-chunks synopsis (deterministic; not LLM-generated)
  significance                  TEXT,
  classical_significance_score  NUMERIC(4,3),
  created_at                    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_compendium_text    ON brahma_compendium_index(text_id);
CREATE INDEX IF NOT EXISTS idx_compendium_topic   ON brahma_compendium_index(topic_id);
CREATE INDEX IF NOT EXISTS idx_compendium_chapter ON brahma_compendium_index(text_id, chapter_num);
COMMENT ON TABLE brahma_compendium_index IS
  'L0 bg_compendium_index — cross-reference index per design §3.12 (deterministic-only; summary_text is mechanical first-N-chunks synopsis, not LLM-generated)';

COMMIT;

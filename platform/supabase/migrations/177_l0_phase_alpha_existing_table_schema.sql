-- L0 Phase α: schema changes to existing tables per design §3.3, §3.6, §3.7, §3.8
-- (L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md v1.1 — deterministic-only)
BEGIN;

-- §3.3 — Add topic_tag to classical_text_chunks (for bg_text_index new metric)
-- topic_tag is set by deterministic Python keyword-rule classifier; NOT by LLM
ALTER TABLE classical_text_chunks ADD COLUMN IF NOT EXISTS topic_tag TEXT;
CREATE INDEX IF NOT EXISTS idx_text_chunks_topic_tag ON classical_text_chunks(topic_tag);

-- §3.6 — Add columns to sutravali_rules (quality scoring + cross-refs)
ALTER TABLE sutravali_rules ADD COLUMN IF NOT EXISTS quality_score NUMERIC(4,3);
ALTER TABLE sutravali_rules ADD COLUMN IF NOT EXISTS yoga_canonical_id TEXT;
ALTER TABLE sutravali_rules ADD COLUMN IF NOT EXISTS dasha_system_id TEXT;
ALTER TABLE sutravali_rules ADD COLUMN IF NOT EXISTS transit_marker BOOLEAN;
-- extracted_by already exists; values remain 'python_regex_v1' style (no llm_*)

-- §3.7 — Add scaffold_status to brahma_remedy_corpus
-- classical_attestation_text already present (not added again)
ALTER TABLE brahma_remedy_corpus ADD COLUMN IF NOT EXISTS scaffold_status TEXT
  DEFAULT 'live' CHECK (scaffold_status IN ('live','review','rejected'));
-- No llm_prompt_hash; remedies are 100% native-authored YAML (Python loader; no LLM)

-- §3.8 — classical_attributions reshaped to chunk-pointer-index per v1.1 refinement
-- The existing table stores MSR signal→chunk attributions (different semantics).
-- Drop and rebuild with the new bg_concordance chunk-pointer-index model.
-- Per design v1.1 §2.5: store WHICH chunks; SYNTHESIS happens at L1+ query-time.
DROP TABLE IF EXISTS classical_attributions;
CREATE TABLE classical_attributions (
  attribution_id        BIGSERIAL PRIMARY KEY,
  topic_id              TEXT NOT NULL,           -- e.g. 'saturn_7th_marriage'
  topic_canonical_name  TEXT NOT NULL,           -- 'Effect of Saturn in 7th house on marriage'
  topic_category        TEXT NOT NULL,           -- 'house_placement' | 'yoga' | 'dosha' | 'remedy' | 'dasha' | 'transit'
  school                TEXT NOT NULL,           -- 'parashari' | 'jaimini' | 'kp' | 'tajaka' | 'lal-kitab' | 'phaladeepika'
  source_text_ids       TEXT[] DEFAULT ARRAY[]::TEXT[],
  source_chunk_ids      BIGINT[] NOT NULL DEFAULT ARRAY[]::BIGINT[],
  rule_ids              UUID[] DEFAULT ARRAY[]::UUID[],
  match_method          TEXT NOT NULL,           -- 'keyword' | 'topic_tag' | 'manual' | 'cross_ref'
  match_confidence      NUMERIC(4,3),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_topic_school UNIQUE (topic_id, school)
);
CREATE INDEX IF NOT EXISTS idx_concordance_topic    ON classical_attributions(topic_id);
CREATE INDEX IF NOT EXISTS idx_concordance_school   ON classical_attributions(school);
CREATE INDEX IF NOT EXISTS idx_concordance_category ON classical_attributions(topic_category);
COMMENT ON TABLE classical_attributions IS
  'L0 bg_concordance — chunk-pointer index per (topic, school). '
  'Stores WHICH chunks contain each school''s discussion of each topic; '
  'SYNTHESIS of stance happens at L1+ query-time per design v1.1 §2.5 refinement.';

COMMIT;

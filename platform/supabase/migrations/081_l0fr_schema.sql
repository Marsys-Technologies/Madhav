-- Migration 081: L0FR Schema
-- L0 Foundation Rebuild — new tables for classical text pipeline,
-- sūtravali extraction, panchanga cache, and remedy corpus enrichment
-- Applied by: Stream A conductor 2026-06-07

BEGIN;

-- ----------------------------------------------------------------
-- 1. sutravali_rules — extracted Jyotish rules from classical texts
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sutravali_rules (
  rule_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  text_id              text NOT NULL,
  verse_ref            text NOT NULL,
  antecedent_jsonb     jsonb NOT NULL DEFAULT '[]'::jsonb,
  predicate_jsonb      jsonb NOT NULL DEFAULT '{}'::jsonb,
  prediction_jsonb     jsonb NOT NULL DEFAULT '{}'::jsonb,
  confidence           numeric(4,3) NOT NULL DEFAULT 0.0
                         CHECK (confidence >= 0 AND confidence <= 1),
  extracted_by         text NOT NULL DEFAULT 'stream_d',
  extraction_pass_log  jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sutravali_text_id
  ON sutravali_rules(text_id);
CREATE INDEX IF NOT EXISTS idx_sutravali_verse_ref
  ON sutravali_rules(verse_ref);
CREATE INDEX IF NOT EXISTS idx_sutravali_antecedent
  ON sutravali_rules USING gin(antecedent_jsonb);
CREATE INDEX IF NOT EXISTS idx_sutravali_prediction
  ON sutravali_rules USING gin(prediction_jsonb);

-- ----------------------------------------------------------------
-- 2. sutravali_review — review queue for low-confidence rules
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sutravali_review (
  rule_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  text_id              text NOT NULL,
  verse_ref            text NOT NULL,
  antecedent_jsonb     jsonb NOT NULL DEFAULT '[]'::jsonb,
  predicate_jsonb      jsonb NOT NULL DEFAULT '{}'::jsonb,
  prediction_jsonb     jsonb NOT NULL DEFAULT '{}'::jsonb,
  confidence           numeric(4,3) NOT NULL DEFAULT 0.0
                         CHECK (confidence >= 0 AND confidence <= 1),
  extracted_by         text NOT NULL DEFAULT 'stream_d',
  extraction_pass_log  jsonb NOT NULL DEFAULT '[]'::jsonb,
  rejection_reason     text,
  review_status        text NOT NULL DEFAULT 'pending'
                         CHECK (review_status IN ('pending','approved','rejected')),
  created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sutravali_review_status
  ON sutravali_review(review_status);

-- ----------------------------------------------------------------
-- 3. chart_panchanga_cache — per-chart daily panchanga cache
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chart_panchanga_cache (
  chart_id       uuid NOT NULL,
  date           date NOT NULL,
  tithi          text,
  vara           text,
  nakshatra      text,
  yoga           text,
  karana         text,
  sunrise_utc    timestamptz,
  sunset_utc     timestamptz,
  computed_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, date)
);

CREATE INDEX IF NOT EXISTS idx_chart_panchanga_cache_chart_id
  ON chart_panchanga_cache(chart_id);

-- ----------------------------------------------------------------
-- 4. classical_texts_source — canonical edition registry for 15 texts
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS classical_texts_source (
  text_id            text PRIMARY KEY,
  title              text NOT NULL,
  author             text,
  era                text,
  edition            text,
  translator         text,
  publisher          text,
  year               int,
  sha256             text,
  license            text,
  citation_format    text,
  source_url         text
);

-- ----------------------------------------------------------------
-- 5. ALTER classical_text_chunks — add L0FR columns
-- ----------------------------------------------------------------
ALTER TABLE classical_text_chunks
  ADD COLUMN IF NOT EXISTS translator           text,
  ADD COLUMN IF NOT EXISTS tradition_school     text,
  ADD COLUMN IF NOT EXISTS embedding            vector(768),
  ADD COLUMN IF NOT EXISTS content_sha256       text;

-- HNSW index for vector cosine search (pgvector 0.5+)
CREATE INDEX IF NOT EXISTS idx_classical_text_chunks_embedding
  ON classical_text_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- ----------------------------------------------------------------
-- 6. ALTER brahma_remedy_corpus — add L0FR enrichment columns
-- ----------------------------------------------------------------
ALTER TABLE brahma_remedy_corpus
  ADD COLUMN IF NOT EXISTS category                  text,
  ADD COLUMN IF NOT EXISTS deity                     text,
  ADD COLUMN IF NOT EXISTS mantra_sanskrit           text,
  ADD COLUMN IF NOT EXISTS mantra_transliteration    text,
  ADD COLUMN IF NOT EXISTS ingredients_jsonb         jsonb,
  ADD COLUMN IF NOT EXISTS timing_rules_jsonb        jsonb,
  ADD COLUMN IF NOT EXISTS cost_tier                 text
    CHECK (cost_tier IS NULL OR cost_tier IN ('free','low','medium','high')),
  ADD COLUMN IF NOT EXISTS contraindications         text,
  ADD COLUMN IF NOT EXISTS classical_attestation_text text;

-- ----------------------------------------------------------------
-- 7. remedy_review_queue — review queue for tantric/uncertain remedies
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS remedy_review_queue (
  id                         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  remedy_id                  text NOT NULL,
  planet                     text NOT NULL,
  domain                     text NOT NULL,
  remedy_type                text NOT NULL,
  prescription_text          text NOT NULL,
  mantra_text                text,
  gemstone                   text,
  charity_action             text,
  day_of_week                text,
  color_associated           text,
  confidence                 numeric(3,2) NOT NULL DEFAULT 0.85,
  source_canonical_id        text NOT NULL,
  source_citation            text NOT NULL,
  classical_ref              text,
  category                   text,
  deity                      text,
  mantra_sanskrit            text,
  mantra_transliteration     text,
  ingredients_jsonb          jsonb,
  timing_rules_jsonb         jsonb,
  cost_tier                  text
    CHECK (cost_tier IS NULL OR cost_tier IN ('free','low','medium','high')),
  contraindications          text,
  classical_attestation_text text,
  rejection_reason           text,
  review_status              text NOT NULL DEFAULT 'pending'
    CHECK (review_status IN ('pending','approved','rejected')),
  created_at                 timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_remedy_review_status
  ON remedy_review_queue(review_status);
CREATE INDEX IF NOT EXISTS idx_remedy_review_planet
  ON remedy_review_queue(planet);

COMMIT;

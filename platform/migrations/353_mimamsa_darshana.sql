-- Migration 353: mi_darshana — insight retrieval surface (tables + views + embeddings)
-- Created: 2026-06-26

CREATE EXTENSION IF NOT EXISTS vector;

BEGIN;

CREATE TABLE IF NOT EXISTS mimamsa_insight_units (
  chart_id                uuid        NOT NULL,
  insight_id              text        NOT NULL,
  insight_type            text        NOT NULL,  -- 'calibrated_outlook'|'manifestation_grammar'|'emergent_law'|'load_bearing'|'negative_knowledge'|'contradiction_dominance'|'temporal_rhythm'
  domain                  text,
  horizon                 text,
  question_lens           text,
  statement               text        NOT NULL,
  rank_consequence        numeric     NOT NULL,
  confidence_band         numrange,
  n_support               int         NOT NULL,
  leakage_status          text        NOT NULL,
  evidence_grade          text        NOT NULL,
  freshness_lel_version   text        NOT NULL,
  last_calibrated_at      timestamptz,
  provenance_chain        jsonb       NOT NULL,
  is_negative_knowledge   boolean     NOT NULL,
  surface_formula_version text        NOT NULL,
  updated_at              timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, insight_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_insight_units_chart_id
  ON mimamsa_insight_units (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_insight_units_type
  ON mimamsa_insight_units (chart_id, insight_type);

CREATE INDEX IF NOT EXISTS idx_mimamsa_insight_units_domain
  ON mimamsa_insight_units (chart_id, domain);

CREATE INDEX IF NOT EXISTS idx_mimamsa_insight_units_negative
  ON mimamsa_insight_units (chart_id, is_negative_knowledge);

CREATE TABLE IF NOT EXISTS mimamsa_insight_embeddings (
  chart_id          uuid        NOT NULL,
  insight_id        text        NOT NULL,
  embedding         vector(768) NOT NULL,
  embed_model_version text      NOT NULL,
  embedded_at       timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, insight_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_insight_embeddings_chart_id
  ON mimamsa_insight_embeddings (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_insight_embeddings_vector
  ON mimamsa_insight_embeddings
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE OR REPLACE VIEW vw_mimamsa_insight_by_domain AS
  SELECT * FROM mimamsa_insight_units
  ORDER BY chart_id, domain, rank_consequence DESC;

CREATE OR REPLACE VIEW vw_mimamsa_insight_by_horizon AS
  SELECT * FROM mimamsa_insight_units
  WHERE horizon IS NOT NULL
  ORDER BY chart_id, horizon, rank_consequence DESC;

CREATE OR REPLACE VIEW vw_mimamsa_insight_by_lens AS
  SELECT * FROM mimamsa_insight_units
  WHERE question_lens IS NOT NULL
  ORDER BY chart_id, question_lens, rank_consequence DESC;

CREATE OR REPLACE VIEW vw_mimamsa_negative_knowledge AS
  SELECT * FROM mimamsa_insight_units
  WHERE is_negative_knowledge = true;

COMMIT;

-- Migration 351: mi_pariksha — attribution + QA + discoveries
-- Created: 2026-06-26

BEGIN;

CREATE TABLE IF NOT EXISTS mimamsa_attribution (
  chart_id                uuid    NOT NULL,
  match_id                text    NOT NULL,
  signal_id               text    NOT NULL,
  family_id               text    NOT NULL,
  dimension               text    NOT NULL,  -- 'timing'|'magnitude'|'domain'|'falsifier'|'manifestation'
  credit_blame            numeric NOT NULL,
  channel_fired           text,
  attribution_formula_ver text    NOT NULL,
  PRIMARY KEY (chart_id, match_id, signal_id, dimension)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_attribution_chart_id
  ON mimamsa_attribution (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_attribution_match
  ON mimamsa_attribution (chart_id, match_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_attribution_signal
  ON mimamsa_attribution (chart_id, signal_id);

CREATE TABLE IF NOT EXISTS mimamsa_qa_eval (
  chart_id    uuid        NOT NULL,
  check_id    text        NOT NULL,
  check_type  text        NOT NULL,  -- 'negative_control'|'degenerate_distribution'|'reproducibility'
  target      text        NOT NULL,
  result_score numeric,
  status      text        NOT NULL,  -- 'pass'|'FAIL'
  detail      jsonb,
  checked_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, check_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_qa_eval_chart_id
  ON mimamsa_qa_eval (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_qa_eval_status
  ON mimamsa_qa_eval (chart_id, status);

CREATE TABLE IF NOT EXISTS mimamsa_discoveries (
  chart_id              uuid     NOT NULL,
  discovery_id          text     NOT NULL,
  discovery_class       text     NOT NULL,  -- 'emergent_law'|'contradiction_dominance'|'temporal_rhythm'|'residual_candidate'
  statement             text     NOT NULL,
  evidence_refs         jsonb    NOT NULL,
  strength              numeric,
  n_support             int      NOT NULL,
  confidence_band       numrange,
  activation_status     text     NOT NULL,  -- 'candidate'|'supported'|'promoted'
  citation_required     boolean  NOT NULL,
  citation_ref          jsonb,
  discovery_formula_ver text     NOT NULL,
  PRIMARY KEY (chart_id, discovery_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_discoveries_chart_id
  ON mimamsa_discoveries (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_discoveries_class
  ON mimamsa_discoveries (chart_id, discovery_class);

COMMIT;

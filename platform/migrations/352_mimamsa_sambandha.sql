-- Migration 352: mi_sambandha — manifestation grammar
-- Created: 2026-06-26

BEGIN;

CREATE TABLE IF NOT EXISTS mimamsa_manifestation_grammar (
  chart_id              uuid        NOT NULL,
  origin_kind           text        NOT NULL,
  origin_ref            text        NOT NULL,
  channel_id            text        NOT NULL,
  domain                text        NOT NULL,
  fire_count            int         NOT NULL,
  opportunity_count     int         NOT NULL,
  channel_propensity    numeric,
  prior_propensity      numeric     NOT NULL,
  propensity_delta      numeric,
  n_support             int         NOT NULL,
  confidence_band       numrange,
  evidence_grade        text        NOT NULL,  -- 'empirical'|'prior_only'|'structural'
  citation_ref          jsonb       NOT NULL,
  grammar_formula_version text      NOT NULL,
  updated_at            timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, origin_kind, origin_ref, channel_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_manifestation_grammar_chart_id
  ON mimamsa_manifestation_grammar (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_manifestation_grammar_channel
  ON mimamsa_manifestation_grammar (chart_id, channel_id);

COMMIT;

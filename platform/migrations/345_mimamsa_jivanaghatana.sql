-- Migration 345: mi_jivanaghatana — evidence vault (event provenance)
-- Created: 2026-06-26

BEGIN;

CREATE TABLE IF NOT EXISTS mimamsa_event_provenance (
  chart_id                uuid        NOT NULL,
  event_id                text        NOT NULL,
  shaped_predictor        boolean     NOT NULL,
  shaped_predictor_refs   jsonb,
  disclosure_timing       text        NOT NULL,  -- 'pre_framework' | 'post_framework' | 'post_framework_undated' | 'unknown'
  disclosure_date         date,
  event_date              date        NOT NULL,
  domain_primary          text        NOT NULL,
  domain_secondary        text[],
  event_magnitude         text,                   -- 'minor'|'moderate'|'major'|'rupture'
  held_out                boolean     NOT NULL,
  admissible_clean        boolean     NOT NULL,
  admissibility_reason    text        NOT NULL,
  partition_seed_version  text        NOT NULL,
  lel_version             text        NOT NULL,
  provenance_formula_ver  text        NOT NULL,
  created_at              timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, event_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_event_provenance_chart_id
  ON mimamsa_event_provenance (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_event_provenance_held_out
  ON mimamsa_event_provenance (chart_id, held_out);

CREATE INDEX IF NOT EXISTS idx_mimamsa_event_provenance_admissible
  ON mimamsa_event_provenance (chart_id, admissible_clean);

CREATE OR REPLACE VIEW vw_mimamsa_held_out AS
  SELECT * FROM mimamsa_event_provenance WHERE held_out = true;

CREATE OR REPLACE VIEW vw_mimamsa_admissible_clean AS
  SELECT * FROM mimamsa_event_provenance WHERE admissible_clean = true AND held_out = false;

COMMIT;

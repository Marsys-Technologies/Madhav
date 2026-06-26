-- Migration 350: mi_adhilepa — overlay tables (4 types) + load-bearing table
-- Created: 2026-06-26

BEGIN;

-- Signal overlay (origin: bodha_msr_signals.signal_id)
CREATE TABLE IF NOT EXISTS mimamsa_signal_adjustment (
  chart_id                  uuid        NOT NULL,
  origin_layer              text        NOT NULL,
  origin_asset_id           text        NOT NULL,
  origin_id                 text        NOT NULL,
  weight_id                 text        NOT NULL,
  multiplier                numeric     NOT NULL,
  raw_multiplier            numeric     NOT NULL,
  applied_bound             numeric     NOT NULL,
  evidence_n                int         NOT NULL,
  leakage_status            text        NOT NULL,
  applies_to_reading        boolean     NOT NULL,
  derived_from_pramana_ids  jsonb       NOT NULL,
  overlay_formula_version   text        NOT NULL,
  created_at                timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, origin_id, weight_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_signal_adjustment_chart_id
  ON mimamsa_signal_adjustment (chart_id);

-- Fact overlay (origin: chart_facts.fact_id)
CREATE TABLE IF NOT EXISTS mimamsa_fact_adjustment (
  chart_id                  uuid        NOT NULL,
  origin_layer              text        NOT NULL,
  origin_asset_id           text        NOT NULL,
  origin_id                 text        NOT NULL,
  weight_id                 text        NOT NULL,
  multiplier                numeric     NOT NULL,
  raw_multiplier            numeric     NOT NULL,
  applied_bound             numeric     NOT NULL,
  evidence_n                int         NOT NULL,
  leakage_status            text        NOT NULL,
  applies_to_reading        boolean     NOT NULL,
  derived_from_pramana_ids  jsonb       NOT NULL,
  overlay_formula_version   text        NOT NULL,
  created_at                timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, origin_id, weight_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_fact_adjustment_chart_id
  ON mimamsa_fact_adjustment (chart_id);

-- Convergence overlay (origin: kala_convergence.convergence_id)
CREATE TABLE IF NOT EXISTS mimamsa_convergence_adjustment (
  chart_id                  uuid        NOT NULL,
  origin_layer              text        NOT NULL,
  origin_asset_id           text        NOT NULL,
  origin_id                 text        NOT NULL,
  weight_id                 text        NOT NULL,
  multiplier                numeric     NOT NULL,
  raw_multiplier            numeric     NOT NULL,
  applied_bound             numeric     NOT NULL,
  evidence_n                int         NOT NULL,
  leakage_status            text        NOT NULL,
  applies_to_reading        boolean     NOT NULL,
  derived_from_pramana_ids  jsonb       NOT NULL,
  overlay_formula_version   text        NOT NULL,
  created_at                timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, origin_id, weight_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_convergence_adjustment_chart_id
  ON mimamsa_convergence_adjustment (chart_id);

-- Anchor overlay (origin: phala_anchors.anchor_id)
CREATE TABLE IF NOT EXISTS mimamsa_anchor_adjustment (
  chart_id                  uuid        NOT NULL,
  origin_layer              text        NOT NULL,
  origin_asset_id           text        NOT NULL,
  origin_id                 text        NOT NULL,
  weight_id                 text        NOT NULL,
  multiplier                numeric     NOT NULL,
  raw_multiplier            numeric     NOT NULL,
  applied_bound             numeric     NOT NULL,
  evidence_n                int         NOT NULL,
  leakage_status            text        NOT NULL,
  applies_to_reading        boolean     NOT NULL,
  derived_from_pramana_ids  jsonb       NOT NULL,
  overlay_formula_version   text        NOT NULL,
  created_at                timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, origin_id, weight_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_anchor_adjustment_chart_id
  ON mimamsa_anchor_adjustment (chart_id);

-- Load-bearing conclusions table
CREATE TABLE IF NOT EXISTS mimamsa_load_bearing (
  chart_id        uuid    NOT NULL,
  conclusion_id   text    NOT NULL,
  signal_id       text    NOT NULL,
  sensitivity     numeric NOT NULL,
  role            text    NOT NULL,  -- 'load_bearing'|'supporting'|'redundant'
  formula_version text    NOT NULL,
  PRIMARY KEY (chart_id, conclusion_id, signal_id)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_load_bearing_chart_id
  ON mimamsa_load_bearing (chart_id);

COMMIT;

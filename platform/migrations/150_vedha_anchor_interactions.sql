-- Migration 150: l25_vedha_anchor_interactions — Vedha-Anchor Interaction Table
-- BRIDGE-S1 [BUILD-ORCH-STREAM-D-BRIDGE-S1]
-- Captures resolved interaction when A18 vedha is active during A16 anchor window.
-- Per: TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md §2.B
--
-- PK type notes (confirmed from existing migrations):
--   l1_vedha_extended.vedha_id   : BIGSERIAL (migration 144)
--   l1_phase_locked_anchors.anchor_id : BIGSERIAL (migration 146)

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS l25_vedha_anchor_interactions (
  interaction_id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id                    UUID        NOT NULL,
  ayanamsha_id                TEXT        NOT NULL,
  build_id                    UUID        NOT NULL,

  -- FKs match BIGSERIAL PKs in source tables
  vedha_id                    BIGINT      NOT NULL,   -- references l1_vedha_extended.vedha_id
  anchor_id                   BIGINT,                 -- references l1_phase_locked_anchors.anchor_id

  interaction_class           TEXT        NOT NULL
    CHECK (interaction_class IN (
      'full_mitigation', 'partial_mitigation', 'inversion', 'amplification', 'neutralizing'
    )),
  mitigation_strength         NUMERIC     CHECK (mitigation_strength >= 0 AND mitigation_strength <= 1),
  expected_outcome_modification_class TEXT,
  severity_after_mitigation   NUMERIC     CHECK (severity_after_mitigation >= 0 AND severity_after_mitigation <= 1),
  confidence_after_mitigation NUMERIC     CHECK (confidence_after_mitigation >= 0 AND confidence_after_mitigation <= 1),

  classical_resolution_methodology TEXT,
  classical_citation          TEXT        NOT NULL DEFAULT 'Tajika Neelakanthi',

  verification_pass_status    TEXT        NOT NULL DEFAULT 'unverified',
  citation_ref                TEXT        NOT NULL DEFAULT 'TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md §2.B',
  citation_human              TEXT        NOT NULL DEFAULT 'Vedha-Anchor interaction per Tajika + BPHS vedha rules',
  computed_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS vai_chart_idx  ON l25_vedha_anchor_interactions (chart_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS vai_vedha_idx  ON l25_vedha_anchor_interactions (vedha_id);
CREATE INDEX IF NOT EXISTS vai_anchor_idx ON l25_vedha_anchor_interactions (anchor_id)
  WHERE anchor_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS vai_class_idx  ON l25_vedha_anchor_interactions (interaction_class);

-- Prevent duplicate computation runs for the same vedha+anchor+build combination
CREATE UNIQUE INDEX IF NOT EXISTS vai_unique_idx
  ON l25_vedha_anchor_interactions (vedha_id, anchor_id, build_id)
  WHERE anchor_id IS NOT NULL;

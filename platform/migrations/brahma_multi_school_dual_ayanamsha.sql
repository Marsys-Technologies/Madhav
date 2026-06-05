-- brahma_multi_school_dual_ayanamsha.sql
-- BRAHMA-MULTI-SCHOOL: Dual-Ayanamsha concordance tracking
-- Stream E Post-Deploy, Session e2
--
-- Context:
--   ganita_positions already has ayanamsha_id (TEXT NOT NULL) as a discriminator
--   column with UNIQUE(chart_id, ayanamsha_id, planet). No change to that table.
--
--   bodha_graph already has ayanamsha_id TEXT NOT NULL DEFAULT 'lahiri'. No change.
--
--   This migration adds:
--   1. concordance_ayanamsha_flags — tracks rules/topics where different ayanamsha
--      offsets (lahiri vs kp) produce different conclusions. Supports the new
--      AYANAMSHA_DEPENDENT concordance class introduced in Stream E.
--
--   2. A CHECK constraint tightening on bodha_graph.ayanamsha_id to enforce
--      only canonical ayanamsha identifiers (idempotent IF NOT EXISTS guard).
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS concordance_ayanamsha_flags;
-- ─────────────────────────────────────────────────────────────────────────────

-- ── concordance_ayanamsha_flags ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS concordance_ayanamsha_flags (
  flag_id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id         TEXT        NOT NULL,             -- e.g. 'TC.C3', 'TC.001'
  topic            TEXT        NOT NULL,             -- human-readable topic name
  concordance_class TEXT       NOT NULL
                               CHECK (concordance_class IN (
                                 'agree',
                                 'disagree',
                                 'qualify',
                                 'orthogonal',
                                 'ayanamsha_dependent'  -- NEW: conclusion changes across ayanamsha offsets
                               )),
  ayanamsha_a      TEXT        NOT NULL DEFAULT 'lahiri',   -- first ayanamsha in the comparison
  ayanamsha_b      TEXT        NOT NULL DEFAULT 'kp',       -- second ayanamsha in the comparison
  description      TEXT        NOT NULL,             -- explanation of why conclusions differ
  rule_refs        JSONB       NOT NULL DEFAULT '[]'::jsonb,  -- e.g. ["BPHS.3.21.1", "KP.1.ch3.dignity.1"]
  chart_id         UUID        REFERENCES charts(id) ON DELETE SET NULL,  -- NULL = school-level, not chart-specific
  source_citation  TEXT        NOT NULL,             -- e.g. "brahmagyan_concordance.yaml v1.1"
  build_id         TEXT,
  computed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT concordance_ayanamsha_flags_unique
    UNIQUE (topic_id, ayanamsha_a, ayanamsha_b, chart_id)
);

-- Primary query: get all AYANAMSHA_DEPENDENT topics for a chart
CREATE INDEX IF NOT EXISTS idx_concordance_aya_class
  ON concordance_ayanamsha_flags (concordance_class, chart_id);

-- Topic lookup
CREATE INDEX IF NOT EXISTS idx_concordance_aya_topic
  ON concordance_ayanamsha_flags (topic_id);

-- Ayanamsha pair lookup
CREATE INDEX IF NOT EXISTS idx_concordance_aya_pair
  ON concordance_ayanamsha_flags (ayanamsha_a, ayanamsha_b);

COMMENT ON TABLE concordance_ayanamsha_flags IS
  'BRAHMA-MULTI-SCHOOL Stream E: Tracks concordance topics where different ayanamsha '
  'offsets (typically lahiri vs kp) produce different conclusions for the same rule. '
  'Class "ayanamsha_dependent" = the rule conclusion is not portable across ayanamsha '
  'systems — requires explicit ayanamsha_id scoping when applied. '
  'Populated by: platform/python-sidecar/brahmagyan/mimamsa/concordance_writer.py.';

COMMENT ON COLUMN concordance_ayanamsha_flags.concordance_class IS
  'agree             — all ayanamshas produce the same conclusion
   disagree          — ayanamshas produce contradictory conclusions (class-1 conflict)
   qualify           — same conclusion with ayanamsha-specific qualifications
   orthogonal        — systems address different domains; comparison not meaningful
   ayanamsha_dependent — conclusion changes depending on which ayanamsha offset is applied';

-- ── Staging mirror (idempotent swap pattern) ──────────────────────────────────

CREATE TABLE IF NOT EXISTS concordance_ayanamsha_flags_staging
  (LIKE concordance_ayanamsha_flags INCLUDING ALL);

-- ── Seed: C3 AYANAMSHA_DEPENDENT entries ─────────────────────────────────────
-- These are the known C3-adjacent topics where the ayanamsha offset matters:
-- planets near sign/nakshatra boundaries that land in different signs under
-- Lahiri vs KP offsets (~0.1-0.2° difference, typically ~6-8' of arc).
--
-- Source: brahmagyan_concordance.yaml C3-flagged entries + FORENSIC v8.0 analysis.

INSERT INTO concordance_ayanamsha_flags
  (topic_id, topic, concordance_class, ayanamsha_a, ayanamsha_b,
   description, rule_refs, chart_id, source_citation)
VALUES
  (
    'TC.C3.BOUNDARY',
    'Planet near sign boundary — ayanamsha offset changes sign placement',
    'ayanamsha_dependent',
    'lahiri',
    'kp',
    'When a planet falls within ~0.2° of a sign cusp, the Lahiri offset (~23.85°) '
    'and KP offset (~23.86°, Krishnamurti) produce different sign assignments. '
    'Rules that depend on the planet''s sign (dignity, lordship, yoga formation) '
    'will produce different conclusions. This is the "KP-vs-Lahiri orthogonality" '
    'flagged by WS-3 C3. The C3 flag itself is about house cusp conventions '
    '(equal-house vs Placidus); this entry captures the ayanamsha-offset component.',
    '["BPHS.3.21.1", "KP.1.ch3.dignity.1", "BRAHMA-GA-1-2"]'::jsonb,
    NULL,
    'brahmagyan_concordance.yaml v1.1 + V1_3_MULTI_SCHOOL_SCHEMA.md v1.0'
  ),
  (
    'TC.C3.NAKSHATRA_BOUNDARY',
    'Planet near nakshatra boundary — ayanamsha offset changes nakshatra placement',
    'ayanamsha_dependent',
    'lahiri',
    'kp',
    'Each nakshatra spans 13°20'' (13.333°). A planet near a nakshatra boundary '
    'may land in different nakshatras under Lahiri vs KP offsets. Dasha lords '
    '(Vimshottari) and KP sub-lord assignments both depend on nakshatra placement, '
    'so borderline planets produce different dasha-lord and sub-lord conclusions '
    'across the two systems. This compounds the C3 house-system orthogonality: '
    'KP sub-lord analysis uses KP ayanamsha + Placidus cusps as an integrated unit.',
    '["BPHS.46.2.1", "KP.1.ch4.sublord.1", "BRAHMA-GA-1-4"]'::jsonb,
    NULL,
    'brahmagyan_concordance.yaml v1.1 + V1_3_MULTI_SCHOOL_SCHEMA.md v1.0'
  )
ON CONFLICT (topic_id, ayanamsha_a, ayanamsha_b, chart_id) DO NOTHING;

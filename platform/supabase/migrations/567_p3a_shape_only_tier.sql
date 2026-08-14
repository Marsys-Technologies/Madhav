-- migration 567: P3-a shape_only tier infrastructure
-- (DHARA_ENGINE_SPEC_v1_0.md §4, SM-R-10)
--
-- Two additive changes:
--
-- 1. kala_field_windows.baseline_is_synthetic (BOOLEAN, default FALSE)
--    The §N.8 earned-signal tag for shape_only rows. Every row the writer
--    produces for a shape_only class carries TRUE here; calibrated rows carry
--    FALSE (the column default). Consumers use this to SUPPRESS or RELABEL
--    absolute-count fields (P3-b census — see PR description).
--
-- 2. ka_kshetra_tier_basis
--    The P3-d tier-basis table: 27 rows (one per event class) mapping each
--    class to 'calibrated', 'shape_only', or 'not_applicable'.
--    Populated by the conductor/PRATINIDHI as a committed deliverable BEFORE
--    any shape_only row is written (§N.8 — the tier decision must be an earned
--    classification, not inferred at build time).
--
-- Both changes are ADDITIVE and backwards-compatible:
--   • Existing kala_field_windows rows get baseline_is_synthetic = FALSE
--     (correct: they were built on calibrated priors).
--   • ka_kshetra_tier_basis starts empty; the writer's _is_shape_only_class()
--     falls back to the calibrated path (ClassSkipped) until it is populated.
--
-- Rollback (non-destructive):
--   ALTER TABLE kala_field_windows DROP COLUMN IF EXISTS baseline_is_synthetic;
--   DROP TABLE IF EXISTS ka_kshetra_tier_basis;

-- ── 1. kala_field_windows.baseline_is_synthetic ───────────────────────────────

ALTER TABLE kala_field_windows
  ADD COLUMN IF NOT EXISTS baseline_is_synthetic BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN kala_field_windows.baseline_is_synthetic IS
  'P3-a (DHARA_ENGINE_SPEC_v1_0.md §4.1): TRUE when the baseline λ⁰_e for this '
  'window was constructed from SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT (1.0) rather '
  'than a calibrated bg_class_priors row. Consumers MUST suppress or relabel '
  'absolute-count fields (expected_count, kala_field_null.max_stats / q_threshold) '
  'when this is TRUE — see P3-b census in DHARA_ENGINE_SPEC_v1_0.md §4.2. '
  'FALSE = calibrated path; the column default guarantees backwards compatibility '
  'for rows written before this migration.';

-- ── 2. ka_kshetra_tier_basis ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ka_kshetra_tier_basis (
  event_class   TEXT        PRIMARY KEY,
  tier          TEXT        NOT NULL,
  rationale     TEXT,
  ratified_at   TIMESTAMPTZ,
  ratified_by   TEXT,         -- 'PRATINIDHI' once ratified; NULL while draft
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT ka_kshetra_tier_basis_tier_ck
    CHECK (tier IN ('calibrated', 'shape_only', 'not_applicable'))
);

COMMENT ON TABLE ka_kshetra_tier_basis IS
  'P3-d (DHARA_ENGINE_SPEC_v1_0.md §4.3): the 27-row tier-basis table, one row per '
  'event class. Drafted by the SAMPŪRTI-Δ1 conductor and ratified by PRATINIDHI with '
  'written rationale before any shape_only row is written (§N.8 earned-signal '
  'discipline). The writer (_is_shape_only_class in writer.py) queries this table at '
  'build time; until it is populated the calibrated path (ClassSkipped for no-prior '
  'classes) is unchanged.';

COMMENT ON COLUMN ka_kshetra_tier_basis.tier IS
  'calibrated = has a calibrated bg_class_priors row (ne_v01); '
  'shape_only = no calibrated prior; shape (relative timing) is informative but '
  'absolute counts (expected_count, null_p) are not comparable across classes; '
  'not_applicable = ADJUDICATION-2 Tier N-iii; class structurally excluded.';

-- ── 3. P3-d tier-basis data (27 rows) ────────────────────────────────────────
-- Drafted by SAMPŪRTI-Δ1 conductor; ratified by PRATINIDHI (opus agent
-- a3448a407e9a66ba3) 2026-08-14. RATIFICATION COMPLETE — 0 overrides.
-- Source: DHARA_ENGINE_SPEC_v1_0.md §4.3 + l0_class_lifetime_counts.py (ne_v01
-- rows confirm the 6 calibrated classes).

INSERT INTO ka_kshetra_tier_basis
  (event_class, tier, rationale, ratified_at, ratified_by)
VALUES
  ('marriage',              'calibrated',    'ne_v01 row seeded from India NHFS-5 ever-married lifetime prevalence.',                                                                      '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('separation',            'calibrated',    'ne_v01 row seeded from India NHFS-5 divorce/separation lifetime prevalence.',                                                               '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('childbirth',            'calibrated',    'ne_v01 row seeded from India NHFS-5 total fertility rate.',                                                                                 '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('relocation',            'calibrated',    'ne_v01 row seeded from NSSO 64th round interstate migration prevalence.',                                                                   '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('foreign_settlement',    'calibrated',    'ne_v01 row seeded from MOSPI emigration rate for India.',                                                                                   '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('surgery',               'calibrated',    'ne_v01 row seeded from India population-level surgical prevalence.',                                                                        '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('career_entry',          'shape_only',    'No clean per-lifetime count of career entries in Indian employment surveys; labor force participation rates do not decompose into discrete entry events.', '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('career_advancement',    'shape_only',    'Promotion frequency is sector-dependent and not captured at population level in any Indian demographic dataset.',                            '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('career_setback',        'shape_only',    'Unemployment duration data exists but does not map to the magnitude-floored significant setback definition.',                               '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('business_launch',       'shape_only',    'NSSO self-employment prevalence counts persons, not launches per lifetime; no per-capita count derivable at Tier N-i precision.',           '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('education_milestone',   'shape_only',    'Completion rates exist per level but the chain-shape class definition requires further adjudication to produce a defensible N_e.',          '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('exam_outcome',          'shape_only',    'Exam-taking frequency varies by education level and career path; no single Indian demographic source gives a defensible per-lifetime count.','2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('romantic_start',        'shape_only',    'Premarital relationship survey data for India (1984 birth cohort) is too sparse and culturally variable for a Tier N-i baseline.',          '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('parental_event',        'shape_only',    'Bundles parent illness, surgery, and emotional milestones — no single demographic metric maps to this composite.',                          '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('bereavement',           'shape_only',    'Indian life tables give parental mortality distributions, but the class covers close family beyond parents; class definition is broader than any single Tier N-i source.', '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('major_gain',            'shape_only',    'Inherently magnitude-floor-dependent; no demographic source for significant financial gain events per lifetime.',                            '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('major_loss',            'shape_only',    'Same reasoning as major_gain; no Tier N-i source for magnitude-floored financial loss events.',                                             '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('property_acquisition',  'shape_only',    'NSS homeownership rates give prevalence but not a per-lifetime acquisition count respecting the magnitude floor; not cleanly promotable without further adjudication.', '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('illness_acute',         'shape_only',    'NSSO morbidity data gives hospitalization rates but the magnitude floor makes N_e conversion uncertain.',                                   '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('chronic_onset',         'shape_only',    'Chronic disease prevalence data maps to point prevalence, not per-lifetime onset count with the class persistence criteria.',               '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('spiritual_turn',        'shape_only',    'No demographic data exists for significant spiritual life change at population level.',                                                     '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('achievement_recognition','shape_only',   'No population-level awards/recognition frequency data exists for India.',                                                                   '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('financial_deception',   'shape_only',    'NCRB fraud victimization rates exist but do not cleanly match the class magnitude floor or demographic profile.',                           '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('psychological_arc',     'shape_only',    'NMHS prevalence data exists but psychological_arc onset-persistence-resolution criteria do not map to a simple prevalence-to-N_e conversion.', '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('travel_event',          'shape_only',    'Trivial magnitude designation and adjacency-only ontological role; travel frequency data is sparse; shape_only with synthetic baseline is correct.', '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('career_change',         'not_applicable','ADJUDICATION-2 Tier N-iii (DHARA_ENGINE_SPEC_v1_0.md §4.3): class boundary between career_change and career_advancement is definitionally ambiguous; any N_e would be unfalsifiable. Not merely lacks a prior — the class itself cannot produce honest temporal windows.', '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3'),
  ('birth_anchor',          'not_applicable','Chart epoch: the subject''s own birth is at t=0 by definition; ka_kshetra computes forward-looking windows only. No scenario exists where birth_anchor produces a future window for the chart subject.', '2026-08-14T11:00:00+00:00', 'PRATINIDHI_a3448a407e9a66ba3')
ON CONFLICT (event_class) DO UPDATE SET
  tier        = EXCLUDED.tier,
  rationale   = EXCLUDED.rationale,
  ratified_at = EXCLUDED.ratified_at,
  ratified_by = EXCLUDED.ratified_by;

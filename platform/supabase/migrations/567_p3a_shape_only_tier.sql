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

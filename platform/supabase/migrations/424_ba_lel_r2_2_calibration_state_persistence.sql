-- Migration 424: BA-LEL R2.2 Step 4/5 — persist + serve calibration_state (judgment_flags)
-- Created: 2026-07-08
--
-- Feature D: the per-chart LEL calibration judgment (structural | sparse | calibrated)
-- becomes a PERSISTED contract, stamped by ph_rectification onto its best row and
-- served by the L4 query_rectification capability.
--
-- Surgical, transactional, idempotent. NO native-chart literal — availability-driven
-- (a chart's state is a pure function of ITS OWN recorded life-event count).
-- Idempotency: ADD COLUMN IF NOT EXISTS (DDL); ON CONFLICT DO UPDATE (L0 constants).

BEGIN;

-- ── 1. judgment_flags column on the best-rectification row ────────────────────
-- Holds the calibration judgment_flags dict from
-- services.mimamsa.lel_calibration.judgment_flags() — keys:
--   calibration (legacy alias), calibration_state (canonical), rectification_basis,
--   lel_event_count, load_bearing.
ALTER TABLE phala_rectification_best
    ADD COLUMN IF NOT EXISTS judgment_flags jsonb;

COMMENT ON COLUMN phala_rectification_best.judgment_flags IS
  'BA-LEL R2.2 Step 4/5: per-chart LEL calibration judgment (calibration_state = '
  'structural|sparse|calibrated, rectification_basis, lel_event_count, load_bearing). '
  'Stamped by ph_rectification from services.mimamsa.lel_calibration.judgment_flags().';

-- ── 2. Seed the two calibration engineering constants ─────────────────────────
-- class=engineering, calibratable=true. consumer_assets lists the layer assets
-- that READ these constants (ph_rectification threshold; mi_jivanaghatana gate).
INSERT INTO brahma_formula_constants
  (constant_id, value_jsonb, class, consumer_assets, citation_or_ratification, calibratable, bounds, version)
VALUES
  ('mimamsa_calibration_min_events',
    '{"n_min":10}',
    'engineering',
    ARRAY['ph_rectification','mi_jivanaghatana'],
    'BA-LEL R2.2 Step 4/5: calibrated-state threshold. A chart with >= n_min recorded '
    'life events reads as `calibrated` (its empirical LEL fit is load-bearing); fewer is '
    '`sparse`; zero is `structural`. Chosen so a 2-event round-trip reads sparse and the '
    'native''s 57 events read calibrated. Registry-tunable; consumed via the '
    'services.mimamsa.lel_calibration constant-read path (fallback = CALIBRATED_MIN_EVENTS=10).',
    true,
    '{"n_min":[3,25]}',
    '1.0'),

  ('mimamsa_recalibration_debounce_seconds',
    '{"seconds":600}',
    'engineering',
    ARRAY['ph_rectification','mi_jivanaghatana'],
    'BA-LEL R2.2 Step 4/5: 10-minute quiet window. LEL saves arrive in bursts; after the '
    'LAST save settles for `seconds`, one targeted recalibration runs (debounce). Consumed '
    'via services.mimamsa.lel_calibration.should_recalibrate (fallback = '
    'DEFAULT_DEBOUNCE_SECONDS).',
    true,
    '{"seconds":[60,3600]}',
    '1.0')

ON CONFLICT (constant_id)
DO UPDATE SET
    value_jsonb              = EXCLUDED.value_jsonb,
    class                    = EXCLUDED.class,
    consumer_assets          = EXCLUDED.consumer_assets,
    citation_or_ratification = EXCLUDED.citation_or_ratification,
    calibratable             = EXCLUDED.calibratable,
    bounds                   = EXCLUDED.bounds;

COMMIT;

-- ── DOWN ──────────────────────────────────────────────────────────────────────
-- To roll back (run manually; not auto-applied):
-- BEGIN;
--   DELETE FROM brahma_formula_constants
--     WHERE constant_id IN ('mimamsa_calibration_min_events','mimamsa_recalibration_debounce_seconds');
--   ALTER TABLE phala_rectification_best DROP COLUMN IF EXISTS judgment_flags;
-- COMMIT;

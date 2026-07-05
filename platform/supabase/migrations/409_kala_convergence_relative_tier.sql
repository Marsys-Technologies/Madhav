-- Migration 409: JL-014 (BA Phase 2.5 J5) — interim within-chart relative tier
-- for kala_convergence, additive to (never replacing) I-21's confidence_label.
--
-- I-21's absolute thresholds (>=0.75 high, >=0.45 moderate, else speculative)
-- were ratified against an assumed convergence_score scale this chart's real
-- scores never reach (~0.04-0.16 observed) — every row collapses to
-- 'speculative', a degenerate tier. Per JL-014, recalibrating the absolute
-- thresholds/weights is DEFERRED to P5A (needs multi-chart review). This adds
-- a purely additive within-chart percentile tier, explicitly flagged
-- 'relative_uncalibrated' so no downstream consumer mistakes it for a
-- calibrated absolute signal.

BEGIN;

ALTER TABLE kala_convergence
    ADD COLUMN IF NOT EXISTS confidence_label_relative TEXT,
    ADD COLUMN IF NOT EXISTS tier_basis TEXT;

COMMENT ON COLUMN kala_convergence.confidence_label_relative IS
  'JL-014 interim tier: within-chart percentile rank of convergence_score against '
  'this chart''s own batch (top 20%=high, next 30%=moderate, rest=speculative). '
  'NOT calibrated against any absolute scale — see tier_basis.';

COMMENT ON COLUMN kala_convergence.tier_basis IS
  'Provenance for confidence_label_relative. ''relative_uncalibrated'' = within-chart '
  'percentile only; absolute-threshold recalibration deferred to P5A (JL-014). '
  'NULL for rows written before migration 409.';

COMMIT;

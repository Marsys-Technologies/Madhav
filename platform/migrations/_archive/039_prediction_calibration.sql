-- platform/migrations/039_prediction_calibration.sql
-- Migration: Prediction calibration columns — Brier score + correction note.
-- GANGA-P3-R3-S1 (L.5 Calibration Substrate)
--
-- brier_score: per-prediction Brier score contribution, computed at outcome-record time.
--   Formula: (confidence - outcome_binary)^2
--   0.0 = best (fully confident correct), 1.0 = worst (fully confident wrong).
--   NULL for partial/unobservable outcomes.
--
-- correction_note: free-text native annotation for refuted/partial predictions.
--   Feeds the Learning Layer loop (CLAUDE.md §E).

ALTER TABLE prediction_ledger
  ADD COLUMN IF NOT EXISTS brier_score NUMERIC,
  ADD COLUMN IF NOT EXISTS correction_note TEXT;

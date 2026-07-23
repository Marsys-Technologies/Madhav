-- Migration 464: retire the dead update_calibration()/compute_brier_score() SQL functions
-- (CR-115/CR-128, 2026-07-23, native-directed post-close cleanup).
--
-- Root cause: both functions were created by the pre-squash legacy migration
-- brahma_mimamsa_outcome.sql (technique/ayanamsha_id/brier_score-shaped
-- mimamsa_calibration prototype). update_calibration() SELECTs pa.prediction_state FROM
-- public.phala_anchors -- a column that does not exist on the live phala_anchors table
-- (37 real columns, none named prediction_state; live schema is anchor_id/
-- confidence_low/confidence_high/posterior/computed_at, built by a later, unrelated
-- migration). It also INSERTs into mimamsa_calibration using (technique, ayanamsha_id,
-- brier_score, sample_size, source_citation, computed_at) -- none of which exist on the
-- LIVE mimamsa_calibration table either (that table was superseded by the mi_pramana /
-- mi_gunanaka writer family's per-match schema: chart_id, match_id, prediction_id,
-- event_id, score_timing/magnitude/domain/falsifier/manifestation, composite_score,
-- composite_verdict, leakage_status, brier_vs_null, ... -- without a tracked migration
-- ever updating this function to match).
--
-- Confirmed live (2026-07-23): both functions exist and are callable, but
-- update_calibration() would hard-error at the first SELECT ("column pa.prediction_state
-- does not exist") the instant it is invoked. The ONLY caller of either function was
-- brahmagyan/mimamsa/outcome.py's record_outcome() (SQL: "SELECT * FROM
-- update_calibration(...)"), itself retired this same commit (CR-115/CR-128) --
-- disconnected dead code calling disconnected dead code. compute_brier_score() has no
-- other SQL-level caller (verified: grep across platform/python-sidecar, platform/src,
-- platform-mcp/src for any other "SELECT ... compute_brier_score" or
-- "FROM update_calibration" -- zero hits).
--
-- The REAL, live calibration write-surface (mi_pramana -> mimamsa_calibration ->
-- mi_gunanaka -> mimamsa_multipliers) is untouched by this migration -- it does not call
-- either of these functions and never did.
--
-- Native ruling (2026-07-23, CR-128/NP-D4B-009 follow-up): retire, do not repair. Repairing
-- either function to match a live schema would create a second, redundant write path into
-- mimamsa_calibration that bypasses mi_pramana's admissibility/held-out/leakage discipline.
--
-- ROLLBACK: re-run the CREATE OR REPLACE FUNCTION bodies from
-- platform/migrations/brahma_mimamsa_outcome.sql (historical/legacy directory, not applied
-- to this schema chain -- kept for audit trail only) if this migration ever needs reverting.
-- Reverting would restore dead, broken code; not recommended.

BEGIN;

DROP FUNCTION IF EXISTS public.update_calibration(TEXT, TEXT, UUID);
DROP FUNCTION IF EXISTS public.compute_brier_score(FLOAT, BOOLEAN);

COMMIT;

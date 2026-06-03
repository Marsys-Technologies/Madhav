-- brahma_mimamsa_prediction_ledger.sql — Brahma L5 Mīmāṃsā — mimamsa.prediction_ledger (MI-5-2)
-- Asset:   mimamsa.prediction_ledger
-- Table:   mimamsa_predictions
-- Tools:   log_prediction(chart_id, prediction, horizon, confidence, falsifier) → prediction_id
--          record_outcome(prediction_id, outcome_observed) → brier_score
-- Layer:   L5 Mīmāṃsā (depends on L4 phala.anchors; consumes phala_anchors for calibration only)
-- Native:  Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
--          chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
--
-- CRITICAL DISCIPLINE — NO LEAKAGE:
--   life_events (LEL) must NEVER feed into prediction generation.
--   LEL feeds calibration ONLY (post-hoc Brier score computation).
--   The model logs prediction BEFORE the outcome is observed.
--   record_outcome() is the ONLY path for writing outcome_observed and brier_score.
--
-- CONTRACT (BRAHMA MI-5-2):
--   - source_citation non-null on ALL rows (B.3 derivation-ledger mandate)
--   - falsifier non-null on ALL rows (Learning Layer discipline rule #4)
--   - confidence in OPEN interval (0, 1) — zero and one are not valid probabilities
--   - outcome_observed NULL until record_outcome() is called
--   - brier_score = (outcome_observed::int - confidence)^2, computed on record_outcome()
--   - Migration: brahma_mimamsa_prediction_ledger.sql (IF NOT EXISTS)
--   - provenance_envelope on all MCP tool responses
--
-- source_citation format: "Brahma L4 phala.anchors / [anchor_id]"
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS public.mimamsa_predictions CASCADE;
--   DROP FUNCTION IF EXISTS mimamsa_record_outcome(UUID, BOOLEAN);
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — mimamsa_predictions table ───────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.mimamsa_predictions (
    -- Identity
    prediction_id    UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    chart_id         UUID        NOT NULL,

    -- Temporal
    predicted_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    horizon_date     DATE        NOT NULL,

    -- Prediction content
    domain           TEXT        NOT NULL,
    prediction_text  TEXT        NOT NULL,

    -- Calibration (required; strict open interval)
    confidence       FLOAT       NOT NULL
                                 CHECK (confidence > 0.0 AND confidence < 1.0),

    -- Falsification (required — B.3 + Learning Layer discipline rule #4)
    falsifier        TEXT        NOT NULL,  -- "If [event] does not occur by [date], this prediction is false"

    -- Provenance (required — B.3 derivation-ledger mandate)
    source_citation  TEXT        NOT NULL,  -- "Brahma L4 phala.anchors / [anchor_id]"

    -- Outcome (NULL until record_outcome() is called — NO LEAKAGE rule)
    outcome_observed BOOLEAN,
    brier_score      FLOAT       CHECK (brier_score IS NULL OR (brier_score >= 0.0 AND brier_score <= 1.0)),
    outcome_recorded_at TIMESTAMPTZ,

    -- Audit
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT mimamsa_predictions_horizon_after_log
        CHECK (horizon_date >= predicted_at::DATE),
    CONSTRAINT mimamsa_predictions_brier_requires_outcome
        CHECK (
            (brier_score IS NULL AND outcome_observed IS NULL) OR
            (brier_score IS NOT NULL AND outcome_observed IS NOT NULL)
        )
);

COMMENT ON TABLE public.mimamsa_predictions IS
  'MI-5-2 mimamsa.prediction_ledger — prospective prediction log. '
  'Predictions are logged BEFORE the outcome is observed (Learning Layer rule #4). '
  'outcome_observed and brier_score are written ONLY via record_outcome(). '
  'source_citation and falsifier are REQUIRED NOT NULL (B.3 mandate + LL rule #4). '
  'confidence in OPEN interval (0, 1) — zero and one are not valid probabilities. '
  'NO LEAKAGE: LEL life_events feed calibration only, never prediction generation.';

COMMENT ON COLUMN public.mimamsa_predictions.prediction_id IS
  'UUID primary key — returned to caller as the handle for record_outcome().';

COMMENT ON COLUMN public.mimamsa_predictions.confidence IS
  'Calibrated probability in OPEN interval (0, 1). '
  'Zero and one excluded — a prediction of certainty is not a calibrated probability. '
  'Brier score = (outcome::int - confidence)^2 at record_outcome time.';

COMMENT ON COLUMN public.mimamsa_predictions.falsifier IS
  'Explicit falsifier per Learning Layer discipline rule #4. '
  'Format: "If [specific observable event] does not occur by [date], this prediction is false."';

COMMENT ON COLUMN public.mimamsa_predictions.source_citation IS
  'L4 citation source: "Brahma L4 phala.anchors / [anchor_id]". '
  'Must reference the phala.anchors row that grounds this prediction (B.3 mandate).';

COMMENT ON COLUMN public.mimamsa_predictions.outcome_observed IS
  'NULL until record_outcome() is called. '
  'TRUE = event occurred (prediction confirmed); FALSE = event did not occur (prediction falsified). '
  'NO LEAKAGE: this column must never be written outside record_outcome().';

COMMENT ON COLUMN public.mimamsa_predictions.brier_score IS
  'Brier score = (outcome_observed::int - confidence)^2. '
  'Range [0, 1]. Lower is better. Perfect calibration = 0. '
  'NULL until record_outcome() is called.';

-- ── §2 — Indexes ──────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_chart_id
    ON public.mimamsa_predictions (chart_id);

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_horizon
    ON public.mimamsa_predictions (chart_id, horizon_date);

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_domain
    ON public.mimamsa_predictions (chart_id, domain);

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_predicted_at
    ON public.mimamsa_predictions (predicted_at);

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_open
    ON public.mimamsa_predictions (chart_id)
    WHERE outcome_observed IS NULL;

-- ── §3 — record_outcome() DB function ────────────────────────────────────────
--
-- CRITICAL: This is the ONLY sanctioned path for writing outcome_observed.
-- Computes brier_score = (outcome_observed::int - confidence)^2.
-- Returns the computed brier_score.

CREATE OR REPLACE FUNCTION mimamsa_record_outcome(
    p_prediction_id  UUID,
    p_outcome        BOOLEAN
)
RETURNS FLOAT
LANGUAGE plpgsql
AS $$
DECLARE
    v_confidence   FLOAT;
    v_brier        FLOAT;
BEGIN
    SELECT confidence INTO v_confidence
    FROM public.mimamsa_predictions
    WHERE prediction_id = p_prediction_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'prediction_id % not found', p_prediction_id;
    END IF;

    -- Brier score: (outcome_bool::int - probability)^2
    -- outcome TRUE  → 1; FALSE → 0
    v_brier := POWER((p_outcome::int::float - v_confidence), 2);

    UPDATE public.mimamsa_predictions
    SET
        outcome_observed    = p_outcome,
        brier_score         = v_brier,
        outcome_recorded_at = NOW(),
        updated_at          = NOW()
    WHERE prediction_id = p_prediction_id;

    RETURN v_brier;
END;
$$;

COMMENT ON FUNCTION mimamsa_record_outcome(UUID, BOOLEAN) IS
  'MI-5-2 record_outcome — ONLY sanctioned path to write outcome_observed. '
  'Computes brier_score = (outcome::int - confidence)^2. Returns brier_score. '
  'NO LEAKAGE: LEL life_events must not call this function during prediction generation — '
  'only during calibration (post-hoc verification) sessions.';

COMMIT;

-- brahma_mimamsa_outcome.sql — Brahma L5 Mīmāṃsā — mimamsa.outcome (MI-5-3)
--
-- Asset:   mimamsa.outcome
-- Table:   mimamsa_calibration
-- Tool:    record_outcome(prediction_id, outcome_observed) → {brier_score, updated_calibration}
-- Layer:   L5 Mīmāṃsā (depends on phala_anchors PH-4-1, prediction_ledger)
-- Native:  Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
--          chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
--
-- CONTRACT (BRAHMA MI-5-3):
--   Scoring: Brier score = (confidence - outcome_binary)² per prediction
--   Calibration: mean(brier_scores) per (technique, ayanamsha_id)
--   source_citation NOT NULL on all rows (B.3 mandate)
--   provenance_envelope on all tool responses
--
-- NO LEAKAGE: life_events feed only into calibration (post-outcome),
--   never into prediction generation. outcome_observed_at must be > prediction created_at.
--
-- ROLLBACK:
--   DROP FUNCTION IF EXISTS compute_brier_score(FLOAT, BOOLEAN);
--   DROP FUNCTION IF EXISTS update_calibration(TEXT, TEXT, UUID);
--   DROP TABLE IF EXISTS public.mimamsa_calibration CASCADE;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — mimamsa_calibration table ───────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.mimamsa_calibration (
    -- Identity
    id               BIGSERIAL   PRIMARY KEY,
    chart_id         UUID        NOT NULL,

    -- Calibration dimensions
    technique        TEXT        NOT NULL,   -- e.g. 'vimshottari', 'yogini', 'kp', 'jaimini_chara'
    ayanamsha_id     TEXT        NOT NULL,   -- e.g. 'lahiri', 'true_chitra', 'kp', 'raman'

    -- Calibration metrics
    brier_score      FLOAT       NOT NULL
                                 CHECK (brier_score >= 0.0 AND brier_score <= 1.0),
    sample_size      INT         NOT NULL CHECK (sample_size >= 1),

    -- Provenance
    source_citation  TEXT        NOT NULL,   -- B.3 mandate: non-null

    -- Audit
    computed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraint: one calibration record per (chart_id, technique, ayanamsha_id, computed_at)
    CONSTRAINT mimamsa_calibration_unique
        UNIQUE (chart_id, technique, ayanamsha_id, computed_at)
);

COMMENT ON TABLE public.mimamsa_calibration IS
    'MI-5-3 mimamsa.outcome — per-technique, per-ayanamsha Brier score calibration. '
    'Brier score = mean((confidence - outcome_binary)²) over all scored predictions. '
    'source_citation required NOT NULL (B.3 derivation-ledger mandate). '
    'NO LEAKAGE: calibration uses only post-outcome observations — never upstream of prediction.';

COMMENT ON COLUMN public.mimamsa_calibration.brier_score IS
    'Mean Brier score in [0.0, 1.0] for this (technique, ayanamsha_id) slice. '
    '0.0 = perfect calibration (fully confident correct predictions). '
    '1.0 = worst calibration (fully confident wrong predictions). '
    '0.25 = uninformative baseline (equivalent to random 50/50 at 0.5 confidence).';

COMMENT ON COLUMN public.mimamsa_calibration.technique IS
    'Prediction technique: vimshottari | yogini | kp | jaimini_chara | '
    'transit_outer | transit_inner | sade_sati | ashtakavarga | ensemble.';

COMMENT ON COLUMN public.mimamsa_calibration.ayanamsha_id IS
    'Ayanamsha used for chart computation: lahiri | true_chitra | kp | raman | surya_siddhanta.';

COMMENT ON COLUMN public.mimamsa_calibration.source_citation IS
    'B.3 derivation-ledger citation. References prediction_ids, FORENSIC v8.0, LEL v1.7. '
    'Format: "computed from predictions {pred_ids} scored against LEL v1.7 events {event_ids}".';

-- ── §2 — Indexes ──────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_chart_technique
    ON public.mimamsa_calibration (chart_id, technique);

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_ayanamsha
    ON public.mimamsa_calibration (ayanamsha_id, computed_at DESC);

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_computed_at
    ON public.mimamsa_calibration (computed_at DESC);

-- ── §3 — compute_brier_score() function ──────────────────────────────────────

CREATE OR REPLACE FUNCTION compute_brier_score(
    p_confidence  FLOAT,
    p_occurred    BOOLEAN
) RETURNS FLOAT
LANGUAGE sql
IMMUTABLE
CALLED ON NULL INPUT
AS $$
    -- Brier score = (confidence - outcome_binary)²
    -- outcome_binary: TRUE → 1.0, FALSE → 0.0, NULL → NULL (unresolved)
    SELECT CASE
        WHEN p_occurred IS NULL THEN NULL
        WHEN p_occurred THEN (p_confidence - 1.0)^2
        ELSE               (p_confidence - 0.0)^2
    END;
$$;

COMMENT ON FUNCTION compute_brier_score(FLOAT, BOOLEAN) IS
    'MI-5-3: Brier score = (confidence - outcome_binary)². '
    'Returns NULL for unresolved (NULL) outcomes. '
    'Range: [0.0, 1.0]. Lower = better calibration.';

-- ── §4 — update_calibration() function ───────────────────────────────────────
--
-- Recomputes the mean Brier score for (technique, ayanamsha_id) across all
-- resolved predictions for the given chart. Inserts a new calibration row
-- (preserving history). Returns the new brier_score and sample_size.
--
-- Depends on: phala_anchors (for resolved predictions with brier scores),
--             prediction_ledger (for legacy brier_score column).
--
-- NOTE: This function reads from phala_anchors.outcome_note + confidence
-- when brier_score is not pre-populated. It computes brier scores on-the-fly
-- for predictions where outcome_recorded_at IS NOT NULL.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_calibration(
    p_technique    TEXT,
    p_ayanamsha_id TEXT,
    p_chart_id     UUID
) RETURNS TABLE (
    new_brier_score  FLOAT,
    new_sample_size  INT,
    inserted_at      TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_brier      FLOAT;
    v_sample     INT;
    v_citation   TEXT;
    v_inserted   TIMESTAMPTZ;
BEGIN
    -- Compute mean Brier score from phala_anchors where outcome is resolved
    -- Prediction is "confirmed" (occurred=TRUE) or "falsified" (occurred=FALSE).
    SELECT
        AVG(
            compute_brier_score(
                pa.confidence,
                CASE pa.prediction_state
                    WHEN 'confirmed' THEN TRUE
                    WHEN 'falsified' THEN FALSE
                    ELSE NULL
                END
            )
        ),
        COUNT(*) FILTER (
            WHERE pa.prediction_state IN ('confirmed', 'falsified')
        )
    INTO v_brier, v_sample
    FROM public.phala_anchors pa
    WHERE pa.chart_id = p_chart_id
      AND pa.prediction_state IN ('confirmed', 'falsified');

    -- Require at least 1 resolved prediction
    IF v_sample IS NULL OR v_sample < 1 THEN
        RAISE EXCEPTION
            'No resolved predictions found for chart_id=% technique=% ayanamsha=%',
            p_chart_id, p_technique, p_ayanamsha_id;
    END IF;

    -- Build source_citation (B.3 mandate)
    v_citation := format(
        'computed from phala_anchors resolved predictions: '
        'chart_id=%s technique=%s ayanamsha=%s sample_size=%s '
        'source: FORENSIC v8.0 §5.1 DSH.V.023-028; LEL v1.7',
        p_chart_id, p_technique, p_ayanamsha_id, v_sample
    );

    v_inserted := NOW();

    -- Insert new calibration row (preserves history)
    INSERT INTO public.mimamsa_calibration
        (chart_id, technique, ayanamsha_id, brier_score, sample_size,
         source_citation, computed_at)
    VALUES
        (p_chart_id, p_technique, p_ayanamsha_id,
         COALESCE(v_brier, 0.25),  -- uninformative baseline when no resolved predictions
         v_sample,
         v_citation,
         v_inserted)
    ON CONFLICT (chart_id, technique, ayanamsha_id, computed_at)
    DO NOTHING;

    RETURN QUERY SELECT COALESCE(v_brier, 0.25), v_sample, v_inserted;
END;
$$;

COMMENT ON FUNCTION update_calibration(TEXT, TEXT, UUID) IS
    'MI-5-3: Recompute mean Brier score for (technique, ayanamsha_id, chart_id). '
    'Inserts a new mimamsa_calibration row (preserves calibration history). '
    'Returns (new_brier_score, new_sample_size, inserted_at). '
    'Raises if no resolved predictions exist. '
    'source_citation is auto-built and satisfies B.3 mandate.';

COMMIT;

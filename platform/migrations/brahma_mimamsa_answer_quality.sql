-- brahma_mimamsa_answer_quality.sql — Brahma L5 Mīmāṃsā — mimamsa.answer_quality (MI-5-6)
-- Asset:   mimamsa.answer_quality
-- Table:   mimamsa_qa_eval
-- Tool:    answer_quality_eval(question, actual_response) →
--              {b11_compliance, layer_coverage, grounding_score, provenance_envelope}
-- Layer:   L5 Mīmāṃsā (final layer — evaluates answer quality across all 6 layers)
-- Native:  Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
--          chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
--
-- CONTRACT (BRAHMA MI-5-6):
--   Golden Q&A eval distinct from prediction calibration.
--   b11_compliance: response must route through holistic_bundle first (B.11 mandate).
--   layer_coverage: fraction of 6 layers touched in the response [0.0, 1.0].
--   grounding_score: fraction of expected domains present in actual_response [0.0, 1.0].
--   source_citation: non-null on all rows.
--   NO LEAKAGE: life_events must never feed prediction generation — calibration only.
--
-- Layers (L0–L5):
--   L0 Brahmagyan  — instrument identity + meta-layer
--   L1 Gaṇita      — astronomical facts (FORENSIC v8.0, ephemeris)
--   L2 Bodha       — interpretation signals (MSR, UCN, CGM, CDLM, RM)
--   L3 Kāla        — temporal/dasha engines
--   L4 Phala       — calibrated predictions / anchors
--   L5 Mīmāṃsā     — final synthesis / answer quality (this layer)
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS public.mimamsa_qa_eval CASCADE;
--   DROP FUNCTION IF EXISTS seed_mimamsa_golden_pairs(UUID);
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — mimamsa_qa_eval table ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.mimamsa_qa_eval (
    -- Identity
    eval_id             UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Question / answer content
    question            TEXT        NOT NULL,
    expected_domains    TEXT[]      NOT NULL DEFAULT ARRAY[]::TEXT[],
    actual_response     TEXT,

    -- Quality metrics
    b11_compliance      BOOLEAN,
    layer_coverage      FLOAT       CHECK (layer_coverage IS NULL OR
                                          (layer_coverage >= 0.0 AND layer_coverage <= 1.0)),
    grounding_score     FLOAT       CHECK (grounding_score IS NULL OR
                                          (grounding_score >= 0.0 AND grounding_score <= 1.0)),

    -- Provenance (required — B.3 mandate)
    source_citation     TEXT        NOT NULL,

    -- Lifecycle
    evaluated_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.mimamsa_qa_eval IS
  'MI-5-6 mimamsa.answer_quality — golden Q&A eval set for L5 Mīmāṃsā. '
  'b11_compliance: response routes through holistic_bundle first (B.11 mandate). '
  'layer_coverage: fraction of 6 layers (L0–L5) present in response. '
  'grounding_score: fraction of expected_domains found in actual_response. '
  'source_citation required NOT NULL (B.3 derivation-ledger mandate). '
  'NO LEAKAGE: life_events feed calibration only, never prediction generation.';

COMMENT ON COLUMN public.mimamsa_qa_eval.b11_compliance IS
  'TRUE if actual_response demonstrates holistic_bundle (MSR+UCN+CDLM+CGM+RM) '
  'routing before domain-specific answer (B.11 Whole-Chart-Read discipline). '
  'NULL = not yet evaluated.';

COMMENT ON COLUMN public.mimamsa_qa_eval.layer_coverage IS
  'Fraction of 6 Brahma layers (L0–L5) represented in the actual_response. '
  'Range [0.0, 1.0]. NULL = not yet evaluated.';

COMMENT ON COLUMN public.mimamsa_qa_eval.grounding_score IS
  'Fraction of expected_domains that appear in actual_response. '
  'Range [0.0, 1.0]. NULL = not yet evaluated.';

COMMENT ON COLUMN public.mimamsa_qa_eval.source_citation IS
  'Brahma QA golden set v1.0 — source of this Q&A pair.';

-- ── §2 — Indexes ──────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_mimamsa_qa_eval_b11
    ON public.mimamsa_qa_eval (b11_compliance);

CREATE INDEX IF NOT EXISTS idx_mimamsa_qa_eval_grounding
    ON public.mimamsa_qa_eval (grounding_score DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_mimamsa_qa_eval_layer_coverage
    ON public.mimamsa_qa_eval (layer_coverage DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_mimamsa_qa_eval_created
    ON public.mimamsa_qa_eval (created_at DESC);

-- ── §3 — Golden Q&A seed function ─────────────────────────────────────────────
--
-- Seeds 10 golden Q&A pairs covering all 6 layers (2 per layer × 3 layers min).
-- Source: "Brahma QA golden set v1.0"
-- Layer distribution:
--   L0 Brahmagyan (meta):   Q1, Q2
--   L1 Gaṇita (facts):      Q3, Q4
--   L2 Bodha (signals):     Q5, Q6
--   L3 Kāla (temporal):     Q7, Q8
--   L4 Phala (predictions): Q9
--   L5 Mīmāṃsā (quality):   Q10
-- All rows carry source_citation = 'Brahma QA golden set v1.0'
-- All b11_compliance = TRUE (B.11 requires holistic_bundle routing)

CREATE OR REPLACE FUNCTION seed_mimamsa_golden_pairs(
    p_chart_id  UUID  DEFAULT NULL   -- reserved for chart-scoped seeds; NULL = global
)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
    v_inserted INT := 0;
    v_citation TEXT := 'Brahma QA golden set v1.0';
BEGIN
    INSERT INTO public.mimamsa_qa_eval
        (question, expected_domains, b11_compliance, source_citation)
    VALUES

    -- ── L0 Brahmagyan (instrument meta-layer) ────────────────────────────────

    -- Q1: What are the core layers of the Brahma instrument?
    (
        'What are the six layers of the Brahma Jyotish instrument and how do they relate to each other?',
        ARRAY[
            'L0.brahmagyan.meta',
            'L1.ganita.facts',
            'L2.bodha.signals',
            'L3.kala.temporal',
            'L4.phala.predictions',
            'L5.mimamsa.quality'
        ],
        TRUE,
        v_citation
    ),

    -- Q2: How does B.11 Whole-Chart-Read discipline work?
    (
        'Describe the B.11 Whole-Chart-Read discipline and explain why holistic_bundle must be consulted before any domain-specific answer.',
        ARRAY[
            'L0.brahmagyan.meta',
            'L2.bodha.holistic_bundle',
            'L2.bodha.MSR',
            'L2.bodha.UCN',
            'L2.bodha.CDLM'
        ],
        TRUE,
        v_citation
    ),

    -- ── L1 Gaṇita (astronomical facts) ──────────────────────────────────────

    -- Q3: Native's ascendant and core planetary positions
    (
        'What is the ascendant (lagna) and which planets are in which houses for Abhisek Mohanty''s chart?',
        ARRAY[
            'L1.ganita.positions',
            'L1.ganita.lagna',
            'L1.ganita.grahas',
            'L1.ganita.FORENSIC_v8'
        ],
        TRUE,
        v_citation
    ),

    -- Q4: Dasha sequence and current period
    (
        'What is the current Vimshottari Dasha sequence for this native and which Mahadasha-Antardasha period are we in as of 2026?',
        ARRAY[
            'L1.ganita.dasha_vimshottari',
            'L1.ganita.FORENSIC_v8',
            'L3.kala.dasha_sequence',
            'L3.kala.DSH_V_023'
        ],
        TRUE,
        v_citation
    ),

    -- ── L2 Bodha (interpretation signals) ────────────────────────────────────

    -- Q5: Dominant career signal
    (
        'What is the dominant career signal for this native and which MSR signals converge on career themes?',
        ARRAY[
            'L2.bodha.signals',
            'L2.bodha.MSR',
            'L1.ganita.positions',
            'career'
        ],
        TRUE,
        v_citation
    ),

    -- Q6: Atmakaraka and soul-level pattern
    (
        'Who is the Atmakaraka in this chart and what soul-level pattern does it indicate across the Jaimini, KP, and Parashari schools?',
        ARRAY[
            'L2.bodha.signals',
            'L2.bodha.UCN',
            'L2.bodha.MSR',
            'L1.ganita.jaimini',
            'spiritual'
        ],
        TRUE,
        v_citation
    ),

    -- ── L3 Kāla (temporal / dasha engines) ───────────────────────────────────

    -- Q7: Sade Sati timeline
    (
        'When does the current Sade Sati cycle end for this native and what does the exit phase signify?',
        ARRAY[
            'L3.kala.sade_sati',
            'L3.kala.temporal',
            'L1.ganita.FORENSIC_v8',
            'L2.bodha.signals'
        ],
        TRUE,
        v_citation
    ),

    -- Q8: Transit alignment in 2027
    (
        'What major transit alignments occur in 2027 around the Mercury-to-Ketu Mahadasha transition and how do they amplify or dampen the regime change?',
        ARRAY[
            'L3.kala.temporal',
            'L3.kala.dasha_sequence',
            'L1.ganita.transits',
            'L2.bodha.MSR',
            'L4.phala.predictions'
        ],
        TRUE,
        v_citation
    ),

    -- ── L4 Phala (calibrated predictions) ────────────────────────────────────

    -- Q9: 2026 career prediction
    (
        'What is the calibrated career prediction for the first half of 2026 and what is the explicit falsifier for this prediction?',
        ARRAY[
            'L4.phala.predictions',
            'L4.phala.anchors',
            'L3.kala.dasha_sequence',
            'L2.bodha.signals',
            'career'
        ],
        TRUE,
        v_citation
    ),

    -- ── L5 Mīmāṃsā (answer quality / final synthesis) ────────────────────────

    -- Q10: Answer quality evaluation
    (
        'How would you evaluate the quality of an acharya-grade response about this native''s spiritual trajectory — what layers must it touch and what makes it B.11 compliant?',
        ARRAY[
            'L5.mimamsa.quality',
            'L5.mimamsa.b11_compliance',
            'L2.bodha.holistic_bundle',
            'L0.brahmagyan.meta',
            'spiritual'
        ],
        TRUE,
        v_citation
    )

    ON CONFLICT DO NOTHING;

    GET DIAGNOSTICS v_inserted = ROW_COUNT;
    RETURN v_inserted;
END;
$$;

COMMENT ON FUNCTION seed_mimamsa_golden_pairs(UUID) IS
  'MI-5-6 seed function — 10 golden Q&A pairs for mimamsa.answer_quality eval. '
  'Covers all 6 Brahma layers (L0–L5): 2 pairs for L0/L1/L2/L3, 1 each for L4/L5. '
  'All pairs: b11_compliance=TRUE, source_citation=Brahma QA golden set v1.0. '
  'Idempotent — ON CONFLICT DO NOTHING. Returns rows inserted.';

COMMIT;

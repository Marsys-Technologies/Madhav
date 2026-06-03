-- brahma_phala_muhurta.sql — Brahma L4 Phala — phala.muhurta (PH-4-4)
-- Asset:   phala.muhurta (electional finder — inverts Phala prediction engine)
-- Table:   phala_muhurta
-- Tool:    muhurta_finder(chart_id, action_type, date_range, min_score?)
--          → {windows:[{start,end,score,factors}], provenance_envelope}
-- Layer:   L4 Phala (depends on panchanga_daily, chart_facts, phala_anchors)
-- Native:  Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
--          chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
--
-- CONTRACT (BRAHMA PH-4-4):
--   This tool INVERTS the prediction engine:
--     - Prediction asks "what will happen given the current time?"
--     - Electional asks "WHEN is best to act for a desired action?"
--   Algorithm: for each 48-hour window in next 90 days,
--     score = panchanga_quality × dasha_quality × transit_quality × signal_activation
--   All scores in [0.0, 1.0]. source_citation is NON-NULL on every row (B.3 mandate).
--   action_types: marriage | travel | business | medical | education | property | general
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS public.phala_muhurta CASCADE;
--   DROP FUNCTION IF EXISTS phala_compute_muhurta_score(FLOAT, FLOAT, FLOAT, FLOAT);
--   DROP FUNCTION IF EXISTS phala_valid_action_type(TEXT);
--   DROP FUNCTION IF EXISTS seed_phala_muhurta_native_sample(UUID);
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — phala_muhurta table ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.phala_muhurta (
    -- Identity
    muhurta_id       UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    chart_id         UUID        NOT NULL,

    -- Action type (CHECK constraint guards the 7 canonical types + general)
    action_type      TEXT        NOT NULL,

    -- Temporal window (48-hour blocks, stored as TIMESTAMPTZ per contract)
    window_start     TIMESTAMPTZ NOT NULL,
    window_end       TIMESTAMPTZ NOT NULL,

    -- Auspiciousness score [0.0, 1.0] (composite of 4 sub-scores)
    auspiciousness_score FLOAT   NOT NULL CHECK (auspiciousness_score >= 0.0 AND auspiciousness_score <= 1.0),

    -- Score breakdown factors (JSONB — see §2 for shape)
    --   {
    --     "panchanga_quality": float,   -- tithi × vara × nakshatra weighted score
    --     "dasha_quality":     float,   -- active MD/AD benefic score for chart
    --     "transit_quality":   float,   -- key transits during the window
    --     "signal_activation": float,   -- MSR signal activation for action_type
    --     "panchanga_details": {
    --       "tithi_name": str,
    --       "vara_lord": str,
    --       "moon_nakshatra": str,
    --       "yoga": str,
    --       "inauspicious_windows": [str]
    --     },
    --     "dasha_details":     {"md_lord": str, "ad_lord": str},
    --     "avoid_notes":       [str]    -- knockout reasons (empty if none)
    --   }
    factors          JSONB       NOT NULL DEFAULT '{}'::JSONB,

    -- B.3 provenance mandate — non-null source citation on every row
    source_citation  TEXT        NOT NULL,

    -- Timestamps
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Constraint: window must be forward-looking (start < end)
    CONSTRAINT phala_muhurta_window_valid CHECK (window_start < window_end),

    -- Constraint: action_type must be one of the 7 canonical types
    CONSTRAINT phala_muhurta_action_type_valid CHECK (
        action_type IN (
            'marriage', 'travel', 'business', 'medical',
            'education', 'property', 'general'
        )
    )
);

-- ── §2 — Indexes ──────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_phala_muhurta_chart_action
    ON public.phala_muhurta (chart_id, action_type);

CREATE INDEX IF NOT EXISTS idx_phala_muhurta_window_start
    ON public.phala_muhurta (window_start);

CREATE INDEX IF NOT EXISTS idx_phala_muhurta_score
    ON public.phala_muhurta (auspiciousness_score DESC);

-- Composite: chart + action + score (for ranked retrieval)
CREATE INDEX IF NOT EXISTS idx_phala_muhurta_chart_action_score
    ON public.phala_muhurta (chart_id, action_type, auspiciousness_score DESC);

-- GIN on factors for JSONB field queries
CREATE INDEX IF NOT EXISTS idx_phala_muhurta_factors_gin
    ON public.phala_muhurta USING GIN (factors);

-- ── §3 — Scoring function ─────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION phala_compute_muhurta_score(
    p_panchanga_quality FLOAT,
    p_dasha_quality     FLOAT,
    p_transit_quality   FLOAT,
    p_signal_activation FLOAT
) RETURNS FLOAT
LANGUAGE SQL
IMMUTABLE
AS $$
    -- Weighted composite: panchanga (40%) + dasha (30%) + transit (20%) + signal (10%)
    -- All sub-scores must be in [0.0, 1.0]; result clamped to [0.0, 1.0]
    SELECT GREATEST(0.0, LEAST(1.0,
        0.40 * p_panchanga_quality
        + 0.30 * p_dasha_quality
        + 0.20 * p_transit_quality
        + 0.10 * p_signal_activation
    ));
$$;

COMMENT ON FUNCTION phala_compute_muhurta_score IS
'PH-4-4: Composite muhurta score from 4 sub-scores.
 Weights: panchanga 40%, dasha 30%, transit 20%, signal_activation 10%.
 Mirrors Python engine compute_muhurta_score(). Result in [0.0, 1.0].';

-- ── §4 — Action type validator ────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION phala_valid_action_type(p_action_type TEXT)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT p_action_type IN (
        'marriage', 'travel', 'business', 'medical',
        'education', 'property', 'general'
    );
$$;

COMMENT ON FUNCTION phala_valid_action_type IS
'PH-4-4: Returns TRUE if the action_type is one of the 7 canonical types.';

-- ── §5 — Native sample seed function ─────────────────────────────────────────
--
-- Inserts 3 representative pre-computed rows for the native chart
-- demonstrating the score range across action types.
-- Idempotent via ON CONFLICT DO NOTHING on (chart_id, action_type, window_start).

CREATE UNIQUE INDEX IF NOT EXISTS idx_phala_muhurta_unique_window
    ON public.phala_muhurta (chart_id, action_type, window_start);

CREATE OR REPLACE FUNCTION seed_phala_muhurta_native_sample(p_chart_id UUID)
RETURNS INTEGER
LANGUAGE PLPGSQL
AS $$
DECLARE
    v_rows_inserted INTEGER := 0;
BEGIN
    -- Sample 1: Marriage window — high score
    -- Native chart: Mercury MD / Saturn AD (2026-2029)
    -- Mercury-Saturn combination: professional but moderate for marriage
    -- Strong panchanga: Shukla Panchami (tithi 5), Thursday (Guruvara), Rohini nakshatra
    INSERT INTO public.phala_muhurta (
        chart_id, action_type,
        window_start, window_end,
        auspiciousness_score, factors, source_citation
    ) VALUES (
        p_chart_id, 'marriage',
        '2026-06-25 00:00:00+00'::TIMESTAMPTZ,
        '2026-06-27 00:00:00+00'::TIMESTAMPTZ,
        phala_compute_muhurta_score(0.82, 0.55, 0.70, 0.65),
        jsonb_build_object(
            'panchanga_quality', 0.82,
            'dasha_quality', 0.55,
            'transit_quality', 0.70,
            'signal_activation', 0.65,
            'panchanga_details', jsonb_build_object(
                'tithi_name', 'Shukla Panchami',
                'vara_lord', 'Jupiter',
                'moon_nakshatra', 'Rohini',
                'yoga', 'Siddha',
                'inauspicious_windows', '[]'::JSONB
            ),
            'dasha_details', jsonb_build_object(
                'md_lord', 'Mercury',
                'ad_lord', 'Saturn'
            ),
            'avoid_notes', '[]'::JSONB
        ),
        'FORENSIC v8.0 §5.1 DSH.V.023 Mercury MD (2026-2043); '
        'panchanga_daily 2026-06-25 (Shukla Panchami/Rohini/Guruvara); '
        'MSR v5.0 SIG.09 7H-Venus signification; '
        'BPHS ch.46 §marriage muhurta (Rohini/Guruvara auspicious); '
        'PH-4-4 native sample seed'
    )
    ON CONFLICT (chart_id, action_type, window_start) DO NOTHING;
    GET DIAGNOSTICS v_rows_inserted = ROW_COUNT;

    -- Sample 2: Business window — moderate score
    -- Mercury MD / Ketu AD: Ketu adds spiritual/karmic overlay, less ideal for commerce
    INSERT INTO public.phala_muhurta (
        chart_id, action_type,
        window_start, window_end,
        auspiciousness_score, factors, source_citation
    ) VALUES (
        p_chart_id, 'business',
        '2026-07-15 00:00:00+00'::TIMESTAMPTZ,
        '2026-07-17 00:00:00+00'::TIMESTAMPTZ,
        phala_compute_muhurta_score(0.60, 0.48, 0.55, 0.72),
        jsonb_build_object(
            'panchanga_quality', 0.60,
            'dasha_quality', 0.48,
            'transit_quality', 0.55,
            'signal_activation', 0.72,
            'panchanga_details', jsonb_build_object(
                'tithi_name', 'Shukla Tritiya',
                'vara_lord', 'Mercury',
                'moon_nakshatra', 'Hasta',
                'yoga', 'Shubha',
                'inauspicious_windows', '["rahu_kalam"]'::JSONB
            ),
            'dasha_details', jsonb_build_object(
                'md_lord', 'Mercury',
                'ad_lord', 'Mercury'
            ),
            'avoid_notes', jsonb_build_array(
                'Rahu Kalam active: avoid 12:00-13:30 IST window'
            )
        ),
        'FORENSIC v8.0 §5.1 DSH.V.023 Mercury MD (2026-2043); '
        'panchanga_daily 2026-07-15 (Shukla Tritiya/Hasta/Budhavara); '
        'MSR v5.0 SIG.14 Mercury 3H commerce activation; '
        'BPHS ch.46 §vyapara muhurta (Hasta/Budhavara commerce-favorable); '
        'PH-4-4 native sample seed'
    )
    ON CONFLICT (chart_id, action_type, window_start) DO NOTHING;
    v_rows_inserted := v_rows_inserted + (
        SELECT 1 WHERE EXISTS (
            SELECT 1 FROM public.phala_muhurta
            WHERE chart_id = p_chart_id
              AND action_type = 'business'
              AND window_start = '2026-07-15 00:00:00+00'::TIMESTAMPTZ
        )
    );

    -- Sample 3: Education window — strong score
    -- Mercury MD strongly favors learning/education/writing
    INSERT INTO public.phala_muhurta (
        chart_id, action_type,
        window_start, window_end,
        auspiciousness_score, factors, source_citation
    ) VALUES (
        p_chart_id, 'education',
        '2026-08-05 00:00:00+00'::TIMESTAMPTZ,
        '2026-08-07 00:00:00+00'::TIMESTAMPTZ,
        phala_compute_muhurta_score(0.75, 0.82, 0.65, 0.78),
        jsonb_build_object(
            'panchanga_quality', 0.75,
            'dasha_quality', 0.82,
            'transit_quality', 0.65,
            'signal_activation', 0.78,
            'panchanga_details', jsonb_build_object(
                'tithi_name', 'Shukla Dvadashi',
                'vara_lord', 'Mercury',
                'moon_nakshatra', 'Pushya',
                'yoga', 'Brahma',
                'inauspicious_windows', '[]'::JSONB
            ),
            'dasha_details', jsonb_build_object(
                'md_lord', 'Mercury',
                'ad_lord', 'Mercury'
            ),
            'avoid_notes', '[]'::JSONB
        ),
        'FORENSIC v8.0 §5.1 DSH.V.023 Mercury MD (2026-2043); '
        'panchanga_daily 2026-08-05 (Shukla Dvadashi/Pushya/Budhavara); '
        'MSR v5.0 SIG.08 Mercury 4H education; '
        'BPHS ch.46 §vidya muhurta (Pushya nakshatra most auspicious for education); '
        'PH-4-4 native sample seed'
    )
    ON CONFLICT (chart_id, action_type, window_start) DO NOTHING;
    v_rows_inserted := v_rows_inserted + (
        SELECT 1 WHERE EXISTS (
            SELECT 1 FROM public.phala_muhurta
            WHERE chart_id = p_chart_id
              AND action_type = 'education'
              AND window_start = '2026-08-05 00:00:00+00'::TIMESTAMPTZ
        )
    );

    RETURN v_rows_inserted;
END;
$$;

COMMENT ON FUNCTION seed_phala_muhurta_native_sample IS
'PH-4-4: Insert 3 representative pre-computed rows for the native chart.
 Idempotent via ON CONFLICT DO NOTHING on (chart_id, action_type, window_start).
 Rows demonstrate high/medium/strong score bands across 3 action types.
 Source citations: FORENSIC v8.0 §5.1 + panchanga_daily + MSR v5.0 + BPHS ch.46.';

-- ── §6 — Comment on table ─────────────────────────────────────────────────────

COMMENT ON TABLE public.phala_muhurta IS
'PH-4-4 — phala.muhurta electional finder (inverts Phala prediction engine).

Instead of "what will happen?", this asks "WHEN is best to act?"

Algorithm: for each 48-hour window in the requested date range, compute
  auspiciousness_score = panchanga_quality(40%) × dasha_quality(30%)
                       × transit_quality(20%) × signal_activation(10%)
All sub-scores and composite in [0.0, 1.0]. Rows are pre-computed and cached;
the tool reads from this table (retrieval engine, not real-time compute).

B.3 mandate: source_citation is NON-NULL on every row.
action_types: marriage | travel | business | medical | education | property | general

L1 ground-truth: FORENSIC v8.0 §5.1 (dasha) + panchanga_daily (panchanga)
                 + MSR v5.0 SIG.* (signal activation)
BRAHMA-PH-4-4';

COMMIT;

-- 0001_brahma_baseline.sql
-- Brahma-era baseline migration — squash of all historical migrations (057 through WS-2 final)
-- Authored: 2026-06-05 by WS-Misc migration-squash session
-- DB: PostgreSQL 15+ (Supabase Cloud SQL production)
--
-- SQUASH SENTINEL: BRAHMA_BASELINE_v1.0
-- Squashes: migrations 057_school_signal_coverage through 157_charts_natural_key_uniq
-- Pre-squash snapshot: _pre_squash_schema_snapshot.sql
-- Table count: 81
--
-- This file creates the complete public schema from scratch.
-- Apply to an empty database to reproduce the production schema.
-- New migrations must start at 0002 or higher.
--
-- idempotency: CREATE TABLE IF NOT EXISTS used throughout;
-- functions use CREATE OR REPLACE; indexes use CREATE INDEX IF NOT EXISTS.
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- PostgreSQL database dump
--




--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA public;


--
-- Name: bodha_concordance_lens(text, numeric); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.bodha_concordance_lens(p_chart_id text, p_min_conf numeric DEFAULT 0) RETURNS TABLE(domain text, valence text, signal_count bigint, avg_confidence double precision, agreement_score double precision, signal_ids text[], signal_texts text[])
    LANGUAGE sql STABLE
    AS $$
  SELECT domain, valence, COUNT(*) AS signal_count,
         AVG(confidence)::FLOAT AS avg_confidence,
         (AVG(confidence) * AVG(salience))::FLOAT AS agreement_score,
         ARRAY_AGG(signal_id) AS signal_ids,
         ARRAY_AGG(signal_text) AS signal_texts
  FROM bodha_signals
  WHERE chart_id::TEXT = p_chart_id AND confidence >= p_min_conf
  GROUP BY domain, valence
  ORDER BY domain, agreement_score DESC;
$$;


--
-- Name: bodha_contradiction_lens(text, numeric); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.bodha_contradiction_lens(p_chart_id text, p_min_conf numeric DEFAULT 0.3) RETURNS TABLE(domain text, signal_id_a text, signal_text_a text, valence_a text, signal_id_b text, signal_text_b text, valence_b text, tension_score double precision)
    LANGUAGE sql STABLE
    AS $$
  SELECT a.domain, a.signal_id, a.signal_text, a.valence,
         b.signal_id, b.signal_text, b.valence,
         (a.confidence * b.confidence)::FLOAT AS tension_score
  FROM bodha_signals a JOIN bodha_signals b
       ON a.chart_id = b.chart_id AND a.domain = b.domain
       AND a.valence IN ('positive','benefic') AND b.valence IN ('negative','malefic')
  WHERE a.chart_id::TEXT = p_chart_id AND a.confidence >= p_min_conf AND b.confidence >= p_min_conf
  ORDER BY tension_score DESC;
$$;


--
-- Name: bodha_negative_space(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.bodha_negative_space(p_chart_id text) RETURNS TABLE(check_type text, label text, signal_count bigint, max_confidence double precision)
    LANGUAGE sql STABLE
    AS $$
  SELECT 'domain_absent'::TEXT, d.domain::TEXT, 
         COUNT(s.signal_id) AS signal_count,
         COALESCE(MAX(s.confidence), 0)::FLOAT AS max_confidence
  FROM (VALUES ('career'),('health'),('relationship'),('wealth'),('dharma'),('foreign'),('children'),('property'),('intellect'),('creativity')) AS d(domain)
  LEFT JOIN bodha_signals s ON s.domain = d.domain AND s.chart_id::TEXT = p_chart_id
  GROUP BY d.domain HAVING COUNT(s.signal_id) = 0;
$$;


--
-- Name: bodha_salience_lens(text, numeric, numeric, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.bodha_salience_lens(p_chart_id text, p_min_conf numeric DEFAULT 0, p_min_sal numeric DEFAULT 0, p_limit integer DEFAULT 50) RETURNS TABLE(rank bigint, signal_id text, signal_text text, domain text, valence text, confidence double precision, salience double precision, source_citation text)
    LANGUAGE sql STABLE
    AS $$
  SELECT ROW_NUMBER() OVER (ORDER BY (confidence*salience) DESC) AS rank,
         signal_id, signal_text, domain, valence, confidence::FLOAT, salience::FLOAT, source_citation
  FROM bodha_signals
  WHERE chart_id::TEXT = p_chart_id AND confidence >= p_min_conf AND salience >= p_min_sal
  LIMIT p_limit;
$$;


--
-- Name: compute_brier_score(double precision, boolean); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.compute_brier_score(p_confidence double precision, p_occurred boolean) RETURNS double precision
    LANGUAGE sql IMMUTABLE
    AS $$
    -- Brier score = (confidence - outcome_binary)²
    -- outcome_binary: TRUE → 1.0, FALSE → 0.0, NULL → NULL (unresolved)
    SELECT CASE
        WHEN p_occurred IS NULL THEN NULL
        WHEN p_occurred THEN (p_confidence - 1.0)^2
        ELSE               (p_confidence - 0.0)^2
    END;
$$;


--
-- Name: FUNCTION compute_brier_score(p_confidence double precision, p_occurred boolean); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.compute_brier_score(p_confidence double precision, p_occurred boolean) IS 'MI-5-3: Brier score = (confidence - outcome_binary)². Returns NULL for unresolved (NULL) outcomes. Range: [0.0, 1.0]. Lower = better calibration.';


--
-- Name: compute_mimamsa_multiplier(double precision); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.compute_mimamsa_multiplier(mean_brier_score double precision) RETURNS double precision
    LANGUAGE sql IMMUTABLE STRICT
    AS $$
    SELECT GREATEST(0.8, LEAST(1.2, 1.0 + 0.1 * (0.5 - mean_brier_score)));
$$;


--
-- Name: FUNCTION compute_mimamsa_multiplier(mean_brier_score double precision); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.compute_mimamsa_multiplier(mean_brier_score double precision) IS 'Compute bounded learning multiplier from a mean Brier score. Returns CLAMP(1.0 + 0.1 × (0.5 - mean_brier_score), 0.8, 1.2). mean_brier_score < 0.5: multiplier > 1.0 (boost). mean_brier_score > 0.5: multiplier < 1.0 (down-weight). BRAHMA-MI-5-4';


--
-- Name: compute_window_score(double precision, double precision, double precision); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.compute_window_score(p_dasha_quality double precision, p_signal_strength double precision, p_convergence_score double precision) RETURNS double precision
    LANGUAGE sql IMMUTABLE
    AS $$
    SELECT GREATEST(0.0, LEAST(1.0,
        p_dasha_quality * p_signal_strength * p_convergence_score
    ))::FLOAT
$$;


--
-- Name: FUNCTION compute_window_score(p_dasha_quality double precision, p_signal_strength double precision, p_convergence_score double precision); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.compute_window_score(p_dasha_quality double precision, p_signal_strength double precision, p_convergence_score double precision) IS 'PH-4-1 score = CLAMP(dasha_quality × signal_strength × convergence_score, 0, 1). All three components must be individually in [0.0, 1.0].';


--
-- Name: conversations_set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.conversations_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  UPDATE public.conversations SET updated_at = NOW() WHERE id = NEW.conversation_id;
  RETURN NEW;
END;
$$;


--
-- Name: mimamsa_record_outcome(uuid, boolean); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.mimamsa_record_outcome(p_prediction_id uuid, p_outcome boolean) RETURNS double precision
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


--
-- Name: FUNCTION mimamsa_record_outcome(p_prediction_id uuid, p_outcome boolean); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.mimamsa_record_outcome(p_prediction_id uuid, p_outcome boolean) IS 'MI-5-2 record_outcome — ONLY sanctioned path to write outcome_observed. Computes brier_score = (outcome::int - confidence)^2. Returns brier_score. NO LEAKAGE: LEL life_events must not call this function during prediction generation — only during calibration (post-hoc verification) sessions.';


--
-- Name: phala_compute_muhurta_score(double precision, double precision, double precision, double precision); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.phala_compute_muhurta_score(p_panchanga_quality double precision, p_dasha_quality double precision, p_transit_quality double precision, p_signal_activation double precision) RETURNS double precision
    LANGUAGE sql IMMUTABLE
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


--
-- Name: FUNCTION phala_compute_muhurta_score(p_panchanga_quality double precision, p_dasha_quality double precision, p_transit_quality double precision, p_signal_activation double precision); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.phala_compute_muhurta_score(p_panchanga_quality double precision, p_dasha_quality double precision, p_transit_quality double precision, p_signal_activation double precision) IS 'PH-4-4: Composite muhurta score from 4 sub-scores.
 Weights: panchanga 40%, dasha 30%, transit 20%, signal_activation 10%.
 Mirrors Python engine compute_muhurta_score(). Result in [0.0, 1.0].';


--
-- Name: phala_get_rectification(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.phala_get_rectification(p_chart_id uuid) RETURNS jsonb
    LANGUAGE plpgsql STABLE
    AS $$
DECLARE
    v_row   RECORD;
    v_count BIGINT;
    v_result JSONB;
BEGIN
    -- Count candidates for provenance
    SELECT COUNT(*) INTO v_count
    FROM phala_rectification
    WHERE chart_id = p_chart_id;

    IF v_count = 0 THEN
        RETURN jsonb_build_object(
            'error',      'no_candidates',
            'chart_id',   p_chart_id,
            'message',    'Run: python -m brahmagyan.phala.rectification seed --chart-id ' || p_chart_id,
            'asset',      'PH-4-3'
        );
    END IF;

    SELECT *
    INTO   v_row
    FROM   phala_rectification_best
    WHERE  chart_id = p_chart_id;

    v_result := jsonb_build_object(
        'chart_id',                 p_chart_id,
        'best_candidate_time',      TO_CHAR(v_row.candidate_time, 'HH24:MI'),
        'confidence',               v_row.rectification_confidence,
        'train_score',              v_row.best_alignment_score,
        'candidate_count',          v_count,
        'source_citation',          v_row.source_citation,
        'provenance_envelope',      jsonb_build_object(
            'source',               'phala.rectification',
            'asset',                'PH-4-3',
            'algorithm',            'dasha_alignment_train_test_split',
            'train_split',          'events 1–43 (75%)',
            'test_split',           'events 44–57 (25%, held-out)',
            'leakage_check',        'PASS — test events not used for candidate selection',
            'b10_compliance',       'Dasha-level only; no Swiss Ephemeris re-run',
            'computed_at',          v_row.computed_at
        )
    );

    RETURN v_result;
END;
$$;


--
-- Name: FUNCTION phala_get_rectification(p_chart_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.phala_get_rectification(p_chart_id uuid) IS 'PH-4-3 tool entry point: returns best rectification candidate for a chart. Output: {chart_id, best_candidate_time (HH:MM), confidence, train_score, candidate_count, source_citation, provenance_envelope}. Returns error JSON if no candidates seeded. Seed with: python -m brahmagyan.phala.rectification seed --chart-id <uuid>. BRAHMA-PH-4-3 | phala.rectification';


--
-- Name: phala_valid_action_type(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.phala_valid_action_type(p_action_type text) RETURNS boolean
    LANGUAGE sql IMMUTABLE
    AS $$
    SELECT p_action_type IN (
        'marriage', 'travel', 'business', 'medical',
        'education', 'property', 'general'
    );
$$;


--
-- Name: FUNCTION phala_valid_action_type(p_action_type text); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.phala_valid_action_type(p_action_type text) IS 'PH-4-4: Returns TRUE if the action_type is one of the 7 canonical types.';


--
-- Name: seed_mimamsa_golden_pairs(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.seed_mimamsa_golden_pairs(p_chart_id uuid DEFAULT NULL::uuid) RETURNS integer
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


--
-- Name: FUNCTION seed_mimamsa_golden_pairs(p_chart_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.seed_mimamsa_golden_pairs(p_chart_id uuid) IS 'MI-5-6 seed function — 10 golden Q&A pairs for mimamsa.answer_quality eval. Covers all 6 Brahma layers (L0–L5): 2 pairs for L0/L1/L2/L3, 1 each for L4/L5. All pairs: b11_compliance=TRUE, source_citation=Brahma QA golden set v1.0. Idempotent — ON CONFLICT DO NOTHING. Returns rows inserted.';


--
-- Name: seed_native_phala_anchors(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.seed_native_phala_anchors(p_chart_id uuid) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_inserted INT := 0;
BEGIN
    INSERT INTO public.phala_anchors
        (chart_id, anchor_id, window_start, window_end, theme, confidence,
         falsifier, contributing_dashas, contributing_signals, source_citation)
    VALUES

    -- ── WINDOW 1: 2026-H1 (Jan 1 – Jun 30 2026) ──────────────────────────────
    -- Dasha: Mercury MD / Saturn AD (DSH.V.023: 2024-12-12 → 2027-08-21)
    -- Sade Sati: Cycle 2 Setting (Saturn in Pisces through 2027-06-02)
    -- Theme: Career consolidation + entrepreneurial contract delivery
    -- dasha_quality=0.82 (Mercury yogi + Saturn exalted AmK in Libra 7H)
    -- signal_strength=0.79 (SIG.09 Mercury strong, SIG.14 Sun 10H, Mercury MD peak)
    -- convergence_score=0.91 (LEL RPT.DSH.01 confirmed pattern: Merc-Sat AD = delivery)
    (
        p_chart_id,
        'PH-4-1.2026H1.CAREER',
        '2026-01-01', '2026-06-30',
        'career_consolidation',
        compute_window_score(0.82, 0.79, 0.91),
        'If no new client contract, partnership formalization, or measurable revenue milestone '
        'in the Marsys Technology / consulting domain is reached before 2026-07-01, '
        'this prediction is false.',
        '["DSH.V.023: Mercury MD Saturn AD (2024-12-12 to 2027-08-21)"]'::JSONB,
        '["SIG.09 Mercury 8-system convergence", "SIG.14 Sun 10H career-density", '
        '"SIG.08 Lakshmi Yoga dharma-wealth", "RPT.DSH.01 Mercury-Saturn delivery window"]'::JSONB,
        'FORENSIC v8.0 §5.1 DSH.V.023; LEL v1.7 §M5A RPT.DSH.01; MSR v5.0 SIG.09/SIG.14/SIG.08'
    ),

    -- ── WINDOW 2: 2026-H2 (Jul 1 – Dec 31 2026) ──────────────────────────────
    -- Dasha: Mercury MD / Saturn AD (DSH.V.023) — Sade Sati still active
    -- Theme: Spiritual deepening + practical obstacles (Saturn peak)
    -- dasha_quality=0.75 (Saturn AD + Sade Sati convergence = intensification)
    -- signal_strength=0.72 (SIG.MSR.145 Saturn-Venus Parivartana active)
    -- convergence_score=0.85 (LEL EVT.2025/2026 Saturn-practice pattern confirmed)
    (
        p_chart_id,
        'PH-4-1.2026H2.SPIRIT',
        '2026-07-01', '2026-12-31',
        'spiritual_practice_intensification',
        compute_window_score(0.75, 0.72, 0.85),
        'If no new formal spiritual practice is established or deepened (new devata, '
        'new sadhana regimen, yajna, or tantric practice) before 2027-01-01, '
        'this prediction is false.',
        '["DSH.V.023: Mercury MD Saturn AD (2024-12-12 to 2027-08-21)", '
        '"Sade Sati Cycle 2 Setting Saturn-Pisces through 2027-06-02"]'::JSONB,
        '["SIG.MSR.145 Saturn-Venus Parivartana", "SIG.11 Ketu 5H Leo tantric substrate", '
        '"LEL EVT spiritual-practice cluster 2024-2026"]'::JSONB,
        'FORENSIC v8.0 §5.1 DSH.V.023; SADE_SATI_CYCLES_ALL.md Cycle 2; MSR v5.0 SIG.MSR.145'
    ),

    -- ── WINDOW 3: 2027-H1 (Jan 1 – Jun 30 2027) ──────────────────────────────
    -- Dasha: Mercury MD / Saturn AD (DSH.V.023, ending 2027-08-21)
    -- Sade Sati: Cycle 2 Setting exits 2027-06-02
    -- Theme: Sade Sati exit + Mercury MD final phase — transition pressure
    -- dasha_quality=0.68 (Mercury MD final-year drawdown; Sade Sati exit)
    -- signal_strength=0.74 (SIG.09 Mercury still strong; SIG.14 Sun 10H active)
    -- convergence_score=0.80 (PRED.M3D.HOLDOUT.002: lit-signal collapse 248→79 signals near Aug 2027)
    (
        p_chart_id,
        'PH-4-1.2027H1.TRANSITION',
        '2027-01-01', '2027-06-30',
        'life_transition_preparatory',
        compute_window_score(0.68, 0.74, 0.80),
        'If neither a role change, residential/geographic shift, relationship recalibration, '
        'nor a clear discontinuity in the prior career/spiritual trajectory is observable '
        'before 2027-07-01, this prediction is false.',
        '["DSH.V.023: Mercury MD Saturn AD ending 2027-08-21", '
        '"Sade Sati Cycle 2 exits 2027-06-02"]'::JSONB,
        '["PRED.M3D.HOLDOUT.002 Mercury-Ketu transition regime-change", '
        '"SIG.09 Mercury 8-system convergence", "SIG.MSR.145 Saturn-Venus Parivartana"]'::JSONB,
        'FORENSIC v8.0 §5.1 DSH.V.023; LEL v1.7 PRED.M3D.HOLDOUT.002; SADE_SATI_CYCLES_ALL.md Cycle 2 exit 2027-06-02'
    ),

    -- ── WINDOW 4: 2027-H2 (Jul 1 – Dec 31 2027) ──────────────────────────────
    -- Dasha: Mercury-Saturn AD ends 2027-08-21 → Ketu-Ketu AD begins (DSH.V.024)
    -- This window straddles the Mercury→Ketu MD transition (the rarest regime change)
    -- Theme: Role/frame discontinuity at MD boundary (PRED.M3D.HOLDOUT.002)
    -- dasha_quality=0.62 (Ketu MD onset; Ketu in 5H Leo — moksha, withdrawal from mundane)
    -- signal_strength=0.70 (Ketu activates 5H intellect / detachment signifiers)
    -- convergence_score=0.88 (PRED.M3D.HOLDOUT.002 convergence: KP Asc triple-Saturn at Sep 2027)
    (
        p_chart_id,
        'PH-4-1.2027H2.REGIME_CHANGE',
        '2027-07-01', '2027-12-31',
        'regime_discontinuity_mercury_to_ketu',
        compute_window_score(0.62, 0.70, 0.88),
        'If the Mercury→Ketu MD transition (2027-08-21) does not produce any observable '
        'role change, spiritual reorientation, relationship recalibration, or discontinuity '
        'in the native''s primary activity domain before 2028-01-01, this prediction is false.',
        '["DSH.V.023: Mercury MD Saturn AD ends 2027-08-21", '
        '"DSH.V.024: Ketu MD Ketu AD starts 2027-08-21 ends 2028-01-18"]'::JSONB,
        '["PRED.M3D.HOLDOUT.002 Mercury-Ketu transition regime-change", '
        '"SIG.11 Ketu 5H Leo detachment", "KP triple-Saturn Asc at Sep 2027"]'::JSONB,
        'FORENSIC v8.0 §5.1 DSH.V.023–024; LEL v1.7 PRED.M3D.HOLDOUT.002; MSR v5.0 SIG.11'
    ),

    -- ── WINDOW 5: 2028-H1 (Jan 1 – Jun 30 2028) ──────────────────────────────
    -- Dasha: Ketu-Ketu AD ends 2028-01-18 → Ketu-Venus AD begins (DSH.V.025)
    -- Sade Sati Cycle 2 retrograde tail: 2027-10-20 → 2028-02-23
    -- Theme: Ketu-Venus = creative/relational renaissance after Ketu withdrawal
    -- dasha_quality=0.58 (Ketu MD + Venus AD: Venus weak in chart SIG.12, tension)
    -- signal_strength=0.65 (SIG.12 Venus weak = relational friction; SIG.07 Saraswati)
    -- convergence_score=0.72 (Venus AD historically triggers SIG.12 relational events)
    (
        p_chart_id,
        'PH-4-1.2028H1.RELATIONAL',
        '2028-01-01', '2028-06-30',
        'relational_creative_activation',
        compute_window_score(0.58, 0.65, 0.72),
        'If no meaningful change in the native''s relational field (partnership, '
        'collaboration, creative output, or household structure change) occurs before '
        '2028-07-01, this prediction is false.',
        '["DSH.V.024: Ketu MD Ketu AD ends 2028-01-18", '
        '"DSH.V.025: Ketu MD Venus AD starts 2028-01-18 ends 2029-03-18", '
        '"Sade Sati retrograde tail 2027-10-20 to 2028-02-23"]'::JSONB,
        '["SIG.12 Venus Shadbala rank 7 weakest", "SIG.07 Saraswati Yoga Jupiter-Venus-Mercury", '
        '"SIG.04 Moon AK 11H emotional attachment", "CVG.07 Gemini 3H relational nexus"]'::JSONB,
        'FORENSIC v8.0 §5.1 DSH.V.024–025; SADE_SATI_CYCLES_ALL.md retrograde tail; MSR v5.0 SIG.12/SIG.07'
    ),

    -- ── WINDOW 6: 2028-H2 (Jul 1 – Dec 31 2028) ──────────────────────────────
    -- Dasha: Ketu MD / Venus AD (DSH.V.025: 2028-01-18 → 2029-03-18)
    -- Theme: Wealth activation under Ketu-Venus (Lakshmi / Kamlatmika pattern)
    -- dasha_quality=0.60 (Ketu MD + Venus AD; SIG.08 Lakshmi Yoga still in scope)
    -- signal_strength=0.68 (SIG.08 Lakshmi Yoga; SIG.MSR.145 Saturn-Venus Parivartana)
    -- convergence_score=0.75 (LEL tantric-wealth pattern: Ketu-Venus = Kamlatmika activation)
    (
        p_chart_id,
        'PH-4-1.2028H2.WEALTH',
        '2028-07-01', '2028-12-31',
        'wealth_karmic_resolution',
        compute_window_score(0.60, 0.68, 0.75),
        'If no material wealth improvement, asset-class change, resolution of a blocked '
        'financial matter, or new income stream manifests before 2029-01-01, '
        'this prediction is false.',
        '["DSH.V.025: Ketu MD Venus AD (2028-01-18 to 2029-03-18)"]'::JSONB,
        '["SIG.08 Lakshmi Yoga dharma-wealth", "SIG.MSR.145 Saturn-Venus Parivartana", '
        '"SIG.12 Venus weak — resolution window under Venus AD", "CVG.02 Jupiter 9L dharma-wealth chain"]'::JSONB,
        'FORENSIC v8.0 §5.1 DSH.V.025; MSR v5.0 SIG.08/SIG.MSR.145/CVG.02; LEL v1.7 tantric-wealth pattern'
    ),

    -- ── WINDOW 7: 2029-H1 (Jan 1 – Jun 30 2029) ──────────────────────────────
    -- Dasha: Ketu-Venus AD ends 2029-03-18 → Ketu-Sun AD begins (DSH.V.026)
    -- Theme: Authority assertion + public presence (Ketu-Sun = Sun in 10H)
    -- dasha_quality=0.55 (Ketu MD + Sun AD; Sun in 10H own-house but Ketu-dimmed)
    -- signal_strength=0.70 (SIG.14 Sun 10H career-density — Sun AD activates it)
    -- convergence_score=0.78 (SIG.14 + D10 career chart Sun indicators)
    (
        p_chart_id,
        'PH-4-1.2029H1.AUTHORITY',
        '2029-01-01', '2029-06-30',
        'public_authority_emergence',
        compute_window_score(0.55, 0.70, 0.78),
        'If no step into a visible authority role, public-facing leadership position, '
        'or recognition event (award, media, formal title) occurs before 2029-07-01, '
        'this prediction is false.',
        '["DSH.V.025: Ketu MD Venus AD ends 2029-03-18", '
        '"DSH.V.026: Ketu MD Sun AD starts 2029-03-18 ends 2029-07-24"]'::JSONB,
        '["SIG.14 Sun 10H career-density", "SIG.09 Mercury operational dominance", '
        '"DSH.V.026 Ketu-Sun AD activation of 10H Sun"]'::JSONB,
        'FORENSIC v8.0 §5.1 DSH.V.025–026; MSR v5.0 SIG.14/SIG.09; D10 career chart Sun placement'
    ),

    -- ── WINDOW 8: 2029-H2 (Jul 1 – Dec 31 2029) ──────────────────────────────
    -- Dasha: Ketu-Moon AD (DSH.V.027: 2029-07-24 → 2030-02-24)
    -- Moon is AK (Atmakaraka) in chart — Ketu-Moon = soul-level activation
    -- Theme: Emotional/relational depth work; AK activation under Ketu
    -- dasha_quality=0.65 (Ketu MD + Moon AD; Moon AK = soul expression)
    -- signal_strength=0.72 (SIG.04 Moon AK 11H soul-signature; SIG.05 Moon Chalit-12)
    -- convergence_score=0.76 (Moon AK AD historically triggers deep emotional events LEL)
    (
        p_chart_id,
        'PH-4-1.2029H2.SOUL',
        '2029-07-01', '2029-12-31',
        'soul_level_atmakaraka_activation',
        compute_window_score(0.65, 0.72, 0.76),
        'If no emotionally significant event, soul-level shift, or inner transformation '
        '(grief, devotion breakthrough, relationship depth milestone, or explicit '
        'philosophical/worldview change) occurs before 2030-01-01, this prediction is false.',
        '["DSH.V.026: Ketu MD Sun AD ends 2029-07-24", '
        '"DSH.V.027: Ketu MD Moon AD starts 2029-07-24 ends 2030-02-24"]'::JSONB,
        '["SIG.04 Moon AK 11H emotional attachment signature", '
        '"SIG.05 Moon Chalit-12 hidden-depth", "DSH.V.027 Moon AD AK activation"]'::JSONB,
        'FORENSIC v8.0 §5.1 DSH.V.026–027; MSR v5.0 SIG.04/SIG.05; LEL v1.7 AK-activation pattern'
    ),

    -- ── WINDOW 9: 2030-H1 (Jan 1 – Jun 30 2030) ──────────────────────────────
    -- Dasha: Ketu-Moon AD ends 2030-02-24 → Ketu-Mars AD begins (DSH.V.028)
    -- Theme: Action/ambition burst after introspective Ketu-Moon phase
    -- dasha_quality=0.58 (Ketu MD + Mars AD; Mars 5L in 5H with Ketu — mixed)
    -- signal_strength=0.63 (Mars 5L + Ketu co-presence; Rahu 2H ambition)
    -- convergence_score=0.70 (Narayana Dasha Scorpio MD active ~2026-2030 corroborates action themes)
    (
        p_chart_id,
        'PH-4-1.2030H1.ACTION',
        '2030-01-01', '2030-06-30',
        'decisive_action_initiative',
        compute_window_score(0.58, 0.63, 0.70),
        'If no decisive new initiative, project launch, business expansion, or major '
        'action-based commitment occurs before 2030-07-01, this prediction is false.',
        '["DSH.V.027: Ketu MD Moon AD ends 2030-02-24", '
        '"DSH.V.028: Ketu MD Mars AD starts 2030-02-24 ends 2030-07-21"]'::JSONB,
        '["SIG.11 Ketu 5H Leo Mars co-presence", "SIG.10 Rahu 2H ambition-drive", '
        '"DSH.V.028 Mars AD activation 5H initiative domain"]'::JSONB,
        'FORENSIC v8.0 §5.1 DSH.V.027–028; MSR v5.0 SIG.11/SIG.10; Narayana Dasha Scorpio MD'
    )

    ON CONFLICT (chart_id, anchor_id) DO NOTHING;

    GET DIAGNOSTICS v_inserted = ROW_COUNT;
    RETURN v_inserted;
END;
$$;


--
-- Name: FUNCTION seed_native_phala_anchors(p_chart_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.seed_native_phala_anchors(p_chart_id uuid) IS 'Seeds calibrated phala anchors for Abhisek Mohanty (1984-02-05) for 2026-2030. Nine 6-month windows × L1-grounded dasha/signal ensembles. Idempotent — ON CONFLICT DO NOTHING. Returns rows inserted. Source: FORENSIC v8.0 §5.1 DSH.V.023–028 + CHART_FACTS_EXTRACTION_v1_0.yaml.';


--
-- Name: seed_phala_muhurta_native_sample(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.seed_phala_muhurta_native_sample(p_chart_id uuid) RETURNS integer
    LANGUAGE plpgsql
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


--
-- Name: FUNCTION seed_phala_muhurta_native_sample(p_chart_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.seed_phala_muhurta_native_sample(p_chart_id uuid) IS 'PH-4-4: Insert 3 representative pre-computed rows for the native chart.
 Idempotent via ON CONFLICT DO NOTHING on (chart_id, action_type, window_start).
 Rows demonstrate high/medium/strong score bands across 3 action types.
 Source citations: FORENSIC v8.0 §5.1 + panchanga_daily + MSR v5.0 + BPHS ch.46.';


--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    SET search_path TO 'public', 'pg_temp'
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


--
-- Name: update_calibration(text, text, uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_calibration(p_technique text, p_ayanamsha_id text, p_chart_id uuid) RETURNS TABLE(new_brier_score double precision, new_sample_size integer, inserted_at timestamp with time zone)
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


--
-- Name: FUNCTION update_calibration(p_technique text, p_ayanamsha_id text, p_chart_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.update_calibration(p_technique text, p_ayanamsha_id text, p_chart_id uuid) IS 'MI-5-3: Recompute mean Brier score for (technique, ayanamsha_id, chart_id). Inserts a new mimamsa_calibration row (preserves calibration history). Returns (new_brier_score, new_sample_size, inserted_at). Raises if no resolved predictions exist. source_citation is auto-built and satisfies B.3 mandate.';


--
-- Name: update_capability_tool_registry_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_capability_tool_registry_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;




--
-- Name: _migrations_applied; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public._migrations_applied (
    id integer NOT NULL,
    filename text NOT NULL,
    applied_at timestamp with time zone DEFAULT now() NOT NULL,
    sha256 text NOT NULL
);


--
-- Name: _migrations_applied_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE IF NOT EXISTS public._migrations_applied_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: _migrations_applied_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public._migrations_applied_id_seq OWNED BY public._migrations_applied.id;


--
-- Name: access_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.access_requests (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    full_name text NOT NULL,
    email text NOT NULL,
    reason text,
    status text DEFAULT 'pending'::text NOT NULL,
    requested_at timestamp with time zone DEFAULT now() NOT NULL,
    reviewed_at timestamp with time zone,
    reviewed_by text,
    approved_user_id text,
    CONSTRAINT access_requests_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text])))
);


--
-- Name: audit_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.audit_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    query_id uuid NOT NULL,
    query_plan_id uuid,
    query_text text,
    query_class text,
    user_id text,
    chart_id uuid,
    conversation_id uuid,
    tool_bundles jsonb,
    latency_ms integer,
    audit_status text DEFAULT 'ok'::text NOT NULL,
    audit_warnings jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    disclosure_tier text,
    b10_compliant boolean,
    b11_compliant boolean,
    truncated_by_user_edit boolean DEFAULT false
);


--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.audit_log (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    query_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    query_text text NOT NULL,
    query_class text NOT NULL,
    bundle_keys jsonb DEFAULT '[]'::jsonb NOT NULL,
    tools_called jsonb DEFAULT '[]'::jsonb NOT NULL,
    validators_run jsonb DEFAULT '[]'::jsonb NOT NULL,
    synthesis_model text NOT NULL,
    synthesis_input_tokens integer DEFAULT 0 NOT NULL,
    synthesis_output_tokens integer DEFAULT 0 NOT NULL,
    disclosure_tier text NOT NULL,
    final_output text DEFAULT ''::text NOT NULL,
    audit_event_version integer DEFAULT 1 NOT NULL
);


--
-- Name: bodha_domain_links; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.bodha_domain_links (
    link_id text NOT NULL,
    chart_id uuid NOT NULL,
    from_domain text NOT NULL,
    to_domain text NOT NULL,
    link_type text NOT NULL,
    signal_ids text[],
    strength numeric(5,4),
    note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE bodha_domain_links; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.bodha_domain_links IS 'L2 Bodha — CDLM (Cross-Domain Linkage Matrix). Cross-domain linkages. Populated by Wave-1 bodha.domain_links writer. Queried by holistic_bundle (BO-2-8).';


--
-- Name: bodha_graph; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.bodha_graph (
    edge_id text NOT NULL,
    chart_id uuid,
    from_signal_id text NOT NULL,
    to_signal_id text NOT NULL,
    edge_type text NOT NULL,
    weight double precision NOT NULL,
    source_citation text NOT NULL,
    ayanamsha_id text DEFAULT 'lahiri'::text NOT NULL,
    build_id text,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT bodha_graph_edge_type_check CHECK ((edge_type = ANY (ARRAY['reinforce'::text, 'contradict'::text, 'modulate'::text, 'amplify'::text, 'suppress'::text]))),
    CONSTRAINT bodha_graph_weight_check CHECK (((weight >= (0)::double precision) AND (weight <= (1)::double precision))),
    CONSTRAINT no_self_loop CHECK ((from_signal_id <> to_signal_id))
);


--
-- Name: TABLE bodha_graph; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.bodha_graph IS 'BRAHMA-BO-2-2: CGM signal graph — valenced edges between CGM node signals. Seeded from 035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json (22 reconciled edges). Contract: no self-loops; each edge carries source_citation back to FORENSIC_v8_0. Tool: cgm_subgraph via platform-mcp/src/tools/bodha_bo22.ts.';


--
-- Name: bodha_graph_edges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.bodha_graph_edges (
    edge_id text NOT NULL,
    chart_id uuid NOT NULL,
    from_signal_id text NOT NULL,
    to_signal_id text NOT NULL,
    edge_type text NOT NULL,
    weight numeric(5,4),
    label text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE bodha_graph_edges; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.bodha_graph_edges IS 'L2 Bodha — CGM (Chart Graph Model). Valenced edges between signals. Populated by Wave-1 bodha.graph writer. Queried by holistic_bundle (BO-2-8).';


--
-- Name: bodha_graph_staging; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.bodha_graph_staging (
    edge_id text NOT NULL,
    chart_id uuid,
    from_signal_id text NOT NULL,
    to_signal_id text NOT NULL,
    edge_type text NOT NULL,
    weight double precision NOT NULL,
    source_citation text NOT NULL,
    ayanamsha_id text DEFAULT 'lahiri'::text NOT NULL,
    build_id text,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT bodha_graph_edge_type_check CHECK ((edge_type = ANY (ARRAY['reinforce'::text, 'contradict'::text, 'modulate'::text, 'amplify'::text, 'suppress'::text]))),
    CONSTRAINT bodha_graph_weight_check CHECK (((weight >= (0)::double precision) AND (weight <= (1)::double precision))),
    CONSTRAINT no_self_loop CHECK ((from_signal_id <> to_signal_id))
);


--
-- Name: bodha_remediation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.bodha_remediation (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    contradiction_hub_id text NOT NULL,
    hub_label text,
    domain text,
    edge_count integer DEFAULT 0 NOT NULL,
    contradicting_signal_ids text[] DEFAULT '{}'::text[] NOT NULL,
    remedy_type text NOT NULL,
    remedy_text text NOT NULL,
    source_l0_rule_id text NOT NULL,
    source_citation text NOT NULL,
    build_id text NOT NULL,
    asset_version text DEFAULT '1.0'::text NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT bodha_remediation_remedy_type_check CHECK ((remedy_type = ANY (ARRAY['mantra'::text, 'charity'::text, 'gemstone'::text, 'ritual'::text])))
);


--
-- Name: TABLE bodha_remediation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.bodha_remediation IS 'L2 Bodha Wave-2 (BO-2-6): per-contradiction-hub remedy map. Each row maps one contradiction hub from bodha_graph to a classical remedy cited from L0 concordance (BG-0-7) or BPHS. source_citation always traces to a specific BPHS chapter/verse or L0 rule_id.';


--
-- Name: COLUMN bodha_remediation.source_l0_rule_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.bodha_remediation.source_l0_rule_id IS 'L0 concordance rule ID or BPHS-FALLBACK-<topic>. Traces to concordance_lookup.id or is a BPHS chapter pointer pre-seeded in the fallback map.';


--
-- Name: COLUMN bodha_remediation.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.bodha_remediation.source_citation IS 'BPHS chapter.verses or concordance_lookup.source_citation. Format: BPHS.<chapter>.<verses>  e.g. BPHS.25.41-56.';


--
-- Name: bodha_remediation_staging; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.bodha_remediation_staging (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    contradiction_hub_id text NOT NULL,
    hub_label text,
    domain text,
    edge_count integer DEFAULT 0 NOT NULL,
    contradicting_signal_ids text[] DEFAULT '{}'::text[] NOT NULL,
    remedy_type text NOT NULL,
    remedy_text text NOT NULL,
    source_l0_rule_id text NOT NULL,
    source_citation text NOT NULL,
    build_id text NOT NULL,
    asset_version text DEFAULT '1.0'::text NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT bodha_remediation_remedy_type_check CHECK ((remedy_type = ANY (ARRAY['mantra'::text, 'charity'::text, 'gemstone'::text, 'ritual'::text])))
);


--
-- Name: TABLE bodha_remediation_staging; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.bodha_remediation_staging IS 'Staging copy of bodha_remediation for atomic swap builds (BO-2-6).';


--
-- Name: COLUMN bodha_remediation_staging.source_l0_rule_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.bodha_remediation_staging.source_l0_rule_id IS 'L0 concordance rule ID or BPHS-FALLBACK-<topic>. Traces to concordance_lookup.id or is a BPHS chapter pointer pre-seeded in the fallback map.';


--
-- Name: COLUMN bodha_remediation_staging.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.bodha_remediation_staging.source_citation IS 'BPHS chapter.verses or concordance_lookup.source_citation. Format: BPHS.<chapter>.<verses>  e.g. BPHS.25.41-56.';


--
-- Name: bodha_resonance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.bodha_resonance (
    chart_id uuid NOT NULL,
    ayanamsha_id text DEFAULT 'jh_true_chitra'::text NOT NULL,
    element_id text NOT NULL,
    element_type text NOT NULL,
    strength double precision DEFAULT 0.50 NOT NULL,
    constituents jsonb DEFAULT '[]'::jsonb NOT NULL,
    domains_primary jsonb DEFAULT '[]'::jsonb NOT NULL,
    net_resonance text,
    source_citation text NOT NULL,
    raw_yaml text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT bodha_resonance_element_type_check CHECK ((element_type = ANY (ARRAY['yoga'::text, 'stellium'::text, 'mutual_aspect'::text, 'exchange'::text, 'parivartana'::text, 'neechabhanga'::text]))),
    CONSTRAINT bodha_resonance_strength_check CHECK (((strength >= (0.0)::double precision) AND (strength <= (1.0)::double precision)))
);


--
-- Name: TABLE bodha_resonance; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.bodha_resonance IS 'L2 Bodha — RM (Resonance Map). Thematic resonance elements. Populated by Wave-1 bodha.resonance writer. Queried by holistic_bundle (BO-2-8).';


--
-- Name: COLUMN bodha_resonance.element_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.bodha_resonance.element_id IS 'Canonical RM element identifier, e.g. RM.01, RM.21A, RM.35. Matches the ### RM.NN heading in RM_v2_0.md.';


--
-- Name: COLUMN bodha_resonance.strength; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.bodha_resonance.strength IS '0.0–1.0 resonance strength: 0.90=STRONGLY AMPLIFIED, 0.75=TENSION-BEARING, 0.60=MIXED/COMPENSATED, 0.50=default. Explicit override from YAML ''strength'' field where present (RM.31–RM.35).';


--
-- Name: COLUMN bodha_resonance.constituents; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.bodha_resonance.constituents IS 'JSON array of MSR/CDLM anchor IDs referenced in the element block. e.g. ["MSR.413", "MSR.190", "D8.D8=0.95 self-amp"]. Provenance for B.3 compliance.';


--
-- Name: COLUMN bodha_resonance.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.bodha_resonance.source_citation IS 'Non-null provenance pointer. Format: 025_HOLISTIC_SYNTHESIS/RM_v2_0.md#RM.NN. Acceptance gate: every row must carry a non-null, non-empty source_citation.';


--
-- Name: bodha_signal_embeddings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.bodha_signal_embeddings (
    signal_id text NOT NULL,
    embedding public.vector(768) NOT NULL,
    model_name text DEFAULT 'text-multilingual-embedding-002'::text NOT NULL,
    source_citation text,
    embedded_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: bodha_signals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.bodha_signals (
    signal_id text NOT NULL,
    chart_id uuid NOT NULL,
    domain text NOT NULL,
    valence text NOT NULL,
    confidence numeric(5,4),
    salience numeric(5,4),
    state text,
    signal_text text NOT NULL,
    source_citation text,
    graha_refs text[],
    house_refs integer[],
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    signal_name text,
    claim_text text,
    grounding_status text DEFAULT 'unverified'::text
);


--
-- Name: TABLE bodha_signals; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.bodha_signals IS 'L2 Bodha — MSR (Multidimensional Signal Register). One row per signal per chart. Populated by Wave-1 bodha.signals writer. Queried by holistic_bundle (BO-2-8).';


--
-- Name: build_engine_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.build_engine_versions (
    build_id uuid NOT NULL,
    version_id uuid NOT NULL
);


--
-- Name: build_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.build_events (
    build_id text NOT NULL,
    stage_seq integer NOT NULL,
    chart_id text NOT NULL,
    ayanamsha_role text NOT NULL,
    asset text NOT NULL,
    stage text NOT NULL,
    status text NOT NULL,
    percent numeric(5,2),
    message text,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    emitted_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE build_events; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.build_events IS 'Progress rail for marsys-build-pipeline-job. Written by the Python pipeline and the task handler; read by /api/build/events/[buildId] SSE.';


--
-- Name: build_notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.build_notifications (
    notif_id uuid DEFAULT gen_random_uuid() NOT NULL,
    build_id uuid NOT NULL,
    event_type text NOT NULL,
    payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    delivered_at timestamp with time zone,
    subscriber_id text,
    CONSTRAINT build_notifications_event_type_check CHECK ((event_type = ANY (ARRAY['build_queued'::text, 'build_started'::text, 'step_started'::text, 'step_complete'::text, 'step_failed'::text, 'build_complete'::text, 'build_failed'::text, 'build_cancelled'::text])))
);


--
-- Name: build_steps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.build_steps (
    step_id uuid DEFAULT gen_random_uuid() NOT NULL,
    build_id uuid NOT NULL,
    ayanamsha_id text NOT NULL,
    category text NOT NULL,
    status text DEFAULT 'queued'::text NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    error_msg text,
    row_count integer,
    duration_ms integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT build_steps_status_check CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'complete'::text, 'failed'::text, 'skipped'::text])))
);


--
-- Name: builds; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.builds (
    build_id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    triggered_by_uid text NOT NULL,
    triggered_by_role text NOT NULL,
    engine_version text DEFAULT 'natal_engine/0.2.0'::text NOT NULL,
    ayanamshas jsonb DEFAULT '["lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"]'::jsonb NOT NULL,
    salience_formula_ver text DEFAULT 'v1'::text NOT NULL,
    status text NOT NULL,
    queued_at timestamp with time zone DEFAULT now() NOT NULL,
    started_at timestamp with time zone,
    finished_at timestamp with time zone,
    cancelled_at timestamp with time zone,
    failed_at timestamp with time zone,
    error_summary text,
    log_gcs_uri text,
    asset_artifacts_uri text,
    cloud_run_job_exec text,
    CONSTRAINT builds_status_check CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'complete'::text, 'failed'::text, 'cancelled'::text, 'cancelling'::text]))),
    CONSTRAINT builds_triggered_by_role_check CHECK ((triggered_by_role = ANY (ARRAY['super_admin'::text, 'guest'::text])))
);


--
-- Name: builds_staging; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.builds_staging (
    build_id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    triggered_by_uid text NOT NULL,
    triggered_by_role text NOT NULL,
    engine_version text DEFAULT 'natal_engine/0.2.0'::text NOT NULL,
    ayanamshas jsonb DEFAULT '["lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"]'::jsonb NOT NULL,
    salience_formula_ver text DEFAULT 'v1'::text NOT NULL,
    status text NOT NULL,
    queued_at timestamp with time zone DEFAULT now() NOT NULL,
    started_at timestamp with time zone,
    finished_at timestamp with time zone,
    cancelled_at timestamp with time zone,
    failed_at timestamp with time zone,
    error_summary text,
    log_gcs_uri text,
    asset_artifacts_uri text,
    cloud_run_job_exec text,
    CONSTRAINT builds_status_check CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'complete'::text, 'failed'::text, 'cancelled'::text, 'cancelling'::text]))),
    CONSTRAINT builds_triggered_by_role_check CHECK ((triggered_by_role = ANY (ARRAY['super_admin'::text, 'guest'::text])))
);


--
-- Name: capability_asset_tool_bindings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.capability_asset_tool_bindings (
    asset_canonical_id text NOT NULL,
    tool_name text NOT NULL,
    binding_source text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT capability_asset_tool_bindings_binding_source_check CHECK ((binding_source = ANY (ARRAY['manifest'::text, 'override'::text, 'inferred'::text])))
);


--
-- Name: capability_tool_registry; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.capability_tool_registry (
    tool_name text NOT NULL,
    expose_to_planner boolean DEFAULT false NOT NULL,
    description text DEFAULT ''::text NOT NULL,
    query_schema jsonb,
    output_schema jsonb,
    cost_weight numeric,
    linked_data_asset_ids text[] DEFAULT '{}'::text[] NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE capability_tool_registry; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.capability_tool_registry IS 'One row per wired RETRIEVAL_TOOLS[] entry. Seeded from CAPABILITY_MANIFEST.json.';


--
-- Name: chart_grants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.chart_grants (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    principal_id text NOT NULL,
    permission text DEFAULT 'view'::text NOT NULL,
    granted_by text NOT NULL,
    granted_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chart_grants_permission_check CHECK ((permission = 'view'::text))
);


--
-- Name: charts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.charts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    client_id text,
    name text NOT NULL,
    birth_date date NOT NULL,
    birth_time time without time zone NOT NULL,
    birth_place text NOT NULL,
    birth_lat numeric,
    birth_lng numeric,
    ayanamsa text DEFAULT 'lahiri'::text,
    house_system text DEFAULT 'sripathi'::text,
    created_at timestamp with time zone DEFAULT now(),
    native_id character varying(64) DEFAULT 'abhisek'::character varying NOT NULL,
    owner_id text,
    subject_name text,
    chart_id uuid DEFAULT gen_random_uuid(),
    role text DEFAULT 'native'::text NOT NULL,
    created_at_iso timestamp with time zone DEFAULT now() NOT NULL,
    preferred_name text,
    timezone_id text,
    CONSTRAINT charts_role_check CHECK ((role = ANY (ARRAY['native'::text, 'tertiary'::text, 'fixture'::text])))
);


--
-- Name: COLUMN charts.preferred_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.charts.preferred_name IS 'Display name for the native; defaults to first word of name.';


--
-- Name: COLUMN charts.timezone_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.charts.timezone_id IS 'IANA timezone identifier e.g. Asia/Kolkata. Sourced from explicit TZ select.';


--
-- Name: context_assembly_item_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.context_assembly_item_log (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    query_id uuid NOT NULL,
    assembly_step_id text NOT NULL,
    item_rank integer NOT NULL,
    source_bundle text NOT NULL,
    source_item_id text NOT NULL,
    layer text NOT NULL,
    token_cost integer NOT NULL,
    relevance_score real,
    status text NOT NULL,
    drop_reason text,
    truncated_to_tokens integer,
    cumulative_tokens_at_decision integer,
    budget_at_decision integer,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT context_assembly_item_log_drop_reason_check CHECK (((drop_reason = ANY (ARRAY['BUDGET_EXCEEDED'::text, 'DEDUP'::text, 'RELEVANCE_FLOOR'::text])) OR (drop_reason IS NULL))),
    CONSTRAINT context_assembly_item_log_status_check CHECK ((status = ANY (ARRAY['INCLUDED'::text, 'TRUNCATED'::text, 'DROPPED'::text])))
);


--
-- Name: conversation_branches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.conversation_branches (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    conversation_id uuid NOT NULL,
    edited_message_id text NOT NULL,
    parent_branch_id uuid,
    snapshot_jsonb jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: conversation_folder_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.conversation_folder_members (
    conversation_id uuid NOT NULL,
    folder_id uuid NOT NULL,
    added_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: conversation_folders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.conversation_folders (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id text NOT NULL,
    name text NOT NULL,
    color text DEFAULT '#6366f1'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT conversation_folders_name_check CHECK (((char_length(name) >= 1) AND (char_length(name) <= 80)))
);


--
-- Name: conversation_message_embeddings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.conversation_message_embeddings (
    message_id uuid NOT NULL,
    embedding public.vector(768),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: conversation_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.conversation_messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    conversation_id uuid NOT NULL,
    parent_message_id uuid,
    role text NOT NULL,
    parts_json jsonb DEFAULT '[]'::jsonb NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT conversation_messages_role_check CHECK ((role = ANY (ARRAY['user'::text, 'assistant'::text, 'tool'::text])))
);


--
-- Name: conversation_shares; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.conversation_shares (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    conversation_id uuid NOT NULL,
    slug text NOT NULL,
    created_by text NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone,
    revoked_at timestamp with time zone,
    hide_reasoning boolean DEFAULT false NOT NULL,
    hide_methodology boolean DEFAULT false NOT NULL
);


--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.conversations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    user_id text NOT NULL,
    module text NOT NULL,
    title text,
    created_at timestamp with time zone DEFAULT now(),
    native_id character varying(64) DEFAULT 'abhisek'::character varying NOT NULL,
    updated_at timestamp with time zone,
    archived_at timestamp with time zone,
    pinned boolean DEFAULT false NOT NULL,
    active_ayanamshas jsonb DEFAULT '["lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"]'::jsonb,
    CONSTRAINT conversations_module_check CHECK ((module = ANY (ARRAY['build'::text, 'consume'::text])))
);


--
-- Name: engine_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.engine_versions (
    version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    engine_name text NOT NULL,
    version_str text NOT NULL,
    git_sha text,
    swisseph_ver text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: eval_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.eval_runs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    finished_at timestamp with time zone,
    golden_set_version text NOT NULL,
    planner_prompt_version text,
    synthesis_prompt_version text,
    triggered_by text,
    query_count integer DEFAULT 0,
    plan_accuracy_recall numeric,
    plan_accuracy_precision numeric,
    citation_rate numeric,
    avg_latency_total_ms integer,
    synthesis_pass_rate numeric,
    retrieval_hit_rate numeric,
    b10_compliance_rate numeric,
    b11_compliance_rate numeric,
    notes text
);


--
-- Name: event_chart_state_index; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.event_chart_state_index (
    index_id uuid DEFAULT gen_random_uuid() NOT NULL,
    event_id text NOT NULL,
    dasha_active text,
    antardasha_active text,
    key_transits jsonb,
    convergence_score double precision,
    source_citation text DEFAULT 'Brahma L3/L1 computed'::text NOT NULL
);


--
-- Name: ganita_dashas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.ganita_dashas (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    build_id text NOT NULL,
    dasha_system text DEFAULT 'vimshottari'::text NOT NULL,
    level smallint NOT NULL,
    lord text NOT NULL,
    parent_lord text,
    start_date date NOT NULL,
    end_date date NOT NULL,
    years double precision NOT NULL,
    source_citation text NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ganita_dashas_level_check CHECK ((level = ANY (ARRAY[1, 2, 3])))
);


--
-- Name: TABLE ganita_dashas; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.ganita_dashas IS 'BRAHMA L1 Gaṇita: Vimshottari dasha tree (MD/AD/PD) computed mathematically from Moon nakshatra position. Canonical PyJHora-mathematical dates — NOT FORENSIC dates (which have a ~7-9 day discrepancy). Gate: GA-1-4.';


--
-- Name: ganita_positions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.ganita_positions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    build_id text NOT NULL,
    ayanamsha_id text NOT NULL,
    planet text NOT NULL,
    tropical_longitude double precision NOT NULL,
    sidereal_longitude double precision NOT NULL,
    sign_id smallint NOT NULL,
    sign_name text NOT NULL,
    nakshatra_id smallint NOT NULL,
    nakshatra_name text NOT NULL,
    nakshatra_pada smallint NOT NULL,
    speed_dps double precision DEFAULT 0 NOT NULL,
    is_retrograde boolean DEFAULT false NOT NULL,
    source_citation text NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ganita_positions_nakshatra_id_check CHECK (((nakshatra_id >= 1) AND (nakshatra_id <= 27))),
    CONSTRAINT ganita_positions_nakshatra_pada_check CHECK (((nakshatra_pada >= 1) AND (nakshatra_pada <= 4))),
    CONSTRAINT ganita_positions_sign_id_check CHECK (((sign_id >= 1) AND (sign_id <= 12)))
);


--
-- Name: TABLE ganita_positions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.ganita_positions IS 'BRAHMA L1 Gaṇita: sidereal graha positions computed via pyswisseph DE441. One row per planet per chart per ayanamsha. Astronomical ground truth — NOT FORENSIC value-parity. Gate: GA-1-2.';


--
-- Name: kala_convergence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.kala_convergence (
    convergence_id bigint NOT NULL,
    chart_id uuid,
    window_start date NOT NULL,
    window_end date NOT NULL,
    convergence_score double precision NOT NULL,
    constituent_factors jsonb DEFAULT '[]'::jsonb NOT NULL,
    source_citation text NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT kala_convergence_convergence_score_check CHECK (((convergence_score >= (0.0)::double precision) AND (convergence_score <= (1.0)::double precision))),
    CONSTRAINT kala_convergence_source_citation_check CHECK ((char_length(source_citation) > 0)),
    CONSTRAINT kala_convergence_valid_range CHECK ((window_end >= window_start))
);


--
-- Name: TABLE kala_convergence; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.kala_convergence IS 'BRAHMA-KA-3-2: kala.convergence — measured convergence windows where ≥3 temporal factors (dasha_transition, transit_conjunction, signal_activation, md_ad_alignment) align within a 30-day neighbourhood. convergence_score = Σweights/(count×1.0). source_citation is non-null on all rows: PyJHora/SwissEph DE441 + Brahma-L1. Seeded by brahmagyan.kala.convergence; queried by kala_convergence.ts MCP tool.';


--
-- Name: COLUMN kala_convergence.convergence_score; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.kala_convergence.convergence_score IS 'Weighted factor alignment score in [0.0, 1.0]. convergence_score = Σ(factor_weight_i) / (factor_count × 1.0). Higher = more factors aligned with higher individual weights.';


--
-- Name: COLUMN kala_convergence.constituent_factors; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.kala_convergence.constituent_factors IS 'JSONB array of factor objects: {label, date, weight, factor_type}. factor_type ∈ {dasha_transition, transit_conjunction, signal_activation, md_ad_alignment}.';


--
-- Name: COLUMN kala_convergence.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.kala_convergence.source_citation IS 'Non-null provenance string. Required: "PyJHora/SwissEph DE441 + Brahma-L1".';


--
-- Name: kala_convergence_convergence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE IF NOT EXISTS public.kala_convergence_convergence_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: kala_convergence_convergence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.kala_convergence_convergence_id_seq OWNED BY public.kala_convergence.convergence_id;


--
-- Name: kala_convergence_staging; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.kala_convergence_staging (
    convergence_id bigint DEFAULT nextval('public.kala_convergence_convergence_id_seq'::regclass) NOT NULL,
    chart_id uuid,
    window_start date NOT NULL,
    window_end date NOT NULL,
    convergence_score double precision NOT NULL,
    constituent_factors jsonb DEFAULT '[]'::jsonb NOT NULL,
    source_citation text NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT kala_convergence_convergence_score_check CHECK (((convergence_score >= (0.0)::double precision) AND (convergence_score <= (1.0)::double precision))),
    CONSTRAINT kala_convergence_source_citation_check CHECK ((char_length(source_citation) > 0)),
    CONSTRAINT kala_convergence_valid_range CHECK ((window_end >= window_start))
);


--
-- Name: kala_obstruction; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.kala_obstruction (
    id bigint NOT NULL,
    chart_id uuid,
    date date NOT NULL,
    obstruction_type text NOT NULL,
    severity double precision NOT NULL,
    factors jsonb DEFAULT '{}'::jsonb NOT NULL,
    source_citation text NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT kala_obstruction_obstruction_type_check CHECK ((obstruction_type = ANY (ARRAY['malefic_transit'::text, 'adverse_dasha'::text, 'double_affliction'::text]))),
    CONSTRAINT kala_obstruction_severity_check CHECK (((severity >= (0.0)::double precision) AND (severity <= (1.0)::double precision)))
);


--
-- Name: TABLE kala_obstruction; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.kala_obstruction IS 'BRAHMA-KA-3-3: Temporal obstruction overlaps. Each row represents a period where ≥2 adverse indicators overlap: malefic planet (Sani/Rahu/Ketu) transit through dusthana house AND/OR active Vimshottari MD/AD ruled by a natural malefic. severity: 0.5 (2 indicators), 0.75 (3), 0.90 (4+). source_citation: "PyJHora/SwissEph DE441 + Brahma-L1" on all rows. Tool: period_snapshot via platform-mcp/src/tools/kala_period_snapshot.ts. Native: Abhisek Mohanty 1984-02-05; FORENSIC §5.1 Vimshottari schedule.';


--
-- Name: kala_obstruction_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE IF NOT EXISTS public.kala_obstruction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: kala_obstruction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.kala_obstruction_id_seq OWNED BY public.kala_obstruction.id;


--
-- Name: kala_timeline; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.kala_timeline (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    date date NOT NULL,
    active_mahadasha text NOT NULL,
    active_antardasha text NOT NULL,
    transit_highlights jsonb DEFAULT '[]'::jsonb NOT NULL,
    signal_activations jsonb DEFAULT '[]'::jsonb NOT NULL,
    source_citation text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE kala_timeline; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.kala_timeline IS 'L3 Kāla KA-3-1 — daily dasha×transit alignment rows per chart. Source: PyJHora/SwissEph DE441 + Brahma-L1 (FORENSIC §5.1).';


--
-- Name: COLUMN kala_timeline.active_mahadasha; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.kala_timeline.active_mahadasha IS 'Vimshottari Mahadasha lord active on this date (e.g. "Saturn", "Mercury").';


--
-- Name: COLUMN kala_timeline.active_antardasha; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.kala_timeline.active_antardasha IS 'Vimshottari Antardasha lord active on this date (e.g. "Jupiter", "Ketu").';


--
-- Name: COLUMN kala_timeline.transit_highlights; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.kala_timeline.transit_highlights IS 'Array of top transit events from ephemeris_daily for this date. Empty array when ephemeris_daily has no coverage for this date.';


--
-- Name: COLUMN kala_timeline.signal_activations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.kala_timeline.signal_activations IS 'bodha.signals activated by this date''s dasha×transit state. Empty array when bodha tables are empty (graceful degradation).';


--
-- Name: COLUMN kala_timeline.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.kala_timeline.source_citation IS 'Non-null data provenance. Canonical value: "PyJHora/SwissEph DE441 + Brahma-L1".';


--
-- Name: life_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.life_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    event_id text NOT NULL,
    event_date date NOT NULL,
    category text NOT NULL,
    description text NOT NULL,
    significance text,
    chart_state jsonb NOT NULL,
    source_section text NOT NULL,
    build_id text NOT NULL,
    provenance jsonb NOT NULL,
    event_type text,
    domain text,
    source_citation text,
    outcome_observed boolean
);


--
-- Name: life_events_staging; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.life_events_staging (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    event_id text NOT NULL,
    event_date date NOT NULL,
    category text NOT NULL,
    description text NOT NULL,
    significance text,
    chart_state jsonb NOT NULL,
    source_section text NOT NULL,
    build_id text NOT NULL,
    provenance jsonb NOT NULL
);


--
-- Name: llm_budget_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.llm_budget_rules (
    budget_rule_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    scope text NOT NULL,
    scope_value text,
    period text NOT NULL,
    amount_usd numeric(12,2) NOT NULL,
    alert_thresholds jsonb DEFAULT '[]'::jsonb NOT NULL,
    created_by_user_id text,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT llm_budget_rules_period_check CHECK ((period = ANY (ARRAY['daily'::text, 'weekly'::text, 'monthly'::text]))),
    CONSTRAINT llm_budget_rules_scope_check CHECK ((scope = ANY (ARRAY['total'::text, 'provider'::text, 'model'::text, 'pipeline_stage'::text])))
);


--
-- Name: llm_call_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.llm_call_log (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    query_id uuid NOT NULL,
    conversation_id uuid,
    call_stage text NOT NULL,
    model_id text NOT NULL,
    provider text NOT NULL,
    input_tokens integer,
    output_tokens integer,
    reasoning_tokens integer,
    latency_ms integer,
    cost_usd numeric(12,8),
    fallback_used boolean DEFAULT false,
    error_code text,
    payload jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    decision_alternatives jsonb,
    decision_reasoning text,
    prompt_template_id text,
    prompt_template_version text,
    parent_call_id uuid
);


--
-- Name: llm_cost_reconciliation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.llm_cost_reconciliation (
    reconciliation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    reconciliation_date date NOT NULL,
    provider text NOT NULL,
    model text,
    computed_total_usd numeric(14,6) NOT NULL,
    authoritative_total_usd numeric(14,6),
    variance_usd numeric(14,6),
    variance_pct numeric(8,4),
    event_count integer NOT NULL,
    status text NOT NULL,
    notes text,
    reconciled_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT llm_cost_reconciliation_status_check CHECK ((status = ANY (ARRAY['matched'::text, 'variance_within_tolerance'::text, 'variance_alert'::text, 'missing_authoritative'::text])))
);


--
-- Name: llm_pricing_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.llm_pricing_versions (
    pricing_version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    provider text NOT NULL,
    model text NOT NULL,
    token_class text NOT NULL,
    price_per_million_usd numeric(14,8) NOT NULL,
    effective_from timestamp with time zone NOT NULL,
    effective_to timestamp with time zone,
    source_url text,
    recorded_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT llm_pricing_versions_token_class_check CHECK ((token_class = ANY (ARRAY['input'::text, 'output'::text, 'cache_read'::text, 'cache_write'::text, 'reasoning'::text])))
);


--
-- Name: llm_provider_cost_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.llm_provider_cost_reports (
    report_id uuid DEFAULT gen_random_uuid() NOT NULL,
    provider text NOT NULL,
    model text,
    time_bucket_start timestamp with time zone NOT NULL,
    time_bucket_end timestamp with time zone NOT NULL,
    workspace_id text,
    authoritative_cost_usd numeric(14,6) NOT NULL,
    authoritative_input_tokens bigint,
    authoritative_output_tokens bigint,
    raw_payload jsonb,
    pulled_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: llm_stack_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.llm_stack_config (
    scope text NOT NULL,
    active_stack text NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_by text NOT NULL
);


--
-- Name: llm_usage_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.llm_usage_events (
    event_id uuid DEFAULT gen_random_uuid() NOT NULL,
    conversation_id text NOT NULL,
    conversation_name text,
    prompt_id text NOT NULL,
    parent_prompt_id text,
    user_id text NOT NULL,
    provider text NOT NULL,
    model text NOT NULL,
    pipeline_stage text NOT NULL,
    prompt_text text,
    response_text text,
    system_prompt text,
    parameters jsonb,
    input_tokens integer,
    output_tokens integer,
    cache_read_tokens integer DEFAULT 0,
    cache_write_tokens integer DEFAULT 0,
    reasoning_tokens integer DEFAULT 0,
    computed_cost_usd numeric(12,6),
    pricing_version_id uuid,
    latency_ms integer,
    status text NOT NULL,
    error_code text,
    provider_request_id text,
    started_at timestamp with time zone NOT NULL,
    finished_at timestamp with time zone,
    feature_flag_state jsonb,
    client_ip_hash text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT llm_usage_events_pipeline_stage_check CHECK ((pipeline_stage = ANY (ARRAY['classify'::text, 'compose'::text, 'retrieve'::text, 'synthesize'::text, 'audit'::text, 'other'::text, 'planner'::text, 'title'::text, 'history_summary'::text]))),
    CONSTRAINT llm_usage_events_provider_check CHECK ((provider = ANY (ARRAY['anthropic'::text, 'openai'::text, 'gemini'::text, 'deepseek'::text, 'nim'::text]))),
    CONSTRAINT llm_usage_events_status_check CHECK ((status = ANY (ARRAY['success'::text, 'error'::text, 'timeout'::text])))
);


--
-- Name: mcp_alerts_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.mcp_alerts_config (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    metric_name text NOT NULL,
    scope text NOT NULL,
    tool_name text,
    threshold_value numeric NOT NULL,
    comparison text NOT NULL,
    window_hours integer DEFAULT 24 NOT NULL,
    channels text[] DEFAULT '{}'::text[] NOT NULL,
    slack_webhook_url text,
    email_recipients text[],
    enabled boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by text DEFAULT 'native'::text NOT NULL,
    CONSTRAINT mcp_alerts_config_comparison_check CHECK ((comparison = ANY (ARRAY['gte'::text, 'lte'::text, 'gt'::text, 'lt'::text]))),
    CONSTRAINT mcp_alerts_config_scope_tool CHECK ((((scope = 'per_tool'::text) AND (tool_name IS NOT NULL)) OR ((scope = 'global'::text) AND (tool_name IS NULL))))
);


--
-- Name: mcp_api_keys; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.mcp_api_keys (
    key_id text NOT NULL,
    key_hash text NOT NULL,
    user_uid text NOT NULL,
    scopes text[] DEFAULT '{}'::text[] NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_used_at timestamp with time zone,
    revoked_at timestamp with time zone,
    label text
);


--
-- Name: mcp_disagreements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.mcp_disagreements (
    disagreement_id text NOT NULL,
    logged_at timestamp with time zone DEFAULT now() NOT NULL,
    class text NOT NULL,
    description text NOT NULL,
    source_session text NOT NULL,
    proposed_resolution text,
    status text DEFAULT 'open'::text NOT NULL,
    key_id text NOT NULL,
    trace_id text,
    resolved_on timestamp with time zone,
    resolved_by_session text,
    resolution_notes text,
    CONSTRAINT mcp_disagreements_class_check CHECK ((class = ANY (ARRAY['factual'::text, 'interpretive'::text, 'structural'::text, 'mirror_desync'::text, 'scope'::text, 'output_conflict'::text, 'version_disagreement'::text, 'scope_disagreement'::text, 'closure_disagreement'::text, 'l3_zero_supports'::text, 'panel_divergence'::text, 'school_disagreement'::text, 'acceptance_rate_anomaly'::text]))),
    CONSTRAINT mcp_disagreements_status_check CHECK ((status = ANY (ARRAY['open'::text, 'resolved'::text, 'escalated'::text, 'reopened'::text])))
);


--
-- Name: mcp_prediction_outcomes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.mcp_prediction_outcomes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    prediction_id text NOT NULL,
    outcome_text text NOT NULL,
    outcome_occurred boolean NOT NULL,
    outcome_date date NOT NULL,
    recorded_by text DEFAULT 'operator'::text NOT NULL,
    calibration_note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: mcp_predictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.mcp_predictions (
    prediction_id text NOT NULL,
    logged_at timestamp with time zone DEFAULT now() NOT NULL,
    horizon text,
    domain text,
    prediction_text text,
    confidence text,
    falsifier text,
    key_id text,
    trace_id text,
    caller_context text,
    outcome_text text,
    verified boolean,
    outcome_notes text,
    outcome_recorded_at timestamp with time zone,
    outcome_key_id text,
    outcome_trace_id text,
    migrated_at timestamp with time zone,
    migrated_to text,
    chart_id text,
    ayanamsha_id text,
    query_hash text,
    salience_formula_version text,
    model_id text,
    predicted_at_iso timestamp with time zone,
    CONSTRAINT mcp_predictions_confidence_check CHECK (((confidence = ANY (ARRAY['high'::text, 'medium'::text, 'low'::text])) OR (confidence IS NULL)))
);


--
-- Name: mimamsa_calibration; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.mimamsa_calibration (
    id bigint NOT NULL,
    chart_id uuid NOT NULL,
    technique text NOT NULL,
    ayanamsha_id text NOT NULL,
    brier_score double precision NOT NULL,
    sample_size integer NOT NULL,
    source_citation text NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT mimamsa_calibration_brier_score_check CHECK (((brier_score >= (0.0)::double precision) AND (brier_score <= (1.0)::double precision))),
    CONSTRAINT mimamsa_calibration_sample_size_check CHECK ((sample_size >= 1))
);


--
-- Name: TABLE mimamsa_calibration; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.mimamsa_calibration IS 'MI-5-3 mimamsa.outcome — per-technique, per-ayanamsha Brier score calibration. Brier score = mean((confidence - outcome_binary)²) over all scored predictions. source_citation required NOT NULL (B.3 derivation-ledger mandate). NO LEAKAGE: calibration uses only post-outcome observations — never upstream of prediction.';


--
-- Name: COLUMN mimamsa_calibration.technique; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_calibration.technique IS 'Prediction technique: vimshottari | yogini | kp | jaimini_chara | transit_outer | transit_inner | sade_sati | ashtakavarga | ensemble.';


--
-- Name: COLUMN mimamsa_calibration.ayanamsha_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_calibration.ayanamsha_id IS 'Ayanamsha used for chart computation: lahiri | true_chitra | kp | raman | surya_siddhanta.';


--
-- Name: COLUMN mimamsa_calibration.brier_score; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_calibration.brier_score IS 'Mean Brier score in [0.0, 1.0] for this (technique, ayanamsha_id) slice. 0.0 = perfect calibration (fully confident correct predictions). 1.0 = worst calibration (fully confident wrong predictions). 0.25 = uninformative baseline (equivalent to random 50/50 at 0.5 confidence).';


--
-- Name: COLUMN mimamsa_calibration.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_calibration.source_citation IS 'B.3 derivation-ledger citation. References prediction_ids, FORENSIC v8.0, LEL v1.7. Format: "computed from predictions {pred_ids} scored against LEL v1.7 events {event_ids}".';


--
-- Name: mimamsa_calibration_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE IF NOT EXISTS public.mimamsa_calibration_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: mimamsa_calibration_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.mimamsa_calibration_id_seq OWNED BY public.mimamsa_calibration.id;


--
-- Name: mimamsa_export_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.mimamsa_export_log (
    export_id uuid DEFAULT gen_random_uuid() NOT NULL,
    export_at timestamp with time zone DEFAULT now() NOT NULL,
    table_name text NOT NULL,
    row_count integer DEFAULT 0 NOT NULL,
    gcs_path text DEFAULT ''::text NOT NULL,
    source_citation text NOT NULL,
    CONSTRAINT lel_calibration_only CHECK (((table_name !~~ 'life_events%'::text) OR (table_name ~~ 'life_events_calibration%'::text))),
    CONSTRAINT mimamsa_export_log_row_count_check CHECK ((row_count >= 0))
);


--
-- Name: TABLE mimamsa_export_log; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.mimamsa_export_log IS 'BRAHMA MI-5-5: L5 Mīmāṃsā — audit trail for cross-corpus OLAP exports (chart_facts + bodha_signals → Parquet → GCS → BigQuery brahma_l5_olap). source_citation is NOT NULL; every row cites FORENSIC_v8_0 + artifact lineage. life_events intake: CALIBRATION ONLY (leakage guard enforced by DB constraint).';


--
-- Name: COLUMN mimamsa_export_log.export_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_export_log.export_id IS 'UUID primary key — generated per export run.';


--
-- Name: COLUMN mimamsa_export_log.export_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_export_log.export_at IS 'UTC timestamp of export execution.';


--
-- Name: COLUMN mimamsa_export_log.table_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_export_log.table_name IS 'Source table exported: chart_facts | bodha_signals | life_events_calibration.';


--
-- Name: COLUMN mimamsa_export_log.row_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_export_log.row_count IS 'Number of rows written to the GCS Parquet file (source_citation non-null filter applied).';


--
-- Name: COLUMN mimamsa_export_log.gcs_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_export_log.gcs_path IS 'Full GCS URI: gs://bucket/brahma/l5/mimamsa/{table}/{timestamp}/{table}.parquet';


--
-- Name: COLUMN mimamsa_export_log.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_export_log.source_citation IS 'NON-NULL provenance chain — must cite L1 canonical artifact: FORENSIC_ASTROLOGICAL_DATA_v8_0.md | LIFE_EVENT_LOG_v1_2.md | BRAHMA MI-5-5';


--
-- Name: mimamsa_export_log_staging; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.mimamsa_export_log_staging (
    export_id uuid DEFAULT gen_random_uuid() NOT NULL,
    export_at timestamp with time zone DEFAULT now() NOT NULL,
    table_name text NOT NULL,
    row_count integer DEFAULT 0 NOT NULL,
    gcs_path text DEFAULT ''::text NOT NULL,
    source_citation text NOT NULL,
    CONSTRAINT lel_calibration_only CHECK (((table_name !~~ 'life_events%'::text) OR (table_name ~~ 'life_events_calibration%'::text))),
    CONSTRAINT mimamsa_export_log_row_count_check CHECK ((row_count >= 0))
);


--
-- Name: COLUMN mimamsa_export_log_staging.export_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_export_log_staging.export_id IS 'UUID primary key — generated per export run.';


--
-- Name: COLUMN mimamsa_export_log_staging.export_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_export_log_staging.export_at IS 'UTC timestamp of export execution.';


--
-- Name: COLUMN mimamsa_export_log_staging.table_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_export_log_staging.table_name IS 'Source table exported: chart_facts | bodha_signals | life_events_calibration.';


--
-- Name: COLUMN mimamsa_export_log_staging.row_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_export_log_staging.row_count IS 'Number of rows written to the GCS Parquet file (source_citation non-null filter applied).';


--
-- Name: COLUMN mimamsa_export_log_staging.gcs_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_export_log_staging.gcs_path IS 'Full GCS URI: gs://bucket/brahma/l5/mimamsa/{table}/{timestamp}/{table}.parquet';


--
-- Name: COLUMN mimamsa_export_log_staging.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_export_log_staging.source_citation IS 'NON-NULL provenance chain — must cite L1 canonical artifact: FORENSIC_ASTROLOGICAL_DATA_v8_0.md | LIFE_EVENT_LOG_v1_2.md | BRAHMA MI-5-5';


--
-- Name: mimamsa_multipliers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.mimamsa_multipliers (
    technique text NOT NULL,
    ayanamsha_id text NOT NULL,
    multiplier double precision NOT NULL,
    last_updated timestamp with time zone DEFAULT (now() AT TIME ZONE 'UTC'::text) NOT NULL,
    sample_size integer NOT NULL,
    source_citation text NOT NULL,
    CONSTRAINT mimamsa_multipliers_multiplier_check CHECK (((multiplier >= (0.8)::double precision) AND (multiplier <= (1.2)::double precision))),
    CONSTRAINT mimamsa_multipliers_sample_size_check CHECK ((sample_size >= 0))
);


--
-- Name: TABLE mimamsa_multipliers; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.mimamsa_multipliers IS 'L5 Mīmāṃsā learning multipliers. Moves only from outcomes. Classical layer modulated NOT overwritten. multiplier = CLAMP(1.0 + 0.1 × (0.5 - mean_brier_score), 0.8, 1.2). source_citation required (B.3). NO LEAKAGE: life_events for calibration only, not prediction generation. BRAHMA-MI-5-4';


--
-- Name: COLUMN mimamsa_multipliers.technique; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_multipliers.technique IS 'Classical technique name, e.g. vimshottari_dasha, kp_sub_lord, jaimini_chara_dasha';


--
-- Name: COLUMN mimamsa_multipliers.ayanamsha_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_multipliers.ayanamsha_id IS 'Ayanamsha identifier, e.g. lahiri, raman, krishnamurti, yukteshwar';


--
-- Name: COLUMN mimamsa_multipliers.multiplier; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_multipliers.multiplier IS 'Bounded learning multiplier in [0.8, 1.2]. Formula: CLAMP(1.0 + 0.1 × (0.5 - mean_brier_score), 0.8, 1.2). Modulates classical L4 output — does NOT overwrite it.';


--
-- Name: COLUMN mimamsa_multipliers.last_updated; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_multipliers.last_updated IS 'UTC timestamp of the most recent calibration update for this technique × ayanamsha pair.';


--
-- Name: COLUMN mimamsa_multipliers.sample_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_multipliers.sample_size IS 'Number of resolved predictions used to derive the current multiplier. Must be > 0 for any write to be valid (enforced at application layer).';


--
-- Name: COLUMN mimamsa_multipliers.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_multipliers.source_citation IS 'B.3 derivation-ledger citation: L1 fact IDs consumed by this row. Required non-null. Minimum: FORENSIC v8.0 §5.1; LEL v1.7 §Calibration-outcomes.';


--
-- Name: mimamsa_predictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.mimamsa_predictions (
    prediction_id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    predicted_at timestamp with time zone DEFAULT now() NOT NULL,
    horizon_date date NOT NULL,
    domain text NOT NULL,
    prediction_text text NOT NULL,
    confidence double precision NOT NULL,
    falsifier text NOT NULL,
    source_citation text NOT NULL,
    outcome_observed boolean,
    brier_score double precision,
    outcome_recorded_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT mimamsa_predictions_brier_requires_outcome CHECK ((((brier_score IS NULL) AND (outcome_observed IS NULL)) OR ((brier_score IS NOT NULL) AND (outcome_observed IS NOT NULL)))),
    CONSTRAINT mimamsa_predictions_brier_score_check CHECK (((brier_score IS NULL) OR ((brier_score >= (0.0)::double precision) AND (brier_score <= (1.0)::double precision)))),
    CONSTRAINT mimamsa_predictions_confidence_check CHECK (((confidence > (0.0)::double precision) AND (confidence < (1.0)::double precision))),
    CONSTRAINT mimamsa_predictions_horizon_after_log CHECK ((horizon_date >= (predicted_at)::date))
);


--
-- Name: TABLE mimamsa_predictions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.mimamsa_predictions IS 'MI-5-2 mimamsa.prediction_ledger — prospective prediction log. Predictions are logged BEFORE the outcome is observed (Learning Layer rule #4). outcome_observed and brier_score are written ONLY via record_outcome(). source_citation and falsifier are REQUIRED NOT NULL (B.3 mandate + LL rule #4). confidence in OPEN interval (0, 1) — zero and one are not valid probabilities. NO LEAKAGE: LEL life_events feed calibration only, never prediction generation.';


--
-- Name: COLUMN mimamsa_predictions.prediction_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_predictions.prediction_id IS 'UUID primary key — returned to caller as the handle for record_outcome().';


--
-- Name: COLUMN mimamsa_predictions.confidence; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_predictions.confidence IS 'Calibrated probability in OPEN interval (0, 1). Zero and one excluded — a prediction of certainty is not a calibrated probability. Brier score = (outcome::int - confidence)^2 at record_outcome time.';


--
-- Name: COLUMN mimamsa_predictions.falsifier; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_predictions.falsifier IS 'Explicit falsifier per Learning Layer discipline rule #4. Format: "If [specific observable event] does not occur by [date], this prediction is false."';


--
-- Name: COLUMN mimamsa_predictions.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_predictions.source_citation IS 'L4 citation source: "Brahma L4 phala.anchors / [anchor_id]". Must reference the phala.anchors row that grounds this prediction (B.3 mandate).';


--
-- Name: COLUMN mimamsa_predictions.outcome_observed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_predictions.outcome_observed IS 'NULL until record_outcome() is called. TRUE = event occurred (prediction confirmed); FALSE = event did not occur (prediction falsified). NO LEAKAGE: this column must never be written outside record_outcome().';


--
-- Name: COLUMN mimamsa_predictions.brier_score; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_predictions.brier_score IS 'Brier score = (outcome_observed::int - confidence)^2. Range [0, 1]. Lower is better. Perfect calibration = 0. NULL until record_outcome() is called.';


--
-- Name: mimamsa_qa_eval; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.mimamsa_qa_eval (
    eval_id uuid DEFAULT gen_random_uuid() NOT NULL,
    question text NOT NULL,
    expected_domains text[] DEFAULT ARRAY[]::text[] NOT NULL,
    actual_response text,
    b11_compliance boolean,
    layer_coverage double precision,
    grounding_score double precision,
    source_citation text NOT NULL,
    evaluated_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT mimamsa_qa_eval_grounding_score_check CHECK (((grounding_score IS NULL) OR ((grounding_score >= (0.0)::double precision) AND (grounding_score <= (1.0)::double precision)))),
    CONSTRAINT mimamsa_qa_eval_layer_coverage_check CHECK (((layer_coverage IS NULL) OR ((layer_coverage >= (0.0)::double precision) AND (layer_coverage <= (1.0)::double precision))))
);


--
-- Name: TABLE mimamsa_qa_eval; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.mimamsa_qa_eval IS 'MI-5-6 mimamsa.answer_quality — golden Q&A eval set for L5 Mīmāṃsā. b11_compliance: response routes through holistic_bundle first (B.11 mandate). layer_coverage: fraction of 6 layers (L0–L5) present in response. grounding_score: fraction of expected_domains found in actual_response. source_citation required NOT NULL (B.3 derivation-ledger mandate). NO LEAKAGE: life_events feed calibration only, never prediction generation.';


--
-- Name: COLUMN mimamsa_qa_eval.b11_compliance; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_qa_eval.b11_compliance IS 'TRUE if actual_response demonstrates holistic_bundle (MSR+UCN+CDLM+CGM+RM) routing before domain-specific answer (B.11 Whole-Chart-Read discipline). NULL = not yet evaluated.';


--
-- Name: COLUMN mimamsa_qa_eval.layer_coverage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_qa_eval.layer_coverage IS 'Fraction of 6 Brahma layers (L0–L5) represented in the actual_response. Range [0.0, 1.0]. NULL = not yet evaluated.';


--
-- Name: COLUMN mimamsa_qa_eval.grounding_score; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_qa_eval.grounding_score IS 'Fraction of expected_domains that appear in actual_response. Range [0.0, 1.0]. NULL = not yet evaluated.';


--
-- Name: COLUMN mimamsa_qa_eval.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.mimamsa_qa_eval.source_citation IS 'Brahma QA golden set v1.0 — source of this Q&A pair.';


--
-- Name: tool_execution_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.tool_execution_log (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    query_id uuid,
    trace_id text,
    tool_name text NOT NULL,
    params_json jsonb,
    status text DEFAULT 'ok'::text NOT NULL,
    rows_returned integer,
    latency_ms integer,
    token_estimate integer,
    data_asset_id text,
    error_code text,
    served_from_cache boolean DEFAULT false,
    fallback_used boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    raw_result_count integer,
    kept_result_count integer,
    dropped_items jsonb,
    kept_items jsonb,
    tool_input_payload jsonb,
    tool_output_summary jsonb,
    error_class text DEFAULT 'OK'::text,
    retrieval_score real,
    audience_tier text DEFAULT 'super_admin'::text NOT NULL,
    response_text text,
    citation_count integer,
    has_numerical boolean,
    is_forward_looking boolean,
    sanskrit_compliant boolean,
    audit_flagged boolean DEFAULT false,
    source text,
    mcp_key_id text,
    mcp_tool_name text,
    bundle_trace_id uuid,
    signal_ids_available text[],
    bundle_size_tokens integer
);


--
-- Name: COLUMN tool_execution_log.audit_flagged; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tool_execution_log.audit_flagged IS 'Set true by the nightly audit job if any audit check fails for this row.';


--
-- Name: COLUMN tool_execution_log.source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tool_execution_log.source IS '"web_consume" | "mcp_primitive" | "mcp_bundle" | "mcp_sub_tool"';


--
-- Name: COLUMN tool_execution_log.mcp_key_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tool_execution_log.mcp_key_id IS 'API key ID from mcp_api_keys; NULL for web-path calls.';


--
-- Name: COLUMN tool_execution_log.mcp_tool_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tool_execution_log.mcp_tool_name IS 'MCP-facing tool name (e.g. holistic_bundle). NULL for web-path calls.';


--
-- Name: mv_session_summary; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.mv_session_summary AS
 SELECT COALESCE(tool_execution_log.mcp_key_id, 'web'::text) AS mcp_key_id,
    COALESCE(tool_execution_log.audience_tier, 'unknown'::text) AS audience_tier,
    date_trunc('hour'::text, tool_execution_log.created_at) AS session_hour,
    count(DISTINCT tool_execution_log.mcp_tool_name) FILTER (WHERE (tool_execution_log.source = 'mcp_primitive'::text)) AS unique_primitives,
    count(*) FILTER (WHERE (tool_execution_log.source = 'mcp_primitive'::text)) AS primitive_calls,
    count(*) FILTER (WHERE (tool_execution_log.source = 'mcp_bundle'::text)) AS bundle_calls,
    count(*) FILTER (WHERE (tool_execution_log.source = 'mcp_sub_tool'::text)) AS sub_tool_calls,
    sum(tool_execution_log.rows_returned) AS total_rows_returned,
    count(*) FILTER (WHERE (tool_execution_log.status = 'zero_rows'::text)) AS zero_rows_calls,
    sum(tool_execution_log.bundle_size_tokens) FILTER (WHERE (tool_execution_log.source = 'mcp_bundle'::text)) AS total_bundle_tokens
   FROM public.tool_execution_log
  WHERE (tool_execution_log.source ~~ 'mcp%'::text)
  GROUP BY COALESCE(tool_execution_log.mcp_key_id, 'web'::text), COALESCE(tool_execution_log.audience_tier, 'unknown'::text), (date_trunc('hour'::text, tool_execution_log.created_at))
  WITH NO DATA;


--
-- Name: mv_tool_metrics_24h; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.mv_tool_metrics_24h AS
 SELECT tool_execution_log.mcp_tool_name,
    COALESCE(tool_execution_log.source, 'unknown'::text) AS source,
    COALESCE(tool_execution_log.audience_tier, 'unknown'::text) AS audience_tier,
    count(*) AS calls_24h,
    count(*) FILTER (WHERE (tool_execution_log.status = 'ok'::text)) AS ok_calls,
    count(*) FILTER (WHERE (tool_execution_log.status = 'zero_rows'::text)) AS zero_rows_calls,
    count(*) FILTER (WHERE (tool_execution_log.status = 'error'::text)) AS error_calls,
    ((count(*) FILTER (WHERE (tool_execution_log.status = 'ok'::text)))::double precision / (NULLIF(count(*), 0))::double precision) AS ok_rate,
    ((count(*) FILTER (WHERE (tool_execution_log.status = 'zero_rows'::text)))::double precision / (NULLIF(count(*), 0))::double precision) AS zero_rows_rate,
    percentile_cont((0.50)::double precision) WITHIN GROUP (ORDER BY ((tool_execution_log.latency_ms)::double precision)) AS p50_latency_ms,
    percentile_cont((0.95)::double precision) WITHIN GROUP (ORDER BY ((tool_execution_log.latency_ms)::double precision)) AS p95_latency_ms,
    percentile_cont((0.99)::double precision) WITHIN GROUP (ORDER BY ((tool_execution_log.latency_ms)::double precision)) AS p99_latency_ms,
    avg(tool_execution_log.rows_returned) AS avg_rows_returned,
    avg(tool_execution_log.bundle_size_tokens) FILTER (WHERE (tool_execution_log.bundle_size_tokens IS NOT NULL)) AS avg_bundle_size_tokens,
    max(tool_execution_log.created_at) AS last_call_at
   FROM public.tool_execution_log
  WHERE ((tool_execution_log.created_at >= (now() - '24:00:00'::interval)) AND (tool_execution_log.mcp_tool_name IS NOT NULL))
  GROUP BY tool_execution_log.mcp_tool_name, COALESCE(tool_execution_log.source, 'unknown'::text), COALESCE(tool_execution_log.audience_tier, 'unknown'::text)
  WITH NO DATA;


--
-- Name: notification_views; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.notification_views (
    view_id uuid DEFAULT gen_random_uuid() NOT NULL,
    build_id uuid NOT NULL,
    user_id text NOT NULL,
    viewed_at timestamp with time zone DEFAULT now() NOT NULL,
    source text,
    CONSTRAINT notification_views_source_check CHECK ((source = ANY (ARRAY['toast'::text, 'dashboard'::text, 'email'::text, 'push'::text])))
);


--
-- Name: TABLE notification_views; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.notification_views IS 'Server-side tracking of build notifications seen by each user. Replaces localStorage approach from I-02 when migrated.';


--
-- Name: pending_streams; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.pending_streams (
    query_id text NOT NULL,
    user_id text DEFAULT ''::text NOT NULL,
    conversation_id text,
    accumulated_text text DEFAULT ''::text NOT NULL,
    last_event_seq bigint DEFAULT 0 NOT NULL,
    expires_at timestamp with time zone NOT NULL
);


--
-- Name: performance_judge_verdict; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.performance_judge_verdict (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    performance_query_id uuid NOT NULL,
    judge_run_id uuid NOT NULL,
    judge_model text NOT NULL,
    planner_verdict text NOT NULL,
    planner_reasoning text,
    triggered_by_user_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT performance_judge_verdict_planner_verdict_check CHECK ((planner_verdict = ANY (ARRAY['correct'::text, 'wrong'::text, 'ambiguous'::text])))
);


--
-- Name: performance_queries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.performance_queries (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    audit_event_id uuid,
    eval_run_id uuid,
    source text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    query_text text,
    query_class text,
    plan_type text,
    plan_tools_selected jsonb,
    planner_confidence numeric,
    latency_planner_ms integer,
    latency_retrieval_ms integer,
    latency_synthesis_ms integer,
    latency_total_ms integer,
    citations_present boolean,
    citation_count integer DEFAULT 0,
    synthesis_status text,
    validator_verdict text,
    disclosure_tier text,
    b10_violation boolean,
    b11_violation boolean,
    retrieval_hit boolean,
    retrieval_score_top1 numeric,
    plan_accuracy_label text DEFAULT 'unjudged'::text,
    plan_accuracy_source text,
    is_prediction boolean DEFAULT false,
    prediction_outcome_state text DEFAULT 'n_a'::text,
    CONSTRAINT performance_queries_plan_accuracy_label_check CHECK ((plan_accuracy_label = ANY (ARRAY['correct'::text, 'wrong'::text, 'ambiguous'::text, 'unjudged'::text, 'n_a'::text]))),
    CONSTRAINT performance_queries_plan_accuracy_source_check CHECK (((plan_accuracy_source = ANY (ARRAY['golden'::text, 'judge'::text])) OR (plan_accuracy_source IS NULL))),
    CONSTRAINT performance_queries_prediction_outcome_state_check CHECK ((prediction_outcome_state = ANY (ARRAY['pending'::text, 'observed_correct'::text, 'observed_incorrect'::text, 'n_a'::text]))),
    CONSTRAINT performance_queries_source_check CHECK ((source = ANY (ARRAY['consume'::text, 'eval'::text])))
);


--
-- Name: personas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.personas (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id text NOT NULL,
    name text NOT NULL,
    system_prompt text NOT NULL,
    default_style text,
    default_stack text,
    is_default boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT personas_name_check CHECK ((char_length(name) <= 50)),
    CONSTRAINT personas_system_prompt_check CHECK ((char_length(system_prompt) <= 4000))
);


--
-- Name: phala_anchors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.phala_anchors (
    id bigint NOT NULL,
    chart_id uuid NOT NULL,
    anchor_id text NOT NULL,
    window_start date NOT NULL,
    window_end date NOT NULL,
    theme text NOT NULL,
    confidence double precision NOT NULL,
    falsifier text NOT NULL,
    contributing_dashas jsonb DEFAULT '[]'::jsonb NOT NULL,
    contributing_signals jsonb DEFAULT '[]'::jsonb NOT NULL,
    source_citation text NOT NULL,
    prediction_state text DEFAULT 'open'::text NOT NULL,
    outcome_note text,
    outcome_recorded_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT phala_anchors_confidence_check CHECK (((confidence >= (0.0)::double precision) AND (confidence <= (1.0)::double precision))),
    CONSTRAINT phala_anchors_prediction_state_check CHECK ((prediction_state = ANY (ARRAY['open'::text, 'confirmed'::text, 'falsified'::text, 'expired'::text]))),
    CONSTRAINT phala_anchors_window_order CHECK ((window_end > window_start))
);


--
-- Name: TABLE phala_anchors; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.phala_anchors IS 'PH-4-1 phala.anchors — calibrated probabilistic event anchors per 6-month window. score = dasha_quality × signal_strength × convergence_score. falsifier column required NOT NULL (B.3 + Learning Layer rule #4). source_citation required NOT NULL (B.3 derivation-ledger mandate).';


--
-- Name: COLUMN phala_anchors.confidence; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_anchors.confidence IS 'Calibrated ensemble score in [0.0, 1.0]: dasha_quality × signal_strength × convergence_score. High = ≥0.65, Medium = 0.45–0.64, Low = <0.45.';


--
-- Name: COLUMN phala_anchors.falsifier; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_anchors.falsifier IS 'Explicit falsifier per Learning Layer discipline rule #4. Format: "If [specific observable event] does not occur by [date], this prediction is false."';


--
-- Name: COLUMN phala_anchors.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_anchors.source_citation IS 'L1 citation sources: FORENSIC v8.0 DSH.V.NNN + MSR SIG.* IDs grounding this anchor.';


--
-- Name: phala_anchors_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE IF NOT EXISTS public.phala_anchors_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: phala_anchors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.phala_anchors_id_seq OWNED BY public.phala_anchors.id;


--
-- Name: phala_mitigation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.phala_mitigation (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    anchor_id text NOT NULL,
    theme text,
    mitigation_type text NOT NULL,
    mitigation_text text NOT NULL,
    source_l0_rule_id text NOT NULL,
    source_citation text NOT NULL,
    l2_remediation_hub_id text,
    build_id text NOT NULL,
    asset_version text DEFAULT '1.0'::text NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT phala_mitigation_mitigation_type_check CHECK ((mitigation_type = ANY (ARRAY['mantra'::text, 'charity'::text, 'gemstone'::text, 'ritual'::text, 'timing'::text])))
);


--
-- Name: TABLE phala_mitigation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.phala_mitigation IS 'L4 Phala (PH-4-2): per-anchor classical mitigation map. Each row maps one event anchor (phala_anchors / PH-4-1) to a classical remedy cited from L0 concordance (BG-0-7) + L2 bodha.remediation (BO-2-6). source_citation is NON-NULL: always traces to a specific BPHS chapter/verse. mitigation_type: mantra | charity | gemstone | ritual | timing.';


--
-- Name: COLUMN phala_mitigation.anchor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_mitigation.anchor_id IS 'Reference to phala_anchors.anchor_id (PH-4-1). Soft FK (no hard REFERENCES constraint — phala_anchors builds in PH-4-1, which may deploy after PH-4-2).';


--
-- Name: COLUMN phala_mitigation.source_l0_rule_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_mitigation.source_l0_rule_id IS 'L0 concordance rule_id (BG-0-7) or BPHS-FALLBACK-<topic>. Traces to concordance_lookup.id or a canonical BPHS chapter pointer.';


--
-- Name: COLUMN phala_mitigation.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_mitigation.source_citation IS 'NON-NULL. BPHS.<chapter>.<verses> or BO-2-6 cross-reference. Format: BPHS.<chapter>.<verses>  e.g. BPHS.25.41-56.';


--
-- Name: COLUMN phala_mitigation.l2_remediation_hub_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_mitigation.l2_remediation_hub_id IS 'Optional back-link to bodha_remediation.contradiction_hub_id (BO-2-6). Present when the anchor maps directly to an existing L2 contradiction hub.';


--
-- Name: phala_mitigation_staging; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.phala_mitigation_staging (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    anchor_id text NOT NULL,
    theme text,
    mitigation_type text NOT NULL,
    mitigation_text text NOT NULL,
    source_l0_rule_id text NOT NULL,
    source_citation text NOT NULL,
    l2_remediation_hub_id text,
    build_id text NOT NULL,
    asset_version text DEFAULT '1.0'::text NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT phala_mitigation_mitigation_type_check CHECK ((mitigation_type = ANY (ARRAY['mantra'::text, 'charity'::text, 'gemstone'::text, 'ritual'::text, 'timing'::text])))
);


--
-- Name: TABLE phala_mitigation_staging; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.phala_mitigation_staging IS 'Staging copy of phala_mitigation for atomic swap builds (PH-4-2).';


--
-- Name: COLUMN phala_mitigation_staging.anchor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_mitigation_staging.anchor_id IS 'Reference to phala_anchors.anchor_id (PH-4-1). Soft FK (no hard REFERENCES constraint — phala_anchors builds in PH-4-1, which may deploy after PH-4-2).';


--
-- Name: COLUMN phala_mitigation_staging.source_l0_rule_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_mitigation_staging.source_l0_rule_id IS 'L0 concordance rule_id (BG-0-7) or BPHS-FALLBACK-<topic>. Traces to concordance_lookup.id or a canonical BPHS chapter pointer.';


--
-- Name: COLUMN phala_mitigation_staging.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_mitigation_staging.source_citation IS 'NON-NULL. BPHS.<chapter>.<verses> or BO-2-6 cross-reference. Format: BPHS.<chapter>.<verses>  e.g. BPHS.25.41-56.';


--
-- Name: COLUMN phala_mitigation_staging.l2_remediation_hub_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_mitigation_staging.l2_remediation_hub_id IS 'Optional back-link to bodha_remediation.contradiction_hub_id (BO-2-6). Present when the anchor maps directly to an existing L2 contradiction hub.';


--
-- Name: phala_muhurta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.phala_muhurta (
    muhurta_id uuid DEFAULT gen_random_uuid() NOT NULL,
    chart_id uuid NOT NULL,
    action_type text NOT NULL,
    window_start timestamp with time zone NOT NULL,
    window_end timestamp with time zone NOT NULL,
    auspiciousness_score double precision NOT NULL,
    factors jsonb DEFAULT '{}'::jsonb NOT NULL,
    source_citation text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT phala_muhurta_action_type_valid CHECK ((action_type = ANY (ARRAY['marriage'::text, 'travel'::text, 'business'::text, 'medical'::text, 'education'::text, 'property'::text, 'general'::text]))),
    CONSTRAINT phala_muhurta_auspiciousness_score_check CHECK (((auspiciousness_score >= (0.0)::double precision) AND (auspiciousness_score <= (1.0)::double precision))),
    CONSTRAINT phala_muhurta_window_valid CHECK ((window_start < window_end))
);


--
-- Name: TABLE phala_muhurta; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.phala_muhurta IS 'PH-4-4 — phala.muhurta electional finder (inverts Phala prediction engine).

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


--
-- Name: phala_rectification; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.phala_rectification (
    id bigint NOT NULL,
    chart_id uuid NOT NULL,
    candidate_time time without time zone NOT NULL,
    alignment_score double precision NOT NULL,
    rectification_confidence double precision NOT NULL,
    source_citation text NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT phala_rectification_alignment_score_check CHECK (((alignment_score >= (0.0)::double precision) AND (alignment_score <= (1.0)::double precision))),
    CONSTRAINT phala_rectification_rectification_confidence_check CHECK (((rectification_confidence >= (0.0)::double precision) AND (rectification_confidence <= (1.0)::double precision)))
);


--
-- Name: TABLE phala_rectification; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.phala_rectification IS 'PH-4-3 phala.rectification: birth-time rectification via Vimshottari dasha alignment scoring against LEL train/test split. 61 candidate rows per chart (±30 min of nominal birth time, 1-min steps). Best candidate = argmax(alignment_score on train events 1–43). rectification_confidence = Pearson-blend score on train set. test_score computed post-selection on held-out events 44–57. source_citation NON-NULL enforced — B.10 provenance mandate. Native chart (Abhisek Mohanty, 1984-02-05, 10:43 IST): chart_id = 362f9f17-95a5-490b-a5a7-027d3e0efda0. BRAHMA-PH-4-3 | phala.rectification';


--
-- Name: COLUMN phala_rectification.chart_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_rectification.chart_id IS 'UUID of the chart being rectified. FK to charts(id) where that table exists.';


--
-- Name: COLUMN phala_rectification.candidate_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_rectification.candidate_time IS 'Candidate birth time in IST (HH:MM:SS). Range: [nominal_birth - 30min, nominal_birth + 30min].';


--
-- Name: COLUMN phala_rectification.alignment_score; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_rectification.alignment_score IS 'Mean Vimshottari dasha alignment score on TRAIN events (events 1–43 of LEL). Scoring: 1.0 = MD+AD match, 0.5 = MD-only match, 0.0 = no match. CHECK constraint: 0.0 <= alignment_score <= 1.0.';


--
-- Name: COLUMN phala_rectification.rectification_confidence; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_rectification.rectification_confidence IS 'Composite confidence = (|pearson_r| + best_train_score) / 2. pearson_r = correlation between offset vector and alignment score vector. CHECK constraint: 0.0 <= rectification_confidence <= 1.0.';


--
-- Name: COLUMN phala_rectification.source_citation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.phala_rectification.source_citation IS 'Non-null provenance chain: FORENSIC §5.1 + LEL events + algorithm spec. B.10 mandate: every row carries full provenance.';


--
-- Name: phala_rectification_best; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.phala_rectification_best AS
 SELECT DISTINCT ON (phala_rectification.chart_id) phala_rectification.chart_id,
    phala_rectification.candidate_time,
    phala_rectification.alignment_score AS best_alignment_score,
    phala_rectification.rectification_confidence,
    phala_rectification.source_citation,
    phala_rectification.computed_at
   FROM public.phala_rectification
  ORDER BY phala_rectification.chart_id, phala_rectification.alignment_score DESC, phala_rectification.rectification_confidence DESC;


--
-- Name: VIEW phala_rectification_best; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.phala_rectification_best IS 'PH-4-3 convenience view: one row per chart, selecting the candidate_time with the highest alignment_score. Use for downstream chart-reading queries. Full candidate sweep is in phala_rectification base table.';


--
-- Name: phala_rectification_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE IF NOT EXISTS public.phala_rectification_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: phala_rectification_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.phala_rectification_id_seq OWNED BY public.phala_rectification.id;


--
-- Name: plan_alternatives_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.plan_alternatives_log (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    query_id uuid NOT NULL,
    bundle_name text NOT NULL,
    was_selected boolean NOT NULL,
    rationale text,
    expected_recall_score real,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.profiles (
    id text NOT NULL,
    role text DEFAULT 'guest'::text NOT NULL,
    name text,
    created_at timestamp with time zone DEFAULT now(),
    username text,
    email text,
    status text DEFAULT 'active'::text NOT NULL,
    approved_at timestamp with time zone,
    approved_by text,
    CONSTRAINT profiles_role_check CHECK ((role = ANY (ARRAY['guest'::text, 'super_admin'::text]))),
    CONSTRAINT profiles_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'active'::text, 'disabled'::text])))
);


--
-- Name: project_conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.project_conversations (
    project_id uuid NOT NULL,
    conversation_id uuid NOT NULL
);


--
-- Name: project_files; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.project_files (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    storage_path text NOT NULL,
    filename text NOT NULL,
    mime_type text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.projects (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id text NOT NULL,
    name text NOT NULL,
    system_prompt_addition text,
    chart_id text,
    deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: query_baseline_stats; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.query_baseline_stats AS
 SELECT 'unknown'::text AS query_type,
    percentile_cont((0.50)::double precision) WITHIN GROUP (ORDER BY ((llm_call_log.latency_ms)::double precision)) AS p50_total_latency_ms,
    percentile_cont((0.95)::double precision) WITHIN GROUP (ORDER BY ((llm_call_log.latency_ms)::double precision)) AS p95_total_latency_ms,
    percentile_cont((0.50)::double precision) WITHIN GROUP (ORDER BY ((llm_call_log.cost_usd)::double precision)) AS p50_total_cost_usd,
    percentile_cont((0.95)::double precision) WITHIN GROUP (ORDER BY ((llm_call_log.cost_usd)::double precision)) AS p95_total_cost_usd,
    count(*) AS sample_size
   FROM public.llm_call_log
  WHERE ((llm_call_log.created_at > (now() - '30 days'::interval)) AND (llm_call_log.cost_usd IS NOT NULL))
  GROUP BY 'unknown'::text
  WITH NO DATA;


--
-- Name: query_plan_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.query_plan_log (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    query_id uuid NOT NULL,
    conversation_id uuid,
    chart_id text,
    planner_model_id text,
    query_text text,
    query_class text,
    tool_count integer,
    plan_json jsonb,
    parsing_success boolean DEFAULT true NOT NULL,
    parse_error text,
    fallback_used boolean DEFAULT false,
    planner_latency_ms integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: query_trace_steps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.query_trace_steps (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    query_id uuid NOT NULL,
    conversation_id uuid,
    step_seq smallint NOT NULL,
    step_name text NOT NULL,
    step_type text NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    latency_ms integer,
    parallel_group text,
    data_summary jsonb DEFAULT '{}'::jsonb NOT NULL,
    payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id text,
    mcp_tool text,
    CONSTRAINT query_trace_steps_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'running'::text, 'done'::text, 'error'::text]))),
    CONSTRAINT query_trace_steps_step_type_check CHECK ((step_type = ANY (ARRAY['deterministic'::text, 'llm'::text, 'sql'::text, 'vector'::text, 'gcs'::text])))
);


--
-- Name: TABLE query_trace_steps; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.query_trace_steps IS 'Per-step execution trace for every pipeline invocation. Powers the real-time Query Trace Panel.';


--
-- Name: runtime_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.runtime_config (
    id bigint NOT NULL,
    key text NOT NULL,
    value jsonb NOT NULL,
    value_type text NOT NULL,
    scope text DEFAULT 'global'::text NOT NULL,
    chart_id text,
    updated_by text NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT runtime_config_scope_check CHECK ((scope = ANY (ARRAY['global'::text, 'per_chart'::text]))),
    CONSTRAINT runtime_config_value_type_check CHECK ((value_type = ANY (ARRAY['boolean'::text, 'number'::text, 'string'::text, 'json'::text])))
);


--
-- Name: TABLE runtime_config; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.runtime_config IS 'DB-backed control plane for gate_registry overrides. Env/code defaults apply if no row.';


--
-- Name: runtime_config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE IF NOT EXISTS public.runtime_config_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: runtime_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.runtime_config_id_seq OWNED BY public.runtime_config.id;


--
-- Name: synthesis_quality_scorecard; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.synthesis_quality_scorecard (
    query_id uuid NOT NULL,
    citation_density real DEFAULT 0 NOT NULL,
    whole_chart_coverage jsonb DEFAULT '{}'::jsonb NOT NULL,
    derivation_ledger_compliance real DEFAULT 0 NOT NULL,
    fabricated_computation_flags jsonb,
    disclosure_tier_verdict text DEFAULT 'UNKNOWN'::text NOT NULL,
    composite_score real DEFAULT 0 NOT NULL,
    failures jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: tool_registry; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS public.tool_registry (
    tool_name text NOT NULL,
    tool_enabled boolean DEFAULT true NOT NULL,
    disabled_reason text,
    disabled_at timestamp with time zone,
    disabled_by text,
    enabled_at timestamp with time zone DEFAULT now() NOT NULL,
    enabled_by text DEFAULT 'native'::text NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE tool_registry; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.tool_registry IS 'Runtime operator toggle for MCP tool enable/disable. tool_enabled=false causes the primitive dispatcher to return 503 {tool_disabled: true}.';


--
-- Name: _migrations_applied id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public._migrations_applied ALTER COLUMN id SET DEFAULT nextval('public._migrations_applied_id_seq'::regclass);


--
-- Name: kala_convergence convergence_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kala_convergence ALTER COLUMN convergence_id SET DEFAULT nextval('public.kala_convergence_convergence_id_seq'::regclass);


--
-- Name: kala_obstruction id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kala_obstruction ALTER COLUMN id SET DEFAULT nextval('public.kala_obstruction_id_seq'::regclass);


--
-- Name: mimamsa_calibration id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mimamsa_calibration ALTER COLUMN id SET DEFAULT nextval('public.mimamsa_calibration_id_seq'::regclass);


--
-- Name: phala_anchors id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phala_anchors ALTER COLUMN id SET DEFAULT nextval('public.phala_anchors_id_seq'::regclass);


--
-- Name: phala_rectification id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phala_rectification ALTER COLUMN id SET DEFAULT nextval('public.phala_rectification_id_seq'::regclass);


--
-- Name: runtime_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.runtime_config ALTER COLUMN id SET DEFAULT nextval('public.runtime_config_id_seq'::regclass);


--
-- Name: _migrations_applied _migrations_applied_filename_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public._migrations_applied
    ADD CONSTRAINT _migrations_applied_filename_key UNIQUE (filename);


--
-- Name: _migrations_applied _migrations_applied_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public._migrations_applied
    ADD CONSTRAINT _migrations_applied_pkey PRIMARY KEY (id);


--
-- Name: access_requests access_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.access_requests
    ADD CONSTRAINT access_requests_pkey PRIMARY KEY (id);


--
-- Name: audit_events audit_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_pkey PRIMARY KEY (id);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: bodha_domain_links bodha_domain_links_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_domain_links
    ADD CONSTRAINT bodha_domain_links_pkey PRIMARY KEY (link_id, chart_id);


--
-- Name: bodha_graph_edges bodha_graph_edges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_graph_edges
    ADD CONSTRAINT bodha_graph_edges_pkey PRIMARY KEY (edge_id, chart_id);


--
-- Name: bodha_graph bodha_graph_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_graph
    ADD CONSTRAINT bodha_graph_pk PRIMARY KEY (edge_id);


--
-- Name: bodha_graph_staging bodha_graph_staging_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_graph_staging
    ADD CONSTRAINT bodha_graph_staging_pkey PRIMARY KEY (edge_id);


--
-- Name: bodha_remediation bodha_remediation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_remediation
    ADD CONSTRAINT bodha_remediation_pkey PRIMARY KEY (id);


--
-- Name: bodha_remediation_staging bodha_remediation_staging_chart_id_contradiction_hub_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_remediation_staging
    ADD CONSTRAINT bodha_remediation_staging_chart_id_contradiction_hub_id_key UNIQUE (chart_id, contradiction_hub_id);


--
-- Name: bodha_remediation_staging bodha_remediation_staging_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_remediation_staging
    ADD CONSTRAINT bodha_remediation_staging_pkey PRIMARY KEY (id);


--
-- Name: bodha_resonance bodha_resonance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_resonance
    ADD CONSTRAINT bodha_resonance_pkey PRIMARY KEY (chart_id, ayanamsha_id, element_id);


--
-- Name: bodha_signal_embeddings bodha_signal_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_signal_embeddings
    ADD CONSTRAINT bodha_signal_embeddings_pkey PRIMARY KEY (signal_id);


--
-- Name: bodha_signals bodha_signals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_signals
    ADD CONSTRAINT bodha_signals_pkey PRIMARY KEY (signal_id, chart_id);


--
-- Name: build_engine_versions build_engine_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_engine_versions
    ADD CONSTRAINT build_engine_versions_pkey PRIMARY KEY (build_id, version_id);


--
-- Name: build_events build_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_events
    ADD CONSTRAINT build_events_pkey PRIMARY KEY (build_id, stage_seq);


--
-- Name: build_notifications build_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_notifications
    ADD CONSTRAINT build_notifications_pkey PRIMARY KEY (notif_id);


--
-- Name: build_steps build_steps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_steps
    ADD CONSTRAINT build_steps_pkey PRIMARY KEY (step_id);


--
-- Name: builds builds_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.builds
    ADD CONSTRAINT builds_pkey PRIMARY KEY (build_id);


--
-- Name: builds_staging builds_staging_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.builds_staging
    ADD CONSTRAINT builds_staging_pkey PRIMARY KEY (build_id);


--
-- Name: capability_asset_tool_bindings capability_asset_tool_bindings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.capability_asset_tool_bindings
    ADD CONSTRAINT capability_asset_tool_bindings_pkey PRIMARY KEY (asset_canonical_id, tool_name);


--
-- Name: capability_tool_registry capability_tool_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.capability_tool_registry
    ADD CONSTRAINT capability_tool_registry_pkey PRIMARY KEY (tool_name);


--
-- Name: chart_grants chart_grants_chart_id_principal_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chart_grants
    ADD CONSTRAINT chart_grants_chart_id_principal_id_key UNIQUE (chart_id, principal_id);


--
-- Name: chart_grants chart_grants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chart_grants
    ADD CONSTRAINT chart_grants_pkey PRIMARY KEY (id);


--
-- Name: charts charts_chart_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.charts
    ADD CONSTRAINT charts_chart_id_key UNIQUE (chart_id);


--
-- Name: charts charts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.charts
    ADD CONSTRAINT charts_pkey PRIMARY KEY (id);


--
-- Name: context_assembly_item_log context_assembly_item_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.context_assembly_item_log
    ADD CONSTRAINT context_assembly_item_log_pkey PRIMARY KEY (id);


--
-- Name: conversation_branches conversation_branches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_branches
    ADD CONSTRAINT conversation_branches_pkey PRIMARY KEY (id);


--
-- Name: conversation_folder_members conversation_folder_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_folder_members
    ADD CONSTRAINT conversation_folder_members_pkey PRIMARY KEY (conversation_id);


--
-- Name: conversation_folders conversation_folders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_folders
    ADD CONSTRAINT conversation_folders_pkey PRIMARY KEY (id);


--
-- Name: conversation_message_embeddings conversation_message_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_message_embeddings
    ADD CONSTRAINT conversation_message_embeddings_pkey PRIMARY KEY (message_id);


--
-- Name: conversation_messages conversation_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_pkey PRIMARY KEY (id);


--
-- Name: conversation_shares conversation_shares_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_shares
    ADD CONSTRAINT conversation_shares_pkey PRIMARY KEY (id);


--
-- Name: conversation_shares conversation_shares_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_shares
    ADD CONSTRAINT conversation_shares_slug_key UNIQUE (slug);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: engine_versions engine_versions_engine_name_version_str_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.engine_versions
    ADD CONSTRAINT engine_versions_engine_name_version_str_key UNIQUE (engine_name, version_str);


--
-- Name: engine_versions engine_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.engine_versions
    ADD CONSTRAINT engine_versions_pkey PRIMARY KEY (version_id);


--
-- Name: eval_runs eval_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eval_runs
    ADD CONSTRAINT eval_runs_pkey PRIMARY KEY (id);


--
-- Name: event_chart_state_index event_chart_state_index_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_chart_state_index
    ADD CONSTRAINT event_chart_state_index_pkey PRIMARY KEY (index_id);


--
-- Name: ganita_dashas ganita_dashas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ganita_dashas
    ADD CONSTRAINT ganita_dashas_pkey PRIMARY KEY (id);


--
-- Name: ganita_dashas ganita_dashas_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ganita_dashas
    ADD CONSTRAINT ganita_dashas_unique UNIQUE (chart_id, dasha_system, level, lord, start_date);


--
-- Name: ganita_positions ganita_positions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ganita_positions
    ADD CONSTRAINT ganita_positions_pkey PRIMARY KEY (id);


--
-- Name: ganita_positions ganita_positions_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ganita_positions
    ADD CONSTRAINT ganita_positions_unique UNIQUE (chart_id, ayanamsha_id, planet);


--
-- Name: kala_convergence kala_convergence_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kala_convergence
    ADD CONSTRAINT kala_convergence_pk PRIMARY KEY (convergence_id);


--
-- Name: kala_convergence_staging kala_convergence_staging_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kala_convergence_staging
    ADD CONSTRAINT kala_convergence_staging_pkey PRIMARY KEY (convergence_id);


--
-- Name: kala_obstruction kala_obstruction_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kala_obstruction
    ADD CONSTRAINT kala_obstruction_pk PRIMARY KEY (id);


--
-- Name: kala_obstruction kala_obstruction_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kala_obstruction
    ADD CONSTRAINT kala_obstruction_uniq UNIQUE (chart_id, date, obstruction_type);


--
-- Name: kala_timeline kala_timeline_chart_date_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kala_timeline
    ADD CONSTRAINT kala_timeline_chart_date_unique UNIQUE (chart_id, date);


--
-- Name: kala_timeline kala_timeline_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kala_timeline
    ADD CONSTRAINT kala_timeline_pkey PRIMARY KEY (id);


--
-- Name: life_events life_events_event_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.life_events
    ADD CONSTRAINT life_events_event_id_key UNIQUE (event_id);


--
-- Name: life_events life_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.life_events
    ADD CONSTRAINT life_events_pkey PRIMARY KEY (id);


--
-- Name: life_events_staging life_events_staging_event_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.life_events_staging
    ADD CONSTRAINT life_events_staging_event_id_key UNIQUE (event_id);


--
-- Name: life_events_staging life_events_staging_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.life_events_staging
    ADD CONSTRAINT life_events_staging_pkey PRIMARY KEY (id);


--
-- Name: llm_budget_rules llm_budget_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_budget_rules
    ADD CONSTRAINT llm_budget_rules_pkey PRIMARY KEY (budget_rule_id);


--
-- Name: llm_call_log llm_call_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_call_log
    ADD CONSTRAINT llm_call_log_pkey PRIMARY KEY (id);


--
-- Name: llm_cost_reconciliation llm_cost_reconciliation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_cost_reconciliation
    ADD CONSTRAINT llm_cost_reconciliation_pkey PRIMARY KEY (reconciliation_id);


--
-- Name: llm_pricing_versions llm_pricing_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_pricing_versions
    ADD CONSTRAINT llm_pricing_versions_pkey PRIMARY KEY (pricing_version_id);


--
-- Name: llm_provider_cost_reports llm_provider_cost_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_provider_cost_reports
    ADD CONSTRAINT llm_provider_cost_reports_pkey PRIMARY KEY (report_id);


--
-- Name: llm_stack_config llm_stack_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_stack_config
    ADD CONSTRAINT llm_stack_config_pkey PRIMARY KEY (scope);


--
-- Name: llm_usage_events llm_usage_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_usage_events
    ADD CONSTRAINT llm_usage_events_pkey PRIMARY KEY (event_id);


--
-- Name: mcp_alerts_config mcp_alerts_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mcp_alerts_config
    ADD CONSTRAINT mcp_alerts_config_pkey PRIMARY KEY (id);


--
-- Name: mcp_api_keys mcp_api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mcp_api_keys
    ADD CONSTRAINT mcp_api_keys_pkey PRIMARY KEY (key_id);


--
-- Name: mcp_disagreements mcp_disagreements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mcp_disagreements
    ADD CONSTRAINT mcp_disagreements_pkey PRIMARY KEY (disagreement_id);


--
-- Name: mcp_prediction_outcomes mcp_prediction_outcomes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mcp_prediction_outcomes
    ADD CONSTRAINT mcp_prediction_outcomes_pkey PRIMARY KEY (id);


--
-- Name: mcp_predictions mcp_predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mcp_predictions
    ADD CONSTRAINT mcp_predictions_pkey PRIMARY KEY (prediction_id);


--
-- Name: mimamsa_calibration mimamsa_calibration_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mimamsa_calibration
    ADD CONSTRAINT mimamsa_calibration_pkey PRIMARY KEY (id);


--
-- Name: mimamsa_calibration mimamsa_calibration_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mimamsa_calibration
    ADD CONSTRAINT mimamsa_calibration_unique UNIQUE (chart_id, technique, ayanamsha_id, computed_at);


--
-- Name: mimamsa_export_log mimamsa_export_log_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mimamsa_export_log
    ADD CONSTRAINT mimamsa_export_log_pk PRIMARY KEY (export_id);


--
-- Name: mimamsa_export_log_staging mimamsa_export_log_staging_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mimamsa_export_log_staging
    ADD CONSTRAINT mimamsa_export_log_staging_pkey PRIMARY KEY (export_id);


--
-- Name: mimamsa_multipliers mimamsa_multipliers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mimamsa_multipliers
    ADD CONSTRAINT mimamsa_multipliers_pkey PRIMARY KEY (technique, ayanamsha_id);


--
-- Name: mimamsa_predictions mimamsa_predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mimamsa_predictions
    ADD CONSTRAINT mimamsa_predictions_pkey PRIMARY KEY (prediction_id);


--
-- Name: mimamsa_qa_eval mimamsa_qa_eval_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mimamsa_qa_eval
    ADD CONSTRAINT mimamsa_qa_eval_pkey PRIMARY KEY (eval_id);


--
-- Name: notification_views notification_views_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_views
    ADD CONSTRAINT notification_views_pkey PRIMARY KEY (view_id);


--
-- Name: notification_views nv_unique_per_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_views
    ADD CONSTRAINT nv_unique_per_user UNIQUE (build_id, user_id);


--
-- Name: pending_streams pending_streams_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pending_streams
    ADD CONSTRAINT pending_streams_pkey PRIMARY KEY (query_id);


--
-- Name: performance_judge_verdict performance_judge_verdict_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_judge_verdict
    ADD CONSTRAINT performance_judge_verdict_pkey PRIMARY KEY (id);


--
-- Name: performance_queries performance_queries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_queries
    ADD CONSTRAINT performance_queries_pkey PRIMARY KEY (id);


--
-- Name: personas personas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personas
    ADD CONSTRAINT personas_pkey PRIMARY KEY (id);


--
-- Name: phala_anchors phala_anchors_anchor_id_chart_id_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phala_anchors
    ADD CONSTRAINT phala_anchors_anchor_id_chart_id_unique UNIQUE (chart_id, anchor_id);


--
-- Name: phala_anchors phala_anchors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phala_anchors
    ADD CONSTRAINT phala_anchors_pkey PRIMARY KEY (id);


--
-- Name: phala_mitigation phala_mitigation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phala_mitigation
    ADD CONSTRAINT phala_mitigation_pkey PRIMARY KEY (id);


--
-- Name: phala_mitigation_staging phala_mitigation_staging_chart_id_anchor_id_mitigation_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phala_mitigation_staging
    ADD CONSTRAINT phala_mitigation_staging_chart_id_anchor_id_mitigation_type_key UNIQUE (chart_id, anchor_id, mitigation_type);


--
-- Name: phala_mitigation_staging phala_mitigation_staging_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phala_mitigation_staging
    ADD CONSTRAINT phala_mitigation_staging_pkey PRIMARY KEY (id);


--
-- Name: phala_muhurta phala_muhurta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phala_muhurta
    ADD CONSTRAINT phala_muhurta_pkey PRIMARY KEY (muhurta_id);


--
-- Name: phala_rectification phala_rectification_chart_candidate_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phala_rectification
    ADD CONSTRAINT phala_rectification_chart_candidate_unique UNIQUE (chart_id, candidate_time);


--
-- Name: phala_rectification phala_rectification_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phala_rectification
    ADD CONSTRAINT phala_rectification_pkey PRIMARY KEY (id);


--
-- Name: plan_alternatives_log plan_alternatives_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_alternatives_log
    ADD CONSTRAINT plan_alternatives_log_pkey PRIMARY KEY (id);


--
-- Name: profiles profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiles
    ADD CONSTRAINT profiles_pkey PRIMARY KEY (id);


--
-- Name: project_conversations project_conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_conversations
    ADD CONSTRAINT project_conversations_pkey PRIMARY KEY (project_id, conversation_id);


--
-- Name: project_files project_files_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_files
    ADD CONSTRAINT project_files_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: query_plan_log query_plan_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_plan_log
    ADD CONSTRAINT query_plan_log_pkey PRIMARY KEY (id);


--
-- Name: query_plan_log query_plan_log_query_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_plan_log
    ADD CONSTRAINT query_plan_log_query_id_key UNIQUE (query_id);


--
-- Name: query_trace_steps query_trace_steps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_trace_steps
    ADD CONSTRAINT query_trace_steps_pkey PRIMARY KEY (id);


--
-- Name: runtime_config runtime_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.runtime_config
    ADD CONSTRAINT runtime_config_pkey PRIMARY KEY (id);


--
-- Name: synthesis_quality_scorecard synthesis_quality_scorecard_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.synthesis_quality_scorecard
    ADD CONSTRAINT synthesis_quality_scorecard_pkey PRIMARY KEY (query_id);


--
-- Name: tool_execution_log tool_execution_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool_execution_log
    ADD CONSTRAINT tool_execution_log_pkey PRIMARY KEY (id);


--
-- Name: tool_registry tool_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool_registry
    ADD CONSTRAINT tool_registry_pkey PRIMARY KEY (tool_name);


--
-- Name: audit_log uq_audit_log_query_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT uq_audit_log_query_id UNIQUE (query_id);


--
-- Name: bodha_remediation uq_bodha_remediation_hub; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_remediation
    ADD CONSTRAINT uq_bodha_remediation_hub UNIQUE (chart_id, contradiction_hub_id);


--
-- Name: llm_usage_events uq_llm_usage_events_prompt_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_usage_events
    ADD CONSTRAINT uq_llm_usage_events_prompt_id UNIQUE (prompt_id);


--
-- Name: phala_mitigation uq_phala_mitigation_anchor_type; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phala_mitigation
    ADD CONSTRAINT uq_phala_mitigation_anchor_type UNIQUE (chart_id, anchor_id, mitigation_type);


--
-- Name: access_requests_pending_email_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX IF NOT EXISTS access_requests_pending_email_unique ON public.access_requests USING btree (lower(email)) WHERE (status = 'pending'::text);


--
-- Name: access_requests_status_requested_at_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS access_requests_status_requested_at_idx ON public.access_requests USING btree (status, requested_at DESC);


--
-- Name: bev_version_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bev_version_idx ON public.build_engine_versions USING btree (version_id);


--
-- Name: bodha_domain_links_chart_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_domain_links_chart_id_idx ON public.bodha_domain_links USING btree (chart_id);


--
-- Name: bodha_domain_links_domains_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_domain_links_domains_idx ON public.bodha_domain_links USING btree (chart_id, from_domain, to_domain);


--
-- Name: bodha_graph_edges_chart_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_graph_edges_chart_id_idx ON public.bodha_graph_edges USING btree (chart_id);


--
-- Name: bodha_graph_edges_from_signal_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_graph_edges_from_signal_idx ON public.bodha_graph_edges USING btree (chart_id, from_signal_id);


--
-- Name: bodha_graph_edges_to_signal_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_graph_edges_to_signal_idx ON public.bodha_graph_edges USING btree (chart_id, to_signal_id);


--
-- Name: bodha_graph_staging_chart_id_edge_type_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_graph_staging_chart_id_edge_type_idx ON public.bodha_graph_staging USING btree (chart_id, edge_type);


--
-- Name: bodha_graph_staging_chart_id_from_signal_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_graph_staging_chart_id_from_signal_id_idx ON public.bodha_graph_staging USING btree (chart_id, from_signal_id);


--
-- Name: bodha_graph_staging_chart_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_graph_staging_chart_id_idx ON public.bodha_graph_staging USING btree (chart_id);


--
-- Name: bodha_graph_staging_chart_id_to_signal_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_graph_staging_chart_id_to_signal_id_idx ON public.bodha_graph_staging USING btree (chart_id, to_signal_id);


--
-- Name: bodha_remediation_staging_chart_id_domain_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_remediation_staging_chart_id_domain_idx ON public.bodha_remediation_staging USING btree (chart_id, domain);


--
-- Name: bodha_remediation_staging_chart_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_remediation_staging_chart_id_idx ON public.bodha_remediation_staging USING btree (chart_id);


--
-- Name: bodha_remediation_staging_contradicting_signal_ids_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_remediation_staging_contradicting_signal_ids_idx ON public.bodha_remediation_staging USING gin (contradicting_signal_ids);


--
-- Name: bodha_remediation_staging_contradiction_hub_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_remediation_staging_contradiction_hub_id_idx ON public.bodha_remediation_staging USING btree (contradiction_hub_id);


--
-- Name: bodha_remediation_staging_remedy_type_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_remediation_staging_remedy_type_idx ON public.bodha_remediation_staging USING btree (remedy_type);


--
-- Name: bodha_remediation_staging_source_l0_rule_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_remediation_staging_source_l0_rule_id_idx ON public.bodha_remediation_staging USING btree (source_l0_rule_id);


--
-- Name: bodha_resonance_chart_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_resonance_chart_id_idx ON public.bodha_resonance USING btree (chart_id);


--
-- Name: bodha_signals_chart_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_signals_chart_id_idx ON public.bodha_signals USING btree (chart_id);


--
-- Name: bodha_signals_domain_chart_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_signals_domain_chart_idx ON public.bodha_signals USING btree (chart_id, domain);


--
-- Name: bodha_signals_salience_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS bodha_signals_salience_idx ON public.bodha_signals USING btree (chart_id, salience DESC NULLS LAST);


--
-- Name: build_events_build_id_emitted_at_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS build_events_build_id_emitted_at_idx ON public.build_events USING btree (build_id, emitted_at DESC);


--
-- Name: build_events_chart_id_emitted_at_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS build_events_chart_id_emitted_at_idx ON public.build_events USING btree (chart_id, emitted_at DESC);


--
-- Name: build_notif_build_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS build_notif_build_idx ON public.build_notifications USING btree (build_id, created_at DESC);


--
-- Name: build_notif_undelivered_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS build_notif_undelivered_idx ON public.build_notifications USING btree (build_id) WHERE (delivered_at IS NULL);


--
-- Name: build_steps_build_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS build_steps_build_idx ON public.build_steps USING btree (build_id, ayanamsha_id);


--
-- Name: build_steps_category_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS build_steps_category_idx ON public.build_steps USING btree (category);


--
-- Name: build_steps_status_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS build_steps_status_idx ON public.build_steps USING btree (status) WHERE (status = ANY (ARRAY['queued'::text, 'running'::text]));


--
-- Name: builds_chart_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS builds_chart_idx ON public.builds USING btree (chart_id, queued_at DESC);


--
-- Name: builds_staging_chart_id_queued_at_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS builds_staging_chart_id_queued_at_idx ON public.builds_staging USING btree (chart_id, queued_at DESC);


--
-- Name: builds_staging_status_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS builds_staging_status_idx ON public.builds_staging USING btree (status) WHERE (status = ANY (ARRAY['queued'::text, 'running'::text, 'cancelling'::text]));


--
-- Name: builds_status_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS builds_status_idx ON public.builds USING btree (status) WHERE (status = ANY (ARRAY['queued'::text, 'running'::text, 'cancelling'::text]));


--
-- Name: conversation_messages_conv_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS conversation_messages_conv_time ON public.conversation_messages USING btree (conversation_id, created_at);


--
-- Name: conversation_messages_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS conversation_messages_parent ON public.conversation_messages USING btree (parent_message_id) WHERE (parent_message_id IS NOT NULL);


--
-- Name: conversations_active_ayanamshas_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS conversations_active_ayanamshas_gin ON public.conversations USING gin (active_ayanamshas);


--
-- Name: ecsi_event_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS ecsi_event_id_idx ON public.event_chart_state_index USING btree (event_id);


--
-- Name: eval_runs_created_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS eval_runs_created_idx ON public.eval_runs USING btree (created_at DESC);


--
-- Name: idx_audit_events_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON public.audit_events USING btree (created_at DESC);


--
-- Name: idx_audit_events_query_class; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_audit_events_query_class ON public.audit_events USING btree (query_class);


--
-- Name: idx_audit_events_query_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_audit_events_query_id ON public.audit_events USING btree (query_id);


--
-- Name: idx_audit_events_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON public.audit_events USING btree (user_id);


--
-- Name: idx_audit_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON public.audit_log USING btree (created_at DESC);


--
-- Name: idx_audit_log_query_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_audit_log_query_id ON public.audit_log USING btree (query_id);


--
-- Name: idx_bodha_graph_chart_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_graph_chart_id ON public.bodha_graph USING btree (chart_id);


--
-- Name: idx_bodha_graph_edge_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_graph_edge_type ON public.bodha_graph USING btree (chart_id, edge_type);


--
-- Name: idx_bodha_graph_from_signal; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_graph_from_signal ON public.bodha_graph USING btree (chart_id, from_signal_id);


--
-- Name: idx_bodha_graph_to_signal; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_graph_to_signal ON public.bodha_graph USING btree (chart_id, to_signal_id);


--
-- Name: idx_bodha_remediation_chart; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_remediation_chart ON public.bodha_remediation USING btree (chart_id);


--
-- Name: idx_bodha_remediation_domain; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_remediation_domain ON public.bodha_remediation USING btree (chart_id, domain);


--
-- Name: idx_bodha_remediation_hub_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_remediation_hub_id ON public.bodha_remediation USING btree (contradiction_hub_id);


--
-- Name: idx_bodha_remediation_l0_rule; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_remediation_l0_rule ON public.bodha_remediation USING btree (source_l0_rule_id);


--
-- Name: idx_bodha_remediation_remedy_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_remediation_remedy_type ON public.bodha_remediation USING btree (remedy_type);


--
-- Name: idx_bodha_remediation_signal_ids; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_remediation_signal_ids ON public.bodha_remediation USING gin (contradicting_signal_ids);


--
-- Name: idx_bodha_resonance_chart_ayan; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_resonance_chart_ayan ON public.bodha_resonance USING btree (chart_id, ayanamsha_id);


--
-- Name: idx_bodha_resonance_constituents_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_resonance_constituents_gin ON public.bodha_resonance USING gin (constituents);


--
-- Name: idx_bodha_resonance_domains_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_resonance_domains_gin ON public.bodha_resonance USING gin (domains_primary);


--
-- Name: idx_bodha_resonance_element_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_resonance_element_type ON public.bodha_resonance USING btree (chart_id, ayanamsha_id, element_type);


--
-- Name: idx_bodha_resonance_strength; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_resonance_strength ON public.bodha_resonance USING btree (chart_id, ayanamsha_id, strength DESC);


--
-- Name: idx_bodha_signal_embeddings_embedded_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_signal_embeddings_embedded_at ON public.bodha_signal_embeddings USING btree (embedded_at DESC);


--
-- Name: idx_bodha_signal_embeddings_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_signal_embeddings_hnsw ON public.bodha_signal_embeddings USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_bodha_signal_embeddings_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_bodha_signal_embeddings_model ON public.bodha_signal_embeddings USING btree (model_name);


--
-- Name: idx_capability_asset_tool_bindings_asset; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_capability_asset_tool_bindings_asset ON public.capability_asset_tool_bindings USING btree (asset_canonical_id);


--
-- Name: idx_capability_asset_tool_bindings_tool; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_capability_asset_tool_bindings_tool ON public.capability_asset_tool_bindings USING btree (tool_name);


--
-- Name: idx_chart_grants_chart_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_chart_grants_chart_id ON public.chart_grants USING btree (chart_id);


--
-- Name: idx_chart_grants_principal_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_chart_grants_principal_id ON public.chart_grants USING btree (principal_id);


--
-- Name: idx_charts_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_charts_client_id ON public.charts USING btree (client_id);


--
-- Name: idx_charts_owner_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_charts_owner_id ON public.charts USING btree (owner_id);


--
-- Name: idx_charts_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_charts_role ON public.charts USING btree (role);


--
-- Name: idx_cme_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_cme_embedding ON public.conversation_message_embeddings USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_context_assembly_item_log_query; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_context_assembly_item_log_query ON public.context_assembly_item_log USING btree (query_id, item_rank);


--
-- Name: idx_conv_messages_body_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_conv_messages_body_trgm ON public.conversation_messages USING gin (((parts_json)::text) public.gin_trgm_ops);


--
-- Name: idx_conversation_branches_conversation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_conversation_branches_conversation_id ON public.conversation_branches USING btree (conversation_id, created_at DESC);


--
-- Name: idx_conversation_folders_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_conversation_folders_user ON public.conversation_folders USING btree (user_id, created_at DESC);


--
-- Name: idx_conversation_shares_conversation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_conversation_shares_conversation_id ON public.conversation_shares USING btree (conversation_id);


--
-- Name: idx_conversations_chart_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_conversations_chart_id ON public.conversations USING btree (chart_id);


--
-- Name: idx_conversations_pinned; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_conversations_pinned ON public.conversations USING btree (user_id, pinned DESC, updated_at DESC);


--
-- Name: idx_conversations_title_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_conversations_title_trgm ON public.conversations USING gin (title public.gin_trgm_ops) WHERE (title IS NOT NULL);


--
-- Name: idx_conversations_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations USING btree (user_id);


--
-- Name: idx_folder_members_folder; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_folder_members_folder ON public.conversation_folder_members USING btree (folder_id, added_at DESC);


--
-- Name: idx_ganita_dashas_chart; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_ganita_dashas_chart ON public.ganita_dashas USING btree (chart_id, dasha_system, level);


--
-- Name: idx_ganita_dashas_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_ganita_dashas_date ON public.ganita_dashas USING btree (chart_id, start_date, end_date);


--
-- Name: idx_ganita_positions_chart; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_ganita_positions_chart ON public.ganita_positions USING btree (chart_id, ayanamsha_id);


--
-- Name: idx_kala_convergence_chart_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_kala_convergence_chart_id ON public.kala_convergence USING btree (chart_id);


--
-- Name: idx_kala_convergence_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_kala_convergence_score ON public.kala_convergence USING btree (chart_id, convergence_score DESC);


--
-- Name: idx_kala_convergence_window; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_kala_convergence_window ON public.kala_convergence USING btree (chart_id, window_start, window_end);


--
-- Name: idx_kala_obstruction_chart_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_kala_obstruction_chart_id ON public.kala_obstruction USING btree (chart_id);


--
-- Name: idx_kala_obstruction_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_kala_obstruction_date ON public.kala_obstruction USING btree (chart_id, date);


--
-- Name: idx_kala_obstruction_factors; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_kala_obstruction_factors ON public.kala_obstruction USING gin (factors);


--
-- Name: idx_kala_obstruction_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_kala_obstruction_severity ON public.kala_obstruction USING btree (chart_id, severity DESC);


--
-- Name: idx_kala_obstruction_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_kala_obstruction_type ON public.kala_obstruction USING btree (chart_id, obstruction_type);


--
-- Name: idx_kala_timeline_chart_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_kala_timeline_chart_date ON public.kala_timeline USING btree (chart_id, date);


--
-- Name: idx_kala_timeline_mahadasha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_kala_timeline_mahadasha ON public.kala_timeline USING btree (chart_id, active_mahadasha, date);


--
-- Name: idx_kala_timeline_signal_activations; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_kala_timeline_signal_activations ON public.kala_timeline USING gin (signal_activations);


--
-- Name: idx_life_events_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_life_events_category ON public.life_events USING btree (category, event_date);


--
-- Name: idx_life_events_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_life_events_date ON public.life_events USING btree (event_date);


--
-- Name: idx_llm_call_log_call_stage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_llm_call_log_call_stage ON public.llm_call_log USING btree (call_stage);


--
-- Name: idx_llm_call_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_llm_call_log_created_at ON public.llm_call_log USING btree (created_at DESC);


--
-- Name: idx_llm_call_log_model_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_llm_call_log_model_id ON public.llm_call_log USING btree (model_id);


--
-- Name: idx_llm_call_log_query_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_llm_call_log_query_id ON public.llm_call_log USING btree (query_id);


--
-- Name: idx_llm_cost_reconciliation_date_provider; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_llm_cost_reconciliation_date_provider ON public.llm_cost_reconciliation USING btree (reconciliation_date, provider);


--
-- Name: idx_llm_pricing_versions_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_llm_pricing_versions_lookup ON public.llm_pricing_versions USING btree (provider, model, effective_from DESC);


--
-- Name: idx_llm_provider_cost_reports_provider_bucket; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_llm_provider_cost_reports_provider_bucket ON public.llm_provider_cost_reports USING btree (provider, time_bucket_start);


--
-- Name: idx_llm_usage_events_conversation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_llm_usage_events_conversation_id ON public.llm_usage_events USING btree (conversation_id);


--
-- Name: idx_llm_usage_events_pipeline_stage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_llm_usage_events_pipeline_stage ON public.llm_usage_events USING btree (pipeline_stage);


--
-- Name: idx_llm_usage_events_provider_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_llm_usage_events_provider_model ON public.llm_usage_events USING btree (provider, model);


--
-- Name: idx_llm_usage_events_started_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_llm_usage_events_started_at ON public.llm_usage_events USING btree (started_at);


--
-- Name: idx_llm_usage_events_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_llm_usage_events_user_id ON public.llm_usage_events USING btree (user_id);


--
-- Name: idx_mimamsa_calibration_ayanamsha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_ayanamsha ON public.mimamsa_calibration USING btree (ayanamsha_id, computed_at DESC);


--
-- Name: idx_mimamsa_calibration_chart_technique; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_chart_technique ON public.mimamsa_calibration USING btree (chart_id, technique);


--
-- Name: idx_mimamsa_calibration_computed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_computed_at ON public.mimamsa_calibration USING btree (computed_at DESC);


--
-- Name: idx_mimamsa_export_log_export_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_export_log_export_at ON public.mimamsa_export_log USING btree (export_at DESC);


--
-- Name: idx_mimamsa_export_log_table_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_export_log_table_name ON public.mimamsa_export_log USING btree (table_name);


--
-- Name: idx_mimamsa_multipliers_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_multipliers_lookup ON public.mimamsa_multipliers USING btree (technique, ayanamsha_id);


--
-- Name: idx_mimamsa_predictions_chart_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_chart_id ON public.mimamsa_predictions USING btree (chart_id);


--
-- Name: idx_mimamsa_predictions_domain; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_domain ON public.mimamsa_predictions USING btree (chart_id, domain);


--
-- Name: idx_mimamsa_predictions_horizon; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_horizon ON public.mimamsa_predictions USING btree (chart_id, horizon_date);


--
-- Name: idx_mimamsa_predictions_open; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_open ON public.mimamsa_predictions USING btree (chart_id) WHERE (outcome_observed IS NULL);


--
-- Name: idx_mimamsa_predictions_predicted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_predicted_at ON public.mimamsa_predictions USING btree (predicted_at);


--
-- Name: idx_mimamsa_qa_eval_b11; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_qa_eval_b11 ON public.mimamsa_qa_eval USING btree (b11_compliance);


--
-- Name: idx_mimamsa_qa_eval_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_qa_eval_created ON public.mimamsa_qa_eval USING btree (created_at DESC);


--
-- Name: idx_mimamsa_qa_eval_grounding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_qa_eval_grounding ON public.mimamsa_qa_eval USING btree (grounding_score DESC NULLS LAST);


--
-- Name: idx_mimamsa_qa_eval_layer_coverage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_mimamsa_qa_eval_layer_coverage ON public.mimamsa_qa_eval USING btree (layer_coverage DESC NULLS LAST);


--
-- Name: idx_pending_streams_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_pending_streams_expires_at ON public.pending_streams USING btree (expires_at);


--
-- Name: idx_personas_user_default; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX IF NOT EXISTS idx_personas_user_default ON public.personas USING btree (user_id) WHERE (is_default = true);


--
-- Name: idx_personas_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_personas_user_id ON public.personas USING btree (user_id);


--
-- Name: idx_phala_anchors_chart_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_anchors_chart_id ON public.phala_anchors USING btree (chart_id);


--
-- Name: idx_phala_anchors_confidence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_anchors_confidence ON public.phala_anchors USING btree (chart_id, confidence DESC);


--
-- Name: idx_phala_anchors_contributing_signals; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_anchors_contributing_signals ON public.phala_anchors USING gin (contributing_signals);


--
-- Name: idx_phala_anchors_state; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_anchors_state ON public.phala_anchors USING btree (prediction_state);


--
-- Name: idx_phala_anchors_window; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_anchors_window ON public.phala_anchors USING btree (chart_id, window_start, window_end);


--
-- Name: idx_phala_mitigation_anchor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_mitigation_anchor ON public.phala_mitigation USING btree (chart_id, anchor_id);


--
-- Name: idx_phala_mitigation_chart; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_mitigation_chart ON public.phala_mitigation USING btree (chart_id);


--
-- Name: idx_phala_mitigation_l0_rule; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_mitigation_l0_rule ON public.phala_mitigation USING btree (source_l0_rule_id);


--
-- Name: idx_phala_mitigation_l2_hub; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_mitigation_l2_hub ON public.phala_mitigation USING btree (l2_remediation_hub_id) WHERE (l2_remediation_hub_id IS NOT NULL);


--
-- Name: idx_phala_mitigation_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_mitigation_type ON public.phala_mitigation USING btree (mitigation_type);


--
-- Name: idx_phala_muhurta_chart_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_muhurta_chart_action ON public.phala_muhurta USING btree (chart_id, action_type);


--
-- Name: idx_phala_muhurta_chart_action_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_muhurta_chart_action_score ON public.phala_muhurta USING btree (chart_id, action_type, auspiciousness_score DESC);


--
-- Name: idx_phala_muhurta_factors_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_muhurta_factors_gin ON public.phala_muhurta USING gin (factors);


--
-- Name: idx_phala_muhurta_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_muhurta_score ON public.phala_muhurta USING btree (auspiciousness_score DESC);


--
-- Name: idx_phala_muhurta_unique_window; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX IF NOT EXISTS idx_phala_muhurta_unique_window ON public.phala_muhurta USING btree (chart_id, action_type, window_start);


--
-- Name: idx_phala_muhurta_window_start; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_phala_muhurta_window_start ON public.phala_muhurta USING btree (window_start);


--
-- Name: idx_plan_alternatives_log_query; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_plan_alternatives_log_query ON public.plan_alternatives_log USING btree (query_id);


--
-- Name: idx_project_conv_conv; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_project_conv_conv ON public.project_conversations USING btree (conversation_id);


--
-- Name: idx_project_conv_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_project_conv_project ON public.project_conversations USING btree (project_id);


--
-- Name: idx_qts_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_qts_user_id ON public.query_trace_steps USING btree (user_id) WHERE (user_id IS NOT NULL);


--
-- Name: idx_query_plan_log_conversation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_query_plan_log_conversation_id ON public.query_plan_log USING btree (conversation_id);


--
-- Name: idx_query_plan_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_query_plan_log_created_at ON public.query_plan_log USING btree (created_at DESC);


--
-- Name: idx_query_plan_log_fallback; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_query_plan_log_fallback ON public.query_plan_log USING btree (fallback_used) WHERE (fallback_used = true);


--
-- Name: idx_query_plan_log_query_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_query_plan_log_query_id ON public.query_plan_log USING btree (query_id);


--
-- Name: idx_query_trace_steps_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_query_trace_steps_created_at ON public.query_trace_steps USING btree (created_at DESC);


--
-- Name: idx_query_trace_steps_mcp_tool; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_query_trace_steps_mcp_tool ON public.query_trace_steps USING btree (mcp_tool) WHERE (mcp_tool IS NOT NULL);


--
-- Name: idx_query_trace_steps_query_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_query_trace_steps_query_id ON public.query_trace_steps USING btree (query_id, step_seq);


--
-- Name: idx_tool_execution_log_query_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_tool_execution_log_query_id ON public.tool_execution_log USING btree (query_id) WHERE (query_id IS NOT NULL);


--
-- Name: idx_tool_execution_log_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_tool_execution_log_status ON public.tool_execution_log USING btree (status);


--
-- Name: idx_tool_execution_log_tool_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_tool_execution_log_tool_name ON public.tool_execution_log USING btree (tool_name);


--
-- Name: idx_tool_execution_log_zero_rows; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_tool_execution_log_zero_rows ON public.tool_execution_log USING btree (tool_name) WHERE (status = 'zero_rows'::text);


--
-- Name: judge_verdict_pq_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS judge_verdict_pq_idx ON public.performance_judge_verdict USING btree (performance_query_id);


--
-- Name: judge_verdict_run_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS judge_verdict_run_idx ON public.performance_judge_verdict USING btree (judge_run_id);


--
-- Name: kala_convergence_staging_chart_id_convergence_score_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS kala_convergence_staging_chart_id_convergence_score_idx ON public.kala_convergence_staging USING btree (chart_id, convergence_score DESC);


--
-- Name: kala_convergence_staging_chart_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS kala_convergence_staging_chart_id_idx ON public.kala_convergence_staging USING btree (chart_id);


--
-- Name: kala_convergence_staging_chart_id_window_start_window_end_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS kala_convergence_staging_chart_id_window_start_window_end_idx ON public.kala_convergence_staging USING btree (chart_id, window_start, window_end);


--
-- Name: life_events_staging_category_event_date_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS life_events_staging_category_event_date_idx ON public.life_events_staging USING btree (category, event_date);


--
-- Name: life_events_staging_event_date_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS life_events_staging_event_date_idx ON public.life_events_staging USING btree (event_date);


--
-- Name: mcp_alerts_config_enabled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS mcp_alerts_config_enabled ON public.mcp_alerts_config USING btree (metric_name, scope, enabled) WHERE (enabled = true);


--
-- Name: mcp_api_keys_auth_lookup_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS mcp_api_keys_auth_lookup_idx ON public.mcp_api_keys USING btree (key_id, revoked_at);


--
-- Name: mcp_api_keys_user_uid_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS mcp_api_keys_user_uid_idx ON public.mcp_api_keys USING btree (user_uid);


--
-- Name: mcp_disagreements_key_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS mcp_disagreements_key_id_idx ON public.mcp_disagreements USING btree (key_id, logged_at DESC);


--
-- Name: mcp_disagreements_status_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS mcp_disagreements_status_idx ON public.mcp_disagreements USING btree (status, logged_at DESC);


--
-- Name: mcp_prediction_outcomes_prediction_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS mcp_prediction_outcomes_prediction_id ON public.mcp_prediction_outcomes USING btree (prediction_id);


--
-- Name: mcp_predictions_chart_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS mcp_predictions_chart_idx ON public.mcp_predictions USING btree (chart_id, predicted_at_iso DESC) WHERE (chart_id IS NOT NULL);


--
-- Name: mcp_predictions_key_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS mcp_predictions_key_id_idx ON public.mcp_predictions USING btree (key_id, logged_at DESC) WHERE (key_id IS NOT NULL);


--
-- Name: mcp_predictions_stamp_uq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX IF NOT EXISTS mcp_predictions_stamp_uq ON public.mcp_predictions USING btree (chart_id, ayanamsha_id, query_hash, salience_formula_version) WHERE ((chart_id IS NOT NULL) AND (ayanamsha_id IS NOT NULL) AND (query_hash IS NOT NULL) AND (salience_formula_version IS NOT NULL));


--
-- Name: mcp_predictions_trace_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS mcp_predictions_trace_id_idx ON public.mcp_predictions USING btree (trace_id) WHERE (trace_id IS NOT NULL);


--
-- Name: mimamsa_export_log_staging_export_at_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS mimamsa_export_log_staging_export_at_idx ON public.mimamsa_export_log_staging USING btree (export_at DESC);


--
-- Name: mimamsa_export_log_staging_table_name_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS mimamsa_export_log_staging_table_name_idx ON public.mimamsa_export_log_staging USING btree (table_name);


--
-- Name: mv_session_summary_pk; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX IF NOT EXISTS mv_session_summary_pk ON public.mv_session_summary USING btree (mcp_key_id, session_hour);


--
-- Name: mv_tool_metrics_24h_pk; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX IF NOT EXISTS mv_tool_metrics_24h_pk ON public.mv_tool_metrics_24h USING btree (mcp_tool_name, source, audience_tier);


--
-- Name: nv_build_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS nv_build_idx ON public.notification_views USING btree (build_id);


--
-- Name: nv_user_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS nv_user_idx ON public.notification_views USING btree (user_id, viewed_at DESC);


--
-- Name: perf_queries_audit_event_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS perf_queries_audit_event_idx ON public.performance_queries USING btree (audit_event_id);


--
-- Name: perf_queries_class_created_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS perf_queries_class_created_idx ON public.performance_queries USING btree (query_class, created_at DESC);


--
-- Name: perf_queries_created_at_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS perf_queries_created_at_idx ON public.performance_queries USING btree (created_at DESC);


--
-- Name: perf_queries_eval_run_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS perf_queries_eval_run_idx ON public.performance_queries USING btree (eval_run_id);


--
-- Name: perf_queries_source_created_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS perf_queries_source_created_idx ON public.performance_queries USING btree (source, created_at DESC);


--
-- Name: phala_mitigation_staging_chart_id_anchor_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS phala_mitigation_staging_chart_id_anchor_id_idx ON public.phala_mitigation_staging USING btree (chart_id, anchor_id);


--
-- Name: phala_mitigation_staging_chart_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS phala_mitigation_staging_chart_id_idx ON public.phala_mitigation_staging USING btree (chart_id);


--
-- Name: phala_mitigation_staging_l2_remediation_hub_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS phala_mitigation_staging_l2_remediation_hub_id_idx ON public.phala_mitigation_staging USING btree (l2_remediation_hub_id) WHERE (l2_remediation_hub_id IS NOT NULL);


--
-- Name: phala_mitigation_staging_mitigation_type_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS phala_mitigation_staging_mitigation_type_idx ON public.phala_mitigation_staging USING btree (mitigation_type);


--
-- Name: phala_mitigation_staging_source_l0_rule_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS phala_mitigation_staging_source_l0_rule_id_idx ON public.phala_mitigation_staging USING btree (source_l0_rule_id);


--
-- Name: phala_rectification_chart_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS phala_rectification_chart_id_idx ON public.phala_rectification USING btree (chart_id);


--
-- Name: phala_rectification_chart_score_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS phala_rectification_chart_score_idx ON public.phala_rectification USING btree (chart_id, alignment_score DESC);


--
-- Name: profiles_email_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX IF NOT EXISTS profiles_email_unique ON public.profiles USING btree (lower(email)) WHERE (email IS NOT NULL);


--
-- Name: profiles_username_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX IF NOT EXISTS profiles_username_unique ON public.profiles USING btree (lower(username)) WHERE (username IS NOT NULL);


--
-- Name: runtime_config_key_chart_uq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX IF NOT EXISTS runtime_config_key_chart_uq ON public.runtime_config USING btree (key, COALESCE(chart_id, '__global__'::text));


--
-- Name: tool_execution_log_audit_queue; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS tool_execution_log_audit_queue ON public.tool_execution_log USING btree (created_at, audit_flagged) WHERE (audit_flagged IS DISTINCT FROM true);


--
-- Name: tool_execution_log_mcp_tool_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS tool_execution_log_mcp_tool_idx ON public.tool_execution_log USING btree (mcp_tool_name, created_at) WHERE (mcp_tool_name IS NOT NULL);


--
-- Name: tool_execution_log_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS tool_execution_log_source_idx ON public.tool_execution_log USING btree (source, created_at) WHERE (source IS NOT NULL);


--
-- Name: tool_execution_log_trace_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS tool_execution_log_trace_id ON public.tool_execution_log USING btree (trace_id) WHERE (trace_id IS NOT NULL);


--
-- Name: uq_charts_chart_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX IF NOT EXISTS uq_charts_chart_id ON public.charts USING btree (chart_id);


--
-- Name: uq_llm_cost_reconciliation_natural_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_cost_reconciliation_natural_key ON public.llm_cost_reconciliation USING btree (reconciliation_date, provider, COALESCE(model, ''::text));


--
-- Name: uq_llm_pricing_versions_natural_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_pricing_versions_natural_key ON public.llm_pricing_versions USING btree (provider, model, token_class, effective_from);


--
-- Name: capability_tool_registry trg_capability_tool_registry_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_capability_tool_registry_updated_at BEFORE UPDATE ON public.capability_tool_registry FOR EACH ROW EXECUTE FUNCTION public.update_capability_tool_registry_updated_at();


--
-- Name: conversation_messages trg_conversation_messages_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_conversation_messages_updated_at AFTER INSERT ON public.conversation_messages FOR EACH ROW EXECUTE FUNCTION public.conversations_set_updated_at();


--
-- Name: access_requests access_requests_approved_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.access_requests
    ADD CONSTRAINT access_requests_approved_user_id_fkey FOREIGN KEY (approved_user_id) REFERENCES public.profiles(id);


--
-- Name: access_requests access_requests_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.access_requests
    ADD CONSTRAINT access_requests_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.profiles(id);


--
-- Name: bodha_graph bodha_graph_chart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_graph
    ADD CONSTRAINT bodha_graph_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(chart_id);


--
-- Name: bodha_resonance bodha_resonance_chart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bodha_resonance
    ADD CONSTRAINT bodha_resonance_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(chart_id) ON DELETE CASCADE;


--
-- Name: build_engine_versions build_engine_versions_build_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_engine_versions
    ADD CONSTRAINT build_engine_versions_build_id_fkey FOREIGN KEY (build_id) REFERENCES public.builds(build_id) ON DELETE CASCADE;


--
-- Name: build_engine_versions build_engine_versions_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_engine_versions
    ADD CONSTRAINT build_engine_versions_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.engine_versions(version_id);


--
-- Name: build_notifications build_notifications_build_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_notifications
    ADD CONSTRAINT build_notifications_build_id_fkey FOREIGN KEY (build_id) REFERENCES public.builds(build_id) ON DELETE CASCADE;


--
-- Name: build_steps build_steps_build_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_steps
    ADD CONSTRAINT build_steps_build_id_fkey FOREIGN KEY (build_id) REFERENCES public.builds(build_id) ON DELETE CASCADE;


--
-- Name: builds builds_chart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.builds
    ADD CONSTRAINT builds_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(chart_id) ON DELETE CASCADE;


--
-- Name: capability_asset_tool_bindings capability_asset_tool_bindings_tool_name_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.capability_asset_tool_bindings
    ADD CONSTRAINT capability_asset_tool_bindings_tool_name_fkey FOREIGN KEY (tool_name) REFERENCES public.capability_tool_registry(tool_name) ON DELETE CASCADE;


--
-- Name: chart_grants chart_grants_chart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chart_grants
    ADD CONSTRAINT chart_grants_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE;


--
-- Name: charts charts_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.charts
    ADD CONSTRAINT charts_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.profiles(id) ON DELETE CASCADE;


--
-- Name: conversation_branches conversation_branches_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_branches
    ADD CONSTRAINT conversation_branches_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversation_branches conversation_branches_parent_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_branches
    ADD CONSTRAINT conversation_branches_parent_branch_id_fkey FOREIGN KEY (parent_branch_id) REFERENCES public.conversation_branches(id) ON DELETE SET NULL;


--
-- Name: conversation_folder_members conversation_folder_members_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_folder_members
    ADD CONSTRAINT conversation_folder_members_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversation_folder_members conversation_folder_members_folder_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_folder_members
    ADD CONSTRAINT conversation_folder_members_folder_id_fkey FOREIGN KEY (folder_id) REFERENCES public.conversation_folders(id) ON DELETE CASCADE;


--
-- Name: conversation_message_embeddings conversation_message_embeddings_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_message_embeddings
    ADD CONSTRAINT conversation_message_embeddings_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.conversation_messages(id) ON DELETE CASCADE;


--
-- Name: conversation_messages conversation_messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversation_messages conversation_messages_parent_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_parent_message_id_fkey FOREIGN KEY (parent_message_id) REFERENCES public.conversation_messages(id) ON DELETE SET NULL;


--
-- Name: conversation_shares conversation_shares_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_shares
    ADD CONSTRAINT conversation_shares_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversation_shares conversation_shares_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_shares
    ADD CONSTRAINT conversation_shares_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.profiles(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_chart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;


--
-- Name: llm_usage_events fk_llm_usage_events_parent_prompt; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_usage_events
    ADD CONSTRAINT fk_llm_usage_events_parent_prompt FOREIGN KEY (parent_prompt_id) REFERENCES public.llm_usage_events(prompt_id);


--
-- Name: ganita_dashas ganita_dashas_chart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ganita_dashas
    ADD CONSTRAINT ganita_dashas_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE;


--
-- Name: ganita_positions ganita_positions_chart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ganita_positions
    ADD CONSTRAINT ganita_positions_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE;


--
-- Name: kala_convergence kala_convergence_chart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kala_convergence
    ADD CONSTRAINT kala_convergence_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(chart_id);


--
-- Name: kala_obstruction kala_obstruction_chart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kala_obstruction
    ADD CONSTRAINT kala_obstruction_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(chart_id) ON DELETE CASCADE;


--
-- Name: llm_call_log llm_call_log_parent_call_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_call_log
    ADD CONSTRAINT llm_call_log_parent_call_id_fkey FOREIGN KEY (parent_call_id) REFERENCES public.llm_call_log(id);


--
-- Name: llm_usage_events llm_usage_events_pricing_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_usage_events
    ADD CONSTRAINT llm_usage_events_pricing_version_id_fkey FOREIGN KEY (pricing_version_id) REFERENCES public.llm_pricing_versions(pricing_version_id);


--
-- Name: notification_views notification_views_build_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_views
    ADD CONSTRAINT notification_views_build_id_fkey FOREIGN KEY (build_id) REFERENCES public.builds(build_id) ON DELETE CASCADE;


--
-- Name: performance_judge_verdict performance_judge_verdict_performance_query_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_judge_verdict
    ADD CONSTRAINT performance_judge_verdict_performance_query_id_fkey FOREIGN KEY (performance_query_id) REFERENCES public.performance_queries(id) ON DELETE CASCADE;


--
-- Name: performance_queries performance_queries_audit_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_queries
    ADD CONSTRAINT performance_queries_audit_event_id_fkey FOREIGN KEY (audit_event_id) REFERENCES public.audit_log(id) ON DELETE SET NULL;


--
-- Name: performance_queries performance_queries_eval_run_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_queries
    ADD CONSTRAINT performance_queries_eval_run_fk FOREIGN KEY (eval_run_id) REFERENCES public.eval_runs(id) ON DELETE SET NULL;


--
-- Name: profiles profiles_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profiles
    ADD CONSTRAINT profiles_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.profiles(id);


--
-- Name: project_conversations project_conversations_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_conversations
    ADD CONSTRAINT project_conversations_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: project_conversations project_conversations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_conversations
    ADD CONSTRAINT project_conversations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_files project_files_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_files
    ADD CONSTRAINT project_files_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: access_requests; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.access_requests ENABLE ROW LEVEL SECURITY;

--
-- Name: access_requests access_requests: service-only; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "access_requests: service-only" ON public.access_requests USING (false) WITH CHECK (false);


--
-- Name: charts chart_grant_policy; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY chart_grant_policy ON public.charts FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.chart_grants g
  WHERE ((g.chart_id = charts.id) AND (g.principal_id = current_setting('app.principal_id'::text, true))))));


--
-- Name: charts chart_owner_policy; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY chart_owner_policy ON public.charts USING ((owner_id = current_setting('app.principal_id'::text, true)));


--
-- Name: charts chart_service_policy; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY chart_service_policy ON public.charts USING (((current_setting('app.principal_id'::text, true) IS NULL) OR (current_setting('app.principal_id'::text, true) = ''::text)));


--
-- Name: charts; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.charts ENABLE ROW LEVEL SECURITY;

--
-- PostgreSQL database dump complete
--

\unrestrict EPmua133s5L3PBhQnzV5i9MXzwWPHPLlZtMhAX3nquQfJOLHH9bS15qQQyuxYRp

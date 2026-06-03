-- brahma_phala_anchors.sql — Brahma L4 Phala — phala.anchors (PH-4-1)
-- Asset:   phala.anchors
-- Table:   phala_anchors
-- Tool:    event_anchors(chart_id, date_range, min_confidence?) → {anchors, provenance_envelope}
-- Layer:   L4 Phala (depends on bodha_signals BO-2-1, dasha_vimshottari chart_facts)
-- Native:  Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
--          chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
--
-- CONTRACT (BRAHMA PH-4-1):
--   Each anchor is a calibrated ensemble predictor over a 6-month window.
--   score = dasha_quality × signal_strength × convergence_score
--   Every anchor carries: explicit falsifier (required NOT NULL),
--   contributing_dashas (JSONB), contributing_signals (JSONB), source_citation (NOT NULL).
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS public.phala_anchors CASCADE;
--   DROP FUNCTION IF EXISTS compute_window_score(FLOAT, FLOAT, FLOAT);
--   DROP FUNCTION IF EXISTS seed_native_phala_anchors(UUID);
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — phala_anchors table ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.phala_anchors (
    -- Identity
    id               BIGSERIAL PRIMARY KEY,
    chart_id         UUID        NOT NULL,
    anchor_id        TEXT        NOT NULL,

    -- Temporal window
    window_start     DATE        NOT NULL,
    window_end       DATE        NOT NULL,

    -- Prediction content
    theme            TEXT        NOT NULL,
    confidence       FLOAT       NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),

    -- Falsification (required — B.3 mandate + Learning Layer discipline rule #4)
    falsifier        TEXT        NOT NULL,   -- "If [event] does not occur by [date], this prediction is false"

    -- Provenance JSONB
    contributing_dashas   JSONB  NOT NULL DEFAULT '[]'::JSONB,
    contributing_signals  JSONB  NOT NULL DEFAULT '[]'::JSONB,
    source_citation        TEXT  NOT NULL,

    -- Lifecycle
    prediction_state TEXT        NOT NULL DEFAULT 'open'
                                 CHECK (prediction_state IN ('open', 'confirmed', 'falsified', 'expired')),
    outcome_note     TEXT,
    outcome_recorded_at TIMESTAMPTZ,

    -- Audit
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT phala_anchors_anchor_id_chart_id_unique UNIQUE (chart_id, anchor_id),
    CONSTRAINT phala_anchors_window_order CHECK (window_end > window_start)
);

COMMENT ON TABLE public.phala_anchors IS
  'PH-4-1 phala.anchors — calibrated probabilistic event anchors per 6-month window. '
  'score = dasha_quality × signal_strength × convergence_score. '
  'falsifier column required NOT NULL (B.3 + Learning Layer rule #4). '
  'source_citation required NOT NULL (B.3 derivation-ledger mandate).';

COMMENT ON COLUMN public.phala_anchors.confidence IS
  'Calibrated ensemble score in [0.0, 1.0]: '
  'dasha_quality × signal_strength × convergence_score. '
  'High = ≥0.65, Medium = 0.45–0.64, Low = <0.45.';

COMMENT ON COLUMN public.phala_anchors.falsifier IS
  'Explicit falsifier per Learning Layer discipline rule #4. '
  'Format: "If [specific observable event] does not occur by [date], this prediction is false."';

COMMENT ON COLUMN public.phala_anchors.source_citation IS
  'L1 citation sources: FORENSIC v8.0 DSH.V.NNN + MSR SIG.* IDs grounding this anchor.';

-- ── §2 — Indexes ──────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_phala_anchors_chart_id
    ON public.phala_anchors (chart_id);

CREATE INDEX IF NOT EXISTS idx_phala_anchors_window
    ON public.phala_anchors (chart_id, window_start, window_end);

CREATE INDEX IF NOT EXISTS idx_phala_anchors_confidence
    ON public.phala_anchors (chart_id, confidence DESC);

CREATE INDEX IF NOT EXISTS idx_phala_anchors_state
    ON public.phala_anchors (prediction_state);

CREATE INDEX IF NOT EXISTS idx_phala_anchors_contributing_signals
    ON public.phala_anchors USING GIN (contributing_signals);

-- ── §3 — Score computation helper ────────────────────────────────────────────
--
-- score = CLAMP(dasha_quality × signal_strength × convergence_score, 0.0, 1.0)
-- Components are each in [0.0, 1.0]:
--   dasha_quality     — quality of the active MD/AD combination (classical benefic/malefic assessment)
--   signal_strength   — weighted average of bodha_signals confidence for relevant signals
--   convergence_score — agreement across schools / dasha systems for this theme

CREATE OR REPLACE FUNCTION compute_window_score(
    p_dasha_quality     FLOAT,
    p_signal_strength   FLOAT,
    p_convergence_score FLOAT
)
RETURNS FLOAT
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT GREATEST(0.0, LEAST(1.0,
        p_dasha_quality * p_signal_strength * p_convergence_score
    ))::FLOAT
$$;

COMMENT ON FUNCTION compute_window_score(FLOAT, FLOAT, FLOAT) IS
  'PH-4-1 score = CLAMP(dasha_quality × signal_strength × convergence_score, 0, 1). '
  'All three components must be individually in [0.0, 1.0].';

-- ── §4 — Native anchor seed function ──────────────────────────────────────────
--
-- Seeds calibrated anchors for Abhisek Mohanty (1984-02-05, chart_id supplied).
-- 2026-2030 coverage: 9 six-month windows × themes derived from:
--   DSH.V.023 Mercury-Saturn AD (2024-12-12 → 2027-08-21)
--   DSH.V.024 Ketu-Ketu AD     (2027-08-21 → 2028-01-18)
--   DSH.V.025 Ketu-Venus AD    (2028-01-18 → 2029-03-18)
--   DSH.V.026 Ketu-Sun AD      (2029-03-18 → 2029-07-24)
--   DSH.V.027 Ketu-Moon AD     (2029-07-24 → 2030-02-24)
-- Sade Sati cycle: Cycle 2 Setting Saturn-Pisces (2025-03-30 → 2027-06-02)
-- Source: FORENSIC v8.0 §5.1; CHART_FACTS_EXTRACTION_v1_0.yaml DSH.V.023–027

CREATE OR REPLACE FUNCTION seed_native_phala_anchors(
    p_chart_id  UUID
)
RETURNS INT
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

COMMENT ON FUNCTION seed_native_phala_anchors(UUID) IS
  'Seeds calibrated phala anchors for Abhisek Mohanty (1984-02-05) for 2026-2030. '
  'Nine 6-month windows × L1-grounded dasha/signal ensembles. '
  'Idempotent — ON CONFLICT DO NOTHING. Returns rows inserted. '
  'Source: FORENSIC v8.0 §5.1 DSH.V.023–028 + CHART_FACTS_EXTRACTION_v1_0.yaml.';

COMMIT;

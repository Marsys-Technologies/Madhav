-- brahma_mimamsa_multiplier.sql — Brahma L5 Mīmāṃsā — mimamsa.multiplier (MI-5-4)
--
-- Asset:   mimamsa.multiplier
-- Table:   mimamsa_multipliers
-- Layer:   L5 Mīmāṃsā (final layer — internal to L4 computation; no MCP tool)
--
-- Algorithm:
--   learning_multiplier(technique, ayanamsha_id) =
--       CLAMP(1.0 + 0.1 × (0.5 - mean_brier_score), 0.8, 1.2)
--
--   mean_brier_score < 0.5 → multiplier > 1.0 (boost: technique performs above random)
--   mean_brier_score > 0.5 → multiplier < 1.0 (down-weight: below random)
--   mean_brier_score = 0.5 → multiplier = 1.0 (neutral: random baseline)
--
-- CONTRACT (BRAHMA MI-5-4):
--   - source_citation NOT NULL on all rows (B.3 mandate)
--   - multiplier CHECK(0.8 <= multiplier <= 1.2)
--   - sample_size > 0 required before any update (enforced at application layer)
--   - Classical layer modulated NOT overwritten
--   - NO LEAKAGE: life_events (LEL) feed calibration only, never prediction generation
--   - Migration: IF NOT EXISTS — safe to re-apply
--
-- Native:  Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
--          chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
--
-- Depends: FORENSIC v8.0 §5.1 (canonical L1 chart ground-truth)
--          LEL v1.7 §Events 1–57 (calibration outcomes ONLY)
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS public.mimamsa_multipliers CASCADE;
--   DROP FUNCTION IF EXISTS compute_mimamsa_multiplier(FLOAT);
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — mimamsa_multipliers table ───────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.mimamsa_multipliers (
    -- Identity (composite primary key: technique × ayanamsha)
    technique           TEXT        NOT NULL,
    ayanamsha_id        TEXT        NOT NULL,

    -- Learning multiplier (bounded: classical layer modulated NOT overwritten)
    multiplier          FLOAT       NOT NULL
                        CHECK (multiplier >= 0.8 AND multiplier <= 1.2),

    -- Audit trail
    last_updated        TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),

    -- Calibration metadata (sample_size > 0 enforced at application layer)
    sample_size         INT         NOT NULL CHECK (sample_size >= 0),

    -- Provenance (B.3 mandate — non-null)
    source_citation     TEXT        NOT NULL,

    PRIMARY KEY (technique, ayanamsha_id)
);

COMMENT ON TABLE public.mimamsa_multipliers IS
    'L5 Mīmāṃsā learning multipliers. Moves only from outcomes. '
    'Classical layer modulated NOT overwritten. '
    'multiplier = CLAMP(1.0 + 0.1 × (0.5 - mean_brier_score), 0.8, 1.2). '
    'source_citation required (B.3). '
    'NO LEAKAGE: life_events for calibration only, not prediction generation. '
    'BRAHMA-MI-5-4';

COMMENT ON COLUMN public.mimamsa_multipliers.technique IS
    'Classical technique name, e.g. vimshottari_dasha, kp_sub_lord, jaimini_chara_dasha';
COMMENT ON COLUMN public.mimamsa_multipliers.ayanamsha_id IS
    'Ayanamsha identifier, e.g. lahiri, raman, krishnamurti, yukteshwar';
COMMENT ON COLUMN public.mimamsa_multipliers.multiplier IS
    'Bounded learning multiplier in [0.8, 1.2]. '
    'Formula: CLAMP(1.0 + 0.1 × (0.5 - mean_brier_score), 0.8, 1.2). '
    'Modulates classical L4 output — does NOT overwrite it.';
COMMENT ON COLUMN public.mimamsa_multipliers.last_updated IS
    'UTC timestamp of the most recent calibration update for this technique × ayanamsha pair.';
COMMENT ON COLUMN public.mimamsa_multipliers.sample_size IS
    'Number of resolved predictions used to derive the current multiplier. '
    'Must be > 0 for any write to be valid (enforced at application layer).';
COMMENT ON COLUMN public.mimamsa_multipliers.source_citation IS
    'B.3 derivation-ledger citation: L1 fact IDs consumed by this row. '
    'Required non-null. Minimum: FORENSIC v8.0 §5.1; LEL v1.7 §Calibration-outcomes.';


-- ── §2 — Index for fast single-pair lookup (L4 → L5 hot path) ────────────────

CREATE INDEX IF NOT EXISTS idx_mimamsa_multipliers_lookup
    ON public.mimamsa_multipliers (technique, ayanamsha_id);


-- ── §3 — SQL helper: compute_mimamsa_multiplier ───────────────────────────────
--
-- Mirrors the Python compute_multiplier() function.
-- Used in SQL-level seeding and verification queries.

CREATE OR REPLACE FUNCTION compute_mimamsa_multiplier(mean_brier_score FLOAT)
RETURNS FLOAT
LANGUAGE sql
IMMUTABLE
STRICT
AS $$
    SELECT GREATEST(0.8, LEAST(1.2, 1.0 + 0.1 * (0.5 - mean_brier_score)));
$$;

COMMENT ON FUNCTION compute_mimamsa_multiplier(FLOAT) IS
    'Compute bounded learning multiplier from a mean Brier score. '
    'Returns CLAMP(1.0 + 0.1 × (0.5 - mean_brier_score), 0.8, 1.2). '
    'mean_brier_score < 0.5: multiplier > 1.0 (boost). '
    'mean_brier_score > 0.5: multiplier < 1.0 (down-weight). '
    'BRAHMA-MI-5-4';


-- ── §4 — Seed rows: native chart, Lahiri × 4 classical techniques ─────────────
--
-- Initial seed uses mean_brier_score = 0.5 (neutral / no evidence yet) → multiplier = 1.0.
-- These rows are the starting point. Updates flow from phala_anchors calibration outcomes.
--
-- Techniques seeded:
--   vimshottari_dasha  — primary Parashari dasha system (FORENSIC §5.1 DSH.V.*)
--   kp_sub_lord        — Krishnamurti Paddhati sub-lord system
--   jaimini_chara_dasha — Jaimini Chara Dasha (FORENSIC §5.3)
--   yogini_dasha       — Yogini dasha system (minor Parashari)
--
-- Ayanamshas seeded: lahiri (primary), krishnamurti (KP system), raman, yukteshwar
--
-- Source citation (all seed rows):
--   FORENSIC v8.0 §5.1 (Vimshottari ground-truth)
--   LEL v1.7 §Calibration-outcomes (0 resolved outcomes at seed time)
--   Brier (1950) Verification of Forecasts Expressed in Terms of Probability
--   BRAHMA MI-5-4

INSERT INTO public.mimamsa_multipliers
    (technique, ayanamsha_id, multiplier, sample_size, source_citation)
VALUES
    -- Vimshottari Dasha × all ayanamshas
    ('vimshottari_dasha', 'lahiri',
     compute_mimamsa_multiplier(0.5), 0,
     'FORENSIC v8.0 §5.1 DSH.V.*; LEL v1.7 §Calibration-outcomes (0 resolved at seed); Brier (1950); BRAHMA MI-5-4'),

    ('vimshottari_dasha', 'krishnamurti',
     compute_mimamsa_multiplier(0.5), 0,
     'FORENSIC v8.0 §5.1 DSH.V.*; LEL v1.7 §Calibration-outcomes (0 resolved at seed); Brier (1950); BRAHMA MI-5-4'),

    ('vimshottari_dasha', 'raman',
     compute_mimamsa_multiplier(0.5), 0,
     'FORENSIC v8.0 §5.1 DSH.V.*; LEL v1.7 §Calibration-outcomes (0 resolved at seed); Brier (1950); BRAHMA MI-5-4'),

    ('vimshottari_dasha', 'yukteshwar',
     compute_mimamsa_multiplier(0.5), 0,
     'FORENSIC v8.0 §5.1 DSH.V.*; LEL v1.7 §Calibration-outcomes (0 resolved at seed); Brier (1950); BRAHMA MI-5-4'),

    -- KP Sub-Lord × all ayanamshas
    ('kp_sub_lord', 'lahiri',
     compute_mimamsa_multiplier(0.5), 0,
     'FORENSIC v8.0 §5.1 KP sub-lord system; LEL v1.7 §Calibration-outcomes (0 resolved at seed); Brier (1950); BRAHMA MI-5-4'),

    ('kp_sub_lord', 'krishnamurti',
     compute_mimamsa_multiplier(0.5), 0,
     'FORENSIC v8.0 §5.1 KP sub-lord system; LEL v1.7 §Calibration-outcomes (0 resolved at seed); Brier (1950); BRAHMA MI-5-4'),

    -- Jaimini Chara Dasha × primary ayanamshas
    ('jaimini_chara_dasha', 'lahiri',
     compute_mimamsa_multiplier(0.5), 0,
     'FORENSIC v8.0 §5.3 Jaimini Chara Dasha; LEL v1.7 §Calibration-outcomes (0 resolved at seed); Brier (1950); BRAHMA MI-5-4'),

    ('jaimini_chara_dasha', 'raman',
     compute_mimamsa_multiplier(0.5), 0,
     'FORENSIC v8.0 §5.3 Jaimini Chara Dasha; LEL v1.7 §Calibration-outcomes (0 resolved at seed); Brier (1950); BRAHMA MI-5-4'),

    -- Yogini Dasha × lahiri
    ('yogini_dasha', 'lahiri',
     compute_mimamsa_multiplier(0.5), 0,
     'FORENSIC v8.0 §5.1 Yogini dasha system; LEL v1.7 §Calibration-outcomes (0 resolved at seed); Brier (1950); BRAHMA MI-5-4')

ON CONFLICT (technique, ayanamsha_id) DO NOTHING;


-- ── §5 — Verification query (informational — no side effects) ─────────────────
--
-- After applying this migration, run to verify:
--   SELECT technique, ayanamsha_id, multiplier, sample_size,
--          CASE WHEN multiplier BETWEEN 0.8 AND 1.2 THEN 'PASS' ELSE 'FAIL' END AS range_check,
--          CASE WHEN source_citation IS NOT NULL AND source_citation <> '' THEN 'PASS' ELSE 'FAIL' END AS b3_check
--   FROM public.mimamsa_multipliers
--   ORDER BY technique, ayanamsha_id;
--
-- Expected: 9 rows, all range_check='PASS', all b3_check='PASS', all multiplier=1.0 at seed.


COMMIT;

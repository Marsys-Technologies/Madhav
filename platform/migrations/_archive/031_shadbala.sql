-- platform/migrations/031_shadbala.sql
-- Migration: shadbala table (six-fold strength substrate; engine v1 = 4 of 6
--            components computed via pyswisseph + Lahiri sidereal; Sthana Bala
--            and Drik Bala marked [EXTERNAL_COMPUTATION_REQUIRED] per CLAUDE.md
--            §I B.10).
-- Created by M3-W3-C3-SHADBALA (2026-05-01).
-- Source:    compute_shadbala.py + 05_TEMPORAL_ENGINES/shadbala/SHADBALA_RAW_v1_0.json
-- Cross-check: 05_TEMPORAL_ENGINES/shadbala/CROSSCHECK_v1_0.md
--   (AC.M3C.4 anchors PASS: Saturn Uccha 59.19 vs FORENSIC 59.18 Δ+0.01;
--    Sun Uccha 33.99 vs FORENSIC 33.99 Δ+0.00; Verdict: WITHIN_TOLERANCE_PENDING_REVIEW
--    on Naisargika + Nathonnatha findings flagged for native disposition.)
-- Idempotent: CREATE ... IF NOT EXISTS + ON CONFLICT DO NOTHING for INSERT rows.
--
-- Carry-forward at M3-W3-C3 close: per session DB pre-check, migrations 022-025
-- have not been applied to the live DB at session-open
-- (to_regclass returned NULL for dasha_periods, signal_states, kp_sublords,
-- varshaphala). Migration 031 is self-contained and does not depend on those
-- tables; native authorization required to apply 022-031 together.

BEGIN;

CREATE TABLE IF NOT EXISTS shadbala (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id            TEXT         NOT NULL,
    planet              TEXT         NOT NULL,
    query_date          DATE         NOT NULL,
    query_context       TEXT,                              -- 'natal' | 'current' | 'MD_start_<lord>' | 'MD_end_<lord>'
    uccha_bala          NUMERIC,                           -- pyswisseph-computed (D1.a)
    dig_bala            NUMERIC,                           -- pyswisseph-computed (D1.b; Placidus angles)
    naisargika_bala     NUMERIC,                           -- constant per planet (D1.c)
    nathonnatha_bala    NUMERIC,                           -- pyswisseph-computed via Sun altitude (D1.d)
    partial_total       NUMERIC,                           -- = uccha + dig + naisargika + nathonnatha
                                                            --   (excludes ECR Sthana + Drik)
    sthana_ecr          BOOLEAN      NOT NULL DEFAULT true, -- always true in engine v1 — JH export required
    drik_ecr            BOOLEAN      NOT NULL DEFAULT true, -- always true in engine v1 — JH export required
    ecr_components      TEXT[],                             -- ['sthana', 'drik']
    needs_verification  BOOLEAN      NOT NULL DEFAULT true,
    computed_by         TEXT         NOT NULL DEFAULT 'pyswisseph',
    ayanamsha           TEXT         NOT NULL DEFAULT 'lahiri',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (chart_id, planet, query_date, query_context)
);

CREATE INDEX IF NOT EXISTS idx_shadbala_chart_date
    ON shadbala (chart_id, query_date);

CREATE INDEX IF NOT EXISTS idx_shadbala_planet
    ON shadbala (chart_id, planet);

-- Data inserts: 63 rows (9 snapshots × 7 planets) for the native chart at the
-- time-of-day = native birth time-of-day convention (10:43 IST). Source rows
-- emitted verbatim from compute_shadbala.py output to keep the migration
-- self-contained for offline replays.

INSERT INTO shadbala (chart_id, planet, query_date, query_context, uccha_bala, dig_bala, naisargika_bala, nathonnatha_bala, partial_total, sthana_ecr, drik_ecr, ecr_components, needs_verification, computed_by, ayanamsha) VALUES ('abhisek_mohanty_primary', 'Sun', '1984-02-05', 'MD_start_Jupiter', 33.9913, 53.6726, 7.5, 58.0606, 153.2245, true, true, ARRAY['sthana','drik']::TEXT[], true, 'pyswisseph 2.10.03', 'lahiri') ON CONFLICT (chart_id, planet, query_date, query_context) DO NOTHING;
INSERT INTO shadbala (chart_id, planet, query_date, query_context, uccha_bala, dig_bala, naisargika_bala, nathonnatha_bala, partial_total, sthana_ecr, drik_ecr, ecr_components, needs_verification, computed_by, ayanamsha) VALUES ('abhisek_mohanty_primary', 'Moon', '1984-02-05', 'MD_start_Jupiter', 38.0241, 18.0258, 10.0, 1.9394, 67.9893, true, true, ARRAY['sthana','drik']::TEXT[], true, 'pyswisseph 2.10.03', 'lahiri') ON CONFLICT (chart_id, planet, query_date, query_context) DO NOTHING;
INSERT INTO shadbala (chart_id, planet, query_date, query_context, uccha_bala, dig_bala, naisargika_bala, nathonnatha_bala, partial_total, sthana_ecr, drik_ecr, ecr_components, needs_verification, computed_by, ayanamsha) VALUES ('abhisek_mohanty_primary', 'Mars', '1984-02-05', 'MD_start_Jupiter', 26.8401, 35.1842, 30.0, 1.9394, 93.9637, true, true, ARRAY['sthana','drik']::TEXT[], true, 'pyswisseph 2.10.03', 'lahiri') ON CONFLICT (chart_id, planet, query_date, query_context) DO NOTHING;
INSERT INTO shadbala (chart_id, planet, query_date, query_context, uccha_bala, dig_bala, naisargika_bala, nathonnatha_bala, partial_total, sthana_ecr, drik_ecr, ecr_components, needs_verification, computed_by, ayanamsha) VALUES ('abhisek_mohanty_primary', 'Mercury', '1984-02-05', 'MD_start_Jupiter', 24.7167, 26.1432, 25.0, 60.0, 135.8599, true, true, ARRAY['sthana','drik']::TEXT[], true, 'pyswisseph 2.10.03', 'lahiri') ON CONFLICT (chart_id, planet, query_date, query_context) DO NOTHING;
INSERT INTO shadbala (chart_id, planet, query_date, query_context, uccha_bala, dig_bala, naisargika_bala, nathonnatha_bala, partial_total, sthana_ecr, drik_ecr, ecr_components, needs_verification, computed_by, ayanamsha) VALUES ('abhisek_mohanty_primary', 'Jupiter', '1984-02-05', 'MD_start_Jupiter', 8.4072, 19.1232, 20.0, 58.0606, 105.591, true, true, ARRAY['sthana','drik']::TEXT[], true, 'pyswisseph 2.10.03', 'lahiri') ON CONFLICT (chart_id, planet, query_date, query_context) DO NOTHING;
INSERT INTO shadbala (chart_id, planet, query_date, query_context, uccha_bala, dig_bala, naisargika_bala, nathonnatha_bala, partial_total, sthana_ecr, drik_ecr, ecr_components, needs_verification, computed_by, ayanamsha) VALUES ('abhisek_mohanty_primary', 'Venus', '1984-02-05', 'MD_start_Jupiter', 27.3905, 4.6037, 15.0, 1.9394, 48.9336, true, true, ARRAY['sthana','drik']::TEXT[], true, 'pyswisseph 2.10.03', 'lahiri') ON CONFLICT (chart_id, planet, query_date, query_context) DO NOTHING;
INSERT INTO shadbala (chart_id, planet, query_date, query_context, uccha_bala, dig_bala, naisargika_bala, nathonnatha_bala, partial_total, sthana_ecr, drik_ecr, ecr_components, needs_verification, computed_by, ayanamsha) VALUES ('abhisek_mohanty_primary', 'Saturn', '1984-02-05', 'MD_start_Jupiter', 59.1864, 56.6605, 60.0, 58.0606, 233.9075, true, true, ARRAY['sthana','drik']::TEXT[], true, 'pyswisseph 2.10.03', 'lahiri') ON CONFLICT (chart_id, planet, query_date, query_context) DO NOTHING;

-- The remaining 56 rows (8 snapshots × 7 planets) for query_dates
-- 1991-08-19 / 2010-08-18 / 2026-05-01 / 2027-08-19 / 2034-08-18 / 2054-08-18 /
-- 2060-08-18 / 2070-08-18 are emitted in the SHADBALA_INSERT_v1_0.sql sibling
-- file in 05_TEMPORAL_ENGINES/shadbala/. To apply the full 63-row dataset:
--
--   psql "$DATABASE_URL" < platform/migrations/031_shadbala.sql            -- (creates table + 7 natal rows)
--   psql "$DATABASE_URL" < 05_TEMPORAL_ENGINES/shadbala/SHADBALA_INSERT_v1_0.sql  -- (applies all 63 idempotently)
--
-- This split keeps migration 031 small and verifiable as a schema migration
-- with a natal-row sanity payload, while the over-time series ships as a
-- companion data file (same pattern as 022_dasha_periods.sql + VIMSHOTTARI_INSERT
-- in M3-W2-B1).

COMMIT;

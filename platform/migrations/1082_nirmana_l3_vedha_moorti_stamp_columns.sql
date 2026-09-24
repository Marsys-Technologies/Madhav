-- Migration 1082: kala_vedha_gochara + kala_moorti_nirnaya — overlay stamp columns
--                 (source_qualification / precision_regime / corpus_verifiable)
-- Created: 2026-09-24
-- WP9 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1 §5.4): every Vedha/Moorti overlay row
-- served on the WP0-7 kernel carries three machine-readable stamps:
--   * source_qualification ∈ {verse_cited, algorithmic_approximation, unsourced}
--       — house_vedha is verse_cited (bg_transit_rules + Phaladīpikā XXVI);
--         sarvatobhadra is algorithmic_approximation exactly when
--         grid_basis='algorithmic_approximation' (the current, only-populated
--         state; see migration 526's R-19 disclosure); latta is verse_cited
--         except the Ketu gap (Ketu rows are simply never emitted —
--         bg_phaladeepika_latta has no Ketu rule). Vipareeta-vedha exceptions
--         on house_vedha rows are translator commentary, not verse — recorded
--         as detail.vipareeta.source_qualification='translator_commentary'
--         (the CHECK vocabulary has only three values; the row-level stamp
--         stays verse_cited because the house_vedha rule itself is).
--   * precision_regime ∈ {date_grain, instant_grain}
--       — date_grain on every current row (all three vedha kinds and moorti are
--         computed from ephemeris_daily, one row per day); instant_grain only
--         on moorti rows graded at a true kernel ingress instant (WP9 5.3).
--   * corpus_verifiable BOOLEAN
--       — FALSE on house_vedha rows whose bg_transit_rules citation is the
--         struck "BPHS Ch.29" string (39 of 41 favourable+vedha rules; only
--         the Rāhu-11th/Ketu-11th rules cite Phaladīpikā XXVI) until the G-9
--         re-citation lands; FALSE on sarvatobhadra rows while the served grid
--         is the algorithmic approximation; TRUE on latta rows (Phaladīpikā
--         PG338-339, REAL cited); moorti rows are corpus_verifiable exactly
--         when moorti_computed (bg_transit_moorti, migration 401, REAL cited).
-- Author: nirmana l3 autonomous gochara run (WP9, overlay stamps on the kernel).
--
-- Numbering: 1082 is the next-free number in the shared platform/migrations +
-- platform/supabase/migrations sequence (1081 is this branch's own WP6 ledger
-- migration; origin/l0/vedha-and-frame-repair holds 1075-1079; origin/main max
-- is 1070). Verified 2026-09-24 by directory listing of both paths + git
-- branches.
--
-- DESIGN ARTIFACT for WP9: this file is applied ONLY to the disposable WP6
-- database (docker gochara-wp6-disposable). It must NEVER be applied to a
-- shared or production database; production application is WP10-gated.
--
-- Shape notes (each deliberate):
--   * Purely additive ALTERs — no existing column or constraint is touched;
--     the base tables' natural keys, window-order CHECKs and
--     computed-consistency CHECK (525/526) are unchanged.
--   * Columns are nullable at the DDL level so pre-existing rows (if any) do
--     not violate on apply; the WP9 writers populate all three on EVERY row
--     they emit, and the WP9 tests assert non-null coverage on writer output.
--   * The stamps deliberately mirror the migration-670 integrity-contract
--     conjuncts they tighten: conjunct (a) (sbc uncited ⟺
--     grid_basis='algorithmic_approximation') now has a machine-readable twin
--     in source_qualification; conjunct (c) (house_vedha restates
--     bg_transit_rules verbatim) gains the corpus_verifiable companion.
--
-- ROLLBACK (down-migration):
--   ALTER TABLE kala_moorti_nirnaya
--     DROP COLUMN IF EXISTS source_qualification,
--     DROP COLUMN IF EXISTS precision_regime,
--     DROP COLUMN IF EXISTS corpus_verifiable;
--   ALTER TABLE kala_vedha_gochara
--     DROP COLUMN IF EXISTS source_qualification,
--     DROP COLUMN IF EXISTS precision_regime,
--     DROP COLUMN IF EXISTS corpus_verifiable;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

ALTER TABLE kala_vedha_gochara
  ADD COLUMN IF NOT EXISTS source_qualification TEXT
    CHECK (source_qualification IN ('verse_cited', 'algorithmic_approximation', 'unsourced')),
  ADD COLUMN IF NOT EXISTS precision_regime TEXT
    CHECK (precision_regime IN ('date_grain', 'instant_grain')),
  ADD COLUMN IF NOT EXISTS corpus_verifiable BOOLEAN;

COMMENT ON COLUMN kala_vedha_gochara.source_qualification IS
  'WP9 overlay stamp: verse_cited | algorithmic_approximation | unsourced. '
  'sarvatobhadra is algorithmic_approximation exactly when grid_basis='
  '''algorithmic_approximation''; house_vedha/latta are verse_cited.';
COMMENT ON COLUMN kala_vedha_gochara.precision_regime IS
  'WP9 overlay stamp: date_grain (ephemeris_daily, current state) | '
  'instant_grain (kernel ingress instant — only after kernel-graded rows land).';
COMMENT ON COLUMN kala_vedha_gochara.corpus_verifiable IS
  'WP9 overlay stamp: FALSE on house_vedha rows citing struck "BPHS Ch.29" '
  '(until G-9 re-citation) and on sarvatobhadra rows served by the algorithmic '
  'approximation; TRUE on latta rows.';

ALTER TABLE kala_moorti_nirnaya
  ADD COLUMN IF NOT EXISTS source_qualification TEXT
    CHECK (source_qualification IN ('verse_cited', 'algorithmic_approximation', 'unsourced')),
  ADD COLUMN IF NOT EXISTS precision_regime TEXT
    CHECK (precision_regime IN ('date_grain', 'instant_grain')),
  ADD COLUMN IF NOT EXISTS corpus_verifiable BOOLEAN;

COMMENT ON COLUMN kala_moorti_nirnaya.source_qualification IS
  'WP9 overlay stamp: verse_cited when moorti_computed (bg_transit_moorti, '
  'migration 401, REAL cited); unsourced when the moorti could not be computed.';
COMMENT ON COLUMN kala_moorti_nirnaya.precision_regime IS
  'WP9 overlay stamp: date_grain (ingress day from ephemeris_daily) | '
  'instant_grain (true kernel sign-ingress instant, WP9 5.3).';
COMMENT ON COLUMN kala_moorti_nirnaya.corpus_verifiable IS
  'WP9 overlay stamp: TRUE exactly when moorti_computed.';

COMMIT;

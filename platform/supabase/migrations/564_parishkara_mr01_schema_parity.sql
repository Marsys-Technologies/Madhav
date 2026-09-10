-- Migration 564: kala_gochara_windows schema parity — PARIṢKĀRA MR-01
-- =============================================================================
-- GAP: the three gochara MCP tools (gochara_activation_get, gochara_forecast_get,
-- gochara_election_avoidance_get) all returned HTTP 500 with "column
-- term_breakdown does not exist" because register_gochara_windows.ts line ~300
-- selects `generation, era_slice_key, term_breakdown` (and 5 more v3 columns)
-- from kala_gochara_windows. Those 8 v3 output-model columns existed ONLY on
-- the staging table kala_gochara_windows_v2 (migrations 558/559) but were
-- never backfilled to the production table kala_gochara_windows.
--
-- FIX: add all 8 missing columns to kala_gochara_windows as nullable. They
-- will be NULL for all existing v1 rows (which is honest: those rows were
-- written before these columns were designed). v3 rows written by the
-- ka_gochara materializer (post-W5.4 repoint) will populate them.
--
-- THE 8 COLUMNS (mirrored from kala_gochara_windows_v2 migrations 558 + 559):
--   From migration 559 (W1.5 λ decomposition):
--     term_breakdown     JSONB         — per-mechanism λ_v3 decomposition
--     lambda_v3_ci_low   DOUBLE PRECISION — lower bound of 80% CI on λ_v3
--     lambda_v3_ci_high  DOUBLE PRECISION — upper bound of 80% CI on λ_v3
--     ci_source          TEXT          — how the CI was computed
--   From migration 558 (W1.4 self-normalizing thresholds):
--     threshold_lambda       NUMERIC(12,8) — λ_thresh for activation
--     threshold_percentile   NUMERIC(8,6)  — percentile P used for threshold
--     implied_density        NUMERIC(10,4) — windows/year implied by threshold
--     base_rate_cited        NUMERIC(8,6)  — age-band base rate from ontology
--
-- All eight are NULLABLE: existing rows keep NULL and remain valid under the
-- new schema. NULL is the honest "not computed for this row" value per §N.4
-- ("Floors aspirational, not gates": never fabricate data to fill a column).
--
-- ROW_COLUMNS false comment fix: the W5.1 comment at ~line 303 in
-- register_gochara_windows.ts claimed these columns were "present on
-- kala_gochara_windows since migrations 527/556/559" — that was false. They
-- were only on kala_gochara_windows_v2. The comment is corrected in the
-- accompanying TS change (Commit 4) to name migration 564.
--
-- IDEMPOTENT: ADD COLUMN IF NOT EXISTS — safe to re-run. The self-
-- verification DO block at the end raises if any column is still missing after
-- the ADD, per §N.4 "a migration that cannot verify itself is not trustworthy".
--
-- PROTECTED CORPUS: kala_gochara_windows carries the v1 sweep corpus for
-- charts 482012f1 and 1c826d5a (build_protected_assets). This migration is
-- schema-only (ADD COLUMN, no INSERT/UPDATE/DELETE of any row) — the
-- protection triggers (migration 540) are row-level and never fire on DDL.
-- Grep-verifiable: this file contains no INSERT, UPDATE, or DELETE targeting
-- kala_gochara_windows rows.
-- =============================================================================

BEGIN;

SET LOCAL lock_timeout = '2s';

-- ── 1. Add the 4 W1.5 λ-decomposition columns (from migration 559 on _v2) ───

ALTER TABLE kala_gochara_windows
  ADD COLUMN IF NOT EXISTS term_breakdown     JSONB,
  ADD COLUMN IF NOT EXISTS lambda_v3_ci_low   DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS lambda_v3_ci_high  DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS ci_source          TEXT;

COMMENT ON COLUMN kala_gochara_windows.term_breakdown IS
  'Migration 564 (PARIṢKĀRA MR-01): per-mechanism λ_v3 decomposition. '
  'Mirrors kala_gochara_windows_v2.term_breakdown (migration 559). '
  'Structure: {promise, permission, activity, quality_gates, lambda_v3, '
  'activity_terms: [{primitive, target_ref, orb_decay, target_weight, p_i}]}. '
  'NULL on v1 rows (written before GOCHARA-UTKARSA W1.5; v1_parity_mode=True '
  'path never populates this column).';

COMMENT ON COLUMN kala_gochara_windows.lambda_v3_ci_low IS
  'Migration 564 (PARIṢKĀRA MR-01): lower bound of the 80% credible interval '
  'on lambda_v3. Pre-calibration formula: max(0, lambda_v3 * 0.8). '
  'Mirrors kala_gochara_windows_v2.lambda_v3_ci_low (migration 559). '
  'NULL on v1 rows. ci_source column discloses which band this is.';

COMMENT ON COLUMN kala_gochara_windows.lambda_v3_ci_high IS
  'Migration 564 (PARIṢKĀRA MR-01): upper bound of the 80% credible interval '
  'on lambda_v3. Pre-calibration formula: min(1, lambda_v3 * 1.2). '
  'Mirrors kala_gochara_windows_v2.lambda_v3_ci_high (migration 559). '
  'NULL on v1 rows. ci_source column discloses which band this is.';

COMMENT ON COLUMN kala_gochara_windows.ci_source IS
  'Migration 564 (PARIṢKĀRA MR-01): how the credible interval was computed. '
  'Values: ''structural_prior'' (±20% symmetric pre-calibration band, W1.5 '
  'default), ''fitted_posterior'' (Wave-4.5 calibrated posteriors, deferred). '
  'Mirrors kala_gochara_windows_v2.ci_source (migration 559). '
  'NULL on v1 rows.';

-- ── 2. Add the 4 W1.4 self-normalizing threshold columns (from migration 558) ─

ALTER TABLE kala_gochara_windows
  ADD COLUMN IF NOT EXISTS threshold_lambda       NUMERIC(12,8),
  ADD COLUMN IF NOT EXISTS threshold_percentile   NUMERIC(8,6),
  ADD COLUMN IF NOT EXISTS implied_density        NUMERIC(10,4),
  ADD COLUMN IF NOT EXISTS base_rate_cited        NUMERIC(8,6);

COMMENT ON COLUMN kala_gochara_windows.threshold_lambda IS
  'Migration 564 (PARIṢKĀRA MR-01): λ_thresh = percentile(P) of the century-scale '
  'λ_v3 distribution. A JD is "active" iff λ_v3 ≥ threshold_lambda. In [0,1]. '
  'Mirrors kala_gochara_windows_v2.threshold_lambda (migration 558). '
  'NULL for pre-W1.4 rows or v1_parity_mode rows.';

COMMENT ON COLUMN kala_gochara_windows.threshold_percentile IS
  'Migration 564 (PARIṢKĀRA MR-01): percentile P ∈ [0,1] of the century-scale '
  'λ_v3 distribution used as the activation threshold. Derived from '
  'P = 1 − base_rate_cited × Δt (Δt = 1/52 yr). '
  'Mirrors kala_gochara_windows_v2.threshold_percentile (migration 558). '
  'NULL for rows written before W1.4 or in v1_parity_mode.';

COMMENT ON COLUMN kala_gochara_windows.implied_density IS
  'Migration 564 (PARIṢKĀRA MR-01): windows/year implied by threshold_lambda on '
  'this chart×class, estimated from the century sample. >52 → density_flag '
  'pathological_dense; 0 on nonzero base_rate → density_flag starved. '
  'Mirrors kala_gochara_windows_v2.implied_density (migration 558). '
  'NULL for pre-W1.4 rows.';

COMMENT ON COLUMN kala_gochara_windows.base_rate_cited IS
  'Migration 564 (PARIṢKĀRA MR-01): normalized age-band base rate from '
  'brahma_event_ontology.base_rate_by_age that drove threshold_percentile. '
  'band_41_60 for native age ~42 at evaluation time. '
  'Mirrors kala_gochara_windows_v2.base_rate_cited (migration 558). '
  'NULL for pre-W1.4 rows or fallback-only rows.';

-- ── 3. Self-verification (§N.4 mandate) ──────────────────────────────────────
-- A migration that cannot verify itself is not trustworthy. Each of the 8 new
-- columns is checked individually; the block raises with a named error so the
-- exact missing column is identified in the failure message.

DO $$
BEGIN
  -- 3a. term_breakdown
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows'
       AND column_name  = 'term_breakdown'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-564 SELF-CHECK FAILED: term_breakdown column missing on kala_gochara_windows';
  END IF;

  -- 3b. lambda_v3_ci_low
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows'
       AND column_name  = 'lambda_v3_ci_low'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-564 SELF-CHECK FAILED: lambda_v3_ci_low column missing on kala_gochara_windows';
  END IF;

  -- 3c. lambda_v3_ci_high
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows'
       AND column_name  = 'lambda_v3_ci_high'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-564 SELF-CHECK FAILED: lambda_v3_ci_high column missing on kala_gochara_windows';
  END IF;

  -- 3d. ci_source
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows'
       AND column_name  = 'ci_source'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-564 SELF-CHECK FAILED: ci_source column missing on kala_gochara_windows';
  END IF;

  -- 3e. threshold_lambda
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows'
       AND column_name  = 'threshold_lambda'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-564 SELF-CHECK FAILED: threshold_lambda column missing on kala_gochara_windows';
  END IF;

  -- 3f. threshold_percentile
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows'
       AND column_name  = 'threshold_percentile'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-564 SELF-CHECK FAILED: threshold_percentile column missing on kala_gochara_windows';
  END IF;

  -- 3g. implied_density
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows'
       AND column_name  = 'implied_density'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-564 SELF-CHECK FAILED: implied_density column missing on kala_gochara_windows';
  END IF;

  -- 3h. base_rate_cited
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows'
       AND column_name  = 'base_rate_cited'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-564 SELF-CHECK FAILED: base_rate_cited column missing on kala_gochara_windows';
  END IF;

  -- 3i. All 8 new columns are nullable (must not have NOT NULL constraint —
  --     existing v1 rows carry NULL and must remain valid).
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows'
       AND column_name  IN (
         'term_breakdown', 'lambda_v3_ci_low', 'lambda_v3_ci_high', 'ci_source',
         'threshold_lambda', 'threshold_percentile', 'implied_density', 'base_rate_cited'
       )
       AND is_nullable = 'NO'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-564 SELF-CHECK FAILED: one or more of the 8 new columns '
      'on kala_gochara_windows has NOT NULL constraint — must be nullable (v1 rows carry NULL)';
  END IF;

END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   ALTER TABLE kala_gochara_windows
--     DROP COLUMN IF EXISTS term_breakdown,
--     DROP COLUMN IF EXISTS lambda_v3_ci_low,
--     DROP COLUMN IF EXISTS lambda_v3_ci_high,
--     DROP COLUMN IF EXISTS ci_source,
--     DROP COLUMN IF EXISTS threshold_lambda,
--     DROP COLUMN IF EXISTS threshold_percentile,
--     DROP COLUMN IF EXISTS implied_density,
--     DROP COLUMN IF EXISTS base_rate_cited;
--   COMMIT;
-- Safe: all 8 columns are wholly owned by this migration. No existing row data
-- is modified — only the schema extension is reversed. The v1 row corpus (with
-- its NULL values in these columns) is unaffected by both this migration and
-- its DOWN. No INSERT/UPDATE/DELETE of kala_gochara_windows rows in either
-- direction — the protection triggers (migration 540) are never invoked by DDL.
-- =============================================================================

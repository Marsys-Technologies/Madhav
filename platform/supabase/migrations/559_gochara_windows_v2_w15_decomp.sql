-- Migration 559: kala_gochara_windows_v2 — W1.5 λ decomposition + structural prior CI
-- =============================================================================
-- GOCHARA-UTKARṢA campaign, wave W1.5 (λ decomposition + uncertainty output model).
--
-- Adds three nullable columns to kala_gochara_windows_v2 carrying the per-row
-- λ decomposition (term_breakdown JSONB) and the 80% structural-prior credible
-- interval (lambda_v3_ci_low, lambda_v3_ci_high, ci_source) produced by the
-- W1.5-patched gochara_v3 engine.
--
-- ADDITIVE-ONLY (AC4): all columns are nullable with no default constraint
-- beyond nullability — existing rows keep NULL in these columns and remain
-- valid under the schema. No column is removed, renamed, or has its type
-- changed. No existing index is dropped or altered.
--
-- WHY NULLABLE (not NOT NULL with DEFAULT):
--   v1-parity rows (v1_parity_mode=True) never populate these fields;
--   forcing a default would misrepresent the absence of a W1.5 decomposition.
--   NULL is the honest "not computed for this row" value, not a missing value.
--
-- AC5 invariant: v1-parity rows (those written via the v1 formula path) will
--   have NULL in all three columns — this is by design, not a gap. The writer
--   only populates them when IntensityResult.term_breakdown is not None.
--
-- ci_source values (text, no FK constraint — extensible for Wave-4.5):
--   'structural_prior'  — ±20% symmetric band, pre-calibration (W1.5)
--   'fitted_posterior'  — posterior from outcome calibration (Wave 4.5+)
--
-- kala_gochara_windows (v1, protected) is NOT touched by this migration.
-- grep-verifiable: the literal string 'kala_gochara_windows' appears in this
-- file ONLY as a strict prefix of 'kala_gochara_windows_v2', inside comments.
--
-- Idempotent: ADD COLUMN IF NOT EXISTS; verification DO blocks are safe to
-- re-run (they raise only if the column is absent after the ADD).
-- =============================================================================

BEGIN;

SET LOCAL lock_timeout = '2s';

-- ── 1. Add the three W1.5 nullable columns ───────────────────────────────────

-- Only run if kala_gochara_windows_v2 exists (created by migration 542, which
-- may not be present in every target environment). A missing table means the
-- W2G surface was never provisioned — the migration no-ops safely.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
     WHERE table_schema = 'public'
       AND table_name = 'kala_gochara_windows_v2'
  ) THEN
    EXECUTE 'ALTER TABLE kala_gochara_windows_v2
               ADD COLUMN IF NOT EXISTS term_breakdown     jsonb,
               ADD COLUMN IF NOT EXISTS lambda_v3_ci_low  double precision,
               ADD COLUMN IF NOT EXISTS lambda_v3_ci_high double precision,
               ADD COLUMN IF NOT EXISTS ci_source         text';

    EXECUTE $comment$
      COMMENT ON COLUMN kala_gochara_windows_v2.term_breakdown IS
        'Migration 557 (GOCHARA-UTKARṢA W1.5): per-mechanism λ_v3 decomposition. '
        'Structure: {promise, permission, activity, quality_gates, lambda_v3, '
        'activity_terms: [{primitive, target_ref, orb_decay, target_weight, p_i}, ...], '
        'formula: "PROMISE × PERMISSION × activity × quality_gates"}. '
        'NULL on v1-parity rows (v1_parity_mode=True path never populates this column).'
    $comment$;

    EXECUTE $comment$
      COMMENT ON COLUMN kala_gochara_windows_v2.lambda_v3_ci_low IS
        'Migration 557 (GOCHARA-UTKARṢA W1.5): lower bound of the 80% credible '
        'interval on lambda_v3. Pre-calibration formula: max(0, lambda_v3 * 0.8). '
        'NULL on v1-parity rows. ci_source column discloses which band this is.'
    $comment$;

    EXECUTE $comment$
      COMMENT ON COLUMN kala_gochara_windows_v2.lambda_v3_ci_high IS
        'Migration 557 (GOCHARA-UTKARṢA W1.5): upper bound of the 80% credible '
        'interval on lambda_v3. Pre-calibration formula: min(1, lambda_v3 * 1.2). '
        'NULL on v1-parity rows. ci_source column discloses which band this is.'
    $comment$;

    EXECUTE $comment$
      COMMENT ON COLUMN kala_gochara_windows_v2.ci_source IS
        'Migration 557 (GOCHARA-UTKARṢA W1.5): how the credible interval was '
        'computed. Values: ''structural_prior'' (±20% symmetric pre-calibration '
        'band, W1.5 default), ''fitted_posterior'' (Wave-4.5 calibrated posteriors, '
        'not yet implemented). NULL on v1-parity rows.'
    $comment$;

  END IF;
END;
$$;

-- ── 2. Verification (§N.4 — a migration that cannot verify itself is not ─────
--         trustworthy) ────────────────────────────────────────────────────────

-- Only verify when the table exists (same guard as the ADD above).
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
     WHERE table_schema = 'public'
       AND table_name = 'kala_gochara_windows_v2'
  ) THEN
    -- 2a. term_breakdown column exists
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
       WHERE table_schema = 'public'
         AND table_name = 'kala_gochara_windows_v2'
         AND column_name = 'term_breakdown'
    ) THEN
      RAISE EXCEPTION 'MIGRATION-557 VERIFICATION FAILED: term_breakdown column missing on kala_gochara_windows_v2';
    END IF;

    -- 2b. lambda_v3_ci_low column exists
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
       WHERE table_schema = 'public'
         AND table_name = 'kala_gochara_windows_v2'
         AND column_name = 'lambda_v3_ci_low'
    ) THEN
      RAISE EXCEPTION 'MIGRATION-557 VERIFICATION FAILED: lambda_v3_ci_low column missing on kala_gochara_windows_v2';
    END IF;

    -- 2c. lambda_v3_ci_high column exists
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
       WHERE table_schema = 'public'
         AND table_name = 'kala_gochara_windows_v2'
         AND column_name = 'lambda_v3_ci_high'
    ) THEN
      RAISE EXCEPTION 'MIGRATION-557 VERIFICATION FAILED: lambda_v3_ci_high column missing on kala_gochara_windows_v2';
    END IF;

    -- 2d. ci_source column exists
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
       WHERE table_schema = 'public'
         AND table_name = 'kala_gochara_windows_v2'
         AND column_name = 'ci_source'
    ) THEN
      RAISE EXCEPTION 'MIGRATION-557 VERIFICATION FAILED: ci_source column missing on kala_gochara_windows_v2';
    END IF;

    -- 2e. All three new columns are nullable (no NOT NULL constraint)
    IF EXISTS (
      SELECT 1 FROM information_schema.columns
       WHERE table_schema = 'public'
         AND table_name = 'kala_gochara_windows_v2'
         AND column_name IN ('term_breakdown', 'lambda_v3_ci_low',
                             'lambda_v3_ci_high', 'ci_source')
         AND is_nullable = 'NO'
    ) THEN
      RAISE EXCEPTION 'MIGRATION-557 VERIFICATION FAILED: one or more W1.5 columns on kala_gochara_windows_v2 are NOT NULL — must be nullable (v1-parity rows carry NULL)';
    END IF;

  END IF;
END;
$$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   ALTER TABLE kala_gochara_windows_v2
--     DROP COLUMN IF EXISTS term_breakdown,
--     DROP COLUMN IF EXISTS lambda_v3_ci_low,
--     DROP COLUMN IF EXISTS lambda_v3_ci_high,
--     DROP COLUMN IF EXISTS ci_source;
--   COMMIT;
-- Safe: all four columns are wholly owned by this migration (created here,
-- no other migration or constraint references them). Existing rows lose only
-- the W1.5 decomposition data — all other row content is unaffected.
-- kala_gochara_windows (v1, protected) is never referenced or modified by
-- this migration or its DOWN.
-- =============================================================================

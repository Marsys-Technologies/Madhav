-- Migration 556: gochara generation schema — GOCHARA-UTKARSA W0.3
-- =============================================================================
-- Two-phase deploy making generation-3.0 rows coexist safely with v1 rows in
-- kala_gochara_windows:
--
--   1. `era_slice_key` column on both gochara tables (future use).
--   2. `protected_generations` column on build_protected_assets (generation-
--      aware guard scoping).
--   3. Replace the generation-blind unique index (migration 460) with a
--      generation-inclusive one — so a 3.0 row with the same natural key as
--      a v1 row does NOT collide.
--   4. Amend the row-level guard function to check OLD.generation against
--      the protected_generations array — so a generation-3.0 DELETE passes
--      while a v1 DELETE still raises on protected charts.
--
-- Invariants:
--   I1: v1 rows for charts 482012f1-… and 1c826d5a-… are UNTOUCHABLE.
--   I6: No destructive SQL outside reviewed migrations.
--
-- Idempotency: all DDL uses IF NOT EXISTS / IF EXISTS / CREATE OR REPLACE /
--   DROP … IF EXISTS + re-CREATE patterns. Re-run is a clean no-op.
-- =============================================================================

BEGIN;

SET LOCAL lock_timeout = '2s';

-- ─── 1. era_slice_key column on both gochara tables ─────────────────────────

ALTER TABLE kala_gochara_windows
  ADD COLUMN IF NOT EXISTS era_slice_key TEXT;

COMMENT ON COLUMN kala_gochara_windows.era_slice_key IS
  'Migration 556 (GOCHARA-UTKARSA W0.3): optional era-slice key for generation '
  '3.0 rows. NULL for v1 rows (which predate this column). Future use.';

-- kala_gochara_windows_v2 may not exist in all environments (created by
-- migration 542, which is on the shad-darshana branch and may not have merged
-- to every target). Guard with a DO block so this migration never fails on
-- a database that lacks the table.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
     WHERE table_schema = 'public'
       AND table_name = 'kala_gochara_windows_v2'
  ) THEN
    EXECUTE 'ALTER TABLE kala_gochara_windows_v2 ADD COLUMN IF NOT EXISTS era_slice_key TEXT';
    EXECUTE $comment$
      COMMENT ON COLUMN kala_gochara_windows_v2.era_slice_key IS
        'Migration 556 (GOCHARA-UTKARSA W0.3): optional era-slice key for generation '
        '3.0 rows. Mirrors kala_gochara_windows.era_slice_key.'
    $comment$;
  END IF;
END;
$$;

-- ─── 2. protected_generations column on build_protected_assets ──────────────

ALTER TABLE build_protected_assets
  ADD COLUMN IF NOT EXISTS protected_generations TEXT[] NOT NULL DEFAULT '{v1}';

COMMENT ON COLUMN build_protected_assets.protected_generations IS
  'Migration 556 (GOCHARA-UTKARSA W0.3): array of generation labels whose rows '
  'are protected for this (asset_id, chart_id) pair. Default ''{v1}'' protects '
  'the original sweep corpus. A generation NOT in this array (e.g. ''3.0'') can '
  'be freely DELETEd/UPDATEd without the override GUC.';

-- ─── 3. Replace the generation-blind unique index ───────────────────────────
-- The old index (migration 460):
--   (chart_id, event_class, window_start, peak_date, COALESCE(milestone_id, ''))
-- The new index adds `generation` so a 3.0 row with the same natural key as a
-- v1 row coexists without collision.

DROP INDEX IF EXISTS uq_kala_gochara_windows_natural_key;

CREATE UNIQUE INDEX uq_kala_gochara_windows_natural_key
  ON kala_gochara_windows (
    chart_id, event_class, window_start, peak_date,
    COALESCE(milestone_id, ''), generation
  );

-- ─── 4. Amend the row-level guard function ──────────────────────────────────
-- The CURRENT function (migration 540) is generation-blind: it refuses ANY
-- DELETE/UPDATE on a protected chart_id regardless of the row's generation.
-- The AMENDED function checks OLD.generation against the protected_generations
-- array: a DELETE of a generation='3.0' row passes (not in '{v1}'), while a
-- DELETE of a generation='v1' row still raises.

CREATE OR REPLACE FUNCTION build_protected_assets_guard_row()
RETURNS TRIGGER AS $$
BEGIN
  -- Explicit, per-session, non-default override. `true` as the second arg to
  -- current_setting means "missing_ok" — an unset GUC reads as NULL rather
  -- than raising, so the IF below is false (not an error) when nobody has
  -- opted in.
  IF current_setting('app.allow_protected_sweep_rewrite', true) = 'on' THEN
    RETURN COALESCE(NEW, OLD);
  END IF;

  -- Generation-aware check (migration 556, GOCHARA-UTKARSA W0.3): only refuse
  -- if this row's generation is in the protected_generations array for this
  -- (asset_id, chart_id) pair. A generation NOT listed (e.g. '3.0' when
  -- protected_generations = '{v1}') passes through without the override.
  IF EXISTS (
    SELECT 1 FROM build_protected_assets
     WHERE asset_id = 'ka_gochara_sweep'
       AND chart_id = OLD.chart_id
       AND OLD.generation = ANY(protected_generations)
  ) THEN
    RAISE EXCEPTION
      'BUILD-PROTECTED: kala_gochara_windows row(s) for chart_id % generation % '
      '(asset_id=ka_gochara_sweep) are protected — % is refused. Set '
      'app.allow_protected_sweep_rewrite=on for this session to override '
      '(native decision required; see build_protected_assets.reason).',
      OLD.chart_id, OLD.generation, TG_OP;
  END IF;

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION build_protected_assets_guard_row() IS
  'Migration 556 amends migration 540''s row-level guard to be generation-aware: '
  'only rows whose generation is in build_protected_assets.protected_generations '
  'are protected. A generation NOT in that array (e.g. ''3.0'') can be freely '
  'DELETEd/UPDATEd without the override GUC. The trigger attachment on '
  'kala_gochara_windows (trg_kala_gochara_windows_protect_row) is unchanged — '
  'CREATE OR REPLACE FUNCTION updates the function body in place without '
  'needing to re-create the trigger.';

-- ─── 5. Verification (§N.4 — a migration that cannot verify itself is not ───
--         trustworthy) ────────────────────────────────────────────────────────

-- 5a. era_slice_key exists on kala_gochara_windows
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'kala_gochara_windows'
       AND column_name = 'era_slice_key'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-556 VERIFICATION FAILED: era_slice_key column missing on kala_gochara_windows';
  END IF;
END;
$$;

-- 5b. protected_generations exists on build_protected_assets
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'build_protected_assets'
       AND column_name = 'protected_generations'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-556 VERIFICATION FAILED: protected_generations column missing on build_protected_assets';
  END IF;
END;
$$;

-- 5c. The unique index includes generation (6 columns, not 5)
-- Postgres stores the index column count in pg_index.indnatts. The old index
-- had 5 key columns; the new one has 6. This is the most direct check that
-- the DROP + re-CREATE actually applied.
DO $$
DECLARE
  _nkeys INT;
BEGIN
  SELECT indnatts INTO _nkeys
    FROM pg_index
    JOIN pg_class ON pg_class.oid = pg_index.indexrelid
   WHERE pg_class.relname = 'uq_kala_gochara_windows_natural_key';
  IF _nkeys IS NULL THEN
    RAISE EXCEPTION 'MIGRATION-556 VERIFICATION FAILED: uq_kala_gochara_windows_natural_key index not found';
  END IF;
  IF _nkeys <> 6 THEN
    RAISE EXCEPTION 'MIGRATION-556 VERIFICATION FAILED: uq_kala_gochara_windows_natural_key has % key columns, expected 6', _nkeys;
  END IF;
END;
$$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   SET LOCAL lock_timeout = '2s';
--
--   -- Restore the generation-blind unique index
--   DROP INDEX IF EXISTS uq_kala_gochara_windows_natural_key;
--   CREATE UNIQUE INDEX uq_kala_gochara_windows_natural_key
--     ON kala_gochara_windows (chart_id, event_class, window_start, peak_date, COALESCE(milestone_id, ''));
--
--   -- Restore the generation-blind guard function (migration 540 original)
--   CREATE OR REPLACE FUNCTION build_protected_assets_guard_row()
--   RETURNS TRIGGER AS $$
--   BEGIN
--     IF current_setting('app.allow_protected_sweep_rewrite', true) = 'on' THEN
--       RETURN COALESCE(NEW, OLD);
--     END IF;
--     IF EXISTS (
--       SELECT 1 FROM build_protected_assets
--        WHERE asset_id = 'ka_gochara_sweep' AND chart_id = OLD.chart_id
--     ) THEN
--       RAISE EXCEPTION 'BUILD-PROTECTED: ...', OLD.chart_id, TG_OP;
--     END IF;
--     RETURN COALESCE(NEW, OLD);
--   END;
--   $$ LANGUAGE plpgsql;
--
--   ALTER TABLE build_protected_assets DROP COLUMN IF EXISTS protected_generations;
--   ALTER TABLE kala_gochara_windows DROP COLUMN IF EXISTS era_slice_key;
--   -- kala_gochara_windows_v2.era_slice_key: DROP IF EXISTS separately if table exists
--   COMMIT;
-- =============================================================================

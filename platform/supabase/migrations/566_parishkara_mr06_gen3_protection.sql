-- Migration 566: gen-3.0 row protection on kala_gochara_windows
-- =============================================================================
-- PARISHKARA campaign, MR-06 (cutover durability).
--
-- BACKGROUND:
--   Migration 556 (GOCHARA-UTKARSA W0.3) added `protected_generations TEXT[]`
--   to build_protected_assets with DEFAULT '{v1}', and amended the row-level
--   guard (build_protected_assets_guard_row) to check OLD.generation against
--   that array. This means:
--     - Deleting a v1 row for a protected chart → RAISES (correct).
--     - Deleting a generation='3.0' row for a protected chart → PASSES
--       (3.0 not in '{v1}' — the guard intentionally allows it).
--
--   Plan W6.4 promised that after the cutover, generation='3.0' rows in
--   kala_gochara_windows (the authority-generation rows written by the renamed
--   ka_gochara materializer) would receive their OWN protection — a BEFORE
--   DELETE trigger that refuses unauthorized deletion of gen-3.0 rows.
--   This protection was NEVER authored. MR-06 closes that gap.
--
-- DESIGN DECISION — separate trigger, not extending the migration-540 guard:
--   The migration-540 guard is asset_id='ka_gochara_sweep'-scoped (by design:
--   it protects the v1 sweep corpus). The post-cutover materializer is
--   asset_id='ka_gochara'. Rather than re-scope the existing guard (which
--   would require modifying migration 540's trigger function, breaking the
--   frozen guarantee), this migration:
--
--   1. Inserts (ka_gochara, <both canonical charts>) rows into
--      build_protected_assets so the planner-side guard (plan.ts) withholds
--      the renamed materializer from rebuild/clear plans.
--
--   2. Adds protected_generations = '{3.0}' on those rows (NOT '{v1}' — the
--      materializer's rows carry generation='3.0', the protected generation).
--
--   3. Creates a NEW trigger function + trigger on kala_gochara_windows that
--      refuses DELETE of generation='3.0' rows for protected charts unless
--      app.allow_protected_sweep_rewrite='on'. This is structurally parallel
--      to the migration-540 guard for v1, but scoped to generation='3.0' and
--      asset_id='ka_gochara'.
--
-- INVARIANTS (binding on this migration and its trigger):
--   I1: v1 rows for protected charts are UNTOUCHABLE (existing migration-540
--       guard — this migration does NOT modify it).
--   I2: generation='3.0' rows for both canonical charts are now UNTOUCHABLE
--       without app.allow_protected_sweep_rewrite='on'.
--   I3: No DDL touches kala_gochara_windows's schema or existing rows —
--       only TRIGGER and FUNCTION creation, plus registry inserts.
--
-- Migration-number coordination:
--   Checked CAMPAIGN_COORDINATION.md on origin/campaign-coordination:
--   "| 566+ | — | next free; claim here before use | — |" — 566 was free.
--   PARIṢKĀRA MR-06 claims 566. Migration file lives in
--   platform/supabase/migrations/ (consistent with 540/542/556/560-562).
--
-- Idempotency: CREATE OR REPLACE FUNCTION, DROP TRIGGER IF EXISTS + CREATE
--   TRIGGER, INSERT ... ON CONFLICT DO NOTHING for registry rows.
--   Re-running is a clean no-op rebuild of the same trigger definitions.
-- =============================================================================

BEGIN;

SET LOCAL lock_timeout = '2s';

-- ── 1. Register ka_gochara in build_protected_assets for both canonical charts ─

-- Insert (ka_gochara, native chart) — protected since W6.4 cutover
INSERT INTO build_protected_assets (asset_id, chart_id, reason, protected_generations)
VALUES (
  'ka_gochara',
  '482012f1-710e-4a25-994a-93821f5871aa',
  'PARISHKARA MR-06 (2026-08-10): post-cutover gen-3.0 protection. '
  'ka_gochara (renamed from ka_gochara_v2_materialize at W6.4, migration 563) '
  'is the new authority materializer writing kala_gochara_windows with '
  'generation=''3.0''. Its rows for the native chart are as expensive to rebuild '
  'as the v1 sweep and must not be silently destroyed. Protected_generations '
  'is set to ''{3.0}'' (not ''{v1}'') — this guard covers the new generation, '
  'migration 540''s guard covers v1.',
  '{3.0}'
)
ON CONFLICT (asset_id, chart_id) DO NOTHING;

-- Insert (ka_gochara, Abhinandan chart) — same protection
INSERT INTO build_protected_assets (asset_id, chart_id, reason, protected_generations)
VALUES (
  'ka_gochara',
  '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
  'PARISHKARA MR-06 (2026-08-10): post-cutover gen-3.0 protection. '
  'Same protection extended to the second canonical chart (Abhinandan Mohanty), '
  'the standing SAFE non-native rebuild/rehearsal subject '
  '(REBUILD_SESSION_PLAN_v1_0.md). Protected_generations=''{3.0}''.',
  '{3.0}'
)
ON CONFLICT (asset_id, chart_id) DO NOTHING;

-- ── 2. Trigger function: gen-3.0 row guard ───────────────────────────────────

CREATE OR REPLACE FUNCTION build_gen3_gochara_guard_row()
RETURNS TRIGGER AS $$
BEGIN
  -- Explicit, per-session, non-default override. `true` as the second arg to
  -- current_setting means "missing_ok" — an unset GUC reads as NULL rather
  -- than raising, so the IF below is false (not an error) when nobody has
  -- opted in.
  IF current_setting('app.allow_protected_sweep_rewrite', true) = 'on' THEN
    RETURN COALESCE(NEW, OLD);
  END IF;

  -- Only intercept generation='3.0' rows (this guard is the gen-3.0 parallel
  -- to migration 540's generation='v1' guard; the two guards are independent).
  IF OLD.generation <> '3.0' THEN
    RETURN COALESCE(NEW, OLD);
  END IF;

  -- Check if this (ka_gochara, chart_id) pair is protected for generation='3.0'.
  IF EXISTS (
    SELECT 1 FROM build_protected_assets
     WHERE asset_id = 'ka_gochara'
       AND chart_id = OLD.chart_id
       AND '3.0' = ANY(protected_generations)
  ) THEN
    RAISE EXCEPTION
      'BUILD-PROTECTED: kala_gochara_windows row(s) for chart_id % '
      '(generation=3.0, asset_id=ka_gochara) are protected — % is refused. '
      'Set app.allow_protected_sweep_rewrite=on for this session to override '
      '(native decision required; see build_protected_assets.reason for '
      'PARISHKARA MR-06 protection rationale).',
      OLD.chart_id, TG_OP;
  END IF;

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION build_gen3_gochara_guard_row() IS
  'PARISHKARA MR-06 (migration 566): BEFORE DELETE/UPDATE guard for '
  'generation=''3.0'' rows on kala_gochara_windows. Parallel to migration '
  '540''s build_protected_assets_guard_row() which covers generation=''v1''. '
  'Refuses to modify a gen-3.0 row whose chart_id is protected for '
  'asset_id=''ka_gochara'' in build_protected_assets, unless '
  'app.allow_protected_sweep_rewrite=on is set for the session. '
  'INSERT is never gated (normal write path). The existing migration-540 '
  'trigger covers v1 rows; this trigger covers 3.0 rows exclusively.';

-- ── 3. Attach the trigger to kala_gochara_windows ────────────────────────────

DROP TRIGGER IF EXISTS trg_kala_gochara_windows_protect_gen3_row ON kala_gochara_windows;
CREATE TRIGGER trg_kala_gochara_windows_protect_gen3_row
  BEFORE DELETE OR UPDATE ON kala_gochara_windows
  FOR EACH ROW EXECUTE FUNCTION build_gen3_gochara_guard_row();

-- ── 4. Self-verification ─────────────────────────────────────────────────────

-- 4a. Both build_protected_assets rows for ka_gochara exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM build_protected_assets
     WHERE asset_id = 'ka_gochara'
       AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  ) THEN
    RAISE EXCEPTION
      'MIGRATION-566 VERIFICATION FAILED: ka_gochara protection row missing '
      'for native chart (482012f1-...)';
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM build_protected_assets
     WHERE asset_id = 'ka_gochara'
       AND chart_id = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
  ) THEN
    RAISE EXCEPTION
      'MIGRATION-566 VERIFICATION FAILED: ka_gochara protection row missing '
      'for Abhinandan chart (1c826d5a-...)';
  END IF;
END;
$$;

-- 4b. The trigger exists on kala_gochara_windows
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.triggers
     WHERE event_object_table = 'kala_gochara_windows'
       AND trigger_name = 'trg_kala_gochara_windows_protect_gen3_row'
  ) THEN
    RAISE EXCEPTION
      'MIGRATION-566 VERIFICATION FAILED: '
      'trg_kala_gochara_windows_protect_gen3_row trigger not found on '
      'kala_gochara_windows';
  END IF;
END;
$$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   SET LOCAL lock_timeout = '2s';
--   DROP TRIGGER IF EXISTS trg_kala_gochara_windows_protect_gen3_row ON kala_gochara_windows;
--   DROP FUNCTION IF EXISTS build_gen3_gochara_guard_row();
--   DELETE FROM build_protected_assets
--     WHERE asset_id = 'ka_gochara'
--       AND chart_id IN (
--         '482012f1-710e-4a25-994a-93821f5871aa',
--         '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
--       );
--   COMMIT;
-- Safe: kala_gochara_windows schema and data are untouched by both this
--  migration and its DOWN. The DOWN removes only what this migration added:
--  the trigger, the function, and the two build_protected_assets rows.
-- =============================================================================

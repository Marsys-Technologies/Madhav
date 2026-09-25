-- Migration 1120: bg_prashna_rules registry row — NULL target_table made honest.
-- Created: 2026-09-25
--
-- W-L0-1 (MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md §4.2, "Registry truth",
-- and §3.1 operational honesty): bg_prashna_rules carries target_table NULL while
-- being a five-table asset. The strategy authorizes "five tables, or a declared
-- multi-table set"; the chosen form is the declared multi-table set — the five
-- peer tables as a comma-separated target_table, with the description naming
-- the set and its seeder. count_sql already aggregates the same five tables and
-- is unchanged.
--
-- Companion code change (same worktree, prerequisite — already landed on
-- l0/nirmana-elevation-20260921): every consumer that resolves target_table to
-- relation names now splits on ',' — asset_registry_seed.ts pre-flight,
-- generate_tci.ts bootstrapMaps, assetClearSpec.ts (EXPLICIT_CLEAR_OPS for the
-- five tables), AtlasView.tsx getDisplayTables, dag_edge_guard.py
-- _producer_tables — so the comma-set is a serving-safe declaration, not a
-- string that 500s the clear paths.
--
-- Guard discipline (migration 1075 pattern): this migration refuses to run
-- unless the live row still carries the exact pre-fix state (target_table NULL
-- plus the original short description), so it cannot silently overwrite a row
-- another session already moved on. It also refuses if any of the five tables
-- it declares is absent — the declaration must not name a phantom.
--
-- HELD: authored 2026-09-25 against the unreconciled _migrations_applied ledger
-- (1080–1095 effects live, ledger empty). Apply only after the consolidation
-- session (madhav-65) reconciles the ledger and the strategy session confirms
-- the number. Number 1120 chosen by scanning every origin/* head across BOTH
-- platform/migrations/ (head 1091) and platform/supabase/migrations/ (head
-- 1090): no 1092–1199 exists on any ref.
--
-- Transaction ownership belongs to migrate.ts.

BEGIN;

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  prior_description constant text :=
    'Static horary astrology rules — Prashna lagna methods, Tajik yogas, significators, fructification rules, and special techniques.';
  canonical_target constant text :=
    'bg_prashna_lagna_methods,bg_prashna_tajik_yogas,bg_prashna_significators,bg_prashna_fructification_rules,bg_prashna_special_techniques';
  canonical_description constant text :=
    'Static horary astrology rules — Prashna lagna methods, Tajik yogas, ' ||
    'significators, fructification rules, and special techniques. Five peer ' ||
    'tables (declared multi-table set, comma-separated): bg_prashna_lagna_methods, ' ||
    'bg_prashna_tajik_yogas, bg_prashna_significators, ' ||
    'bg_prashna_fructification_rules, bg_prashna_special_techniques — seeded ' ||
    'together by l0_prashna.seed_prashna_rules; no single one is the primary table.';
  member_table text;
BEGIN
  -- Pre-flight: every table the declaration names must exist.
  FOREACH member_table IN ARRAY string_to_array(canonical_target, ',')
  LOOP
    IF to_regclass(member_table) IS NULL THEN
      RAISE EXCEPTION 'migration 1120 refuses: declared member table % does not exist', member_table;
    END IF;
  END LOOP;

  SELECT * INTO registry_row
  FROM asset_registry
  WHERE asset_id = 'bg_prashna_rules'
  FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.target_table IS NULL
    AND registry_row.english_description = prior_description
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 1120 refuses: bg_prashna_rules does not match the expected pre-fix state (target_table NULL + original description) — already moved on by another session';
  END IF;

  UPDATE asset_registry
  SET target_table = canonical_target,
      english_description = canonical_description
  WHERE asset_id = 'bg_prashna_rules';

  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 1120 expected 1 row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_prashna_rules'
      AND target_table = canonical_target
      AND english_description = canonical_description
  ) THEN
    RAISE EXCEPTION 'migration 1120 postflight registry mismatch';
  END IF;
END $$;

COMMIT;

-- =============================================================================
-- VERIFY (falsifier — run after apply):
--   SELECT target_table FROM asset_registry WHERE asset_id = 'bg_prashna_rules';
--   -- expect: bg_prashna_lagna_methods,bg_prashna_tajik_yogas,bg_prashna_significators,
--   --         bg_prashna_fructification_rules,bg_prashna_special_techniques
--
-- DOWN (manual rollback — restores exactly the pre-fix state):
--   BEGIN;
--   UPDATE asset_registry
--      SET target_table = NULL,
--          english_description = 'Static horary astrology rules — Prashna lagna methods, Tajik yogas, significators, fructification rules, and special techniques.'
--    WHERE asset_id = 'bg_prashna_rules';
--   COMMIT;
-- =============================================================================

-- 589_drop_orphaned_protection_functions.sql
--
-- Follow-up to 588. Migration 588 dropped the three protection TRIGGERS and
-- emptied build_protected_assets, but its DROP FUNCTION statements named the
-- functions incorrectly (they were guessed from the trigger names, not read from
-- migrations 540/566), so they were no-ops — psql reported "does not exist,
-- skipping" for all three.
--
-- The actual function names are below. They are now orphaned: verified that no
-- trigger in the database references any of them after 588.
--
-- 588 is NOT edited — it has been applied (CLAUDE.md §N.4: never edit an applied
-- migration). This migration corrects it forward.
--
-- REVERSIBLE: re-apply migrations 540 and 566 to recreate both the functions and
-- their triggers.

BEGIN;

DROP FUNCTION IF EXISTS build_protected_assets_guard_row();
DROP FUNCTION IF EXISTS build_protected_assets_guard_truncate();
DROP FUNCTION IF EXISTS build_gen3_gochara_guard_row();

COMMIT;

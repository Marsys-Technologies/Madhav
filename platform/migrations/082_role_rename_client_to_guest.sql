-- 082_role_rename_client_to_guest.sql
-- Unit 2c (Stream B) — rename profiles.role value 'client' → 'guest'.
-- super_admin unchanged. Idempotent + safe to re-run.
--
-- profiles.role is a text column with a CHECK constraint (no Postgres enum type).
-- See migration 117 (audience_tier) for the same pattern.

BEGIN;

DO $$
DECLARE
  v_conname text;
BEGIN
  -- 1. Drop any existing role CHECK constraint (regardless of its current name).
  SELECT c.conname
    INTO v_conname
    FROM pg_constraint c
    JOIN pg_class      t ON t.oid = c.conrelid
   WHERE t.relname = 'profiles'
     AND c.contype = 'c'
     AND pg_get_constraintdef(c.oid) ILIKE '%role%'
   LIMIT 1;

  IF v_conname IS NOT NULL THEN
    EXECUTE format('ALTER TABLE profiles DROP CONSTRAINT %I', v_conname);
  END IF;

  -- 2. Backfill 'client' → 'guest'.
  UPDATE profiles SET role = 'guest' WHERE role = 'client';

  -- 3. Re-add CHECK constraint with the new allowed value set.
  ALTER TABLE profiles
    ADD CONSTRAINT profiles_role_check
    CHECK (role IN ('guest', 'super_admin'));
END $$;

COMMIT;

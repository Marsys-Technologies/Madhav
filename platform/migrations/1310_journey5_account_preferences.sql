-- Migration 1310: Journey 5 owner account preferences
-- Created: 2026-10-06
-- Additive/backward-compatible; no automatic persona or credential mutation.
-- Transaction and application receipt are owned by scripts/migrate.ts.
SET LOCAL lock_timeout = '5s';
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS account_preferences jsonb NOT NULL DEFAULT '{}'::jsonb;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.profiles'::regclass AND conname='profiles_account_preferences_object') THEN
  ALTER TABLE public.profiles ADD CONSTRAINT profiles_account_preferences_object CHECK (jsonb_typeof(account_preferences)='object');
 END IF;
END $$;
COMMENT ON COLUMN public.profiles.account_preferences IS 'Own-user display/panel/reading preferences; strict allowlist validated by account API. Persona and exact AI configuration defaults retain their existing authorities.';

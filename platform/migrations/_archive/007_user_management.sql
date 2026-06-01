-- Migration 007: User management
-- Adds username + status lifecycle to profiles, renames the legacy 'astrologer'
-- role to 'super_admin', and creates an access_requests table for the public
-- sign-up queue. All steps are idempotent.
--
-- Rollback (manual):
--   ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_role_check;
--   UPDATE public.profiles SET role = 'astrologer' WHERE role = 'super_admin';
--   ALTER TABLE public.profiles ADD CONSTRAINT profiles_role_check
--     CHECK (role IN ('astrologer','client'));
--   ALTER TABLE public.profiles
--     DROP COLUMN IF EXISTS approved_by,
--     DROP COLUMN IF EXISTS approved_at,
--     DROP COLUMN IF EXISTS status,
--     DROP COLUMN IF EXISTS email,
--     DROP COLUMN IF EXISTS username;
--   DROP INDEX IF EXISTS profiles_email_unique;
--   DROP INDEX IF EXISTS profiles_username_unique;
--   DROP TABLE IF EXISTS public.access_requests;

-- ─── Step 1: profiles — new columns ──────────────────────────────────────────

ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS username     text,
  ADD COLUMN IF NOT EXISTS email        text,
  ADD COLUMN IF NOT EXISTS status       text NOT NULL DEFAULT 'active'
    CHECK (status IN ('pending','active','disabled')),
  ADD COLUMN IF NOT EXISTS approved_at  timestamptz,
  ADD COLUMN IF NOT EXISTS approved_by  text REFERENCES public.profiles(id);

-- Username is unique once populated (case-insensitive). NULL allowed for legacy rows.
CREATE UNIQUE INDEX IF NOT EXISTS profiles_username_unique
  ON public.profiles (lower(username))
  WHERE username IS NOT NULL;

-- Email is unique once populated (case-insensitive).
CREATE UNIQUE INDEX IF NOT EXISTS profiles_email_unique
  ON public.profiles (lower(email))
  WHERE email IS NOT NULL;

-- ─── Step 2: rename role enum value 'astrologer' → 'super_admin' ─────────────

ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_role_check;
UPDATE public.profiles SET role = 'super_admin' WHERE role = 'astrologer';
ALTER TABLE public.profiles ADD CONSTRAINT profiles_role_check
  CHECK (role IN ('super_admin','client'));

-- Default for new rows: clients (matches the original schema's default behaviour).
ALTER TABLE public.profiles ALTER COLUMN role SET DEFAULT 'client';

-- ─── Step 3: backfill the existing super-admin row (Abhisek) ─────────────────

-- The seed row inserted by 006_firebase_uid_schema.sql gets username + email
-- so login-by-username works immediately after this migration runs.
UPDATE public.profiles
   SET username = 'abhisek',
       email    = 'mail.abhisek.mohanty@gmail.com'
 WHERE id = 'xl2wYZRPwsVgPSAgtn9XJ80Xkub2';

-- ─── Step 4: access_requests table ───────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.access_requests (
  id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name         text        NOT NULL,
  email             text        NOT NULL,
  reason            text,
  status            text        NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','approved','rejected')),
  requested_at      timestamptz NOT NULL DEFAULT now(),
  reviewed_at       timestamptz,
  reviewed_by       text        REFERENCES public.profiles(id),
  approved_user_id  text        REFERENCES public.profiles(id)
);

-- A given email may have at most one pending request at a time. Rejected/approved
-- rows are not subject to this — the user can re-request after a rejection.
CREATE UNIQUE INDEX IF NOT EXISTS access_requests_pending_email_unique
  ON public.access_requests (lower(email))
  WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS access_requests_status_requested_at_idx
  ON public.access_requests (status, requested_at DESC);

-- ─── Step 5: RLS for access_requests (defence-in-depth) ──────────────────────

-- All platform queries go through createServiceClient() (service-role bypasses
-- RLS by design). This deny-all policy ensures that if the anon/auth client is
-- ever used here by mistake, no row leaks.
ALTER TABLE public.access_requests ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "access_requests: service-only" ON public.access_requests;
CREATE POLICY "access_requests: service-only" ON public.access_requests
  FOR ALL USING (false) WITH CHECK (false);

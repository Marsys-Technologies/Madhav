-- Migration 006: Firebase Auth UID compatibility
-- The platform migrated from Supabase Auth to Firebase Auth. Firebase UIDs are
-- text strings (e.g. "xl2wYZRPwsVgPSAgtn9XJ80Xkub2"), not Supabase UUIDs.
-- This migration:
--   1. Drops legacy RLS policies that depend on auth.uid() / changing columns
--   2. Drops FKs that reference profiles.id or auth.users
--   3. Changes all user-identity columns from uuid → text
--   4. Re-adds inter-table FKs (profiles only, not auth.users)
--   5. Seeds the astrologer profile with the Firebase UID
--
-- RLS-policy note: All public-schema policies referenced auth.uid(), which is
-- a Supabase-Auth construct. Under Firebase Auth + service-role-only access
-- (every server query uses SUPABASE_SERVICE_ROLE_KEY which bypasses RLS),
-- these policies were dead code. Dropping them aligns the schema with reality
-- and unblocks the type change. See routes/clients/[id]/layout.tsx and
-- lib/supabase/server.ts for the service-role access pattern.

-- ─── Step 0: Drop legacy Supabase-Auth RLS policies ──────────────────────────

DROP POLICY IF EXISTS "profiles: read own"                  ON public.profiles;
DROP POLICY IF EXISTS "profiles: update own"                ON public.profiles;
DROP POLICY IF EXISTS "charts: astrologer all"              ON public.charts;
DROP POLICY IF EXISTS "charts: client own"                  ON public.charts;
DROP POLICY IF EXISTS "chat_attachments: astrologer all"    ON public.chat_attachments;
DROP POLICY IF EXISTS "chat_attachments: client own"        ON public.chat_attachments;
DROP POLICY IF EXISTS "conversation_shares: astrologer all" ON public.conversation_shares;
DROP POLICY IF EXISTS "conversation_shares: creator select" ON public.conversation_shares;
DROP POLICY IF EXISTS "conversations: astrologer all"       ON public.conversations;
DROP POLICY IF EXISTS "documents: astrologer all"           ON public.documents;
DROP POLICY IF EXISTS "documents: client read own"          ON public.documents;
DROP POLICY IF EXISTS "message_feedback: astrologer all"    ON public.message_feedback;
DROP POLICY IF EXISTS "messages: astrologer all"            ON public.messages;
DROP POLICY IF EXISTS "pyramid_layers: astrologer all"      ON public.pyramid_layers;
DROP POLICY IF EXISTS "pyramid_layers: client read own"     ON public.pyramid_layers;
DROP POLICY IF EXISTS "reports: astrologer all"             ON public.reports;
DROP POLICY IF EXISTS "reports: client read own"            ON public.reports;

-- storage.objects policies that join on profiles.id / charts.client_id also block.
-- The "chat-attachments: owner *" policies use auth.uid() directly without a join
-- to a changing column; they're dead under Firebase Auth too but don't block DDL.
DROP POLICY IF EXISTS "storage: astrologer all"             ON storage.objects;
DROP POLICY IF EXISTS "storage: client read own"            ON storage.objects;

-- ─── Step 1: Drop all FK constraints that depend on profiles.id ───────────────

-- profiles.id used to reference auth.users(id) (Supabase Auth bootstrap).
-- Firebase Auth users don't exist in auth.users; this FK is dead and must
-- be dropped without recreation.
ALTER TABLE public.profiles           DROP CONSTRAINT IF EXISTS profiles_id_fkey;
ALTER TABLE public.charts             DROP CONSTRAINT IF EXISTS charts_client_id_fkey;
ALTER TABLE public.conversations      DROP CONSTRAINT IF EXISTS conversations_user_id_fkey;
ALTER TABLE public.message_feedback   DROP CONSTRAINT IF EXISTS message_feedback_user_id_fkey;
ALTER TABLE public.chat_attachments   DROP CONSTRAINT IF EXISTS chat_attachments_user_id_fkey;
ALTER TABLE public.conversation_shares DROP CONSTRAINT IF EXISTS conversation_shares_created_by_fkey;

-- Drop the trigger that auto-creates profiles from Supabase auth signups
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- ─── Step 2: Alter profiles.id uuid → text ───────────────────────────────────

ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_pkey;
ALTER TABLE public.profiles ALTER COLUMN id TYPE text USING id::text;
ALTER TABLE public.profiles ADD CONSTRAINT profiles_pkey PRIMARY KEY (id);

-- ─── Step 3: Alter all referencing columns uuid → text ───────────────────────

ALTER TABLE public.charts ALTER COLUMN client_id TYPE text USING client_id::text;
ALTER TABLE public.charts ADD CONSTRAINT charts_client_id_fkey
  FOREIGN KEY (client_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

ALTER TABLE public.conversations ALTER COLUMN user_id TYPE text USING user_id::text;
ALTER TABLE public.conversations ADD CONSTRAINT conversations_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

ALTER TABLE public.message_feedback ALTER COLUMN user_id TYPE text USING user_id::text;
ALTER TABLE public.message_feedback ADD CONSTRAINT message_feedback_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
-- Recreate the unique constraint (composite unique may include uuid column)
ALTER TABLE public.message_feedback DROP CONSTRAINT IF EXISTS message_feedback_message_id_user_id_key;
ALTER TABLE public.message_feedback ADD CONSTRAINT message_feedback_message_id_user_id_key
  UNIQUE (message_id, user_id);

ALTER TABLE public.chat_attachments ALTER COLUMN user_id TYPE text USING user_id::text;
ALTER TABLE public.chat_attachments ADD CONSTRAINT chat_attachments_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

ALTER TABLE public.conversation_shares ALTER COLUMN created_by TYPE text USING created_by::text;
ALTER TABLE public.conversation_shares ADD CONSTRAINT conversation_shares_created_by_fkey
  FOREIGN KEY (created_by) REFERENCES public.profiles(id) ON DELETE CASCADE;

-- ─── Step 4: Seed astrologer profile ─────────────────────────────────────────

INSERT INTO public.profiles (id, role, name, created_at)
VALUES (
  'xl2wYZRPwsVgPSAgtn9XJ80Xkub2',
  'astrologer',
  'Abhisek Mohanty',
  now()
)
ON CONFLICT (id) DO UPDATE SET role = 'astrologer', name = 'Abhisek Mohanty';

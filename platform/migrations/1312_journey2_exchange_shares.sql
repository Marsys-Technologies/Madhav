-- Migration 1312: persist the exchange selected for a Journey Two share.
-- Created: 2026-10-07
-- Transaction owned by migrate.ts. Existing links retain conversation scope.
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
ALTER TABLE public.conversation_shares
  ADD COLUMN IF NOT EXISTS message_id UUID REFERENCES public.conversation_messages(id) ON DELETE CASCADE;
-- The partial index idx_conversation_shares_message (message_id WHERE NOT NULL)
-- was dropped from this migration before it ever applied (owner decision,
-- 2026-10-07, SS N-212): CREATE INDEX needs CREATE on schema public, which the
-- routine migrator (amjis_app) deliberately lacks, so the whole release train
-- stopped here. The index is performance-only on a small table; add it later
-- through the protected public-schema route.

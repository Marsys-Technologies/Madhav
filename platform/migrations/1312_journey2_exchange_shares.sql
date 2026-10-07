-- Migration 1312: persist the exchange selected for a Journey Two share.
-- Created: 2026-10-07
-- Transaction owned by migrate.ts. Existing links retain conversation scope.
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
ALTER TABLE public.conversation_shares
  ADD COLUMN IF NOT EXISTS message_id UUID REFERENCES public.conversation_messages(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_conversation_shares_message
  ON public.conversation_shares(message_id) WHERE message_id IS NOT NULL;

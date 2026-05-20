-- ─── X-S8: Selective share — hide_reasoning and hide_methodology columns ───────
-- Gated by MARSYS_FLAG_R10_SELECTIVE_SHARE (server-side, default true).
-- DEFAULT FALSE means "do not hide" → existing shares show everything unchanged.

ALTER TABLE public.conversation_shares
  ADD COLUMN IF NOT EXISTS hide_reasoning  BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS hide_methodology BOOLEAN NOT NULL DEFAULT FALSE;

-- Rollback: DROP COLUMN IF EXISTS hide_reasoning, hide_methodology

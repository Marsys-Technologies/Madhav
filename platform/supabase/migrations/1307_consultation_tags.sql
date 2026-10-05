-- Migration 1307: consultation tags
-- Created: 2026-10-05
-- Reserved after origin/main and all 131 open PR migration claims were checked.
-- User-owned bookmarks only; independent of message metadata overwritten by writers.
-- Apply separately during an authorized release. No backfill or engine changes.
BEGIN;
SET LOCAL lock_timeout = '5s';
ALTER TABLE conversations
  ADD COLUMN IF NOT EXISTS consultation_tagged boolean NOT NULL DEFAULT false;
ALTER TABLE conversation_messages
  ADD COLUMN IF NOT EXISTS consultation_tagged boolean NOT NULL DEFAULT false;
COMMENT ON COLUMN conversations.consultation_tagged IS
  'Owner-selected Consultation conversation tag; distinct from navigation pins.';
COMMENT ON COLUMN conversation_messages.consultation_tagged IS
  'Owner-selected Consultation answer tag; unchanged by canonical message writes.';
COMMIT;

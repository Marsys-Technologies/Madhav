-- β2: conversation_messages table for Chat V2 persistence.
-- The existing `conversations` table is extended; the existing `messages`
-- table remains the legacy store for ConsumeChatLegacy (untouched).

-- ── Extend existing conversations table ────────────────────────────────────

ALTER TABLE conversations
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

-- Keep updated_at in sync with conversation_messages writes.
CREATE OR REPLACE FUNCTION conversations_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  UPDATE conversations SET updated_at = NOW() WHERE id = NEW.conversation_id;
  RETURN NEW;
END;
$$;

-- ── New conversation_messages table ────────────────────────────────────────
-- Stores UIMessage parts as JSONB. Separate from the legacy `messages` table.

CREATE TABLE IF NOT EXISTS conversation_messages (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  parent_message_id UUID NULL REFERENCES conversation_messages(id) ON DELETE SET NULL,
  role             TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
  parts_json       JSONB NOT NULL DEFAULT '[]',
  metadata_json    JSONB NOT NULL DEFAULT '{}',
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS conversation_messages_conv_time
  ON conversation_messages (conversation_id, created_at);

CREATE INDEX IF NOT EXISTS conversation_messages_parent
  ON conversation_messages (parent_message_id)
  WHERE parent_message_id IS NOT NULL;

DROP TRIGGER IF EXISTS trg_conversation_messages_updated_at ON conversation_messages;
CREATE TRIGGER trg_conversation_messages_updated_at
  AFTER INSERT ON conversation_messages
  FOR EACH ROW EXECUTE FUNCTION conversations_set_updated_at();

-- RLS: users may only access their own conversations' messages.
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY conversation_messages_owner ON conversation_messages
  USING (
    EXISTS (
      SELECT 1 FROM conversations c
      WHERE c.id = conversation_messages.conversation_id
        AND c.user_id = auth.uid()::text
    )
  );

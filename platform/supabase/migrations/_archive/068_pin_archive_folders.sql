-- R8-S4: Pin, archive, and folder organisation for conversations.
-- Adds: conversations.pinned column, conversation_folders table,
-- conversation_folder_members table.
-- The conversations table already has archived_at (061_conversations_v2.sql).

-- 1. Pinned flag on conversations
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS pinned BOOLEAN NOT NULL DEFAULT false;

-- Index for efficient "pinned first" ordering in sidebar
CREATE INDEX IF NOT EXISTS idx_conversations_pinned
  ON conversations (user_id, pinned DESC, updated_at DESC);

-- 2. conversation_folders — named colour-coded folder per user
CREATE TABLE IF NOT EXISTS conversation_folders (
  id         UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id    TEXT        NOT NULL,
  name       TEXT        NOT NULL CHECK (char_length(name) BETWEEN 1 AND 80),
  color      TEXT        NOT NULL DEFAULT '#6366f1',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conversation_folders_user
  ON conversation_folders (user_id, created_at DESC);

-- 3. conversation_folder_members — many-to-many (conversations ↔ folders, one folder per conversation)
CREATE TABLE IF NOT EXISTS conversation_folder_members (
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  folder_id       UUID NOT NULL REFERENCES conversation_folders(id) ON DELETE CASCADE,
  added_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (conversation_id)   -- one folder per conversation
);

CREATE INDEX IF NOT EXISTS idx_folder_members_folder
  ON conversation_folder_members (folder_id, added_at DESC);

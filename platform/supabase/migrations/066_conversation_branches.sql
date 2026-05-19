-- R8-S1: conversation_branches table
-- Persists branching state (message editing history) so reloads don't
-- destroy branch navigation.  The in-memory useBranches hook hydrates from
-- this table on mount and fires a fire-and-forget POST on every branch create.

CREATE TABLE IF NOT EXISTS conversation_branches (
  id               UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  conversation_id  UUID        NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  edited_message_id TEXT       NOT NULL,
  parent_branch_id UUID        REFERENCES conversation_branches(id) ON DELETE SET NULL,
  snapshot_jsonb   JSONB       NOT NULL DEFAULT '{}',
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conversation_branches_conversation_id
  ON conversation_branches (conversation_id, created_at DESC);

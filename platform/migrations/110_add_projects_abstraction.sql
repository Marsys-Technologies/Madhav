-- R9-S1: Projects abstraction — organisational layer above conversations.
-- A Project groups related conversations, optionally pins a chart context,
-- and injects a system_prompt_addition prepended to synthesis prompts at
-- query time. Gated behind MARSYS_FLAG_R9_PROJECTS (default false).
--
-- Rollback / down-migration notes:
--   DROP TABLE project_conversations;
--   DROP TABLE project_files;
--   DROP TABLE projects;
-- (cascade order; constraints ensure project_files + project_conversations
--  must be dropped before projects due to FK references)

CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  system_prompt_addition TEXT,
  chart_id TEXT,
  deleted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE project_files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  storage_path TEXT NOT NULL,
  filename TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE project_conversations (
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  PRIMARY KEY (project_id, conversation_id)
);

CREATE INDEX idx_project_conv_project ON project_conversations(project_id);
CREATE INDEX idx_project_conv_conv    ON project_conversations(conversation_id);

-- MARSYS-JIS Baseline Migration — Clean Slate
-- Synthesized from migrations 001–163 (teardown branch).
-- Creates ONLY the KEEP tables: identity/auth, chat, app, LEL, ops/governance.
-- DROP tables (ephemeris, panchanga, chart_facts, rag_*, classical_*, l25_*, etc.)
-- are excluded entirely.
--
-- Prerequisites: Postgres 15+, pgvector extension available, auth schema present
-- (Supabase-style). Run as superuser or migration role with CREATE privilege.
--
-- Dependency order:
--   extensions → profiles → charts → chart_grants
--   → conversations → conversation_messages → conversation_branches
--   → conversation_shares → conversation_folders / folder_members
--   → projects → project_files → project_conversations
--   → personas → pending_streams
--   → life_events / life_events_staging
--   → audit_log → audit_events → query_trace_steps → llm_call_log
--   → tool_execution_log → query_plan_log → llm_usage_events / pricing / cost tables
--   → performance_queries → eval_runs → performance_judge_verdict
--   → context_assembly_item_log → synthesis_quality_scorecard → plan_alternatives_log
--   → mcp_api_keys → mcp_predictions → mcp_prediction_outcomes → mcp_disagreements
--   → mcp_bundle_cache → mcp_alerts_config → mcp_audit_findings → audit_job_runs
--   → tool_registry → capability_tool_registry → capability_asset_tool_bindings
--   → runtime_config → llm_stack_config
--   → predictions

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- §0  Extensions
-- ─────────────────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────────────────────────────────────────────
-- §1  Shared utility function: set_updated_at
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- ─────────────────────────────────────────────────────────────────────────────
-- §2  profiles
--     Sources: 001, 006 (uuid→text), 007 (username/email/status/approved_by),
--              082 (role 'client'→'guest')
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE public.profiles (
  id          TEXT        PRIMARY KEY,                -- Firebase UID (text since mig 006)
  role        TEXT        NOT NULL DEFAULT 'guest'
                          CHECK (role IN ('guest', 'super_admin')),
  name        TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  -- added mig 007
  username    TEXT,
  email       TEXT,
  status      TEXT        NOT NULL DEFAULT 'active'
                          CHECK (status IN ('pending', 'active', 'disabled')),
  approved_at TIMESTAMPTZ,
  approved_by TEXT        REFERENCES public.profiles(id)
);

-- username + email unique (partial — null allowed for legacy rows)
CREATE UNIQUE INDEX IF NOT EXISTS profiles_username_unique
  ON public.profiles (lower(username))
  WHERE username IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS profiles_email_unique
  ON public.profiles (lower(email))
  WHERE email IS NOT NULL;

-- RLS enabled; service-role key bypasses; no auth.uid() policies (Firebase Auth)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Seed the super-admin (Abhisek Mohanty) — idempotent
INSERT INTO public.profiles (id, role, name, username, email, created_at)
VALUES (
  'xl2wYZRPwsVgPSAgtn9XJ80Xkub2',
  'super_admin',
  'Abhisek Mohanty',
  'abhisek',
  'mail.abhisek.mohanty@gmail.com',
  NOW()
)
ON CONFLICT (id) DO UPDATE
  SET role     = 'super_admin',
      name     = 'Abhisek Mohanty',
      username = 'abhisek',
      email    = 'mail.abhisek.mohanty@gmail.com';

-- access_requests (gate-kept sign-up queue; part of mig 007)
CREATE TABLE IF NOT EXISTS public.access_requests (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name        TEXT        NOT NULL,
  email            TEXT        NOT NULL,
  reason           TEXT,
  status           TEXT        NOT NULL DEFAULT 'pending'
                               CHECK (status IN ('pending', 'approved', 'rejected')),
  requested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reviewed_at      TIMESTAMPTZ,
  reviewed_by      TEXT        REFERENCES public.profiles(id),
  approved_user_id TEXT        REFERENCES public.profiles(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS access_requests_pending_email_unique
  ON public.access_requests (lower(email))
  WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS access_requests_status_requested_at_idx
  ON public.access_requests (status, requested_at DESC);

ALTER TABLE public.access_requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY "access_requests: service-only" ON public.access_requests
  FOR ALL USING (false) WITH CHECK (false);

-- ─────────────────────────────────────────────────────────────────────────────
-- §3  charts
--     Sources: 001, 006 (client_id uuid→text), 008 (native_id),
--              081 (owner_id, subject_name), 083 (RLS),
--              086_0 (chart_id UUID alias, role, created_at_iso),
--              161/162 (preferred_name, timezone_id)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE public.charts (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  -- legacy FK retained (Firebase UID text since mig 006)
  client_id     TEXT        REFERENCES public.profiles(id) ON DELETE CASCADE,
  name          TEXT        NOT NULL,
  birth_date    DATE        NOT NULL,
  birth_time    TIME        NOT NULL,
  birth_place   TEXT        NOT NULL,
  birth_lat     NUMERIC,
  birth_lng     NUMERIC,
  ayanamsa      TEXT        DEFAULT 'lahiri',
  house_system  TEXT        DEFAULT 'sripathi',
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  -- added mig 008
  native_id     VARCHAR(64) NOT NULL DEFAULT 'abhisek',
  -- added mig 081
  owner_id      TEXT,
  subject_name  TEXT,
  -- added mig 086_0 (modernization-arc columns)
  chart_id      UUID        UNIQUE,           -- mirrors id; FK target for L2.5 tables
  role          TEXT        NOT NULL DEFAULT 'native'
                            CHECK (role IN ('native', 'tertiary', 'fixture')),
  created_at_iso TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- added mig 161/162
  preferred_name TEXT,
  timezone_id    TEXT
);

COMMENT ON COLUMN public.charts.preferred_name IS
  'Display name for the native; defaults to first word of name.';
COMMENT ON COLUMN public.charts.timezone_id IS
  'IANA timezone identifier e.g. Asia/Kolkata. Sourced from explicit TZ select.';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_charts_client_id  ON public.charts(client_id);
CREATE INDEX IF NOT EXISTS idx_charts_owner_id   ON public.charts(owner_id);
CREATE INDEX IF NOT EXISTS idx_charts_role       ON public.charts(role);
CREATE UNIQUE INDEX IF NOT EXISTS uq_charts_chart_id ON public.charts(chart_id);

-- Backfill chart_id = id for any row present at baseline time
-- (safe no-op on empty DB)
UPDATE public.charts SET chart_id = id WHERE chart_id IS NULL;

-- RLS (mig 083)
ALTER TABLE public.charts ENABLE ROW LEVEL SECURITY;

CREATE POLICY chart_service_policy ON public.charts
  AS PERMISSIVE FOR ALL
  USING (
    current_setting('app.principal_id', true) IS NULL
    OR current_setting('app.principal_id', true) = ''
  );

CREATE POLICY chart_owner_policy ON public.charts
  AS PERMISSIVE FOR ALL
  USING (owner_id = current_setting('app.principal_id', true));

-- ─────────────────────────────────────────────────────────────────────────────
-- §4  chart_grants  (mig 081, 083)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE public.chart_grants (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id     UUID        NOT NULL REFERENCES public.charts(id) ON DELETE CASCADE,
  principal_id TEXT        NOT NULL,
  permission   TEXT        NOT NULL DEFAULT 'view'
                           CHECK (permission IN ('view')),
  granted_by   TEXT        NOT NULL,
  granted_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (chart_id, principal_id)
);

CREATE INDEX IF NOT EXISTS idx_chart_grants_chart_id     ON public.chart_grants(chart_id);
CREATE INDEX IF NOT EXISTS idx_chart_grants_principal_id ON public.chart_grants(principal_id);

-- RLS grant policy on charts (needs chart_grants to exist first)
CREATE POLICY chart_grant_policy ON public.charts
  AS PERMISSIVE FOR SELECT
  USING (
    EXISTS (
      SELECT 1
        FROM public.chart_grants g
       WHERE g.chart_id     = public.charts.id
         AND g.principal_id = current_setting('app.principal_id', true)
    )
  );

-- ─────────────────────────────────────────────────────────────────────────────
-- §5  conversations
--     Sources: 001, 006 (user_id uuid→text), 008 (native_id),
--              061 (updated_at, archived_at),
--              068 (pinned),
--              155 (active_ayanamshas)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE public.conversations (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id            UUID        NOT NULL REFERENCES public.charts(id) ON DELETE CASCADE,
  user_id             TEXT        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  module              TEXT        NOT NULL CHECK (module IN ('build', 'consume')),
  title               TEXT,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  -- added mig 008
  native_id           VARCHAR(64) NOT NULL DEFAULT 'abhisek',
  -- added mig 061
  updated_at          TIMESTAMPTZ,
  archived_at         TIMESTAMPTZ,
  -- added mig 068
  pinned              BOOLEAN     NOT NULL DEFAULT FALSE,
  -- added mig 155
  active_ayanamshas   JSONB       DEFAULT '["lahiri","true_chitra","kp","raman","surya_siddhanta"]'::JSONB
);

CREATE INDEX IF NOT EXISTS idx_conversations_chart_id    ON public.conversations(chart_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id     ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_pinned
  ON public.conversations(user_id, pinned DESC, updated_at DESC);
CREATE INDEX IF NOT EXISTS conversations_active_ayanamshas_gin
  ON public.conversations USING GIN (active_ayanamshas);
CREATE INDEX IF NOT EXISTS idx_conversations_title_trgm
  ON public.conversations USING GIN (title gin_trgm_ops)
  WHERE title IS NOT NULL;

-- conversations_set_updated_at function + trigger (mig 061)
CREATE OR REPLACE FUNCTION public.conversations_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  UPDATE public.conversations SET updated_at = NOW() WHERE id = NEW.conversation_id;
  RETURN NEW;
END;
$$;

-- ─────────────────────────────────────────────────────────────────────────────
-- §6  conversation_messages  (mig 061 + 112 embeddings)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE public.conversation_messages (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id   UUID        NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  parent_message_id UUID        REFERENCES public.conversation_messages(id) ON DELETE SET NULL,
  role              TEXT        NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
  parts_json        JSONB       NOT NULL DEFAULT '[]',
  metadata_json     JSONB       NOT NULL DEFAULT '{}',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS conversation_messages_conv_time
  ON public.conversation_messages(conversation_id, created_at);

CREATE INDEX IF NOT EXISTS conversation_messages_parent
  ON public.conversation_messages(parent_message_id)
  WHERE parent_message_id IS NOT NULL;

-- GIN trigram index on parts_json body text (mig 067)
CREATE INDEX IF NOT EXISTS idx_conv_messages_body_trgm
  ON public.conversation_messages USING GIN ((parts_json::TEXT) gin_trgm_ops);

-- Trigger: keep conversations.updated_at in sync
DROP TRIGGER IF EXISTS trg_conversation_messages_updated_at ON public.conversation_messages;
CREATE TRIGGER trg_conversation_messages_updated_at
  AFTER INSERT ON public.conversation_messages
  FOR EACH ROW EXECUTE FUNCTION public.conversations_set_updated_at();

-- RLS
ALTER TABLE public.conversation_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY conversation_messages_owner ON public.conversation_messages
  USING (
    EXISTS (
      SELECT 1 FROM public.conversations c
      WHERE c.id = public.conversation_messages.conversation_id
        AND c.user_id = auth.uid()::TEXT
    )
  );

-- conversation_message_embeddings (mig 112 — R9-S2 semantic search)
CREATE TABLE IF NOT EXISTS public.conversation_message_embeddings (
  message_id UUID        PRIMARY KEY REFERENCES public.conversation_messages(id) ON DELETE CASCADE,
  embedding  VECTOR(768),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cme_embedding
  ON public.conversation_message_embeddings
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ─────────────────────────────────────────────────────────────────────────────
-- §7  conversation_shares  (mig 004, 006, 113)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE public.conversation_shares (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID        NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  slug            TEXT        NOT NULL UNIQUE,
  created_by      TEXT        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  expires_at      TIMESTAMPTZ,
  revoked_at      TIMESTAMPTZ,
  -- added mig 113
  hide_reasoning   BOOLEAN    NOT NULL DEFAULT FALSE,
  hide_methodology BOOLEAN    NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_conversation_shares_conversation_id
  ON public.conversation_shares(conversation_id);

ALTER TABLE public.conversation_shares ENABLE ROW LEVEL SECURITY;

-- ─────────────────────────────────────────────────────────────────────────────
-- §8  conversation_branches  (mig 066 supabase)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.conversation_branches (
  id                UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  conversation_id   UUID        NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  edited_message_id TEXT        NOT NULL,
  parent_branch_id  UUID        REFERENCES public.conversation_branches(id) ON DELETE SET NULL,
  snapshot_jsonb    JSONB       NOT NULL DEFAULT '{}',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversation_branches_conversation_id
  ON public.conversation_branches(conversation_id, created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- §9  conversation_folders + folder_members  (mig 068 supabase)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.conversation_folders (
  id         UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id    TEXT        NOT NULL,
  name       TEXT        NOT NULL CHECK (char_length(name) BETWEEN 1 AND 80),
  color      TEXT        NOT NULL DEFAULT '#6366f1',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversation_folders_user
  ON public.conversation_folders(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS public.conversation_folder_members (
  conversation_id UUID        NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  folder_id       UUID        NOT NULL REFERENCES public.conversation_folders(id) ON DELETE CASCADE,
  added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (conversation_id)   -- one folder per conversation
);

CREATE INDEX IF NOT EXISTS idx_folder_members_folder
  ON public.conversation_folder_members(folder_id, added_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- §10  pending_streams  (mig 063 supabase)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.pending_streams (
  query_id         TEXT        PRIMARY KEY,
  user_id          TEXT        NOT NULL DEFAULT '',
  conversation_id  TEXT,
  accumulated_text TEXT        NOT NULL DEFAULT '',
  last_event_seq   BIGINT      NOT NULL DEFAULT 0,
  expires_at       TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pending_streams_expires_at
  ON public.pending_streams(expires_at);

-- ─────────────────────────────────────────────────────────────────────────────
-- §11  projects + project_files + project_conversations  (mig 110)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE public.projects (
  id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               TEXT        NOT NULL,
  name                  TEXT        NOT NULL,
  system_prompt_addition TEXT,
  chart_id              TEXT,
  deleted_at            TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.project_files (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id   UUID        NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  storage_path TEXT        NOT NULL,
  filename     TEXT        NOT NULL,
  mime_type    TEXT        NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.project_conversations (
  project_id      UUID        NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  conversation_id UUID        NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  PRIMARY KEY (project_id, conversation_id)
);

CREATE INDEX idx_project_conv_project ON public.project_conversations(project_id);
CREATE INDEX idx_project_conv_conv    ON public.project_conversations(conversation_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- §12  personas  (mig 111)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE public.personas (
  id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        TEXT        NOT NULL,
  name           TEXT        NOT NULL CHECK (char_length(name) <= 50),
  system_prompt  TEXT        NOT NULL CHECK (char_length(system_prompt) <= 4000),
  default_style  TEXT,
  default_stack  TEXT,
  is_default     BOOLEAN     NOT NULL DEFAULT FALSE,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_personas_user_id ON public.personas(user_id);

-- At most one default persona per user
CREATE UNIQUE INDEX idx_personas_user_default
  ON public.personas(user_id)
  WHERE is_default = TRUE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §13  life_events + life_events_staging  (mig 017 — LEL ground truth)
--      NOTE: build_manifests FK removed — LEL tables are KEEP but build_manifests
--            is a DROP table. The FK is omitted in the baseline; life_events rows
--            carry build_id as a plain text reference only.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.life_events (
  id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id       TEXT        UNIQUE NOT NULL,
  event_date     DATE        NOT NULL,
  category       TEXT        NOT NULL,
  description    TEXT        NOT NULL,
  significance   TEXT,
  chart_state    JSONB       NOT NULL,
  source_section TEXT        NOT NULL,
  build_id       TEXT        NOT NULL,   -- soft ref; build_manifests is a DROP table
  provenance     JSONB       NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_life_events_date     ON public.life_events(event_date);
CREATE INDEX IF NOT EXISTS idx_life_events_category ON public.life_events(category, event_date);

CREATE TABLE IF NOT EXISTS public.life_events_staging (LIKE public.life_events INCLUDING ALL);

-- ─────────────────────────────────────────────────────────────────────────────
-- §14  audit_log  (mig 011)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.audit_log (
  id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id                UUID        NOT NULL,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  query_text              TEXT        NOT NULL,
  query_class             TEXT        NOT NULL,
  bundle_keys             JSONB       NOT NULL DEFAULT '[]',
  tools_called            JSONB       NOT NULL DEFAULT '[]',
  validators_run          JSONB       NOT NULL DEFAULT '[]',
  synthesis_model         TEXT        NOT NULL,
  synthesis_input_tokens  INTEGER     NOT NULL DEFAULT 0,
  synthesis_output_tokens INTEGER     NOT NULL DEFAULT 0,
  disclosure_tier         TEXT        NOT NULL,
  final_output            TEXT        NOT NULL DEFAULT '',
  audit_event_version     INTEGER     NOT NULL DEFAULT 1,
  CONSTRAINT uq_audit_log_query_id UNIQUE (query_id)
);

CREATE INDEX IF NOT EXISTS idx_audit_log_query_id   ON public.audit_log(query_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON public.audit_log(created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- §15  audit_events  (mig 026, 045, 114)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.audit_events (
  id                     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id               UUID        NOT NULL,
  query_plan_id          UUID,
  query_text             TEXT,
  query_class            TEXT,
  user_id                TEXT,
  chart_id               UUID,
  conversation_id        UUID,
  tool_bundles           JSONB,
  latency_ms             INTEGER,
  audit_status           TEXT        NOT NULL DEFAULT 'ok',
  audit_warnings         JSONB,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- added mig 045
  disclosure_tier        TEXT,
  b10_compliant          BOOLEAN,
  b11_compliant          BOOLEAN,
  -- added mig 114
  truncated_by_user_edit BOOLEAN     DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_audit_events_query_id    ON public.audit_events(query_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at  ON public.audit_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_user_id     ON public.audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_query_class ON public.audit_events(query_class);

-- ─────────────────────────────────────────────────────────────────────────────
-- §16  query_trace_steps  (mig 020, 064, 116)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.query_trace_steps (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id        UUID        NOT NULL,
  conversation_id UUID,
  step_seq        SMALLINT    NOT NULL,
  step_name       TEXT        NOT NULL,
  step_type       TEXT        NOT NULL
                  CHECK (step_type IN ('deterministic', 'llm', 'sql', 'vector', 'gcs')),
  status          TEXT        NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'running', 'done', 'error')),
  started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at    TIMESTAMPTZ,
  latency_ms      INTEGER,
  parallel_group  TEXT,
  data_summary    JSONB       NOT NULL DEFAULT '{}',
  payload         JSONB       NOT NULL DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- added mig 064
  user_id         TEXT,
  -- added mig 116
  mcp_tool        TEXT
);

CREATE INDEX IF NOT EXISTS idx_query_trace_steps_query_id
  ON public.query_trace_steps(query_id, step_seq);

CREATE INDEX IF NOT EXISTS idx_query_trace_steps_created_at
  ON public.query_trace_steps(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_qts_user_id
  ON public.query_trace_steps(user_id)
  WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_query_trace_steps_mcp_tool
  ON public.query_trace_steps(mcp_tool)
  WHERE mcp_tool IS NOT NULL;

COMMENT ON TABLE public.query_trace_steps IS
  'Per-step execution trace for every pipeline invocation. Powers the real-time Query Trace Panel.';

-- ─────────────────────────────────────────────────────────────────────────────
-- §17  llm_call_log  (mig 032, 040)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.llm_call_log (
  id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id                UUID        NOT NULL,
  conversation_id         UUID,
  call_stage              TEXT        NOT NULL,
  model_id                TEXT        NOT NULL,
  provider                TEXT        NOT NULL,
  input_tokens            INTEGER,
  output_tokens           INTEGER,
  reasoning_tokens        INTEGER,
  latency_ms              INTEGER,
  cost_usd                NUMERIC(12, 8),
  fallback_used           BOOLEAN     DEFAULT FALSE,
  error_code              TEXT,
  payload                 JSONB,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- added mig 040
  decision_alternatives   JSONB,
  decision_reasoning      TEXT,
  prompt_template_id      TEXT,
  prompt_template_version TEXT,
  parent_call_id          UUID        REFERENCES public.llm_call_log(id)
);

CREATE INDEX IF NOT EXISTS idx_llm_call_log_query_id   ON public.llm_call_log(query_id);
CREATE INDEX IF NOT EXISTS idx_llm_call_log_model_id   ON public.llm_call_log(model_id);
CREATE INDEX IF NOT EXISTS idx_llm_call_log_call_stage ON public.llm_call_log(call_stage);
CREATE INDEX IF NOT EXISTS idx_llm_call_log_created_at ON public.llm_call_log(created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- §18  tool_execution_log  (mig 034, 040, 042, 073, 082)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.tool_execution_log (
  id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id             UUID,                               -- web-path key
  trace_id             TEXT,                               -- MCP-path key (073)
  tool_name            TEXT        NOT NULL,
  params_json          JSONB,
  status               TEXT        NOT NULL DEFAULT 'ok',
  rows_returned        INTEGER,
  latency_ms           INTEGER,
  token_estimate       INTEGER,
  data_asset_id        TEXT,
  error_code           TEXT,
  served_from_cache    BOOLEAN     DEFAULT FALSE,
  fallback_used        BOOLEAN     DEFAULT FALSE,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- added mig 040
  raw_result_count     INTEGER,
  kept_result_count    INTEGER,
  dropped_items        JSONB,
  kept_items           JSONB,
  tool_input_payload   JSONB,
  tool_output_summary  JSONB,
  error_class          TEXT        DEFAULT 'OK',
  -- added mig 042
  retrieval_score      REAL,
  -- added mig 073 (perf-system audit columns)
  audience_tier        TEXT        NOT NULL DEFAULT 'super_admin',
  response_text        TEXT,
  citation_count       INTEGER,
  has_numerical        BOOLEAN,
  is_forward_looking   BOOLEAN,
  sanskrit_compliant   BOOLEAN,
  audit_flagged        BOOLEAN     DEFAULT FALSE,
  -- added mig 082 (MCP-aware columns)
  source               TEXT,
  mcp_key_id           TEXT,
  mcp_tool_name        TEXT,
  bundle_trace_id      UUID,
  signal_ids_available TEXT[],
  bundle_size_tokens   INTEGER
);

CREATE INDEX IF NOT EXISTS idx_tool_execution_log_query_id   ON public.tool_execution_log(query_id)   WHERE query_id   IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tool_execution_log_tool_name  ON public.tool_execution_log(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_execution_log_status     ON public.tool_execution_log(status);
CREATE INDEX IF NOT EXISTS idx_tool_execution_log_zero_rows  ON public.tool_execution_log(tool_name)   WHERE status = 'zero_rows';
-- mig 073
CREATE INDEX IF NOT EXISTS tool_execution_log_trace_id
  ON public.tool_execution_log(trace_id)
  WHERE trace_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS tool_execution_log_audit_queue
  ON public.tool_execution_log(created_at, audit_flagged)
  WHERE audit_flagged IS DISTINCT FROM TRUE;
-- mig 082
CREATE INDEX IF NOT EXISTS tool_execution_log_mcp_tool_idx
  ON public.tool_execution_log(mcp_tool_name, created_at)
  WHERE mcp_tool_name IS NOT NULL;
CREATE INDEX IF NOT EXISTS tool_execution_log_source_idx
  ON public.tool_execution_log(source, created_at)
  WHERE source IS NOT NULL;

COMMENT ON COLUMN public.tool_execution_log.source IS
  '"web_consume" | "mcp_primitive" | "mcp_bundle" | "mcp_sub_tool"';
COMMENT ON COLUMN public.tool_execution_log.mcp_key_id IS
  'API key ID from mcp_api_keys; NULL for web-path calls.';
COMMENT ON COLUMN public.tool_execution_log.mcp_tool_name IS
  'MCP-facing tool name (e.g. holistic_bundle). NULL for web-path calls.';
COMMENT ON COLUMN public.tool_execution_log.audit_flagged IS
  'Set true by the nightly audit job if any audit check fails for this row.';

-- ─────────────────────────────────────────────────────────────────────────────
-- §19  query_plan_log  (mig 033)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.query_plan_log (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id            UUID        NOT NULL UNIQUE,
  conversation_id     UUID,
  chart_id            TEXT,
  planner_model_id    TEXT,
  query_text          TEXT,
  query_class         TEXT,
  tool_count          INTEGER,
  plan_json           JSONB,
  parsing_success     BOOLEAN     NOT NULL DEFAULT TRUE,
  parse_error         TEXT,
  fallback_used       BOOLEAN     DEFAULT FALSE,
  planner_latency_ms  INTEGER,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_query_plan_log_query_id        ON public.query_plan_log(query_id);
CREATE INDEX IF NOT EXISTS idx_query_plan_log_conversation_id ON public.query_plan_log(conversation_id);
CREATE INDEX IF NOT EXISTS idx_query_plan_log_created_at      ON public.query_plan_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_plan_log_fallback
  ON public.query_plan_log(fallback_used)
  WHERE fallback_used = TRUE;

-- ─────────────────────────────────────────────────────────────────────────────
-- §20  Observatory tables  (mig 038, 041)
-- ─────────────────────────────────────────────────────────────────────────────

-- llm_pricing_versions
CREATE TABLE IF NOT EXISTS public.llm_pricing_versions (
  pricing_version_id    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  provider              TEXT        NOT NULL,
  model                 TEXT        NOT NULL,
  token_class           TEXT        NOT NULL,
  price_per_million_usd NUMERIC(14, 8) NOT NULL,
  effective_from        TIMESTAMPTZ NOT NULL,
  effective_to          TIMESTAMPTZ,
  source_url            TEXT,
  recorded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT llm_pricing_versions_token_class_check
    CHECK (token_class IN ('input', 'output', 'cache_read', 'cache_write', 'reasoning'))
);

CREATE INDEX IF NOT EXISTS idx_llm_pricing_versions_lookup
  ON public.llm_pricing_versions(provider, model, effective_from DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_pricing_versions_natural_key
  ON public.llm_pricing_versions(provider, model, token_class, effective_from);

-- llm_usage_events
CREATE TABLE IF NOT EXISTS public.llm_usage_events (
  event_id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id     TEXT        NOT NULL,
  conversation_name   TEXT,
  prompt_id           TEXT        NOT NULL,
  parent_prompt_id    TEXT,
  user_id             TEXT        NOT NULL,
  provider            TEXT        NOT NULL,
  model               TEXT        NOT NULL,
  pipeline_stage      TEXT        NOT NULL,
  prompt_text         TEXT,
  response_text       TEXT,
  system_prompt       TEXT,
  parameters          JSONB,
  input_tokens        INTEGER,
  output_tokens       INTEGER,
  cache_read_tokens   INTEGER     DEFAULT 0,
  cache_write_tokens  INTEGER     DEFAULT 0,
  reasoning_tokens    INTEGER     DEFAULT 0,
  computed_cost_usd   NUMERIC(12, 6),
  pricing_version_id  UUID        REFERENCES public.llm_pricing_versions(pricing_version_id),
  latency_ms          INTEGER,
  status              TEXT        NOT NULL,
  error_code          TEXT,
  provider_request_id TEXT,
  started_at          TIMESTAMPTZ NOT NULL,
  finished_at         TIMESTAMPTZ,
  feature_flag_state  JSONB,
  client_ip_hash      TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT llm_usage_events_provider_check
    CHECK (provider IN ('anthropic', 'openai', 'gemini', 'deepseek', 'nim')),
  CONSTRAINT llm_usage_events_pipeline_stage_check
    CHECK (pipeline_stage IN (
      'classify', 'compose', 'retrieve', 'synthesize', 'audit', 'other',
      'planner', 'title', 'history_summary'   -- expanded mig 041
    )),
  CONSTRAINT llm_usage_events_status_check
    CHECK (status IN ('success', 'error', 'timeout')),
  CONSTRAINT uq_llm_usage_events_prompt_id UNIQUE (prompt_id),
  CONSTRAINT fk_llm_usage_events_parent_prompt
    FOREIGN KEY (parent_prompt_id) REFERENCES public.llm_usage_events(prompt_id)
);

CREATE INDEX IF NOT EXISTS idx_llm_usage_events_started_at      ON public.llm_usage_events(started_at);
CREATE INDEX IF NOT EXISTS idx_llm_usage_events_provider_model  ON public.llm_usage_events(provider, model);
CREATE INDEX IF NOT EXISTS idx_llm_usage_events_conversation_id ON public.llm_usage_events(conversation_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_events_user_id         ON public.llm_usage_events(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_events_pipeline_stage  ON public.llm_usage_events(pipeline_stage);

-- llm_provider_cost_reports
CREATE TABLE IF NOT EXISTS public.llm_provider_cost_reports (
  report_id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  provider                    TEXT        NOT NULL,
  model                       TEXT,
  time_bucket_start           TIMESTAMPTZ NOT NULL,
  time_bucket_end             TIMESTAMPTZ NOT NULL,
  workspace_id                TEXT,
  authoritative_cost_usd      NUMERIC(14, 6) NOT NULL,
  authoritative_input_tokens  BIGINT,
  authoritative_output_tokens BIGINT,
  raw_payload                 JSONB,
  pulled_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_provider_cost_reports_provider_bucket
  ON public.llm_provider_cost_reports(provider, time_bucket_start);

-- llm_cost_reconciliation
CREATE TABLE IF NOT EXISTS public.llm_cost_reconciliation (
  reconciliation_id       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  reconciliation_date     DATE        NOT NULL,
  provider                TEXT        NOT NULL,
  model                   TEXT,
  computed_total_usd      NUMERIC(14, 6) NOT NULL,
  authoritative_total_usd NUMERIC(14, 6),
  variance_usd            NUMERIC(14, 6),
  variance_pct            NUMERIC(8, 4),
  event_count             INTEGER     NOT NULL,
  status                  TEXT        NOT NULL,
  notes                   TEXT,
  reconciled_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT llm_cost_reconciliation_status_check
    CHECK (status IN ('matched', 'variance_within_tolerance', 'variance_alert', 'missing_authoritative'))
);

CREATE INDEX IF NOT EXISTS idx_llm_cost_reconciliation_date_provider
  ON public.llm_cost_reconciliation(reconciliation_date, provider);

CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_cost_reconciliation_natural_key
  ON public.llm_cost_reconciliation(reconciliation_date, provider, COALESCE(model, ''));

-- llm_budget_rules
CREATE TABLE IF NOT EXISTS public.llm_budget_rules (
  budget_rule_id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  name                TEXT        NOT NULL,
  scope               TEXT        NOT NULL,
  scope_value         TEXT,
  period              TEXT        NOT NULL,
  amount_usd          NUMERIC(12, 2) NOT NULL,
  alert_thresholds    JSONB       NOT NULL DEFAULT '[]'::JSONB,
  created_by_user_id  TEXT,
  active              BOOLEAN     NOT NULL DEFAULT TRUE,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT llm_budget_rules_scope_check
    CHECK (scope IN ('total', 'provider', 'model', 'pipeline_stage')),
  CONSTRAINT llm_budget_rules_period_check
    CHECK (period IN ('daily', 'weekly', 'monthly'))
);

-- llm_stack_config (mig 046)
CREATE TABLE IF NOT EXISTS public.llm_stack_config (
  scope        TEXT        PRIMARY KEY,
  active_stack TEXT        NOT NULL,
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by   TEXT        NOT NULL
);

-- ─────────────────────────────────────────────────────────────────────────────
-- §21  Performance + eval tables  (mig 043, 044)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.performance_queries (
  id                       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  audit_event_id           UUID        REFERENCES public.audit_log(id) ON DELETE SET NULL,
  eval_run_id              UUID,         -- FK to eval_runs added below after eval_runs exists
  source                   TEXT        NOT NULL CHECK (source IN ('consume', 'eval')),
  created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  query_text               TEXT,
  query_class              TEXT,
  plan_type                TEXT,
  plan_tools_selected      JSONB,
  planner_confidence       NUMERIC,
  latency_planner_ms       INTEGER,
  latency_retrieval_ms     INTEGER,
  latency_synthesis_ms     INTEGER,
  latency_total_ms         INTEGER,
  citations_present        BOOLEAN,
  citation_count           INTEGER     DEFAULT 0,
  synthesis_status         TEXT,
  validator_verdict        TEXT,
  disclosure_tier          TEXT,
  b10_violation            BOOLEAN,
  b11_violation            BOOLEAN,
  retrieval_hit            BOOLEAN,
  retrieval_score_top1     NUMERIC,
  plan_accuracy_label      TEXT        DEFAULT 'unjudged'
                           CHECK (plan_accuracy_label IN
                             ('correct', 'wrong', 'ambiguous', 'unjudged', 'n_a')),
  plan_accuracy_source     TEXT
                           CHECK (plan_accuracy_source IN ('golden', 'judge')
                                  OR plan_accuracy_source IS NULL),
  is_prediction            BOOLEAN     DEFAULT FALSE,
  prediction_outcome_state TEXT        DEFAULT 'n_a'
                           CHECK (prediction_outcome_state IN
                             ('pending', 'observed_correct', 'observed_incorrect', 'n_a'))
);

CREATE INDEX IF NOT EXISTS perf_queries_created_at_idx
  ON public.performance_queries(created_at DESC);
CREATE INDEX IF NOT EXISTS perf_queries_source_created_idx
  ON public.performance_queries(source, created_at DESC);
CREATE INDEX IF NOT EXISTS perf_queries_class_created_idx
  ON public.performance_queries(query_class, created_at DESC);
CREATE INDEX IF NOT EXISTS perf_queries_audit_event_idx
  ON public.performance_queries(audit_event_id);
CREATE INDEX IF NOT EXISTS perf_queries_eval_run_idx
  ON public.performance_queries(eval_run_id);

-- eval_runs
CREATE TABLE IF NOT EXISTS public.eval_runs (
  id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at             TIMESTAMPTZ,
  golden_set_version      TEXT        NOT NULL,
  planner_prompt_version  TEXT,
  synthesis_prompt_version TEXT,
  triggered_by            TEXT,
  query_count             INTEGER     DEFAULT 0,
  plan_accuracy_recall    NUMERIC,
  plan_accuracy_precision NUMERIC,
  citation_rate           NUMERIC,
  avg_latency_total_ms    INTEGER,
  synthesis_pass_rate     NUMERIC,
  retrieval_hit_rate      NUMERIC,
  b10_compliance_rate     NUMERIC,
  b11_compliance_rate     NUMERIC,
  notes                   TEXT
);

CREATE INDEX IF NOT EXISTS eval_runs_created_idx ON public.eval_runs(created_at DESC);

-- Finalize FK on performance_queries.eval_run_id
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'performance_queries_eval_run_fk'
  ) THEN
    ALTER TABLE public.performance_queries
      ADD CONSTRAINT performance_queries_eval_run_fk
      FOREIGN KEY (eval_run_id) REFERENCES public.eval_runs(id) ON DELETE SET NULL;
  END IF;
END $$;

-- performance_judge_verdict
CREATE TABLE IF NOT EXISTS public.performance_judge_verdict (
  id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  performance_query_id UUID        NOT NULL
                       REFERENCES public.performance_queries(id) ON DELETE CASCADE,
  judge_run_id         UUID        NOT NULL,
  judge_model          TEXT        NOT NULL,
  planner_verdict      TEXT        NOT NULL
                       CHECK (planner_verdict IN ('correct', 'wrong', 'ambiguous')),
  planner_reasoning    TEXT,
  triggered_by_user_id TEXT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS judge_verdict_pq_idx  ON public.performance_judge_verdict(performance_query_id);
CREATE INDEX IF NOT EXISTS judge_verdict_run_idx ON public.performance_judge_verdict(judge_run_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- §22  Query trace capture auxiliary tables  (mig 040)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.context_assembly_item_log (
  id                            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id                      UUID        NOT NULL,
  assembly_step_id              TEXT        NOT NULL,
  item_rank                     INTEGER     NOT NULL,
  source_bundle                 TEXT        NOT NULL,
  source_item_id                TEXT        NOT NULL,
  layer                         TEXT        NOT NULL,
  token_cost                    INTEGER     NOT NULL,
  relevance_score               REAL,
  status                        TEXT        NOT NULL CHECK (status IN ('INCLUDED', 'TRUNCATED', 'DROPPED')),
  drop_reason                   TEXT        CHECK (
    drop_reason IN ('BUDGET_EXCEEDED', 'DEDUP', 'RELEVANCE_FLOOR') OR drop_reason IS NULL
  ),
  truncated_to_tokens           INTEGER,
  cumulative_tokens_at_decision INTEGER,
  budget_at_decision            INTEGER,
  created_at                    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_context_assembly_item_log_query
  ON public.context_assembly_item_log(query_id, item_rank);

CREATE TABLE IF NOT EXISTS public.synthesis_quality_scorecard (
  query_id                     UUID        PRIMARY KEY,
  citation_density             REAL        NOT NULL DEFAULT 0,
  whole_chart_coverage         JSONB       NOT NULL DEFAULT '{}',
  derivation_ledger_compliance REAL        NOT NULL DEFAULT 0,
  fabricated_computation_flags JSONB,
  disclosure_tier_verdict      TEXT        NOT NULL DEFAULT 'UNKNOWN',
  composite_score              REAL        NOT NULL DEFAULT 0,
  failures                     JSONB,
  created_at                   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.plan_alternatives_log (
  id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id              UUID        NOT NULL,
  bundle_name           TEXT        NOT NULL,
  was_selected          BOOLEAN     NOT NULL,
  rationale             TEXT,
  expected_recall_score REAL,
  created_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_plan_alternatives_log_query
  ON public.plan_alternatives_log(query_id);

-- Baseline stats materialized view (mig 040)
CREATE MATERIALIZED VIEW IF NOT EXISTS public.query_baseline_stats AS
SELECT
  'unknown'::TEXT                                                                       AS query_type,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms)                             AS p50_total_latency_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)                             AS p95_total_latency_ms,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY cost_usd::DOUBLE PRECISION)             AS p50_total_cost_usd,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY cost_usd::DOUBLE PRECISION)             AS p95_total_cost_usd,
  COUNT(*)                                                                              AS sample_size
FROM public.llm_call_log
WHERE created_at > NOW() - INTERVAL '30 days'
  AND cost_usd IS NOT NULL
GROUP BY 1;

-- ─────────────────────────────────────────────────────────────────────────────
-- §23  MCP API keys  (mig 070, 090, 117 — audience_tier column removed per 090)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.mcp_api_keys (
  key_id       TEXT        PRIMARY KEY,
  key_hash     TEXT        NOT NULL,
  user_uid     TEXT        NOT NULL,
  -- audience_tier column removed per mig 090 (stream A 3.tier_excision)
  scopes       TEXT[]      NOT NULL DEFAULT '{}',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_used_at TIMESTAMPTZ,
  revoked_at   TIMESTAMPTZ,
  label        TEXT
);

CREATE INDEX IF NOT EXISTS mcp_api_keys_user_uid_idx
  ON public.mcp_api_keys(user_uid);

CREATE INDEX IF NOT EXISTS mcp_api_keys_auth_lookup_idx
  ON public.mcp_api_keys(key_id, revoked_at);

-- ─────────────────────────────────────────────────────────────────────────────
-- §24  mcp_predictions  (mig 071 supabase + 075 supabase + 119)
--      NOTE: The two schemas (071 text-keyed PPL vs 075 UUID-keyed PPL) are
--            different tables in production. We keep BOTH under their own names.
-- ─────────────────────────────────────────────────────────────────────────────

-- mcp_predictions (text-keyed PPL log from mig 071, extended by 119)
CREATE TABLE IF NOT EXISTS public.mcp_predictions (
  prediction_id            TEXT        PRIMARY KEY,
  logged_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  horizon                  TEXT,                   -- nullable per mig 119
  domain                   TEXT,                   -- nullable per mig 119
  prediction_text          TEXT,                   -- nullable per mig 119
  confidence               TEXT
                           CHECK (confidence IN ('high', 'medium', 'low') OR confidence IS NULL),
  falsifier                TEXT,                   -- nullable per mig 119
  key_id                   TEXT,                   -- nullable per mig 119
  trace_id                 TEXT,
  caller_context           TEXT,
  outcome_text             TEXT,
  verified                 BOOLEAN,
  outcome_notes            TEXT,
  outcome_recorded_at      TIMESTAMPTZ,
  outcome_key_id           TEXT,
  outcome_trace_id         TEXT,
  migrated_at              TIMESTAMPTZ,
  migrated_to              TEXT,
  -- added mig 119 (calibration stamp columns)
  chart_id                 TEXT,
  ayanamsha_id             TEXT,
  query_hash               TEXT,
  salience_formula_version TEXT,
  model_id                 TEXT,
  predicted_at_iso         TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS mcp_predictions_key_id_idx
  ON public.mcp_predictions(key_id, logged_at DESC)
  WHERE key_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS mcp_predictions_trace_id_idx
  ON public.mcp_predictions(trace_id)
  WHERE trace_id IS NOT NULL;

-- mig 119 calibration stamp indexes
CREATE UNIQUE INDEX IF NOT EXISTS mcp_predictions_stamp_uq
  ON public.mcp_predictions(chart_id, ayanamsha_id, query_hash, salience_formula_version)
  WHERE chart_id IS NOT NULL
    AND ayanamsha_id IS NOT NULL
    AND query_hash IS NOT NULL
    AND salience_formula_version IS NOT NULL;

CREATE INDEX IF NOT EXISTS mcp_predictions_chart_idx
  ON public.mcp_predictions(chart_id, predicted_at_iso DESC)
  WHERE chart_id IS NOT NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- §25  mcp_prediction_outcomes  (mig 075 supabase)
-- ─────────────────────────────────────────────────────────────────────────────

-- UUID-keyed predictions table from mig 075 (separate from the text-keyed one above)
-- In production both coexist; the UUID-keyed variant is the MCPT v3.1.0-S4 one.
CREATE TABLE IF NOT EXISTS public.mcp_prediction_outcomes (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  prediction_id    TEXT        NOT NULL,   -- soft ref to mcp_predictions.prediction_id
  outcome_text     TEXT        NOT NULL,
  outcome_occurred BOOLEAN     NOT NULL,
  outcome_date     DATE        NOT NULL,
  recorded_by      TEXT        NOT NULL DEFAULT 'operator',
  calibration_note TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS mcp_prediction_outcomes_prediction_id
  ON public.mcp_prediction_outcomes(prediction_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- §26  mcp_disagreements  (mig 071 supabase)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.mcp_disagreements (
  disagreement_id     TEXT        PRIMARY KEY,
  logged_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  class               TEXT        NOT NULL
                      CHECK (class IN (
                        'factual', 'interpretive', 'structural',
                        'mirror_desync', 'scope',
                        'output_conflict', 'version_disagreement',
                        'scope_disagreement', 'closure_disagreement',
                        'l3_zero_supports', 'panel_divergence',
                        'school_disagreement', 'acceptance_rate_anomaly'
                      )),
  description         TEXT        NOT NULL,
  source_session      TEXT        NOT NULL,
  proposed_resolution TEXT,
  status              TEXT        NOT NULL DEFAULT 'open'
                      CHECK (status IN ('open', 'resolved', 'escalated', 'reopened')),
  key_id              TEXT        NOT NULL,
  trace_id            TEXT,
  resolved_on         TIMESTAMPTZ,
  resolved_by_session TEXT,
  resolution_notes    TEXT
);

CREATE INDEX IF NOT EXISTS mcp_disagreements_status_idx
  ON public.mcp_disagreements(status, logged_at DESC);

CREATE INDEX IF NOT EXISTS mcp_disagreements_key_id_idx
  ON public.mcp_disagreements(key_id, logged_at DESC);

-- NOTE: mcp_bundle_cache + mcp_audit_findings removed — kill-list §3 DROP tables.
-- Operator: drop them via infra/teardown/01_drop_tables.sql

-- ─────────────────────────────────────────────────────────────────────────────
-- §27  mcp_alerts_config  (mig 077 supabase)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.mcp_alerts_config (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  metric_name     TEXT        NOT NULL,
  scope           TEXT        NOT NULL,
  tool_name       TEXT,
  threshold_value NUMERIC     NOT NULL,
  comparison      TEXT        NOT NULL CHECK (comparison IN ('gte', 'lte', 'gt', 'lt')),
  window_hours    INTEGER     NOT NULL DEFAULT 24,
  channels        TEXT[]      NOT NULL DEFAULT '{}',
  slack_webhook_url TEXT,
  email_recipients  TEXT[],
  enabled         BOOLEAN     NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by      TEXT        NOT NULL DEFAULT 'native',
  CONSTRAINT mcp_alerts_config_scope_tool CHECK (
    (scope = 'per_tool' AND tool_name IS NOT NULL) OR
    (scope = 'global'   AND tool_name IS NULL)
  )
);

CREATE INDEX IF NOT EXISTS mcp_alerts_config_enabled
  ON public.mcp_alerts_config(metric_name, scope, enabled)
  WHERE enabled = TRUE;

-- Seed default alert thresholds
INSERT INTO public.mcp_alerts_config
  (metric_name, scope, tool_name, threshold_value, comparison, window_hours, channels, enabled)
VALUES
  ('zero_rows_rate',        'global', NULL, 0.5, 'gte', 24, ARRAY['slack'],          TRUE),
  ('error_rate',            'global', NULL, 0.1, 'gte', 24, ARRAY['slack', 'email'], TRUE),
  ('audit_class1_count',    'global', NULL, 1,   'gte', 24, ARRAY['slack', 'email'], TRUE),
  ('audit_class2_count',    'global', NULL, 5,   'gte', 24, ARRAY['slack'],          TRUE),
  ('disabled_tool_call_count', 'global', NULL, 1, 'gte', 1, ARRAY['slack'],          TRUE)
ON CONFLICT DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- §30  tool_registry  (mig 077 supabase)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.tool_registry (
  tool_name       TEXT        PRIMARY KEY,
  tool_enabled    BOOLEAN     NOT NULL DEFAULT TRUE,
  disabled_reason TEXT,
  disabled_at     TIMESTAMPTZ,
  disabled_by     TEXT,
  enabled_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  enabled_by      TEXT        NOT NULL DEFAULT 'native',
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.tool_registry IS
  'Runtime operator toggle for MCP tool enable/disable. '
  'tool_enabled=false causes the primitive dispatcher to return 503 {tool_disabled: true}.';

-- Seed all MCP-facing tools (enabled by default)
INSERT INTO public.tool_registry (tool_name, tool_enabled) VALUES
  ('query_chart_facts',      TRUE),
  ('query_signals',          TRUE),
  ('query_dasha_periods',    TRUE),
  ('query_panchanga',        TRUE),
  ('query_ephemeris',        TRUE),
  ('query_transit_event',    TRUE),
  ('lel_query',              TRUE),
  ('vector_search',          TRUE),
  ('get_cgm_subgraph',       TRUE),
  ('cross_school_lookup',    TRUE),
  ('holistic_bundle',        TRUE),
  ('multi_school_bundle',    TRUE),
  ('read_asset',             TRUE),
  ('get_trace',              TRUE),
  ('list_recent_queries',    TRUE),
  ('tool_health',            TRUE),
  ('data_coverage',          TRUE),
  ('log_prediction',         TRUE),
  ('record_outcome',         TRUE),
  ('flag_disagreement',      TRUE)
ON CONFLICT (tool_name) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- §31  capability_tool_registry + bindings  (mig 070 supabase)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.capability_tool_registry (
  tool_name            TEXT        PRIMARY KEY,
  expose_to_planner    BOOLEAN     NOT NULL DEFAULT FALSE,
  description          TEXT        NOT NULL DEFAULT '',
  query_schema         JSONB,
  output_schema        JSONB,
  cost_weight          NUMERIC,
  linked_data_asset_ids TEXT[]     NOT NULL DEFAULT '{}',
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.capability_tool_registry IS
  'One row per wired RETRIEVAL_TOOLS[] entry. Seeded from CAPABILITY_MANIFEST.json.';

CREATE TABLE IF NOT EXISTS public.capability_asset_tool_bindings (
  asset_canonical_id TEXT        NOT NULL,
  tool_name          TEXT        NOT NULL
                     REFERENCES public.capability_tool_registry(tool_name) ON DELETE CASCADE,
  binding_source     TEXT        NOT NULL CHECK (binding_source IN ('manifest', 'override', 'inferred')),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (asset_canonical_id, tool_name)
);

CREATE INDEX IF NOT EXISTS idx_capability_asset_tool_bindings_asset
  ON public.capability_asset_tool_bindings(asset_canonical_id);

CREATE INDEX IF NOT EXISTS idx_capability_asset_tool_bindings_tool
  ON public.capability_asset_tool_bindings(tool_name);

-- updated_at trigger for capability_tool_registry
CREATE OR REPLACE FUNCTION public.update_capability_tool_registry_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_capability_tool_registry_updated_at ON public.capability_tool_registry;
CREATE TRIGGER trg_capability_tool_registry_updated_at
  BEFORE UPDATE ON public.capability_tool_registry
  FOR EACH ROW EXECUTE FUNCTION public.update_capability_tool_registry_updated_at();

-- ─────────────────────────────────────────────────────────────────────────────
-- §32  runtime_config  (mig 084)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.runtime_config (
  id         BIGSERIAL   PRIMARY KEY,
  key        TEXT        NOT NULL,
  value      JSONB       NOT NULL,
  value_type TEXT        NOT NULL CHECK (value_type IN ('boolean', 'number', 'string', 'json')),
  scope      TEXT        NOT NULL DEFAULT 'global' CHECK (scope IN ('global', 'per_chart')),
  chart_id   TEXT,
  updated_by TEXT        NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS runtime_config_key_chart_uq
  ON public.runtime_config(key, COALESCE(chart_id, '__global__'));

COMMENT ON TABLE public.runtime_config IS
  'DB-backed control plane for gate_registry overrides. Env/code defaults apply if no row.';

-- ─────────────────────────────────────────────────────────────────────────────
-- §33  predictions (Chat V2 γ3 PPL)  (mig 062 supabase)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.predictions (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id            UUID,
  conversation_id     UUID        REFERENCES public.conversations(id) ON DELETE SET NULL,
  prediction_text     TEXT        NOT NULL,
  confidence          NUMERIC(4, 3) CHECK (confidence >= 0 AND confidence <= 1),
  horizon             TEXT,
  falsifier           TEXT,
  logged_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  outcome             TEXT,
  outcome_observed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS predictions_query_id_idx        ON public.predictions(query_id);
CREATE INDEX IF NOT EXISTS predictions_conversation_id_idx ON public.predictions(conversation_id);
CREATE INDEX IF NOT EXISTS predictions_logged_at_idx       ON public.predictions(logged_at DESC);

ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;

-- RLS: owner-only reads via query_trace_steps.user_id
CREATE POLICY predictions_select ON public.predictions
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.query_trace_steps qts
      WHERE qts.query_id = public.predictions.query_id
        AND qts.user_id = auth.uid()::TEXT
    )
  );

CREATE POLICY predictions_insert ON public.predictions
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.query_trace_steps qts
      WHERE qts.query_id = public.predictions.query_id
        AND qts.user_id = auth.uid()::TEXT
    )
  );

COMMENT ON TABLE public.predictions IS
  'PPL: Prospective Prediction Log. Records time-indexed predictions from assistant output. '
  'outcome is intentionally nullable — never captured at logging time per Learning Layer rule #4.';

-- ─────────────────────────────────────────────────────────────────────────────
-- §34  Perf system materialized views  (mig 082 supabase)
--      These reference tool_execution_log and are safe here since that table
--      is created in §18.  Views referencing DROP tables (chart_facts, rag_chunks,
--      msr_signals, panchanga_daily, ephemeris_daily, build_manifests,
--      classical_texts) are intentionally OMITTED (mv_data_source_coverage,
--      mv_tool_grounding_24h depend on mcp_audit_findings which IS kept).
-- ─────────────────────────────────────────────────────────────────────────────

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_tool_metrics_24h AS
SELECT
  mcp_tool_name,
  COALESCE(source, 'unknown')                                               AS source,
  COALESCE(audience_tier, 'unknown')                                        AS audience_tier,
  count(*)                                                                  AS calls_24h,
  count(*) FILTER (WHERE status = 'ok')                                     AS ok_calls,
  count(*) FILTER (WHERE status = 'zero_rows')                              AS zero_rows_calls,
  count(*) FILTER (WHERE status = 'error')                                  AS error_calls,
  count(*) FILTER (WHERE status = 'ok')::FLOAT / NULLIF(count(*), 0)        AS ok_rate,
  count(*) FILTER (WHERE status = 'zero_rows')::FLOAT / NULLIF(count(*), 0) AS zero_rows_rate,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms)                  AS p50_latency_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)                  AS p95_latency_ms,
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms)                  AS p99_latency_ms,
  avg(rows_returned)                                                        AS avg_rows_returned,
  avg(bundle_size_tokens) FILTER (WHERE bundle_size_tokens IS NOT NULL)     AS avg_bundle_size_tokens,
  max(created_at)                                                           AS last_call_at
FROM public.tool_execution_log
WHERE created_at >= NOW() - INTERVAL '24 hours'
  AND mcp_tool_name IS NOT NULL
GROUP BY mcp_tool_name, COALESCE(source, 'unknown'), COALESCE(audience_tier, 'unknown');

CREATE UNIQUE INDEX IF NOT EXISTS mv_tool_metrics_24h_pk
  ON public.mv_tool_metrics_24h(mcp_tool_name, source, audience_tier);

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_session_summary AS
SELECT
  COALESCE(mcp_key_id, 'web')                                               AS mcp_key_id,
  COALESCE(audience_tier, 'unknown')                                        AS audience_tier,
  date_trunc('hour', created_at)                                            AS session_hour,
  count(DISTINCT mcp_tool_name) FILTER (WHERE source = 'mcp_primitive')    AS unique_primitives,
  count(*) FILTER (WHERE source = 'mcp_primitive')                          AS primitive_calls,
  count(*) FILTER (WHERE source = 'mcp_bundle')                             AS bundle_calls,
  count(*) FILTER (WHERE source = 'mcp_sub_tool')                           AS sub_tool_calls,
  sum(rows_returned)                                                        AS total_rows_returned,
  count(*) FILTER (WHERE status = 'zero_rows')                              AS zero_rows_calls,
  sum(bundle_size_tokens) FILTER (WHERE source = 'mcp_bundle')              AS total_bundle_tokens
FROM public.tool_execution_log
WHERE source LIKE 'mcp%'
GROUP BY COALESCE(mcp_key_id, 'web'), COALESCE(audience_tier, 'unknown'),
         date_trunc('hour', created_at);

CREATE UNIQUE INDEX IF NOT EXISTS mv_session_summary_pk
  ON public.mv_session_summary(mcp_key_id, session_hour);

-- mv_tool_grounding_24h removed: referenced mcp_audit_findings (reclassified DROP).

-- Initial population of MVs (empty DB; safe no-op)
REFRESH MATERIALIZED VIEW public.mv_tool_metrics_24h;
REFRESH MATERIALIZED VIEW public.mv_session_summary;

COMMIT;

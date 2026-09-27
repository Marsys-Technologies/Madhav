-- Migration 1120: AI Console BYOK routing persistence
-- Created: 2026-09-27
-- Provisional cross-cutting slot; 1070-1119 reserved for L3.
-- Additive only. Rollback requires export/retention review of immutable history.
-- Firebase ownership is checked by the server; these tables are service-only.
-- Transaction owned by platform/scripts/migrate.ts, including its tracking insert.
-- Do not add transaction control here: an inner COMMIT would break runner atomicity.

CREATE OR REPLACE FUNCTION ai_choice_shape(k text, conn uuid, model text, config uuid, cli text, allow_default boolean DEFAULT false)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT COALESCE(
    (k = 'provider_model' AND conn IS NOT NULL AND model IS NOT NULL AND btrim(model) <> '' AND config IS NULL AND cli IS NULL)
    OR (k = 'custom_configuration' AND config IS NOT NULL AND conn IS NULL AND model IS NULL AND cli IS NULL)
    OR (k = 'local_cli' AND cli IS NOT NULL AND conn IS NULL AND config IS NULL AND (model IS NULL OR btrim(model) <> ''))
    OR (allow_default AND k = 'default' AND conn IS NULL AND model IS NULL AND config IS NULL AND cli IS NULL), false)
$$;

CREATE TABLE IF NOT EXISTS ai_provider_connections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  provider_id text NOT NULL CHECK (provider_id IN ('openai', 'anthropic', 'google', 'xai', 'deepseek', 'kimi', 'openrouter')),
  name text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 120),
  credential_ciphertext bytea NOT NULL CHECK (octet_length(credential_ciphertext) > 0),
  credential_nonce bytea NOT NULL CHECK (octet_length(credential_nonce) = 12),
  credential_tag bytea NOT NULL CHECK (octet_length(credential_tag) = 16),
  wrapped_dek bytea NOT NULL CHECK (octet_length(wrapped_dek) > 0),
  wrap_nonce bytea NOT NULL CHECK (octet_length(wrap_nonce) = 12),
  wrap_tag bytea NOT NULL CHECK (octet_length(wrap_tag) = 16),
  kek_version text NOT NULL CHECK (btrim(kek_version) <> ''),
  masked_suffix text NOT NULL CHECK (length(masked_suffix) BETWEEN 1 AND 8),
  keyed_fingerprint text NOT NULL CHECK (btrim(keyed_fingerprint) <> ''),
  credential_version bigint NOT NULL DEFAULT 1 CHECK (credential_version > 0),
  credential_validity text NOT NULL DEFAULT 'unknown' CHECK (credential_validity IN ('unknown', 'valid', 'invalid')),
  validation_state text NOT NULL DEFAULT 'untested' CHECK (validation_state IN ('untested', 'validating', 'validated', 'needs_attention', 'invalid', 'unreachable')),
  last_validated_at timestamptz,
  last_checked_at timestamptz,
  last_error_code text CHECK (last_error_code IN ('AI_CONNECTION_INVALID','AI_MODEL_UNAVAILABLE','AI_ROLE_INCOMPATIBLE','AI_PROVIDER_UNREACHABLE','AI_PERMISSION_DENIED','AI_BILLING_UNAVAILABLE','AI_RATE_LIMITED','AI_EXECUTION_FAILED')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  UNIQUE (user_id, id),
  CHECK (credential_validity <> 'valid' OR last_validated_at IS NOT NULL),
  CHECK (validation_state <> 'validated' OR credential_validity = 'valid')
);
CREATE UNIQUE INDEX IF NOT EXISTS ai_connections_name_idx ON ai_provider_connections (user_id, lower(name)) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ai_connections_refresh_idx ON ai_provider_connections (validation_state, last_checked_at) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS ai_connection_models (
  connection_id uuid NOT NULL REFERENCES ai_provider_connections(id) ON DELETE CASCADE,
  model_id text NOT NULL CHECK (btrim(model_id) <> ''),
  display_name text NOT NULL,
  compatible_roles text[] NOT NULL CHECK (cardinality(compatible_roles) > 0 AND compatible_roles <@ ARRAY['synthesizer','planner','deep_planner','worker']::text[] AND array_position(compatible_roles, NULL) IS NULL),
  supports_tools boolean NOT NULL DEFAULT false,
  supports_structured_output boolean NOT NULL DEFAULT false,
  available boolean NOT NULL DEFAULT true,
  first_seen_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (connection_id, model_id)
);

CREATE TABLE IF NOT EXISTS ai_cli_installations (
  cli_id text PRIMARY KEY CHECK (cli_id IN ('codex', 'claude_code', 'gemini_antigravity', 'kimi_code')),
  detected_product text,
  detected_version text,
  validation_state text NOT NULL DEFAULT 'untested' CHECK (validation_state IN ('untested','validating','reachable','not_installed','auth_unavailable','unreachable','needs_attention')),
  last_checked_at timestamptz,
  last_error_code text CHECK (last_error_code IN ('AI_CLI_NOT_INSTALLED','AI_CLI_AUTH_UNAVAILABLE','AI_CLI_UNREACHABLE','AI_CLI_TIMEOUT','AI_CLI_OUTPUT_LIMIT','AI_EXECUTION_FAILED')),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ai_cli_models (
  cli_id text NOT NULL REFERENCES ai_cli_installations(cli_id) ON DELETE CASCADE,
  model_id text NOT NULL CHECK (btrim(model_id) <> ''),
  display_name text NOT NULL,
  is_builtin_default boolean NOT NULL DEFAULT false,
  available boolean NOT NULL DEFAULT true,
  compatible_roles text[] NOT NULL CHECK (cardinality(compatible_roles) > 0 AND compatible_roles <@ ARRAY['synthesizer','planner','deep_planner','worker']::text[] AND array_position(compatible_roles, NULL) IS NULL),
  supports_tools boolean NOT NULL DEFAULT false,
  supports_structured_output boolean NOT NULL DEFAULT false,
  first_seen_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (cli_id, model_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ai_cli_builtin_default_idx ON ai_cli_models(cli_id) WHERE is_builtin_default;
CREATE TABLE IF NOT EXISTS ai_cli_grants (
  user_id text NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  cli_id text NOT NULL REFERENCES ai_cli_installations(cli_id) ON DELETE RESTRICT,
  granted_by text NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  granted_at timestamptz NOT NULL DEFAULT now(),
  revoked_at timestamptz,
  PRIMARY KEY (user_id, cli_id),
  CHECK (revoked_at IS NULL OR revoked_at >= granted_at)
);
CREATE INDEX IF NOT EXISTS ai_grants_cli_idx ON ai_cli_grants(cli_id, user_id) WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS ai_custom_configurations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  name text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 120),
  version bigint NOT NULL DEFAULT 1 CHECK (version > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  UNIQUE (user_id, id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ai_configurations_name_idx ON ai_custom_configurations (user_id, lower(name)) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS ai_custom_configuration_roles (
  configuration_id uuid NOT NULL,
  user_id text NOT NULL,
  role text NOT NULL CHECK (role IN ('synthesizer', 'planner', 'deep_planner', 'worker')),
  kind text NOT NULL CHECK (kind IN ('provider_model','local_cli')),
  connection_id uuid,
  model_id text,
  cli_id text REFERENCES ai_cli_installations(cli_id) ON DELETE RESTRICT,
  PRIMARY KEY (configuration_id, role),
  FOREIGN KEY (user_id, configuration_id) REFERENCES ai_custom_configurations(user_id, id) ON DELETE CASCADE,
  FOREIGN KEY (user_id, connection_id) REFERENCES ai_provider_connections(user_id, id) ON DELETE RESTRICT,
  CHECK (ai_choice_shape(kind, connection_id, model_id, NULL, cli_id))
);
CREATE INDEX IF NOT EXISTS ai_roles_connection_idx ON ai_custom_configuration_roles(connection_id) WHERE connection_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS ai_user_defaults (
  user_id text PRIMARY KEY REFERENCES profiles(id) ON DELETE RESTRICT,
  kind text NOT NULL CHECK (kind IN ('provider_model','custom_configuration','local_cli')),
  connection_id uuid,
  model_id text,
  configuration_id uuid,
  cli_id text REFERENCES ai_cli_installations(cli_id) ON DELETE RESTRICT,
  updated_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (user_id, connection_id) REFERENCES ai_provider_connections(user_id, id) ON DELETE RESTRICT,
  FOREIGN KEY (user_id, configuration_id) REFERENCES ai_custom_configurations(user_id, id) ON DELETE RESTRICT,
  CHECK (ai_choice_shape(kind, connection_id, model_id, configuration_id, cli_id))
);
-- Zero rows until first explicit selection. Repository uses INSERT ... ON CONFLICT(user_id) DO UPDATE.
CREATE INDEX IF NOT EXISTS ai_defaults_connection_idx ON ai_user_defaults(connection_id) WHERE connection_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ai_defaults_configuration_idx ON ai_user_defaults(configuration_id) WHERE configuration_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS ai_conversation_selections (
  conversation_id uuid PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,
  user_id text NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  kind text NOT NULL CHECK (kind IN ('default','provider_model','custom_configuration','local_cli')),
  connection_id uuid,
  model_id text,
  configuration_id uuid,
  cli_id text REFERENCES ai_cli_installations(cli_id) ON DELETE RESTRICT,
  changed_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (user_id, connection_id) REFERENCES ai_provider_connections(user_id, id) ON DELETE RESTRICT,
  FOREIGN KEY (user_id, configuration_id) REFERENCES ai_custom_configurations(user_id, id) ON DELETE RESTRICT,
  CHECK (ai_choice_shape(kind, connection_id, model_id, configuration_id, cli_id, true))
);
CREATE INDEX IF NOT EXISTS ai_selections_user_idx ON ai_conversation_selections(user_id, conversation_id);

-- Strict safe JSON allowlists: no arbitrary metadata bags in history.
CREATE OR REPLACE FUNCTION ai_safe_target(v jsonb, resolved boolean DEFAULT false, allow_config boolean DEFAULT true)
RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
  IF jsonb_typeof(v) IS DISTINCT FROM 'object' THEN RETURN false; END IF;
  IF v->>'kind' = 'provider_model' THEN
    RETURN COALESCE(jsonb_typeof(v->'connectionId') = 'string' AND length(v->>'connectionId') = 36
      AND jsonb_typeof(v->'modelId') = 'string' AND btrim(v->>'modelId') <> ''
      AND v - ARRAY['kind','connectionId','modelId','providerId'] = '{}'::jsonb
      AND (CASE WHEN resolved THEN v->>'providerId' IN ('openai','anthropic','google','xai','deepseek','kimi','openrouter')
                ELSE NOT v ? 'providerId' END), false);
  ELSIF v->>'kind' = 'local_cli' THEN
    RETURN COALESCE(v->>'cliId' IN ('codex','claude_code','gemini_antigravity','kimi_code')
      AND v ? 'modelId' AND (v->'modelId' = 'null'::jsonb OR (jsonb_typeof(v->'modelId') = 'string' AND btrim(v->>'modelId') <> ''))
      AND v - ARRAY['kind','cliId','modelId'] = '{}'::jsonb, false);
  ELSIF allow_config AND v->>'kind' = 'custom_configuration' THEN
    RETURN COALESCE(jsonb_typeof(v->'configurationId') = 'string' AND length(v->>'configurationId') = 36
      AND v - ARRAY['kind','configurationId'] = '{}'::jsonb, false);
  END IF;
  RETURN false;
END $$;
CREATE OR REPLACE FUNCTION ai_snapshot_shape(selection jsonb, choice jsonb, role_map jsonb, config_version bigint)
RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE r text;
BEGIN
  IF NOT ai_safe_target(choice) OR jsonb_typeof(role_map) IS DISTINCT FROM 'object'
    OR role_map - ARRAY['synthesizer','planner','deep_planner','worker'] <> '{}'::jsonb
    OR ((choice->>'kind' = 'custom_configuration') <> (config_version IS NOT NULL))
    OR config_version <= 0 THEN RETURN false; END IF;
  IF selection IS DISTINCT FROM '{"kind":"default"}'::jsonb THEN
    IF jsonb_typeof(selection) IS DISTINCT FROM 'object' OR selection->>'kind' IS DISTINCT FROM 'explicit'
      OR selection - ARRAY['kind','choice'] <> '{}'::jsonb
      OR NOT ai_safe_target(selection->'choice') OR selection->'choice' IS DISTINCT FROM choice THEN RETURN false; END IF;
  END IF;
  FOREACH r IN ARRAY ARRAY['synthesizer','planner','deep_planner','worker'] LOOP
    IF NOT ai_safe_target(role_map->r, true, false) THEN RETURN false; END IF;
    IF choice->>'kind' <> 'custom_configuration' AND (role_map->r - 'providerId') IS DISTINCT FROM choice THEN RETURN false; END IF;
  END LOOP;
  RETURN true;
END $$;

CREATE TABLE IF NOT EXISTS ai_turn_routing_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  correlation_id text NOT NULL CHECK (btrim(correlation_id) <> ''),
  source text NOT NULL CHECK (source IN ('pariprashna','mcp','backend')),
  conversation_id uuid REFERENCES conversations(id) ON DELETE CASCADE,
  selection jsonb NOT NULL,
  resolved_choice jsonb NOT NULL,
  configuration_version bigint,
  roles jsonb NOT NULL,
  configuration_id uuid GENERATED ALWAYS AS ((resolved_choice->>'configurationId')::uuid) STORED,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, correlation_id),
  FOREIGN KEY (user_id, configuration_id) REFERENCES ai_custom_configurations(user_id, id) ON DELETE RESTRICT,
  CHECK (ai_snapshot_shape(selection, resolved_choice, roles, configuration_version))
);
CREATE INDEX IF NOT EXISTS ai_snapshots_conversation_idx ON ai_turn_routing_snapshots(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS ai_snapshots_configuration_idx ON ai_turn_routing_snapshots(configuration_id) WHERE configuration_id IS NOT NULL;

-- Generated role references retain every historical connection/CLI, including prior configuration versions.
DO $$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['synthesizer','planner','deep_planner','worker'] LOOP
    EXECUTE format('ALTER TABLE ai_turn_routing_snapshots ADD COLUMN IF NOT EXISTS %I uuid GENERATED ALWAYS AS ((roles->%L->>''connectionId'')::uuid) STORED', r || '_connection_id', r);
    EXECUTE format('ALTER TABLE ai_turn_routing_snapshots ADD COLUMN IF NOT EXISTS %I text GENERATED ALWAYS AS (roles->%L->>''cliId'') STORED', r || '_cli_id', r);
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='ai_turn_routing_snapshots'::regclass AND conname='ai_snapshot_' || r || '_connection_fk') THEN
      EXECUTE format('ALTER TABLE ai_turn_routing_snapshots ADD CONSTRAINT %I FOREIGN KEY(user_id,%I) REFERENCES ai_provider_connections(user_id,id) ON DELETE RESTRICT', 'ai_snapshot_' || r || '_connection_fk', r || '_connection_id');
      EXECUTE format('ALTER TABLE ai_turn_routing_snapshots ADD CONSTRAINT %I FOREIGN KEY(%I) REFERENCES ai_cli_installations(cli_id) ON DELETE RESTRICT', 'ai_snapshot_' || r || '_cli_fk', r || '_cli_id');
    END IF;
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON ai_turn_routing_snapshots(%I)', 'ai_snapshot_' || r || '_connection_idx', r || '_connection_id');
  END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS ai_turn_role_invocations (
  snapshot_id uuid NOT NULL REFERENCES ai_turn_routing_snapshots(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('synthesizer','planner','deep_planner','worker')),
  invocation_id uuid NOT NULL,
  phase text NOT NULL CHECK (phase IN ('start', 'terminal')),
  status text NOT NULL CHECK (status IN ('started','succeeded','failed','cancelled')),
  error_code text CHECK (error_code IN ('AI_DEFAULT_REQUIRED','AI_CHOICE_BROKEN','AI_CONNECTION_INVALID','AI_MODEL_UNAVAILABLE','AI_ROLE_INCOMPATIBLE','AI_CLI_NOT_GRANTED','AI_CLI_UNREACHABLE','AI_PROVIDER_UNREACHABLE','AI_PERMISSION_DENIED','AI_BILLING_UNAVAILABLE','AI_RATE_LIMITED','AI_CLI_NOT_INSTALLED','AI_CLI_AUTH_UNAVAILABLE','AI_CLI_TIMEOUT','AI_CLI_OUTPUT_LIMIT','AI_EXECUTION_FAILED')),
  start_phase text GENERATED ALWAYS AS (CASE WHEN phase = 'terminal' THEN 'start' END) STORED,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (snapshot_id, role, invocation_id, phase),
  FOREIGN KEY (snapshot_id, role, invocation_id, start_phase) REFERENCES ai_turn_role_invocations(snapshot_id, role, invocation_id, phase) ON DELETE RESTRICT,
  CHECK ((phase = 'start' AND status = 'started' AND error_code IS NULL)
    OR (phase = 'terminal' AND status IN ('succeeded','failed','cancelled') AND (status <> 'succeeded' OR error_code IS NULL)))
);

CREATE TABLE IF NOT EXISTS ai_configuration_audit_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  actor_user_id text NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  event text NOT NULL CHECK (event IN ('connection_created','connection_updated','connection_renamed','connection_credential_replaced','connection_validated','connection_deleted','configuration_created','configuration_updated','configuration_duplicated','configuration_deleted','default_selected','cli_granted','cli_revoked','conversation_selected')),
  connection_id uuid,
  configuration_id uuid,
  cli_id text REFERENCES ai_cli_installations(cli_id) ON DELETE RESTRICT,
  configuration_version bigint CHECK (configuration_version > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (user_id, connection_id) REFERENCES ai_provider_connections(user_id,id) ON DELETE RESTRICT,
  FOREIGN KEY (user_id, configuration_id) REFERENCES ai_custom_configurations(user_id,id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS ai_audit_user_idx ON ai_configuration_audit_log(user_id, created_at);

CREATE OR REPLACE FUNCTION ai_check_four_roles() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target uuid;
BEGIN
  IF TG_TABLE_NAME = 'ai_custom_configurations' THEN target := COALESCE(NEW.id, OLD.id);
  ELSE target := COALESCE(NEW.configuration_id, OLD.configuration_id); END IF;
  -- Serialize checks without upgrading the FK's KEY SHARE to a conflicting lock.
  PERFORM 1 FROM ai_custom_configurations WHERE id=target FOR NO KEY UPDATE;
  IF FOUND AND (SELECT count(*) FROM ai_custom_configuration_roles WHERE configuration_id=target) <> 4 THEN
    RAISE EXCEPTION 'AI configuration requires all four roles' USING ERRCODE='23514';
  END IF;
  IF TG_OP='UPDATE' AND TG_TABLE_NAME='ai_custom_configuration_roles' THEN
    IF OLD.configuration_id IS DISTINCT FROM NEW.configuration_id THEN
      PERFORM 1 FROM ai_custom_configurations WHERE id=OLD.configuration_id FOR NO KEY UPDATE;
      IF FOUND AND (SELECT count(*) FROM ai_custom_configuration_roles WHERE configuration_id=OLD.configuration_id) <> 4 THEN
        RAISE EXCEPTION 'AI configuration requires all four roles' USING ERRCODE='23514';
      END IF;
    END IF;
  END IF;
  RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS ai_configuration_four_roles ON ai_custom_configurations;
CREATE CONSTRAINT TRIGGER ai_configuration_four_roles AFTER INSERT OR UPDATE ON ai_custom_configurations DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ai_check_four_roles();
DROP TRIGGER IF EXISTS ai_roles_four_roles ON ai_custom_configuration_roles;
CREATE CONSTRAINT TRIGGER ai_roles_four_roles AFTER INSERT OR UPDATE OR DELETE ON ai_custom_configuration_roles DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ai_check_four_roles();

CREATE OR REPLACE FUNCTION ai_configuration_version_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.id IS DISTINCT FROM OLD.id OR NEW.user_id IS DISTINCT FROM OLD.user_id OR NEW.version <> OLD.version + 1 THEN
    RAISE EXCEPTION 'AI configuration update requires immutable identity and next version' USING ERRCODE='23514';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS ai_configuration_version ON ai_custom_configurations;
CREATE TRIGGER ai_configuration_version BEFORE UPDATE ON ai_custom_configurations FOR EACH ROW EXECUTE FUNCTION ai_configuration_version_guard();

CREATE OR REPLACE FUNCTION ai_check_conversation_owner() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE cid uuid; owner_id text;
BEGIN
  IF TG_TABLE_NAME = 'conversations' THEN cid := NEW.id; ELSE cid := NEW.conversation_id; END IF;
  IF cid IS NULL THEN RETURN NULL; END IF;
  SELECT user_id INTO owner_id FROM conversations WHERE id=cid FOR NO KEY UPDATE;
  IF EXISTS (SELECT 1 FROM ai_conversation_selections WHERE conversation_id=cid AND user_id IS DISTINCT FROM owner_id)
    OR EXISTS (SELECT 1 FROM ai_turn_routing_snapshots WHERE conversation_id=cid AND user_id IS DISTINCT FROM owner_id) THEN
    RAISE EXCEPTION 'AI conversation owner mismatch' USING ERRCODE='23514';
  END IF;
  RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS ai_selection_owner ON ai_conversation_selections;
CREATE CONSTRAINT TRIGGER ai_selection_owner AFTER INSERT OR UPDATE ON ai_conversation_selections DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ai_check_conversation_owner();
DROP TRIGGER IF EXISTS ai_snapshot_owner ON ai_turn_routing_snapshots;
CREATE CONSTRAINT TRIGGER ai_snapshot_owner AFTER INSERT ON ai_turn_routing_snapshots DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ai_check_conversation_owner();
DROP TRIGGER IF EXISTS ai_conversation_owner ON conversations;
CREATE CONSTRAINT TRIGGER ai_conversation_owner AFTER UPDATE ON conversations DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ai_check_conversation_owner();

CREATE OR REPLACE FUNCTION ai_reject_history_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  -- Conversation/consent erasure is the sole exception to ordinary append-only history.
  -- FK cascades run after their parent disappears, at nested trigger depth. Requiring
  -- BOTH conditions prevents direct DELETE (including DELETE with a forged setting).
  -- Audit rows have no conversation payload and are never included in this exception.
  IF TG_OP = 'DELETE' AND pg_trigger_depth() > 1 THEN
    IF TG_TABLE_NAME = 'ai_turn_routing_snapshots' THEN
      IF OLD.conversation_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM conversations WHERE id = OLD.conversation_id) THEN
        RETURN OLD;
      END IF;
    ELSIF TG_TABLE_NAME = 'ai_turn_role_invocations' THEN
      IF NOT EXISTS (SELECT 1 FROM ai_turn_routing_snapshots WHERE id = OLD.snapshot_id) THEN
        RETURN OLD;
      END IF;
    END IF;
  END IF;
  RAISE EXCEPTION 'AI history is append-only' USING ERRCODE='23514';
END $$;
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['ai_turn_routing_snapshots','ai_turn_role_invocations','ai_configuration_audit_log'] LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS ai_history_immutable ON %I', t);
    EXECUTE format('CREATE TRIGGER ai_history_immutable BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION ai_reject_history_mutation()', t);
    EXECUTE format('DROP TRIGGER IF EXISTS ai_history_no_truncate ON %I', t);
    EXECUTE format('CREATE TRIGGER ai_history_no_truncate BEFORE TRUNCATE ON %I FOR EACH STATEMENT EXECUTE FUNCTION ai_reject_history_mutation()', t);
  END LOOP;
  FOREACH t IN ARRAY ARRAY['ai_provider_connections','ai_connection_models','ai_custom_configurations',
    'ai_custom_configuration_roles','ai_user_defaults','ai_cli_installations','ai_cli_models','ai_cli_grants',
    'ai_conversation_selections','ai_turn_routing_snapshots','ai_turn_role_invocations','ai_configuration_audit_log'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('REVOKE ALL ON TABLE %I FROM PUBLIC', t);
    -- Supabase service role is optional in Firebase-only installs; table owner remains the trusted server.
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='service_role') THEN
      EXECUTE format('DROP POLICY IF EXISTS ai_service_only ON %I', t);
      EXECUTE format('CREATE POLICY ai_service_only ON %I TO service_role USING (true) WITH CHECK (true)', t);
      EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE %I TO service_role', t);
      IF t IN ('ai_turn_routing_snapshots','ai_turn_role_invocations','ai_configuration_audit_log') THEN
        EXECUTE format('REVOKE UPDATE, DELETE, TRUNCATE ON TABLE %I FROM service_role', t);
      END IF;
    END IF;
  END LOOP;
END $$;

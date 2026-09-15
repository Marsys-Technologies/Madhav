-- Migration 1038: durable, principal-bound managed Prashna jobs
-- Active migration tree: platform/supabase/migrations.
-- Created: 2026-09-15
-- Allocation: 1035/1036 are reserved by the Data Plane stack; 1037 is the
-- planner inquiry action-reservation migration in this recovery wave.

BEGIN;

CREATE TABLE IF NOT EXISTS planner_managed_prashna_jobs (
  job_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  principal_uid text NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  principal_key_id text NOT NULL,
  principal_auth_kind text NOT NULL CHECK (principal_auth_kind IN ('api_key', 'oauth')),
  api_key_id text,
  oauth_token_hash text,
  chart_id uuid NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
  request_jsonb jsonb NOT NULL CHECK (jsonb_typeof(request_jsonb) = 'object'),
  status text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'running', 'complete', 'failed')),
  progress_jsonb jsonb,
  result_jsonb jsonb,
  error_text text,
  lease_owner text,
  lease_expires_at timestamptz,
  terminal_worker_id text,
  attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count BETWEEN 0 AND 3),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  retention_expires_at timestamptz NOT NULL DEFAULT (now() + interval '24 hours'),
  CONSTRAINT planner_managed_prashna_jobs_key_owner_fk
    FOREIGN KEY (api_key_id) REFERENCES mcp_api_keys(key_id) ON DELETE CASCADE,
  CONSTRAINT planner_managed_prashna_jobs_oauth_owner_fk
    FOREIGN KEY (oauth_token_hash) REFERENCES mcp_oauth_tokens(access_token_hash) ON DELETE CASCADE,
  CONSTRAINT planner_managed_prashna_jobs_credential_shape CHECK (
    (principal_auth_kind = 'api_key' AND api_key_id = principal_key_id
      AND oauth_token_hash IS NULL)
    OR
    (principal_auth_kind = 'oauth' AND api_key_id IS NULL
      AND principal_key_id = 'oauth_sha256:' || oauth_token_hash
      AND oauth_token_hash ~ '^[0-9a-f]{64}$')
  ),
  CONSTRAINT planner_managed_prashna_jobs_state_shape CHECK (
    (status = 'pending' AND lease_owner IS NULL AND lease_expires_at IS NULL
      AND terminal_worker_id IS NULL
      AND result_jsonb IS NULL AND error_text IS NULL)
    OR
    (status = 'running' AND lease_owner IS NOT NULL AND lease_expires_at IS NOT NULL
      AND terminal_worker_id IS NULL
      AND result_jsonb IS NULL AND error_text IS NULL)
    OR
    (status = 'complete' AND lease_owner IS NULL AND lease_expires_at IS NULL
      AND terminal_worker_id IS NOT NULL
      AND result_jsonb IS NOT NULL AND error_text IS NULL)
    OR
    (status = 'failed' AND lease_owner IS NULL AND lease_expires_at IS NULL
      AND terminal_worker_id IS NOT NULL
      AND result_jsonb IS NULL AND error_text IS NOT NULL)
  )
);

CREATE INDEX IF NOT EXISTS planner_managed_prashna_jobs_owner_idx
  ON planner_managed_prashna_jobs (principal_uid, principal_key_id, created_at DESC);
CREATE INDEX IF NOT EXISTS planner_managed_prashna_jobs_recovery_idx
  ON planner_managed_prashna_jobs (lease_expires_at)
  WHERE status = 'running';
CREATE INDEX IF NOT EXISTS planner_managed_prashna_jobs_retention_idx
  ON planner_managed_prashna_jobs (retention_expires_at);

COMMENT ON TABLE planner_managed_prashna_jobs IS
  'Durable managed-MCP Prashna requests and full terminal results. Job ids are correlation handles; every function also binds principal UID and authenticated credential id. retention_expires_at is the hard logical access deadline; guaranteed physical erasure requires the separately operated maintenance schedule.';

CREATE OR REPLACE FUNCTION planner_managed_prashna_job_credential_guard()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  credential_owner text;
BEGIN
  IF NEW.principal_auth_kind = 'api_key' THEN
    SELECT user_uid INTO credential_owner FROM public.mcp_api_keys
     WHERE key_id = NEW.api_key_id AND revoked_at IS NULL
     FOR NO KEY UPDATE;
  ELSIF NEW.principal_auth_kind = 'oauth' THEN
    SELECT uid INTO credential_owner FROM public.mcp_oauth_tokens
     WHERE access_token_hash = NEW.oauth_token_hash AND expires_at > now()
     FOR NO KEY UPDATE;
  END IF;
  IF credential_owner IS NULL OR credential_owner IS DISTINCT FROM NEW.principal_uid THEN
    RAISE EXCEPTION 'planner managed job credential owner mismatch' USING ERRCODE = '42501';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS planner_managed_prashna_job_credential_guard_trigger
  ON planner_managed_prashna_jobs;
CREATE TRIGGER planner_managed_prashna_job_credential_guard_trigger
BEFORE INSERT ON planner_managed_prashna_jobs
FOR EACH ROW EXECUTE FUNCTION planner_managed_prashna_job_credential_guard();

CREATE OR REPLACE FUNCTION planner_managed_prashna_job_immutable_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF ROW(NEW.job_id, NEW.principal_uid, NEW.principal_key_id,
         NEW.principal_auth_kind, NEW.api_key_id, NEW.oauth_token_hash, NEW.chart_id,
         NEW.request_jsonb, NEW.created_at, NEW.retention_expires_at)
     IS DISTINCT FROM
     ROW(OLD.job_id, OLD.principal_uid, OLD.principal_key_id,
         OLD.principal_auth_kind, OLD.api_key_id, OLD.oauth_token_hash, OLD.chart_id,
         OLD.request_jsonb, OLD.created_at, OLD.retention_expires_at) THEN
    RAISE EXCEPTION 'planner managed job immutable identity cannot change';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS planner_managed_prashna_job_immutable_guard_trigger
  ON planner_managed_prashna_jobs;
CREATE TRIGGER planner_managed_prashna_job_immutable_guard_trigger
BEFORE UPDATE ON planner_managed_prashna_jobs
FOR EACH ROW EXECUTE FUNCTION planner_managed_prashna_job_immutable_guard();

CREATE OR REPLACE FUNCTION create_planner_managed_prashna_job(
  p_job_id uuid,
  p_principal_uid text,
  p_principal_key_id text,
  p_principal_auth_kind text,
  p_chart_id uuid,
  p_request_jsonb jsonb
)
RETURNS SETOF planner_managed_prashna_jobs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  recent_count integer;
  active_count integer;
  credential_active boolean;
  current_job public.planner_managed_prashna_jobs%ROWTYPE;
BEGIN
  IF p_principal_uid IS DISTINCT FROM current_setting('app.principal_id', true)
     OR p_chart_id IS DISTINCT FROM public.app_chart_context()
     OR length(p_principal_key_id) < 1
     OR p_principal_auth_kind NOT IN ('api_key', 'oauth')
     OR (p_principal_auth_kind = 'oauth'
         AND p_principal_key_id !~ '^oauth_sha256:[0-9a-f]{64}$')
     OR jsonb_typeof(p_request_jsonb) IS DISTINCT FROM 'object' THEN
    RAISE EXCEPTION 'planner managed job creation context mismatch' USING ERRCODE = '42501';
  END IF;

  -- The caller chooses the job UUID before the request. Serializing on that UUID
  -- makes an ambiguous HTTP retry create-or-return-same-request, never a second
  -- orphan job. Reusing the UUID for a different owner or payload fails closed.
  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('managed-job-id:' || p_job_id::text, 0)
  );
  SELECT * INTO current_job FROM public.planner_managed_prashna_jobs
   WHERE job_id = p_job_id;
  IF FOUND THEN
    IF current_job.principal_uid IS DISTINCT FROM p_principal_uid
       OR current_job.principal_key_id IS DISTINCT FROM p_principal_key_id
       OR current_job.principal_auth_kind IS DISTINCT FROM p_principal_auth_kind
       OR current_job.chart_id IS DISTINCT FROM p_chart_id
       OR current_job.request_jsonb IS DISTINCT FROM p_request_jsonb
       OR current_job.retention_expires_at <= now() THEN
      RAISE EXCEPTION 'MANAGED_JOB_IDEMPOTENCY_CONFLICT' USING ERRCODE = '23505';
    END IF;
    IF current_job.principal_auth_kind = 'api_key' THEN
      SELECT EXISTS (
        SELECT 1 FROM public.mcp_api_keys AS key
         WHERE key.key_id=current_job.api_key_id
           AND key.user_uid=current_job.principal_uid AND key.revoked_at IS NULL
      ) INTO credential_active;
    ELSE
      SELECT EXISTS (
        SELECT 1 FROM public.mcp_oauth_tokens AS token
         WHERE token.access_token_hash=current_job.oauth_token_hash
           AND token.uid=current_job.principal_uid AND token.expires_at > now()
      ) INTO credential_active;
    END IF;
    IF NOT coalesce(credential_active, false) THEN
      RAISE EXCEPTION 'planner managed job credential is no longer active' USING ERRCODE = '42501';
    END IF;
    RETURN NEXT current_job;
    RETURN;
  END IF;

  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_principal_uid || ':' || p_principal_key_id, 0)
  );
  -- Bounded opportunistic physical cleanup. `retention_expires_at` is a hard
  -- logical access deadline; a separately operated maintenance schedule is
  -- still required to guarantee physical deletion for an otherwise quiet fleet.
  DELETE FROM public.planner_managed_prashna_jobs
   WHERE ctid IN (
     SELECT ctid FROM public.planner_managed_prashna_jobs
      WHERE retention_expires_at <= now()
      ORDER BY retention_expires_at
      LIMIT 500
   );
  DELETE FROM public.planner_managed_prashna_jobs
   WHERE principal_uid=p_principal_uid AND principal_key_id=p_principal_key_id
     AND retention_expires_at <= now();

  SELECT count(*) INTO recent_count
    FROM public.planner_managed_prashna_jobs
   WHERE principal_uid=p_principal_uid AND principal_key_id=p_principal_key_id
     AND created_at > now() - interval '1 hour';
  IF recent_count >= 32 THEN
    RAISE EXCEPTION 'MANAGED_JOB_CREATION_RATE_LIMITED' USING ERRCODE = 'P0001';
  END IF;

  SELECT count(*) INTO active_count
    FROM public.planner_managed_prashna_jobs
   WHERE principal_uid=p_principal_uid AND principal_key_id=p_principal_key_id
     AND chart_id=p_chart_id AND status IN ('pending','running');
  IF active_count >= 8 THEN
    RAISE EXCEPTION 'MANAGED_JOB_ACTIVE_LIMIT_REACHED' USING ERRCODE = 'P0001';
  END IF;

  RETURN QUERY
  INSERT INTO public.planner_managed_prashna_jobs
    (job_id, principal_uid, principal_key_id, principal_auth_kind,
     api_key_id, oauth_token_hash, chart_id, request_jsonb)
  VALUES (
    p_job_id, p_principal_uid, p_principal_key_id, p_principal_auth_kind,
    CASE WHEN p_principal_auth_kind = 'api_key' THEN p_principal_key_id END,
    CASE WHEN p_principal_auth_kind = 'oauth' THEN substring(p_principal_key_id FROM 14) END,
    p_chart_id, p_request_jsonb
  )
  RETURNING *;
END;
$$;

CREATE OR REPLACE FUNCTION get_planner_managed_prashna_job(
  p_job_id uuid,
  p_principal_uid text,
  p_principal_key_id text
)
RETURNS SETOF planner_managed_prashna_jobs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  IF p_principal_uid IS DISTINCT FROM current_setting('app.principal_id', true) THEN
    RAISE EXCEPTION 'planner managed job principal context mismatch' USING ERRCODE = '42501';
  END IF;
  RETURN QUERY
  SELECT job.* FROM public.planner_managed_prashna_jobs AS job
   WHERE job.job_id=p_job_id AND job.principal_uid=p_principal_uid
     AND job.principal_key_id=p_principal_key_id AND job.retention_expires_at > now()
     AND (
       (job.principal_auth_kind = 'api_key' AND EXISTS (
         SELECT 1 FROM public.mcp_api_keys AS key
          WHERE key.key_id=job.api_key_id AND key.user_uid=job.principal_uid
            AND key.revoked_at IS NULL
       ))
       OR
       (job.principal_auth_kind = 'oauth' AND EXISTS (
         SELECT 1 FROM public.mcp_oauth_tokens AS token
          WHERE token.access_token_hash=job.oauth_token_hash
            AND token.uid=job.principal_uid AND token.expires_at > now()
       ))
     );
END;
$$;

CREATE OR REPLACE FUNCTION claim_planner_managed_prashna_job(
  p_job_id uuid,
  p_principal_uid text,
  p_principal_key_id text,
  p_lease_owner text,
  p_lease_seconds integer DEFAULT 450
)
RETURNS SETOF planner_managed_prashna_jobs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  current_job public.planner_managed_prashna_jobs%ROWTYPE;
  bounded_lease integer;
BEGIN
  IF p_principal_uid IS DISTINCT FROM current_setting('app.principal_id', true)
     OR length(p_lease_owner) < 1 THEN
    RAISE EXCEPTION 'planner managed job claim context mismatch' USING ERRCODE = '42501';
  END IF;
  bounded_lease := greatest(30, least(p_lease_seconds, 600));
  SELECT job.* INTO current_job FROM public.planner_managed_prashna_jobs AS job
   WHERE job.job_id=p_job_id AND job.principal_uid=p_principal_uid
     AND job.principal_key_id=p_principal_key_id AND job.retention_expires_at > now()
     AND (
       (job.principal_auth_kind = 'api_key' AND EXISTS (
         SELECT 1 FROM public.mcp_api_keys AS key
          WHERE key.key_id=job.api_key_id AND key.user_uid=job.principal_uid
            AND key.revoked_at IS NULL
       ))
       OR
       (job.principal_auth_kind = 'oauth' AND EXISTS (
         SELECT 1 FROM public.mcp_oauth_tokens AS token
          WHERE token.access_token_hash=job.oauth_token_hash
            AND token.uid=job.principal_uid AND token.expires_at > now()
       ))
     )
   FOR UPDATE OF job;
  IF NOT FOUND THEN RETURN; END IF;

  IF current_job.status IN ('complete','failed')
     OR (current_job.status='running' AND current_job.lease_expires_at > now()) THEN
    RETURN NEXT current_job;
    RETURN;
  END IF;

  IF current_job.attempt_count >= 3 THEN
    UPDATE public.planner_managed_prashna_jobs
       SET status='failed', error_text='MANAGED_JOB_RETRY_EXHAUSTED',
           lease_owner=NULL, lease_expires_at=NULL,
           terminal_worker_id=p_lease_owner, updated_at=now()
     WHERE job_id=p_job_id
     RETURNING * INTO current_job;
    RETURN NEXT current_job;
    RETURN;
  END IF;

  UPDATE public.planner_managed_prashna_jobs AS job
     SET status='running', lease_owner=p_lease_owner,
         lease_expires_at=now() + make_interval(secs => bounded_lease),
         attempt_count=attempt_count+1,
         progress_jsonb=coalesce(progress_jsonb, '{"message":"prashna_ask: engine call started","pct":0}'::jsonb),
         updated_at=now()
   WHERE job_id=p_job_id
   RETURNING * INTO current_job;
  RETURN NEXT current_job;
END;
$$;

CREATE OR REPLACE FUNCTION update_planner_managed_prashna_job_progress(
  p_job_id uuid,
  p_principal_uid text,
  p_principal_key_id text,
  p_lease_owner text,
  p_progress_jsonb jsonb,
  p_lease_seconds integer DEFAULT 450
)
RETURNS SETOF planner_managed_prashna_jobs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  IF p_principal_uid IS DISTINCT FROM current_setting('app.principal_id', true)
     OR jsonb_typeof(p_progress_jsonb) IS DISTINCT FROM 'object' THEN
    RAISE EXCEPTION 'planner managed job progress context mismatch' USING ERRCODE = '42501';
  END IF;
  RETURN QUERY
  UPDATE public.planner_managed_prashna_jobs AS job
     SET progress_jsonb=p_progress_jsonb,
         lease_expires_at=now() + make_interval(secs => greatest(30, least(p_lease_seconds, 600))),
         updated_at=now()
   WHERE job.job_id=p_job_id AND job.principal_uid=p_principal_uid
     AND job.principal_key_id=p_principal_key_id AND job.status='running'
     AND job.lease_owner=p_lease_owner AND job.retention_expires_at > now()
     AND (
       (job.principal_auth_kind = 'api_key' AND EXISTS (
         SELECT 1 FROM public.mcp_api_keys AS key
          WHERE key.key_id=job.api_key_id AND key.user_uid=job.principal_uid
            AND key.revoked_at IS NULL
       ))
       OR
       (job.principal_auth_kind = 'oauth' AND EXISTS (
         SELECT 1 FROM public.mcp_oauth_tokens AS token
          WHERE token.access_token_hash=job.oauth_token_hash
            AND token.uid=job.principal_uid AND token.expires_at > now()
       ))
     )
   RETURNING job.*;
END;
$$;

CREATE OR REPLACE FUNCTION complete_planner_managed_prashna_job(
  p_job_id uuid,
  p_principal_uid text,
  p_principal_key_id text,
  p_lease_owner text,
  p_result_jsonb jsonb
)
RETURNS SETOF planner_managed_prashna_jobs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  IF p_principal_uid IS DISTINCT FROM current_setting('app.principal_id', true)
     OR jsonb_typeof(p_result_jsonb) IS DISTINCT FROM 'object' THEN
    RAISE EXCEPTION 'planner managed job completion context mismatch' USING ERRCODE = '42501';
  END IF;
  RETURN QUERY
  UPDATE public.planner_managed_prashna_jobs AS job
     SET status='complete', result_jsonb=p_result_jsonb, error_text=NULL,
         progress_jsonb='{"message":"prashna_ask: complete","pct":100}'::jsonb,
         lease_owner=NULL, lease_expires_at=NULL,
         terminal_worker_id=p_lease_owner, updated_at=now()
   WHERE job.job_id=p_job_id AND job.principal_uid=p_principal_uid
     AND job.principal_key_id=p_principal_key_id AND job.status='running'
     AND job.lease_owner=p_lease_owner AND job.retention_expires_at > now()
     AND (
       (job.principal_auth_kind = 'api_key' AND EXISTS (
         SELECT 1 FROM public.mcp_api_keys AS key
          WHERE key.key_id=job.api_key_id AND key.user_uid=job.principal_uid
            AND key.revoked_at IS NULL
       ))
       OR
       (job.principal_auth_kind = 'oauth' AND EXISTS (
         SELECT 1 FROM public.mcp_oauth_tokens AS token
          WHERE token.access_token_hash=job.oauth_token_hash
            AND token.uid=job.principal_uid AND token.expires_at > now()
       ))
     )
   RETURNING job.*;
  IF FOUND THEN RETURN; END IF;

  -- A terminal-store HTTP acknowledgement can be lost after the transaction
  -- commits. Reconcile that ambiguity only for the same worker and identical
  -- result; a different worker or payload remains a lease conflict.
  RETURN QUERY
  SELECT job.* FROM public.planner_managed_prashna_jobs AS job
   WHERE job.job_id=p_job_id AND job.principal_uid=p_principal_uid
     AND job.principal_key_id=p_principal_key_id AND job.status='complete'
     AND job.terminal_worker_id=p_lease_owner
     AND job.result_jsonb IS NOT DISTINCT FROM p_result_jsonb
     AND job.retention_expires_at > now()
     AND (
       (job.principal_auth_kind = 'api_key' AND EXISTS (
         SELECT 1 FROM public.mcp_api_keys AS key
          WHERE key.key_id=job.api_key_id AND key.user_uid=job.principal_uid
            AND key.revoked_at IS NULL
       ))
       OR
       (job.principal_auth_kind = 'oauth' AND EXISTS (
         SELECT 1 FROM public.mcp_oauth_tokens AS token
          WHERE token.access_token_hash=job.oauth_token_hash
            AND token.uid=job.principal_uid AND token.expires_at > now()
       ))
     );
END;
$$;

CREATE OR REPLACE FUNCTION fail_planner_managed_prashna_job(
  p_job_id uuid,
  p_principal_uid text,
  p_principal_key_id text,
  p_lease_owner text,
  p_error_text text
)
RETURNS SETOF planner_managed_prashna_jobs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  bounded_error text;
BEGIN
  IF p_principal_uid IS DISTINCT FROM current_setting('app.principal_id', true)
     OR length(p_error_text) < 1 THEN
    RAISE EXCEPTION 'planner managed job failure context mismatch' USING ERRCODE = '42501';
  END IF;
  bounded_error := left(p_error_text, 1000);
  RETURN QUERY
  UPDATE public.planner_managed_prashna_jobs AS job
     SET status='failed', error_text=bounded_error, result_jsonb=NULL,
         progress_jsonb='{"message":"prashna_ask: failed","pct":100}'::jsonb,
         lease_owner=NULL, lease_expires_at=NULL,
         terminal_worker_id=p_lease_owner, updated_at=now()
   WHERE job.job_id=p_job_id AND job.principal_uid=p_principal_uid
     AND job.principal_key_id=p_principal_key_id AND job.status='running'
     AND job.lease_owner=p_lease_owner AND job.retention_expires_at > now()
     AND (
       (job.principal_auth_kind = 'api_key' AND EXISTS (
         SELECT 1 FROM public.mcp_api_keys AS key
          WHERE key.key_id=job.api_key_id AND key.user_uid=job.principal_uid
            AND key.revoked_at IS NULL
       ))
       OR
       (job.principal_auth_kind = 'oauth' AND EXISTS (
         SELECT 1 FROM public.mcp_oauth_tokens AS token
          WHERE token.access_token_hash=job.oauth_token_hash
            AND token.uid=job.principal_uid AND token.expires_at > now()
       ))
     )
   RETURNING job.*;
  IF FOUND THEN RETURN; END IF;

  RETURN QUERY
  SELECT job.* FROM public.planner_managed_prashna_jobs AS job
   WHERE job.job_id=p_job_id AND job.principal_uid=p_principal_uid
     AND job.principal_key_id=p_principal_key_id AND job.status='failed'
     AND job.terminal_worker_id=p_lease_owner
     AND job.error_text IS NOT DISTINCT FROM bounded_error
     AND job.retention_expires_at > now()
     AND (
       (job.principal_auth_kind = 'api_key' AND EXISTS (
         SELECT 1 FROM public.mcp_api_keys AS key
          WHERE key.key_id=job.api_key_id AND key.user_uid=job.principal_uid
            AND key.revoked_at IS NULL
       ))
       OR
       (job.principal_auth_kind = 'oauth' AND EXISTS (
         SELECT 1 FROM public.mcp_oauth_tokens AS token
          WHERE token.access_token_hash=job.oauth_token_hash
            AND token.uid=job.principal_uid AND token.expires_at > now()
       ))
     );
END;
$$;

REVOKE ALL ON planner_managed_prashna_jobs FROM PUBLIC, role_web_serve;
REVOKE ALL ON FUNCTION planner_managed_prashna_job_credential_guard() FROM PUBLIC;
REVOKE ALL ON FUNCTION planner_managed_prashna_job_immutable_guard() FROM PUBLIC;
REVOKE ALL ON FUNCTION create_planner_managed_prashna_job(uuid,text,text,text,uuid,jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION get_planner_managed_prashna_job(uuid,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION claim_planner_managed_prashna_job(uuid,text,text,text,integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION update_planner_managed_prashna_job_progress(uuid,text,text,text,jsonb,integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION complete_planner_managed_prashna_job(uuid,text,text,text,jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION fail_planner_managed_prashna_job(uuid,text,text,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION create_planner_managed_prashna_job(uuid,text,text,text,uuid,jsonb) TO role_web_serve;
GRANT EXECUTE ON FUNCTION get_planner_managed_prashna_job(uuid,text,text) TO role_web_serve;
GRANT EXECUTE ON FUNCTION claim_planner_managed_prashna_job(uuid,text,text,text,integer) TO role_web_serve;
GRANT EXECUTE ON FUNCTION update_planner_managed_prashna_job_progress(uuid,text,text,text,jsonb,integer) TO role_web_serve;
GRANT EXECUTE ON FUNCTION complete_planner_managed_prashna_job(uuid,text,text,text,jsonb) TO role_web_serve;
GRANT EXECUTE ON FUNCTION fail_planner_managed_prashna_job(uuid,text,text,text,text) TO role_web_serve;

ALTER TABLE planner_managed_prashna_jobs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS planner_managed_prashna_jobs_principal_chart ON planner_managed_prashna_jobs;
CREATE POLICY planner_managed_prashna_jobs_principal_chart
  ON planner_managed_prashna_jobs AS PERMISSIVE FOR ALL TO role_web_serve
  USING (principal_uid = current_setting('app.principal_id', true)
         AND chart_id = app_chart_context())
  WITH CHECK (principal_uid = current_setting('app.principal_id', true)
              AND chart_id = app_chart_context());

COMMIT;

-- DOWN (manual, destructive; retain/export terminal job evidence before use):
-- DROP FUNCTION IF EXISTS fail_planner_managed_prashna_job(uuid,text,text,text,text);
-- DROP FUNCTION IF EXISTS complete_planner_managed_prashna_job(uuid,text,text,text,jsonb);
-- DROP FUNCTION IF EXISTS update_planner_managed_prashna_job_progress(uuid,text,text,text,jsonb,integer);
-- DROP FUNCTION IF EXISTS claim_planner_managed_prashna_job(uuid,text,text,text,integer);
-- DROP FUNCTION IF EXISTS get_planner_managed_prashna_job(uuid,text,text);
-- DROP FUNCTION IF EXISTS create_planner_managed_prashna_job(uuid,text,text,text,uuid,jsonb);
-- DROP TABLE IF EXISTS planner_managed_prashna_jobs;
-- DROP FUNCTION IF EXISTS planner_managed_prashna_job_immutable_guard();
-- DROP FUNCTION IF EXISTS planner_managed_prashna_job_credential_guard();

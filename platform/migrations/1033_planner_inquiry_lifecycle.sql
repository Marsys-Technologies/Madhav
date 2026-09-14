-- Migration 1033: durable planner inquiry lifecycle and evidence receipts
-- Created: 2026-09-13

BEGIN;

CREATE TABLE IF NOT EXISTS planner_inquiry_lifecycles (
  inquiry_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  principal_uid text NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  chart_id uuid NOT NULL REFERENCES charts(id) ON DELETE RESTRICT,
  semantic_contract_hash text NOT NULL,
  execution_plan_hash text NOT NULL,
  capability_content_hash text NOT NULL,
  capability_compatibility_version text NOT NULL,
  chart_overlay_version text,
  chart_build_id text,
  authorization_jsonb jsonb NOT NULL,
  contract_jsonb jsonb NOT NULL,
  status text NOT NULL DEFAULT 'INCOMPLETE'
    CHECK (status IN ('INCOMPLETE', 'COMPLETE', 'BLOCKED')),
  revision integer NOT NULL DEFAULT 0 CHECK (revision >= 0),
  current_jti_hash text NOT NULL,
  expires_at timestamptz NOT NULL,
  retention_expires_at timestamptz NOT NULL DEFAULT (now() + interval '30 days'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS planner_inquiry_lifecycles_principal_chart_idx
  ON planner_inquiry_lifecycles (principal_uid, chart_id, created_at DESC);

CREATE INDEX IF NOT EXISTS planner_inquiry_lifecycles_expiry_idx
  ON planner_inquiry_lifecycles (expires_at)
  WHERE status = 'INCOMPLETE';

CREATE TABLE IF NOT EXISTS planner_inquiry_evidence_receipts (
  receipt_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  inquiry_id uuid NOT NULL REFERENCES planner_inquiry_lifecycles(inquiry_id) ON DELETE CASCADE,
  revision integer NOT NULL CHECK (revision >= 1),
  obligation_ids text[] NOT NULL,
  plan_item_id text NOT NULL,
  scu_id text NOT NULL,
  binding_id text NOT NULL,
  canonical_args_hash text NOT NULL,
  raw_result_hash text NOT NULL,
  disposition text NOT NULL CHECK (disposition IN ('served', 'empty', 'dark', 'failed')),
  pagination_jsonb jsonb NOT NULL DEFAULT '{"semantics":"none","exhausted":true}'::jsonb,
  evidence_jsonb jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (inquiry_id, revision)
);

CREATE INDEX IF NOT EXISTS planner_inquiry_evidence_receipts_inquiry_idx
  ON planner_inquiry_evidence_receipts (inquiry_id, created_at);

CREATE INDEX IF NOT EXISTS planner_inquiry_evidence_receipts_item_idx
  ON planner_inquiry_evidence_receipts (inquiry_id, plan_item_id, revision);

COMMENT ON TABLE planner_inquiry_lifecycles IS
  'Durable, principal-bound Inquiry Contract state. current_jti_hash + revision are consumed with compare-and-swap; raw MCP tokens are not bearer access to chart evidence.';
COMMENT ON TABLE planner_inquiry_evidence_receipts IS
  'Server-observed raw retrieval evidence. A client cannot self-assert served/empty completion.';
COMMENT ON COLUMN planner_inquiry_lifecycles.chart_build_id IS
  'Opaque build/provenance token copied from the chart overlay. Not a build_runs foreign key because legacy build identities are not uniformly UUID typed.';

-- Existing table grants are point-in-time, so new lifecycle tables require
-- explicit least-privilege grants. Evidence rows are immutable to the web role.
REVOKE INSERT ON planner_inquiry_lifecycles FROM role_web_serve;
GRANT SELECT ON planner_inquiry_lifecycles TO role_web_serve;
GRANT UPDATE (contract_jsonb, status, revision, current_jti_hash, updated_at)
  ON planner_inquiry_lifecycles TO role_web_serve;
GRANT SELECT, INSERT ON planner_inquiry_evidence_receipts TO role_web_serve;

CREATE INDEX IF NOT EXISTS planner_inquiry_lifecycles_retention_idx
  ON planner_inquiry_lifecycles (retention_expires_at);

CREATE OR REPLACE FUNCTION planner_inquiry_immutable_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF ROW(NEW.inquiry_id, NEW.principal_uid, NEW.chart_id, NEW.semantic_contract_hash,
         NEW.execution_plan_hash, NEW.capability_content_hash,
         NEW.capability_compatibility_version, NEW.chart_overlay_version,
         NEW.chart_build_id, NEW.authorization_jsonb, NEW.expires_at,
         NEW.retention_expires_at)
     IS DISTINCT FROM
     ROW(OLD.inquiry_id, OLD.principal_uid, OLD.chart_id, OLD.semantic_contract_hash,
         OLD.execution_plan_hash, OLD.capability_content_hash,
         OLD.capability_compatibility_version, OLD.chart_overlay_version,
         OLD.chart_build_id, OLD.authorization_jsonb, OLD.expires_at,
         OLD.retention_expires_at) THEN
    RAISE EXCEPTION 'planner inquiry immutable authorization cannot change';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS planner_inquiry_immutable_guard_trigger ON planner_inquiry_lifecycles;
CREATE TRIGGER planner_inquiry_immutable_guard_trigger
BEFORE UPDATE ON planner_inquiry_lifecycles
FOR EACH ROW EXECUTE FUNCTION planner_inquiry_immutable_guard();

CREATE OR REPLACE FUNCTION create_planner_inquiry_lifecycle(
  p_inquiry_id uuid,
  p_principal_uid text,
  p_chart_id uuid,
  p_semantic_contract_hash text,
  p_execution_plan_hash text,
  p_capability_content_hash text,
  p_capability_compatibility_version text,
  p_chart_overlay_version text,
  p_chart_build_id text,
  p_authorization_jsonb jsonb,
  p_contract_jsonb jsonb,
  p_status text,
  p_current_jti_hash text,
  p_expires_at timestamptz
)
RETURNS SETOF planner_inquiry_lifecycles
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  recent_count integer;
  active_count integer;
BEGIN
  IF p_principal_uid IS DISTINCT FROM current_setting('app.principal_id', true)
     OR p_chart_id IS DISTINCT FROM public.app_chart_context() THEN
    RAISE EXCEPTION 'planner inquiry creation context mismatch' USING ERRCODE = '42501';
  END IF;

  -- This transaction-scoped lock makes the quota check and subsequent INSERT
  -- atomic for one principal across every chart and serving instance.
  PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_principal_uid, 0));

  DELETE FROM public.planner_inquiry_lifecycles
   WHERE principal_uid=p_principal_uid AND chart_id=p_chart_id
     AND retention_expires_at <= now();

  SELECT count(*) INTO recent_count
    FROM public.planner_inquiry_lifecycles
   WHERE principal_uid=p_principal_uid
     AND created_at > now() - interval '1 hour';
  IF recent_count >= 32 THEN
    RAISE EXCEPTION 'INQUIRY_CREATION_RATE_LIMITED' USING ERRCODE = 'P0001';
  END IF;

  SELECT count(*) INTO active_count
    FROM public.planner_inquiry_lifecycles
   WHERE principal_uid=p_principal_uid AND chart_id=p_chart_id
     AND status='INCOMPLETE' AND expires_at > now();
  IF active_count >= 8 THEN
    RAISE EXCEPTION 'INQUIRY_ACTIVE_LIMIT_REACHED' USING ERRCODE = 'P0001';
  END IF;

  RETURN QUERY
  INSERT INTO public.planner_inquiry_lifecycles
    (inquiry_id, principal_uid, chart_id, semantic_contract_hash, execution_plan_hash,
     capability_content_hash, capability_compatibility_version, chart_overlay_version,
     chart_build_id, authorization_jsonb, contract_jsonb, status, revision,
     current_jti_hash, expires_at)
  VALUES
    (p_inquiry_id, p_principal_uid, p_chart_id, p_semantic_contract_hash,
     p_execution_plan_hash, p_capability_content_hash,
     p_capability_compatibility_version, p_chart_overlay_version, p_chart_build_id,
     p_authorization_jsonb, p_contract_jsonb, p_status, 0, p_current_jti_hash,
     p_expires_at)
  RETURNING *;
END;
$$;

REVOKE ALL ON FUNCTION create_planner_inquiry_lifecycle(
  uuid, text, uuid, text, text, text, text, text, text, jsonb, jsonb, text, text, timestamptz
) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION create_planner_inquiry_lifecycle(
  uuid, text, uuid, text, text, text, text, text, text, jsonb, jsonb, text, text, timestamptz
) TO role_web_serve;

-- The already-scheduled pending-stream reaper calls this bounded-retention
-- sweep. Expiry is immutable, so exposing only this no-argument deletion to
-- the serving role cannot select a tenant or delete a live lifecycle.
CREATE OR REPLACE FUNCTION purge_expired_planner_inquiries_global()
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  deleted_count integer;
BEGIN
  DELETE FROM planner_inquiry_lifecycles WHERE retention_expires_at <= now();
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$;

REVOKE ALL ON FUNCTION purge_expired_planner_inquiries_global() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION purge_expired_planner_inquiries_global() TO role_web_serve;

ALTER TABLE planner_inquiry_lifecycles ENABLE ROW LEVEL SECURITY;
ALTER TABLE planner_inquiry_evidence_receipts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS planner_inquiry_lifecycles_principal_chart ON planner_inquiry_lifecycles;
CREATE POLICY planner_inquiry_lifecycles_principal_chart
  ON planner_inquiry_lifecycles AS PERMISSIVE FOR ALL TO role_web_serve
  USING (principal_uid = current_setting('app.principal_id', true)
         AND chart_id = app_chart_context())
  WITH CHECK (principal_uid = current_setting('app.principal_id', true)
              AND chart_id = app_chart_context());

DROP POLICY IF EXISTS planner_inquiry_evidence_receipts_principal_chart ON planner_inquiry_evidence_receipts;
CREATE POLICY planner_inquiry_evidence_receipts_principal_chart
  ON planner_inquiry_evidence_receipts AS PERMISSIVE FOR ALL TO role_web_serve
  USING (EXISTS (
    SELECT 1 FROM planner_inquiry_lifecycles lifecycle
    WHERE lifecycle.inquiry_id = planner_inquiry_evidence_receipts.inquiry_id
      AND lifecycle.principal_uid = current_setting('app.principal_id', true)
      AND lifecycle.chart_id = app_chart_context()
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM planner_inquiry_lifecycles lifecycle
    WHERE lifecycle.inquiry_id = planner_inquiry_evidence_receipts.inquiry_id
      AND lifecycle.principal_uid = current_setting('app.principal_id', true)
      AND lifecycle.chart_id = app_chart_context()
  ));

COMMIT;

-- DOWN (manual, destructive; retain/export evidence before use):
-- User/chart archival or early deletion must first export retained evidence.
-- Normal retention purges delete the lifecycle and cascade only its child receipts.
-- DROP FUNCTION IF EXISTS purge_expired_planner_inquiries_global();
-- DROP FUNCTION IF EXISTS create_planner_inquiry_lifecycle(uuid, text, uuid, text, text, text, text, text, text, jsonb, jsonb, text, text, timestamptz);
-- DROP TABLE IF EXISTS planner_inquiry_evidence_receipts;
-- DROP TABLE IF EXISTS planner_inquiry_lifecycles;
-- DROP FUNCTION IF EXISTS planner_inquiry_immutable_guard();

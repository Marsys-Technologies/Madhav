-- Migration 1040: atomic planner inquiry successor lifecycle
-- Created: 2026-09-18
--
-- A continuation is a new signed contract, never a mutation of the parent
-- authorization.  The parent terminal transition and child creation are one
-- transaction so a retry cannot create sibling successors or strand a
-- terminal parent without its approved continuation.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_roles
     WHERE rolname='purna_inquiry_owner'
       AND NOT rolcanlogin AND NOT rolinherit AND NOT rolsuper
       AND NOT rolcreatedb AND NOT rolcreaterole
       AND NOT rolreplication AND NOT rolbypassrls
  ) THEN
    RAISE EXCEPTION 'Purna successor migration requires normalized NOLOGIN purna_inquiry_owner';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_auth_members membership
      JOIN pg_roles owner ON owner.oid=membership.roleid
      JOIN pg_roles actor ON actor.oid=membership.member
     WHERE owner.rolname='purna_inquiry_owner'
       AND actor.rolname=session_user
       AND membership.admin_option
  ) THEN
    RAISE EXCEPTION 'Purna successor migration requires freshly provisioned direct temporary owner membership with admin option';
  END IF;
  IF NOT has_schema_privilege('purna_inquiry_owner', 'public', 'CREATE') THEN
    RAISE EXCEPTION 'Purna successor migration requires temporary owner CREATE on public';
  END IF;
END $$;

SET LOCAL ROLE purna_inquiry_owner;

ALTER TABLE planner_inquiry_lifecycles
  ADD COLUMN IF NOT EXISTS parent_inquiry_id uuid
  REFERENCES planner_inquiry_lifecycles(inquiry_id) ON DELETE RESTRICT;

-- Retain the complete ancestry of a live successor.  Once the successor has
-- expired and been removed, its parent becomes eligible for the next purge.
CREATE OR REPLACE FUNCTION purge_expired_planner_inquiries_global()
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  deleted_count integer;
BEGIN
  DELETE FROM public.planner_inquiry_lifecycles parent
   WHERE parent.retention_expires_at <= now()
     AND NOT EXISTS (
       SELECT 1 FROM public.planner_inquiry_lifecycles child
        WHERE child.parent_inquiry_id=parent.inquiry_id
     );
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$;

CREATE OR REPLACE FUNCTION create_planner_inquiry_successor_lifecycle(
  p_parent_inquiry_id uuid,
  p_principal_uid text,
  p_chart_id uuid,
  p_expected_parent_revision integer,
  p_expected_parent_jti_hash text,
  p_parent_final_contract jsonb,
  p_inquiry_id uuid,
  p_semantic_contract_hash text,
  p_execution_plan_hash text,
  p_capability_content_hash text,
  p_capability_compatibility_version text,
  p_chart_overlay_version text,
  p_chart_build_id text,
  p_authorization_jsonb jsonb,
  p_contract_jsonb jsonb,
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
  parent_row public.planner_inquiry_lifecycles%ROWTYPE;
BEGIN
  IF p_principal_uid IS DISTINCT FROM current_setting('app.principal_id', true)
     OR p_chart_id IS DISTINCT FROM public.app_chart_context()
     OR p_expected_parent_revision < 0
     OR p_parent_final_contract IS NULL OR jsonb_typeof(p_parent_final_contract) <> 'object'
     OR p_authorization_jsonb IS NULL OR jsonb_typeof(p_authorization_jsonb) <> 'object'
     OR p_contract_jsonb IS NULL OR jsonb_typeof(p_contract_jsonb) <> 'object'
     OR p_parent_final_contract->>'status' IS DISTINCT FROM 'BLOCKED'
     OR p_contract_jsonb->>'status' IS DISTINCT FROM 'INCOMPLETE'
     OR p_authorization_jsonb->>'contract_id' IS DISTINCT FROM p_contract_jsonb->>'contract_id'
     OR p_authorization_jsonb->>'semantic_contract_hash' IS DISTINCT FROM p_semantic_contract_hash
     OR p_authorization_jsonb->>'execution_plan_hash' IS DISTINCT FROM p_execution_plan_hash
     OR p_contract_jsonb->>'semantic_contract_hash' IS DISTINCT FROM p_semantic_contract_hash
     OR p_contract_jsonb->>'execution_plan_hash' IS DISTINCT FROM p_execution_plan_hash
     OR p_authorization_jsonb#>>'{successor,parent_inquiry_id}' IS DISTINCT FROM p_parent_inquiry_id::text
     OR p_contract_jsonb#>>'{successor,parent_inquiry_id}' IS DISTINCT FROM p_parent_inquiry_id::text
     OR p_authorization_jsonb#>>'{successor,parent_contract_hash}' IS DISTINCT FROM p_contract_jsonb#>>'{successor,parent_contract_hash}'
     OR p_authorization_jsonb#>>'{successor,parent_execution_plan_hash}' IS DISTINCT FROM p_contract_jsonb#>>'{successor,parent_execution_plan_hash}'
     OR p_authorization_jsonb#>>'{successor,parent_contract_state_hash}' IS DISTINCT FROM p_contract_jsonb#>>'{successor,parent_contract_state_hash}'
     OR p_authorization_jsonb#>'{successor,parent_contract}' IS DISTINCT FROM p_contract_jsonb#>'{successor,parent_contract}'
     OR p_contract_jsonb#>>'{successor,parent_contract_hash}' IS NULL
     OR p_contract_jsonb#>>'{successor,parent_contract_state_hash}' IS NULL THEN
    RAISE EXCEPTION 'planner inquiry successor creation context mismatch' USING ERRCODE = '42501';
  END IF;

  PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_principal_uid, 0));

  SELECT * INTO parent_row
    FROM public.planner_inquiry_lifecycles
   WHERE inquiry_id=p_parent_inquiry_id
     AND principal_uid=p_principal_uid
     AND chart_id=p_chart_id
     AND revision=p_expected_parent_revision
     AND current_jti_hash=p_expected_parent_jti_hash
     AND status='INCOMPLETE'
     AND expires_at > now()
   FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'INQUIRY_TOKEN_REPLAYED_OR_STALE' USING ERRCODE = 'P0001';
  END IF;

  IF p_contract_jsonb#>>'{successor,parent_contract_hash}' IS DISTINCT FROM parent_row.semantic_contract_hash
     OR p_contract_jsonb#>>'{successor,parent_execution_plan_hash}' IS DISTINCT FROM parent_row.execution_plan_hash THEN
    RAISE EXCEPTION 'planner inquiry successor parent authorization mismatch' USING ERRCODE = '42501';
  END IF;
  IF p_contract_jsonb#>'{successor,parent_contract}' IS DISTINCT FROM p_parent_final_contract
     OR (p_parent_final_contract - 'status' - 'status_reasons')
        IS DISTINCT FROM (parent_row.contract_jsonb - 'status' - 'status_reasons')
     OR jsonb_typeof(p_parent_final_contract->'status_reasons') IS DISTINCT FROM 'array'
     OR NOT EXISTS (
       SELECT 1 FROM jsonb_array_elements_text(p_parent_final_contract->'status_reasons') reason
        WHERE reason='evidence-admitted successor issued'
     ) THEN
    RAISE EXCEPTION 'planner inquiry successor parent state mismatch' USING ERRCODE = '42501';
  END IF;

  IF EXISTS (
    SELECT 1 FROM public.planner_inquiry_action_reservations reservation
     WHERE reservation.inquiry_id=parent_row.inquiry_id
       AND reservation.revision=parent_row.revision
       AND reservation.state IN ('reserved', 'dispatched')
  ) THEN
    RAISE EXCEPTION 'INQUIRY_ACTION_IN_PROGRESS' USING ERRCODE = 'P0001';
  END IF;

  UPDATE public.planner_inquiry_lifecycles
     SET contract_jsonb=p_parent_final_contract, status=p_parent_final_contract->>'status',
         revision=revision+1, current_jti_hash='terminal', updated_at=now()
   WHERE inquiry_id=parent_row.inquiry_id AND revision=parent_row.revision
     AND current_jti_hash=p_expected_parent_jti_hash AND status='INCOMPLETE';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'INQUIRY_TOKEN_REPLAYED_OR_STALE' USING ERRCODE = 'P0001';
  END IF;

  SELECT count(*) INTO recent_count
    FROM public.planner_inquiry_lifecycles
   WHERE principal_uid=p_principal_uid AND created_at > now() - interval '1 hour';
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
    (inquiry_id, parent_inquiry_id, principal_uid, chart_id, semantic_contract_hash, execution_plan_hash,
     capability_content_hash, capability_compatibility_version, chart_overlay_version,
     chart_build_id, authorization_jsonb, contract_jsonb, status, revision,
     current_jti_hash, expires_at)
  VALUES
    (p_inquiry_id, p_parent_inquiry_id, p_principal_uid, p_chart_id, p_semantic_contract_hash,
     p_execution_plan_hash, p_capability_content_hash,
     p_capability_compatibility_version, p_chart_overlay_version, p_chart_build_id,
     p_authorization_jsonb, p_contract_jsonb, 'INCOMPLETE', 0, p_current_jti_hash,
     p_expires_at)
  RETURNING *;
END;
$$;

REVOKE ALL ON FUNCTION create_planner_inquiry_successor_lifecycle(
  uuid, text, uuid, integer, text, jsonb, uuid, text, text, text, text, text,
  text, jsonb, jsonb, text, timestamptz
) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION create_planner_inquiry_successor_lifecycle(
  uuid, text, uuid, integer, text, jsonb, uuid, text, text, text, text, text,
  text, jsonb, jsonb, text, timestamptz
) TO role_web_serve;

-- The preflight creates a one-shot direct membership solely so this migration
-- can create protected objects.  Close that edge before migration success;
-- any later protected change requires a newly reviewed preflight.
RESET ROLE;
DO $$
BEGIN
  EXECUTE format('REVOKE purna_inquiry_owner FROM %I', session_user);
  IF EXISTS (
    SELECT 1 FROM pg_auth_members membership
      JOIN pg_roles role ON role.oid=membership.roleid OR role.oid=membership.member
     WHERE role.rolname='purna_inquiry_owner'
  ) THEN
    RAISE EXCEPTION 'Purna successor migration protected-owner membership cleanup did not converge';
  END IF;
END $$;

-- No DOWN migration: removing a lineage primitive can orphan retained evidence.

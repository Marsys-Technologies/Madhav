-- 897_nirmana_evidence_ingress_writer_ga_transit_anchors_grant.sql
--
-- Renumbered from 896 (cycle 224): collided with L2's independently-authored
-- 896_nirmana_l2_bo_sudarshana_output_digest_spec.sql, which merged into main first. This
-- file was already applied live under its original 896 filename before the collision
-- surfaced; disclosed via migration_renumber_disclosed.json (sql_identity unchanged --
-- the RAISE EXCEPTION message text below still literally says "migration 896", left as-is
-- deliberately since editing it would change this file's sql_identity and break the
-- disclosed match).
--
-- NIRMĀṆA — same class of gap as migrations 645/646/885/890: `nirmana_evidence_ingress_writer`
-- never had `SELECT` on `ga_transit_anchors`. Discovered live: `ga_transit_anchors`' first real
-- `integrity_verified` submission (cycle 212, first-ever campaign dispatch for this asset,
-- adjudication #2224/#2317 finally unblocking it) failed with `permission denied for table
-- ga_transit_anchors` (`code: '42501'`, `routine: 'aclcheck_error'`).
--
-- Same additive, existence-checked, SELECT-only pattern as migrations 645/646/885/890.

BEGIN;

DO $$
DECLARE
  relation_name text;
  new_read_relations constant text[] := ARRAY['ga_transit_anchors'];
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 896 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  FOREACH relation_name IN ARRAY new_read_relations LOOP
    IF to_regclass(format('%I.%I', current_schema(), relation_name)) IS NULL THEN
      RAISE EXCEPTION 'migration 896 requires % to already exist', relation_name;
    END IF;
    EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), relation_name);
  END LOOP;

  IF EXISTS (
    SELECT 1 FROM information_schema.role_table_grants
     WHERE grantee = 'nirmana_evidence_ingress_writer'
       AND table_schema = current_schema()
       AND table_name = ANY(new_read_relations)
       AND privilege_type <> 'SELECT'
  ) THEN
    RAISE EXCEPTION 'migration 896 granted more than SELECT on one or more of the new relations';
  END IF;
END;
$$;

COMMIT;

-- Reversal (only before any integrity_verified receipt relies on this grant):
-- REVOKE SELECT ON ga_transit_anchors FROM nirmana_evidence_ingress_writer;

-- Migration 647: grant nirmana_evidence_ingress_writer SELECT on
-- chart_grants -- the one table 645/646's own sweeps both missed.
--
-- Migration 632 (immutable) established nirmana_evidence_ingress_writer as
-- the least-privilege server role backing every layer's integrity_verified
-- submission. Migration 645 added life_events/charts (Nirmana #1869's first
-- finding); migration 646 swept 65 more tables any integrity_check_sql
-- literally names in a FROM/JOIN clause. Neither swept chart_grants,
-- because no check's SQL text references it directly -- but charts has row-
-- level security enabled (chart_grant_policy), and RLS policy evaluation
-- runs under the querying role's own privileges: a plain SELECT that merely
-- joins charts requires SELECT on chart_grants too, to let the role
-- evaluate the RLS predicate, regardless of whether chart_grants is named
-- anywhere in the check's own SQL. Confirmed twice independently on #1869
-- after 645/646 landed -- lel_events and mi_vistara's integrity_verified
-- submissions both failed live with `permission denied for table
-- chart_grants`, same signature, different assets, both already-verified-
-- correct check SQL and preserved digests otherwise ready to resubmit.
--
-- Additive only: does not touch migration 632/645/646's existing grants or
-- any other role's privileges. Idempotent and existence-checked, matching
-- 632/645/646's own pattern.
BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 647 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  IF to_regclass(format('%I.%I', current_schema(), 'chart_grants')) IS NOT NULL THEN
    EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), 'chart_grants');
  END IF;

  -- Verify exactly the intended grant landed -- SELECT only, on exactly
  -- this table, nothing broader (mirrors 632/645/646's own post-grant
  -- assertion style).
  IF EXISTS (
    SELECT 1 FROM information_schema.role_table_grants
     WHERE grantee = 'nirmana_evidence_ingress_writer'
       AND table_schema = current_schema()
       AND table_name = 'chart_grants'
       AND privilege_type <> 'SELECT'
  ) THEN
    RAISE EXCEPTION 'migration 647 granted more than SELECT on chart_grants';
  END IF;

  IF to_regclass(format('%I.%I', current_schema(), 'chart_grants')) IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM information_schema.role_table_grants
     WHERE grantee = 'nirmana_evidence_ingress_writer'
       AND table_schema = current_schema()
       AND table_name = 'chart_grants'
       AND privilege_type = 'SELECT'
  ) THEN
    RAISE EXCEPTION 'migration 647 did not grant SELECT on chart_grants';
  END IF;
END;
$$;

COMMIT;

-- Reversal (only before any integrity_verified receipt relies on this
-- grant): REVOKE SELECT ON chart_grants FROM nirmana_evidence_ingress_writer;

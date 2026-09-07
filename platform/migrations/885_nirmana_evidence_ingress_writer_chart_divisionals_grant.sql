-- 885_nirmana_evidence_ingress_writer_chart_divisionals_grant.sql
--
-- NIRMĀṆA — `nirmana_evidence_ingress_writer` (migration 632, whitelist audited in 646) never
-- had `SELECT` on `chart_divisionals`. Discovered live, not audited in advance: `ga_vargas`'
-- first real `integrity_verified` submission this cycle failed with `permission denied for
-- table chart_divisionals` (`code: '42501'`, `aclcheck_error`) -- migration 646's own audit
-- scanned every `integrity_check_sql` for `FROM`/`JOIN` references at the time it ran, but
-- `ga_vargas`' check either postdates that audit or was edited since (this campaign has
-- already rewritten it twice this cycle, migrations 883/884) without re-running the audit.
--
-- Same additive, existence-checked, SELECT-only pattern as migrations 645/646 -- one missing
-- relation, not a re-audit of the full whitelist (out of scope for a single-asset unblock).

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 885 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  IF to_regclass(format('%I.chart_divisionals', current_schema())) IS NULL THEN
    RAISE EXCEPTION 'migration 885 requires chart_divisionals to already exist';
  END IF;

  EXECUTE format('GRANT SELECT ON TABLE %I.chart_divisionals TO nirmana_evidence_ingress_writer', current_schema());

  IF EXISTS (
    SELECT 1 FROM information_schema.role_table_grants
     WHERE grantee = 'nirmana_evidence_ingress_writer'
       AND table_schema = current_schema()
       AND table_name = 'chart_divisionals'
       AND privilege_type <> 'SELECT'
  ) THEN
    RAISE EXCEPTION 'migration 885 granted more than SELECT on chart_divisionals';
  END IF;
END;
$$;

COMMIT;

-- Reversal (only before any integrity_verified receipt relies on this grant):
-- REVOKE SELECT ON chart_divisionals FROM nirmana_evidence_ingress_writer;

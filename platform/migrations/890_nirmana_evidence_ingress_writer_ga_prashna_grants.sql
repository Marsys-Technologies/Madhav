-- 890_nirmana_evidence_ingress_writer_ga_prashna_grants.sql
--
-- NIRMĀṆA — same class of gap as migration 885 (chart_divisionals): `nirmana_evidence_
-- ingress_writer` never had `SELECT` on `ga_prashna_lagna` or `prashna_charts`. Discovered
-- live: `ga_prashna`'s first real `integrity_verified` submission failed with
-- `permission denied for table ga_prashna_lagna` (`code: '42501'`). Its own integrity_check_sql
-- header says "target: ga_prashna_lagna" -- a DIFFERENT table than `asset_registry.
-- target_table` for this asset (`ga_prashna_judgment`); the check also joins `prashna_charts`.
-- Neither table was ever in migration 646's audited whitelist.
--
-- Same additive, existence-checked, SELECT-only pattern as migrations 645/646/885.

BEGIN;

DO $$
DECLARE
  relation_name text;
  new_read_relations constant text[] := ARRAY['ga_prashna_lagna', 'prashna_charts'];
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 890 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  FOREACH relation_name IN ARRAY new_read_relations LOOP
    IF to_regclass(format('%I.%I', current_schema(), relation_name)) IS NULL THEN
      RAISE EXCEPTION 'migration 890 requires % to already exist', relation_name;
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
    RAISE EXCEPTION 'migration 890 granted more than SELECT on one or more of the new relations';
  END IF;
END;
$$;

COMMIT;

-- Reversal (only before any integrity_verified receipt relies on these grants):
-- REVOKE SELECT ON ga_prashna_lagna, prashna_charts FROM nirmana_evidence_ingress_writer;

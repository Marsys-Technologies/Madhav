-- 903_nirmana_evidence_ingress_writer_l1_frontier_grants.sql
--
-- Migration 903. Authored as 901 in cycle 259 but L3's
-- `901_nirmana_l3_ka_gochara_resonance_output_digest_spec.sql` claimed that number on main —
-- renumbered per MIG-1 (max() across both directories). These GRANTs were already applied
-- live ad-hoc at the tail of cycle 259 (verified: `has_table_privilege` = true for all three
-- relations; `ga_condition`'s `integrity_verified` went through at 20:36:29Z on the strength
-- of the first grant) — this file is the durable, tracked record; re-apply is idempotent.
--
-- NIRMĀṆA — same class of gap as migrations 645/646/885/890/898: the server-side
-- `integrity_verified` re-evaluation runs each asset's `integrity_check_sql` as
-- `nirmana_evidence_ingress_writer`, which never had `SELECT` on the tables the three
-- remaining L1 frontier assets' checks read. Discovered live in cycle 259, immediately after
-- the #2300 / D-NATIVE-10 unblock: `ga_condition`'s first `integrity_verified` submission
-- (build_run 7a6f34fb) failed HTTP 500; `has_table_privilege('nirmana_evidence_ingress_writer',
-- 'ga_condition_composite', 'SELECT')` = false — the exact migration-898 signature (42501,
-- aclcheck_error, cycle 212). Probed the whole remaining frontier's check-read tables in the
-- same pass rather than rediscovering this one asset at a time:
--   ga_condition  → ga_condition_composite            (missing)
--   ga_tajaka     → l1_tajik_varsha_year_lords        (missing)
--   ga_structural → chart_facts (granted), chart_divisionals (granted),
--                   ga_yoga_firings                   (missing)
--
-- Same additive, existence-checked, SELECT-only pattern as migration 898.

BEGIN;

DO $$
DECLARE
  relation_name text;
  new_read_relations constant text[] := ARRAY[
    'ga_condition_composite',
    'l1_tajik_varsha_year_lords',
    'ga_yoga_firings'
  ];
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 903 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  FOREACH relation_name IN ARRAY new_read_relations LOOP
    IF to_regclass(format('%I.%I', current_schema(), relation_name)) IS NULL THEN
      RAISE EXCEPTION 'migration 903 requires % to already exist', relation_name;
    END IF;
    EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), relation_name);
  END LOOP;
END $$;

COMMIT;

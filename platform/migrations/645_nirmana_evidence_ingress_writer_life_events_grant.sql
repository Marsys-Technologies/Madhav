-- Migration 645: grant nirmana_evidence_ingress_writer SELECT on life_events
-- and charts -- the two tables lel_events's integrity_check_sql reads.
--
-- Migration 632 (immutable) established this role as a least-privilege,
-- explicit-whitelist read login for server-reconstructed Nirmana evidence
-- (integrity_verified / asset_frozen / probe_accepted), granting SELECT on a
-- curated detector_read_relations set -- deliberately explicit rather than
-- inferred, per its own comment: "any future detector relation needs a
-- reviewed migration addition before an ingress receipt can be earned."
-- lel_events's integrity_check_sql (a LEFT JOIN over life_events and charts,
-- neither of which is any layer's own target_table) was not in that original
-- set, so its first real integrity_verified submission failed HTTP 500 /
-- permission denied for table life_events (Nirmana #1869).
--
-- Additive only: does not touch migration 632's REVOKE-then-GRANT sequence
-- (already applied, immutable per S N.4), does not alter any other grant.
-- Idempotent and existence-checked, matching 632's own pattern exactly.
BEGIN;

DO $$
DECLARE
  relation_name text;
  new_read_relations constant text[] := ARRAY['life_events', 'charts'];
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 645 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  FOREACH relation_name IN ARRAY new_read_relations LOOP
    IF to_regclass(format('%I.%I', current_schema(), relation_name)) IS NOT NULL THEN
      EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), relation_name);
    END IF;
  END LOOP;

  -- Verify exactly the intended grants landed -- SELECT only, on exactly these
  -- two tables, nothing broader (mirrors 632's own post-grant assertion style).
  IF EXISTS (
    SELECT 1 FROM information_schema.role_table_grants
     WHERE grantee = 'nirmana_evidence_ingress_writer'
       AND table_schema = current_schema()
       AND table_name = ANY(new_read_relations)
       AND privilege_type <> 'SELECT'
  ) THEN
    RAISE EXCEPTION 'migration 645 granted more than SELECT on life_events/charts';
  END IF;
  IF (
    SELECT count(DISTINCT table_name) FROM information_schema.role_table_grants
     WHERE grantee = 'nirmana_evidence_ingress_writer'
       AND table_schema = current_schema()
       AND table_name = ANY(new_read_relations)
       AND privilege_type = 'SELECT'
  ) <> (
    SELECT count(*) FROM unnest(new_read_relations) AS rel
     WHERE to_regclass(format('%I.%I', current_schema(), rel)) IS NOT NULL
  ) THEN
    RAISE EXCEPTION 'migration 645 did not grant SELECT on every existing target relation';
  END IF;
END;
$$;

COMMIT;

-- Reversal (only before any integrity_verified receipt relies on this grant):
-- REVOKE SELECT ON life_events, charts FROM nirmana_evidence_ingress_writer;

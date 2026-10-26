-- 1411_gochara_verifier_closure_grants.sql
--
-- SR-W4-VERIFIER-GRANTS (owner surrogate, 2026-10-26). Allocated to that item in /Users/Dev/kalayantra/run/MIGRATION_ALLOCATION.json
-- (branch kalayantra/verifier-closure-grants). Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here).
--
-- WHAT IT ADDS: SELECT for role gochara_verifier on exactly the ELEVEN public tables the verification job's import closure reads and the role
-- could not read. NOTHING ELSE: no table, column, function, trigger or row is created or touched; no applied migration is edited; no write
-- privilege is granted; ka_gochara_seal_approval (not read by the verifier) is NOT granted.
--
-- WHY. The first W4 report-only verification execution (gochara-verification-job-zfrfg, 2026-10-26T08:50Z) exited 5 after 15 s:
-- "InsufficientPrivilege: permission denied for table bg_combustion_orbs". A production readback of every relation named in the verifier's
-- import closure (pipeline/orchestrator/verification_job.py and the services/gochara_kernel modules it imports; 43 relations) found these
-- eleven without SELECT for gochara_verifier; the other 32 were already granted. The window_qualification/1 verification path that reads
-- them post-dates the last live verifier run (2026-10-22). Readers per table (closure module):
--   _migrations_applied               seal_brief (the brief records the migration ledger)
--   bg_combustion_orbs, bg_dignity_reference, bg_graha_naisargika_friendship   p1_operands / p1_operands_check / input_vector(_verifier)
--   bg_transit_rules                  vedha_verifier / input_vector(_verifier) / ledger
--   ephemeris_daily                   knots
--   ka_gochara_contact_identity       record_store
--   ka_gochara_sky_event              window_verifier / near_miss_verifier / record_store / substrate
--   kala_gochara_authority, kala_gochara_convention   ledger
--   kala_gochara_windows              ledger / candidate_boundary
-- The guard test platform/python-sidecar/tests/l3/gochara/test_verifier_closure_grants.py fails when a relation the closure reads is
-- neither in the measured pre-1411 grant set nor in this migration's list.
--
-- ROLE ABSENT (fresh or test databases): NO grant is issued and a NOTICE names the role — never a grant to nobody passed off as done.
-- ROUTE: table-level GRANTs only (no CREATE, no GRANT ON SCHEMA) — a routine migration.
-- IDEMPOTENT: GRANT of a held privilege is a no-op. FAIL-CLOSED: refuses when a listed table is missing; the post-apply block raises unless
-- every listed table carries an explicit ACL SELECT entry for gochara_verifier from another role (ownership never counts).
-- ROLLBACK: REVOKE SELECT ON <the eleven tables> FROM gochara_verifier; the verification job then fails by name (InsufficientPrivilege).

SET LOCAL lock_timeout = '5s';

-- ── 0. Prerequisites (fail-closed) ───────────────────────────────────────────
DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(x.name, ', ' ORDER BY x.name) INTO missing
  FROM (VALUES ('public._migrations_applied'), ('public.bg_combustion_orbs'), ('public.bg_dignity_reference'),
               ('public.bg_graha_naisargika_friendship'), ('public.bg_transit_rules'), ('public.ephemeris_daily'),
               ('public.ka_gochara_contact_identity'), ('public.ka_gochara_sky_event'), ('public.kala_gochara_authority'),
               ('public.kala_gochara_convention'), ('public.kala_gochara_windows')) AS x(name)
  WHERE to_regclass(x.name) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1411: prerequisite table(s) missing: %', missing;
  END IF;
END;
$$;

-- ── 1. Grants (to the role only if it exists) ────────────────────────────────
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier') THEN
    GRANT SELECT ON public._migrations_applied TO gochara_verifier;
    GRANT SELECT ON public.bg_combustion_orbs TO gochara_verifier;
    GRANT SELECT ON public.bg_dignity_reference TO gochara_verifier;
    GRANT SELECT ON public.bg_graha_naisargika_friendship TO gochara_verifier;
    GRANT SELECT ON public.bg_transit_rules TO gochara_verifier;
    GRANT SELECT ON public.ephemeris_daily TO gochara_verifier;
    GRANT SELECT ON public.ka_gochara_contact_identity TO gochara_verifier;
    GRANT SELECT ON public.ka_gochara_sky_event TO gochara_verifier;
    GRANT SELECT ON public.kala_gochara_authority TO gochara_verifier;
    GRANT SELECT ON public.kala_gochara_convention TO gochara_verifier;
    GRANT SELECT ON public.kala_gochara_windows TO gochara_verifier;
    RAISE NOTICE 'migration 1411: SELECT granted to gochara_verifier on 11 tables';
  ELSE
    RAISE NOTICE 'migration 1411: role gochara_verifier NOT FOUND — NO grant was issued; the verification job cannot read its closure until it is provisioned and granted';
  END IF;
END;
$$;

-- ── 2. Post-apply measurement (explicit ACL entries only) ────────────────────
DO $$
DECLARE missing text;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier') THEN
    RAISE NOTICE 'migration 1411 post-apply: role gochara_verifier absent — nothing to measure';
    RETURN;
  END IF;
  SELECT string_agg(x.name, ', ' ORDER BY x.name) INTO missing
  FROM (VALUES ('public._migrations_applied'), ('public.bg_combustion_orbs'), ('public.bg_dignity_reference'),
               ('public.bg_graha_naisargika_friendship'), ('public.bg_transit_rules'), ('public.ephemeris_daily'),
               ('public.ka_gochara_contact_identity'), ('public.ka_gochara_sky_event'), ('public.kala_gochara_authority'),
               ('public.kala_gochara_convention'), ('public.kala_gochara_windows')) AS x(name)
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_class c, LATERAL aclexplode(c.relacl) a
    WHERE c.oid = to_regclass(x.name) AND a.grantee = 'gochara_verifier'::regrole::oid AND a.privilege_type = 'SELECT' AND a.grantor <> a.grantee);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1411 post-apply check failed: gochara_verifier has no explicit ACL grant of SELECT on: % (a privilege from ownership or PUBLIC does not count)', missing;
  END IF;
  RAISE NOTICE 'migration 1411: gochara_verifier holds an explicit SELECT grant on all 11 tables';
END;
$$;

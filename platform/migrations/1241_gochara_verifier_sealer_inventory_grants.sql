-- Migration 1241: grant the VERIFIER and the SEALER the privileges the INVENTORY side of the seal needs — grants only, role-existence-guarded.
-- Pravāha B6.0, Codex round 9 R9-6 (steward M20261002T062613-6d61, T075234-8e98), 2026-10-02. Author: pravaha stream B. STATUS: DRAFT, HOLD.
-- GRANTS ONLY — creates no object, replaces no function, edits no applied migration, REVOKES nothing (PC-4 — the builder's 1206 §7 grant on
-- ka_gochara_search_inventory_verification — is removed AT SOURCE by the stacked edit to 1206 itself, PR #2934, if the native chooses ND-ROLES
-- option A; this file therefore carries no REVOKE and no closed-execution-interval assumption).
--
-- WHY THIS NUMBER, AND WHEN IT RUNS
-- ═════════════════════════════════
-- It MUST be numbered above 1240: it references objects 1206 and 1240 create, and any number BELOW 1240 would be an unapplied routine predecessor
-- of the protected window (`migrate.ts --only` refuses unselected, unapplied files below its ceiling). It is a ROUTINE migration (the owner grants on
-- existing objects; nothing is created in schema public), applied by the ordinary deploy AFTER the protected window has applied 1204/1206/1232/
-- 1233/1240 — the routine runner refuses LOUDLY at the first pending protected file, so merging this file before the window would block routine
-- deploys; MERGE IT AFTER THE WINDOW. Until it runs the verifier and the sealer hold only what 1240 itself gave them (its own window-verification
-- table and reads); the candidate gate stays CLOSED and no seal is possible — the safe state.
--
-- WHAT 1240 ALREADY GIVES (not repeated here): the verifier INSERT/SELECT/DELETE on ka_gochara_eval_window_verification and SELECT on the window,
-- record, contact, coverage, pin, snapshot, seal, rule-path and publication tables; EXECUTE on lock_chart, lock_global_shared, generation_is_sealed,
-- generation_governed and the window digest functions; the sealer's SELECT on the window-verification table. What it does NOT give — because 1206's
-- inventory verification, the Moon-scope domain (1232) and the legacy ledger reads are 1206/1232/1081 objects — is below.
--
-- DERIVATION (the 1206-R6 method; the composed rehearsal is the detector)
-- ═══════════════════════════════════════════════════════════════════════
-- `tests/l3/gochara/test_b6_composed_seal_flows.py` (integration branch): the REAL production-ordered stack on PostgreSQL 15 (earlier window 1081,
-- 1152–1157; routine 1216, 1220, 1234, 1236, 1242; window 1204, 1206 + PC-4, 1232, 1233, 1240), every object owned by amjis_app, PUBLIC EXECUTE
-- revoked, the verifier and sealer as separate NOLOGIN principals, BOTH seal triggers (1206's and 1240's) ENABLED, the real Swiss ephemeris. The
-- flows (a restricted-builder build; the verifier's window verifications then inventory verification, twice; the sealer's first seal; a
-- generation sealed between 1206 and 1240; builder/sealer contention) were run adding one grant per `permission denied` until they converged, and
-- then EACH grant was individually removed and the first-seal and re-verification flows re-run: a grant that does not make a flow fail is NOT
-- here. Of the 53 candidates the earlier role suites and the derivation produced, 18 are left out: 13 are ALREADY held through 1240 and the
-- earlier migrations (the sealer's SELECT on the seal, publication, record, window, membership, snapshot and pin tables and EXECUTE on
-- lock_chart, lock_global_shared, sha256_hex, canonical_json; the verifier's EXECUTE on lock_chart and generation_is_sealed), and 5 are needed by
-- NO flow (the verifier's DELETE on the inventory-verification table — a re-run REPLACES without it — and its SELECT on the search-interval table, which
-- Stream A's real job never reads as the verifier; the sealer's SELECT on the polarity declaration and EXECUTE on av_entry and inventories_digest). NOTE the correction the REPLAY flow forced: a first-seal-only sweep had counted
-- ka_gochara_search_replay_violations among the unneeded; replaying an EXISTING seal (ka_gochara_seal_generation inserts ON CONFLICT DO NOTHING; 1206's
-- BEFORE trigger fires first) calls it as the sealer, so it is granted — the necessity tests now run first seal AND replay.
--
-- THE GRANTS
-- ══════════
-- VERIFIER (gochara_verifier)
--   SELECT, INSERT   ka_gochara_search_inventory_verification   the inventory verification row (the writer's `verify:<class>` step, run by the
--                                                               verification RUNNER under this identity, R9-6.1)
--   SELECT           ka_gochara_sky_convention, ka_gochara_rule_path_prerequisite, ka_gochara_predicate,
--                    ka_gochara_search_obligation                                    reads of the independent re-derivation
--                    (ka_gochara_search_interval is NOT granted: Stream A's REAL job never reads it as the verifier — measured; an earlier
--                    hand-written verifier needed it, which is why it appeared in the first derivation)
--   EXECUTE          ka_gochara_window_verification_violations(uuid,text)            the candidate gate the `verify:` step runs first
--   (NO DELETE: a re-run replaces the row without it — measured. NO UPDATE, NO seal, NO build-data write.)
-- SEALER (gochara_sealer)
--   INSERT           ka_gochara_generation_seal                  the seal row; UPDATE kala_gochara_publication — the publication flip
--   SELECT           kala_gochara_coverage, kala_gochara_contacts, ka_gochara_rule_path_seal, ka_gochara_convention_bridge,
--                    ka_gochara_search_inventory, ka_gochara_search_obligation, ka_gochara_search_interval,
--                    ka_gochara_search_inventory_verification                          what the seal-side checks read as the invoker
--   EXECUTE          ka_gochara_seal_generation, ka_gochara_coverage_drift, ka_gochara_horizon_finite_ok, ka_gochara_coverage_facts,
--                    ka_gochara_facts_horizon, ka_gochara_membership_violations, ka_gochara_membership_violation,
--                    ka_gochara_search_completeness_violations, ka_gochara_search_replay_violations (the REPLAY of an existing seal),
--                    ka_gochara_search_l1_facts_digest, ka_gochara_search_dasha_digest,
--                    ka_gochara_search_inventory_digest, ka_gochara_search_ledger_digest, ka_gochara_search_inventory_preimage,
--                    ka_gochara_utc_ts, ka_gochara_search_moon_scope_violations, ka_gochara_search_moon_resolved_domain,
--                    ka_gochara_generation_governed
--
-- NOT HERE, ON PURPOSE — an OPEN item for the owner of the data-plane ACLs (NOT granted by this file): both principals ALSO need SELECT on the L1
-- tables `chart_facts` and `chart_dashas` (the independent derivations and the seal's L1/daśā digests read them as the invoker — measured: the flows
-- fail without it). Those tables' ACLs are managed by `platform/scripts/data-plane-ownership-preflight.ts` (L1_ACTIVE_TABLES; ownership by
-- data_plane_l1_owner); a hand grant here risks that script's allowlist-drift/ACL checks, so it is NOT made by a Gochara migration. It must be
-- provisioned by the data-plane owner (or added to that script's grantee set) BEFORE the first verification run.
--
-- ROLE GUARD AND RECEIPT: the roles are created by an admin act that may run before or after this file. For each principal found the grants are
-- issued and a NOTICE says so; for a principal NOT found a WARNING says NO grant was issued to it (a grants migration that silently granted to
-- nobody is the standing hazard, CLAUDE.md §N.4). The final post-check PRINTS which principals were found, verifies every grant for each found
-- principal, and verifies that NEITHER holds anything it must not (no UPDATE/DELETE on build data, no write on the verification-of-the-window
-- table beyond 1240's, no seal for the verifier, no verification write for the sealer). If the roles are created later, the grants are applied by a
-- follow-up routine migration carrying these same statements (the operator's receipt is the printed line).
-- Idempotent. ROLLBACK: REVOKE the same grants.
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
BEGIN
  IF to_regclass('public.ka_gochara_eval_window_verification') IS NULL
     OR to_regclass('public.ka_gochara_search_inventory_verification') IS NULL
     OR to_regclass('public.ka_gochara_generation_seal') IS NULL THEN
    RAISE EXCEPTION 'migration 1241: the protected window (1206, 1240) has not been applied — refusing; apply the window first';
  END IF;
END;
$$;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier') THEN
    GRANT SELECT, INSERT ON public.ka_gochara_search_inventory_verification TO gochara_verifier;
    GRANT SELECT ON public.ka_gochara_sky_convention, public.ka_gochara_rule_path_prerequisite, public.ka_gochara_predicate,
      public.ka_gochara_search_obligation TO gochara_verifier;
    GRANT EXECUTE ON FUNCTION public.ka_gochara_window_verification_violations(uuid, text) TO gochara_verifier;
    RAISE NOTICE 'migration 1241: grants issued to role gochara_verifier';
  ELSE
    RAISE WARNING 'migration 1241: role gochara_verifier NOT FOUND — NO grant was issued to it; it cannot persist an inventory verification until a follow-up grants migration runs';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_sealer') THEN
    GRANT INSERT ON public.ka_gochara_generation_seal TO gochara_sealer;
    GRANT UPDATE ON public.kala_gochara_publication TO gochara_sealer;
    GRANT SELECT ON public.kala_gochara_coverage, public.kala_gochara_contacts, public.ka_gochara_rule_path_seal,
      public.ka_gochara_convention_bridge, public.ka_gochara_search_inventory, public.ka_gochara_search_obligation,
      public.ka_gochara_search_interval, public.ka_gochara_search_inventory_verification TO gochara_sealer;
    GRANT EXECUTE ON FUNCTION
      public.ka_gochara_seal_generation(uuid, text), public.ka_gochara_coverage_drift(uuid, text),
      public.ka_gochara_horizon_finite_ok(tstzrange), public.ka_gochara_coverage_facts(text, tstzrange, text[]),
      public.ka_gochara_facts_horizon(jsonb), public.ka_gochara_membership_violations(uuid, text),
      public.ka_gochara_membership_violation(jsonb, uuid, text, jsonb, tstzrange[]),
      public.ka_gochara_search_completeness_violations(uuid, text), public.ka_gochara_search_replay_violations(uuid, text),
      public.ka_gochara_search_l1_facts_digest(uuid, text[]),
      public.ka_gochara_search_dasha_digest(uuid, uuid[]), public.ka_gochara_search_inventory_digest(uuid, text, text),
      public.ka_gochara_search_ledger_digest(uuid, text, text), public.ka_gochara_search_inventory_preimage(uuid, text, text),
      public.ka_gochara_utc_ts(timestamptz), public.ka_gochara_search_moon_scope_violations(uuid, text),
      public.ka_gochara_search_moon_resolved_domain(uuid, text, text, uuid), public.ka_gochara_generation_governed(text)
      TO gochara_sealer;
    RAISE NOTICE 'migration 1241: grants issued to role gochara_sealer';
  ELSE
    RAISE WARNING 'migration 1241: role gochara_sealer NOT FOUND — NO grant was issued to it; it cannot seal until a follow-up grants migration runs';
  END IF;
END;
$$;

-- Post-check: PRINT which principals were found, verify every grant for each, and refuse extras.
DO $$
DECLARE v boolean := EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier');
        s boolean := EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_sealer');
BEGIN
  RAISE NOTICE 'migration 1241 principals found: gochara_verifier=%, gochara_sealer=%', v, s;
  IF v THEN
    IF NOT (has_table_privilege('gochara_verifier', 'public.ka_gochara_search_inventory_verification', 'INSERT')
            AND has_table_privilege('gochara_verifier', 'public.ka_gochara_search_inventory_verification', 'SELECT')
            AND has_table_privilege('gochara_verifier', 'public.ka_gochara_sky_convention', 'SELECT')
            AND has_table_privilege('gochara_verifier', 'public.ka_gochara_rule_path_prerequisite', 'SELECT')
            AND has_table_privilege('gochara_verifier', 'public.ka_gochara_predicate', 'SELECT')
            AND has_table_privilege('gochara_verifier', 'public.ka_gochara_search_obligation', 'SELECT')
            AND has_function_privilege('gochara_verifier', 'public.ka_gochara_window_verification_violations(uuid, text)', 'EXECUTE')) THEN
      RAISE EXCEPTION 'migration 1241 post-apply check failed: gochara_verifier does not hold the inventory-verification privileges';
    END IF;
    IF has_table_privilege('gochara_verifier', 'public.ka_gochara_search_inventory_verification', 'UPDATE')
       OR has_table_privilege('gochara_verifier', 'public.ka_gochara_generation_seal', 'INSERT')
       OR has_table_privilege('gochara_verifier', 'public.kala_gochara_publication', 'UPDATE')
       OR has_table_privilege('gochara_verifier', 'public.ka_gochara_relationship_record', 'INSERT')
       OR has_table_privilege('gochara_verifier', 'public.ka_gochara_eval_window', 'INSERT')
       OR has_function_privilege('gochara_verifier', 'public.ka_gochara_seal_generation(uuid, text)', 'EXECUTE') THEN
      RAISE EXCEPTION 'migration 1241 post-apply check failed: gochara_verifier holds a privilege beyond verification (a seal, a publication update or a build-data write)';
    END IF;
  END IF;
  IF s THEN
    IF NOT (has_table_privilege('gochara_sealer', 'public.ka_gochara_generation_seal', 'INSERT')
            AND has_table_privilege('gochara_sealer', 'public.kala_gochara_publication', 'UPDATE')
            AND has_table_privilege('gochara_sealer', 'public.kala_gochara_coverage', 'SELECT')
            AND has_table_privilege('gochara_sealer', 'public.kala_gochara_contacts', 'SELECT')
            AND has_table_privilege('gochara_sealer', 'public.ka_gochara_search_inventory', 'SELECT')
            AND has_table_privilege('gochara_sealer', 'public.ka_gochara_search_inventory_verification', 'SELECT')
            AND has_function_privilege('gochara_sealer', 'public.ka_gochara_seal_generation(uuid, text)', 'EXECUTE')
            AND has_function_privilege('gochara_sealer', 'public.ka_gochara_search_completeness_violations(uuid, text)', 'EXECUTE')) THEN
      RAISE EXCEPTION 'migration 1241 post-apply check failed: gochara_sealer does not hold the seal privileges';
    END IF;
    IF has_table_privilege('gochara_sealer', 'public.ka_gochara_search_inventory_verification', 'INSERT')
       OR has_table_privilege('gochara_sealer', 'public.ka_gochara_eval_window_verification', 'INSERT')
       OR has_table_privilege('gochara_sealer', 'public.ka_gochara_relationship_record', 'INSERT')
       OR has_table_privilege('gochara_sealer', 'public.ka_gochara_eval_window', 'INSERT')
       OR has_table_privilege('gochara_sealer', 'public.ka_gochara_relationship_record', 'DELETE') THEN
      RAISE EXCEPTION 'migration 1241 post-apply check failed: gochara_sealer holds a content-write privilege (the sealer reads and seals; it never writes build or verification data)';
    END IF;
  END IF;
END;
$$;

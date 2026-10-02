-- Migration 1234: grant data_plane_builder the EVAL-WINDOW write path — two tables and three functions, nothing else.
-- Pravāha B6.0, Codex round 8 R8-10 (steward M20261002T032818-fea8) + Stream A's derived set (relay M20261002T034924-82ce), 2026-10-02.
-- Author: pravaha stream B. STATUS: HOLD. GRANTS ONLY — creates no object, replaces no function, edits no applied migration.
--
-- WHY THIS EXISTS (the gap 1216 deferred and 1220 does not cover)
-- ═══════════════════════════════════════════════════════════════
-- 1216 states it plainly: "DEFERRED — no write path exists yet, so no grant: ka_gochara_eval_window, ka_gochara_eval_window_record
-- (interval sweep persistence lands with A5.3's writerbase conformance)". 1220 grants EXECUTE for the contact/record writer flow and
-- says it is a narrower flow. Stream A's window writer (substep 'window:<class>:<path>') now exists, and as data_plane_builder it stops
-- at 'permission denied for table ka_gochara_eval_window' at its first INSERT, and — once the table grants exist — at
-- 'permission denied for function …' from the invoker-security guards and CHECK predicates the 1156 tables carry. Production default
-- privileges revoke PUBLIC EXECUTE on everything amjis_app creates (nirmana-evidence-ownership-preflight.ts:259), so TABLE grants alone
-- never suffice.
--
-- DERIVATION (the 1206-R6 method — the live suite is the detector)
-- ═════════════════════════════════════════════════════════════════
-- 1. Stream A's instrumented run of the real writer listed 22 statements: INSERT / DELETE on ka_gochara_eval_window, INSERT on
--    ka_gochara_eval_window_record, and reads of eleven other relations. Read-only production check (2026-10-02): the builder
--    ALREADY holds SELECT on every one of those reads (relationship_record, contact, physical_object, kala_gochara_coverage,
--    rule_path_soft_factor, factor, sky_event, publication, rule_path, rule_path_prerequisite, rule_path_seal, predicate,
--    sky_convention, chart_facts, chart_dashas, bg_transit_rules) and EXECUTE on ka_gochara_lock_chart,
--    ka_gochara_generation_is_sealed and ka_gochara_coverage_facts (1220). The search-snapshot read and the two SQL-derivation
--    functions (ka_gochara_canonical_json, ka_gochara_sha256_hex) arrive with 1206 §7. So only the window tables and the functions
--    below are missing.
-- 2. The writer's statements were then run AS data_plane_builder under a deployment-faithful role mirror (objects owned by amjis_app,
--    PUBLIC EXECUTE revoked) after 1216 + 1220, adding one grant per 'permission denied …' until the path converged. It converged on
--    EXACTLY the three functions below (the static prediction from 1156's guard bodies named the same three) and the two tables.
-- 3. tests/integration/gochara_b6_1234_eval_window_builder_grants.db.test.ts re-proves that EACH grant is individually necessary
--    (revoking any one breaks the writer path) and that nothing else is granted.
--
-- THE GRANTS, each tied to a reachable call
-- ═════════════════════════════════════════
--   ka_gochara_eval_window         SELECT, INSERT, DELETE   INSERT: the window row. DELETE ... WHERE (chart, generation, class, path,
--                                  version): the delete-then-insert replace of a grain (CLAUDE.md §N.3). SELECT: a DELETE with a
--                                  WHERE clause reads the columns it filters on. NO UPDATE, NO TRUNCATE.
--   ka_gochara_eval_window_record  SELECT, INSERT           INSERT: membership rows. NO DELETE: membership removal rides the window's
--                                  ON DELETE CASCADE (1156 kgewr_window_fk / kgewr_record_fk) — measured: the replace works without a
--                                  DELETE grant here, and a direct DELETE by the builder is refused. SELECT: not needed by the database
--                                  guards (measured) but by the WRITER's read-back of the pairs it just wrote
--                                  (window_store.py:212/224 at the A5.3 writer head) — granted for that, stated plainly.
--   ka_gochara_text_array_ok(text[],integer)   CHECK predicate evaluated as the INVOKER on every window INSERT (null_states_used).
--   ka_gochara_facts_horizon(jsonb)            called by the window coverage guard (ka_gochara_window_coverage_guard) as the invoker.
--   ka_gochara_membership_violation(jsonb,uuid,text,jsonb,tstzrange[])   called by the membership guard
--                                  (ka_gochara_window_membership_guard) as the invoker on every membership INSERT.
-- NOT granted (by design): the seal-side functions ka_gochara_membership_violations(uuid,text) and ka_gochara_coverage_drift(uuid,text)
-- (the sealing principal's), and the guard TRIGGER functions (a trigger function needs no EXECUTE to fire — 1220's reasoning).
-- Not touched: the verification table of 1240 (written by the verifier role only), the inventory-verification privilege of the builder
-- (1206 §7 — PC-4, a separate decision).
--
-- ROUTE / WINDOW: like 1216 and 1220 this is a ROUTINE migration (the owner grants on existing objects; no object is created in schema
-- public), so it is NOT in PROTECTED_PUBLIC_SCHEMA_MIGRATIONS. LEDGER PRECONDITION (rehearsal plan): the protected window's single
-- `migrate.ts --only` invocation refuses every unselected, unapplied file whose number is <= the highest selected number — so 1234 (and
-- 1230) must be APPLIED by the routine deploy BEFORE the window lists anything numbered >= 1234 (the window's ceiling becomes 1240).
-- Idempotent: GRANT of an already-held privilege is a no-op. ROLLBACK: REVOKE the same grants.
-- ─────────────────────────────────────────────────────────────────────────────

GRANT SELECT, INSERT, DELETE ON public.ka_gochara_eval_window TO data_plane_builder;
GRANT SELECT, INSERT ON public.ka_gochara_eval_window_record TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_text_array_ok(text[], integer) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_facts_horizon(jsonb) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.ka_gochara_membership_violation(jsonb, uuid, text, jsonb, tstzrange[]) TO data_plane_builder;

-- Presence check: verify the grants are ACTUALLY held (a grants-only migration that silently granted nothing is the hazard — §N.4).
DO $$
BEGIN
  IF NOT (has_table_privilege('data_plane_builder', 'public.ka_gochara_eval_window', 'SELECT')
          AND has_table_privilege('data_plane_builder', 'public.ka_gochara_eval_window', 'INSERT')
          AND has_table_privilege('data_plane_builder', 'public.ka_gochara_eval_window', 'DELETE')
          AND has_table_privilege('data_plane_builder', 'public.ka_gochara_eval_window_record', 'SELECT')
          AND has_table_privilege('data_plane_builder', 'public.ka_gochara_eval_window_record', 'INSERT')) THEN
    RAISE EXCEPTION 'migration 1234 post-apply check failed: the builder does not hold the window table privileges';
  END IF;
  IF has_table_privilege('data_plane_builder', 'public.ka_gochara_eval_window', 'UPDATE')
     OR has_table_privilege('data_plane_builder', 'public.ka_gochara_eval_window_record', 'DELETE')
     OR has_table_privilege('data_plane_builder', 'public.ka_gochara_eval_window_record', 'UPDATE') THEN
    RAISE EXCEPTION 'migration 1234 post-apply check failed: the builder holds a window privilege beyond the derived set';
  END IF;
  IF NOT (has_function_privilege('data_plane_builder', 'public.ka_gochara_text_array_ok(text[], integer)', 'EXECUTE')
          AND has_function_privilege('data_plane_builder', 'public.ka_gochara_facts_horizon(jsonb)', 'EXECUTE')
          AND has_function_privilege('data_plane_builder', 'public.ka_gochara_membership_violation(jsonb, uuid, text, jsonb, tstzrange[])', 'EXECUTE')) THEN
    RAISE EXCEPTION 'migration 1234 post-apply check failed: the builder does not hold the three window functions';
  END IF;
  RAISE NOTICE 'migration 1234: presence checks passed';
END;
$$;

-- Migration 1241: ONE reviewed, additive grants migration for the VERIFIER and the SEALER — it BACKFILLS 1240's role-conditional grants AND carries
-- the inventory/publication/seal-side grants of its own. Grants only, role-existence-guarded, idempotent, closed by an exact ACL check.
-- Pravāha B6.0, Codex rounds 9 (R9-6) and 10 (R10-7); steward M20261002T062613-6d61, T075234-8e98, T111719-1bb1. Author: pravaha stream B.
-- STATUS: DRAFT, HOLD. Creates no object, replaces no function, edits no applied migration, REVOKES nothing (PC-4 — the builder's 1206 §7 grant on
-- ka_gochara_search_inventory_verification — is removed AT SOURCE by the edit to 1206 itself, folded into #2867).
--
-- WHY IT CARRIES 1240's GRANTS TOO (R10-7 i — a role absent when 1240 ran; Codex round 11: comments corrected)
-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
-- 1240 grants to gochara_verifier / gochara_sealer only IF those roles exist when it is applied, and prints a NOTICE otherwise — a migration runs once, so a
-- role that is ABSENT at that moment never receives 1240's grants from 1240. The delegated sequence creates the two roles IMMEDIATELY BEFORE the protected window
-- (runbooks/ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md: acts 1 and 2a precede act 9), so in the intended order 1240's guarded grants FIRE and this file is the
-- complete additive specification applied afterwards (a backfill for any grant 1240 did not make, and the exact-ACL closure over everything). It also covers the
-- other order — a role created AFTER the window: this file carries the UNION (every privilege 1240 would have granted, origin "1240" in the spec, and every
-- privilege 1241 adds, origin "1241"), so ONE application after the roles exist yields the complete, closed set. Applying it when a role already held 1240's grants
-- is a no-op for those. IF THIS FILE ITSELF RUNS WHILE A ROLE IS ABSENT, its WARNING creates NO deferred grant: an additive follow-up migration carrying the SAME
-- spec is then required once the role exists. It also backfills the one builder grant 1240 makes conditionally (EXECUTE on the window CHECK helper), harmlessly if already held.
-- TESTS (composed rehearsal): (i) the intended order — roles exist → window applied (1240's guarded grants fire) → this file applied → verification job + seal work;
-- (ii) the other order — roles absent at the window → role created → this file applied → verification job + seal work.
--
-- WHY THIS NUMBER, AND WHEN IT RUNS
-- ═════════════════════════════════
-- Above 1240 (a lower number would be an unapplied routine predecessor of the window); a ROUTINE migration (grants on existing objects, nothing created
-- in schema public), applied by the ordinary deploy AFTER the window — the routine runner refuses loudly at the first pending protected file, so MERGE IT
-- AFTER THE WINDOW. It refuses to apply if the window's objects are missing. Until it runs the principals hold nothing; the gate stays CLOSED.
--
-- THE SPEC (the single source: the GRANT statements and the closure check are both driven by the jsonb below)
-- ═════════════════════════════════════════════════════════════════════════════════════════════════════════
-- tables: [relation, privilege, columns|null, origin]; functions: [signature, origin]. A privilege with a column list is a COLUMN-LEVEL grant.
--   VERIFIER — SELECT+INSERT on the inventory verification table; SELECT on six input relations (the four of the independent derivations, plus the convention bridge
--              and the search-interval ledger that the 1206/1232 completeness digests read as the INVOKER); EXECUTE on window_verification_violations and on the completeness function's nine-function helper
--              closure (R10-4 iii: the job ENDS in the combined candidate gate, run as the INVOKER — the delta derived the 1206-R6 way, one grant per
--              `permission denied` until the job's own final gate converged; 1240 grants EXECUTE on the combined function itself);
--              and 1240's: SELECT/INSERT/DELETE on its own window-verification table, reads, EXECUTE lists. NO DELETE on the inventory-verification
--              table (a re-run replaces it without one — measured), NO UPDATE anywhere, NO seal, NO build-data write.
--   SEALER   — INSERT on the seal table; UPDATE on kala_gochara_publication ONLY on the four columns ledger.publish actually sets (status, published_at,
--              content_digest, row_counts — R10-7 iii; narrowed from table-wide); SELECT on the legacy windows relation ONLY on (chart_id, generation)
--              (R10-7 ii: `ledger.publish` counts the legacy projection's rows when the relation exists, so the production-shaped schema needs this read
--              and nothing more); SELECT on eight inventory/legacy-ledger relations; EXECUTE on 18 seal-side functions; and 1240's SELECT/EXECUTE lists.
-- Candidates left out (each shown NOT needed by a flow): the verifier's DELETE on the inventory-verification table (its SELECT on the search-interval table WAS
-- left out while the job never read it; R10-4 iii made it necessary — the combined gate's ledger digest reads it, and it is back); the sealer's SELECT on the polarity declaration and EXECUTE on av_entry and inventories_digest.
-- NOT HERE, ON PURPOSE — an OPEN item for the owner of the data-plane ACLs: both principals ALSO need SELECT on the L1 tables `chart_facts` and
-- `chart_dashas` (RLS is OFF on both in production — a table-level SELECT suffices); their ACLs are managed by data-plane-ownership-preflight.ts, so a hand
-- grant here risks its allowlist-drift gate. Provision them BEFORE the first verification run. Because they are outside this spec's `ka_/kala_gochara_`
-- namespace the closure check below does not see them.
--
-- THE CLOSURE CHECK (R10-7 iv)
-- ════════════════════════════
-- After applying, for each FOUND principal the check compares the ENTIRE ACL over every ka_gochara_*/kala_gochara_* relation (table-level for SELECT,
-- INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER, and per-COLUMN for SELECT/INSERT/UPDATE/REFERENCES) and every ka_gochara_* function (EXECUTE)
-- with the spec: a required privilege that is missing AND a privilege the spec does not name (whatever its origin) both raise, listing the differences.
-- It assumes production's bootstrap (PUBLIC EXECUTE revoked on functions the migration role creates). The migration PRINTS which principals were found.
-- ROLE GUARD: a principal that does not exist yet gets a WARNING and nothing; applying a follow-up migration carrying the SAME spec once it exists
-- completes the set (a migration runs once — the operator's receipt is the printed "principals found" line).
-- ROLLBACK: REVOKE the same grants.
-- ─────────────────────────────────────────────────────────────────────────────

DO $migration$
DECLARE
  spec constant jsonb := $spec$
{
  "roles": {
    "gochara_verifier": {
     "tables": [
      ["ka_gochara_eval_window_verification","SELECT",null,"1240"],
      ["ka_gochara_eval_window_verification","INSERT",null,"1240"],
      ["ka_gochara_eval_window_verification","DELETE",null,"1240"],
      ["ka_gochara_eval_window","SELECT",null,"1240"],
      ["ka_gochara_eval_window_record","SELECT",null,"1240"],
      ["ka_gochara_relationship_record","SELECT",null,"1240"],
      ["ka_gochara_record_prerequisite","SELECT",null,"1240"],
      ["ka_gochara_contact","SELECT",null,"1240"],
      ["ka_gochara_physical_object","SELECT",null,"1240"],
      ["kala_gochara_coverage","SELECT",null,"1240"],
      ["ka_gochara_search_inventory","SELECT",null,"1240"],
      ["ka_gochara_search_path_pin","SELECT",null,"1240"],
      ["ka_gochara_search_input_snapshot","SELECT",null,"1240"],
      ["ka_gochara_generation_seal","SELECT",null,"1240"],
      ["ka_gochara_rule_path","SELECT",null,"1240"],
      ["ka_gochara_rule_path_seal","SELECT",null,"1240"],
      ["ka_gochara_rule_path_soft_factor","SELECT",null,"1240"],
      ["ka_gochara_factor","SELECT",null,"1240"],
      ["kala_gochara_publication","SELECT",null,"1240"],
      ["ka_gochara_search_inventory_verification","SELECT",null,"1241"],
      ["ka_gochara_search_inventory_verification","INSERT",null,"1241"],
      ["ka_gochara_sky_convention","SELECT",null,"1241"],
      ["ka_gochara_rule_path_prerequisite","SELECT",null,"1241"],
      ["ka_gochara_predicate","SELECT",null,"1241"],
      ["ka_gochara_search_obligation","SELECT",null,"1241"],
      ["ka_gochara_convention_bridge","SELECT",null,"1241"],
      ["ka_gochara_search_interval","SELECT",null,"1241"]
     ],
     "functions": [
      ["ka_gochara_lock_chart(uuid)","1240"],
      ["ka_gochara_lock_global_shared()","1240"],
      ["ka_gochara_generation_is_sealed(uuid,text)","1240"],
      ["ka_gochara_generation_governed(text)","1240"],
      ["ka_gochara_eval_window_content_digest(uuid,text,text,text,text)","1240"],
      ["ka_gochara_eval_window_stored_digest(uuid,text,text,text,text)","1240"],
      ["ka_gochara_eval_window_expected_digest(uuid,text,text,text,text)","1240"],
      ["ka_gochara_eval_window_inputs_digest(uuid,text,text,text,text)","1240"],
      ["ka_gochara_canonical_json(jsonb)","1240"],
      ["ka_gochara_sha256_hex(text)","1240"],
      ["ka_gochara_f4_token(real)","1240"],
      ["ka_gochara_candidate_gate_violations(uuid,text)","1240"],
      ["ka_gochara_window_verification_violations(uuid,text)","1241"],
      ["ka_gochara_search_completeness_violations(uuid,text)","1241"],
      ["ka_gochara_search_l1_facts_digest(uuid,text[])","1241"],
      ["ka_gochara_search_dasha_digest(uuid,uuid[])","1241"],
      ["ka_gochara_search_inventory_digest(uuid,text,text)","1241"],
      ["ka_gochara_search_ledger_digest(uuid,text,text)","1241"],
      ["ka_gochara_search_inventory_preimage(uuid,text,text)","1241"],
      ["ka_gochara_utc_ts(timestamptz)","1241"],
      ["ka_gochara_search_moon_scope_violations(uuid,text)","1241"],
      ["ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)","1241"]
     ]
    },
    "gochara_sealer": {
     "tables": [
      ["ka_gochara_eval_window_verification","SELECT",null,"1240"],
      ["ka_gochara_eval_window","SELECT",null,"1240"],
      ["ka_gochara_eval_window_record","SELECT",null,"1240"],
      ["ka_gochara_relationship_record","SELECT",null,"1240"],
      ["ka_gochara_search_path_pin","SELECT",null,"1240"],
      ["ka_gochara_search_input_snapshot","SELECT",null,"1240"],
      ["ka_gochara_generation_seal","SELECT",null,"1240"],
      ["kala_gochara_publication","SELECT",null,"1240"],
      ["ka_gochara_record_prerequisite","SELECT",null,"1240"],
      ["ka_gochara_contact","SELECT",null,"1240"],
      ["ka_gochara_physical_object","SELECT",null,"1240"],
      ["ka_gochara_generation_seal","INSERT",null,"1241"],
      ["kala_gochara_publication","UPDATE",["status","published_at","content_digest","row_counts"],"1241"],
      ["kala_gochara_windows","SELECT",["chart_id","generation"],"1241"],
      ["kala_gochara_coverage","SELECT",null,"1241"],
      ["kala_gochara_contacts","SELECT",null,"1241"],
      ["ka_gochara_rule_path_seal","SELECT",null,"1241"],
      ["ka_gochara_convention_bridge","SELECT",null,"1241"],
      ["ka_gochara_search_inventory","SELECT",null,"1241"],
      ["ka_gochara_search_obligation","SELECT",null,"1241"],
      ["ka_gochara_search_interval","SELECT",null,"1241"],
      ["ka_gochara_search_inventory_verification","SELECT",null,"1241"]
     ],
     "functions": [
      ["ka_gochara_window_verification_violations(uuid,text)","1240"],
      ["ka_gochara_window_verification_replay_violations(uuid,text)","1240"],
      ["ka_gochara_candidate_gate_violations(uuid,text)","1240"],
      ["ka_gochara_eval_window_content_digest(uuid,text,text,text,text)","1240"],
      ["ka_gochara_eval_window_stored_digest(uuid,text,text,text,text)","1240"],
      ["ka_gochara_eval_window_expected_digest(uuid,text,text,text,text)","1240"],
      ["ka_gochara_eval_window_inputs_digest(uuid,text,text,text,text)","1240"],
      ["ka_gochara_f4_token(real)","1240"],
      ["ka_gochara_canonical_json(jsonb)","1240"],
      ["ka_gochara_sha256_hex(text)","1240"],
      ["ka_gochara_lock_chart(uuid)","1240"],
      ["ka_gochara_lock_global_shared()","1240"],
      ["ka_gochara_seal_generation(uuid,text)","1241"],
      ["ka_gochara_coverage_drift(uuid,text)","1241"],
      ["ka_gochara_horizon_finite_ok(tstzrange)","1241"],
      ["ka_gochara_coverage_facts(text,tstzrange,text[])","1241"],
      ["ka_gochara_facts_horizon(jsonb)","1241"],
      ["ka_gochara_membership_violations(uuid,text)","1241"],
      ["ka_gochara_membership_violation(jsonb,uuid,text,jsonb,tstzrange[])","1241"],
      ["ka_gochara_search_completeness_violations(uuid,text)","1241"],
      ["ka_gochara_search_replay_violations(uuid,text)","1241"],
      ["ka_gochara_search_l1_facts_digest(uuid,text[])","1241"],
      ["ka_gochara_search_dasha_digest(uuid,uuid[])","1241"],
      ["ka_gochara_search_inventory_digest(uuid,text,text)","1241"],
      ["ka_gochara_search_ledger_digest(uuid,text,text)","1241"],
      ["ka_gochara_search_inventory_preimage(uuid,text,text)","1241"],
      ["ka_gochara_utc_ts(timestamptz)","1241"],
      ["ka_gochara_search_moon_scope_violations(uuid,text)","1241"],
      ["ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)","1241"],
      ["ka_gochara_generation_governed(text)","1241"]
     ]
    }
  },
  "builder_backfill": {"role":"data_plane_builder","functions":["ka_gochara_window_qualification_ok(jsonb)"]}
}
$spec$::jsonb;
  r text; g record; rec record; col record; priv text; sig text; fn_oid oid; cols_sql text;
  problems text[] := '{}'; found_v boolean; found_s boolean; found_b boolean;
  expected_tbl boolean; expected_col boolean; expected_fn boolean;
BEGIN
  IF to_regclass('public.ka_gochara_eval_window_verification') IS NULL
     OR to_regclass('public.ka_gochara_search_inventory_verification') IS NULL
     OR to_regclass('public.ka_gochara_generation_seal') IS NULL THEN
    RAISE EXCEPTION 'migration 1241: the protected window (1206, 1240) has not been applied — refusing; apply the window first';
  END IF;

  -- 1. APPLY (role-existence-guarded; idempotent — a privilege already held is a no-op)
  FOR r IN SELECT jsonb_object_keys(spec->'roles') LOOP
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
      FOR g IN SELECT e->>0 AS tbl, e->>1 AS priv, e->2 AS cols FROM jsonb_array_elements(spec->'roles'->r->'tables') e LOOP
        IF g.priv NOT IN ('SELECT','INSERT','UPDATE','DELETE') THEN RAISE EXCEPTION 'migration 1241: unexpected privilege %', g.priv; END IF;
        IF to_regclass('public.' || quote_ident(g.tbl)) IS NULL THEN RAISE EXCEPTION 'migration 1241: relation % does not exist', g.tbl; END IF;
        cols_sql := CASE WHEN jsonb_typeof(g.cols) = 'array'
                         THEN ' (' || (SELECT string_agg(quote_ident(c), ', ') FROM jsonb_array_elements_text(g.cols) c) || ')' ELSE '' END;
        EXECUTE format('GRANT %s%s ON public.%I TO %I', g.priv, cols_sql, g.tbl, r);
      END LOOP;
      FOR g IN SELECT e->>0 AS sig FROM jsonb_array_elements(spec->'roles'->r->'functions') e LOOP
        fn_oid := to_regprocedure('public.' || g.sig)::oid;
        IF fn_oid IS NULL THEN RAISE EXCEPTION 'migration 1241: function % does not exist', g.sig; END IF;
        EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO %I', fn_oid::regprocedure, r);
      END LOOP;
      RAISE NOTICE 'migration 1241: grants (1240 backfill + 1241) issued to role %', r;
    ELSE
      RAISE WARNING 'migration 1241: role % NOT FOUND — NO grant was issued to it; apply this migration again (a follow-up carrying the SAME spec) once the role exists', r;
    END IF;
  END LOOP;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = spec->'builder_backfill'->>'role') THEN
    FOR sig IN SELECT jsonb_array_elements_text(spec->'builder_backfill'->'functions') LOOP
      fn_oid := to_regprocedure('public.' || sig)::oid;
      IF fn_oid IS NULL THEN RAISE EXCEPTION 'migration 1241: function % does not exist', sig; END IF;
      EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO %I', fn_oid::regprocedure, spec->'builder_backfill'->>'role');
    END LOOP;
  END IF;

  found_v := EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier');
  found_s := EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_sealer');
  found_b := EXISTS (SELECT 1 FROM pg_roles WHERE rolname = spec->'builder_backfill'->>'role');
  RAISE NOTICE 'migration 1241 principals found: gochara_verifier=%, gochara_sealer=%, data_plane_builder=%', found_v, found_s, found_b;

  -- 2. CLOSURE: for each FOUND principal the ENTIRE ACL over every ka_gochara_* / kala_gochara_* relation (table-level and per-column) and every
  --    ka_gochara_* function EQUALS the spec — required privileges present AND nothing else held (INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER
  --    included). A privilege the spec does not name is a violation, whatever its origin.
  FOR r IN SELECT jsonb_object_keys(spec->'roles') LOOP
    CONTINUE WHEN NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r);
    FOR rec IN SELECT c.oid AS relid, c.relname FROM pg_class c
               WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r','p')
                 AND (c.relname LIKE 'ka\_gochara\_%' OR c.relname LIKE 'kala\_gochara\_%') ORDER BY c.relname LOOP
      FOREACH priv IN ARRAY ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER'] LOOP
        expected_tbl := EXISTS (SELECT 1 FROM jsonb_array_elements(spec->'roles'->r->'tables') e
                                WHERE e->>0 = rec.relname AND e->>1 = priv AND jsonb_typeof(e->2) <> 'array');
        IF has_table_privilege(r, rec.relid, priv) <> expected_tbl THEN
          problems := problems || format('%s %s on %s: %s', r, priv, rec.relname, CASE WHEN expected_tbl THEN 'MISSING' ELSE 'PROHIBITED but held' END);
        END IF;
        IF priv IN ('SELECT','INSERT','UPDATE','REFERENCES') AND NOT has_table_privilege(r, rec.relid, priv) THEN
          FOR col IN SELECT a.attnum, a.attname FROM pg_attribute a WHERE a.attrelid = rec.relid AND a.attnum > 0 AND NOT a.attisdropped LOOP
            expected_col := EXISTS (SELECT 1 FROM jsonb_array_elements(spec->'roles'->r->'tables') e
                                    WHERE e->>0 = rec.relname AND e->>1 = priv AND jsonb_typeof(e->2) = 'array' AND (e->2) ? col.attname::text);
            IF has_column_privilege(r, rec.relid, col.attnum, priv) <> expected_col THEN
              problems := problems || format('%s %s (%s) on %s: %s', r, priv, col.attname, rec.relname, CASE WHEN expected_col THEN 'MISSING' ELSE 'PROHIBITED but held' END);
            END IF;
          END LOOP;
        END IF;
      END LOOP;
    END LOOP;
    FOR rec IN SELECT p.oid AS fnid, p.oid::regprocedure::text AS sig FROM pg_proc p
               WHERE p.pronamespace = 'public'::regnamespace AND p.proname LIKE 'ka\_gochara\_%' ORDER BY 2 LOOP
      expected_fn := EXISTS (SELECT 1 FROM jsonb_array_elements(spec->'roles'->r->'functions') e WHERE to_regprocedure('public.' || (e->>0))::oid = rec.fnid);
      IF has_function_privilege(r, rec.fnid, 'EXECUTE') <> expected_fn THEN
        problems := problems || format('%s EXECUTE on %s: %s', r, rec.sig, CASE WHEN expected_fn THEN 'MISSING' ELSE 'PROHIBITED but held' END);
      END IF;
    END LOOP;
  END LOOP;
  IF array_length(problems, 1) > 0 THEN
    RAISE EXCEPTION 'migration 1241 post-apply ACL closure failed (% difference(s)): %', array_length(problems, 1), array_to_string(problems[1:40], '; ');
  END IF;
END
$migration$;

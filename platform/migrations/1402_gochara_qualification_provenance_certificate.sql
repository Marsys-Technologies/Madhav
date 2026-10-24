-- Migration 1402: the window `qualification` shape check admits (a) R-4's combustion-inheritance record, (b) R-6/R-7's solver certificate and (c) the
-- generic `certificate` extension member — ONE function replacement, ADDITIVE.
-- SR-OD1: R-4 (SR-Q6-L1-AMEND, combustion provenance) + R-6/R-7 (window solver certificate, RECONCILIATION.md lines 36-38); number allocated by the cockpit
-- (MIGRATION_ALLOCATION.json 1402 "R-4 provenance + R-6/R-7 certificate keys, one migration").
-- STATUS: composed from two reviewed parts; tested on a disposable database only; NOT applied anywhere. A ROUTINE migration (replaces one function body,
-- creates one function), applied by the ordinary deploy AFTER 1240 (the window that created the function and the column) and after 1378 (its grants).
--
-- PROVENANCE OF THE TEXT
-- ══════════════════════
--   Part A (R-4)    kalayantra/od1-r4 head 4f8954050e55; migration draft sha256 4fa33d9357f6f65132c53ecd7e77672d103b30e9fc88ebc611895d2cc428eafa;
--                   scoped re-review (lane review X-20261021T164408Z-review-lane-r4b): ACCEPTED, blocking none — B1 "provenance stamp refused by the closed key list" FIXED.
--                   That review required its B1 evidence to be re-run on the final text if the R-6/R-7 keys were folded in: done for this file (job X-20261021T184648Z-compose-1402).
--   Part B (R-6/R-7) kalayantra/od1-r67 head 4d45ba99d2fb; fragment 1402_part_r67.sql sha256 ce46e214a734aaaae507a68366b02c51fdc8a6b82056bebcb4f18f817ff9464f;
--                   lane review X-20261021T184636Z-review-lane-r67 (in progress when this file was composed — its verdict is NOT claimed here).
--   The only edits to either part: the two key lists are joined, Part B's `solver_certificate_ok` clause is added with AND, and the builder EXECUTE grant
--   Part B's merge note asked for is added (guarded, as 1240 issues it).
--
-- WHY
-- ═══
-- 1240's `ka_gochara_window_qualification_ok(jsonb)` is a CLOSED key list (policy, unqualified_reason, unresolved, affected_channels, members,
-- qualified_members) behind CHECK `kgew_qualification_shape_ck` on `ka_gochara_eval_window.qualification`. R-4 makes every window of a P1 Form B grain carry,
-- in that provenance, the combustion authority it was derived from (`window_sweep.qualification()` adds `combustion_inheritance`); R-6/R-7 make the window
-- solver store the piece tree its answer rests on under `solver_certificate`. With the closed list the very first build that writes either fails at the
-- window INSERT. This file admits exactly those, and nothing else.
--
-- WHAT IT ADMITS (every key OPTIONAL; a window that carries none of them is exactly as valid as before — no row changes, the constraint is not re-created)
-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
-- 1. `combustion_inheritance` (R-4; a P1 Form B grain, absent for every other grain). A closed object:
--      orb_digest        string   sha256 of the canonical JSON of the bg_combustion_orbs values consumed (the digest L0_CONSUMED binds)
--      orb_row_ids       object   {graha: bg_combustion_orbs.id}, every value a number
--      l1_module         string   the L1 module that holds the combustion function
--      l1_module_digest  string   sha256 of that module's source
--    All four are required when the key is present; an unknown member is refused.
-- 2. `solver_certificate` (R-6/R-7; written by `window_solver.stored_certificate`, read by `window_cert_check`). A closed object, checked by the new function
--    `ka_gochara_solver_certificate_ok(jsonb)`: schema 'window_solver_certificate/1'; objective; t0; outcome 'solved'|'blank'; reason (null iff solved);
--    phase; value / instant / upper_bound (value null iff blank); evals; max_evals; budget_scope 'window'; limits {QUANT, TIE, EPS_M, TIME_TOL, LEAF_CURV,
--    H1_SPACING_S numbers, h4_used boolean}; geometry {cuts, pieces}; geometry_digest (64 lowercase hex); cells (at most 400 elements, each [kind, l, r, u]);
--    open (at most 200 elements, each [l, r]); open_total; truncated; whole text at most 262,144 bytes. The DISAGREEMENT / INCONCLUSIVE class is the
--    VERIFIER's finding, persisted in the verification row's runner_identity — not a key here.
-- 3. `certificate` (Part A's EXTENSION POINT: any JSON OBJECT, no further shape). Kept because the union of the two parts was ordered ("no key dropped");
--    the R67 code writes `solver_certificate`, not `certificate`, so nothing writes this key today.
--
-- IDEMPOTENT / SAFE
-- ═════════════════
-- CREATE OR REPLACE on both signatures: the outer function's ACL (1240's guarded builder grant, 1378's backfill) is KEPT, the CHECK keeps pointing at it, and
-- every row that satisfied the old body satisfies the new one (the new body only admits MORE). The new function gets the same guarded builder EXECUTE grant
-- (production revokes PUBLIC EXECUTE on functions the migration role creates, and a CHECK function is called as the inserting role). A second application is a
-- no-op. The gate refuses to apply when 1240's objects are missing.
--
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns one transaction per file.
-- ROLLBACK (unused installation only): re-apply 1240's function body (CREATE OR REPLACE), DROP FUNCTION public.ka_gochara_solver_certificate_ok(jsonb) and delete
-- the _migrations_applied row — after first removing any window whose qualification carries one of the new keys, since the old body would refuse it.
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE ──────────────────────────────────────────────────────────────────────
DO $$
DECLARE failures text;
BEGIN
  WITH f(failure, detail) AS (
    SELECT 'migration_1240_not_applied', 'ka_gochara_window_qualification_ok(jsonb)'
      WHERE to_regprocedure('public.ka_gochara_window_qualification_ok(jsonb)') IS NULL
    UNION ALL SELECT 'migration_1240_not_applied', 'kgew_qualification_shape_ck'
      WHERE NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conname = 'kgew_qualification_shape_ck'
                        AND c.conrelid = 'public.ka_gochara_eval_window'::regclass)
  )
  SELECT string_agg(failure || ' (' || detail || ')', ', ') INTO failures FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1402 BLOCKED: %', failures;
  END IF;
END;
$$;

-- ── R-6/R-7: the solver certificate's own shape check (Part B, unchanged) ──────
-- Created BEFORE the outer function, which calls it.
CREATE OR REPLACE FUNCTION public.ka_gochara_solver_certificate_ok(c jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path = pg_catalog, public AS $$
  SELECT c IS NULL OR (
    jsonb_typeof(c) = 'object'
    AND c ?& ARRAY['schema', 'objective', 't0', 'outcome', 'reason', 'phase', 'value', 'instant', 'upper_bound', 'evals', 'max_evals', 'budget_scope',
                   'limits', 'geometry', 'geometry_digest', 'cells', 'open', 'open_total', 'truncated']
    AND NOT EXISTS (SELECT 1 FROM jsonb_object_keys(c) k
                    WHERE k NOT IN ('schema', 'objective', 't0', 'outcome', 'reason', 'phase', 'value', 'instant', 'upper_bound', 'evals', 'max_evals',
                                    'budget_scope', 'limits', 'geometry', 'geometry_digest', 'cells', 'open', 'open_total', 'truncated'))
    AND c -> 'schema' = '"window_solver_certificate/1"'::jsonb
    AND c -> 'objective' IN ('"sum_of_group_max"'::jsonb, '"min_of_group_max"'::jsonb)
    AND jsonb_typeof(c -> 't0') = 'string'
    AND c -> 'outcome' IN ('"solved"'::jsonb, '"blank"'::jsonb)
    AND jsonb_typeof(c -> 'reason') IN ('string', 'null')
    AND ((c -> 'outcome') = '"solved"'::jsonb) = ((c -> 'reason') = 'null'::jsonb)
    AND jsonb_typeof(c -> 'phase') = 'string'
    AND jsonb_typeof(c -> 'value') IN ('number', 'null') AND jsonb_typeof(c -> 'instant') IN ('number', 'null') AND jsonb_typeof(c -> 'upper_bound') IN ('number', 'null')
    AND ((c -> 'outcome') = '"solved"'::jsonb) = ((c -> 'value') <> 'null'::jsonb)
    AND jsonb_typeof(c -> 'evals') = 'number' AND jsonb_typeof(c -> 'max_evals') = 'number' AND jsonb_typeof(c -> 'open_total') = 'number'
    AND c -> 'budget_scope' = '"window"'::jsonb
    AND jsonb_typeof(c -> 'limits') = 'object'
    AND c -> 'limits' ?& ARRAY['QUANT', 'TIE', 'EPS_M', 'TIME_TOL', 'LEAF_CURV', 'H1_SPACING_S', 'h4_used']
    AND jsonb_typeof(c -> 'limits' -> 'h4_used') = 'boolean'
    AND jsonb_typeof(c -> 'geometry') = 'object' AND c -> 'geometry' ?& ARRAY['cuts', 'pieces']
    AND jsonb_typeof(c -> 'geometry' -> 'cuts') = 'array' AND jsonb_typeof(c -> 'geometry' -> 'pieces') = 'array'
    AND jsonb_typeof(c -> 'geometry_digest') = 'string' AND (c ->> 'geometry_digest') ~ '^[0-9a-f]{64}$'
    AND jsonb_typeof(c -> 'cells') = 'array' AND jsonb_array_length(c -> 'cells') <= 400
    AND jsonb_typeof(c -> 'open') = 'array' AND jsonb_array_length(c -> 'open') <= 200
    AND jsonb_typeof(c -> 'truncated') = 'boolean'
    AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements(c -> 'cells') e
                    WHERE jsonb_typeof(e) <> 'array' OR jsonb_array_length(e) <> 4
                       OR e -> 0 NOT IN ('"piece"'::jsonb, '"dead"'::jsonb, '"leaf"'::jsonb, '"pruned"'::jsonb)
                       OR jsonb_typeof(e -> 1) <> 'number' OR jsonb_typeof(e -> 2) <> 'number' OR jsonb_typeof(e -> 3) <> 'number')
    AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements(c -> 'open') e
                    WHERE jsonb_typeof(e) <> 'array' OR jsonb_array_length(e) <> 2 OR jsonb_typeof(e -> 0) <> 'number' OR jsonb_typeof(e -> 1) <> 'number')
    AND octet_length(c::text) <= 262144);
$$;

-- ── the shape check: 1240's body, plus the three optional members ─────────────
CREATE OR REPLACE FUNCTION public.ka_gochara_window_qualification_ok(q jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path = pg_catalog, public AS $$
  SELECT q IS NULL OR (
    jsonb_typeof(q) = 'object'
    AND q ?& ARRAY['policy', 'unqualified_reason', 'unresolved', 'affected_channels', 'members', 'qualified_members']
    AND NOT EXISTS (SELECT 1 FROM jsonb_object_keys(q) k
                    WHERE k NOT IN ('policy', 'unqualified_reason', 'unresolved', 'affected_channels', 'members', 'qualified_members',
                                    'combustion_inheritance', 'certificate', 'solver_certificate'))
    -- R9-1: the result policy this window was drafted under — one of the two NAMED policies
    AND (q -> 'policy') IN ('"all_null_candidate/1"'::jsonb, '"window_qualification/1"'::jsonb)
    AND (jsonb_typeof(q -> 'unqualified_reason') IN ('string', 'null'))
    AND jsonb_typeof(q -> 'unresolved') = 'object'
    AND jsonb_typeof(q -> 'affected_channels') = 'array'
    AND jsonb_typeof(q -> 'members') = 'number' AND jsonb_typeof(q -> 'qualified_members') = 'number'
    AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements(q -> 'affected_channels') c
                    WHERE c NOT IN ('"evidence_for_occurrence"'::jsonb, '"evidence_against_occurrence"'::jsonb))
    AND NOT EXISTS (SELECT 1 FROM jsonb_each(q -> 'unresolved') u WHERE jsonb_typeof(u.value) <> 'number')
    -- R-4: the combustion authority a P1 Form B grain derived its states from (absent for every other grain)
    AND (NOT (q ? 'combustion_inheritance') OR (
         jsonb_typeof(q -> 'combustion_inheritance') = 'object'
         AND (q -> 'combustion_inheritance') ?& ARRAY['orb_digest', 'orb_row_ids', 'l1_module', 'l1_module_digest']
         AND NOT EXISTS (SELECT 1 FROM jsonb_object_keys(q -> 'combustion_inheritance') k
                         WHERE k NOT IN ('orb_digest', 'orb_row_ids', 'l1_module', 'l1_module_digest'))
         AND jsonb_typeof(q -> 'combustion_inheritance' -> 'orb_digest') = 'string'
         AND jsonb_typeof(q -> 'combustion_inheritance' -> 'l1_module') = 'string'
         AND jsonb_typeof(q -> 'combustion_inheritance' -> 'l1_module_digest') = 'string'
         AND jsonb_typeof(q -> 'combustion_inheritance' -> 'orb_row_ids') = 'object'
         AND NOT EXISTS (SELECT 1 FROM jsonb_each(q -> 'combustion_inheritance' -> 'orb_row_ids') u WHERE jsonb_typeof(u.value) <> 'number')))
    -- the generic certificate member (Part A's extension point; any JSON object, nothing else writes it today)
    AND (NOT (q ? 'certificate') OR jsonb_typeof(q -> 'certificate') = 'object')
    -- R-6/R-7: the window solver's piece-tree certificate (its own closed shape; SQL NULL when the key is absent, which the function accepts)
    AND public.ka_gochara_solver_certificate_ok(q -> 'solver_certificate') IS TRUE);
$$;

-- ── the builder's EXECUTE on the new function (as 1240 issues it on the outer one; role-existence-guarded) ──
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    GRANT EXECUTE ON FUNCTION public.ka_gochara_solver_certificate_ok(jsonb) TO data_plane_builder;
    RAISE NOTICE 'migration 1402: builder EXECUTE on ka_gochara_solver_certificate_ok issued to role data_plane_builder';
  ELSE
    RAISE NOTICE 'migration 1402: role data_plane_builder NOT FOUND — NO builder grant was issued; once it exists it needs EXECUTE on ka_gochara_solver_certificate_ok(jsonb) or it cannot insert a window carrying a solver certificate';
  END IF;
END;
$$;

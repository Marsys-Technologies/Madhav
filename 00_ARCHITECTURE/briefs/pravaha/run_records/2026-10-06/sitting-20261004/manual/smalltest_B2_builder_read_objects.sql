-- SMALLTEST B2 readback: exactly what the ka_gochara_v5 builder path READS, checked against data_plane_builder.
-- READ-ONLY: SELECTs over the system catalogs only. No DDL, no DML, no function calls on chart data. Safe on production.
-- Provenance of the list: (a) migration 1234's instrumented-run derivation (the writer's reads of existing relations, which the
--   builder already held), (b) the C46 slice's one NEW read: build_runs.plan_manifest by id (ka_gochara_v5.py, plan marker read),
--   (c) the in-build input verification: bg_transit_rules identity digest + the rule-registry tables.
-- Expected: every row has ok = true. A false row names the exact missing privilege.

WITH want(kind, obj, priv) AS (VALUES
  -- Section A: L1 / L0 / orchestrator relations the builder reads (NOT created by the Gochara generation)
  ('table','public.chart_facts','SELECT'),            -- chart_context.py (operands), substrate.py (L1 node convention)
  ('table','public.chart_dashas','SELECT'),           -- dasha_data fetch + dasha_read single-build check (DISTINCT build_id)
  ('table','public.bg_transit_rules','SELECT'),       -- L0 vedha identity digest in the in-build input verification
  ('table','public.build_runs','SELECT'),             -- NEW with C46: plan_manifest read for the slice marker
  -- Section B: Gochara-generation relations the builder reads (rule registry + prior-stage outputs)
  ('table','public.ka_gochara_factor','SELECT'),
  ('table','public.ka_gochara_predicate','SELECT'),
  ('table','public.ka_gochara_rule_path','SELECT'),
  ('table','public.ka_gochara_rule_path_prerequisite','SELECT'),
  ('table','public.ka_gochara_rule_path_soft_factor','SELECT'),
  ('table','public.ka_gochara_rule_path_seal','SELECT'),
  ('table','public.ka_gochara_sky_convention','SELECT'),
  ('table','public.ka_gochara_sky_event','SELECT'),
  ('table','public.ka_gochara_physical_object','SELECT'),
  ('table','public.ka_gochara_contact','SELECT'),
  ('table','public.ka_gochara_relationship_record','SELECT'),
  ('table','public.ka_gochara_search_inventory','SELECT'),
  ('table','public.ka_gochara_search_input_snapshot','SELECT'),
  ('table','public.kala_gochara_coverage','SELECT'),
  ('table','public.kala_gochara_publication','SELECT'),
  ('table','public.ka_gochara_eval_window','SELECT'),
  ('table','public.ka_gochara_eval_window_record','SELECT'),
  ('table','public.ka_gochara_eval_window','INSERT'),
  ('table','public.ka_gochara_eval_window','DELETE'),
  ('table','public.ka_gochara_eval_window_record','INSERT')
), t AS (
  SELECT w.kind, w.obj, w.priv, to_regclass(w.obj) AS oid
  FROM want w
)
SELECT t.obj, t.priv,
       CASE WHEN t.oid IS NULL THEN NULL
            ELSE has_table_privilege('data_plane_builder', t.oid, t.priv) END AS ok,
       CASE WHEN t.oid IS NULL THEN 'OBJECT MISSING' ELSE '' END AS note
FROM t
UNION ALL
-- column-level confirmation for the one NEW read (a column grant would pass has_column_privilege but not the table check above)
SELECT 'public.build_runs.' || c.col, 'SELECT',
       CASE WHEN to_regclass('public.build_runs') IS NULL THEN NULL
            ELSE has_column_privilege('data_plane_builder', 'public.build_runs', c.col, 'SELECT') END,
       ''
FROM (VALUES ('id'),('plan_manifest')) AS c(col)
UNION ALL
-- functions the builder path executes (all overloads by name; schema public)
SELECT p.oid::regprocedure::text, 'EXECUTE',
       has_function_privilege('data_plane_builder', p.oid, 'EXECUTE'), ''
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.proname IN ('ka_gochara_lock_chart','ka_gochara_generation_is_sealed','ka_gochara_coverage_facts',
                    'ka_gochara_canonical_json','ka_gochara_sha256_hex')
ORDER BY 1, 2;

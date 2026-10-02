-- W5 expected-manifest query (Codex R15-5). READ-ONLY. The SAME text runs (a) on the rehearsal mirror at the final window bytes — its output is committed as
-- EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv beside EXPECTED_WINDOW_SHA256.txt (the rehearsal asserts the two are identical) — and (b) on production AFTER 1240. Rule: EVERY line of the
-- committed manifest must appear, byte for byte, in production's output (`comm -23 expected actual` is empty). A missing relation (REL ... MISSING), a missing trigger, or a trigger with a different
-- function, event, timing, level, UPDATE-OF column list, argument list, deferrability or ENABLED mode ⇒ STOP. Production-only extra lines (legacy triggers the mirror does not carry) are REPORTED,
-- not failed — they are listed in the act report so the steward and Stream A can classify them.
-- Each TRG line ends with md5(pg_get_functiondef(trigger function)) so W5 pins the guard BODIES as well as the trigger set (schema-qualified: `SET search_path = ''`).
-- Scope: every relation in the post-seal immutability matrix of Codex's round-15 review (digest/candidate-boundary, brief/seal/receipt, referenced/global/external-guarded) in schema public.
-- Run with:  psql -X -q -t -A -F '	' -v ON_ERROR_STOP=1 -f window_trigger_manifest.sql   (tab-separated, C-collation order, no psql footers).
SET search_path = '';
SET default_transaction_read_only = on;
WITH expected(relname) AS (VALUES
  ('ka_gochara_relationship_record'),('ka_gochara_record_prerequisite'),('ka_gochara_contact'),('ka_gochara_eval_window'),('ka_gochara_eval_window_record'),
  ('ka_gochara_search_path_pin'),('ka_gochara_search_inventory'),('ka_gochara_search_input_snapshot'),('ka_gochara_search_obligation'),('ka_gochara_search_interval'),
  ('ka_gochara_search_inventory_verification'),('ka_gochara_eval_window_verification'),
  ('kala_gochara_coverage'),('kala_gochara_publication'),('kala_gochara_contacts'),('kala_gochara_windows'),
  ('ka_gochara_seal_brief'),('ka_gochara_generation_seal'),('ka_gochara_seal_approval'),
  ('ka_gochara_physical_object'),('ka_gochara_contact_identity'),('ka_gochara_sky_convention'),('ka_gochara_convention_bridge'),
  ('ka_gochara_predicate'),('ka_gochara_factor'),('ka_gochara_rule_path'),('ka_gochara_rule_path_prerequisite'),('ka_gochara_rule_path_soft_factor'),('ka_gochara_rule_path_seal'),
  ('ka_gochara_av_polarity_declaration'),('kala_gochara_convention'),('ka_gochara_sky_event')),
rel AS (
  SELECT e.relname, c.oid AS reloid, c.relkind, c.relrowsecurity
  FROM expected e LEFT JOIN pg_catalog.pg_class c ON c.relname = e.relname AND c.relnamespace = 'public'::regnamespace)
SELECT line FROM (
  SELECT 'REL' || E'\t' || relname || E'\t' || coalesce(relkind::text, 'MISSING') AS line, relname AS k1, '' AS k2 FROM rel
  UNION ALL
  SELECT 'TRG' || E'\t' || 'public' || E'\t' || r.relname || E'\t' || t.tgname || E'\t' || t.tgenabled::text || E'\t'
         || pn.nspname || '.' || p.proname || E'\t'
         || CASE WHEN (t.tgtype & 2) <> 0 THEN 'BEFORE' WHEN (t.tgtype & 64) <> 0 THEN 'INSTEAD' ELSE 'AFTER' END || E'\t'
         || concat_ws(',', CASE WHEN (t.tgtype & 4) <> 0 THEN 'INSERT' END, CASE WHEN (t.tgtype & 8) <> 0 THEN 'DELETE' END,
                           CASE WHEN (t.tgtype & 16) <> 0 THEN 'UPDATE' END, CASE WHEN (t.tgtype & 32) <> 0 THEN 'TRUNCATE' END) || E'\t'
         || CASE WHEN (t.tgtype & 1) <> 0 THEN 'ROW' ELSE 'STATEMENT' END || E'\t'
         || coalesce((SELECT string_agg(a.attname, ',' ORDER BY a.attnum) FROM pg_catalog.pg_attribute a WHERE a.attrelid = t.tgrelid AND a.attnum = ANY (t.tgattr)), '') || E'\t'
         || coalesce(encode(t.tgargs, 'escape'), '') || E'\t'
         || (t.tgconstraint <> 0)::text || '/' || t.tgdeferrable::text || '/' || t.tginitdeferred::text || E'\t'
         || coalesce(replace(replace(substring(pg_catalog.pg_get_triggerdef(t.oid) from ' WHEN (\(.*\)) EXECUTE (?:FUNCTION|PROCEDURE) '), E'\\', E'\\\\'), E'\n', E'\\n'), '') || E'\t'     -- the actual WHEN condition from the trigger definition (`pg_get_expr(tgqual)` cannot render OLD+NEW conditions), escaped — not just its presence (Codex R16-4)
         || md5(pg_catalog.pg_get_functiondef(p.oid)) AS line,                   -- the trigger FUNCTION BODY (Fable F-R16-5a): a changed guard body is a difference, not only a changed trigger set
         r.relname AS k1, t.tgname AS k2
  FROM rel r
  JOIN pg_catalog.pg_trigger t ON t.tgrelid = r.reloid AND NOT t.tgisinternal
  JOIN pg_catalog.pg_proc p ON p.oid = t.tgfoid
  JOIN pg_catalog.pg_namespace pn ON pn.oid = p.pronamespace
) q ORDER BY k1 COLLATE "C", k2 COLLATE "C", line COLLATE "C";

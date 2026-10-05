-- 1295_chart_vichara_token_resolver.sql
--
-- Suvarna S-L2 / lane L-KARANAJALA, N-143 option B (SS 2026-10-05, B3 ruling 2(a)): the L1-side RESOLVER for the
-- deterministic chart_vichara citation token that L2 now writes in place of the bigserial `chart_vichara.id`.
--
-- WHY. L2 rows (bodha_cgm_edges.constituent_ga_vichara_ids_array, bodha_mechanisms.constituent_ga_vichara_ids_array, the
-- RM rows) used to cite `chart_vichara.id`, a serial that every ga_vichara rebuild (DELETE + INSERT) renumbers; those
-- citations already dangle after S-L1. L2 now cites TOKEN = sha256(canonical JSON of the vichara natural key)[:16]
-- (64 bits; bodha_writers/vichara_token.py is the ONE definition, this file is generated from its TOKEN_SQL_TEMPLATE and a
-- test compares the two byte for byte). The natural key is (ayanamsha_id, vichara_family, subject, actor, target, domain,
-- varga_id, varga, value_text, value_num, value_jsonb, constituent_facts_array): production is unique on exactly this on
-- the canonical chart (7,774 rows = 7,774 distinct). A vichara row whose cited facts change gets a NEW token (correct).
--
-- WHAT. Two read-only objects, no stored column, no L1 data change, no table written:
--   1. public.chart_vichara_token(<the 12 natural-key columns>) RETURNS text   (STABLE, pg_catalog-only search_path)
--   2. public.vw_chart_vichara_token: one row per chart_vichara row with its `vichara_token` (and the row's own `id`, for
--      joining back; the id is a lookup aid only and must never be cited).
-- A reader resolves a citation with:  SELECT ... FROM public.vw_chart_vichara_token WHERE chart_id = :chart AND vichara_token = :cited
--
-- CANONICAL RULES (identical in Python and here; see bodha_writers/vichara_token.py): positional JSON array of the 12 fields,
-- compact; text -> to_json (NULL -> null); value_num -> trim_scale(numeric)::text (NULL -> null, NaN -> "NaN"); value_jsonb ->
-- PostgreSQL's own value_jsonb::text (NULL -> null); constituent_facts_array -> to_json (NULL -> null, empty -> []).
--
-- DUPLICATE ROWS. On the canonical chart no two rows share a token. The two older, never-rebuilt charts hold exact
-- duplicate rows (identical in every column but id; 666 / 671 pairs, valence_pass): a token resolves to both, which are
-- content-identical, so a citation still names one natural key. Acceptance statements for the canonical chart assert
-- exactly one row per token; for other charts they assert exactly one DISTINCT natural key per token.
--
-- OWNER / GRANTS. Routine migration path: the migrate runner (amjis_app) creates and OWNS both objects, the same owner as
-- vw_chart_digest. amjis_app already holds SELECT on chart_vichara (verified in the guard below); the view runs with the
-- owner's privilege, so the view must be granted only to roles that ALREADY read chart_vichara: SELECT on the view and
-- EXECUTE on the function go to suvarna_reader and data_plane_builder, nothing wider (retrieval_census_ro and
-- nirmana_evidence_ingress_writer do NOT read chart_vichara and are deliberately not granted).
--
-- RE-RUNNABLE. CREATE OR REPLACE for both objects, GRANT and the REVOKE of PUBLIC EXECUTE on the new function are idempotent, the guard and the post-check raise on any
-- surprise; running it twice changes nothing. No DROP, no table DDL, no data write.
--
-- LOCKS. SET LOCAL lock_timeout = '5s': the first statement; CREATE OR REPLACE VIEW takes a brief lock on the view only.
-- Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here).
--
-- VERIFY AFTER APPLY (production structure, not the deploy log; Trap 103):
--   SELECT public.chart_vichara_token('lahiri_chitrapaksha','valence_pass','SUN','SUN','D1_HOUSE_1',NULL,'D1','D1','mixed',0.50,
--     '{"varga": "D1", "link_kind": "lord_placed"}'::jsonb, ARRAY['3f2a9c1d5b7e4a60','9d8c7b6a5f4e3d2c']);   -- 3bf71fa91397a24a
--   SELECT count(*), count(DISTINCT vichara_token) FROM public.vw_chart_vichara_token
--    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';   -- 7774 | 7774 (at S-L1; counts move with ga_vichara rebuilds)
--   SELECT has_table_privilege('suvarna_reader', 'public.vw_chart_vichara_token', 'SELECT'),
--          has_function_privilege('data_plane_builder', 'public.chart_vichara_token(text,text,text,text,text,text,text,text,text,numeric,jsonb,text[])', 'EXECUTE');  -- t | t

SET LOCAL lock_timeout = '5s';

DO $guard$
DECLARE
  r text;
BEGIN
  IF to_regclass('public.chart_vichara') IS NULL THEN
    RAISE EXCEPTION '1295: public.chart_vichara does not exist';
  END IF;
  IF NOT has_table_privilege(current_user, 'public.chart_vichara', 'SELECT') THEN
    RAISE EXCEPTION '1295: % cannot SELECT public.chart_vichara; the view could not be read', current_user;
  END IF;
  FOREACH r IN ARRAY ARRAY['suvarna_reader', 'data_plane_builder'] LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = r) THEN
      RAISE EXCEPTION '1295: required role % does not exist', r;
    END IF;
    IF NOT has_table_privilege(r, 'public.chart_vichara', 'SELECT') THEN
      RAISE EXCEPTION '1295: role % does not already read public.chart_vichara; refusing to widen its access through the view', r;
    END IF;
  END LOOP;
END
$guard$;

CREATE OR REPLACE FUNCTION public.chart_vichara_token(
  p_ayanamsha_id text, p_vichara_family text, p_subject text, p_actor text, p_target text, p_domain text,
  p_varga_id text, p_varga text, p_value_text text, p_value_num numeric, p_value_jsonb jsonb,
  p_constituent_facts_array text[]
) RETURNS text
LANGUAGE sql
STABLE
PARALLEL SAFE
SET search_path = pg_catalog
AS $fn$
  SELECT left(encode(sha256(convert_to(
    '[' || concat_ws(',',
      coalesce(to_json(p_ayanamsha_id)::text, 'null'),
      coalesce(to_json(p_vichara_family)::text, 'null'),
      coalesce(to_json(p_subject)::text, 'null'),
      coalesce(to_json(p_actor)::text, 'null'),
      coalesce(to_json(p_target)::text, 'null'),
      coalesce(to_json(p_domain)::text, 'null'),
      coalesce(to_json(p_varga_id)::text, 'null'),
      coalesce(to_json(p_varga)::text, 'null'),
      coalesce(to_json(p_value_text)::text, 'null'),
      CASE WHEN p_value_num IS NULL THEN 'null'
           WHEN p_value_num = 'NaN'::numeric THEN '"NaN"'
           ELSE trim_scale(p_value_num)::text END,
      coalesce(p_value_jsonb::text, 'null'),
      coalesce(to_json(p_constituent_facts_array)::text, 'null')
    ) || ']', 'UTF8')), 'hex'), 16)
$fn$;

CREATE OR REPLACE VIEW public.vw_chart_vichara_token AS
SELECT v.id,
       v.chart_id,
       v.ayanamsha_id,
       v.vichara_family,
       v.subject,
       v.actor,
       v.target,
       v.domain,
       v.varga_id,
       v.varga,
       public.chart_vichara_token(
         v.ayanamsha_id, v.vichara_family, v.subject, v.actor, v.target, v.domain, v.varga_id, v.varga,
         v.value_text, v.value_num, v.value_jsonb, v.constituent_facts_array
       ) AS vichara_token
  FROM public.chart_vichara v;

-- The function is pure (reads nothing but its arguments); production's default ACL for objects amjis_app creates already
-- withholds PUBLIC EXECUTE, and a fresh database would grant it, so state it explicitly. Own new object only.
REVOKE ALL ON FUNCTION public.chart_vichara_token(text, text, text, text, text, text, text, text, text, numeric, jsonb, text[]) FROM PUBLIC;
GRANT SELECT ON public.vw_chart_vichara_token TO suvarna_reader, data_plane_builder;
GRANT EXECUTE ON FUNCTION public.chart_vichara_token(text, text, text, text, text, text, text, text, text, numeric, jsonb, text[])
  TO suvarna_reader, data_plane_builder;

DO $post$
DECLARE
  got text;
BEGIN
  got := public.chart_vichara_token('lahiri_chitrapaksha', 'valence_pass', 'SUN', 'SUN', 'D1_HOUSE_1', NULL, 'D1', 'D1', 'mixed',
                                    0.50, '{"varga": "D1", "link_kind": "lord_placed"}'::jsonb,
                                    ARRAY['3f2a9c1d5b7e4a60', '9d8c7b6a5f4e3d2c']);
  IF got IS DISTINCT FROM '3bf71fa91397a24a' THEN
    RAISE EXCEPTION '1295: golden token mismatch: got %, expected 3bf71fa91397a24a (the SQL and Python definitions disagree on this server)', got;
  END IF;
  IF NOT has_table_privilege('suvarna_reader', 'public.vw_chart_vichara_token', 'SELECT')
     OR NOT has_table_privilege('data_plane_builder', 'public.vw_chart_vichara_token', 'SELECT')
     OR NOT has_function_privilege('suvarna_reader', 'public.chart_vichara_token(text,text,text,text,text,text,text,text,text,numeric,jsonb,text[])', 'EXECUTE')
     OR NOT has_function_privilege('data_plane_builder', 'public.chart_vichara_token(text,text,text,text,text,text,text,text,text,numeric,jsonb,text[])', 'EXECUTE') THEN
    RAISE EXCEPTION '1295: a required grant is missing after apply';
  END IF;
END
$post$;

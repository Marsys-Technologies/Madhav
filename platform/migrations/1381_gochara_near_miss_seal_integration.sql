-- Migration 1381: P06b near-miss verification and seal integration (ruling 18 §8).
-- Created: 2026-10-15. Protected; apply AFTER 1305 -> 1306 -> 1308 (1379 is P09's publication authority).
-- migrate.ts owns the transaction. Never edit applied migrations.
-- FB-20: exact pg_get_functiondef pins, measured on guarded PostgreSQL 15.17.
-- Each replacement carries the complete 1240 body plus only its near-miss block.
-- Legacy digests are unchanged when the manifest layer version is absent.
-- FB-21: readback_1381_near_miss_seal.sql records server_version_num and all function pins.
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';
DO $$
DECLARE f text; expected text;
BEGIN
  IF to_regclass('public.ka_gochara_near_miss_search') IS NULL OR
     to_regprocedure('public.ka_gochara_search_snapshot_copy_violations(uuid,text)') IS NULL OR
     position('expected_class_list_missing' in pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure)) = 0 THEN
    RAISE EXCEPTION '1381 predecessor chain missing: require 1305 -> 1306 -> 1308';
  END IF;
  FOR f, expected IN SELECT * FROM (VALUES
    ('ka_gochara_candidate_gate_violations', 'c20ceca3e6f8b3e3dcf02d8ed4a9f885f9202a34652a29577c05fe8e1d716c25'),
    ('ka_gochara_brief_state_digest', 'c2f17a284dcc7cfecd5e67f79eb7beeafbfb8ca8a244a9443ae65ecdf74127f4')
  ) pins(name, digest) LOOP
    IF to_regprocedure('public.' || f || '(uuid,text)') IS NULL OR
       encode(sha256(convert_to(pg_get_functiondef(to_regprocedure('public.' || f || '(uuid,text)')), 'UTF8')), 'hex') IS DISTINCT FROM expected THEN
      RAISE EXCEPTION '1381 predecessor definition mismatch: % (server_version_num %)', f, current_setting('server_version_num');
    END IF;
  END LOOP;
END;
$$;

-- A separate verification row preserves the bytes of historical class verifications.
CREATE TABLE public.ka_gochara_near_miss_verification (
  chart_id uuid NOT NULL REFERENCES public.charts(id),
  generation text NOT NULL CHECK (public.ka_gochara_generation_governed(generation) IS TRUE),
  layer_version integer NOT NULL CHECK (layer_version = 1),
  near_miss_digest text NOT NULL CHECK (near_miss_digest ~ '^[0-9a-f]{64}$'),
  verified_by text NOT NULL DEFAULT current_user,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, generation)
);
CREATE TRIGGER ka_gochara_nmv_0_statement_lock BEFORE UPDATE OR DELETE ON public.ka_gochara_near_miss_verification
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock();
CREATE TRIGGER ka_gochara_nmv_1_write_guard BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_near_miss_verification
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_chart_write_guard('no_update');
CREATE TRIGGER ka_gochara_nmv_no_truncate BEFORE TRUNCATE ON public.ka_gochara_near_miss_verification
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- Includes the expected object census, pinned manifest and global object rows REACHABLE
-- from this generation; no unrelated global object can stale a generation's evidence.
CREATE FUNCTION public.ka_gochara_near_miss_digest(p_chart uuid, p_generation text)
RETURNS text LANGUAGE sql STABLE SET search_path = pg_catalog, public
SET TimeZone = 'UTC' SET DateStyle = 'ISO, YMD' SET extra_float_digits = 1 AS $$
  WITH junction_sources AS (
    SELECT e.event_id FROM public.ka_gochara_sky_event e
    WHERE e.event_kind IN ('sign_ingress','nakshatra_ingress') AND EXISTS (
      SELECT 1 FROM public.ka_gochara_near_miss n JOIN public.ka_gochara_near_miss_object o USING(near_miss_object_id)
      WHERE n.chart_id=p_chart AND n.generation=p_generation AND o.body=e.body AND o.convention_id=e.convention_id)
  ), lines(line) AS (
    SELECT 'manifest:' || (to_jsonb(p) - ARRAY['created_at','published_at','status','content_digest','row_counts','superseded_at'])::text
      FROM public.kala_gochara_publication p WHERE p.chart_id=p_chart AND p.generation=p_generation
    UNION ALL SELECT 'object:' || (to_jsonb(o)-'created_at')::text FROM public.ka_gochara_near_miss_object o
      WHERE o.near_miss_object_id IN (
        SELECT s.near_miss_object_id FROM public.ka_gochara_near_miss_search s WHERE s.chart_id=p_chart AND s.generation=p_generation
        UNION SELECT n.near_miss_object_id FROM public.ka_gochara_near_miss n WHERE n.chart_id=p_chart AND n.generation=p_generation)
    UNION ALL SELECT 'search:' || (to_jsonb(s)-'created_at')::text FROM public.ka_gochara_near_miss_search s
      WHERE s.chart_id=p_chart AND s.generation=p_generation
    UNION ALL SELECT 'occurrence:' || (to_jsonb(n)-'created_at')::text FROM public.ka_gochara_near_miss n
      WHERE n.chart_id=p_chart AND n.generation=p_generation
    -- The junction detector reads this pinned sky population and its direct
    -- superseders (which can be under a corrected convention). Bind their bytes
    -- too: a source correction/enrichment must invalidate the old attestation.
    UNION ALL SELECT 'junction_source:' || encode(sha256(convert_to((to_jsonb(e)-'created_at')::text,'UTF8')),'hex')
      FROM public.ka_gochara_sky_event e WHERE e.event_id IN (SELECT event_id FROM junction_sources)
        OR e.supersedes_event_id IN (SELECT event_id FROM junction_sources)
    UNION ALL SELECT 'snapshot:' || (to_jsonb(s)-'created_at')::text FROM public.ka_gochara_search_input_snapshot s
      WHERE s.chart_id=p_chart AND s.generation=p_generation
    UNION ALL SELECT 'obligation:' || (to_jsonb(o)-'created_at')::text FROM public.ka_gochara_search_obligation o
      WHERE o.chart_id=p_chart AND o.generation=p_generation AND o.relation IN ('aspect','conjunction') AND o.target LIKE 'point:%'
  ) SELECT encode(sha256(convert_to(coalesce(string_agg(line,E'\n' ORDER BY line COLLATE "C"),''),'UTF8')),'hex') FROM lines;
$$;

CREATE FUNCTION public.ka_gochara_near_miss_violations(p_chart uuid, p_generation text)
RETURNS TABLE (violation text, detail text) LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE pin jsonb; h tstzrange;
BEGIN
  SELECT p.input_generation_vector->'near_miss_layer_version', p.horizon INTO pin,h
    FROM public.kala_gochara_publication p WHERE p.chart_id=p_chart AND p.generation=p_generation;
  IF pin IS NULL THEN
    IF EXISTS(SELECT 1 FROM public.ka_gochara_near_miss_search s WHERE s.chart_id=p_chart AND s.generation=p_generation)
       OR EXISTS(SELECT 1 FROM public.ka_gochara_near_miss n WHERE n.chart_id=p_chart AND n.generation=p_generation)
       OR EXISTS(SELECT 1 FROM public.ka_gochara_search_path_pin p WHERE p.chart_id=p_chart AND p.generation=p_generation
                   AND p.disposition='included' AND p.rule_version='1.2.0') THEN
      RETURN QUERY SELECT 'near_miss_layer_unpinned'::text, 'stored layer or final-rules grain has no manifest layer version'::text;
    END IF;
    RETURN; -- legacy/off: never require a new attestation on a historical generation
  END IF;
  IF pin IS DISTINCT FROM '1'::jsonb THEN
    RETURN QUERY SELECT 'near_miss_layer_version'::text, 'unsupported manifest layer version'::text;
    RETURN;
  END IF;
  RETURN QUERY SELECT 'near_miss_unsearched'::text, o.agent||'/'||o.relation||'/'||o.target
    FROM public.ka_gochara_search_obligation o
    WHERE o.chart_id=p_chart AND o.generation=p_generation AND o.relation IN ('aspect','conjunction') AND o.target LIKE 'point:%'
      AND o.agent <> 'moon' AND o.agent NOT LIKE 'period_lord:%'
      AND EXISTS(SELECT 1 FROM public.ka_gochara_search_path_pin p WHERE
        (p.chart_id,p.generation,p.event_class,p.path_id,p.rule_version)=(o.chart_id,o.generation,o.event_class,o.path_id,o.rule_version)
        AND p.disposition='included')
      AND NOT EXISTS(SELECT 1 FROM public.ka_gochara_near_miss_search s JOIN public.ka_gochara_near_miss_object b USING(near_miss_object_id)
        WHERE s.chart_id=p_chart AND s.generation=p_generation AND b.body=o.agent AND b.relation_kind=o.relation AND b.canonical_target=o.target);
  RETURN QUERY SELECT 'near_miss_search_incomplete'::text, s.near_miss_object_id::text
    FROM public.ka_gochara_near_miss_search s WHERE s.chart_id=p_chart AND s.generation=p_generation
      AND (NOT s.searched_complete OR s.horizon IS DISTINCT FROM h OR s.layer_version<>1);
  RETURN QUERY SELECT CASE WHEN s.near_miss_count > count(n.*) THEN 'near_miss_reported_not_stored' ELSE 'near_miss_stored_not_reported' END,
      s.near_miss_object_id::text
    FROM public.ka_gochara_near_miss_search s LEFT JOIN public.ka_gochara_near_miss n
      ON (n.chart_id,n.generation,n.near_miss_object_id)=(s.chart_id,s.generation,s.near_miss_object_id)
    WHERE s.chart_id=p_chart AND s.generation=p_generation GROUP BY s.near_miss_object_id,s.near_miss_count
    HAVING s.near_miss_count<>count(n.*);
  RETURN QUERY SELECT 'near_miss_unsearched'::text, n.near_miss_id::text FROM public.ka_gochara_near_miss n
    WHERE n.chart_id=p_chart AND n.generation=p_generation AND NOT EXISTS(SELECT 1 FROM public.ka_gochara_near_miss_search s
      WHERE (s.chart_id,s.generation,s.near_miss_object_id)=(n.chart_id,n.generation,n.near_miss_object_id));
  IF NOT EXISTS(SELECT 1 FROM public.ka_gochara_near_miss_verification v WHERE v.chart_id=p_chart AND v.generation=p_generation) THEN
    RETURN QUERY SELECT 'near_miss_verification_missing'::text, 'independent ephemeris stage has not persisted a digest'::text;
  ELSIF NOT EXISTS(SELECT 1 FROM public.ka_gochara_near_miss_verification v WHERE v.chart_id=p_chart AND v.generation=p_generation
                   AND v.layer_version=1 AND v.near_miss_digest=public.ka_gochara_near_miss_digest(p_chart,p_generation)) THEN
    RETURN QUERY SELECT 'near_miss_verification_stale'::text, 'stored near-miss state differs from independent verification'::text;
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_candidate_gate_violations(p_chart uuid, p_generation text)
RETURNS TABLE (event_class text, path_id text, rule_version text, violation text, detail text)
LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT c.event_class, NULL::text, NULL::text, c.violation, c.detail
  FROM public.ka_gochara_search_completeness_violations(p_chart, p_generation) c
  UNION ALL
  SELECT w.event_class, w.path_id, w.rule_version, w.violation, w.detail
  FROM public.ka_gochara_window_verification_violations(p_chart, p_generation) w
  UNION ALL
  SELECT '*'::text,NULL::text,NULL::text,n.violation,n.detail
  FROM public.ka_gochara_near_miss_violations(p_chart,p_generation) n;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_brief_state_digest(p_chart uuid, p_generation text)
RETURNS text LANGUAGE plpgsql STABLE
SET search_path = pg_catalog, public SET TimeZone = 'UTC' SET DateStyle = 'ISO, YMD' SET IntervalStyle = 'iso_8601' SET extra_float_digits = 1
AS $$
DECLARE t text; acc text := ''; n bigint; h text; pub record; legacy bigint;
BEGIN
  -- every row (every column but created_at) of the output, the search inputs and BOTH verification tables, one canonical line per row
  FOREACH t IN ARRAY ARRAY[
      'ka_gochara_relationship_record', 'ka_gochara_record_prerequisite', 'ka_gochara_contact', 'ka_gochara_eval_window',
      'ka_gochara_eval_window_record', 'ka_gochara_search_path_pin', 'ka_gochara_search_inventory',
      'ka_gochara_search_input_snapshot', 'ka_gochara_search_obligation', 'ka_gochara_search_interval',
      'ka_gochara_eval_window_verification', 'ka_gochara_search_inventory_verification'] LOOP
    -- (R13-2 cost review) a hash PER ROW, aggregated in hash order: the aggregate holds 65 bytes a row instead of the row's whole JSON text
    -- and no collation decides the order. This REDUCES the field-size risk (the 1 GB value limit is reached at ~15 million rows of one table
    -- and generation, independent of row width) — it does not remove it
    EXECUTE format('SELECT count(*), coalesce(encode(sha256(convert_to(string_agg(h, E''\n'' ORDER BY h COLLATE "C"), ''UTF8'')), ''hex''), '''') '
                   'FROM (SELECT encode(sha256(convert_to((to_jsonb(x) - ''created_at'')::text, ''UTF8'')), ''hex'') AS h '
                   'FROM public.%I x WHERE x.chart_id = $1 AND x.generation = $2) s', t)
      INTO n, h USING p_chart, p_generation;
    acc := acc || t || ':' || n || ':' || h || E'\n';
  END LOOP;
  -- the BUILD coverage partitions (the on-demand Moon kinds are not part of a governed generation's build identity)
  SELECT count(*), coalesce(encode(sha256(convert_to(string_agg(rh, E'\n' ORDER BY rh COLLATE "C"), 'UTF8')), 'hex'), '')
    INTO n, h
  FROM (SELECT encode(sha256(convert_to((to_jsonb(c) - 'created_at')::text, 'UTF8')), 'hex') AS rh FROM public.kala_gochara_coverage c
        WHERE c.chart_id = p_chart AND c.generation = p_generation AND c.partition_kind IN ('body_target', 'event_class')) s;
  acc := acc || 'coverage:' || n || ':' || h || E'\n';
  -- the manifest's IDENTITY (never its publication fields: status / digest / counts — publication fills those in)
  SELECT p.manifest_id::text AS manifest_id, p.horizon::text AS horizon, p.convention_id AS convention_id,
         p.input_generation_vector::text AS vector, p.writer_asset_id AS writer, p.ephemeris_backend::text AS backend INTO pub
  FROM public.kala_gochara_publication p WHERE p.chart_id = p_chart AND p.generation = p_generation;
  acc := acc || 'manifest:' || coalesce(pub.manifest_id, '') || ':' || coalesce(pub.horizon, '') || ':' || coalesce(pub.convention_id::text, '')
         || ':' || coalesce(pub.vector, '') || ':' || coalesce(pub.writer, '') || ':' || coalesce(pub.backend, '') || E'\n';
  SELECT coalesce(sum(l.n), 0) INTO legacy FROM public.ka_gochara_legacy_projection_rows(p_chart, p_generation) l;
  acc := acc || 'legacy:' || legacy || E'\n';
  -- P06b begin: version-gated near-miss state (FB-28)
  IF EXISTS(SELECT 1 FROM public.kala_gochara_publication p WHERE p.chart_id=p_chart AND p.generation=p_generation
              AND p.input_generation_vector ? 'near_miss_layer_version') THEN
    acc := acc || 'near_miss:' || public.ka_gochara_near_miss_digest(p_chart,p_generation) || E'\nverification:' ||
      coalesce((SELECT (to_jsonb(v)-'created_at')::text FROM public.ka_gochara_near_miss_verification v
                WHERE v.chart_id=p_chart AND v.generation=p_generation),'') || E'\n';
  END IF;
  -- P06b end
  RETURN encode(sha256(convert_to(acc, 'UTF8')), 'hex');
END;
$$;

-- 1240's existing seal trigger calls its window half directly. The new UNION alone
-- is insufficient: put the SAME near-miss predicate on the actual seal table too.
CREATE FUNCTION public.ka_gochara_near_miss_seal_guard() RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, public AS $$
DECLARE failures text;
BEGIN
  PERFORM public.ka_gochara_lock_chart(NEW.chart_id);
  PERFORM public.ka_gochara_lock_global_shared();
  SELECT string_agg(v.violation||':'||v.detail, E'\n') INTO failures
    FROM public.ka_gochara_near_miss_violations(NEW.chart_id,NEW.generation) v;
  IF failures IS NOT NULL THEN RAISE EXCEPTION 'near-miss seal refused: %',failures; END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER ka_gochara_generation_seal_0_near_miss BEFORE INSERT ON public.ka_gochara_generation_seal
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_near_miss_seal_guard();

REVOKE ALL ON public.ka_gochara_near_miss_verification FROM PUBLIC;
DO $$
DECLARE r text; f text;
BEGIN
  FOREACH r IN ARRAY ARRAY['data_plane_builder','gochara_verifier','gochara_sealer'] LOOP
    IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=r) THEN CONTINUE; END IF;
    EXECUTE format('GRANT SELECT ON public.ka_gochara_near_miss_verification TO %I',r);
    FOREACH f IN ARRAY ARRAY['ka_gochara_near_miss_digest(uuid,text)',
      'ka_gochara_near_miss_violations(uuid,text)'] LOOP
      EXECUTE format('GRANT EXECUTE ON FUNCTION public.%s TO %I',f,r);
    END LOOP;
  END LOOP;
  IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='gochara_verifier') THEN
    GRANT INSERT,DELETE ON public.ka_gochara_near_miss_verification TO gochara_verifier;
  END IF;
END;
$$;
REVOKE EXECUTE ON FUNCTION public.ka_gochara_near_miss_digest(uuid,text),
  public.ka_gochara_near_miss_violations(uuid,text),public.ka_gochara_near_miss_seal_guard() FROM PUBLIC;

-- FB-28 post-apply catalogue invariants. Fail inside migrate.ts's transaction.
DO $$
DECLARE r text;
BEGIN
  IF (SELECT count(*) FROM pg_trigger WHERE tgrelid='public.ka_gochara_near_miss_verification'::regclass AND NOT tgisinternal) <> 3
    OR NOT EXISTS(SELECT 1 FROM pg_trigger WHERE tgrelid='public.ka_gochara_generation_seal'::regclass
                   AND tgname='ka_gochara_generation_seal_0_near_miss' AND tgenabled='O') THEN
    RAISE EXCEPTION '1381 post-apply: near-miss verification/seal guards missing';
  END IF;
  FOREACH r IN ARRAY ARRAY['data_plane_builder','gochara_sealer'] LOOP
    IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname=r) AND
      (has_table_privilege(r,'public.ka_gochara_near_miss_verification','INSERT') OR
       has_table_privilege(r,'public.ka_gochara_near_miss_verification','DELETE') OR
       has_table_privilege(r,'public.ka_gochara_near_miss_verification','UPDATE') OR
       has_table_privilege(r,'public.ka_gochara_near_miss_verification','TRUNCATE')) THEN
      RAISE EXCEPTION '1381 post-apply: % can write verifier-owned near-miss evidence',r;
    END IF;
  END LOOP;
END;
$$;

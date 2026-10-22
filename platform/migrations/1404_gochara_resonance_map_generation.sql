-- 1404_gochara_resonance_map_generation.sql
--
-- SR-K9-RESONANCE-MAP, branch B (reader measurement verdict READ). Transaction ownership belongs to platform/scripts/migrate.ts
-- (no BEGIN/COMMIT here). Additive: one column, one widened unique key, one view, grants on the view, two registry statements.
-- No DROP or DELETE of data (the only DROP is the superseded 4-column unique constraint, a rule, not rows). The single UPDATE of rows only sets generation.
--
-- WHY. gochara_resonance_map has no generation column. ka_gochara_resonance's legacy path deletes and re-inserts the WHOLE chart, so a K9
-- candidate rebuild rewrote the rows that three MCP tools (gochara_activation_get / gochara_forecast_get / gochara_election_avoidance_get,
-- through computeGocharaCoverage), the ka_gochara / ka_gochara_v3_century_materialize / ka_kshetra writers and the permission-curve route read
-- while serving. A failed run could not give them back, and teardown could not tell the run's rows from the served ones.
--
-- WHAT.
--  1. generation text NOT NULL DEFAULT 'legacy'. 'legacy' stays the partition a run bound to no candidate writes (the same convention as
--     the other unlinked candidate tables, rebuild_control.UNLINKED_CANDIDATE_TABLES).
--  2. The rows that exist when the column is added are STAMPED with their MEASURED producing generation (rule below), never blindly 'legacy'.
--  3. UNIQUE (chart_id, generation, event_class, target_type, target_ref) replaces the 4-column key (looked up in pg_constraint, never by
--     its generated name); index on (chart_id, generation); CHECK (generation <> '').
--  4. View gochara_resonance_map_served: the one served-rows definition every serving reader uses (see SERVED below). Owner-rights view
--     (not security_invoker): readers need SELECT on the view only. SELECT is granted to every grantee that holds SELECT on the base table.
--  5. asset_registry.count_sql of ka_gochara_resonance counts the served view (cockpit truth, N.4); its output-digest spec is replaced.
--     INTERPRETATION (I): the measurement report (section 5.1.5) pointed the digest at the served view. A digest is the writer's OUTPUT
--     receipt; a candidate run writes a generation the served view does not show, so a served-view digest would read the same before and
--     after the run (a proxy, N.8). The replacement spec digests the base table with generation as a key and value column, as 1399 did for
--     ka_yojaka: every generation of the pinned chart enters the digest. Alternative: the served view (rejected above).
--     spec_sha256 6e2fce6b... was computed with the real pipeline.orchestrator.provenance.canonical_digest, which reproduces 901's recorded
--     06beb342... for the 901 spec; the spec passes the real output_digest._validate_spec.
--     INTERPRETATION (I): the value columns are 901's plus generation; 1080's two columns stay out, as in 901 (a separate gap, not this item).
--  6. integrity_check_sql (migrations 670, 1230) is NOT changed: each conjunct is a NOT EXISTS over rows of every generation (or a set-valued
--     existence test), so it stays true or false for the right reason when candidate rows sit beside the served ones.
--
-- SERVED (the definition behind the view; an INTERPRETATION, alternative = a `served` boolean flipped by publication, rejected as larger):
--   the chart's generation is the first of
--     (a) kala_layer_head.generation, when gochara_resonance_map holds rows of that generation for the chart;
--     (b) else the most recently created kala_layer_candidate in state 'published' that holds rows for the chart (a published rebuild that did
--         not run the resonance writer keeps serving the last published resonance rows instead of going empty: N.6.3);
--     (c) else 'legacy'.
--   A chart whose rows are all in unpublished generations therefore serves nothing from them, which is the point.
--
-- BACKFILL (measured rule, deterministic, refuses on ambiguity). Runs ONLY in the statement that adds the column (a re-run finds the column
-- and stamps nothing, so rows written later as 'legacy' are never re-stamped). For each chart, for each distinct computed_at value t of its rows:
--   producers(t) = the build_run_assets rows of asset ka_gochara_resonance, state 'complete', started_at and ended_at set, with
--                  started_at <= t <= ended_at, of a build_runs row of the SAME chart.
--   The writer inserts in the orchestrator's transaction, so computed_at (now(), the transaction start) lies inside [started_at, ended_at]
--   (equal to started_at when asset start and writer share the transaction).
--   outcome(t) = 'legacy'      when producers(t) is empty (the build record is absent: unmeasured, kept as served today);
--                the candidate's generation when exactly one producer exists AND a kala_layer_candidate with build_id = that run exists in state
--                'published' (the only candidates whose rows were ever promoted to serve);
--                'legacy'      when exactly one producer exists but it has no candidate (an ordinary rebuild) or its candidate is not
--                published (the rows were live before this change and stay served as they are; stamping them with an unpublished generation
--                would hide them from the served view);
--                AMBIGUOUS     when two or more producers match t.
--   A chart is AMBIGUOUS also when its distinct t values have different outcomes. Any ambiguous chart RAISES by name and nothing is changed.
--
-- MEASUREMENT (local disposable fixture, tests/l3/kala_db/manifest/test_resmap_generation_migration.py, which applies THIS file):
--   * published candidate window match            -> rows stamped with the candidate generation (O4)
--   * ordinary-run window, unpublished candidate, no window -> stay 'legacy'
--   * two windows containing t / a chart with two t values of different outcome -> the migration raises, 0 rows changed
--   * re-run -> 0 rows change
--   * the real file was also applied, then rolled back, on the locally migrated schema `ky_b1` (1,011 real migrations applied; 0 resonance rows, no
--     build records, no current digest spec): it applies twice without error and leaves nothing behind after the rollback.
--   Production row counts and the production match were NOT measured (no production access by design, R-2026-10-15-01). The migration
--   prints the per-outcome counts as NOTICE lines when it runs; the cockpit reads them from the migration log.
--
-- DEPLOY ORDER. The code that writes the new key (services/ka_gochara_resonance/writer.py) and the code that reads the view ship in the same
-- PR as this file. The routine runner applies migrations before the sidecar and platform-mcp deploys; a ka_gochara_resonance run that
-- straddles the migration fails on the changed unique key (ON CONFLICT target) and is re-run: it writes nothing partial (transaction + savepoint).
--
-- GUARDS. lock_timeout / statement_timeout below. Every precondition RAISES by name. Not a silent no-op.
--
-- NOT PROTECTED. Public-schema DDL: the cockpit decides its protected-migration listing; this file does not edit one.
--
-- ROLLBACK (not executed by migrate.ts; legal only while every row is still generation 'legacy' for its chart):
--   DROP VIEW IF EXISTS gochara_resonance_map_served;
--   ALTER TABLE gochara_resonance_map DROP CONSTRAINT gochara_resonance_map_chart_generation_key;
--   ALTER TABLE gochara_resonance_map ADD UNIQUE (chart_id, event_class, target_type, target_ref);
--   ALTER TABLE gochara_resonance_map DROP COLUMN generation;
--   (and restore count_sql and the 901 digest spec)

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

DO $m1404a$
DECLARE
  v_had_col   boolean;
  v_total     bigint;
  v_candidate bigint := 0;
  v_unmeasured bigint := 0;
  v_ordinary  bigint := 0;
  v_unpublished bigint := 0;
  v_ambiguous text;
  v_measure   text;
  v_stamped   bigint := 0;
  v_after     bigint;
  v_old       record;
  v_cols      text[] := ARRAY['chart_id','event_class','target_type','target_ref'];
BEGIN
  IF to_regclass('gochara_resonance_map') IS NULL THEN
    RAISE EXCEPTION '1404: gochara_resonance_map does not exist; nothing was changed';
  END IF;
  IF to_regclass('kala_layer_head') IS NULL OR to_regclass('kala_layer_candidate') IS NULL THEN
    RAISE EXCEPTION '1404: kala_layer_head / kala_layer_candidate (migration 1330) are required by the served view; nothing was changed';
  END IF;
  IF to_regclass('build_runs') IS NULL OR to_regclass('build_run_assets') IS NULL THEN
    RAISE EXCEPTION '1404: build_runs / build_run_assets are required to measure the producing generation; nothing was changed';
  END IF;

  SELECT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema = current_schema() AND table_name = 'gochara_resonance_map' AND column_name = 'generation')
    INTO v_had_col;

  IF NOT v_had_col THEN
    SELECT count(*) INTO v_total FROM gochara_resonance_map;

    -- Measure BEFORE any change: the outcome per (chart, computed_at). One statement text, used for the refusal check, the counts and the stamp
    -- (no temporary table: the migration role needs no TEMP privilege).
    v_measure := $q$
      WITH rows_t AS (
        SELECT chart_id, computed_at AS t, count(*) AS n FROM gochara_resonance_map GROUP BY chart_id, computed_at
      ), producers AS (
        SELECT r.chart_id, r.t, r.n, b.id AS run_id, c.generation, c.state AS cand_state
          FROM rows_t r
          JOIN build_runs b ON b.chart_id = r.chart_id
          JOIN build_run_assets a ON a.run_id = b.id
                                 AND a.asset_id = 'ka_gochara_resonance' AND a.state = 'complete'
                                 AND a.started_at IS NOT NULL AND a.ended_at IS NOT NULL
                                 AND r.t BETWEEN a.started_at AND a.ended_at
          LEFT JOIN kala_layer_candidate c ON c.build_id = b.id AND c.chart_id = b.chart_id
      )
      SELECT r.chart_id, r.t, r.n,
             CASE WHEN count(p.run_id) = 0 THEN 'no_window'
                  WHEN count(p.run_id) > 1 THEN 'ambiguous'
                  WHEN max(p.cand_state) = 'published' THEN 'candidate'
                  WHEN max(p.generation) IS NULL THEN 'ordinary_run'
                  ELSE 'unpublished_candidate' END AS kind,
             CASE WHEN count(p.run_id) = 1 AND max(p.cand_state) = 'published' THEN max(p.generation) ELSE 'legacy' END AS generation
        FROM rows_t r LEFT JOIN producers p ON p.chart_id = r.chart_id AND p.t = r.t
       GROUP BY r.chart_id, r.t, r.n
    $q$;

    EXECUTE 'SELECT string_agg(chart_id::text, '', '' ORDER BY chart_id) FROM (SELECT chart_id FROM (' || v_measure || ') m '
            || 'GROUP BY chart_id HAVING bool_or(kind = ''ambiguous'') OR count(DISTINCT generation) > 1 LIMIT 10) x' INTO v_ambiguous;
    IF v_ambiguous IS NOT NULL THEN
      RAISE EXCEPTION '1404: the producing generation of the existing gochara_resonance_map rows is ambiguous for chart(s) % (two producers match one computed_at, or one chart''s rows have different producers); refusing to guess; nothing was changed', v_ambiguous;
    END IF;

    EXECUTE 'SELECT coalesce(sum(n) FILTER (WHERE kind = ''candidate''), 0), coalesce(sum(n) FILTER (WHERE kind = ''no_window''), 0), '
            || 'coalesce(sum(n) FILTER (WHERE kind = ''ordinary_run''), 0), coalesce(sum(n) FILTER (WHERE kind = ''unpublished_candidate''), 0) '
            || 'FROM (' || v_measure || ') m' INTO v_candidate, v_unmeasured, v_ordinary, v_unpublished;

    ALTER TABLE gochara_resonance_map ADD COLUMN generation text NOT NULL DEFAULT 'legacy';

    EXECUTE 'UPDATE gochara_resonance_map m SET generation = o.generation FROM (' || v_measure || ') o '
            || 'WHERE m.chart_id = o.chart_id AND m.computed_at = o.t AND o.kind = ''candidate''';
    GET DIAGNOSTICS v_stamped = ROW_COUNT;
    IF v_stamped <> v_candidate THEN
      RAISE EXCEPTION '1404: stamped % row(s) but the measurement matched %; nothing was changed', v_stamped, v_candidate;
    END IF;
    SELECT count(*) INTO v_after FROM gochara_resonance_map;
    IF v_after <> v_total THEN
      RAISE EXCEPTION '1404: row count changed from % to % while stamping; nothing was changed', v_total, v_after;
    END IF;
    RAISE NOTICE '1404 backfill: % row(s) total; stamped with a published candidate generation: %; left legacy because no build window matched: %; left legacy (ordinary run): %; left legacy (candidate not published): %',
      v_total, v_candidate, v_unmeasured, v_ordinary, v_unpublished;
  ELSE
    RAISE NOTICE '1404: the generation column already exists; no row was stamped';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'gochara_resonance_map'::regclass AND conname = 'gochara_resonance_map_generation_nonempty') THEN
    ALTER TABLE gochara_resonance_map ADD CONSTRAINT gochara_resonance_map_generation_nonempty CHECK (generation <> '');
  END IF;

  -- The widened unique key first, then the 4-column key it supersedes (looked up by its columns, never by name).
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'gochara_resonance_map'::regclass AND conname = 'gochara_resonance_map_chart_generation_key') THEN
    ALTER TABLE gochara_resonance_map
      ADD CONSTRAINT gochara_resonance_map_chart_generation_key UNIQUE (chart_id, generation, event_class, target_type, target_ref);
  END IF;
  FOR v_old IN
    SELECT con.oid, con.conname, con.conindid
      FROM pg_constraint con
     WHERE con.conrelid = 'gochara_resonance_map'::regclass AND con.contype = 'u'
       AND (SELECT array_agg(a.attname::text ORDER BY a.attname) FROM unnest(con.conkey) k(attnum)
              JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.attnum)
           = (SELECT array_agg(c ORDER BY c) FROM unnest(v_cols) c)
  LOOP
    IF EXISTS (SELECT 1 FROM pg_constraint f WHERE f.contype = 'f' AND f.confrelid = 'gochara_resonance_map'::regclass AND f.conindid = v_old.conindid) THEN
      RAISE EXCEPTION '1404: a foreign key depends on the superseded unique constraint %; nothing was changed', v_old.conname;
    END IF;
    EXECUTE format('ALTER TABLE gochara_resonance_map DROP CONSTRAINT %I', v_old.conname);
  END LOOP;

  CREATE INDEX IF NOT EXISTS idx_gochara_resonance_chart_generation ON gochara_resonance_map (chart_id, generation);

  COMMENT ON COLUMN gochara_resonance_map.generation IS
    'Migration 1404: the K9 candidate generation that wrote the row; ''legacy'' for a run bound to no candidate. Serving reads gochara_resonance_map_served.';
END
$m1404a$;

-- The served-rows definition (see SERVED in the header).
CREATE OR REPLACE VIEW gochara_resonance_map_served AS
SELECT m.id, m.chart_id, m.generation, m.event_class, m.target_type, m.target_ref, m.weight,
       m.classical_citation, m.uncited_extension, m.source_rule_id, m.computed_at,
       m.target_resolution_state, m.target_qualifier
  FROM gochara_resonance_map m
  JOIN LATERAL (
    SELECT coalesce(
      (SELECT h.generation FROM kala_layer_head h
        WHERE h.chart_id = m.chart_id
          AND EXISTS (SELECT 1 FROM gochara_resonance_map x WHERE x.chart_id = h.chart_id AND x.generation = h.generation)),
      (SELECT c.generation FROM kala_layer_candidate c
        WHERE c.chart_id = m.chart_id AND c.state = 'published'
          AND EXISTS (SELECT 1 FROM gochara_resonance_map x WHERE x.chart_id = c.chart_id AND x.generation = c.generation)
        ORDER BY c.created_at DESC, c.generation DESC LIMIT 1),
      'legacy') AS generation
  ) s ON s.generation = m.generation;

COMMENT ON VIEW gochara_resonance_map_served IS
  'Migration 1404: the rows of gochara_resonance_map that serving reads: the chart head generation when it holds rows, else the latest published '
  'generation that does, else legacy. A K9 candidate generation is never visible here until it is published.';

-- SELECT on the view for every grantee that holds SELECT on the base table (PUBLIC included); idempotent.
DO $m1404b$
DECLARE
  v_grantee oid;
  v_name    text;
BEGIN
  FOR v_grantee IN
    SELECT DISTINCT a.grantee
      FROM pg_class c, aclexplode(c.relacl) a
     WHERE c.oid = 'gochara_resonance_map'::regclass AND a.privilege_type = 'SELECT'
  LOOP
    IF v_grantee = 0 THEN
      GRANT SELECT ON gochara_resonance_map_served TO PUBLIC;
    ELSE
      v_name := (SELECT rolname FROM pg_roles WHERE oid = v_grantee);
      IF v_name IS NOT NULL AND v_name <> current_user THEN
        EXECUTE format('GRANT SELECT ON gochara_resonance_map_served TO %I', v_name);
      END IF;
    END IF;
  END LOOP;
END
$m1404b$;

-- Registry: count_sql counts the served rows; the output digest spec covers every generation.
DO $m1404c$
DECLARE
  v_old_count constant text := 'SELECT COUNT(*) FROM gochara_resonance_map WHERE chart_id=$1';
  v_new_count constant text := 'SELECT COUNT(*) FROM gochara_resonance_map_served WHERE chart_id=$1';
  v_old_sha   constant text := '06beb342ce8c3a88cf0df7d8d7a489abb99db40b520979d6ac9783a61970dd0a';
  v_new_sha   constant text := '6e2fce6b78ae20036ee147876b8d199e1bffa89e3f7694e318319d2cccbaf34d';
  v_new_spec  constant jsonb := '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"gochara_resonance_map","relation":"gochara_resonance_map","where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","generation","event_class","target_type","target_ref"],"value_columns":["chart_id","generation","event_class","target_type","target_ref","weight","classical_citation","uncited_extension","source_rule_id"]}]}'::jsonb;
  v_cur       text;
  v_changed   integer;
  v_cur_specs integer;
  v_old_specs integer;
  v_new_specs integer;
BEGIN
  SELECT count_sql INTO v_cur FROM asset_registry WHERE asset_id = 'ka_gochara_resonance' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION '1404: ka_gochara_resonance has no asset_registry row; nothing was changed';
  END IF;
  IF v_cur IS DISTINCT FROM v_old_count AND v_cur IS DISTINCT FROM v_new_count THEN
    RAISE EXCEPTION '1404: ka_gochara_resonance count_sql is neither the 459 text nor this migration''s (%); refusing to overwrite; nothing was changed', coalesce(v_cur, 'NULL');
  END IF;
  IF v_cur = v_old_count THEN
    UPDATE asset_registry SET count_sql = v_new_count WHERE asset_id = 'ka_gochara_resonance' AND count_sql = v_old_count;
    GET DIAGNOSTICS v_changed = ROW_COUNT;
    IF v_changed <> 1 THEN
      RAISE EXCEPTION '1404: expected to update exactly one asset_registry row, updated %', v_changed;
    END IF;
  END IF;

  SELECT count(*) FILTER (WHERE retired_at IS NULL),
         count(*) FILTER (WHERE retired_at IS NULL AND spec_sha256 = v_old_sha),
         count(*) FILTER (WHERE retired_at IS NULL AND spec_sha256 = v_new_sha)
    INTO v_cur_specs, v_old_specs, v_new_specs
    FROM asset_output_digest_specs WHERE asset_id = 'ka_gochara_resonance';
  -- No current spec at all (a database whose spec registry was never seeded with 901): the replacement is inserted as the current one.
  -- A current spec that is neither 901's nor this migration's is a spec someone else owns: refuse, change nothing.
  IF v_cur_specs > 1 OR (v_cur_specs = 1 AND (v_old_specs + v_new_specs) <> 1) THEN
    RAISE EXCEPTION '1404: the live ka_gochara_resonance digest spec is neither the 901 spec nor this migration''s (% current rows, % matching 901, % matching the new spec)', v_cur_specs, v_old_specs, v_new_specs;
  END IF;
  IF v_cur_specs = 0 THEN
    RAISE NOTICE '1404: ka_gochara_resonance had no current digest spec; the replacement is recorded as the current one';
  END IF;
  IF v_old_specs = 1 THEN
    UPDATE asset_output_digest_specs SET retired_at = now()
     WHERE asset_id = 'ka_gochara_resonance' AND spec_sha256 = v_old_sha AND retired_at IS NULL;
  END IF;
  IF v_new_specs = 0 THEN
    INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
    VALUES ('ka_gochara_resonance', v_new_sha, v_new_spec)
    ON CONFLICT (asset_id, spec_sha256) DO NOTHING;
  END IF;

  SELECT count(*) INTO v_cur_specs FROM asset_output_digest_specs
   WHERE asset_id = 'ka_gochara_resonance' AND retired_at IS NULL AND spec_sha256 = v_new_sha;
  IF v_cur_specs <> 1 THEN
    RAISE EXCEPTION '1404: the replacement ka_gochara_resonance digest spec is not the single current row';
  END IF;
  IF (SELECT count_sql FROM asset_registry WHERE asset_id = 'ka_gochara_resonance') IS DISTINCT FROM v_new_count THEN
    RAISE EXCEPTION '1404: count_sql was not updated';
  END IF;
END
$m1404c$;

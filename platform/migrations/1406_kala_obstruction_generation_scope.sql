-- 1406_kala_obstruction_generation_scope.sql   (NUMBER NOT ALLOCATED: the cockpit allocates and places this file)
--
-- SR-K9-WRITE-SCOPE, item k9-obstruction-scope (branch B).  Transaction ownership belongs to platform/scripts/migrate.ts.
-- Additive / guarded / idempotent: no table is dropped, no row is deleted or rewritten.
--
-- Why.  ka_vighnakara now writes a candidate-bound build's rows under the CANDIDATE generation and leaves the served rows (the
-- legacy NULL partition and the published head's generation) untouched.  Four registry/schema facts still assume ONE partition:
--
--  1. The cascade route.  kala_obstruction.convergence_id REFERENCES kala_convergence(convergence_id) ON DELETE CASCADE (migration
--     245).  ka_sangam deletes the whole chart's kala_convergence (ka_sangam.py first executing substep), so every K9 rebuild would
--     delete the SERVED obstruction rows through the cascade, outside any plan scope.  The action becomes ON DELETE SET NULL: the
--     rows survive (convergence_id NULL), and the ka_vighnakara integrity contract (migration 670, clause (e): a NULL-convergence
--     row must be a dasha-anchored one) turns the loss of the link into a RED check instead of a silent emptying.
--     (I) INTERPRETATION; alternative: ON DELETE RESTRICT, which would make ka_sangam's own whole-chart delete fail for every
--     ordinary rebuild.  kala_convergence itself is NOT changed here (separate lane).
--  2. integrity_check_sql (migration 670, ka_vighnakara, clause (a)) counts duplicates per (chart, convergence_id, type) over the
--     WHOLE table: with a served partition and a candidate partition both holding the same windows it would read FALSE and roll the
--     candidate build back.  The two GROUP BY lists gain `generation`.  asset_runner.py is FROZEN; only the registry text changes.
--  3. count_sql counted every row of the chart; it now counts the SERVED partition (the head's generation when it holds rows, else
--     the legacy NULL partition), the same rule as services/kala_core/served_generation.py.
--  4. The output digest spec (1212) hashed every row of the chart regardless of partition.  It is replaced by a two-component spec:
--     the legacy partition (generation IS NULL) and every non-NULL generation, keyed on generation.  The registry allows ONE current
--     spec per asset, so the 1212 row is RETIRED (not edited, not deleted), as 1399 did for ka_yojaka.  KNOWN LIMIT: a sealed
--     negative-space row (K3-2) has a NULL signal_id; the digest's NULL-key preflight refuses it (fail closed).  No plan writer
--     emits such a row.
--
-- Rollback (not executed by migrate.ts): restore the FK with ON DELETE CASCADE; UPDATE asset_registry back to the pre-image texts
-- (migration 670's integrity text, the seed count_sql 'SELECT count(*) FROM kala_obstruction WHERE chart_id = $1'); un-retire the 1212
-- spec and retire the new one.
--
-- PLACEMENT: replace every '1406' in this file (messages only) with the allocated number before it is placed under platform/migrations/.
-- The migration refuses (RAISE) when the live count_sql is not the seed text: read the live text before applying.

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

DO $runs$
DECLARE n_active int;
BEGIN
  SELECT count(*) INTO n_active
    FROM build_runs r JOIN build_run_assets a ON a.run_id = r.id
   WHERE a.asset_id = 'ka_vighnakara' AND r.state NOT IN ('completed', 'failed', 'stopped');
  IF n_active > 0 THEN
    RAISE EXCEPTION '1406: % active build run(s) for ka_vighnakara; refusing to change its registry contracts under a running build', n_active;
  END IF;
END
$runs$;

-- 1. the cascade route --------------------------------------------------------------------------------------------------------
DO $fk$
DECLARE v_name text; v_action "char";
BEGIN
  SELECT con.conname, con.confdeltype INTO v_name, v_action
    FROM pg_constraint con
    JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = ANY (con.conkey)
   WHERE con.contype = 'f' AND con.conrelid = 'public.kala_obstruction'::regclass
     AND con.confrelid = 'public.kala_convergence'::regclass AND a.attname = 'convergence_id' AND array_length(con.conkey, 1) = 1;
  IF v_name IS NULL THEN
    RAISE EXCEPTION '1406: kala_obstruction.convergence_id has no foreign key to kala_convergence';
  END IF;
  IF v_action = 'n' THEN
    RAISE NOTICE '1406: % is already ON DELETE SET NULL; nothing to do', v_name;
  ELSIF v_action = 'c' THEN
    EXECUTE format('ALTER TABLE public.kala_obstruction DROP CONSTRAINT %I, ADD CONSTRAINT %I FOREIGN KEY (convergence_id) '
                   'REFERENCES public.kala_convergence (convergence_id) ON DELETE SET NULL NOT VALID', v_name, v_name);
    EXECUTE format('ALTER TABLE public.kala_obstruction VALIDATE CONSTRAINT %I', v_name);
  ELSE
    RAISE EXCEPTION '1406: % has the unexpected delete action %', v_name, v_action;
  END IF;
END
$fk$;

-- 2 + 3. registry texts, replaced only when they are exactly the pre-image this migration was written against -------------------
DO $registry$
DECLARE v_integrity text; v_count text; v_new_integrity text;
  c_old_a text := 'GROUP BY chart_id, convergence_id, obstruction_type';
  c_new_a text := 'GROUP BY chart_id, generation, convergence_id, obstruction_type';
  c_old_b text := 'GROUP BY chart_id, signal_id, obstruction_type, obstruction_detail->>''peak_date''';
  c_new_b text := 'GROUP BY chart_id, generation, signal_id, obstruction_type, obstruction_detail->>''peak_date''';
  c_old_count text := 'SELECT count(*) FROM kala_obstruction WHERE chart_id = $1';
  c_new_count text := 'SELECT count(*) FROM kala_obstruction o WHERE o.chart_id = $1 AND o.generation IS NOT DISTINCT FROM (SELECT h.generation FROM kala_layer_head h WHERE h.chart_id = o.chart_id AND EXISTS (SELECT 1 FROM kala_obstruction x WHERE x.chart_id = h.chart_id AND x.generation = h.generation))';
BEGIN
  SELECT integrity_check_sql, count_sql INTO v_integrity, v_count FROM asset_registry WHERE asset_id = 'ka_vighnakara';
  IF NOT FOUND THEN RAISE EXCEPTION '1406: ka_vighnakara is not registered'; END IF;

  IF position(c_new_a IN v_integrity) > 0 AND position(c_new_b IN v_integrity) > 0 THEN
    RAISE NOTICE '1406: the ka_vighnakara integrity check is already partition-aware';
  ELSE
    IF position(c_old_a IN v_integrity) = 0 OR position(c_old_b IN v_integrity) = 0 THEN
      RAISE EXCEPTION '1406: the live ka_vighnakara integrity_check_sql is not the migration 670 text (accretion clause (a) not found)';
    END IF;
    v_new_integrity := replace(replace(v_integrity, c_old_a, c_new_a), c_old_b, c_new_b);
    UPDATE asset_registry SET integrity_check_sql = v_new_integrity WHERE asset_id = 'ka_vighnakara';
  END IF;

  IF v_count = c_new_count THEN
    RAISE NOTICE '1406: the ka_vighnakara count_sql is already the served-partition count';
  ELSIF v_count = c_old_count THEN
    UPDATE asset_registry SET count_sql = c_new_count WHERE asset_id = 'ka_vighnakara';
  ELSE
    RAISE EXCEPTION '1406: the live ka_vighnakara count_sql is neither the seed text nor this migration''s: %', v_count;
  END IF;
END
$registry$;

-- 4. the output digest spec ---------------------------------------------------------------------------------------------------
DO $pre$
DECLARE v_cur int; v_old int; v_new int;
BEGIN
  SELECT count(*) INTO v_cur FROM asset_output_digest_specs WHERE asset_id = 'ka_vighnakara' AND retired_at IS NULL;
  SELECT count(*) INTO v_old FROM asset_output_digest_specs WHERE asset_id = 'ka_vighnakara' AND retired_at IS NULL
     AND spec_sha256 = 'a731cb0c49546583b12dd24f1366389b99eb695aed4142f16560cea08b88f117';
  SELECT count(*) INTO v_new FROM asset_output_digest_specs WHERE asset_id = 'ka_vighnakara' AND retired_at IS NULL
     AND spec_sha256 = '13ba8554c1972bc3a99a5b9c14d2801e55ef96481d35e8771ce42373e56dfc74';
  IF v_cur <> 1 OR (v_old + v_new) <> 1 THEN
    RAISE EXCEPTION '1406: the live ka_vighnakara digest spec is neither the 1212 spec nor this migration''s spec (% current, % matching 1212, % matching the new spec)', v_cur, v_old, v_new;
  END IF;
END
$pre$;

UPDATE asset_output_digest_specs SET retired_at = now()
 WHERE asset_id = 'ka_vighnakara' AND retired_at IS NULL
   AND spec_sha256 = 'a731cb0c49546583b12dd24f1366389b99eb695aed4142f16560cea08b88f117';

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ka_vighnakara',
  '13ba8554c1972bc3a99a5b9c14d2801e55ef96481d35e8771ce42373e56dfc74',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"kala_obstruction_legacy","relation":"kala_obstruction","key_columns":["signal_id","obstruction_type","severity_score","override_score","severity","obstruction_detail"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_is_null":["generation"],"value_columns":["chart_id","signal_id","obstruction_type","severity","severity_score","override_score","obstruction_detail"]},{"name":"kala_obstruction_candidate","relation":"kala_obstruction","key_columns":["generation","signal_id","obstruction_type","severity_score","override_score","severity","obstruction_detail"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"where_not_null":["generation"],"value_columns":["chart_id","signal_id","obstruction_type","severity","severity_score","override_score","obstruction_detail","generation"]}]}'::jsonb
)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

-- post-conditions: never trust a silent no-op ----------------------------------------------------------------------------------
DO $post$
DECLARE v_cur int; v_ok int; v_act "char"; v_integrity text; v_count text;
BEGIN
  SELECT count(*) INTO v_cur FROM asset_output_digest_specs WHERE asset_id = 'ka_vighnakara' AND retired_at IS NULL;
  SELECT count(*) INTO v_ok FROM asset_output_digest_specs WHERE asset_id = 'ka_vighnakara' AND retired_at IS NULL
     AND spec_sha256 = '13ba8554c1972bc3a99a5b9c14d2801e55ef96481d35e8771ce42373e56dfc74' AND jsonb_array_length(spec -> 'components') = 2;
  IF v_cur <> 1 OR v_ok <> 1 THEN
    RAISE EXCEPTION '1406: the new ka_vighnakara digest spec is not the single current row (% current, % matching)', v_cur, v_ok;
  END IF;
  SELECT con.confdeltype INTO v_act FROM pg_constraint con JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = ANY (con.conkey)
   WHERE con.contype = 'f' AND con.conrelid = 'public.kala_obstruction'::regclass AND con.confrelid = 'public.kala_convergence'::regclass
     AND a.attname = 'convergence_id';
  IF v_act IS DISTINCT FROM 'n' THEN RAISE EXCEPTION '1406: the convergence foreign key is not ON DELETE SET NULL (%)', v_act; END IF;
  SELECT integrity_check_sql, count_sql INTO v_integrity, v_count FROM asset_registry WHERE asset_id = 'ka_vighnakara';
  IF position('GROUP BY chart_id, generation, convergence_id, obstruction_type' IN v_integrity) = 0
     OR position('GROUP BY chart_id, generation, signal_id, obstruction_type' IN v_integrity) = 0 THEN
    RAISE EXCEPTION '1406: the ka_vighnakara integrity check is not partition-aware';
  END IF;
  IF position('x.generation = h.generation' IN v_count) = 0 THEN RAISE EXCEPTION '1406: the ka_vighnakara count_sql is not the served-partition count'; END IF;
END
$post$;

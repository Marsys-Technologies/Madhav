-- 1406_kala_obstruction_generation_scope.sql
--
-- SR-K9-WRITE-SCOPE, item k9-obstruction-scope (branch B).  Transaction ownership belongs to platform/scripts/migrate.ts.
-- Additive / guarded / idempotent: no table is dropped, no row is deleted or rewritten, no constraint is changed.
--
-- PREREQUISITE (review of #3864, fk_design = (b)).  Migration 1405 (PR #3869, the scoped ka_sangam convergence delete) MUST be applied
-- before ANY K9 run executes ka_sangam.  The foreign key kala_obstruction.convergence_id REFERENCES kala_convergence(convergence_id)
-- ON DELETE CASCADE (migration 245) is deliberately KEPT: ka_sangam's whole-chart delete of kala_convergence cascades into this table,
-- and only 1405's generation-scoped delete keeps that cascade away from the served rows.  An earlier draft of this file switched the FK
-- to ON DELETE SET NULL; that was WITHDRAWN: it left served rows with convergence_id NULL that still cite a deleted window
-- (`ka_vighnakara:v2.0:conv=<id>`), no reader can filter them out (dasha-anchored rows legitimately have convergence_id NULL), and the
-- 670 clause (e) detector then read FALSE for every later build.  This file therefore has NO ALTER TABLE.
--
-- Why.  ka_vighnakara now writes a candidate-bound build's rows under the CANDIDATE generation and leaves the served rows (the
-- legacy NULL partition and the published head's generation) untouched.  Facts that still assume ONE partition of kala_obstruction:
--
--  1. integrity_check_sql (migration 670, ka_vighnakara, clause (a)) counts duplicates per (chart, convergence_id, type) over the
--     WHOLE table: with a served partition and a candidate partition both holding the same windows it would read FALSE and roll the
--     candidate build back.  The two GROUP BY lists gain `generation`.  asset_runner.py is FROZEN; only the registry text changes.
--  2. count_sql counted every row of the chart; it now counts the SERVED partition (the head's generation when it holds rows, else
--     the legacy NULL partition), the same rule as services/kala_core/served_generation.py.
--  3. The output digest spec (1212) hashed every row of the chart regardless of partition.  It is replaced by a two-component spec:
--     the legacy partition (generation IS NULL) and every non-NULL generation, keyed on generation.  The registry allows ONE current
--     spec per asset, so the 1212 row is RETIRED (not edited, not deleted), as 1399 did for ka_yojaka.  KNOWN LIMIT: a sealed
--     negative-space row (K3-2) has a NULL signal_id; the digest's NULL-key preflight refuses it (fail closed).  No plan writer
--     emits such a row.
--  4. ph_pratikara (migration 1259, the 1:1 tiling `kala_obstruction o FULL OUTER JOIN phala_mitigation m`) read EVERY partition, but
--     ph_pratikara mitigates the SERVED partition only: one unmitigated candidate row turned its integrity FALSE during every K9
--     candidate, and after the first publish the legacy rows (never mitigated again) kept it FALSE for good.  `kala_obstruction o` is
--     scoped to the served predicate.
--  5. ka_kala_darshana's clause (e) (migration 670, live for non-fixture builds through 1356's/1375's ELSE branch) counted a window's
--     obstruction rows over every partition while its summary now mirrors the served partition only: a candidate row on a shared
--     window rolled the build back.  Both kala_obstruction subqueries of clause (e) are scoped to the served predicate.
--
-- Items 4 and 5 are guarded by md5 of the live text (1259 style): a registry text this migration was not written against is refused
-- (RAISE), never silently skipped.  Updating integrity_check_sql of ph_pratikara / ka_kala_darshana / ka_vighnakara fires the
-- registry-invalidation trigger on their freshness receipts, as every integrity edit does; no data row changes.
--
-- Rollback (not executed by migrate.ts): UPDATE asset_registry back to the pre-image texts (migration 670's ka_vighnakara integrity
-- text and the seed count_sql 'SELECT count(*) FROM kala_obstruction WHERE chart_id = $1'; the 1259 ph_pratikara text, md5 fac43b4e3117b30efb93aa87aaf80f5f;
-- the 1375 ka_kala_darshana text, md5 fbb744094d76609b31ebc82b2a265ce9); un-retire the 1212 spec and retire the new one.
--
-- PRE-APPLY READBACK (run on the target database; every value must match or the migration refuses):
--   SELECT asset_id, md5(integrity_check_sql) FROM asset_registry WHERE asset_id IN ('ph_pratikara', 'ka_kala_darshana');
--     -- ph_pratikara fac43b4e3117b30efb93aa87aaf80f5f ; ka_kala_darshana fbb744094d76609b31ebc82b2a265ce9   (already-migrated values: 557bf80f55319c2d412d3c2e91361881 ; f55e6c5d7a50dcc9f60e27c9459f4734)
--   SELECT count_sql = 'SELECT count(*) FROM kala_obstruction WHERE chart_id = $1' FROM asset_registry WHERE asset_id = 'ka_vighnakara';  -- t
--
-- The migration refuses (RAISE) when the live ka_vighnakara count_sql is not the seed text, or an active build run exists for one of
-- the three assets.

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

DO $runs$
DECLARE n_active int;
BEGIN
  SELECT count(*) INTO n_active
    FROM build_runs r JOIN build_run_assets a ON a.run_id = r.id
   WHERE a.asset_id IN ('ka_vighnakara', 'ph_pratikara', 'ka_kala_darshana') AND r.state NOT IN ('completed', 'failed', 'stopped');
  IF n_active > 0 THEN
    RAISE EXCEPTION '1406: % active build run(s) for ka_vighnakara / ph_pratikara / ka_kala_darshana; refusing to change their registry contracts under a running build', n_active;
  END IF;
END
$runs$;

-- 1 + 2. ka_vighnakara registry texts, replaced only when they are exactly the pre-image this migration was written against -------------------
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

-- 3. the output digest spec ---------------------------------------------------------------------------------------------------
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

-- 4. ph_pratikara: the tiling reads the served partition only (the 1259 text, replaced only when it is exactly that text) -----------
DO $pratikara$
DECLARE v_cur text;
  c_served text := $s$o.generation IS NOT DISTINCT FROM (SELECT h.generation FROM kala_layer_head h WHERE h.chart_id = o.chart_id AND EXISTS (SELECT 1 FROM kala_obstruction x WHERE x.chart_id = h.chart_id AND x.generation = h.generation))$s$;
  c_old text := $o$SELECT 1 FROM kala_obstruction o
      FULL OUTER JOIN phala_mitigation m ON m.obstruction_id = o.id AND m.chart_id = o.chart_id$o$;
BEGIN
  SELECT integrity_check_sql INTO v_cur FROM asset_registry WHERE asset_id = 'ph_pratikara';
  IF NOT FOUND THEN RAISE EXCEPTION '1406: ph_pratikara is not registered'; END IF;
  IF md5(v_cur) = '557bf80f55319c2d412d3c2e91361881' THEN
    RAISE NOTICE '1406: the ph_pratikara integrity check already reads the served obstruction partition';
  ELSIF md5(v_cur) = 'fac43b4e3117b30efb93aa87aaf80f5f' THEN
    UPDATE asset_registry
       SET integrity_check_sql = replace(v_cur, c_old, 'SELECT 1 FROM (SELECT * FROM kala_obstruction o WHERE ' || c_served || E') o\n      FULL OUTER JOIN phala_mitigation m ON m.obstruction_id = o.id AND m.chart_id = o.chart_id')
     WHERE asset_id = 'ph_pratikara' AND md5(integrity_check_sql) = 'fac43b4e3117b30efb93aa87aaf80f5f';
  ELSE
    RAISE EXCEPTION '1406: the live ph_pratikara integrity_check_sql is not the migration 1259 text (md5 %)', md5(v_cur);
  END IF;
  IF (SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ph_pratikara') IS DISTINCT FROM '557bf80f55319c2d412d3c2e91361881' THEN
    RAISE EXCEPTION '1406: the ph_pratikara integrity_check_sql did not take';
  END IF;
END
$pratikara$;

-- 5. ka_kala_darshana: clause (e) reads the served partition only (the 1375 text, replaced only when it is exactly that text) -----
DO $darshana$
DECLARE v_cur text;
  c_served text := $s$o.generation IS NOT DISTINCT FROM (SELECT h.generation FROM kala_layer_head h WHERE h.chart_id = o.chart_id AND EXISTS (SELECT 1 FROM kala_obstruction x WHERE x.chart_id = h.chart_id AND x.generation = h.generation))$s$;
  c_old_count text := $o$      SELECT count(*) FROM kala_obstruction o
      WHERE o.convergence_id = d.convergence_id AND o.chart_id = d.chart_id)$o$;
  c_old_match text := $o$      SELECT 1 FROM kala_obstruction o
      WHERE o.convergence_id = d.convergence_id AND o.chart_id = d.chart_id
        AND o.obstruction_type = e->>'type'$o$;
BEGIN
  SELECT integrity_check_sql INTO v_cur FROM asset_registry WHERE asset_id = 'ka_kala_darshana';
  IF NOT FOUND THEN RAISE EXCEPTION '1406: ka_kala_darshana is not registered'; END IF;
  IF md5(v_cur) = 'f55e6c5d7a50dcc9f60e27c9459f4734' THEN
    RAISE NOTICE '1406: the ka_kala_darshana integrity check already reads the served obstruction partition';
  ELSIF md5(v_cur) = 'fbb744094d76609b31ebc82b2a265ce9' THEN
    UPDATE asset_registry
       SET integrity_check_sql = replace(replace(v_cur,
             c_old_count, E'      SELECT count(*) FROM kala_obstruction o\n      WHERE o.convergence_id = d.convergence_id AND o.chart_id = d.chart_id\n        AND ' || c_served || ')'),
             c_old_match, E'      SELECT 1 FROM kala_obstruction o\n      WHERE o.convergence_id = d.convergence_id AND o.chart_id = d.chart_id\n        AND ' || c_served || E'\n        AND o.obstruction_type = e->>''type''')
     WHERE asset_id = 'ka_kala_darshana' AND md5(integrity_check_sql) = 'fbb744094d76609b31ebc82b2a265ce9';
  ELSE
    RAISE EXCEPTION '1406: the live ka_kala_darshana integrity_check_sql is not the migration 1375 text (md5 %)', md5(v_cur);
  END IF;
  IF (SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ka_kala_darshana') IS DISTINCT FROM 'f55e6c5d7a50dcc9f60e27c9459f4734' THEN
    RAISE EXCEPTION '1406: the ka_kala_darshana integrity_check_sql did not take';
  END IF;
END
$darshana$;

-- post-conditions: never trust a silent no-op ----------------------------------------------------------------------------------
DO $post$
DECLARE v_cur int; v_ok int; v_integrity text; v_count text;
BEGIN
  SELECT count(*) INTO v_cur FROM asset_output_digest_specs WHERE asset_id = 'ka_vighnakara' AND retired_at IS NULL;
  SELECT count(*) INTO v_ok FROM asset_output_digest_specs WHERE asset_id = 'ka_vighnakara' AND retired_at IS NULL
     AND spec_sha256 = '13ba8554c1972bc3a99a5b9c14d2801e55ef96481d35e8771ce42373e56dfc74' AND jsonb_array_length(spec -> 'components') = 2;
  IF v_cur <> 1 OR v_ok <> 1 THEN
    RAISE EXCEPTION '1406: the new ka_vighnakara digest spec is not the single current row (% current, % matching)', v_cur, v_ok;
  END IF;
  SELECT integrity_check_sql, count_sql INTO v_integrity, v_count FROM asset_registry WHERE asset_id = 'ka_vighnakara';
  IF position('GROUP BY chart_id, generation, convergence_id, obstruction_type' IN v_integrity) = 0
     OR position('GROUP BY chart_id, generation, signal_id, obstruction_type' IN v_integrity) = 0 THEN
    RAISE EXCEPTION '1406: the ka_vighnakara integrity check is not partition-aware';
  END IF;
  IF position('x.generation = h.generation' IN v_count) = 0 THEN RAISE EXCEPTION '1406: the ka_vighnakara count_sql is not the served-partition count'; END IF;
END
$post$;

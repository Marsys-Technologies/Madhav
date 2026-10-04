-- Migration 1306: G8 — the EXPECTED CLASS CENSUS at seal. ADDITIVE on top of 1232; replaces ONE function.
-- Pravāha B6.0 (steward GAPS-G8-G9 / G8-AUTHOR M20261004T192527-99ad, 2026-10-05; finding: Fable, PR 3110 review; evidence: Stream B). Author: pravaha stream B.
-- STATUS: DRAFT, HOLD (protected-class; second protected window; applies ONLY through the deploy job's exact --only window).
--
-- WHY
-- ═══
-- The seal-time function ka_gochara_search_completeness_violations defines the class census a generation CLAIMS as "its event_class
-- partitions" and checks each claimed partition against its inventory and the reverse; NOTHING compares that census with the set of scored
-- classes (the scored list lives only in the writer's own plan). A candidate left with 16 of the 26 scored classes after a failed dispatch
-- could therefore be verified class by class and sealed if the approver did not count. 26 = the 27 registered classes of the evaluation
-- protocol's fixed table (EVALUATION_PROTOCOL_v2_3 §2; evaluator.ROW_MEMBERSHIP) minus `birth_anchor`, an unscored annotation the evaluator
-- refuses to enumerate by design (O-CF-N6: zero rows).
--
-- WHAT THIS DOES (and what it deliberately does NOT do)
-- ════════════════════════════════════════════════════
--   Replaces ka_gochara_search_completeness_violations with the 1232 body, changed ONLY by (a) three added DECLARE variables and (b) ONE
--   appended block after the 1232 Moon-scope call: the manifest vector must pin `scored_classes` (a non-empty array of distinct, trimmed
--   names); the claimed classes (event_class coverage partitions UNION search inventories) must equal it; violations by name:
--   `expected_class_list_missing`, `expected_class_list_malformed`, `class_missing` (one row per pinned class not claimed),
--   `class_not_pinned` (one row per claimed class not pinned). A static test proves the new function equals the 1232 function with exactly
--   those edits. NO new function, table, trigger or grant: the function is INVOKER-run and CREATE OR REPLACE keeps its ACL, so the verifier's
--   and sealer's exact EXECUTE closure (1241 v7) is unchanged, and the seal trigger and the 1240 combined gate (both call this function)
--   pick the check up with no edit. The pin is produced by the writer (`build_input_vector(scored_classes=...)`) and re-derived from the
--   VERIFIER'S OWN universe (`input_vector_verifier.SCORED_CLASS_UNIVERSE`) by the verification job's independent input check; the job also
--   refuses a mismatching census by name (`class_census_mismatch` / `class_census_unpinned`) before it writes anything.
--   A slice-stamped candidate (PR 3110) stays refused for its own reason (scope `test_slice`, `stored_scope_missing`): its census would
--   fail too, a second reason, never the only one.
--   Not changed: the seal trigger, the replay branch, any 1153–1240 object, any grant, any table.
--
-- VECTOR CHANGE (decided and justified): the manifest vector of FULL builds gains ONE additive key, `scored_classes` (sorted list). Not a
-- schema bump: the serializer adds the key only when it is supplied (the frozen test vectors keep their literal preimages and digests); the
-- key is REQUIRED at verify (verification job, writer's in-build check) and at seal (this function). No '5.x' manifest exists yet, so no stored
-- vector is invalidated. The implementation lock moves (input_vector, input_vector_verifier, verification_job and the writer are locked
-- modules): regenerated once at the final head, never hand-edited.
--
-- WINDOW: protected public-schema window, AFTER 1240 (it replaces a function that 1206/1232 own and 1240 calls). Class: PROTECTED (CREATE OR
-- REPLACE FUNCTION in schema public needs CREATE on public, which the routine role does not hold).
-- GATE PIN: the function it replaces must be EXACTLY what 1232 produced: the sha256 of its pg_get_functiondef text, read READ-ONLY from production on
-- 2026-10-05 (63d9e7e737b020784ca52c4cd06e66e74434c20b60d9b9d65834f4e1c773f1fb) and reproduced by a fresh 1206+1232 chain in the test suite.
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns one transaction per migration.
-- ROLLBACK (unused installation only): CREATE OR REPLACE the completeness function from the 1232 file; delete the _migrations_applied row. After any
-- generation has been sealed under 1306, correct forward instead.
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE ──────────────────────────────────────────────────────────────────────
DO $$
DECLARE failures text;
BEGIN
  WITH f(failure, detail) AS (
    SELECT 'migration_1232_not_applied', 'ka_gochara_search_moon_scope_violations'
    WHERE to_regprocedure('public.ka_gochara_search_moon_scope_violations(uuid,text)') IS NULL
    UNION ALL SELECT 'migration_1232_function_missing', 'ka_gochara_search_completeness_violations'
    WHERE to_regprocedure('public.ka_gochara_search_completeness_violations(uuid,text)') IS NULL
    UNION ALL SELECT 'migration_1240_not_applied', 'ka_gochara_eval_window_verification'
    WHERE to_regclass('public.ka_gochara_eval_window_verification') IS NULL
    UNION ALL SELECT 'completeness_function_is_not_the_1232_body', 'sha256 of its definition is not the one 1232 produces (63d9e7e737b0...)'
    WHERE to_regprocedure('public.ka_gochara_search_completeness_violations(uuid,text)') IS NOT NULL
      AND encode(sha256(convert_to(pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure), 'UTF8')), 'hex')
          <> '63d9e7e737b020784ca52c4cd06e66e74434c20b60d9b9d65834f4e1c773f1fb'
      AND pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure) NOT LIKE '%expected_class_list_missing%'
    UNION ALL SELECT 'migration_1306_already_applied', 'expected_class_list_missing'
    WHERE to_regprocedure('public.ka_gochara_search_completeness_violations(uuid,text)') IS NOT NULL
      AND pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure) LIKE '%expected_class_list_missing%'
  )
  SELECT string_agg(failure || ' (' || detail || ')', ', ') INTO failures FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1306 BLOCKED: %', failures;
  END IF;
END;
$$;

-- ── the completeness function: the 1232 body + the G8 census block ────────────
CREATE OR REPLACE FUNCTION public.ka_gochara_search_completeness_violations(p_chart uuid, p_generation text)
RETURNS TABLE (event_class text, violation text, detail text)
LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE pub record; snap record; live_l1 text; live_dasha text; e text;
  census_vec jsonb; pinned_classes text[]; claimed_classes text[];
BEGIN
  SELECT p.horizon, p.input_generation_vector, p.convention_id INTO pub
  FROM public.kala_gochara_publication p
  WHERE p.chart_id = p_chart AND p.generation = p_generation AND p.status = 'published';

  -- the class census a generation CLAIMS = its event_class partitions
  RETURN QUERY
  SELECT c.partition_key, 'partition_without_inventory'::text, 'event_class partition has no search inventory'::text
  FROM public.kala_gochara_coverage c
  WHERE c.chart_id = p_chart AND c.generation = p_generation AND c.partition_kind = 'event_class'
    AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_inventory i
                    WHERE i.chart_id = p_chart AND i.generation = p_generation AND i.event_class = c.partition_key);
  RETURN QUERY
  SELECT i.event_class, 'inventory_without_partition'::text, 'search inventory has no event_class coverage partition'::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation
    AND NOT EXISTS (SELECT 1 FROM public.kala_gochara_coverage c
                    WHERE c.chart_id = p_chart AND c.generation = p_generation
                      AND c.partition_kind = 'event_class' AND c.partition_key = i.event_class);

  -- snapshot (one per generation)
  SELECT s.* INTO snap FROM public.ka_gochara_search_input_snapshot s
  WHERE s.chart_id = p_chart AND s.generation = p_generation;
  IF FOUND THEN
    live_l1 := public.ka_gochara_search_l1_facts_digest(p_chart, snap.consumed_fact_ids);
    live_dasha := public.ka_gochara_search_dasha_digest(p_chart, snap.consumed_dasha_row_ids);
    IF live_l1 IS DISTINCT FROM snap.l1_facts_digest THEN
      RETURN QUERY SELECT '*'::text, 'input_snapshot_drift'::text, 'consumed L1 fact rows no longer match the snapshot digest'::text;
    END IF;
    IF live_dasha IS DISTINCT FROM snap.dasha_digest THEN
      RETURN QUERY SELECT '*'::text, 'input_snapshot_drift'::text, 'consumed dasha rows no longer match the snapshot digest'::text;
    END IF;
    FOREACH e IN ARRAY snap.av_declarations LOOP
      IF public.ka_gochara_search_av_entry(left(e, GREATEST(length(e) - 65, 0))) IS DISTINCT FROM e THEN
        RETURN QUERY SELECT '*'::text, 'input_snapshot_drift'::text, ('AV declaration entry no longer matches: ' || e)::text;
      END IF;
    END LOOP;
    IF pub.input_generation_vector IS DISTINCT FROM snap.input_generation_vector THEN
      RETURN QUERY SELECT '*'::text, 'input_vector_mismatch'::text, 'snapshot vector differs from the published manifest vector'::text;
    END IF;
    -- R2: the snapshot's sky convention is bound to BOTH the publication's and every claimed
    -- event_class partition's legacy convention through the immutable bridge
    RETURN QUERY
    SELECT '*'::text, 'convention_bridge_missing'::text, ('publication legacy convention ' || COALESCE(pub.convention_id, 'NULL'))::text
    WHERE NOT EXISTS (SELECT 1 FROM public.ka_gochara_convention_bridge b WHERE b.kala_convention_id = pub.convention_id);
    RETURN QUERY
    SELECT '*'::text, 'convention_mismatch'::text,
           ('publication legacy convention ' || pub.convention_id || ' is bridged to ' || b.sky_convention_id ||
            ' but the snapshot is bound to ' || snap.convention_id)::text
    FROM public.ka_gochara_convention_bridge b
    WHERE b.kala_convention_id = pub.convention_id AND b.sky_convention_id IS DISTINCT FROM snap.convention_id;
    RETURN QUERY
    SELECT c.partition_key, 'convention_bridge_missing'::text, ('partition legacy convention ' || c.convention_id)::text
    FROM public.kala_gochara_coverage c
    WHERE c.chart_id = p_chart AND c.generation = p_generation AND c.partition_kind = 'event_class'
      AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_convention_bridge b WHERE b.kala_convention_id = c.convention_id);
    RETURN QUERY
    SELECT c.partition_key, 'convention_mismatch'::text,
           ('partition legacy convention ' || c.convention_id || ' is bridged to ' || b.sky_convention_id ||
            ' but the snapshot is bound to ' || snap.convention_id)::text
    FROM public.kala_gochara_coverage c
    JOIN public.ka_gochara_convention_bridge b ON b.kala_convention_id = c.convention_id
    WHERE c.chart_id = p_chart AND c.generation = p_generation AND c.partition_kind = 'event_class'
      AND b.sky_convention_id IS DISTINCT FROM snap.convention_id;
  END IF;

  -- registry accounting: every sealed (path, version) pinned or excluded, per class
  RETURN QUERY
  SELECT i.event_class, 'registry_unaccounted_path'::text, (rs.path_id || '@' || rs.rule_version)::text
  FROM public.ka_gochara_search_inventory i
  CROSS JOIN public.ka_gochara_rule_path_seal rs
  WHERE i.chart_id = p_chart AND i.generation = p_generation
    AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_path_pin p
                    WHERE (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version)
                        = (i.chart_id, i.generation, i.event_class, rs.path_id, rs.rule_version));

  -- version scope (F-3): per class and path AT MOST ONE version is 'included' — nothing may be
  -- searched twice under two versions of the same rule path and silently double-counted.
  RETURN QUERY
  SELECT p.event_class, 'multiple_included_versions'::text,
         (lower(p.path_id) || '@' || string_agg(p.rule_version, ',' ORDER BY p.rule_version))::text
  FROM public.ka_gochara_search_path_pin p
  WHERE p.chart_id = p_chart AND p.generation = p_generation AND p.disposition = 'included'
  GROUP BY p.event_class, lower(p.path_id)
  HAVING count(DISTINCT p.rule_version) > 1;
  -- 'superseded_by_version' asserts that ANOTHER version of the same path carries the search: a
  -- supersession claim with no included superseder is a coverage hole wearing a non-degrading
  -- reason (no ruling_ref), so it needs its own detector (CLAUDE.md §N.8).
  RETURN QUERY
  SELECT p.event_class, 'superseded_without_included_version'::text,
         (lower(p.path_id) || '@' || p.rule_version)::text
  FROM public.ka_gochara_search_path_pin p
  WHERE p.chart_id = p_chart AND p.generation = p_generation
    AND p.disposition = 'excluded' AND p.exclusion_reason = 'superseded_by_version'
    AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_path_pin q
                    WHERE q.chart_id = p.chart_id AND q.generation = p.generation
                      AND q.event_class = p.event_class AND lower(q.path_id) = lower(p.path_id)
                      AND q.rule_version <> p.rule_version AND q.disposition = 'included');

  -- finalisation, digests, horizon, snapshot binding
  RETURN QUERY
  SELECT i.event_class, 'inventory_not_finalised'::text, 'inventory header is not FINALISED'::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation AND i.inventory_digest IS NULL;
  RETURN QUERY
  SELECT i.event_class, 'inventory_digest_mismatch'::text, 'stored digests differ from recomputation'::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation AND i.inventory_digest IS NOT NULL
    AND (i.inventory_digest IS DISTINCT FROM public.ka_gochara_search_inventory_digest(i.chart_id, i.generation, i.event_class)
         OR i.ledger_digest IS DISTINCT FROM public.ka_gochara_search_ledger_digest(i.chart_id, i.generation, i.event_class));
  RETURN QUERY
  SELECT i.event_class, 'horizon_manifest_mismatch'::text, (i.horizon::text || ' vs manifest ' || COALESCE(pub.horizon::text, 'NULL'))::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation AND i.horizon IS DISTINCT FROM pub.horizon;
  RETURN QUERY
  SELECT i.event_class, 'input_snapshot_mismatch'::text, 'inventory is not bound to the generation snapshot'::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation
    AND (snap.input_digest IS NULL OR i.input_digest IS DISTINCT FROM snap.input_digest);

  -- committed obligation set == stored obligations, per pin, on the FULL key
  -- (chart, generation, class, path, rule_version): another path's — or another version's —
  -- obligations can never satisfy this pin's commitment (Codex R1). The detail names, for each
  -- committed id that is not stored under THIS pin, whether it is stored under a DIFFERENT pin.
  RETURN QUERY
  SELECT p.event_class, 'committed_set_mismatch'::text,
         (p.path_id || '@' || p.rule_version || ' committed-not-stored=' ||
          COALESCE((SELECT string_agg(c::text || COALESCE('(stored-under-' || fo.path_id || '@' || fo.rule_version || ')', ''), ',' ORDER BY c::text)
                    FROM unnest(p.committed_ob_ids) c
                    LEFT JOIN public.ka_gochara_search_obligation fo
                      ON (fo.chart_id, fo.generation, fo.event_class, fo.ob_id) = (p.chart_id, p.generation, p.event_class, c)
                    WHERE NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_obligation o
                                      WHERE (o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version, o.ob_id)
                                          = (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version, c))), '') ||
          ' stored-not-committed=' ||
          COALESCE((SELECT string_agg(o.ob_id::text, ',' ORDER BY o.ob_id::text) FROM public.ka_gochara_search_obligation o
                    WHERE (o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version)
                        = (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version)
                      AND NOT (o.ob_id = ANY (p.committed_ob_ids))), ''))::text
  FROM public.ka_gochara_search_path_pin p
  WHERE p.chart_id = p_chart AND p.generation = p_generation
    AND ( EXISTS (SELECT 1 FROM unnest(p.committed_ob_ids) c
                  WHERE NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_obligation o
                                    WHERE (o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version, o.ob_id)
                                        = (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version, c)))
       OR EXISTS (SELECT 1 FROM public.ka_gochara_search_obligation o
                  WHERE (o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version)
                      = (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version)
                    AND NOT (o.ob_id = ANY (p.committed_ob_ids))) );

  -- ledger coverage: horizon ⊆ ⋃ (searched_complete ∪ searched_unqualified), per obligation
  RETURN QUERY
  SELECT o.event_class, 'obligation_uncovered'::text,
         (o.ob_id::text || ' uncovered ' || (i.horizon::tstzmultirange -
            COALESCE((SELECT range_agg(v.search_range) FROM public.ka_gochara_search_interval v
                      WHERE (v.chart_id, v.generation, v.event_class, v.ob_id) = (o.chart_id, o.generation, o.event_class, o.ob_id)
                        AND v.state IN ('searched_complete','searched_unqualified','excluded_moon_tier')), '{}'::tstzmultirange))::text)::text
  FROM public.ka_gochara_search_obligation o
  JOIN public.ka_gochara_search_inventory i
    ON (i.chart_id, i.generation, i.event_class) = (o.chart_id, o.generation, o.event_class)
  WHERE o.chart_id = p_chart AND o.generation = p_generation
    AND NOT isempty(i.horizon::tstzmultirange -
          COALESCE((SELECT range_agg(v.search_range) FROM public.ka_gochara_search_interval v
                    WHERE (v.chart_id, v.generation, v.event_class, v.ob_id) = (o.chart_id, o.generation, o.event_class, o.ob_id)
                      AND v.state IN ('searched_complete','searched_unqualified','excluded_moon_tier')), '{}'::tstzmultirange));
  RETURN QUERY
  SELECT v.event_class, 'missing_inputs_present'::text, v.ob_id::text
  FROM public.ka_gochara_search_interval v
  WHERE v.chart_id = p_chart AND v.generation = p_generation AND v.state = 'missing_inputs';

  -- partition over-claim: horizon equality; relations_searched == the included obligations' relations
  RETURN QUERY
  SELECT i.event_class, 'partition_overclaims'::text,
         ('partition ' || c.completed_horizon::text || ' / ' || c.relations_searched::text)::text
  FROM public.ka_gochara_search_inventory i
  JOIN public.kala_gochara_coverage c
    ON (c.chart_id, c.generation, c.partition_kind, c.partition_key) = (i.chart_id, i.generation, 'event_class', i.event_class)
  WHERE i.chart_id = p_chart AND i.generation = p_generation
    AND ( c.completed_horizon IS DISTINCT FROM i.horizon
          OR ARRAY(SELECT DISTINCT x FROM unnest(c.relations_searched) x ORDER BY x)
             IS DISTINCT FROM
             ARRAY(SELECT DISTINCT o.relation FROM public.ka_gochara_search_obligation o
                   WHERE (o.chart_id, o.generation, o.event_class) = (i.chart_id, i.generation, i.event_class)
                   ORDER BY o.relation) );

  -- independent verification: a row must exist and EVERY row must equal the stored digest
  RETURN QUERY
  SELECT i.event_class, 'verification_missing_or_mismatch'::text, 'no independent verification row, or a row differs from the stored inventory digest'::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation
    AND ( NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_inventory_verification v
                      WHERE (v.chart_id, v.generation, v.event_class) = (i.chart_id, i.generation, i.event_class))
          OR EXISTS (SELECT 1 FROM public.ka_gochara_search_inventory_verification v
                     WHERE (v.chart_id, v.generation, v.event_class) = (i.chart_id, i.generation, i.event_class)
                       AND v.rederived_inventory_digest IS DISTINCT FROM i.inventory_digest) );

  -- AM-14 (1232): the Moon-scope accounting — stored exclusion = derived Moon-resolved domain; scope bound to the manifest
  RETURN QUERY SELECT * FROM public.ka_gochara_search_moon_scope_violations(p_chart, p_generation);

  -- G8 (1306): the EXPECTED CLASS CENSUS. A generation CLAIMS the classes that have an event_class coverage partition or a search
  -- inventory; its manifest vector pins the scored-class list it was built for (`scored_classes`: a non-empty array of distinct, trimmed
  -- class names, re-derived from the verifier's own universe by the verification job). A pinned class the generation does not claim, a
  -- claimed class that is not pinned, and an absent or malformed pin each refuse the seal BY NAME — a candidate left with 16 of 26 classes
  -- can no longer be verified class by class and sealed. Judged only against the PUBLISHED manifest (the seal path's own precondition).
  census_vec := (SELECT p.input_generation_vector FROM public.kala_gochara_publication p
                 WHERE p.chart_id = p_chart AND p.generation = p_generation AND p.status = 'published');
  IF census_vec IS NOT NULL THEN
    IF jsonb_typeof(census_vec -> 'scored_classes') IS DISTINCT FROM 'array' THEN
      RETURN QUERY SELECT '*'::text, 'expected_class_list_missing'::text,
        'the manifest vector pins no scored_classes array (a candidate must pin the scored-class list it is built for)'::text;
    ELSIF jsonb_array_length(census_vec -> 'scored_classes') = 0
          OR EXISTS (SELECT 1 FROM jsonb_array_elements(census_vec -> 'scored_classes') x
                     WHERE jsonb_typeof(x) <> 'string' OR btrim(x #>> '{}') = '' OR (x #>> '{}') <> btrim(x #>> '{}'))
          OR (SELECT count(DISTINCT x #>> '{}') FROM jsonb_array_elements(census_vec -> 'scored_classes') x)
             <> jsonb_array_length(census_vec -> 'scored_classes') THEN
      RETURN QUERY SELECT '*'::text, 'expected_class_list_malformed'::text,
        'scored_classes is empty, or holds a non-string, a blank, an untrimmed or a duplicated class name'::text;
    ELSE
      pinned_classes := ARRAY(SELECT x #>> '{}' FROM jsonb_array_elements(census_vec -> 'scored_classes') x);
      claimed_classes := ARRAY(SELECT c.partition_key FROM public.kala_gochara_coverage c
                                WHERE c.chart_id = p_chart AND c.generation = p_generation AND c.partition_kind = 'event_class'
                               UNION
                               SELECT i.event_class FROM public.ka_gochara_search_inventory i
                                WHERE i.chart_id = p_chart AND i.generation = p_generation);
      RETURN QUERY
      SELECT k, 'class_missing'::text, 'a pinned scored class has neither an event_class coverage partition nor a search inventory'::text
      FROM unnest(pinned_classes) k WHERE NOT (k = ANY (claimed_classes)) ORDER BY k;
      RETURN QUERY
      SELECT k, 'class_not_pinned'::text, 'a claimed class is not in the manifest''s pinned scored-class list'::text
      FROM unnest(claimed_classes) k WHERE NOT (k = ANY (pinned_classes)) ORDER BY k;
    END IF;
  END IF;
END;
$$;

-- ── Presence checks ────────────────────────────────────────────────────────────
DO $$
DECLARE def text;
BEGIN
  def := pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure);
  IF def NOT LIKE '%expected_class_list_missing%' OR def NOT LIKE '%class_missing%' OR def NOT LIKE '%class_not_pinned%' THEN
    RAISE EXCEPTION 'migration 1306 post-apply check failed: the completeness function does not carry the class census';
  END IF;
  IF def NOT LIKE '%ka_gochara_search_moon_scope_violations%' THEN
    RAISE EXCEPTION 'migration 1306 post-apply check failed: the completeness function lost the Moon-scope check';
  END IF;
  RAISE NOTICE 'migration 1306: presence checks passed';
END;
$$;

-- Migration 1232: AM-14 Moon-scope accounting for period-role obligations — ADDITIVE on top of 1206.
-- Pravāha B6.0, Codex round 6 R2 (steward M20261002T005809-65cb), 2026-10-02. Author: pravaha stream B. STATUS: HOLD.
--
-- WHY
-- ═══
-- AM-4 forbids storing Moon contacts/records in a generation. AM-11's stable `period_lord:md|ad|pd` obligations cover the
-- whole horizon and RESOLVE TO THE MOON during Moon periods. 1206 (accepted) refuses every `missing_inputs` interval and
-- every uncovered obligation, so a class whose period lord is the Moon for part of the horizon can never seal; removing
-- obligations whose literal agent is `moon` does not help, and relabelling an unperformed search as complete would defeat
-- the contract. Codex's closing contract (AM-14 in the amendments draft, v0.13):
--   Moon exclusion applies to the RESOLVED concrete transiting agent, including period-role agents. Each period-role
--   obligation has a snapshot-bound applicable time domain. Moon-resolved portions are explicitly accounted for as excluded
--   from the stored tier; they are neither missing search intervals nor completed geometry searches. Completeness requires
--   coverage of the applicable domain and verified accounting of its excluded complement.
--
-- WHAT THIS DOES (and what it deliberately does NOT do)
-- ════════════════════════════════════════════════════
--   1. Adds ONE interval state, `excluded_moon_tier`, to ka_gochara_search_interval (kgsiv_state_ck). The exclusion is
--      therefore an ordinary interval row: the applied 1206 guard already refuses overlap with any searched interval of the
--      same obligation (a portion cannot be both searched and excluded), refuses ranges outside the horizon, and
--      freezes it with the finalised header; and the row enters the ledger digest.
--   2. ka_gochara_search_moon_resolved_domain(chart, generation, class, ob_id): the snapshot-bound domain — the
--      consumed daśā rows (the snapshot's dasha_digest binds them) at the obligation's level (md=1, ad=2, pd=3)
--      whose lord is the Moon, clipped to the class horizon.
--   3. ka_gochara_search_moon_scope_violations(chart, generation): `moon_domain_missing` (a Moon-resolved portion neither
--      searched nor excluded is ALSO caught by obligation_uncovered), `moon_domain_extra` (an exclusion over a non-Moon
--      portion), `moon_exclusion_on_non_period_obligation`, and `stored_scope_missing` (the manifest vector must carry
--      stored_scope = stored_non_moon).
--   4. Replaces ka_gochara_search_completeness_violations with the 1206 body, changed ONLY in two places: the coverage
--      subtraction of `obligation_uncovered` also counts `excluded_moon_tier` intervals (both occurrences), and the new
--      scope check is called at the end. A static test proves the replacement equals the 1206 function with exactly these
--      edits. `missing_inputs_present` and `obligation_uncovered` are NOT weakened: a Moon-resolved portion that is neither
--      searched nor excluded still leaves the obligation uncovered, and a `missing_inputs` interval is still refused.
--   Not changed: the seal trigger, the replay branch, any 1153–1157 object, any grant to the builder. The seal path
--   needs EXECUTE on the two new functions for the SEALING principal (granted by whoever authorises it; the live suite
--   grants them to its sealer role).
--
-- PRINCIPALS: the builder already holds SELECT/INSERT/DELETE on ka_gochara_search_interval (1206 §7); excluded_moon_tier
-- rows ride the same grants. Nothing new is granted here.
--
-- WINDOW: protected public-schema window, AFTER 1206 (it ALTERs a 1206 table and replaces a 1206 function).
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns one transaction per migration.
-- ROLLBACK (unused installation only): ALTER the CHECK back to the three 1206 states, CREATE OR REPLACE the completeness
-- function from the 1206 file, DROP the two new functions, delete the _migrations_applied row. After any generation has been
-- sealed under 1232, correct forward instead.
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE ──────────────────────────────────────────────────────────────────────
DO $$
DECLARE failures text;
BEGIN
  WITH f(failure, detail) AS (
    SELECT 'migration_1206_not_applied', 'ka_gochara_search_interval'
    WHERE to_regclass('public.ka_gochara_search_interval') IS NULL
    UNION ALL SELECT 'migration_1206_function_missing', 'ka_gochara_search_completeness_violations'
    WHERE to_regprocedure('public.ka_gochara_search_completeness_violations(uuid,text)') IS NULL
    UNION ALL SELECT 'chart_dashas_missing', 'chart_dashas'
    WHERE to_regclass('public.chart_dashas') IS NULL
    UNION ALL SELECT 'migration_1232_already_applied', 'excluded_moon_tier'
    WHERE EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conname = 'kgsiv_state_ck'
                    AND c.conrelid = 'public.ka_gochara_search_interval'::regclass
                    AND pg_get_constraintdef(c.oid) LIKE '%excluded_moon_tier%')
  )
  SELECT string_agg(failure || ' (' || detail || ')', ', ') INTO failures FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1232 BLOCKED: %', failures;
  END IF;
END;
$$;

-- ── 1. the one new interval state ─────────────────────────────────────────────
ALTER TABLE public.ka_gochara_search_interval DROP CONSTRAINT kgsiv_state_ck;
ALTER TABLE public.ka_gochara_search_interval ADD CONSTRAINT kgsiv_state_ck
  CHECK (state IN ('searched_complete','searched_unqualified','missing_inputs','excluded_moon_tier'));

-- ── 2. the snapshot-bound Moon-resolved domain of a period-role obligation ─────
CREATE OR REPLACE FUNCTION public.ka_gochara_search_moon_resolved_domain(
  p_chart uuid, p_generation text, p_class text, p_ob uuid)
RETURNS tstzmultirange LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT COALESCE(
    (SELECT range_agg(tstzrange(d.start_iso, d.end_iso, '[)'))
       FROM public.ka_gochara_search_input_snapshot s
       JOIN public.ka_gochara_search_obligation o
         ON (o.chart_id, o.generation, o.event_class, o.ob_id) = (p_chart, p_generation, p_class, p_ob)
       JOIN public.chart_dashas d ON d.dasha_row_id = ANY (s.consumed_dasha_row_ids) AND d.chart_id = p_chart
      WHERE s.chart_id = p_chart AND s.generation = p_generation
        AND o.agent ~ '^period_lord:(md|ad|pd)$'
        AND d.level_n = CASE substr(o.agent, 13) WHEN 'md' THEN 1 WHEN 'ad' THEN 2 ELSE 3 END
        AND lower(d.lord_graha) = 'moon')
    * (SELECT i.horizon::tstzmultirange FROM public.ka_gochara_search_inventory i
        WHERE (i.chart_id, i.generation, i.event_class) = (p_chart, p_generation, p_class)),
    '{}'::tstzmultirange);
$$;

-- ── 3. the Moon-scope violations ───────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.ka_gochara_search_moon_scope_violations(p_chart uuid, p_generation text)
RETURNS TABLE (event_class text, violation text, detail text)
LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE pub record;
BEGIN
  SELECT p.input_generation_vector INTO pub
  FROM public.kala_gochara_publication p
  WHERE p.chart_id = p_chart AND p.generation = p_generation AND p.status = 'published';
  IF FOUND AND (pub.input_generation_vector ->> 'stored_scope') IS DISTINCT FROM 'stored_non_moon' THEN
    RETURN QUERY SELECT '*'::text, 'stored_scope_missing'::text,
      'the manifest input_generation_vector lacks stored_scope = stored_non_moon (AM-14: serving must be able to state the scope)'::text;
  END IF;

  -- period-role obligations: the stored exclusion must EQUAL the derived Moon-resolved domain
  RETURN QUERY
  SELECT o.event_class, 'moon_domain_missing'::text,
         (o.ob_id::text || ' derived Moon-resolved domain not accounted: ' ||
          (public.ka_gochara_search_moon_resolved_domain(o.chart_id, o.generation, o.event_class, o.ob_id) -
           COALESCE((SELECT range_agg(v.search_range) FROM public.ka_gochara_search_interval v
                      WHERE (v.chart_id, v.generation, v.event_class, v.ob_id) = (o.chart_id, o.generation, o.event_class, o.ob_id)
                        AND v.state = 'excluded_moon_tier'), '{}'::tstzmultirange))::text)::text
  FROM public.ka_gochara_search_obligation o
  WHERE o.chart_id = p_chart AND o.generation = p_generation AND o.agent ~ '^period_lord:(md|ad|pd)$'
    AND NOT isempty(public.ka_gochara_search_moon_resolved_domain(o.chart_id, o.generation, o.event_class, o.ob_id) -
          COALESCE((SELECT range_agg(v.search_range) FROM public.ka_gochara_search_interval v
                     WHERE (v.chart_id, v.generation, v.event_class, v.ob_id) = (o.chart_id, o.generation, o.event_class, o.ob_id)
                       AND v.state = 'excluded_moon_tier'), '{}'::tstzmultirange));
  RETURN QUERY
  SELECT o.event_class, 'moon_domain_extra'::text,
         (o.ob_id::text || ' exclusion outside the derived Moon-resolved domain: ' ||
          (COALESCE((SELECT range_agg(v.search_range) FROM public.ka_gochara_search_interval v
                      WHERE (v.chart_id, v.generation, v.event_class, v.ob_id) = (o.chart_id, o.generation, o.event_class, o.ob_id)
                        AND v.state = 'excluded_moon_tier'), '{}'::tstzmultirange) -
           public.ka_gochara_search_moon_resolved_domain(o.chart_id, o.generation, o.event_class, o.ob_id))::text)::text
  FROM public.ka_gochara_search_obligation o
  WHERE o.chart_id = p_chart AND o.generation = p_generation AND o.agent ~ '^period_lord:(md|ad|pd)$'
    AND NOT isempty(COALESCE((SELECT range_agg(v.search_range) FROM public.ka_gochara_search_interval v
                               WHERE (v.chart_id, v.generation, v.event_class, v.ob_id) = (o.chart_id, o.generation, o.event_class, o.ob_id)
                                 AND v.state = 'excluded_moon_tier'), '{}'::tstzmultirange) -
          public.ka_gochara_search_moon_resolved_domain(o.chart_id, o.generation, o.event_class, o.ob_id));
  -- an exclusion is meaningful only for a period-role obligation (the Moon is never a stored concrete agent)
  RETURN QUERY
  SELECT v.event_class, 'moon_exclusion_on_non_period_obligation'::text, v.ob_id::text
  FROM public.ka_gochara_search_interval v
  JOIN public.ka_gochara_search_obligation o
    ON (o.chart_id, o.generation, o.event_class, o.ob_id) = (v.chart_id, v.generation, v.event_class, v.ob_id)
  WHERE v.chart_id = p_chart AND v.generation = p_generation AND v.state = 'excluded_moon_tier'
    AND o.agent !~ '^period_lord:(md|ad|pd)$';
END;
$$;

-- ── 4. the 1206 completeness function with exactly two edits (see header) ──────
CREATE OR REPLACE FUNCTION public.ka_gochara_search_completeness_violations(p_chart uuid, p_generation text)
RETURNS TABLE (event_class text, violation text, detail text)
LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE pub record; snap record; live_l1 text; live_dasha text; e text;
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
END;
$$;

-- ── Presence checks ────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conname = 'kgsiv_state_ck'
                   AND c.conrelid = 'public.ka_gochara_search_interval'::regclass
                   AND pg_get_constraintdef(c.oid) LIKE '%excluded_moon_tier%') THEN
    RAISE EXCEPTION 'migration 1232 post-apply check failed: kgsiv_state_ck does not admit excluded_moon_tier';
  END IF;
  IF to_regprocedure('public.ka_gochara_search_moon_scope_violations(uuid,text)') IS NULL
     OR to_regprocedure('public.ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)') IS NULL THEN
    RAISE EXCEPTION 'migration 1232 post-apply check failed: a new function is missing';
  END IF;
  IF pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure) NOT LIKE '%ka_gochara_search_moon_scope_violations%' THEN
    RAISE EXCEPTION 'migration 1232 post-apply check failed: the completeness function does not call the scope check';
  END IF;
  RAISE NOTICE 'migration 1232: presence checks passed';
END;
$$;

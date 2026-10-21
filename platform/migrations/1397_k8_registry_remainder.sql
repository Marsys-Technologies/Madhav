-- Migration 1397 (PROVISIONAL NUMBER, see below): K8-REG remainder, ka_sangam candidate-jury integrity (engine form).
-- ONE guarded UPDATE of ONE column (integrity_check_sql) of ONE asset_registry row (ka_sangam); nothing else.
-- Data-only, no DDL, no INSERT/DELETE: ROUTINE class (same shape as applied routine 1253/1297/1304), not a protected window.
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- NUMBER. No number is allocated to this job in /Users/Dev/kalayantra/run/MIGRATION_ALLOCATION.json (K8-REG's own 1392 is
-- applied and never edited). 1397 is the file's next_free at authoring time and is NOT an allocation: the cockpit allocates a
-- number to K8-REG-rest or renumbers this file before queueing (R-2026-10-16-01). The tests find the file by its suffix
-- (*_k8_registry_remainder.sql), so a renumber is a rename with no change to the body.
--
-- THE GAP (SR-K8REG-OPEN, reviews X-20261018T053833Z NB-1 and X-20261018T094646Z NB-4). Plan section 7, Build row, requires an
-- integrity_check_sql in engine form (unparameterised, read-only, first column of the first row truthy; asset_runner._probe_asset
-- and asset_census.integrity_sql_problem) per re-shaped asset. Measured on the replay of the registry-writing migrations
-- (tests/l3/kala_db/registry/test_k8_remainder.py): 23 of the 25 ka_* rows already carry an engine-form check; the two NULL rows
-- are ka_gochara_v5 (NULL by steward ruling CHAIN-3101-RULING-FINAL and pinned by the J-3d dispatch/teardown, migration 1304)
-- and ka_gochara_v4_41_candidate (inactive candidate), both left NULL here. ka_sangam carries only the 670 contract, which reads
-- the legacy kala_convergence table: the K4-2a candidate jury tables (migration 1350), the re-shaped part of the asset, have no
-- detector, so a corrupted candidate partition reads healthy. This migration appends that detector.
--
-- WHAT IS ADDED (violation searches, so a layer with no candidate rows, i.e. every default legacy dispatch, stays true).
-- Each is stated by services/ka_sangam/jury/candidate_contract.json and holds on the writer's real output (tested):
--   (K8-a) grain: "chart x generation x class; exactly one canonical jury assertion per supplied class horizon";
--   (K8-b) segments: "half-open boundaries": the segments of one assertion never overlap (end == next start is allowed);
--   (K8-c) segments: "group support vectors and allowed source roots": support_roots names exactly the groups of support_vector.
-- Table CHECKs and foreign keys of 1350 already cover single-row shape; nothing here restates them, and no invariant the contract
-- does not state is invented (CLAUDE.md B.10, N.8).
--
-- SPLICE. The conjunct is inserted immediately before the contract's final "AS integrity_passed"; every 670 conjunct is kept
-- byte for byte. A marker comment makes the migration idempotent (second apply = no change). It refuses, changing nothing, when
-- the row is missing or its stored text is not the registered shape (no trailing "AS integrity_passed").
--
-- TRIGGER EFFECT (real, intended; migration 596 nirmana_registry_receipt_invalidation, as 1304/1375 state). Changing
-- integrity_check_sql marks the asset_freshness rows of ka_sangam ONLY stale (registry_changed) until a governed build restores
-- them; no other asset and no data row is touched. Deploy with no ka_sangam build in flight.
--
-- NOT CHANGED: depends_on, has_writer, has_substeps, count_sql, target_table, clear_tables, is_active, catalog_status,
-- superseded_by, data_disposition, the seed, any other row. Lifecycle cutovers are not made here (see the test's ledger:
-- J-7a owns ka_gochara/century/2.0, D-R6 owns Tulana, ka_gochara_sweep was settled by 593).
SET LOCAL lock_timeout = '5s';
DO $k8r$
DECLARE
  marker constant text := '-- K8-REG remainder: candidate jury (K4-2a)';
  conjunct constant text := $k8_jury$
  -- K8-REG remainder: candidate jury (K4-2a), contract services/ka_sangam/jury/candidate_contract.json.
  -- (K8-a) grain chart x generation x class holds exactly one canonical jury assertion.
  AND NOT EXISTS (
    SELECT 1 FROM kala_jury_candidate
    GROUP BY chart_id, generation, event_class
    HAVING count(*) <> 1
  )
  -- (K8-b) half-open segments of one assertion never overlap; ordered by start, an overlap shows between neighbours.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT segment_end,
             lead(segment_start) OVER (PARTITION BY chart_id, generation, event_class, assertion_id
                                       ORDER BY segment_start) AS next_start
      FROM kala_jury_candidate_segment
    ) s
    WHERE s.next_start IS NOT NULL AND s.segment_end > s.next_start
  )
  -- (K8-c) a segment's allowed source roots are keyed by exactly the groups of its support vector.
  AND NOT EXISTS (
    SELECT 1 FROM kala_jury_candidate_segment g
    WHERE ARRAY(SELECT jsonb_object_keys(g.support_roots) ORDER BY 1)
          IS DISTINCT FROM ARRAY(SELECT jsonb_array_elements_text(g.support_vector) ORDER BY 1)
  )$k8_jury$;
  old_check text;
  tail_text text;
  new_check text;
BEGIN
  SELECT integrity_check_sql INTO old_check FROM public.asset_registry
    WHERE asset_id = 'ka_sangam' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'K8R: missing asset identity ka_sangam';
  END IF;
  IF old_check IS NULL THEN
    RAISE EXCEPTION 'K8R: ka_sangam has no registered integrity contract to extend';
  END IF;
  IF position(marker IN old_check) = 0 THEN
    tail_text := (regexp_match(old_check, '[[:space:]]*AS integrity_passed[[:space:]]*$'))[1];
    IF tail_text IS NULL THEN
      RAISE EXCEPTION 'K8R: ka_sangam integrity contract does not end with AS integrity_passed';
    END IF;
    new_check := substr(old_check, 1, length(old_check) - length(tail_text))
              || conjunct || E'\n  AS integrity_passed\n';
    UPDATE public.asset_registry SET integrity_check_sql = new_check WHERE asset_id = 'ka_sangam';
  END IF;
  SELECT integrity_check_sql INTO new_check FROM public.asset_registry WHERE asset_id = 'ka_sangam';
  IF new_check IS NULL
     OR position(marker IN new_check) = 0
     OR position(marker IN substr(new_check, position(marker IN new_check) + length(marker))) <> 0
     OR new_check !~ 'AS integrity_passed[[:space:]]*$' THEN
    RAISE EXCEPTION 'K8R: ka_sangam candidate-jury conjunct did not land exactly once';
  END IF;
END
$k8r$;

-- 1269_bg_panchanga_depends_on_ephemeris_engine.sql
--
-- Suvarna Track I, item TI-L0-29 (finding CF-03 / ledger bg_panchanga-G04, SS ruling Q16 of 2026-10-01; number
-- 1269 allocated by SS): declare the dependency edge  bg_panchanga -> bg_ephemeris_engine.
--
--   UPDATE asset_registry SET depends_on = {bg_ephemeris_engine} WHERE asset_id = 'bg_panchanga'   (was {})
--
-- One cell of one row. Nothing else.
--
-- CONCERN
--   bg_panchanga is a registered SERVICE ("Deterministic panchang computation service (swisseph DE441, Lahiri,
--   Drik-parity)", asset_kind = service, has_writer = false, no table) whose registry row declares 0
--   dependencies, although it cannot compute without the ephemeris engine: panchang_engine/__init__.py:63, 79
--   (panchang_day) and :248, 262 (panchang_instant) import and call pyswisseph directly (NOT the ephemeris_daily
--   table, which no panchang_engine module reads, which is why the ledger's `bg_ephemeris` edge is not taken; the
--   ledger cited the same imports at 59-71/149-150/241 against an older base). SS Q16 (2026-10-01): "declare bg_ephemeris_engine (what the code actually
--   calls)". bg_cohort already depends on bg_ephemeris_engine, so a service-to-service L0 edge to this producer
--   is an established shape. The consumer ga_panchanga (depends_on {ga_positions, bg_panchanga}) rests on it.
--
-- WHY IT NEEDS ITS OWN REVIEW (the table says so; this is the review input)
--   1210 deliberately excluded L0 bedrock edges. This one is a registry-order and upstream-hash change, so:
--   (a) DAG ORDER. bg_ephemeris_engine depends on nothing, so no cycle can form: re-checked in the migration with
--       a recursive walk over the live graph, and in the test over the live 129-row registry graph (snapshot of
--       2026-10-03) with a topological order that places bg_ephemeris_engine before bg_panchanga before
--       ga_panchanga.
--   (b) DISPATCH GATE (asset_runner.deps_unsatisfied). A SERVICE dependency is satisfied when its
--       asset_throughput.state is lit or service_ok and its data-freshness receipt is IGNORED ("a service has no
--       data-freshness receipt; service_ok is what lit means for a service"). bg_ephemeris_engine is state lit
--       (last_built_at 2026-08-27). So bg_panchanga is NOT blocked by its new dependency, and ga_panchanga, whose
--       dependency bg_panchanga is also a service, is NOT newly blocked by bg_panchanga becoming stale. Proven in
--       the test by executing the real deps_unsatisfied function against the fixture.
--   (c) UPSTREAM HASH. compute_upstream_hash hashes each asset's DECLARED direct deps only. bg_panchanga is never
--       built (no writer), so its own hash never computes; ga_panchanga's declared deps are unchanged, so its
--       upstream digest is unchanged. The ledger's worry that the edge "may mark ga_panchanga stale" does not
--       hold: the registry trigger acts on NEW.asset_id only (bg_panchanga), never on dependents.
--   (d) IN-FLIGHT RUNS. runner._verify_registry_still_matches_manifest compares each planned asset's live
--       depends_on with the run's FROZEN manifest; a run planned/running/paused across this migration has its
--       diverged assets terminalized and their dependents blocked (the 1210 hazard). ga_panchanga is in the S-L1
--       set. APPLY ONLY WHEN no build_runs row is in state planned/running/paused (this migration does not check;
--       it is a held, SS-sequenced merge, like 1210/1226).
--   (e) NIRMANA FROZEN MANIFESTS. assertManifestMatchesRegistryIdentity throws on any depends_on change versus a
--       frozen manifest, and the T0 manifest records bg_panchanga depends_on []. The Nirmana campaign is OFF and
--       superseded (the 1210 precedent), so no frozen manifest is used for a live dispatch; a wave that was frozen
--       before this change would refuse to dispatch bg_panchanga.
--
-- SERVING EFFECT AT APPLY
--   * Fires nirmana_registry_receipt_invalidation (depends_on is a trigger column): the asset_freshness row of
--     bg_panchanga (unknown, reason output_digest_spec_unavailable) becomes STALE with reason registry_changed
--     appended. Assets that go stale: bg_panchanga ONLY. No other asset's freshness row is touched.
--   * No served surface reads depends_on at serve time, no data is touched, ga_panchanga is not blocked (b).
--   * Cockpit blocking radius: bg_ephemeris_engine gains one direct dependent (bg_panchanga).
--
-- GUARDS (every one raises rather than skip)
--   * bg_panchanga must exist, be active, asset_kind = 'service', has_writer = false, target_table IS NULL, and
--     depends_on exactly {} or already exactly {bg_ephemeris_engine} (then skipped); any other value is DRIFT.
--   * bg_ephemeris_engine must exist, be active and asset_kind = 'service' (dependency trap otherwise).
--   * no cycle: bg_panchanga must not be reachable from bg_ephemeris_engine through depends_on.
--   * ROW_COUNT = 1 and a post-check that re-reads the cell and re-walks the graph for a cycle through bg_panchanga.
--   A row that does not exist (fresh bootstrap without the row) is skipped with a NOTICE (1210 convention).
--
-- PRIVILEGE (P2 rule, W1_PRIVILEGE_AUDIT): runs as amjis_app, OWNER of asset_registry, asset_freshness and the
-- trigger function; needs only UPDATE on asset_registry. No CREATE, no GRANT, no DDL, nothing in schema public
-- beyond USAGE. Proven as amjis_app (NOSUPERUSER, NOINHERIT, no CREATE on public).
--
-- IDEMPOTENT: a second run finds the edge present and updates nothing (the trigger does not fire again).
--
-- NOT DONE HERE
--   * The seed literal depends_on: [] for bg_panchanga in platform/scripts/seed/asset_registry_seed.ts (a #2984
--     file). The seed's ON CONFLICT keeps depends_on migration-governed for an existing row, so a re-seed cannot
--     revert this file; the literal matters only for a fresh bootstrap.
--   * Any service-probe or reads-match detector change; any dispatch; the ledger's `bg_ephemeris` edge (not taken
--     by SS Q16); the bg_ephemeris_engine edge for other services.
--
-- ROLLBACK (ops reference, not executed): UPDATE asset_registry SET depends_on = '{}' WHERE asset_id =
-- 'bg_panchanga'; a new reviewed migration against the then-current state.
--
-- VERIFY AFTER APPLY by production structure, not the deploy log (Trap 103):
--   SELECT asset_id, depends_on FROM asset_registry WHERE asset_id = 'bg_panchanga';       -- {bg_ephemeris_engine}
--   SELECT freshness_state, reasons FROM asset_freshness WHERE asset_id = 'bg_panchanga';  -- stale, [..., "registry_changed"]
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).

SET LOCAL lock_timeout = '5s';

DO $m1269$
DECLARE
    v_kind     text;
    v_writer   boolean;
    v_target   text;
    v_active   boolean;
    v_deps     text[];
    e_kind     text;
    e_active   boolean;
    v_rows     bigint;
BEGIN
    SELECT asset_kind, has_writer, target_table, is_active, depends_on
      INTO v_kind, v_writer, v_target, v_active, v_deps
      FROM asset_registry WHERE asset_id = 'bg_panchanga' FOR UPDATE;
    IF NOT FOUND THEN
        RAISE NOTICE '1269: bg_panchanga is not in asset_registry; skipped';
        RETURN;
    END IF;
    IF v_active IS DISTINCT FROM true OR v_kind IS DISTINCT FROM 'service'
       OR v_writer IS DISTINCT FROM false OR v_target IS NOT NULL THEN
        RAISE EXCEPTION '1269: bg_panchanga has drifted from the audited state (is_active=%, asset_kind=%, has_writer=%, target_table=%); refusing to change depends_on',
            v_active, v_kind, v_writer, v_target;
    END IF;

    SELECT asset_kind, is_active INTO e_kind, e_active
      FROM asset_registry WHERE asset_id = 'bg_ephemeris_engine';
    IF NOT FOUND OR e_active IS DISTINCT FROM true OR e_kind IS DISTINCT FROM 'service' THEN
        RAISE EXCEPTION '1269: bg_ephemeris_engine is missing, inactive or not a service (is_active=%, asset_kind=%); refusing to declare the edge (dependency trap)',
            e_active, e_kind;
    END IF;

    IF v_deps = ARRAY['bg_ephemeris_engine']::text[] THEN
        RAISE NOTICE '1269: bg_panchanga already depends on bg_ephemeris_engine; skipped';
        RETURN;
    END IF;
    IF v_deps IS DISTINCT FROM '{}'::text[] THEN
        RAISE EXCEPTION '1269: bg_panchanga depends_on is % (audited: {}); refusing to overwrite', v_deps;
    END IF;

    -- no cycle: bg_panchanga must not be reachable from bg_ephemeris_engine
    IF EXISTS (
        WITH RECURSIVE reach(asset_id) AS (
            SELECT 'bg_ephemeris_engine'::text
            UNION
            SELECT d FROM reach r
              JOIN asset_registry a ON a.asset_id = r.asset_id
              CROSS JOIN LATERAL unnest(COALESCE(a.depends_on, '{}'::text[])) AS d
        )
        SELECT 1 FROM reach WHERE asset_id = 'bg_panchanga'
    ) THEN
        RAISE EXCEPTION '1269: bg_ephemeris_engine already reaches bg_panchanga; the edge would close a cycle';
    END IF;

    UPDATE asset_registry SET depends_on = ARRAY['bg_ephemeris_engine']::text[]
     WHERE asset_id = 'bg_panchanga' AND depends_on = '{}'::text[];
    GET DIAGNOSTICS v_rows = ROW_COUNT;
    IF v_rows <> 1 THEN
        RAISE EXCEPTION '1269: bg_panchanga depends_on update touched % rows, expected 1', v_rows;
    END IF;

    -- Post-check: re-read the cell and re-walk the graph for a cycle through bg_panchanga.
    IF NOT EXISTS (SELECT 1 FROM asset_registry
                    WHERE asset_id = 'bg_panchanga' AND depends_on = ARRAY['bg_ephemeris_engine']::text[]) THEN
        RAISE EXCEPTION '1269: bg_panchanga depends_on is not {bg_ephemeris_engine} after the update';
    END IF;
    IF EXISTS (
        WITH RECURSIVE reach(asset_id) AS (
            SELECT d FROM asset_registry a CROSS JOIN LATERAL unnest(COALESCE(a.depends_on, '{}'::text[])) AS d
             WHERE a.asset_id = 'bg_panchanga'
            UNION
            SELECT d FROM reach r
              JOIN asset_registry a ON a.asset_id = r.asset_id
              CROSS JOIN LATERAL unnest(COALESCE(a.depends_on, '{}'::text[])) AS d
        )
        SELECT 1 FROM reach WHERE asset_id = 'bg_panchanga'
    ) THEN
        RAISE EXCEPTION '1269: bg_panchanga is on a dependency cycle after the update';
    END IF;
END
$m1269$;

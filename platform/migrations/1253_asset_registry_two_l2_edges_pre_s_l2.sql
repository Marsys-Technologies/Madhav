-- 1253_asset_registry_two_l2_edges_pre_s_l2.sql
--
-- Suvarna Track I / S-L2 prerequisite (SS decision GO option B, 2026-10-02): declare the TWO direct `depends_on`
-- edges between L2 (Bodha) and L1 / L2 assets that were split out of the original six-edge migration (the four L1
-- edges are migration 1226, its own PR, since applied). Same kind as migration 1210: surgical, append-only, guarded,
-- acyclic-checked, verified by production structure afterwards.
--
-- APPLY TIMING RULE (HARD GATE in the S-L2 launch checklist). MERGE = APPLY at the next deploy (migrate.ts runs
-- on every deploy). This migration is applied IMMEDIATELY BEFORE S-L2 is dispatched, and not otherwise:
--   * applying it AFTER the S-L2 build of bo_laksana / bo_upaya would re-stale both assets (CONSEQUENCES 1) right
--     after they were rebuilt fresh, forcing a second rebuild;
--   * applying it EARLY stales bo_laksana / bo_upaya freshness on every chart and gates their lit bo_* dependents
--     (bo_laksana has 24 declared direct dependents, read live) until S-L2 rebuilds them.
-- So the PR is held until the S-L2 window and merges only then.
--
-- PRECONDITIONS AT MERGE TIME (repeat them immediately before merging, not only before arming the PR): (a) the
-- 0-active-runs operator check below; (b) gate readiness: ga_yoga and bo_bimba must be lit and fresh on every
-- chart, because bo_laksana now needs ga_yoga fresh and bo_upaya now needs bo_bimba fresh (checked directly by
-- asset_runner.deps_unsatisfied), i.e. S-L1 is complete first and the S-L2 build order has bo_bimba rebuilt before
-- bo_upaya. Any RAISE here, or a lock_timeout expiry, fails the migrate job and therefore the whole deploy.
--
--   #  consumer (gains the edge)   producer (new dep)   why the consumer reads the producer
--   1  bo_laksana                  ga_yoga              bo_laksana.py:2713,2769 read ga_yoga_firings   (Q-L2-07)
--   2  bo_upaya                    bo_bimba             bo_upaya.py:578 joins bodha_cgm_nodes          (Q-L2-07)
--
-- Live `depends_on` before this migration (read 2026-10-02, production):
--   bo_laksana {bg_rules, ga_positions, ga_strength, ga_sensitive, ga_panchanga, ga_sade_sati, ga_structural,
--               ga_nakshatra, ga_condition, ga_vargas, ga_vichara}
--   bo_upaya   {bo_laksana, bo_sangati, ga_structural, ga_dashas, bo_cgm_motifs}
--   (producers, unchanged: ga_yoga {ga_structural, ga_dashas}; bo_bimba {bo_laksana, bo_sudarshana,
--    bo_nakshatra_semantic, bo_arudha, bo_special_lagna, bo_vargottama_dhana})
--
-- NO ORDERING CHANGE. Both edges duplicate paths that already exist in the live registry graph (checked offline,
-- read-only, 2026-10-02): bo_laksana reaches ga_yoga and bo_upaya reaches bo_bimba transitively. The edges make
-- the dependency DECLARED (compute_upstream_hash hashes declared deps only; the cockpit blocking radius and the
-- E6 reads-match detector see it) without adding a build-order constraint.
--
-- NO DATA ROW CHANGES. Only asset_registry.depends_on of the two consumers is written; no other column, no
-- other row, no chart_* / bodha_* / ga_* data table. The ONE derived side effect is the registry trigger
-- described in CONSEQUENCES 1 (asset_freshness projection rows go stale); it is not a data write by this file.
--
-- ACYCLIC. By hand (to be re-proved by this migration's own guard): ga_yoga depends on no bo_* asset and
-- bo_bimba does not depend on bo_upaya, so bo_laksana -> ga_yoga and bo_upaya -> bo_bimba close no cycle. The
-- migration re-checks this inside the transaction (Guard 3, a recursive-CTE reachability closure over the
-- post-edit graph) and RAISES on any cycle through an edited asset. Together with 1226's four edges the union
-- stays acyclic (checked offline against the live 129-asset graph); either order of the two migrations is valid.
--
-- BEHAVIOUR. Appends only, existing array order preserved, each edge appended only if absent (idempotent: a
-- second run rewrites nothing; a fully-covered row is not touched; a NULL depends_on is treated as empty).
-- Guard 1: if NONE of the four involved assets exists in asset_registry (a database with an empty registry:
-- the TypeScript seed, platform/scripts/seed/asset_registry_seed.ts, carries the same two edges for NEW rows;
-- its re-seed never rewrites depends_on of an existing row) the migration is a no-op; if SOME but not all
-- exist, or any producer is missing or inactive, it RAISES (a dependency trap, as in 1210). Limit, stated
-- plainly: of the four involved assets only ga_yoga is INSERTed by a migration (240); the rest are rows the
-- TypeScript seed creates (migrations only UPDATE them), so a replay of migrations over a registry that holds
-- some but not all of them stops here by design. Every supported database (production, and CI's production
-- registry dump) holds all four.
--
-- CONSEQUENCES (stated plainly):
--  1. Freshness goes stale AT APPLY, for every chart, for exactly TWO assets. asset_registry carries the trigger
--     nirmana_registry_receipt_invalidation (migration 596; AFTER UPDATE OF depends_on, ..., FOR EACH ROW WHEN
--     OLD IS DISTINCT FROM NEW), whose function runs `UPDATE asset_freshness SET freshness_state = 'stale',
--     reasons += 'registry_changed' WHERE asset_id = NEW.asset_id` with NO chart filter. So the moment this
--     UPDATE lands, every asset_freshness row of bo_laksana and bo_upaya reads 'stale' (the last receipt is
--     kept; only the projection flips; the next governed build re-establishes fresh). ga_yoga and bo_bimba are
--     PRODUCERS here and are not touched by this migration. The staleness stays until each chart's rebuild
--     re-establishes a fresh receipt. Read from production 2026-10-02: bo_laksana and bo_upaya each carry one
--     fresh and one stale row (two charts). Through the hard dependency gate (item 4) a stale bo_laksana gates
--     its declared dependents (24 direct, read live) and a stale bo_upaya gates bo_samvada, bo_pramana_mapa,
--     ka_kshetra and ph_pratikara, until rebuilt. A second run does not re-fire the trigger (nothing changes, so OLD IS NOT
--     DISTINCT FROM NEW).
--  2. Upstream hash. `compute_upstream_hash` hashes DECLARED deps, so it changes ONCE for bo_laksana and
--     bo_upaya: a one-time rebuild signal at their next dispatch (S-L2 rebuilds them anyway).
--  3. Frozen manifests. Each edited asset's Nirmana-frozen manifest (where one exists) no longer matches the
--     live registry: `assertManifestMatchesRegistryIdentity` throws on any depends_on change, so the monitor
--     reports `plan_adaptation_required` for bo_laksana and bo_upaya (same effect as 1210), and
--     scripts/dispatch_nirmana_campaign_wave.py refuses a wave whose frozen asset's live depends_on changed. No
--     other run may be dispatching or running these assets at apply (an OPERATOR check, not a RAISE: this file
--     does not enforce it; the 0-active-runs query below).
--  4. Hard dependency gate. asset_runner.deps_unsatisfied (enforce mode) requires every declared dep to be
--     asset_throughput.state 'lit' (or 'service_ok') AND its latest asset_freshness 'fresh'. Both new edges
--     duplicate existing transitive paths (no new ORDERING constraint); the producer is now also checked
--     directly for lit/fresh: bo_laksana now needs ga_yoga fresh, bo_upaya now needs bo_bimba fresh. After S-L1
--     and the S-L2 build order both are fresh before the consumers run.
--  5. Cockpit direct blocking radius of ga_yoga and bo_bimba rises by their new direct consumer.
--
-- APPLY ONLY WHEN no build_runs row is in state planned/running/paused (verify at apply: SELECT count(*) FROM
-- build_runs WHERE state IN ('planned','running','paused') must be 0; read 2026-10-02: 0, and 0 runs involving
-- any of the four assets). runner.py `_verify_registry_still_matches_manifest` compares each planned asset's
-- live depends_on against the run's frozen manifest; a run planned/running across the deploy has its diverged
-- assets terminalized.
--
-- VERIFICATION AFTER APPLY is by PRODUCTION STRUCTURE, not by the deploy log (Trap 103: a deploy run's head_sha
-- metadata can disagree with the SHA actually deployed, and a green deploy can hide a no-op migration):
--   SELECT asset_id, depends_on FROM asset_registry
--    WHERE asset_id IN ('bo_laksana','bo_upaya') ORDER BY 1;
--   -- expect: bo_laksana has ga_yoga; bo_upaya has bo_bimba
--   and the acyclicity closure over the FULL registry (Guard 3 seeds only from the edited consumers; this drops
--   that filter, so it would also show a pre-existing cycle elsewhere) returns no row:
--   WITH RECURSIVE edges AS (SELECT r.asset_id AS src, d.dep FROM asset_registry r
--                             CROSS JOIN LATERAL unnest(COALESCE(r.depends_on, '{}'::text[])) AS d(dep)),
--        reach(src, node) AS (SELECT src, dep FROM edges
--                             UNION SELECT r.src, e.dep FROM reach r JOIN edges e ON e.src = r.node)
--   SELECT DISTINCT src FROM reach WHERE src = node;   -- expect 0 rows
--   SELECT asset_id, chart_id, freshness_state, reasons FROM asset_freshness
--    WHERE asset_id IN ('bo_laksana','bo_upaya') ORDER BY 1, 2;
--   -- expect: every row 'stale' with 'registry_changed' in reasons (CONSEQUENCES 1); ga_yoga and bo_bimba rows unchanged
--
-- LOCK TIMEOUT (pattern: migration 1218). The first statement below is `SET LOCAL lock_timeout = '5s'`:
-- a blocked migrate job must fail fast, not hang a shared deploy.
--
-- NEVER SHARES A PR WITH A WRITER CHANGE. This migration's effect is tied to the S-L2 window: it is applied
-- immediately before S-L2 is dispatched, as its own held PR, and never ships in a writer's PR.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file). No DDL; only
-- row updates on asset_registry (owned by amjis_app, the migration runner's role).

SET LOCAL lock_timeout = '5s';

CREATE TEMP TABLE _m1253_edges (
    asset_id text NOT NULL,
    dep      text NOT NULL
) ON COMMIT DROP;

INSERT INTO _m1253_edges (asset_id, dep) VALUES
  ('bo_laksana', 'ga_yoga'),
  ('bo_upaya',   'bo_bimba');

-- Guard 1: all-or-nothing on the involved assets, and every producer must be ACTIVE.
--   * none of the 4 involved assets present  -> empty registry: no-op (the seed carries the edges); the later
--     steps are inert too because they join asset_registry on the consumer row
--   * some present, some absent              -> RAISE (partial registry: refuse to guess)
--   * a producer inactive                    -> RAISE (dependency trap)
DO $$
DECLARE
    involved text[];
    present  text[];
    missing  text;
    bad      text;
BEGIN
    SELECT array_agg(DISTINCT x ORDER BY x) INTO involved
      FROM (SELECT asset_id AS x FROM _m1253_edges UNION SELECT dep FROM _m1253_edges) s;
    SELECT array_agg(asset_id ORDER BY asset_id) INTO present
      FROM asset_registry WHERE asset_id = ANY (involved);
    IF present IS NULL THEN
        RAISE NOTICE '1253: none of the involved assets exist in asset_registry; no-op (the seed carries the edges)';
        RETURN;
    END IF;
    SELECT string_agg(i, ', ' ORDER BY i) INTO missing
      FROM unnest(involved) i WHERE i <> ALL (present);
    IF missing IS NOT NULL THEN
        RAISE EXCEPTION '1253: involved asset(s) missing from asset_registry (partial registry; dependency trap): %', missing;
    END IF;
    SELECT string_agg(e.asset_id || ' -> ' || e.dep, ', ' ORDER BY e.asset_id, e.dep)
      INTO bad
      FROM _m1253_edges e
      JOIN asset_registry p ON p.asset_id = e.dep
     WHERE NOT p.is_active;
    IF bad IS NOT NULL THEN
        RAISE EXCEPTION '1253: edge target inactive in asset_registry (dependency trap): %', bad;
    END IF;
END $$;

-- Append only the missing deps, preserving existing order. Rows already covered are not touched.
UPDATE asset_registry r
   SET depends_on = COALESCE(r.depends_on, '{}'::text[]) || n.deps
  FROM (
        SELECT e.asset_id, array_agg(e.dep ORDER BY e.dep) AS deps
          FROM _m1253_edges e
          JOIN asset_registry c ON c.asset_id = e.asset_id
         WHERE e.dep <> ALL (COALESCE(c.depends_on, '{}'::text[]))
         GROUP BY e.asset_id
       ) n
 WHERE r.asset_id = n.asset_id;

-- Guard 2: verify it actually applied (never trust a silent no-op) and that no self-edge slipped in.
DO $$
DECLARE
    bad text;
BEGIN
    SELECT string_agg(e.asset_id || ' -> ' || e.dep, ', ' ORDER BY e.asset_id, e.dep)
      INTO bad
      FROM _m1253_edges e
      JOIN asset_registry c ON c.asset_id = e.asset_id
     WHERE e.dep <> ALL (COALESCE(c.depends_on, '{}'::text[]));
    IF bad IS NOT NULL THEN
        RAISE EXCEPTION '1253: edge not present after update: %', bad;
    END IF;
    -- scoped to the consumers this migration touches: a pre-existing self-edge elsewhere must not
    -- fail the deploy for everyone
    IF EXISTS (SELECT 1 FROM asset_registry r
                WHERE r.asset_id IN (SELECT asset_id FROM _m1253_edges)
                  AND r.asset_id = ANY (r.depends_on)) THEN
        RAISE EXCEPTION '1253: self-dependency present in asset_registry.depends_on of an edited asset';
    END IF;
END $$;

-- Guard 3: acyclicity of the post-edit graph. Reachability closure (UNION, so it terminates on cycles) started
-- from the edited consumers only: any cycle this migration could create contains one of its new edges, hence
-- one of its consumers, so reach(c, c) is the exact detector. A pre-existing cycle that does not pass through an
-- edited consumer is not this migration's to fail on.
DO $$
DECLARE
    cyc text;
BEGIN
    WITH RECURSIVE edges AS (
        SELECT r.asset_id AS src, d.dep
          FROM asset_registry r
         CROSS JOIN LATERAL unnest(COALESCE(r.depends_on, '{}'::text[])) AS d(dep)
    ),
    reach(src, node) AS (
        SELECT e.src, e.dep FROM edges e WHERE e.src IN (SELECT asset_id FROM _m1253_edges)
        UNION
        SELECT r.src, e.dep FROM reach r JOIN edges e ON e.src = r.node
    )
    SELECT string_agg(DISTINCT src, ', ' ORDER BY src) INTO cyc FROM reach WHERE src = node;
    IF cyc IS NOT NULL THEN
        RAISE EXCEPTION '1253: dependency cycle through edited asset(s) after adding edges: %', cyc;
    END IF;
END $$;

-- DOWN (ops reference, not executed by migrate.ts): remove exactly these edges.
--   UPDATE asset_registry r SET depends_on = ARRAY(
--       SELECT x FROM unnest(r.depends_on) x
--        WHERE x NOT IN (SELECT e.dep FROM (VALUES <the 2 (asset_id, dep) pairs above>) e(asset_id, dep)
--                         WHERE e.asset_id = r.asset_id))
--    WHERE r.asset_id IN ('bo_laksana','bo_upaya');

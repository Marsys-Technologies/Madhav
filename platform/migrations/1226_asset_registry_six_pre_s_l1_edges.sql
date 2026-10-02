-- 1226_asset_registry_six_pre_s_l1_edges.sql
--
-- Suvarna Track I / S-L1 prerequisite (SS ruling 2026-10-02): declare the SIX direct `depends_on` edges that
-- must exist BEFORE S-L1 (the Ganita rebuild stage) runs. Same kind as migration 1210: surgical,
-- append-only, guarded, acyclic-checked, verified by production structure afterwards.
-- Intent record: 00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1226_EDGES_INTENT_v1_0.md (travels with this PR).
--
-- APPLY TIMING RULE. MERGE = APPLY at the next deploy (migrate.ts runs on every deploy), and this file stales
-- asset_freshness for five assets on EVERY chart (CONSEQUENCES 1). It therefore merges ONLY in the S-L1 window,
-- immediately before the L1 dispatches. Order: S-L1 writer PRs deployed -> 1219 applied -> THIS migration (1226)
-- applied -> F-A2 D6 plan -> dispatches ga_positions, ga_sensitive, ga_vargas, ... Do not merge it earlier.
--
--   #  consumer (gains the edge)   producer (new dep)   why the consumer reads / will read the producer
--   1  bo_laksana                  ga_yoga              bo_laksana.py:2713,2769 read ga_yoga_firings   (Q-L2-07)
--   2  bo_upaya                    bo_bimba             bo_upaya.py:578 joins bodha_cgm_nodes          (Q-L2-07)
--   3  ga_dashas                   ga_vargas            ga_dashas_writer.py:575-587 reads chart_divisionals (Q-L1-02 a)
--   4  ga_yoga                     ga_vargas            ga_yoga_writer.py:2435-2445 reads D9 via ga_structural_writer._load_varga_positions (Q-L1-02 a)
--   5  ga_vargas                   ga_sensitive         ga_vargas will READ ga_sensitive's `kn_rao_rahu_included` karaka
--                                                       assignments instead of re-deriving them (N-69 karaka lane;
--                                                       ga_vargas_writer.py:649-675 re-derives them today)
--   6  ga_dashas                   ga_sensitive         ga_dashas will READ the same karaka assignments instead of the
--                                                       hard-coded _JAIMINI_KARAKAS (ga_dashas_writer.py:645-657; feeds
--                                                       karaka_role_at_period / karakas_active_during_period)
--
-- Live `depends_on` before this migration (read 2026-10-02, production):
--   bo_laksana {bg_rules, ga_positions, ga_strength, ga_sensitive, ga_panchanga, ga_sade_sati, ga_structural,
--               ga_nakshatra, ga_condition, ga_vargas, ga_vichara}
--   bo_upaya   {bo_laksana, bo_sangati, ga_structural, ga_dashas, bo_cgm_motifs}
--   ga_dashas  {ga_positions}
--   ga_yoga    {ga_structural, ga_dashas}
--   ga_vargas  {ga_positions}
--   (producers, unchanged: ga_sensitive {ga_positions, bg_reference}; bo_bimba {bo_laksana, bo_sudarshana,
--    bo_nakshatra_semantic, bo_arudha, bo_special_lagna, bo_vargottama_dhana})
--
-- ORDERING RULE. This migration is applied BEFORE S-L1. The S-L1 writer change that makes ga_vargas read
-- ga_sensitive, and the S-L1 build order `ga_sensitive` then `ga_vargas`, REQUIRE edge 5 (and edge 6 for
-- ga_dashas); without them the orchestrator may plan ga_vargas ahead of ga_sensitive. Do not start S-L1 until
-- the post-apply structure check below has been read from production.
--
-- NO DATA ROW CHANGES. Only asset_registry.depends_on of the five consumers is written; no other column, no
-- other row, no chart_* / bodha_* / ga_* data table. The ONE derived side effect is the registry trigger
-- described in CONSEQUENCES 1 (asset_freshness projection rows go stale); it is not a data write by this file.
--
-- ACYCLIC. By hand (to be re-proved by this migration's own guard): after the six edges
--   ga_dashas -> {ga_positions, ga_vargas, ga_sensitive};  ga_vargas -> {ga_positions, ga_sensitive};
--   ga_sensitive -> {ga_positions, bg_reference};  ga_yoga -> {ga_structural, ga_dashas, ga_vargas}.
-- ga_sensitive depends on neither ga_vargas nor ga_dashas; ga_vargas gains only ga_sensitive; no path leads back
-- from ga_sensitive / ga_vargas / ga_dashas to ga_yoga, ga_structural or ga_dashas. ga_yoga depends on no bo_*;
-- bo_bimba does not depend on bo_upaya. The migration re-checks this inside the transaction (Guard 3, a
-- recursive-CTE reachability closure over the post-edit graph) and RAISES on any cycle through an edited asset.
--
-- BEHAVIOUR. Appends only, existing array order preserved, each edge appended only if absent (idempotent: a
-- second run rewrites nothing; a fully-covered row is not touched; a NULL depends_on is treated as empty).
-- Guard 1: if NONE of the seven involved assets exists in asset_registry (a database with an empty registry:
-- the TypeScript seed, platform/scripts/seed/asset_registry_seed.ts, carries the same six edges for NEW rows;
-- its re-seed never rewrites depends_on of an existing row) the migration is a no-op; if SOME but not all
-- exist, or any producer is missing or inactive, it RAISES (a dependency trap, as in 1210). Limit, stated
-- plainly: of the seven involved assets only ga_yoga is INSERTed by a migration (240); the rest are rows the
-- TypeScript seed creates (migrations only UPDATE them), so a replay of migrations over a registry that holds
-- some but not all of them stops here by design. Every supported database (production, and CI's production
-- registry dump) holds all seven.
--
-- CONSEQUENCES (stated plainly):
--  1. Freshness goes stale AT APPLY, for every chart. asset_registry carries the trigger
--     nirmana_registry_receipt_invalidation (migration 596; AFTER UPDATE OF depends_on, ..., FOR EACH ROW WHEN
--     OLD IS DISTINCT FROM NEW), whose function runs `UPDATE asset_freshness SET freshness_state = 'stale',
--     reasons += 'registry_changed' WHERE asset_id = NEW.asset_id` with NO chart filter. So the moment this
--     UPDATE lands, every asset_freshness row of bo_laksana, bo_upaya, ga_dashas, ga_yoga and ga_vargas reads
--     'stale' (the last receipt is kept; only the projection flips; the next governed build re-establishes
--     fresh). The staleness stays until each chart's rebuild re-establishes a fresh receipt. Read from
--     production 2026-10-02: one chart carries these rows (ga_dashas, ga_yoga, ga_vargas fresh; bo_laksana
--     and bo_upaya one fresh and one stale row each). Through the hard dependency gate
--     (item 4) a stale ga_vargas gates ga_dashas and ga_yoga, and a stale ga_yoga gates bo_laksana, until the
--     rebuild: this IS the intended S-L1 order (ga_sensitive -> ga_vargas -> ga_dashas / ga_yoga -> ...), so
--     S-L1 should follow the apply immediately; anything that reads asset_freshness = 'fresh' for these five
--     assets (and the dependents of ga_dashas, ga_yoga, ga_vargas) sees stale until then. A second run does
--     not re-fire the trigger (nothing changes, so OLD IS NOT DISTINCT FROM NEW).
--  2. Upstream hash. `compute_upstream_hash` hashes DECLARED deps, so it changes ONCE for bo_laksana, bo_upaya,
--     ga_dashas, ga_yoga and ga_vargas: a one-time rebuild signal at their next dispatch. With S-L1 rebuilding
--     the Ganita layer in DAG order this costs nothing extra.
--  3. Frozen manifests. Each edited asset's Nirmana-frozen manifest (where one exists) no longer matches the
--     live registry: `assertManifestMatchesRegistryIdentity` throws on any depends_on change, so the monitor
--     reports `plan_adaptation_required` for them (same effect as 1210), and scripts/dispatch_nirmana_campaign_wave.py
--     refuses a wave whose frozen asset's live depends_on changed. No other run may be dispatching or running
--     these assets at apply (an OPERATOR check, not enforced in this file: the 0-active-runs query below).
--  4. Hard dependency gate. asset_runner.deps_unsatisfied (enforce mode) requires every declared dep to be
--     asset_throughput.state 'lit' (or 'service_ok') AND its latest asset_freshness 'fresh'. The new
--     edges 1, 2 and 4 duplicate existing transitive paths (they cost nothing); edges 3, 5 and 6 add NEW
--     prerequisites: ga_dashas now waits for ga_vargas (3), and ga_vargas (5) and ga_dashas (6) now wait for
--     ga_sensitive. That is exactly the S-L1 build order (ga_sensitive -> ga_vargas -> ga_dashas ...).
--  5. Cockpit direct blocking radius of the four producers rises by their new direct consumers.
--
-- APPLY ONLY WHEN no build_runs row is in state planned/running/paused (verify at apply: SELECT count(*) FROM
-- build_runs WHERE state IN ('planned','running','paused') must be 0; read 2026-10-02: 0, and 0 runs involving
-- any of the seven assets). runner.py `_verify_registry_still_matches_manifest` compares each planned asset's
-- live depends_on against the run's frozen manifest; a run planned/running across the deploy has its diverged
-- assets terminalized.
--
-- VERIFICATION AFTER APPLY is by PRODUCTION STRUCTURE, not by the deploy log (Trap 103: a deploy run's head_sha
-- metadata can disagree with the SHA actually deployed, and a green deploy can hide a no-op migration):
--   SELECT asset_id, depends_on FROM asset_registry
--    WHERE asset_id IN ('bo_laksana','bo_upaya','ga_dashas','ga_yoga','ga_vargas') ORDER BY 1;
--   -- expect: bo_laksana has ga_yoga; bo_upaya has bo_bimba; ga_dashas has ga_vargas and ga_sensitive;
--   --         ga_yoga has ga_vargas; ga_vargas has ga_sensitive
--   and the acyclicity closure over the FULL registry (Guard 3 seeds only from the edited consumers; this drops
--   that filter, so it would also show a pre-existing cycle elsewhere) returns no row:
--   WITH RECURSIVE edges AS (SELECT r.asset_id AS src, d.dep FROM asset_registry r
--                             CROSS JOIN LATERAL unnest(COALESCE(r.depends_on, '{}'::text[])) AS d(dep)),
--        reach(src, node) AS (SELECT src, dep FROM edges
--                             UNION SELECT r.src, e.dep FROM reach r JOIN edges e ON e.src = r.node)
--   SELECT DISTINCT src FROM reach WHERE src = node;   -- expect 0 rows
--   SELECT asset_id, chart_id, freshness_state, reasons FROM asset_freshness
--    WHERE asset_id IN ('bo_laksana','bo_upaya','ga_dashas','ga_yoga','ga_vargas') ORDER BY 1, 2;
--   -- expect: every row 'stale' with 'registry_changed' in reasons (CONSEQUENCES 1); ga_sensitive and bo_bimba
--   --         rows unchanged
--
-- LOCK TIMEOUT (pattern: migration 1218). The first statement below is `SET LOCAL lock_timeout = '5s'`:
-- a blocked migrate job must fail fast, not hang a shared deploy.
--
-- NEVER SHARES A PR WITH A WRITER CHANGE. This migration must PRECEDE the writer RUNS that rely on its edges (the
-- S-L1 dispatches), and may travel with or before the writer deploy; the effect of a migration that is only valid
-- with or after a new writer image must never ship in that writer's PR.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file). No DDL; only
-- row updates on asset_registry (owned by amjis_app, the migration runner's role).

SET LOCAL lock_timeout = '5s';

CREATE TEMP TABLE _m1226_edges (
    asset_id text NOT NULL,
    dep      text NOT NULL
) ON COMMIT DROP;

INSERT INTO _m1226_edges (asset_id, dep) VALUES
  ('bo_laksana', 'ga_yoga'),
  ('bo_upaya',   'bo_bimba'),
  ('ga_dashas',  'ga_sensitive'),
  ('ga_dashas',  'ga_vargas'),
  ('ga_yoga',    'ga_vargas'),
  ('ga_vargas',  'ga_sensitive');

-- Guard 1: all-or-nothing on the involved assets, and every producer must be ACTIVE.
--   * none of the 7 involved assets present  -> empty registry: no-op (the seed carries the edges); the later
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
      FROM (SELECT asset_id AS x FROM _m1226_edges UNION SELECT dep FROM _m1226_edges) s;
    SELECT array_agg(asset_id ORDER BY asset_id) INTO present
      FROM asset_registry WHERE asset_id = ANY (involved);
    IF present IS NULL THEN
        RAISE NOTICE '1226: none of the involved assets exist in asset_registry; no-op (the seed carries the edges)';
        RETURN;
    END IF;
    SELECT string_agg(i, ', ' ORDER BY i) INTO missing
      FROM unnest(involved) i WHERE i <> ALL (present);
    IF missing IS NOT NULL THEN
        RAISE EXCEPTION '1226: involved asset(s) missing from asset_registry (partial registry; dependency trap): %', missing;
    END IF;
    SELECT string_agg(e.asset_id || ' -> ' || e.dep, ', ' ORDER BY e.asset_id, e.dep)
      INTO bad
      FROM _m1226_edges e
      JOIN asset_registry p ON p.asset_id = e.dep
     WHERE NOT p.is_active;
    IF bad IS NOT NULL THEN
        RAISE EXCEPTION '1226: edge target inactive in asset_registry (dependency trap): %', bad;
    END IF;
END $$;

-- Append only the missing deps, preserving existing order. Rows already covered are not touched.
UPDATE asset_registry r
   SET depends_on = COALESCE(r.depends_on, '{}'::text[]) || n.deps
  FROM (
        SELECT e.asset_id, array_agg(e.dep ORDER BY e.dep) AS deps
          FROM _m1226_edges e
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
      FROM _m1226_edges e
      JOIN asset_registry c ON c.asset_id = e.asset_id
     WHERE e.dep <> ALL (COALESCE(c.depends_on, '{}'::text[]));
    IF bad IS NOT NULL THEN
        RAISE EXCEPTION '1226: edge not present after update: %', bad;
    END IF;
    -- scoped to the consumers this migration touches: a pre-existing self-edge elsewhere must not
    -- fail the deploy for everyone
    IF EXISTS (SELECT 1 FROM asset_registry r
                WHERE r.asset_id IN (SELECT asset_id FROM _m1226_edges)
                  AND r.asset_id = ANY (r.depends_on)) THEN
        RAISE EXCEPTION '1226: self-dependency present in asset_registry.depends_on of an edited asset';
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
        SELECT e.src, e.dep FROM edges e WHERE e.src IN (SELECT asset_id FROM _m1226_edges)
        UNION
        SELECT r.src, e.dep FROM reach r JOIN edges e ON e.src = r.node
    )
    SELECT string_agg(DISTINCT src, ', ' ORDER BY src) INTO cyc FROM reach WHERE src = node;
    IF cyc IS NOT NULL THEN
        RAISE EXCEPTION '1226: dependency cycle through edited asset(s) after adding edges: %', cyc;
    END IF;
END $$;

-- DOWN (ops reference, not executed by migrate.ts): remove exactly these edges.
--   UPDATE asset_registry r SET depends_on = ARRAY(
--       SELECT x FROM unnest(r.depends_on) x
--        WHERE x NOT IN (SELECT e.dep FROM (VALUES <the 6 (asset_id, dep) pairs above>) e(asset_id, dep)
--                         WHERE e.asset_id = r.asset_id))
--    WHERE r.asset_id IN ('bo_laksana','bo_upaya','ga_dashas','ga_yoga','ga_vargas');

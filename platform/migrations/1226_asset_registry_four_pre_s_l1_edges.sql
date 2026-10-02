-- 1226_asset_registry_four_pre_s_l1_edges.sql
--
-- Suvarna Track I / S-L1 prerequisite (SS ruling 2026-10-02, option B): declare the FOUR direct `depends_on`
-- edges between L1 (Ganita) assets that must exist BEFORE S-L1 (the Ganita rebuild stage) runs. Same kind as
-- migration 1210: surgical, append-only, guarded, acyclic-checked, verified by production structure afterwards.
-- The two L2 edges of the original six (bo_laksana += ga_yoga, bo_upaya += bo_bimba) are NOT here: they are
-- migration 1253 (its own held PR), applied immediately before S-L2 is dispatched.
-- Intent record: 00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1226_EDGES_INTENT_v1_0.md (travels with this PR).
--
-- APPLY TIMING RULE. MERGE = APPLY at the next deploy (migrate.ts runs on every deploy), and this file stales
-- asset_freshness for THREE assets (ga_vargas, ga_dashas, ga_yoga) on EVERY chart (CONSEQUENCES 1). It therefore
-- merges ONLY in the S-L1 window, immediately before the L1 dispatches. Order: S-L1 writer PRs deployed -> 1219
-- applied -> THIS migration (1226) applied -> F-A2 D6 plan -> dispatches ga_positions, ga_sensitive, ga_vargas,
-- ... Do not merge it earlier.
--
--   #  consumer (gains the edge)   producer (new dep)   why the consumer reads / will read the producer
--   1  ga_dashas                   ga_vargas            ga_dashas_writer.py:575-587 reads chart_divisionals (Q-L1-02 a)
--   2  ga_yoga                     ga_vargas            ga_yoga_writer.py:2435-2445 reads D9 via ga_structural_writer._load_varga_positions (Q-L1-02 a)
--   3  ga_vargas                   ga_sensitive         ga_vargas will READ ga_sensitive's `kn_rao_rahu_included` karaka
--                                                       assignments instead of re-deriving them (N-69 karaka lane;
--                                                       ga_vargas_writer.py:649-675 re-derives them today)
--   4  ga_dashas                   ga_sensitive         ga_dashas will READ the same karaka assignments instead of the
--                                                       hard-coded _JAIMINI_KARAKAS (ga_dashas_writer.py:645-657; feeds
--                                                       karaka_role_at_period / karakas_active_during_period)
--
-- Live `depends_on` before this migration (read 2026-10-02, production):
--   ga_dashas  {ga_positions}
--   ga_yoga    {ga_structural, ga_dashas}
--   ga_vargas  {ga_positions}
--   (producer, unchanged: ga_sensitive {ga_positions, bg_reference})
--
-- ORDERING RULE. This migration is applied BEFORE S-L1. The S-L1 writer change that makes ga_vargas read
-- ga_sensitive, and the S-L1 build order `ga_sensitive` then `ga_vargas`, REQUIRE edge 3 (and edge 4 for
-- ga_dashas); without them the orchestrator may plan ga_vargas ahead of ga_sensitive. Do not start S-L1 until
-- the post-apply structure check below has been read from production.
--
-- NO DATA ROW CHANGES. Only asset_registry.depends_on of the three consumers is written; no other column, no
-- other row, no chart_* / bodha_* / ga_* data table. The ONE derived side effect is the registry trigger
-- described in CONSEQUENCES 1 (asset_freshness projection rows go stale); it is not a data write by this file.
--
-- ACYCLIC. By hand (to be re-proved by this migration's own guard): after the four edges
--   ga_dashas -> {ga_positions, ga_vargas, ga_sensitive};  ga_vargas -> {ga_positions, ga_sensitive};
--   ga_sensitive -> {ga_positions, bg_reference};  ga_yoga -> {ga_structural, ga_dashas, ga_vargas}.
-- ga_sensitive depends on neither ga_vargas nor ga_dashas; ga_vargas gains only ga_sensitive; no path leads back
-- from ga_sensitive / ga_vargas / ga_dashas to ga_yoga, ga_structural or ga_dashas. The migration re-checks this
-- inside the transaction (Guard 3, a recursive-CTE reachability closure over the post-edit graph) and RAISES on
-- any cycle through an edited asset. Together with 1253's two edges the union stays acyclic (checked offline,
-- read-only, against the live 129-asset graph); either order of the two migrations is valid.
--
-- BEHAVIOUR. Appends only, existing array order preserved, each edge appended only if absent (idempotent: a
-- second run rewrites nothing; a fully-covered row is not touched; a NULL depends_on is treated as empty).
-- Guard 1: if NONE of the four involved assets exists in asset_registry (a database with an empty registry:
-- the TypeScript seed, platform/scripts/seed/asset_registry_seed.ts, carries the same four edges for NEW rows;
-- its re-seed never rewrites depends_on of an existing row) the migration is a no-op; if SOME but not all
-- exist, or any producer is missing or inactive, it RAISES (a dependency trap, as in 1210). Limit, stated
-- plainly: of the four involved assets only ga_yoga is INSERTed by a migration (240); the rest are rows the
-- TypeScript seed creates (migrations only UPDATE them), so a replay of migrations over a registry that holds
-- some but not all of them stops here by design. Every supported database (production, and CI's production
-- registry dump) holds all four.
--
-- CONSEQUENCES (stated plainly):
--  1. Freshness goes stale AT APPLY, for every chart, for exactly THREE assets. asset_registry carries the
--     trigger nirmana_registry_receipt_invalidation (migration 596; AFTER UPDATE OF depends_on, ..., FOR EACH ROW
--     WHEN OLD IS DISTINCT FROM NEW), whose function runs `UPDATE asset_freshness SET freshness_state = 'stale',
--     reasons += 'registry_changed' WHERE asset_id = NEW.asset_id` with NO chart filter. So the moment this
--     UPDATE lands, every asset_freshness row of ga_vargas, ga_dashas and ga_yoga reads 'stale' (the last
--     receipt is kept; only the projection flips; the next governed build re-establishes fresh). ga_sensitive is
--     a PRODUCER here and is not touched, and bo_laksana / bo_upaya are NOT staled by this migration (their
--     edges are 1253's). The staleness stays until each chart's rebuild re-establishes a fresh receipt. Serving
--     effect on the canonical chart (SS): exactly those three flip from resolved to unresolved until rebuilt,
--     about 37 min typical compute. Read from production 2026-10-02: one chart carries these rows (ga_dashas,
--     ga_yoga, ga_vargas: one fresh row each). Through the hard dependency gate (item 4) a stale ga_vargas gates
--     ga_dashas, ga_yoga and every other declared dependent of ga_vargas / ga_dashas / ga_yoga until the rebuild:
--     this IS the intended S-L1 order (ga_sensitive -> ga_vargas -> ga_dashas / ga_yoga -> ...), so S-L1 should
--     follow the apply immediately. A second run does not re-fire the trigger (nothing changes, so OLD IS NOT
--     DISTINCT FROM NEW).
--  2. Upstream hash. `compute_upstream_hash` hashes DECLARED deps, so it changes ONCE for ga_dashas, ga_yoga and
--     ga_vargas: a one-time rebuild signal at their next dispatch. With S-L1 rebuilding the Ganita layer in DAG
--     order this costs nothing extra.
--  3. Frozen manifests. Each edited asset's Nirmana-frozen manifest (where one exists) no longer matches the
--     live registry: `assertManifestMatchesRegistryIdentity` throws on any depends_on change, so the monitor
--     reports `plan_adaptation_required` for them (same effect as 1210), and scripts/dispatch_nirmana_campaign_wave.py
--     refuses a wave whose frozen asset's live depends_on changed. No other run may be dispatching or running
--     these assets at apply (an OPERATOR check, not enforced in this file: the 0-active-runs query below).
--  4. Hard dependency gate. asset_runner.deps_unsatisfied (enforce mode) requires every declared dep to be
--     asset_throughput.state 'lit' (or 'service_ok') AND its latest asset_freshness 'fresh'. Edge 2
--     (ga_yoga -> ga_vargas) duplicates an existing transitive path (no new ORDERING constraint; the producer is
--     now also checked directly for lit/fresh, which the apply-time staleness in item 1 makes moot); edges 1, 3
--     and 4 add NEW prerequisites: ga_dashas now waits for ga_vargas (1), and ga_vargas (3) and ga_dashas (4) now
--     wait for ga_sensitive. That is exactly the S-L1 build order (ga_sensitive -> ga_vargas -> ga_dashas ...).
--  5. Cockpit direct blocking radius of ga_vargas and ga_sensitive rises by their new direct consumers.
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
--    WHERE asset_id IN ('ga_dashas','ga_yoga','ga_vargas') ORDER BY 1;
--   -- expect: ga_dashas has ga_vargas and ga_sensitive; ga_yoga has ga_vargas; ga_vargas has ga_sensitive
--   and the acyclicity closure over the FULL registry (Guard 3 seeds only from the edited consumers; this drops
--   that filter, so it would also show a pre-existing cycle elsewhere) returns no row:
--   WITH RECURSIVE edges AS (SELECT r.asset_id AS src, d.dep FROM asset_registry r
--                             CROSS JOIN LATERAL unnest(COALESCE(r.depends_on, '{}'::text[])) AS d(dep)),
--        reach(src, node) AS (SELECT src, dep FROM edges
--                             UNION SELECT r.src, e.dep FROM reach r JOIN edges e ON e.src = r.node)
--   SELECT DISTINCT src FROM reach WHERE src = node;   -- expect 0 rows
--   SELECT asset_id, chart_id, freshness_state, reasons FROM asset_freshness
--    WHERE asset_id IN ('ga_dashas','ga_yoga','ga_vargas') ORDER BY 1, 2;
--   -- expect: every row 'stale' with 'registry_changed' in reasons (CONSEQUENCES 1); ga_sensitive rows unchanged
--
-- LOCK TIMEOUT (pattern: migration 1218). The first statement below is `SET LOCAL lock_timeout = '5s'`:
-- a blocked migrate job must fail fast, not hang a shared deploy.
--
-- NEVER SHARES A PR WITH A WRITER CHANGE. The binding rule is that this migration must PRECEDE the writer RUNS that
-- rely on its edges (the S-L1 dispatches); relative to the writer image DEPLOY either order is safe (the apply
-- order in the APPLY TIMING RULE above has the writer PRs deployed first, and applying it with or before them is
-- equally valid). A migration whose effect is only valid with or after a new writer image must never ship in that
-- writer's PR.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file). No DDL; only
-- row updates on asset_registry (owned by amjis_app, the migration runner's role).

SET LOCAL lock_timeout = '5s';

CREATE TEMP TABLE _m1226_edges (
    asset_id text NOT NULL,
    dep      text NOT NULL
) ON COMMIT DROP;

INSERT INTO _m1226_edges (asset_id, dep) VALUES
  ('ga_dashas',  'ga_sensitive'),
  ('ga_dashas',  'ga_vargas'),
  ('ga_yoga',    'ga_vargas'),
  ('ga_vargas',  'ga_sensitive');

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
--        WHERE x NOT IN (SELECT e.dep FROM (VALUES <the 4 (asset_id, dep) pairs above>) e(asset_id, dep)
--                         WHERE e.asset_id = r.asset_id))
--    WHERE r.asset_id IN ('ga_dashas','ga_yoga','ga_vargas');

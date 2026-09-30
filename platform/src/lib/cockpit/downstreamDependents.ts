// Packet B2 ("the DAG-derived downstream count") — the query behind
// AssetStats.downstream_dependent_count on /api/cockpit/stats.
//
// This is a plain parameterless SELECT, deliberately NOT a database view: the
// migration login has no CREATE on schema public, so a CREATE VIEW migration
// (the original 1202) would fail and break every deploy. The recursive CTE
// below is the exact body that view had; it reads the LIVE asset_registry.depends_on
// graph on every call, so it has nothing to go stale (§N.8) and needs no DDL,
// no GRANT, and no presence probe — asset_registry always exists.
//
// WHAT IT COMPUTES: for each ACTIVE asset A, the size of the reverse-transitive-
// closure of the depends_on DAG rooted at A, RESTRICTED TO is_active = true assets
// on BOTH sides — i.e. how many OTHER active assets would need a rebuild if A's
// data changed. An UPPER BOUND on what a failure of A COULD affect, never a
// prediction of what a failure HAS or WILL affect (the packet's before-measurement
// found this static DAG figure does not predict observed cascade ranking; that is
// driven by incident frequency, not graph shape). Deliberately not named "blocking
// radius": that phrase already names the empirical quantity in
// 00_ARCHITECTURE/briefs/nirmana/BUILD_FAILURE_TRIAGE_2026-09-26_v1_0.md.
//
// C-1 (review B2_review_20260926T202916Z.md): is_active is filtered on the EDGE
// SOURCE (an inactive asset's depends_on never propagates into anyone's closure)
// and on the OUTER asset list (an inactive asset is never a rebuild target).
// This mirrors plan.ts's computeDownstreamClosure() over the registry that
// runs/route.ts loads with `WHERE is_active = true` — without the filter the
// query and the planner disagreed on 13 of 129 real assets (ga_positions 80 vs 79).
//
// `UNION` (not `UNION ALL`) in the closure CTE is load-bearing twice over: it
// terminates on a cycle in depends_on (a repeated (dependent, upstream) pair adds
// no new row), and it collapses diamond convergence — on the real 129-asset graph
// `UNION ALL` exhausts a 512 MB temp_file_limit in ~3 s (review C-3).
//
// SELF IS NEVER ITS OWN DEPENDENT: `c.dependent <> ar.asset_id` in the join. On the
// acyclic registry production has (plan.ts rejects cycles) this changes nothing;
// on a malformed cyclic registry the closure would otherwise contain (a, a) and
// count `a` among "OTHER assets that depend on a" — plan.ts's BFS and the test's
// independent BFS both exclude the seed, and so does this.
//
// HONESTY AT ZERO: the LEFT JOIN gives every active asset a row, and
// count(DISTINCT ...) over a NULL-only join group is 0, not NULL — a leaf reads as
// a real, present 0 ("no downstream impact"), never as an absent row a caller
// could mistake for "not computed". "Not computed" (the query failed) is handled
// by the route, which degrades to null.
//
// Tests: src/app/api/cockpit/stats/__tests__/downstream_dependent_count.test.ts
// (mocked query, route contract) and
// tests/integration/downstream_dependents.db.test.ts (this exact SQL against real
// Postgres: synthetic DAG with diamond + cycle, and the frozen real registry).

/** The `edges` + `closure` CTE pair — exported separately so a test can assert
 *  the closure holds at most one row per (dependent, upstream) pair. */
export const DOWNSTREAM_CLOSURE_CTE = `WITH RECURSIVE edges AS (
  SELECT asset_id AS dependent, unnest(depends_on) AS upstream
  FROM asset_registry
  WHERE is_active = true
),
closure AS (
  SELECT dependent, upstream FROM edges
  UNION
  SELECT c.dependent, e.upstream
  FROM closure c
  JOIN edges e ON e.dependent = c.upstream
)`

/** Registry-wide (chart-independent — the DAG is the same for every chart), no
 *  bound parameters. Rows: { asset_id, downstream_dependent_count } for every
 *  ACTIVE asset (count arrives as a string from pg's bigint — callers Number() it). */
export const DOWNSTREAM_DEPENDENTS_SQL = `${DOWNSTREAM_CLOSURE_CTE}
SELECT
  ar.asset_id,
  count(DISTINCT c.dependent) AS downstream_dependent_count
FROM asset_registry ar
LEFT JOIN closure c ON c.upstream = ar.asset_id AND c.dependent <> ar.asset_id
WHERE ar.is_active = true
GROUP BY ar.asset_id`

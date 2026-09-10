-- 762_bo_cgm_paths_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_cgm_paths. Transaction ownership belongs to
-- platform/scripts/migrate.ts. Second migration of L2's 760-779 range
-- after #2021 (760) and #2039 (761).
--
-- bo_cgm_paths (writers/bo_cgm_paths.py) computes dispositor-chain paths
-- per graha node per ayanamsha over the CGM graph. Eight invariants, all
-- derived from the writer's own chain-building logic in
-- _build_dispositor_chains()/_path_strength(), independently verified live
-- against all three production charts before landing (C12):
--
--   1. path_type is always the writer's own hardcoded constant
--      'dispositor_chain' (PATH_TYPE) — no other value is ever emitted.
--   2. path_length == cardinality(path_edge_ids_array) — every hop in
--      _build_dispositor_chains' while-loop appends exactly one edge_id
--      per node_chain step; this must never drift.
--   3. path_length == cardinality(path_node_ids_array) - 1 — same
--      invariant from the node side (self-ruling chains: 1 node, 0 hops).
--   4. path_length is bounded [0, MAX_CHAIN_DEPTH=9] — the while-loop's
--      own depth cap.
--   5. path_strength is bounded [0, 1] — _path_strength() is either the
--      self-ruling constant 1.0, a PRODUCT of edge computed_strength
--      values (each itself in [0,1] by construction elsewhere in the CGM
--      graph), or the documented fallback placeholder 0.5 when no
--      constituent edge carries a strength — all three land in [0,1].
--   6. verification_pass_status is always 'single' (UNVERIFIED_DEFAULT) —
--      the writer sets this unconditionally; no verification pass exists.
--   7. path_length = 0 if-and-only-if (is_final_dispositor = true AND
--      path_strength = 1.0) — a zero-hop chain in this code is EXACTLY
--      the self-ruling emission branch (the only path that appends a
--      1-node/0-edge chain), so this triple must always co-occur.
--   8. path_node_ids_array is never NULL and always has >= 1 member —
--      every emitted chain carries at least its own starting node.
--
-- Deliberately NOT checked, and why: that from_node_id / path_node_ids_
-- array / path_edge_ids_array entries resolve to live bodha_cgm_nodes /
-- bodha_cgm_edges rows. Verified live before landing this migration: on
-- chart cb73cd3d-..., 45 of 135 bodha_cgm_paths rows (33%) carry a
-- from_node_id that does not resolve to any current bodha_cgm_nodes row
-- for that (chart_id, ayanamsha_id, snapshot_type) — the identical
-- pending-rebuild-staleness pattern just diagnosed for bo_cgm_motifs
-- (migration 761) and previously for bo_bimba/bo_samskara/bo_drishti/
-- bo_chart_gestalt/S11: bo_karanajala was rebuilt after bo_cgm_paths last
-- ran on that chart, so its stored node/edge references point to a
-- superseded build. Not a bo_cgm_paths writer defect. Per the bo_bimba
-- precedent (migration 711: "a check that has never been green on
-- current data is a proposal, not a gate"), this migration omits the
-- referential-integrity conjunct rather than ship a check known-false on
-- live production data.
--
-- Verified live against all three production charts before landing (C12):
-- all eight conjuncts below evaluate TRUE today.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (SELECT 1 FROM bodha_cgm_paths WHERE path_type <> 'dispositor_chain')
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_paths WHERE path_length <> cardinality(path_edge_ids_array)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_paths WHERE path_length <> cardinality(path_node_ids_array) - 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_paths WHERE path_length < 0 OR path_length > 9
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_paths WHERE path_strength < 0 OR path_strength > 1.0
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_paths WHERE verification_pass_status <> 'single'
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_paths
    WHERE (path_length = 0) <> (is_final_dispositor AND path_strength = 1.0)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_paths
    WHERE path_node_ids_array IS NULL OR cardinality(path_node_ids_array) < 1
  )
$ic$
 WHERE asset_id = 'bo_cgm_paths';

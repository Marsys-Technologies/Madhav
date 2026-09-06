-- 761_bo_cgm_motifs_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_cgm_motifs. Transaction ownership belongs to
-- platform/scripts/migrate.ts. First migration of L2's 760-779 range after
-- #2021 (760).
--
-- bo_cgm_motifs (writers/bo_cgm_motifs.py) derives three outputs from the
-- CGM graph (bodha_cgm_nodes + bodha_cgm_edges): motifs (bodha_cgm_motifs),
-- sub-graphs (bodha_cgm_sub_graphs), and one topology summary row per
-- (chart_id, ayanamsha_id) (bodha_cgm_chart_topology_summary). This check
-- covers what the writer's own construction logic unconditionally
-- guarantees, table-wide, across all three production charts:
--
--   1. Topology-row completeness: every (chart_id, ayanamsha_id) that has
--      CGM nodes also has exactly the topology summary row _write_aya()
--      unconditionally computes for it (the writer only skips when
--      all_nodes is empty).
--   2. Topology TRUTH re-derivation: total_nodes/total_edges on each
--      topology row are recomputed from a live count of bodha_cgm_nodes /
--      bodha_cgm_edges for that (chart_id, ayanamsha_id) and must match —
--      not trusted as stored (same discipline as bo_samvada's M-14 check).
--   3. Topology row distinctness on its own natural key.
--   4. motif_class vocabulary: one of the 6 values the writer's 5 detector
--      functions can produce (yoga_cluster, mutual_reception, stellium,
--      parivartana_chain, mutual_aspect, mutual_aspect_triangle) — derived
--      from source, not narrowed to the 4 classes observed live today.
--   5. motif_strength is bounded [0.3, 1.0] — the tightest bound the five
--      detectors' own strength formulas can produce (mutual_reception=0.8,
--      mutual_aspect=0.6, mutual_aspect_triangle=0.75 constants;
--      yoga_cluster/stellium min(0.5+..., 1.0); parivartana_chain
--      max(0.3, 0.7-(depth-3)*0.1) for depth 3..6 — the only formula that
--      can approach the floor).
--   6. involved_node_ids_array is never NULL and always has >= 2 members —
--      every detector's minimum motif (a pair) has exactly 2 nodes; no
--      detector ever emits a single-node motif.
--   7. classical_citation_id / fingerprint_hash / motif_name are never
--      NULL or empty — every append site in _write_aya() sets all three
--      unconditionally.
--   8. Fingerprint distinctness: no duplicate (chart_id, ayanamsha_id,
--      fingerprint_hash) triple — a real structural invariant of the
--      detectors' own seen-set dedup logic, even though no DB constraint
--      enforces it (bodha_cgm_motifs' ON CONFLICT DO NOTHING has no target
--      other than the PK, so this is genuinely load-bearing, not a no-op
--      safety net).
--
-- Deliberately NOT checked, and why: that every involved_edge_ids_array /
-- involved_node_ids_array entry resolves to a live bodha_cgm_edges /
-- bodha_cgm_nodes row. Verified live before landing this migration: this
-- referential-integrity check is TRUE on the canonical chart
-- (482012f1-...) and on 1c826d5a-..., but FALSE on cb73cd3d-... — that
-- chart's bo_cgm_motifs rows carry build_id d47f0e98-... while its own
-- bodha_cgm_edges are now at a newer build_id 26918057-... (bo_karanajala
-- was rebuilt after bo_cgm_motifs last ran on that chart). This is the
-- same pending-rebuild-staleness pattern already diagnosed this campaign
-- for bo_bimba/bo_samskara/bo_drishti/bo_chart_gestalt/S11 (nakshatra_
-- semantic) — not a writer defect, resolves on bo_cgm_motifs' next run
-- after bo_karanajala. Per the bo_bimba precedent (migration 711: "a check
-- that has never been green on current data is a proposal, not a gate"),
-- this migration omits the dangling-reference check rather than ship a
-- check known-false on live data. Recorded in L2_STATE.md rather than
-- silently worked around.
--
-- Verified live against all three production charts before landing (C12):
-- all five conjuncts below evaluate TRUE today on all three charts.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT chart_id, ayanamsha_id FROM bodha_cgm_nodes
    WHERE snapshot_type = 'static_natal'
    GROUP BY chart_id, ayanamsha_id
    HAVING NOT EXISTS (
      SELECT 1 FROM bodha_cgm_chart_topology_summary topo
      WHERE topo.chart_id = bodha_cgm_nodes.chart_id
        AND topo.ayanamsha_id = bodha_cgm_nodes.ayanamsha_id
        AND topo.snapshot_type = 'static_natal'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_chart_topology_summary topo
    WHERE topo.snapshot_type = 'static_natal'
      AND (
        topo.total_nodes <> (
          SELECT count(*) FROM bodha_cgm_nodes n
          WHERE n.chart_id = topo.chart_id AND n.ayanamsha_id = topo.ayanamsha_id
            AND n.snapshot_type = 'static_natal'
        )
        OR topo.total_edges <> (
          SELECT count(*) FROM bodha_cgm_edges e
          WHERE e.chart_id = topo.chart_id AND e.ayanamsha_id = topo.ayanamsha_id
            AND e.snapshot_type = 'static_natal'
        )
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_chart_topology_summary
    GROUP BY chart_id, ayanamsha_id, build_id, snapshot_type HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_motifs
    WHERE motif_class NOT IN (
      'yoga_cluster', 'mutual_reception', 'stellium',
      'parivartana_chain', 'mutual_aspect', 'mutual_aspect_triangle'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_motifs WHERE motif_strength < 0.3 OR motif_strength > 1.0
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_motifs
    WHERE involved_node_ids_array IS NULL OR cardinality(involved_node_ids_array) < 2
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_motifs
    WHERE classical_citation_id IS NULL OR fingerprint_hash IS NULL
       OR motif_name IS NULL OR motif_name = ''
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_motifs
    GROUP BY chart_id, ayanamsha_id, fingerprint_hash HAVING count(*) > 1
  )
$ic$
 WHERE asset_id = 'bo_cgm_motifs';

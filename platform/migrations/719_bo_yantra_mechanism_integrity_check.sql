-- 719_bo_yantra_mechanism_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_yantra_mechanism. Transaction ownership
-- belongs to platform/scripts/migrate.ts. Tenth migration of L2's
-- 710-729 range.
--
-- Nine invariants, all independently verified live against all three
-- production charts before landing (C12). Caught and corrected my own
-- wrong guess before shipping: the module docstring describes member-EDGE
-- valence as harmonious/antagonistic/mixed/neutral, but
-- valence_doctrine.mechanism_valence_from_edges() (the real producer,
-- checked directly in brahmagyan/valence_doctrine.py:340-356) OUTPUTS a
-- different vocabulary -- benefic/malefic/mixed/neutral -- confirmed
-- against live data (1157/475/131/105 rows) before writing the check.
--
--   1. mechanism_class is one of the 10 values the writer's own emit
--      sites can produce: 4 hardcoded structural literals
--      (dispositor_cycle, convergent_dispositor_chain,
--      house_lordship_cycle, graha_bhava_affliction) + the 6
--      bodha_cgm_motifs motif_class values it promotes 1:1 (yoga_cluster,
--      mutual_reception, parivartana_chain, stellium, mutual_aspect,
--      mutual_aspect_triangle) -- 8 of 10 observed live, all 10 legal.
--   2. valence is one of the 4 values mechanism_valence_from_edges() can
--      return (benefic, malefic, mixed, neutral).
--   3. member_node_ids_array is never NULL and never empty (a mechanism
--      with zero member nodes is not a mechanism).
--   4. mechanism_name is never NULL or empty.
--   5. fingerprint_hash is never NULL (the writer's own de-dup key --
--      ON CONFLICT (chart_id, ayanamsha_id, build_id, mechanism_class,
--      fingerprint_hash) DO NOTHING, writers/bo_yantra_mechanism.py:95).
--   6. verification_pass_status is always the honest UNVERIFIED_DEFAULT
--      ('single') -- this writer promotes/aggregates already-computed
--      upstream structure, it does not independently re-verify it.
--   7. ayanamsha_id is one of the 5 canonical ayanamshas.
--   8. edge_strength_min <= edge_strength_avg <= edge_strength_max
--      wherever all three are non-NULL (a real min/avg/max ordering
--      constraint the writer's own _edge_strength_summary() computes).
--   9. Distinctness on both the primary key shape (mechanism_id) and the
--      writer's own documented de-dup tuple (chart_id, ayanamsha_id,
--      build_id, mechanism_class, fingerprint_hash) -- defense-in-depth
--      alongside the DB-level ON CONFLICT clause, not a replacement for it.
--
-- Deliberately NOT checked: member_node_ids_array / member_edge_ids_array
-- resolving to live bodha_cgm_nodes/bodha_cgm_edges rows -- this writer
-- reads from bodha_cgm_motifs and bodha_cgm_edges, the same tables #1888/
-- D-CND-29 already found genuinely orphaned relative to the current
-- bodha_cgm_nodes generation. Same scoping discipline as bo_anveshana's
-- migration 718: check the writer's own vocabulary/bounds/non-null
-- guarantees, not cross-table freshness that's already a tracked, open
-- finding elsewhere.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT 1 FROM bodha_mechanisms
    WHERE mechanism_class NOT IN (
      'dispositor_cycle', 'convergent_dispositor_chain', 'house_lordship_cycle',
      'graha_bhava_affliction', 'yoga_cluster', 'mutual_reception',
      'parivartana_chain', 'stellium', 'mutual_aspect', 'mutual_aspect_triangle'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_mechanisms
    WHERE valence NOT IN ('benefic', 'malefic', 'mixed', 'neutral')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_mechanisms
    WHERE member_node_ids_array IS NULL OR array_length(member_node_ids_array, 1) IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_mechanisms WHERE mechanism_name IS NULL OR mechanism_name = ''
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_mechanisms WHERE fingerprint_hash IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_mechanisms WHERE verification_pass_status != 'single'
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_mechanisms
    WHERE ayanamsha_id NOT IN (
      'lahiri_chitrapaksha', 'raman', 'krishnamurti',
      'surya_siddhanta_classical', 'true_chitra'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_mechanisms
    WHERE edge_strength_min IS NOT NULL AND edge_strength_avg IS NOT NULL AND edge_strength_max IS NOT NULL
      AND (edge_strength_min > edge_strength_avg OR edge_strength_avg > edge_strength_max)
  )
  AND NOT EXISTS (
    SELECT mechanism_id FROM bodha_mechanisms GROUP BY mechanism_id HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, build_id, mechanism_class, fingerprint_hash
    FROM bodha_mechanisms
    GROUP BY 1, 2, 3, 4, 5 HAVING count(*) > 1
  )
$ic$
 WHERE asset_id = 'bo_yantra_mechanism';

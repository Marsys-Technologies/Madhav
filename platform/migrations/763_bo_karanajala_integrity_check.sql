-- 763_bo_karanajala_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_karanajala. Transaction ownership belongs to
-- platform/scripts/migrate.ts. Third migration of L2's 760-779 range
-- after #2021 (760), #2039 (761), #2041 (762).
--
-- bo_karanajala (writers/bo_karanajala.py, 1,757 lines) is L2's largest
-- and most structurally complex edge writer, with 8 distinct edge-
-- construction code paths feeding a single bodha_cgm_edges table. This
-- migration was scoped across two cycles rather than rushed: an initial
-- pass mis-attributed a negative-strength wrinkle to the wrong edge
-- subtype, which a full re-read of every "computed_strength" write site
-- (all 8) corrected before landing anything. Six invariants, each traced
-- to source and independently verified live against all three production
-- charts before landing (C12):
--
--   1. edge_type vocabulary: one of the 13 values derivable from source
--      across every construction path (_EDGE_TYPE_BASIS's 11 keys +
--      arudha_house/special_lagna_house from
--      _build_arudha_special_lagna_nodes_and_edges) — not narrowed to
--      the 8 observed live today (yoga_domain/dosha_domain/conjunction/
--      sade_sati are genuinely chart-data-dependent: they fire only when
--      a matching bodha_msr_signals row exists, absent on all 3 current
--      charts, not missing from the writer).
--   2. relationship_basis is an EXACT function of edge_type, matching
--      _EDGE_TYPE_BASIS's map precisely (e.g. 'dispositor'->
--      'sign_lordship', 'aspect'->'parashari_aspect') via
--      _typed_edge_fields(); arudha_house/special_lagna_house fall back
--      to relationship_basis = edge_type itself (no _EDGE_TYPE_BASIS
--      entry, so _typed_edge_fields' own fallback applies).
--   3. abs(computed_strength) is always in [0.1, 2.0] — EVERY one of the
--      8 write sites derives its strength via _edge_strength_v1(), whose
--      own _clamp_edge_strength() unconditionally bounds to (0.1, 2.0);
--      there is no other strength source anywhere in the writer.
--   4. computed_strength is negative if-and-only-if edge_type =
--      'dosha_domain' — the ONE deliberate sign convention in the writer
--      (line ~1171: "-_magnitude", explicitly NOT folded into the DR-7
--      clamp per its own comment, "which would otherwise clamp a
--      negative value up to +0.1 and silently flip an antagonist edge
--      positive"). Every other write site stores the unsigned
--      _edge_strength_v1() result directly.
--   5. from_node_id and to_node_id are never NULL — every construction
--      path only appends a row after resolving both endpoint node ids.
--   6. cancelled_flag = true only ever co-occurs with relationship_class
--      = 'argala_virodha' — cancellation logic
--      (_build_argala_edges/ARGALA_TO_VIRODHA) is gated on
--      `is_malefic`, which is exactly the condition that sets
--      relationship_class = 'argala_virodha'; no other code path ever
--      sets cancelled_flag True.
--
-- Deliberately NOT checked: DB-enforced distinctness (a real UNIQUE
-- constraint already exists on (chart_id, ayanamsha_id, build_id,
-- snapshot_type, edge_type, from_node_id, to_node_id), so this can never
-- be violated — asserting it here would be a no-op, not a gate).
-- verification_pass_status vocabulary: three write sites hardcode a
-- fixed literal, but the yoga_domain/dosha_domain/aspect/conjunction
-- sites copy the value through from the originating bodha_msr_signals
-- row (`ver_pass`), so there is no single fixed-literal invariant to
-- assert without re-deriving the full verification_vocab.py vocabulary
-- — left for a future pass rather than approximate.
--
-- Verified live against all three production charts before landing (C12):
-- all six conjuncts below evaluate TRUE today, table-wide (not scoped to
-- a single chart — none of these invariants are chart-specific).

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT 1 FROM bodha_cgm_edges WHERE edge_type NOT IN (
      'yoga_domain', 'dosha_domain', 'aspect', 'conjunction', 'dispositor',
      'argala', 'sade_sati', 'lordship', 'occupancy', 'bhava_aspect',
      'yoga_member', 'arudha_house', 'special_lagna_house'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_edges
    WHERE relationship_basis <> (CASE edge_type
      WHEN 'yoga_domain' THEN 'yoga_activation'
      WHEN 'dosha_domain' THEN 'dosha_impairment'
      WHEN 'aspect' THEN 'parashari_aspect'
      WHEN 'conjunction' THEN 'planetary_conjunction'
      WHEN 'dispositor' THEN 'sign_lordship'
      WHEN 'argala' THEN 'argala_intervention'
      WHEN 'sade_sati' THEN 'sade_sati_transit'
      WHEN 'lordship' THEN 'bhava_lordship'
      WHEN 'occupancy' THEN 'graha_bhava_occupancy'
      WHEN 'bhava_aspect' THEN 'parashari_bhava_aspect'
      WHEN 'yoga_member' THEN 'configuration_membership'
      WHEN 'arudha_house' THEN 'arudha_house'
      WHEN 'special_lagna_house' THEN 'special_lagna_house'
      ELSE relationship_basis
    END)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_edges WHERE abs(computed_strength) < 0.1 OR abs(computed_strength) > 2.0
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_edges WHERE (computed_strength < 0) <> (edge_type = 'dosha_domain')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_edges WHERE from_node_id IS NULL OR to_node_id IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_edges WHERE cancelled_flag = true AND relationship_class <> 'argala_virodha'
  )
$ic$
 WHERE asset_id = 'bo_karanajala';

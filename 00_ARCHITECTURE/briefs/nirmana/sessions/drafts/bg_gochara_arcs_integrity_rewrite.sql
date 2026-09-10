-- DRAFT (not yet a migration) — bg_gochara_arcs integrity_check_sql rewrite
-- D-VR-DATA-CORRECTNESS / C12 / D-CND-01. Verdict D-L0-F: the bare per-body count
-- pins are stale (33,933 vs 34,553; the entire delta is Rahu −310 + Ketu −310,
-- the mean-node arcs, and every body TILES PERFECTLY). Not corruption — an
-- underived volume pin. This rewrite KEEPS every real invariant, STRENGTHENS
-- the tiling to a gapless-contiguous assertion, and REPLACES the bare equality
-- with a §N.4 floor (the exact per-body arc count is an ephemeris-derived
-- quantity, not first-principles-derivable without re-running the ephemeris).
--
-- Rewrite floor test (C12): a corrupted set with the right TOTAL count but a gap
-- or duplicate in one body's arc_index PASSES the old `count(*) = 34553` and
-- FAILS this one (the per-body contiguity NOT EXISTS). Strictly stronger, never
-- weaker. Bundle into the D-CND-09 migration (registry change before re-acceptance).
--
-- Floor value <ACHIEVED> is set to the live count AFTER the corrected rebuild
-- (§N.4 achieved-count discipline), not guessed now.

SELECT
  -- structural invariants (kept verbatim; all real, none a bare volume pin)
      (SELECT count(DISTINCT substrate_version) = 1 FROM bg_gochara_arcs)
  AND (SELECT min(substrate_version) = 'arcs_v01' FROM bg_gochara_arcs)
  AND (SELECT count(DISTINCT body) = 9 FROM bg_gochara_arcs)
  AND (SELECT count(DISTINCT (body, arc_fingerprint)) = 9 FROM bg_gochara_arcs)   -- one fingerprint per body
  AND (SELECT count(*) FILTER (WHERE engine_version <> 'w2g_arcs_v01'
                                  OR ayanamsha_id <> 'tropical') = 0 FROM bg_gochara_arcs)
  -- STRENGTHENED tiling: per body, arc_index is a gapless contiguous 0..n-1 with
  -- no duplicates. Catches a missing/duplicated/mis-ordered arc the count pin cannot.
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT body,
             count(*)                    AS n,
             min(arc_index)              AS lo,
             max(arc_index)              AS hi,
             count(DISTINCT arc_index)   AS distinct_idx
      FROM bg_gochara_arcs GROUP BY body
    ) per_body
    WHERE lo <> 0 OR hi <> n - 1 OR distinct_idx <> n   -- gap / dup / offset
  )
  -- volume as a §N.4 FLOOR (not a bare equality): guards gross truncation while
  -- tolerating the legitimate ephemeris-derived node-arc count that the stale
  -- pin got wrong. expected_volume_formula stays NULL by design here — the floor
  -- + total tiling is the volume assertion, not a count equality (D-CND-01).
  AND (SELECT count(*) >= <ACHIEVED> FROM bg_gochara_arcs)
;

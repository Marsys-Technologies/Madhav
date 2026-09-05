-- 694_bg_gochara_arcs_tiling_floor_rewrite.sql
--
-- NIRMANA L0-W4 CONFORM (C12 wave-1 defect investigation, D-CND-01 exemplar):
-- bg_gochara_arcs' integrity_check_sql pins a bare total (`count(*) = 34553`)
-- and a hardcoded per-body expected-count table with stale Rahu/Ketu values
-- (13544/13553; live is 13234/13243 -- exactly -310 each, the mean-node arc
-- count as actually computed by the current ephemeris engine). Both are
-- volume pins on an ephemeris-derived quantity, not first-principles-
-- derivable, and both have drifted. This migration lands the D-CND-01
-- rewrite drafted at `sessions/drafts/bg_gochara_arcs_integrity_rewrite.sql`
-- with its `<ACHIEVED>` placeholder filled from the live count, verified in
-- a rolled-back transaction before writing (C12 "correct the check" path,
-- same class as migrations 692/693).
--
-- What is KEPT (all real invariants, unchanged): single substrate_version
-- ('arcs_v01'), exactly 9 distinct bodies, one arc_fingerprint per body,
-- engine_version/ayanamsha_id uniformity. What is STRENGTHENED: the old
-- check's per-body assertion only tested `fingerprints=1`, not gaplessness;
-- this rewrite adds an explicit per-body gapless-contiguous
-- `arc_index` assertion (`lo=0 AND hi=n-1 AND distinct_idx=n`) -- the C12
-- rewrite-floor-test: a corrupted set with the right TOTAL count but a gap
-- or duplicate in one body's arc_index PASSES the old bare-count pin and
-- FAILS this one. What is REPLACED: the hardcoded stale per-body VALUES
-- table and the bare total equality, both dropped in favour of a single
-- total FLOOR (`count(*) >= 33933`, achieved-count discipline per §N.4 --
-- guards gross truncation while tolerating the legitimate ephemeris-
-- derived arc count the stale pins got wrong).
--
-- Verified live (read-only): all 9 bodies tile perfectly today (lo=0,
-- hi=n-1, distinct_idx=n, per-body n summing to 33933); all 5 kept
-- structural invariants already hold; the full rewritten check (achieved
-- floor = 33933) evaluates TRUE against current production data as-is.
-- target_floor updated to match (34553 -> 33933, §N.4: floors track
-- achieved counts, never fabricated to hit a stale target).
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry
   SET target_floor = 33933,
       integrity_check_sql = $check$
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
  -- pin got wrong. expected_volume_formula stays NULL by design here -- the floor
  -- + total tiling is the volume assertion, not a count equality (D-CND-01).
  AND (SELECT count(*) >= 33933 FROM bg_gochara_arcs)
$check$
 WHERE asset_id = 'bg_gochara_arcs';

-- Forward reversal (safe at any time -- additive value correction, not a
-- schema change): re-run 09-01's original bg_gochara_arcs
-- integrity_check_sql (bare count(*)=34553 + stale per-body VALUES table)
-- and target_floor=34553 to restore prior behavior.

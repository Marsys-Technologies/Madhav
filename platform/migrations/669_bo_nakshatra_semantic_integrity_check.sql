-- 669_bo_nakshatra_semantic_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_nakshatra_semantic -- the sixth and last of
-- L2's 660-669 migration range. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Eight real invariants, all independently verified live on all three
-- production charts before landing (C12: never a check that has yet to
-- be green):
--
--   1. Tiling: EXACTLY 9 rows per (chart_id, ayanamsha_id) -- one per
--      GRAHAS entry (the same 9-candidate list bo_sudarshana's and
--      bo_vargottama_dhana's checks already bound against).
--   2. pada range guard: configuration_jsonb->>'pada' is in [1, 4] --
--      every nakshatra has exactly four padas.
--   3. nakshatra vocabulary: one of the 27 classical names
--      (NAKSHATRA_ORDER, nakshatra_semantic_emitter.py:59-66).
--   4. house_d1 range guard: in [1, 12].
--   5. tara_position range guard: in [1, 9] when present (the 9 tara
--      categories, cyclical from natal Moon's nakshatra).
--   6. tara_favorable is a TRUTHFUL function of tara_position, not just a
--      legal boolean: the writer's own predicate is `tara_position NOT IN
--      (1,3,5,7)` -- Janma/Vipat/Pratyak/Naidhana are inauspicious
--      (nakshatra_semantic_emitter.py:195-196). Re-derived here and
--      compared against the stored value.
--   7. gandanta_flag / gandanta_zone cross-column consistency: flag=true
--      requires a zone string starting 'gandanta_'; flag=false requires
--      either the literal 'not_applicable' or an 'end_pada_'/'start_pada_'
--      prefixed zone (nakshatra_semantic_emitter.py:94-105) -- catches a
--      flag that disagrees with its own zone label.
--   8. dispositor_chain_length matches the actual length of the
--      dispositor_chain array it claims to describe -- a direct re-
--      derivation, not a separately-trusted count.
--
-- Verified live against all three production charts before landing: all
-- eight conjuncts evaluate TRUE today.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  (
    NOT EXISTS (
      SELECT chart_id, ayanamsha_id
      FROM bodha_msr_signals
      WHERE signal_type_class = 'nakshatra_semantic'
      GROUP BY chart_id, ayanamsha_id
      HAVING count(*) != 9
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND (configuration_jsonb->>'pada')::int NOT BETWEEN 1 AND 4
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND configuration_jsonb->>'nakshatra' NOT IN (
        'Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra',
        'Punarvasu','Pushya','Ashlesha','Magha','Purva Phalguni',
        'Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha',
        'Jyeshtha','Mula','Purva Ashadha','Uttara Ashadha','Shravana',
        'Dhanishta','Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati'
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND (configuration_jsonb->>'house_d1')::int NOT BETWEEN 1 AND 12
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND configuration_jsonb->>'tara_position' IS NOT NULL
      AND (configuration_jsonb->>'tara_position')::int NOT BETWEEN 1 AND 9
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND configuration_jsonb->>'tara_position' IS NOT NULL
      AND (configuration_jsonb->>'tara_favorable')::boolean
          != ((configuration_jsonb->>'tara_position')::int NOT IN (1,3,5,7))
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND (
        ((configuration_jsonb->>'gandanta_flag')::boolean = true
          AND configuration_jsonb->>'gandanta_zone' NOT LIKE 'gandanta_%')
        OR ((configuration_jsonb->>'gandanta_flag')::boolean = false
          AND configuration_jsonb->>'gandanta_zone' NOT IN ('not_applicable')
          AND configuration_jsonb->>'gandanta_zone' NOT LIKE 'end_pada_%'
          AND configuration_jsonb->>'gandanta_zone' NOT LIKE 'start_pada_%')
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND (configuration_jsonb->>'dispositor_chain_length')::int
          != jsonb_array_length(configuration_jsonb->'dispositor_chain')
  )
$ic$
 WHERE asset_id = 'bo_nakshatra_semantic';

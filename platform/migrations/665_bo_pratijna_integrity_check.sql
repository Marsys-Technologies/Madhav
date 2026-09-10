-- 665_bo_pratijna_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; §N.4 M-14 layer-wide gap: 0 of 22 L2 assets
-- had an integrity_check_sql before this wave started). Adds a real
-- integrity_check_sql for bo_pratijna. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Why this is a genuine tiling invariant, not a bare count(*) = N
-- --------------------------------------------------------------------------
-- bodha_pratijna is one adjudicated row per (chart_id, ayanamsha_id,
-- event_class_id): 5 canonical ayanamshas x 27 KARYATVA_REGISTRY event
-- classes. Verified live before writing this check (all three production
-- charts, not assumed from one): every chart carries EXACTLY 135 rows,
-- and 135 = 135 distinct (ayanamsha_id, event_class_id) tuples -- i.e. no
-- chart has a duplicate or a gap. That is a tiling invariant (C12's named
-- class: "tiling with no gaps/overlaps"), not an unexplained magic number:
-- a rebuild that silently drops or duplicates one event class for one
-- ayanamsha would move the total away from 135 without this check ever
-- having to assert "135" as a bare literal -- the check derives the
-- expected tiling from the two enumerated sets themselves.
--
-- Two further real invariants, both independently verified live and both
-- named cross-column consistency / NULL-range guards in C12's own list:
--   1. grade IS NULL if and only if status = 'no_evidence' -- under the v4
--      engine a no_evidence row is a defensive "no karyatva registry entry"
--      case and is never scored; every other status IS scored. A row that
--      violates either direction (a scored status with no grade, or
--      no_evidence carrying a grade) is a real defect, not noise.
--   2. grade, when present, is bounded to the documented 0-10 scoring
--      range (measured live: 0.000-9.100 today, comfortably inside a
--      0-10 bound that leaves room for a legitimate future extreme without
--      being so loose it catches nothing).
--   3. status is one of the four documented values (promised / denied /
--      conditional / no_evidence) -- catches a typo'd or unversioned
--      status string a schema-less JSONB-adjacent column could otherwise
--      let through silently.
--
-- Deliberately NOT checked here: varga_confirmation's internal shape. That
-- column legitimately carries two different shapes today (the current
-- writer's consensus object and an older single-ayanamsha reading on
-- charts bo_pratijna hasn't rebuilt since -- see query_pratijna.ts's
-- consensus_chip, PR #1862) and asserting one shape here would make this
-- check RED on data that is honestly stale, not corrupt (C12: a check that
-- has never been green is a proposal, not a gate).
--
-- Verified live against all three production charts before landing (C12):
-- all five conjuncts evaluate TRUE today.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  (
    NOT EXISTS (
      SELECT 1
      FROM (SELECT DISTINCT chart_id FROM bodha_pratijna) c
      CROSS JOIN unnest(ARRAY[
        'krishnamurti','lahiri_chitrapaksha','raman',
        'surya_siddhanta_classical','true_chitra'
      ]) AS aya(ayanamsha_id)
      CROSS JOIN unnest(ARRAY[
        'achievement_recognition','bereavement','birth_anchor','business_launch',
        'career_advancement','career_change','career_entry','career_setback',
        'childbirth','chronic_onset','education_milestone','exam_outcome',
        'financial_deception','foreign_settlement','illness_acute','major_gain',
        'major_loss','marriage','parental_event','property_acquisition',
        'psychological_arc','relocation','romantic_start','separation',
        'spiritual_turn','surgery','travel_event'
      ]) AS ec(event_class_id)
      LEFT JOIN bodha_pratijna p
        ON p.chart_id = c.chart_id AND p.ayanamsha_id = aya.ayanamsha_id
       AND p.event_class_id = ec.event_class_id
      WHERE p.pratijna_id IS NULL
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_pratijna
    GROUP BY chart_id, ayanamsha_id, event_class_id
    HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_pratijna
    WHERE (status = 'no_evidence' AND grade IS NOT NULL)
       OR (status != 'no_evidence' AND grade IS NULL)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_pratijna
    WHERE grade IS NOT NULL AND (grade < 0 OR grade > 10)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_pratijna
    WHERE status NOT IN ('promised', 'denied', 'conditional', 'no_evidence')
  )
$ic$
 WHERE asset_id = 'bo_pratijna';

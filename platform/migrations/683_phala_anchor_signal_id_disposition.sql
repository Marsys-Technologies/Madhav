-- 683_phala_anchor_signal_id_disposition.sql
--
-- NIRMĀṆA v2.1 · L4 Phala · C13 / D-NATIVE-05 action 7: the no-FK disposition owed for
-- `phala_anchors.signal_id` (188 populated rows).
--
-- C13: "No-FK referrers get dispositions, not cascades: either a real FK with an intended
-- delete rule, or documented orphan-tolerance WITH A DETECTOR. Silent orphaning is worse than
-- loud cascade."
--
-- THE DISPOSITION: DOCUMENTED ORPHAN-TOLERANCE, WITH THE DETECTOR THIS MIGRATION SHIPS.
-- ------------------------------------------------------------------------------------
-- `signal_id` points at the `bodha_msr_signals` GENERATION an anchor was derived from.
-- `bo_laksana` mints it with `uuid.uuid4()` per build (#1748) and replaces its rows per chart,
-- so an L2 MSR rebuild leaves these pointers dangling. Measured live at the time of writing:
-- 188 populated, 21 distinct signals, **0 dangling** -- and that zero is a fact about build
-- ORDER (nobody has rebuilt L2 since these anchors were written), not a property of the design.
--
-- Orphan-tolerance is the right disposition, and NOT merely the convenient one:
--
--   * A stale pointer is the HONEST record of what the anchor was derived from. Re-aiming it at
--     the new generation's "equivalent" signal would assert a derivation that never happened.
--   * NULLing it on L2's delete (a FK with ON DELETE SET NULL) is more honest than dangling --
--     but it would make an L2 rebuild WRITE to phala_anchors, adding L4 to L2's blast radius
--     and creating a new cross-layer mutation surface. Under C13 that is not a change one layer
--     makes unilaterally. It is filed as an adjudication with this migration's evidence.
--   * What is NOT acceptable is the status quo before this migration: orphaning that nothing
--     could observe. C13's actual requirement is the detector, and that is what ships here.
--
-- WHAT GATES AND WHAT MERELY SURFACES
-- -----------------------------------
-- Orphaning is TOLERATED, so it must NOT gate the freeze -- installing a check that can go red
-- on an expected, accepted state would be a knowingly-red gate.
--
-- What DOES gate is the thing that must never be true: an anchor citing a signal belonging to a
-- DIFFERENT CHART. That is real cross-chart contamination (the JL-017 class), it is checkable
-- now, it is chart-partitioned per D-CND-03, and it holds today (verified: 0 rows).
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

-- ---------------------------------------------------------------------------
-- 1. The detector: makes orphaning OBSERVABLE rather than silent
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION phala_anchor_signal_provenance(p_chart_id uuid DEFAULT NULL)
RETURNS TABLE (
  chart_id            uuid,
  anchors_total       bigint,
  signal_cited        bigint,
  signal_resolvable   bigint,
  signal_orphaned     bigint,
  signal_absent       bigint
) LANGUAGE sql STABLE AS
$$
  SELECT
    a.chart_id,
    count(*)                                                   AS anchors_total,
    count(*) FILTER (WHERE a.signal_id IS NOT NULL)             AS signal_cited,
    count(*) FILTER (WHERE a.signal_id IS NOT NULL AND EXISTS (
      SELECT 1 FROM bodha_msr_signals s WHERE s.signal_id::text = a.signal_id::text))
                                                               AS signal_resolvable,
    count(*) FILTER (WHERE a.signal_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM bodha_msr_signals s WHERE s.signal_id::text = a.signal_id::text))
                                                               AS signal_orphaned,
    count(*) FILTER (WHERE a.signal_id IS NULL)                 AS signal_absent
  FROM phala_anchors a
  WHERE p_chart_id IS NULL OR a.chart_id = p_chart_id
  GROUP BY a.chart_id
$$;

COMMENT ON FUNCTION phala_anchor_signal_provenance(uuid) IS
  'C13 / D-NATIVE-05 action 7 -- the DETECTOR behind phala_anchors.signal_id''s documented '
  'orphan-tolerance disposition. signal_id has no FK by design: it records the '
  'bodha_msr_signals GENERATION an anchor was derived from, and bo_laksana mints signal_id '
  'with uuid4 per build (#1748), so an L2 MSR rebuild legitimately strands these pointers. A '
  'stale pointer is the honest record of a real derivation; re-aiming it would assert a '
  'derivation that never happened. Orphaning is therefore TOLERATED -- but never silent: this '
  'function reports signal_orphaned per chart so the count is an observable. signal_absent '
  'counts discovery-sourced anchors, which never had a signal (ph_nimitta selects NULL for '
  'them) and are not orphans.';

-- ---------------------------------------------------------------------------
-- 2. The gate: cross-chart contamination must never happen
-- ---------------------------------------------------------------------------
-- Appended to ph_nimitta's existing detector (migration 680) rather than replacing it, and
-- chart-partitioned per D-CND-03 so a violation names the chart it belongs to.
UPDATE asset_registry
   SET integrity_check_sql = integrity_check_sql || $add$
  -- C13 / #1748: an anchor may cite a signal that no longer exists (orphan-tolerant by
  -- disposition -- see phala_anchor_signal_provenance()), but it must NEVER cite a signal
  -- belonging to a DIFFERENT CHART. That is cross-chart contamination (the JL-017 class),
  -- not staleness, and nothing else detects it.
  AND NOT EXISTS (
    SELECT 1 FROM phala_anchors a
      JOIN bodha_msr_signals s ON s.signal_id::text = a.signal_id::text
     WHERE a.signal_id IS NOT NULL AND s.chart_id <> a.chart_id
     GROUP BY a.chart_id HAVING count(*) > 0)
$add$
 WHERE asset_id = 'ph_nimitta';

-- ---------------------------------------------------------------------------
-- 3. Record the disposition where a reader will find it
-- ---------------------------------------------------------------------------
UPDATE asset_registry
   SET volume_explanation = volume_explanation ||
       ' SIGNAL_ID DISPOSITION (C13): phala_anchors.signal_id has NO foreign key, by design. It '
       'records the bodha_msr_signals generation an anchor was derived from, and bo_laksana '
       'mints signal_id with uuid4 per build (#1748), so an L2 MSR rebuild legitimately strands '
       'these pointers. Orphaning is TOLERATED -- a stale pointer is the honest record of a real '
       'derivation, and re-aiming it would assert one that never happened -- but it is never '
       'silent: phala_anchor_signal_provenance() reports the orphan count per chart. Adding a FK '
       'with ON DELETE SET NULL would be more honest still, but it would make an L2 rebuild write '
       'to phala_anchors and so enlarge L2''s blast radius; under C13 that is an adjudication, '
       'not a unilateral change.'
 WHERE asset_id = 'ph_nimitta';

-- ---------------------------------------------------------------------------
-- 4. Prove the gate works AND can fail (C12 rewrite floor test)
-- ---------------------------------------------------------------------------
DO $$
DECLARE sql text; ok boolean; v_anchor uuid; v_foreign uuid;
BEGIN
  SELECT integrity_check_sql INTO sql FROM asset_registry WHERE asset_id = 'ph_nimitta';
  EXECUTE sql INTO ok;
  IF ok IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 683: ph_nimitta detector is RED on current data -- refusing to install';
  END IF;

  -- The detector must go red on real cross-chart contamination. Inject one, confirm, roll back.
  SELECT a.anchor_id INTO v_anchor
    FROM phala_anchors a WHERE a.signal_id IS NOT NULL LIMIT 1;
  SELECT s.signal_id INTO v_foreign
    FROM bodha_msr_signals s
   WHERE s.chart_id <> (SELECT chart_id FROM phala_anchors WHERE anchor_id = v_anchor)
   LIMIT 1;

  IF v_anchor IS NULL OR v_foreign IS NULL THEN
    RAISE EXCEPTION 'migration 683 cannot run its rewrite-floor test: no cross-chart signal available';
  END IF;

  BEGIN
    UPDATE phala_anchors SET signal_id = v_foreign WHERE anchor_id = v_anchor;
    EXECUTE sql INTO ok;
    IF ok IS NOT FALSE THEN
      RAISE EXCEPTION
        'migration 683 FAILED the rewrite floor test: the detector stayed green on an anchor '
        'citing another chart''s signal';
    END IF;
    RAISE EXCEPTION 'rollback_probe';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'rollback_probe' THEN RAISE; END IF;
  END;

  -- And it must NOT go red on mere orphaning, which is the tolerated state.
  BEGIN
    UPDATE phala_anchors SET signal_id = '00000000-0000-0000-0000-0000000000fe'
     WHERE anchor_id = v_anchor;
    EXECUTE sql INTO ok;
    IF ok IS NOT TRUE THEN
      RAISE EXCEPTION
        'migration 683: the detector went red on a merely ORPHANED signal_id, which is the '
        'documented tolerated state -- that would be a knowingly-red gate';
    END IF;
    RAISE EXCEPTION 'rollback_probe';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'rollback_probe' THEN RAISE; END IF;
  END;
END $$;

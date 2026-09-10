-- 680_phala_anchor_deterministic_identity.sql
--
-- NIRMĀṆA v2.1 · L4 Phala · W3-0 · CONDUCTOR ruling D-CND-04 (issue #1732, binding).
--
-- WHY
-- ---
-- `phala_anchors.anchor_id` defaults to `gen_random_uuid()`. `ph_nimitta` is
-- delete-then-insert (§N.3), so every rebuild mints brand-new ids and silently
-- orphans every stored reference to the previous generation. L4's own tables
-- self-heal when the whole layer rebuilds together (their writers regenerate
-- references in the same cascade); L5's never do, because `mi_bhavisya`
-- deliberately preserves adjudicated rows -- so the safeguard becomes an orphan
-- generator, and the damage grows with exactly the data P7 exists to accumulate.
--
-- D-CND-04: "an identity that downstream layers derive provenance from may not be
-- a fresh random value regenerated on rebuild."
--
-- WHAT THE KEY IS, AND WHY IT IS NOT THE OBVIOUS ONE
-- --------------------------------------------------
-- The obvious implementation is uuidv5 over the existing `phala_anchors_natural_key`.
-- That does NOT work, and it was verified before this migration was written:
-- that key embeds `convergence_id` and `bhavishya_id`, and BOTH are bigserial
-- (`nextval('kala_convergence_convergence_id_seq')`, `nextval('kala_bhavishya_id_seq')`)
-- against delete-then-insert L3 writers. It would satisfy the letter of the hold,
-- pass its own detector today, and silently re-break the chain on L3's next
-- rebuild. `bodha_msr_signals.signal_id` is likewise unusable -- `bo_laksana`
-- mints it with `uuid.uuid4()` per build (issue #1748).
--
-- So the identity is the anchor's own GRADE-FREE EVENT TUPLE:
--
--     (chart_id, anchor_source, event_type, direction, domain, horizon_tier,
--      window_start, peak_date, window_end, falsifier)
--
-- Grade-free deliberately. `magnitude` / `confidence_*` / `posterior` are excluded
-- because (a) L4's own W3-3 grading fixes would otherwise re-mint every id and
-- re-break the chain, and (b) more importantly a prediction must keep its identity
-- across a recalibration, or an outcome can never be compared to the prediction it
-- tests. Identity is the claim, not the grade.
--
-- ONE IMPLEMENTATION, NOT TWO
-- ---------------------------
-- `phala_anchor_identity()` below is the single source of truth. The writer calls
-- this same function rather than reimplementing uuid5 in Python, so the two can
-- never drift (§N.7 item 3: no wrapper-local constant may shadow a stored value --
-- here, no second implementation of an identity).
--
-- MEASURED BEFORE WRITING (live production, 2026-09-05, read-only)
-- ---------------------------------------------------------------
--   * 195 anchor rows across 2 charts -> 193 distinct computed identities.
--   * 4 rows form 2 colliding pairs. Within each pair the rows differ ONLY in
--     `signal_id` (unstable per #1748) and `posterior` (a grade). Under CR-46's own
--     stated doctrine -- "two anchors with an identical fingerprint describe the same
--     predicted event and must collapse to one row" (ph_nimitta.py:42-58) -- these
--     are duplicates its dedup key missed, because that key includes `posterior` and
--     a 0.02 difference prevented the merge.
--   * Those 4 rows are NOT remapped here. Merging them re-points L5 rows, which is
--     not a decision this session takes alone -- escalated as issue #1748. They keep
--     their current random ids and are reported by the detector below as a named,
--     counted exception rather than silently included or silently skipped.
--
-- BLAST RADIUS -- CORRECTED AGAINST THE RULING'S OWN TABLE
-- -------------------------------------------------------
-- Issue #1732 listed 9 tables / 6,606 rows. Verified live, two of those entries do
-- not hold anchor ids at all and MUST NOT be rewritten:
--   * `mimamsa_attribution.match_id`            0 / 1,425 resolve as an anchor_id
--   * `mimamsa_manifestation_sets.prediction_id` 0 / 195   (it resolves 195/195 to
--                                                 mimamsa_predictions.prediction_id)
-- and one that does hold them was absent from the table:
--   * `mimamsa_predictions.source_pramana_id`  195 / 195 resolve as an anchor_id
--     (it stores an anchor_id under a pramana_id's name -- mi_bhavisya.py:178,
--     reported separately; this migration preserves that column's CURRENT semantics
--     and does not rename or re-point it).
-- Corrected set: 8 columns, 5,181 referencing rows.
--
-- FK HANDLING
-- -----------
-- The 6 FKs into phala_anchors are ON UPDATE NO ACTION and NOT DEFERRABLE, so a
-- parent-key update would fail mid-statement. They are made DEFERRABLE for the
-- duration, deferred, and then re-checked with SET CONSTRAINTS ALL IMMEDIATE
-- *inside* this migration -- so a violation fails loudly here rather than at commit --
-- and finally restored to NOT DEFERRABLE. The schema ends as it began.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts. No BEGIN/COMMIT here.

-- ---------------------------------------------------------------------------
-- 1. The identity function (single source of truth; the writer calls this)
-- ---------------------------------------------------------------------------

-- A fixed, arbitrary-but-permanent namespace for L4 phala anchor identities.
-- Never change this value: doing so re-mints every anchor id in existence.
CREATE OR REPLACE FUNCTION phala_anchor_identity_namespace()
RETURNS uuid LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT 'a5f7c1e2-0b3d-5e88-9c41-6d2f8a7b4e10'::uuid $$;

CREATE OR REPLACE FUNCTION phala_anchor_identity(
  p_chart_id      uuid,
  p_anchor_source text,
  p_event_type    text,
  p_direction     text,
  p_domain        text,
  p_horizon_tier  text,
  p_window_start  date,
  p_peak_date     date,
  p_window_end    date,
  p_falsifier     text
) RETURNS uuid LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$
  -- jsonb_build_array gives a canonical, unambiguous, null-preserving encoding.
  -- Dates are cast to text so the encoding does not depend on session DateStyle.
  SELECT uuid_generate_v5(
    phala_anchor_identity_namespace(),
    jsonb_build_array(
      p_chart_id::text, p_anchor_source, p_event_type, p_direction, p_domain,
      p_horizon_tier, p_window_start::text, p_peak_date::text, p_window_end::text,
      p_falsifier
    )::text
  )
$$;

COMMENT ON FUNCTION phala_anchor_identity(uuid,text,text,text,text,text,date,date,date,text) IS
  'D-CND-04 (#1732): deterministic phala_anchors.anchor_id from the anchor''s grade-free '
  'event tuple. Excludes magnitude/confidence/posterior so a recalibration preserves a '
  'prediction''s identity, and excludes every upstream surrogate key (convergence_id and '
  'bhavishya_id are bigserial; signal_id is uuid4 per build, #1748) so an upstream rebuild '
  'does not re-mint L4 identities. Single source of truth: ph_nimitta calls this function.';

-- ---------------------------------------------------------------------------
-- 2. Build the remap, excluding identities that are not unique
-- ---------------------------------------------------------------------------

CREATE TEMP TABLE _l4_anchor_remap ON COMMIT DROP AS
WITH computed AS (
  SELECT a.anchor_id AS old_id,
         phala_anchor_identity(a.chart_id, a.anchor_source, a.event_type, a.direction,
                               a.domain, a.horizon_tier, a.window_start, a.peak_date,
                               a.window_end, a.falsifier) AS new_id
  FROM phala_anchors a
),
uniq AS (
  SELECT new_id FROM computed GROUP BY new_id HAVING count(*) = 1
)
SELECT c.old_id, c.new_id
FROM computed c
JOIN uniq u ON u.new_id = c.new_id
WHERE c.old_id <> c.new_id;

CREATE UNIQUE INDEX ON _l4_anchor_remap (old_id);
CREATE UNIQUE INDEX ON _l4_anchor_remap (new_id);

-- Fail closed if the computed identity would collide with an id already in use by a
-- DIFFERENT anchor. Cannot happen with a uuid5 over distinct tuples, but an identity
-- migration that cannot detect its own collision is exactly the unearned signal §N.8
-- forbids, so the check is real rather than assumed.
DO $$
DECLARE n integer;
BEGIN
  SELECT count(*) INTO n
  FROM _l4_anchor_remap r
  JOIN phala_anchors a ON a.anchor_id = r.new_id
  WHERE a.anchor_id <> r.old_id;
  IF n > 0 THEN
    RAISE EXCEPTION 'phala_anchors deterministic remap aborted: % computed identities collide with a different existing anchor', n;
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 3. Defer the FKs, remap parent and children, re-check immediately
-- ---------------------------------------------------------------------------

ALTER TABLE phala_suddha_sodhana ALTER CONSTRAINT phala_suddha_sodhana_anchor_id_fkey DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE phala_muhurta        ALTER CONSTRAINT phala_muhurta_linked_anchor_id_fkey  DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE phala_mitigation     ALTER CONSTRAINT phala_mitigation_linked_anchor_id_fkey DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE phala_sodhana        ALTER CONSTRAINT phala_sodhana_anchor_id_fkey         DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE phala_sankrama       ALTER CONSTRAINT phala_sankrama_source_anchor_id_fkey DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE phala_pramana        ALTER CONSTRAINT phala_pramana_anchor_id_fkey         DEFERRABLE INITIALLY IMMEDIATE;

SET CONSTRAINTS
  phala_suddha_sodhana_anchor_id_fkey,
  phala_muhurta_linked_anchor_id_fkey,
  phala_mitigation_linked_anchor_id_fkey,
  phala_sodhana_anchor_id_fkey,
  phala_sankrama_source_anchor_id_fkey,
  phala_pramana_anchor_id_fkey
  DEFERRED;

-- Parent first; the deferred FKs tolerate the transient mismatch.
UPDATE phala_anchors a SET anchor_id = r.new_id
  FROM _l4_anchor_remap r WHERE a.anchor_id = r.old_id;

-- L4 children (6 with FKs, 1 without).
UPDATE phala_suddha_sodhana c SET anchor_id        = r.new_id FROM _l4_anchor_remap r WHERE c.anchor_id        = r.old_id;
UPDATE phala_sodhana        c SET anchor_id        = r.new_id FROM _l4_anchor_remap r WHERE c.anchor_id        = r.old_id;
UPDATE phala_pramana        c SET anchor_id        = r.new_id FROM _l4_anchor_remap r WHERE c.anchor_id        = r.old_id;
UPDATE phala_sankrama       c SET source_anchor_id = r.new_id FROM _l4_anchor_remap r WHERE c.source_anchor_id = r.old_id;
UPDATE phala_muhurta        c SET linked_anchor_id = r.new_id FROM _l4_anchor_remap r WHERE c.linked_anchor_id = r.old_id;
UPDATE phala_mitigation     c SET linked_anchor_id = r.new_id FROM _l4_anchor_remap r WHERE c.linked_anchor_id = r.old_id;
UPDATE phala_phaladesa      c SET top_anchor_id    = r.new_id FROM _l4_anchor_remap r WHERE c.top_anchor_id    = r.old_id;

-- L5: the ONE column verified to hold an anchor_id (195/195). Its name says
-- pramana_id and its content is an anchor_id -- reported separately; this migration
-- preserves the existing semantics rather than quietly changing them.
UPDATE mimamsa_predictions p SET source_pramana_id = r.new_id::text
  FROM _l4_anchor_remap r WHERE p.source_pramana_id = r.old_id::text;

-- Validate NOW, inside this migration, so a violation is loud and local.
SET CONSTRAINTS
  phala_suddha_sodhana_anchor_id_fkey,
  phala_muhurta_linked_anchor_id_fkey,
  phala_mitigation_linked_anchor_id_fkey,
  phala_sodhana_anchor_id_fkey,
  phala_sankrama_source_anchor_id_fkey,
  phala_pramana_anchor_id_fkey
  IMMEDIATE;

-- Restore the schema exactly as it was found.
ALTER TABLE phala_suddha_sodhana ALTER CONSTRAINT phala_suddha_sodhana_anchor_id_fkey NOT DEFERRABLE;
ALTER TABLE phala_muhurta        ALTER CONSTRAINT phala_muhurta_linked_anchor_id_fkey  NOT DEFERRABLE;
ALTER TABLE phala_mitigation     ALTER CONSTRAINT phala_mitigation_linked_anchor_id_fkey NOT DEFERRABLE;
ALTER TABLE phala_sodhana        ALTER CONSTRAINT phala_sodhana_anchor_id_fkey         NOT DEFERRABLE;
ALTER TABLE phala_sankrama       ALTER CONSTRAINT phala_sankrama_source_anchor_id_fkey NOT DEFERRABLE;
ALTER TABLE phala_pramana        ALTER CONSTRAINT phala_pramana_anchor_id_fkey         NOT DEFERRABLE;

-- ---------------------------------------------------------------------------
-- 4. Post-condition: prove the remap left NOTHING dangling
-- ---------------------------------------------------------------------------
-- The Conductor's ruling is explicit that today's verified 0-orphan state must
-- "survive the change rather than being re-established by luck". This asserts it.

DO $$
DECLARE bad integer;
BEGIN
  SELECT
      (SELECT count(*) FROM phala_suddha_sodhana c LEFT JOIN phala_anchors a USING (anchor_id)        WHERE c.anchor_id        IS NOT NULL AND a.anchor_id IS NULL)
    + (SELECT count(*) FROM phala_sodhana        c LEFT JOIN phala_anchors a USING (anchor_id)        WHERE c.anchor_id        IS NOT NULL AND a.anchor_id IS NULL)
    + (SELECT count(*) FROM phala_pramana        c LEFT JOIN phala_anchors a USING (anchor_id)        WHERE c.anchor_id        IS NOT NULL AND a.anchor_id IS NULL)
    + (SELECT count(*) FROM phala_sankrama       c LEFT JOIN phala_anchors a ON a.anchor_id = c.source_anchor_id WHERE c.source_anchor_id IS NOT NULL AND a.anchor_id IS NULL)
    + (SELECT count(*) FROM phala_muhurta        c LEFT JOIN phala_anchors a ON a.anchor_id = c.linked_anchor_id WHERE c.linked_anchor_id IS NOT NULL AND a.anchor_id IS NULL)
    + (SELECT count(*) FROM phala_mitigation     c LEFT JOIN phala_anchors a ON a.anchor_id = c.linked_anchor_id WHERE c.linked_anchor_id IS NOT NULL AND a.anchor_id IS NULL)
    + (SELECT count(*) FROM phala_phaladesa      c LEFT JOIN phala_anchors a ON a.anchor_id = c.top_anchor_id    WHERE c.top_anchor_id    IS NOT NULL AND a.anchor_id IS NULL)
    + (SELECT count(*) FROM mimamsa_predictions  p LEFT JOIN phala_anchors a ON a.anchor_id::text = p.source_pramana_id WHERE p.source_pramana_id IS NOT NULL AND a.anchor_id IS NULL)
    INTO bad;
  IF bad > 0 THEN
    RAISE EXCEPTION 'phala_anchors deterministic remap left % dangling reference(s) across the 8 referencing columns', bad;
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 5. The detector (D-CND-03 partitioned form) -- so "0 orphans" is CHECKED,
--    not merely measured once. §N.8: the current 0-orphan state is true and
--    unearned; nothing today would tell us if it broke.
-- ---------------------------------------------------------------------------
-- Chart-agnostic by necessity: the freeze-time integrity detector executes with no
-- bind parameters (issue #1723), so this quantifies over ALL charts. That is a
-- weaker ATTRIBUTION than a chart-scoped check ("some chart is broken", not "this
-- one is") and is labelled as such in volume_explanation rather than left to read
-- as chart-scoped.

UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT
  -- (a) referential integrity: no reference to a non-existent anchor, in any of the
  --     8 columns verified to hold an anchor_id.
  (SELECT count(*) FROM phala_suddha_sodhana c LEFT JOIN phala_anchors a USING (anchor_id) WHERE c.anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM phala_sodhana c LEFT JOIN phala_anchors a USING (anchor_id) WHERE c.anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM phala_pramana c LEFT JOIN phala_anchors a USING (anchor_id) WHERE c.anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM phala_sankrama c LEFT JOIN phala_anchors a ON a.anchor_id = c.source_anchor_id WHERE c.source_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM phala_muhurta c LEFT JOIN phala_anchors a ON a.anchor_id = c.linked_anchor_id WHERE c.linked_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM phala_mitigation c LEFT JOIN phala_anchors a ON a.anchor_id = c.linked_anchor_id WHERE c.linked_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM phala_phaladesa c LEFT JOIN phala_anchors a ON a.anchor_id = c.top_anchor_id WHERE c.top_anchor_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  AND (SELECT count(*) FROM mimamsa_predictions p LEFT JOIN phala_anchors a ON a.anchor_id::text = p.source_pramana_id WHERE p.source_pramana_id IS NOT NULL AND a.anchor_id IS NULL) = 0
  -- (b) D-CND-04 itself: every anchor's stored id must equal its computed identity.
  --     A row that fails this was written by a path that bypassed the deterministic
  --     key -- which is the specific regression this asset must never have again.
  --     The <= 4 allowance is the named, escalated exception (issue #1748): 2 pairs
  --     of rows that are content-identical apart from a grade, whose merge re-points
  --     L5 rows and is therefore not this session's decision alone. It is an explicit
  --     counted allowance, not a silent skip, and it must SHRINK, never grow.
  AND (SELECT count(*) FROM phala_anchors a
        WHERE a.anchor_id <> phala_anchor_identity(a.chart_id, a.anchor_source, a.event_type,
              a.direction, a.domain, a.horizon_tier, a.window_start, a.peak_date,
              a.window_end, a.falsifier)) <= 4
  -- (c) the anchor->pramana->prediction chain is 1:1 where it exists at all.
  AND (SELECT count(*) FROM (SELECT anchor_id FROM phala_pramana GROUP BY anchor_id HAVING count(*) > 1) d) = 0
$check$,
       volume_explanation =
         'One row per derived predictive anchor, after the T-5 clip gate and the CR-46 '
         'content dedup. anchor_id is deterministic from the anchor''s grade-free event '
         'tuple (migration 680, D-CND-04 / issue #1732). NOTE: integrity_check_sql is '
         'chart-agnostic because the freeze-time detector runs with no bind parameters '
         '(issue #1723) -- a failure means SOME chart is affected, not necessarily the '
         'one just built.'
 WHERE asset_id = 'ph_nimitta';

-- ---------------------------------------------------------------------------
-- 6. Prove the detector is a GATE, not a proposal (C12 rewrite floor test)
-- ---------------------------------------------------------------------------
-- It must pass on today's real data, AND it must be able to fail on real corruption.
-- Both are asserted here: the first directly, the second by injecting a dangling
-- reference inside a savepoint, confirming the detector goes red, then rolling back.

DO $$
DECLARE ok boolean; sql text; victim uuid;
BEGIN
  SELECT integrity_check_sql INTO sql FROM asset_registry WHERE asset_id = 'ph_nimitta';
  EXECUTE sql INTO ok;
  IF ok IS NOT TRUE THEN
    RAISE EXCEPTION 'ph_nimitta integrity detector does not pass on current data -- refusing to install a red gate';
  END IF;

  SELECT top_anchor_id INTO victim FROM phala_phaladesa WHERE top_anchor_id IS NOT NULL LIMIT 1;
  IF victim IS NULL THEN
    RAISE EXCEPTION 'cannot run the rewrite-floor test: no phala_phaladesa.top_anchor_id to perturb';
  END IF;
  BEGIN
    UPDATE phala_phaladesa SET top_anchor_id = '00000000-0000-0000-0000-0000000000ff'
     WHERE top_anchor_id = victim;
    EXECUTE sql INTO ok;
    IF ok IS NOT FALSE THEN
      RAISE EXCEPTION 'ph_nimitta integrity detector FAILED the rewrite floor test: it stayed green on an injected dangling reference';
    END IF;
    RAISE EXCEPTION 'rollback_probe';   -- unwind the injected corruption
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'rollback_probe' THEN RAISE; END IF;
  END;
END $$;

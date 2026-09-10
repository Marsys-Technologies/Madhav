-- 682_phala_anchor_identity_trigger.sql
--
-- NIRMĀṆA v2.1 · L4 Phala · completes D-CND-04 (issue #1732). Lifts the campaign-wide hold
-- on ph_nimitta / phala_anchors rebuilds once deployed and announced under CAPABILITIES LANDED.
--
-- WHAT MIGRATION 680 LEFT OPEN
-- ----------------------------
-- 680 made the identity deterministic and remapped the existing rows: verified live, 191 of
-- 195 anchors now equal their computed identity (the 4 exceptions are the two escalated
-- content-identical pairs, issue #1748), and all 3,513 child references across
-- phala_sankrama / phala_pramana / phala_suddha_sodhana / phala_sodhana were carried with
-- zero dangling.
--
-- But `phala_anchors.anchor_id` still DEFAULTS to gen_random_uuid(). So the guarantee lived
-- in exactly one writer: any INSERT that omits the column -- from the legacy sidecar estate,
-- a repair script, a future writer, a hand-run statement -- still minted a random id and
-- silently reintroduced the orphan hazard D-CND-04 exists to prevent. A guarantee that one
-- caller upholds is not a property of the data; it is a property of that caller.
--
-- WHY A TRIGGER AND NOT A BETTER DEFAULT
-- -------------------------------------
-- A column DEFAULT expression cannot reference other columns of the row being inserted, so a
-- deterministic default is not expressible in Postgres. A BEFORE INSERT trigger can, and it
-- moves the invariant from "the writer remembers" to "the table enforces" -- which is the
-- whole of D-CND-04.
--
-- INSERT ONLY, DELIBERATELY. The trigger does not fire on UPDATE. Under §N.3 L4+ rebuilds are
-- delete-then-insert, so INSERT is the only path that mints an identity. Recomputing on UPDATE
-- would let an ordinary column edit silently CHANGE an anchor's identity and orphan every
-- reference to it -- converting a safe operation into the exact failure this migration
-- prevents. An UPDATE that genuinely changes the event tuple is a different anchor and must go
-- through delete-then-insert.
--
-- The trigger OVERWRITES rather than filling only when NULL. `anchor_id` is NOT NULL with a
-- default, so a caller omitting it never presents NULL to the trigger -- it presents a freshly
-- minted random uuid, indistinguishable from a deliberate one. Fill-if-null would therefore
-- never fire on precisely the case it exists to catch. Overwriting also means a caller cannot
-- assert an identity that contradicts the row's own content.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts. No BEGIN/COMMIT here.

-- ---------------------------------------------------------------------------
-- 1. Fail closed if 680's groundwork is not present
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF to_regprocedure('phala_anchor_identity(uuid,text,text,text,text,text,date,date,date,text)') IS NULL THEN
    RAISE EXCEPTION 'migration 682 requires phala_anchor_identity() from migration 680';
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 2. The trigger: identity is computed by the TABLE, for every writer
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION phala_anchors_set_identity()
RETURNS trigger LANGUAGE plpgsql AS
$$
BEGIN
  NEW.anchor_id := phala_anchor_identity(
    NEW.chart_id, NEW.anchor_source, NEW.event_type, NEW.direction, NEW.domain,
    NEW.horizon_tier, NEW.window_start, NEW.peak_date, NEW.window_end, NEW.falsifier
  );
  RETURN NEW;
END
$$;

COMMENT ON FUNCTION phala_anchors_set_identity() IS
  'D-CND-04 (#1732): derives phala_anchors.anchor_id from the row''s own grade-free event '
  'tuple on INSERT, so the deterministic identity holds for EVERY writer rather than only for '
  'ph_nimitta. INSERT only -- recomputing on UPDATE would let an ordinary column edit change '
  'an anchor''s identity and orphan every reference to it.';

DROP TRIGGER IF EXISTS phala_anchors_identity_biu ON phala_anchors;
CREATE TRIGGER phala_anchors_identity_biu
  BEFORE INSERT ON phala_anchors
  FOR EACH ROW EXECUTE FUNCTION phala_anchors_set_identity();

-- ---------------------------------------------------------------------------
-- 3. Retire the random default -- it is now unreachable, and leaving it is a lie
-- ---------------------------------------------------------------------------
-- Kept as NOT NULL: the trigger always supplies a value, so no insert can present NULL.
ALTER TABLE phala_anchors ALTER COLUMN anchor_id DROP DEFAULT;

-- ---------------------------------------------------------------------------
-- 4. Prove it -- both that it works and that it can fail (C12 rewrite floor test)
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  v_chart uuid;
  v_expected uuid;
  v_got uuid;
  v_before bigint;
  v_after bigint;
BEGIN
  SELECT chart_id INTO v_chart FROM phala_anchors LIMIT 1;
  IF v_chart IS NULL THEN
    RAISE EXCEPTION 'migration 682 cannot self-verify: phala_anchors is empty';
  END IF;

  v_expected := phala_anchor_identity(
    v_chart, 'convergence', 'migration_682_probe', 'mixed', 'career', 'near',
    DATE '2099-01-01', DATE '2099-02-01', DATE '2099-03-01', 'MIGRATION-682-PROBE');

  SELECT count(*) INTO v_before FROM phala_anchors;

  BEGIN
    -- Insert WITHOUT anchor_id, exactly as a careless writer would. Before this migration
    -- that produced a random uuid; it must now produce the derived identity.
    INSERT INTO phala_anchors (
      chart_id, anchor_source, event_type, direction, domain, horizon_tier,
      window_start, peak_date, window_end, magnitude, magnitude_basis,
      confidence_low, confidence_high, confidence_basis, malleability,
      falsifier, derivation_ledger_jsonb, source_citation
    ) VALUES (
      v_chart, 'convergence', 'migration_682_probe', 'mixed', 'career', 'near',
      DATE '2099-01-01', DATE '2099-02-01', DATE '2099-03-01', 'minor', 'probe',
      0.1, 0.2, 'structural_not_yet_empirical', 'influenceable',
      'MIGRATION-682-PROBE', '{}'::jsonb, 'migration_682/probe'
    );

    SELECT anchor_id INTO v_got FROM phala_anchors
     WHERE falsifier = 'MIGRATION-682-PROBE';

    IF v_got IS DISTINCT FROM v_expected THEN
      RAISE EXCEPTION
        'migration 682 FAILED: an anchor_id-omitting insert produced % but the derived identity is %',
        v_got, v_expected;
    END IF;

    -- And the identity must be STABLE: the same event tuple inserted again collapses onto
    -- the same row rather than minting a second id. This is the property the whole hold is
    -- about, so it is proven rather than assumed.
    INSERT INTO phala_anchors (
      chart_id, anchor_source, event_type, direction, domain, horizon_tier,
      window_start, peak_date, window_end, magnitude, magnitude_basis,
      confidence_low, confidence_high, confidence_basis, malleability,
      falsifier, derivation_ledger_jsonb, source_citation
    ) VALUES (
      v_chart, 'convergence', 'migration_682_probe', 'mixed', 'career', 'near',
      DATE '2099-01-01', DATE '2099-02-01', DATE '2099-03-01',
      'pivotal', 'probe-different-grade',          -- different GRADE on purpose...
      0.7, 0.79, 'structural_not_yet_empirical', 'influenceable',
      'MIGRATION-682-PROBE', '{}'::jsonb, 'migration_682/probe-2'
    ) ON CONFLICT (anchor_id) DO NOTHING;         -- ...must collapse, not duplicate

    SELECT count(*) INTO v_after FROM phala_anchors;
    IF v_after <> v_before + 1 THEN
      RAISE EXCEPTION
        'migration 682 FAILED: the same event tuple minted a second identity (% -> %)',
        v_before, v_after;
    END IF;

    RAISE EXCEPTION 'rollback_probe';   -- unwind both probe rows
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'rollback_probe' THEN RAISE; END IF;
  END;
END $$;

-- Post-condition: the random default is gone and the trigger is installed.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_name = 'phala_anchors' AND column_name = 'anchor_id'
                AND column_default IS NOT NULL) THEN
    RAISE EXCEPTION 'migration 682 FAILED: phala_anchors.anchor_id still carries a column default';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger
                  WHERE tgname = 'phala_anchors_identity_biu' AND NOT tgisinternal) THEN
    RAISE EXCEPTION 'migration 682 FAILED: the identity trigger is not installed';
  END IF;
END $$;

-- 1266_l0_registry_parihara_floor_and_rider_has_writer.sql
--
-- Suvarna Track I, item TI-L0-07 (finding CF-03, SS ruling Q6 of 2026-10-01; number 1266 allocated by SS):
-- the L0 registry-correction batch, three asset_registry rows, two columns, nothing else.
--
--   1. bg_parihara_rules   target_floor 449 -> 440
--   2. bg_nakshatra_medical has_writer false -> true
--   3. bg_transit_engine    has_writer false -> true
--
-- CONCERN
--   (1) The parihara floor is stale. Migration 644 set it to 449 over 61 + 329 + 59 rows; migration 703 (applied
--   2026-09-06) deleted 9 orphaned rows and re-pinned the integrity check but left the floor. Live, read as the
--   reader role on 2026-10-03: bg_parihara_rules 60 + bg_muhurta_activity_rules 329 + bg_muhurta_factor_census 51
--   = 440, which is exactly the sum count_sql returns and exactly what asset_throughput recorded for the last build
--   (rows_written = 440). CLAUDE.md N.4: a floor equals the achieved count after a build, never an estimate.
--   (2) Two riders are registered in code but flagged as having no writer. The census reads Build.registered FAIL
--   ("@register in <file> but registry says has_writer=false") for both:
--     bg_nakshatra_medical : @register at pipeline/orchestrator/writers/bg_medical_mappings.py:26 (the class that
--                            also registers bg_medical_mappings and bg_sign_medical)
--     bg_transit_engine    : second @register on BgTransitRulesWriter, pipeline/orchestrator/writers/
--                            bg_transit_rules.py:12 (the class that also registers bg_transit_rules)
--   bg_sign_medical, the third rider of the medical writer, is ALREADY has_writer = true and is left alone.
--
-- DECISION RECORD
--   SS Q6 (2026-10-01): a sibling's dispatch counts (producer_covered) when the registry declares the rider
--   relation, and "the R61 cascade may stand until the first L0 dispatch". The has_writer flip here is the half
--   of Q6 that fixes Build.registered. The rider relation itself is migration 1267 (TI-L0-08), NOT this file.
--
-- EXPECTED CASCADE (recorded, not a regression): Nikasa R61. With has_writer = true the census reads
-- Build.exercised FAIL ("registered with a writer and never dispatched") for bg_nakshatra_medical and
-- bg_transit_engine until the id is dispatched in a build run (or, once 1267 is read by the inspector, until its
-- producer is). Clearing it needs a production L0 dispatch: a REVIEW item for SS, not done here.
-- Also: has_writer = true makes the two ids selectable by the plan resolver (WHERE is_active AND has_writer) in
-- a layer-scope L0 plan; they would then be planned as their own steps although their writer is a sibling's
-- class. That is the reason this file is held until SS has the rider relation (1267) decided.
--
-- SERVING EFFECT AT APPLY
--   * Fires trigger nirmana_registry_receipt_invalidation (AFTER UPDATE OF ... target_floor, has_writer ... WHEN
--     the row changed): it sets asset_freshness to 'stale' (reason 'registry_changed') for the NEW.asset_id row.
--       - bg_parihara_rules  has an asset_freshness row (fresh, 2026-09-06): it goes STALE. It has NO declared
--         dependents (no asset lists it in depends_on), so no dispatch gate reads it; only the cockpit and the
--         freshness census show stale until the asset is next rebuilt or re-receipted.
--       - bg_nakshatra_medical, bg_transit_engine have NO asset_freshness row, so the trigger updates nothing.
--   * No consumer reads target_floor or has_writer at serve time; no served surface changes. No data is touched.
--   * Assets that go stale: bg_parihara_rules ONLY.
--
-- GUARDS (values read through the reader role, 2026-10-03; every one raises rather than skip on drift)
--   bg_parihara_rules   : target_table = 'bg_parihara_rules', md5(count_sql) = 6d886abbfa16a5c5d6b6688dd8d01b17
--                         and target_floor = 449 (then updated) or already 440 (then skipped). Any other floor,
--                         or a changed count_sql (the floor is the achieved count OF that count_sql), raises.
--   bg_nakshatra_medical: target_table = 'bg_nakshatra_medical', asset_kind = 'data',
--                         md5(count_sql) = c81dda22bcfe765b0e4d0750db3780c5; has_writer false (updated) or true (skipped).
--   bg_transit_engine   : target_table = 'bg_transit_engine', asset_kind = 'data',
--                         md5(count_sql) = 40a0fe926e122a3fb8fe2e628dc33614; has_writer false (updated) or true (skipped).
--   A row that does not exist (a fresh bootstrap that has not seeded it yet) is skipped with a NOTICE, the
--   convention of 1210; production has all three (verified). After the updates the file re-reads all three rows
--   and raises unless each is at its target (never trust a silent no-op).
--
-- PRIVILEGE (P2 rule, W1_PRIVILEGE_AUDIT): runs as the routine runner role amjis_app, which OWNS asset_registry
-- and asset_freshness and the trigger function; it needs only UPDATE on asset_registry and nothing in schema
-- public beyond USAGE. No CREATE, no GRANT, no DDL. Proven as amjis_app (NOSUPERUSER, NOINHERIT, production ACL).
--
-- IDEMPOTENT: a second run finds every row at its target and updates nothing, so the trigger does not fire again.
--
-- NOT DONE HERE
--   * The seed literals in platform/scripts/seed/asset_registry_seed.ts (floor 449, has_writer) - that file is
--     owned by PR #2984. The seed's ON CONFLICT clause keeps target_floor and has_writer migration-governed for an
--     existing row, so a re-seed does not revert this file; the literals only matter for a fresh bootstrap.
--   * The rider relation (1267), the Build.exercised cascade (needs a dispatch), the other floors that sit below
--     the live count (bg_muhurta_lattice, bg_sky_calendar, bg_ontology: cosmetic, Count.floor still PASS).
--   * Any change to the integrity check, count_sql or the data of any of the three assets.
--
-- ROLLBACK (ops reference, not executed): UPDATE asset_registry SET target_floor = 449 WHERE asset_id =
-- 'bg_parihara_rules'; UPDATE asset_registry SET has_writer = false WHERE asset_id IN ('bg_nakshatra_medical',
-- 'bg_transit_engine'); each is a new reviewed migration against the then-current state.
--
-- VERIFY AFTER APPLY by production structure, not the deploy log (Trap 103):
--   SELECT asset_id, target_floor, has_writer FROM asset_registry
--    WHERE asset_id IN ('bg_parihara_rules','bg_nakshatra_medical','bg_transit_engine');
--   -- expect: bg_nakshatra_medical 27/t, bg_parihara_rules 440/t, bg_transit_engine 9/t ; and
--   SELECT freshness_state, reasons FROM asset_freshness WHERE asset_id = 'bg_parihara_rules';  -- stale, ["registry_changed"]
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).

SET LOCAL lock_timeout = '5s';

DO $m1266$
DECLARE
    v_floor    integer;
    v_md5      text;
    v_target   text;
    v_kind     text;
    v_writer   boolean;
    v_rows     bigint;
    rider      text;
    rider_md5  constant jsonb := '{"bg_nakshatra_medical":"c81dda22bcfe765b0e4d0750db3780c5","bg_transit_engine":"40a0fe926e122a3fb8fe2e628dc33614"}';
BEGIN
    -- 1. bg_parihara_rules target_floor 449 -> 440
    SELECT target_floor, md5(count_sql), target_table
      INTO v_floor, v_md5, v_target
      FROM asset_registry WHERE asset_id = 'bg_parihara_rules' FOR UPDATE;
    IF NOT FOUND THEN
        RAISE NOTICE '1266: bg_parihara_rules is not in asset_registry; skipped';
    ELSIF v_floor = 440 THEN
        RAISE NOTICE '1266: bg_parihara_rules target_floor is already 440; skipped';
    ELSIF v_floor = 449
          AND v_target = 'bg_parihara_rules'
          AND v_md5 = '6d886abbfa16a5c5d6b6688dd8d01b17' THEN
        UPDATE asset_registry SET target_floor = 440
         WHERE asset_id = 'bg_parihara_rules' AND target_floor = 449;
        GET DIAGNOSTICS v_rows = ROW_COUNT;
        IF v_rows <> 1 THEN
            RAISE EXCEPTION '1266: bg_parihara_rules floor update touched % rows, expected 1', v_rows;
        END IF;
    ELSE
        RAISE EXCEPTION '1266: bg_parihara_rules has drifted from the audited state (target_floor=%, target_table=%, md5(count_sql)=%); refusing to change the floor',
            v_floor, v_target, v_md5;
    END IF;

    -- 2 and 3. has_writer false -> true for the two riders
    FOREACH rider IN ARRAY ARRAY['bg_nakshatra_medical', 'bg_transit_engine'] LOOP
        SELECT has_writer, md5(count_sql), target_table, asset_kind
          INTO v_writer, v_md5, v_target, v_kind
          FROM asset_registry WHERE asset_id = rider FOR UPDATE;
        IF NOT FOUND THEN
            RAISE NOTICE '1266: % is not in asset_registry; skipped', rider;
        ELSIF v_target IS DISTINCT FROM rider
              OR v_kind IS DISTINCT FROM 'data'
              OR v_md5 IS DISTINCT FROM (rider_md5 ->> rider) THEN
            RAISE EXCEPTION '1266: % has drifted from the audited state (target_table=%, asset_kind=%, md5(count_sql)=%); refusing to change has_writer',
                rider, v_target, v_kind, v_md5;
        ELSIF v_writer THEN
            RAISE NOTICE '1266: % has_writer is already true; skipped', rider;
        ELSE
            UPDATE asset_registry SET has_writer = true
             WHERE asset_id = rider AND has_writer = false;
            GET DIAGNOSTICS v_rows = ROW_COUNT;
            IF v_rows <> 1 THEN
                RAISE EXCEPTION '1266: % has_writer update touched % rows, expected 1', rider, v_rows;
            END IF;
        END IF;
    END LOOP;

    -- Post-check: re-read, never trust a silent no-op.
    IF EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'bg_parihara_rules' AND target_floor IS DISTINCT FROM 440) THEN
        RAISE EXCEPTION '1266: bg_parihara_rules target_floor is not 440 after the update';
    END IF;
    IF EXISTS (SELECT 1 FROM asset_registry
                WHERE asset_id IN ('bg_nakshatra_medical', 'bg_transit_engine') AND has_writer IS DISTINCT FROM true) THEN
        RAISE EXCEPTION '1266: a rider still has has_writer <> true after the update';
    END IF;
END
$m1266$;

-- DOWN (ops reference, not executed by migrate.ts): see ROLLBACK in the header.

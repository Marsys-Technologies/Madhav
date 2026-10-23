-- 1409_k9_floors_achieved_zero.sql
--
-- SR-K9-ADMITTED-ZERO (owner surrogate, 2026-10-23; supersedes the scope of SR-SANGAM-FLOOR-ZERO): set asset_registry.target_floor of ka_sangam (14868 -> 0) and
-- ka_vighnakara (536 -> 0) to the ACHIEVED count of the K9 candidate build, which is 0. Data-only: ONE column (target_floor) of exactly TWO asset_registry
-- rows, no DDL, no new object. Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Same pattern as migrations 1408, 1395, 1329.
--
-- PREPARED, MERGE ONLY IF THE TRIAGE READS "BY DESIGN" (SR-K9-ADMITTED-ZERO (iii)-first): the read-only triage of why 0 of 50,678 head-generation predicates are
-- admitted must conclude that the K4-2b `stage_to_reader_mapping_unadmitted` state is by design until admission goes live. If it finds a defect, this file is not merged.
--
-- WHY. Production readback (counts only): 0 admitted predicates; ka_sangam floor 14,868, ka_vighnakara floor 536; kala_convergence 0 rows. With nothing admitted,
-- a K9 rebuild can only produce 0 rows for these two writers. asset_runner.py:1098-1114 (FROZEN, untouched) records a 0-row chart-scoped completion as 'lit' ONLY when
-- asset_registry.target_floor = 0, else 'dormant', and the DEP-ASSERT dependency gate then blocks every dependent of a 'dormant' asset: the whole K9 plan stalls on two layers
-- that are structurally empty. root CLAUDE.md N.4: "Floors are aspirational, not gates: set target_floor to the achieved count; never fabricate rows to hit a number."
-- The achieved count is 0 (precedent: ga_prashna, target_floor 0, "the writer ran, evaluated, found nothing, by design").
--
-- COMPENSATION (N.8, outside the frozen path). Declaring floor 0 removes the orchestrator's own "0 rows = silent failure" signal for these two assets, so a detector that
-- can read false replaces it, in this same change set: services/kala_core/publication.py `_candidate` (the entry of `verify` and `publish`) REFUSES a ka_sangam or
-- ka_vighnakara zero-row grain unless the emptiness is explained by a named vacuous reason the gate re-measures from the candidate's own rows AND the asset's
-- integrity_check_sql passes. The writers label the run `vacuous=true reason=<named>` (notes + WARNING log). The K9 receipt must state that these two layers are structurally
-- empty pending admission.
--
-- GUARD (never a silent change, idempotent). Each row is read FOR UPDATE under the lock_timeout below.
--   * row absent                                   -> RAISE, nothing changed;
--   * target_floor = 14868 (ka_sangam) / 536 (ka_vighnakara) -> set 0 (the one transition per row this migration exists for);
--   * target_floor = 0                             -> already landed (a fresh registry seeded at 0, or a replay): NOTICE, nothing is written;
--   * NULL or any other value                      -> RAISE (ambiguous: somebody set it for a reason this migration cannot see), nothing changed.
-- After an UPDATE: ROW_COUNT must be exactly 1; the row re-read must show 0; the whole row minus target_floor must equal what was read before; and after BOTH rows
-- no OTHER asset_registry row version may have been written by this transaction (xmin check, the 1304/1395/1408 pattern).
--
-- TRIGGER EFFECT (stated, intended). target_floor IS in the column list of nirmana_registry_receipt_invalidation:
--     AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table
--     ON asset_registry FOR EACH ROW WHEN (old.* IS DISTINCT FROM new.*) EXECUTE FUNCTION nirmana_invalidate_registry_receipts()
-- (as recorded verbatim in migration 1333); the function body is `UPDATE asset_freshness SET freshness_state = 'stale', reasons += 'registry_changed',
-- observed_at = now() WHERE asset_id = NEW.asset_id`. It fires once per changed row, so on THIS migration: the asset_freshness rows of ka_sangam and ka_vighnakara (and only
-- those two assets) are marked stale with reason 'registry_changed'. That is INTENDED and correct: both assets are rebuilt by the K9-4b candidate build this change exists for, and
-- a freshness receipt taken at the old floor must not be trusted at the new one. The trigger does not walk dependents and does not touch asset_throughput (build state). If a
-- replay or an already-landed row is met, the migration returns before any UPDATE, so the trigger does not fire.
--
-- NOT PROTECTED. A plain UPDATE: no public-schema DDL, so it is in neither PROTECTED_PUBLIC_SCHEMA_MIGRATIONS nor PROTECTED_DATA_PLANE_MIGRATIONS.
-- NO FROZEN PATH. asset_runner.py and DEP-ASSERT semantics are unchanged; this migration only sets the registry value the frozen code already reads.
--
-- Seed: platform/scripts/seed/asset_registry_seed.ts declares target_floor: 0 for both assets, consistent with this migration (its ON CONFLICT preserves live values,
-- so the seed governs a fresh registry only).
--
-- Post-apply verification (read-only):
--   SELECT asset_id, target_floor, is_active, has_writer FROM asset_registry WHERE asset_id IN ('ka_sangam','ka_vighnakara') ORDER BY asset_id;
--     -- expect ka_sangam | 0 | t | t   and   ka_vighnakara | 0 | t | t
--   SELECT asset_id, freshness_state FROM asset_freshness WHERE asset_id IN ('ka_sangam','ka_vighnakara');   -- stale where a row exists (intended)
--
-- ROLLBACK (not executed by migrate.ts):
--   UPDATE asset_registry SET target_floor = 14868 WHERE asset_id = 'ka_sangam'      AND target_floor = 0;
--   UPDATE asset_registry SET target_floor = 536   WHERE asset_id = 'ka_vighnakara' AND target_floor = 0;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

DO $m1409$
DECLARE
  v_asset   text;
  v_expect  integer;
  v_before  jsonb;
  v_after   jsonb;
  v_cur     integer;
  v_changed integer;
  v_other   integer;
BEGIN
  FOR v_asset, v_expect IN VALUES ('ka_sangam', 14868), ('ka_vighnakara', 536) LOOP
    SELECT to_jsonb(r) INTO v_before
      FROM asset_registry r
     WHERE r.asset_id = v_asset
       FOR UPDATE;
    IF v_before IS NULL THEN
      RAISE EXCEPTION '1409: % has no asset_registry row; nothing was changed', v_asset;
    END IF;

    v_cur := (v_before ->> 'target_floor')::integer;
    IF v_cur = 0 THEN
      RAISE NOTICE '1409: % target_floor is already 0; nothing was changed', v_asset;
      CONTINUE;
    END IF;
    IF v_cur IS DISTINCT FROM v_expect THEN
      RAISE EXCEPTION '1409: refusing to change %: target_floor is % (expected exactly %, or 0 when already landed); nothing was changed', v_asset, coalesce(v_cur::text, 'NULL'), v_expect;
    END IF;

    UPDATE asset_registry
       SET target_floor = 0
     WHERE asset_id = v_asset
       AND target_floor = v_expect;

    GET DIAGNOSTICS v_changed = ROW_COUNT;
    IF v_changed <> 1 THEN
      RAISE EXCEPTION '1409: expected to update exactly one asset_registry row (%), updated %', v_asset, v_changed;
    END IF;

    SELECT to_jsonb(r) INTO v_after FROM asset_registry r WHERE r.asset_id = v_asset;
    IF (v_after ->> 'target_floor') IS DISTINCT FROM '0' THEN
      RAISE EXCEPTION '1409: % target_floor update did not take (expected 0, found %)', v_asset, coalesce(v_after ->> 'target_floor', 'NULL');
    END IF;
    IF (v_after - 'target_floor') IS DISTINCT FROM (v_before - 'target_floor') THEN
      RAISE EXCEPTION '1409: a column other than target_floor changed on %; the migration must touch ONLY that column', v_asset;
    END IF;
  END LOOP;

  SELECT count(*) INTO v_other
    FROM asset_registry
   WHERE xmin = pg_current_xact_id()::xid
     AND asset_id NOT IN ('ka_sangam', 'ka_vighnakara');
  IF v_other <> 0 THEN
    RAISE EXCEPTION '1409: % other asset_registry row version(s) were written by this transaction; the migration must touch ONLY ka_sangam and ka_vighnakara', v_other;
  END IF;
END
$m1409$;

-- Migration 1223: A2.6 tranche — re-scope ka_gochara count_sql '4.0' → '4.1'.
-- Pravāha stream C, TASK C1 (steward M20261001T212520-1e31, 2026-10-01).
-- Created: 2026-10-02. Author: pravaha stream C.
--
-- Numbering: 1223 is the lowest free number by the E-009-discipline scan at
-- authoring time (highest numeric prefix across every origin/* head and both
-- migration directories = 1222; 1204/1205/1206 are held by open PRs).
--
-- WHY THIS EXISTS
-- ═══════════════
-- Migration 1091 (WP10 step 5) repointed asset_registry.count_sql for
-- asset_id='ka_gochara' to
--   SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'
-- as a TRANSIENT between cutover steps 5 and 6 ("EXPECTED AND BENIGN … cockpit
-- shows 0"). The '4.0' label was subsequently built, flipped, and reversed as a
-- live hazard, and is BURNED for this chart (ADK-0027 §4 — "re-attempt under a
-- new label"); the standing successor is '4.1' (ADK-0028 sequence). A count_sql
-- pinned to '4.0' can therefore never go non-zero again — the transient became
-- permanent. Decision note:
-- 00_ARCHITECTURE/briefs/pravaha/decisions/KA_GOCHARA_COCKPIT_COUNT_NOTE_v1_0.md
-- (branch campaign/pravaha), recommendation Option 1: re-scope the generation
-- literal in count_sql at the '4.1' tranche.
--
-- SCOPE (exactly what the steward authorised, nothing more)
-- ══════════════════════════════════════════════════════════
-- Updates ONLY the count_sql column of ONLY the asset_id='ka_gochara' row,
-- changing the generation literal '4.0' → '4.1'. target_table stays as 1091 set
-- it (kala_gochara_windows); integrity_check_sql conjuncts are untouched —
-- conjunct (k)'s '4.%' pattern already covers '4.1' and conjunct (j) pins only
-- target_table = count_sql's relation, which this migration preserves (both
-- still kala_gochara_windows). Migration 1091 itself is NOT edited.
--
-- SAFETY
-- ══════
-- Idempotent: a second run finds the '4.1' text and is a no-op.
-- Fails closed: if the current count_sql is not exactly what 1091 wrote (and
-- not already the '4.1' target), the migration RAISEs and changes nothing —
-- the guard refuses to overwrite a state it does not recognise.
--
-- PR is titled HOLD (A2.6 tranche): merged by the steward's queue, not before.
--
-- No BEGIN/COMMIT here: the migration runner owns the transaction
-- (platform/scripts/migrate.ts ~L828-835: BEGIN; <SQL>; INSERT INTO
-- _migrations_applied; COMMIT) — an inner COMMIT would end it early and the
-- tracking row would be written outside it.

DO $$
DECLARE
  r RECORD;
  c_1091 CONSTANT text := 'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation=''4.0''';
  c_41   CONSTANT text := 'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation=''4.1''';
BEGIN
  SELECT count_sql INTO r FROM asset_registry WHERE asset_id = 'ka_gochara';
  IF NOT FOUND THEN
    RAISE EXCEPTION '1223: asset_registry row for ka_gochara not found — refusing to proceed';
  END IF;
  IF r.count_sql = c_41 THEN
    RAISE NOTICE '1223: ka_gochara count_sql already scoped to generation 4.1 — no-op';
    RETURN;
  END IF;
  IF r.count_sql IS DISTINCT FROM c_1091 THEN
    RAISE EXCEPTION '1223: unexpected ka_gochara count_sql — expected exactly the 1091 text, found: %', r.count_sql;
  END IF;
  UPDATE asset_registry SET count_sql = c_41 WHERE asset_id = 'ka_gochara';
END $$;

-- Post-gate: 1091's conjunct (j) condition still holds (target_table IS the
-- relation count_sql reads) and the literal actually moved to '4.1'.
DO $$
DECLARE
  r RECORD;
BEGIN
  SELECT target_table, count_sql INTO r FROM asset_registry WHERE asset_id = 'ka_gochara';
  IF r.target_table IS DISTINCT FROM substring(r.count_sql from 'FROM ([a-z0-9_]+)') THEN
    RAISE EXCEPTION '1223 gate failed: target_table != count_sql relation for ka_gochara';
  END IF;
  IF r.count_sql NOT LIKE '%generation=''4.1''%' THEN
    RAISE EXCEPTION '1223 gate failed: count_sql not re-scoped to generation 4.1';
  END IF;
END $$;

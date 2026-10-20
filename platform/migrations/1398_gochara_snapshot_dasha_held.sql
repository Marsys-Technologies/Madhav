-- Migration 1398: the search-input snapshot RECORDS which (lord, level) daśā pairs the pinned build HOLDS. ADDITIVE on top of 1305 (1305 is never edited).
-- Pravāha / KĀLA-YANTRA fix-1305-unrestricted (ruling SR-F1305-FIX-CONDITIONS; #3774). STATUS: protected window B (kala_schema_migration=true), with 1381.
--
-- WHY: 1305's daśā copy holds only the rows OVERLAPPING the manifest horizon (ka_gochara_search_dasha_live_population), so it cannot say whether the pinned
-- build holds a row for a (lord, level) whose rows all lie outside the horizon. The P1 record builder (record_store._p1_running_support) and the verifier
-- (inventory_verifier.RECORD_SUPPORT_HELD_COPY) read "no rows" off the copy and so INVENT the contact span as support, with `unknown`, for such a lord
-- (B.10, §N.5), where the live reader gives an empty running set and `false`. This records, at capture, which (lord, level) pairs the build holds.
--
-- consumed_dasha_held: jsonb array of {"lord": <lowercase>, "level_n": 1|2|3}, one per DISTINCT pair held by the build(s) of the snapshot's copy, under the
-- verifier's own pins (lahiri_chitrapaksha / vimshottari / two_pass_verified / levels 1-3). NULL = a snapshot captured before this record existed (the readers
-- then fall back to the copy alone, the pre-record behaviour, and say so: dasha_read.make_period_rows_for_snapshot `held_recorded`).
-- It is computed by the database from the consumed row ids (the builder submits nothing for it; a submitted value is overwritten), and it is keyed to the
-- copy's builds, which are immutable.
--
-- WHAT THIS ADDS: one nullable column; one invoker-rights STABLE function (ka_gochara_search_dasha_held); one trigger function and one BEFORE INSERT trigger,
-- named 0zz_ so it fires AFTER 1305's 0z_copy_build trigger and so reads the consumed_dasha_row_ids the copy-build already accepted. No existing function,
-- constraint or row is touched; no backfill (a legacy snapshot keeps NULL).
--
-- PRINCIPALS: production revokes PUBLIC EXECUTE on every function amjis_app creates (1220), so EXECUTE on the new function is granted (only if the role exists) to
-- data_plane_builder, the one role that inserts a snapshot and so fires the trigger as the invoker. The verifier and the sealer only READ the column (a table-level
-- privilege already inherited by a new column) and call no new function. The trigger function needs no grant: EXECUTE on a trigger function is checked when the
-- trigger is created, by its owner. No table grant changes.
--
-- WINDOW: protected public-schema window B: it is picked up AUTOMATICALLY by governance/kala_protected_migrations.py (a numbered migration above the guard's
-- pinned baseline with public-schema DDL), so it applies via deploy.yml `kala_schema_migration=true`, ascending after 1381, NOT via gochara_contracts (that
-- window is the explicit 1153-1308 list, and 1305 must already be applied by it: the gate below refuses otherwise). Transaction ownership: NO BEGIN/COMMIT —
-- migrate.ts owns one transaction per migration. ROLLBACK (unused installation only): drop the trigger, the trigger function and the function, drop the column,
-- delete the _migrations_applied row. After any generation has been built under 1398, correct forward instead.
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE ──────────────────────────────────────────────────────────────────────
DO $$
DECLARE failures text;
BEGIN
  WITH f(failure, detail) AS (
    SELECT 'snapshot_table_missing', 'ka_gochara_search_input_snapshot' WHERE to_regclass('public.ka_gochara_search_input_snapshot') IS NULL
    UNION ALL SELECT 'migration_1305_not_applied', 'the snapshot has no consumed_dasha_rows copy column: apply 1305 (gochara_contracts window) first'
    WHERE NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'
                        AND column_name = 'consumed_dasha_rows')
    UNION ALL SELECT 'copy_build_trigger_missing', 'ka_gochara_search_input_snapshot_0z_copy_build'
    WHERE to_regclass('public.ka_gochara_search_input_snapshot') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.ka_gochara_search_input_snapshot'::regclass
                        AND tgname = 'ka_gochara_search_input_snapshot_0z_copy_build' AND NOT tgisinternal)
    UNION ALL SELECT 'chart_dashas_missing', 'chart_dashas' WHERE to_regclass('public.chart_dashas') IS NULL
    UNION ALL SELECT 'migration_1398_already_applied', 'consumed_dasha_held'
    WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'
                    AND column_name = 'consumed_dasha_held')
  )
  SELECT string_agg(failure || ' (' || detail || ')', ', ') INTO failures FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1398 BLOCKED: %', failures;
  END IF;
END;
$$;

ALTER TABLE public.ka_gochara_search_input_snapshot ADD COLUMN IF NOT EXISTS consumed_dasha_held jsonb;

CREATE OR REPLACE FUNCTION public.ka_gochara_search_dasha_held(p_chart uuid, p_ids uuid[])
RETURNS jsonb LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT COALESCE(jsonb_agg(jsonb_build_object('lord', h.lord, 'level_n', h.level_n) ORDER BY h.lord COLLATE "C", h.level_n), '[]'::jsonb)
  FROM (SELECT DISTINCT lower(d.lord_graha) AS lord, d.level_n
        FROM public.chart_dashas d
        WHERE d.chart_id = p_chart AND d.ayanamsha_id = 'lahiri_chitrapaksha' AND d.system_id = 'vimshottari'
          AND d.verification_pass_status = 'two_pass_verified' AND d.level_n IN (1, 2, 3)
          AND d.build_id IN (SELECT x.build_id FROM public.chart_dashas x WHERE x.chart_id = p_chart AND x.dasha_row_id = ANY (p_ids))) h;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_search_input_snapshot_held_build()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  NEW.consumed_dasha_held := CASE WHEN NEW.consumed_dasha_row_ids IS NULL THEN NULL
                                  ELSE public.ka_gochara_search_dasha_held(NEW.chart_id, NEW.consumed_dasha_row_ids) END;       -- overwrites whatever was submitted
  RETURN NEW;
END;
$$;
CREATE TRIGGER ka_gochara_search_input_snapshot_0zz_held_build
  BEFORE INSERT ON public.ka_gochara_search_input_snapshot
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_search_input_snapshot_held_build();

-- ── grants (only to a role that exists; production revokes PUBLIC EXECUTE on functions amjis_app creates, 1220) ──────────────────
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    GRANT EXECUTE ON FUNCTION public.ka_gochara_search_dasha_held(uuid, uuid[]) TO data_plane_builder;
  END IF;
END;
$$;

-- ── Presence checks ────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'
                   AND column_name = 'consumed_dasha_held' AND data_type = 'jsonb' AND is_nullable = 'YES') THEN
    RAISE EXCEPTION 'migration 1398 post-apply check failed: consumed_dasha_held (nullable jsonb) is missing';
  END IF;
  IF to_regprocedure('public.ka_gochara_search_dasha_held(uuid,uuid[])') IS NULL THEN
    RAISE EXCEPTION 'migration 1398 post-apply check failed: ka_gochara_search_dasha_held is missing';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.ka_gochara_search_input_snapshot'::regclass
                   AND tgname = 'ka_gochara_search_input_snapshot_0zz_held_build' AND NOT tgisinternal) THEN
    RAISE EXCEPTION 'migration 1398 post-apply check failed: the held-record trigger is missing';
  END IF;
  RAISE NOTICE 'migration 1398: presence checks passed';
END;
$$;

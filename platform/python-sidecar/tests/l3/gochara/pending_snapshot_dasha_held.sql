-- PENDING MIGRATION (not numbered: no migration number is allocated to fix-1305-unrestricted; the cockpit allocates one, then this file moves to
-- platform/migrations/<NNNN>_gochara_snapshot_records_held_dasha_lords.sql unchanged). Until then the tests apply it to their disposable fixture as a stand-in.
--
-- WHY: 1305's daśā copy holds only the rows OVERLAPPING the manifest horizon (ka_gochara_search_dasha_live_population), so it cannot say whether the pinned
-- build holds a row for a (lord, level) whose rows all lie outside the horizon. The P1 record builder (record_store._p1_running_support) and the verifier
-- (inventory_verifier.RECORD_SUPPORT_HELD_COPY) read "no rows" off the copy and so INVENT the contact span as support, with `unknown`, for such a lord
-- (B.10, §N.5), where the live reader gives an empty running set and `false`. This records, at capture, which (lord, level) pairs the build holds.
--
-- consumed_dasha_held: jsonb array of {"lord": <lowercase>, "level_n": 1|2|3}, one per DISTINCT pair held by the build(s) of the snapshot's copy, under the
-- verifier's own pins (lahiri_chitrapaksha / vimshottari / two_pass_verified / levels 1-3). NULL = a snapshot captured before this record existed.
-- It is computed by the database from the consumed row ids (the builder submits nothing for it), and it is keyed to the copy's builds, which are immutable.
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

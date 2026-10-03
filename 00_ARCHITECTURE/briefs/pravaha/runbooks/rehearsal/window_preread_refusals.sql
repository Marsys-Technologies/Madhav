-- READ-ONLY pre-reads of the window files' OWN forward refusal conditions (round-21 F-R21-5): run in checklist row 2 and again right before row 8, so a refusal cannot
-- surprise the dispatch. Each line states the expected value. A DIFFERENT value = STOP (the named file would refuse at apply).
-- 1233 (migration gate :43-59): refuses if 1155's table is missing, if its two anchor columns already exist, or if ANY P1 relationship record exists.
SELECT to_regclass('public.ka_gochara_relationship_record') IS NOT NULL AS t1155_table_present;                                          -- expect t
SELECT count(*) AS anchor_columns_present FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_relationship_record' AND column_name IN ('period_anchor_lord', 'period_anchor_level');   -- expect 0
SELECT count(*) AS p1_records FROM public.ka_gochara_relationship_record WHERE path_id = 'P1';                                          -- expect 0 (1233 refuses over existing P1 rows)
-- 1204 (preflight gate :69-110): refuses unless the table, the CHECK kgrr_object_role_ck and ka_gochara_object_selector_ok(jsonb) exist, 1155 is RECORDED and 1204 is NOT.
-- (1204 has NO forward 'av_qualifier' refusal: that refusal belongs to its ROLLBACK note — it widens the vocabulary; the count below is informational.)
SELECT (SELECT count(*) FROM pg_constraint c WHERE c.conrelid = 'public.ka_gochara_relationship_record'::regclass AND c.conname = 'kgrr_object_role_ck') AS kgrr_object_role_ck,      -- expect 1
       (to_regprocedure('public.ka_gochara_object_selector_ok(jsonb)') IS NOT NULL) AS selector_fn,                                                                                -- expect t
       EXISTS (SELECT 1 FROM public._migrations_applied WHERE starts_with(filename, '1155_')) AS m1155_recorded,                                                                       -- expect t
       NOT EXISTS (SELECT 1 FROM public._migrations_applied WHERE starts_with(filename, '1204_')) AS m1204_not_applied;                                                               -- expect t
SELECT count(*) AS av_qualifier_rows_informational FROM public.ka_gochara_relationship_record WHERE object_role = 'av_qualifier';       -- expect 0 (informational: only the rollback refuses on it)
-- the window files themselves must not be recorded yet:
SELECT count(*) AS window_files_already_recorded FROM public._migrations_applied WHERE filename IN ('1204_gochara_av_qualifier_object_role.sql', '1206_gochara_search_inventory_completeness.sql', '1232_gochara_search_moon_scope_domain.sql', '1233_gochara_p1_period_anchor.sql', '1240_gochara_window_verification_gate.sql');   -- expect 0

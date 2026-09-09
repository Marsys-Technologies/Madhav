-- 1010_nirmana_l2_bo_yantra_mechanism_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 1009 (bo_yantra_mechanism output_digest_spec) --
-- see that migration's header for the full verified account: the
-- `disp_edges` ORDER BY determinism fix, sole-writer confirmation, and the
-- live duplicate/NULL-key check. Declared per the DEP-ASSERT precedent
-- (880/908/909/910/927/930/939-940/941-942/943-944/946-947/948-949/
-- 950-951/952-953/954-955/956-957/958-959/960-961/962-963/964-965/
-- 968-969/970-971/972-973/974-975/978-979/982-983/984-985/986-987/
-- 988-989/990-991): `natural_key_partition` being NULL reads as
-- `freshness_state='unknown'` (reason `partition_undeclared`) regardless
-- of writer exclusivity or build success.

UPDATE asset_registry
   SET natural_key_partition = 'bodha_mechanisms (chart_id, ayanamsha_id, mechanism_class, fingerprint_hash) -- BoYantraMechanismWriter (@register(''bo_yantra_mechanism'')) is the confirmed sole live writer (tree-wide grep for bodha_mechanisms across platform/ found only read-only references in routers/taranga.py, services/taranga_service.py, and bg_vidhi_primitives.py, plus two test files -- no other INSERT/DELETE/UPDATE site). The table''s own live UNIQUE CONSTRAINT is (chart_id, ayanamsha_id, build_id, mechanism_class, fingerprint_hash) -- build_id excluded from this declared key because the writer''s own idempotent DELETE FROM bodha_mechanisms WHERE chart_id = %s removes all prior rows for the chart before inserting, so exactly one build_id generation exists per chart at any time (live-verified: 1 distinct build_id per chart_id, all 3 charts). Determinism fix landed same-cycle: _detect_dispositor_cycles_and_chains''s disp_edges SELECT (no prior ORDER BY, byte-order-non-determinism shape affecting member_node_ids_array/mechanism_name for convergent_dispositor_chain rows) now carries ORDER BY n1.node_subject, live-verified tie-free (0 duplicate (chart_id, ayanamsha_id, from_subject) groups across all 3 charts x 5 ayanamshas). Live-verified 0 duplicate-key groups and 0 NULLs on (ayanamsha_id, mechanism_class, fingerprint_hash) across all 1,868 live rows fleet-wide (3 charts x up to 5 ayanamshas).'
 WHERE asset_id = 'bo_yantra_mechanism'
   AND natural_key_partition IS NULL;

-- 1013_nirmana_l2_bo_upaya_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 1012 (bo_upaya output_digest_spec) -- see that
-- migration's header for the full verified account of sole-writer
-- confirmation, the six tables' natural keys, and the live duplicate/NULL
-- checks. Declared per the DEP-ASSERT precedent (880/908/909/.../
-- 1009-1010): `natural_key_partition` being NULL reads as
-- `freshness_state='unknown'` (reason `partition_undeclared`) regardless of
-- writer exclusivity or build success.

UPDATE asset_registry
   SET natural_key_partition = 'bo_upaya writes six tables, BoUpayaWriter (@register(''bo_upaya'')) confirmed sole live writer of all six (tree-wide grep for each table name across platform/ found only read-only references in bo_pramana_mapa.py, bo_samvada.py, ph_pratikara.py/engine.py -- no other INSERT/UPDATE/DELETE site; all six deleted-then-inserted per (chart_id, ayanamsha_id) via the shared bodha_writers/_idempotency.py replace_prior_rm_* helpers, live-verified exactly one build_id generation per chart x ayanamsha across all six tables). Natural keys (chart_id scoped via where_equals, build_id excluded per the standard DEP-ASSERT precedent): bodha_rm_resonances (ayanamsha_id, snapshot_type, graha) -- matches the table''s own live UNIQUE CONSTRAINT (chart_id, ayanamsha_id, build_id, snapshot_type, graha). bodha_rm_remedy_prescriptions (ayanamsha_id, snapshot_type, target_graha, tradition, remedy_category, remedy_id_g27) -- derived from the table''s live UNIQUE CONSTRAINT (chart_id, ayanamsha_id, build_id, snapshot_type, target_graha, tradition, sub_tradition, remedy_category, remedy_id_g27) with sub_tradition dropped (405/405 NULL fleet-wide, zero discriminating power; a narrower fleet-wide dup check without it still returns zero collisions). bodha_rm_chart_summary (ayanamsha_id, snapshot_type) -- matches its live UNIQUE CONSTRAINT (chart_id, ayanamsha_id, build_id, snapshot_type). bodha_rm_dosha_remedy_bundles (ayanamsha_id, dosha_class) -- matches its live UNIQUE CONSTRAINT (chart_id, ayanamsha_id, build_id, dosha_class). bodha_rm_dasha_windowed_prescriptions (ayanamsha_id, dasha_lord) -- no DB unique constraint; one row per top wealth-leverage graha per ayanamsha (writer''s _build_remedy_leverage_windows, capped at 3 distinct grahas), live-verified 0 duplicate-key groups fleet-wide across all 3 charts (20 rows). bodha_rm_pattern_remedies (ayanamsha_id, source_kind, source_id) -- no DB unique constraint; one row per resonance carrying >=1 prescription (writer''s _build_pattern_remedies, source_id=resonance_id), live-verified 0 duplicate-key groups fleet-wide across all 3 charts (135 rows). All key columns live-verified 0% NULL fleet-wide via the real compute_output_digest NULL-reviewed-key preflight (migration 1012 rehearsal) -- no vacuous key candidacy.'
 WHERE asset_id = 'bo_upaya'
   AND natural_key_partition IS NULL;

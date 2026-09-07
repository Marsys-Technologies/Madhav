-- 908_nirmana_l2_bo_nakshatra_semantic_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha) W4 pre-dispatch. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- bo_nakshatra_semantic is one of the three co-writers cleared for W4 dispatch
-- under the #1770 EXTENSION RULING (D-NATIVE-12, 2026-09-07 20:41:01Z), which
-- extended bo_sudarshana's proven canary remedy to bo_nakshatra_semantic,
-- bo_special_lagna, bo_vargottama_dhana. `bodha_msr_signals` is shared by
-- seven active L2 writers -- provenance.py's `has_cowriters` check is true
-- for all seven, so each needs its own `natural_key_partition` describing the
-- slice it actually owns, mirroring the ga_* precedent (migrations 868-874,
-- adjudication #2180) and bo_sudarshana's own fix (migration 880): without
-- it, DEP-ASSERT reads `freshness_state='unknown'` (reason
-- `partition_undeclared`) forever, regardless of a successful build.
--
-- bo_nakshatra_semantic's own ownership, verified directly against
-- pipeline/orchestrator/writers/bo_nakshatra_semantic.py's own declared
-- allowlist (BO_NAKSHATRA_SEMANTIC_OWNED_SIGNAL_TYPE_CLASSES =
-- ["nakshatra_semantic"], line 44) and bodha_writers/
-- nakshatra_semantic_emitter.py's row-construction site -- a single
-- signal_type_class, `nakshatra_semantic`. Confirmed no overlap: live
-- production (canonical chart) shows exactly 45 rows at
-- signal_type_class='nakshatra_semantic' and no other co-writer's class
-- collides with it (18 distinct classes present, one row-owner each).
--
-- Only bo_nakshatra_semantic is authored here (mirrors migration 880's own
-- stated reasoning of not collapsing several writers' provenance into one
-- rushed guess) -- bo_special_lagna and bo_vargottama_dhana get their own
-- sibling migrations (909, 910).

UPDATE asset_registry
   SET natural_key_partition = 'bodha_msr_signals.signal_type_class = nakshatra_semantic'
 WHERE asset_id = 'bo_nakshatra_semantic'
   AND natural_key_partition IS NULL;

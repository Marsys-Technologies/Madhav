-- 991_nirmana_l2_bo_sangati_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 990 (bo_sangati output_digest_spec) -- see that
-- migration's header for the full verified account: the three-table
-- co-writer investigation (BoSangatiWriter is the confirmed sole live writer
-- of bodha_cdlm_cells/bodha_convergence/bodha_triangulation; every other hit
-- across all three tables is a read), the confirmed dead-computation finding
-- (bodha_cdlm_cells.domain_relationship_class computed then discarded, never
-- bound in the INSERT), the confirmed live salience-tie non-determinism in
-- two order-sensitive array columns (bodha_convergence.top_signal_ids_array,
-- bodha_triangulation.signal_ids -- deliberately excluded from the digest,
-- every other derived column proven order-independent), and the live
-- duplicate/NULL-key check (0 duplicate groups, 0 NULLs across 280+60+195
-- rows for the canonical chart). Declared per the DEP-ASSERT precedent
-- (880/908/909/910/927/930/939-940/941-942/943-944/946-947/948-949/
-- 950-951/952-953/954-955/956-957/958-959/960-961/962-963/964-965/
-- 968-969/970-971/972-973/974-975/978-979/980-981/982-983/984-985/986-987/
-- 988-989): natural_key_partition being NULL reads as
-- freshness_state='unknown' (reason 'partition_undeclared') regardless of
-- writer exclusivity or build success.
--
-- bo_sangati differs from most prior single-table specs in this campaign by
-- owning THREE independent output tables at once, each replace-then-insert
-- per (chart_id, ayanamsha_id) with its own natural key (bodha_cdlm_cells:
-- chart_id/ayanamsha_id/snapshot_type/domain_row/domain_col;
-- bodha_convergence: chart_id/ayanamsha_id/snapshot_type/domain;
-- bodha_triangulation: chart_id/ayanamsha_id/question_class/tradition, its
-- own live UNIQUE constraint verbatim). The recorded partition text below
-- names all three tables and their per-table keys so a reader does not need
-- to cross-reference the writer source to know what this asset owns.

UPDATE asset_registry
   SET natural_key_partition = 'bodha_cdlm_cells (chart_id, ayanamsha_id, snapshot_type, domain_row, domain_col) + bodha_convergence (chart_id, ayanamsha_id, snapshot_type, domain) + bodha_triangulation (chart_id, ayanamsha_id, question_class, tradition) -- BoSangatiWriter (@register(''bo_sangati'')) is the confirmed sole live BUILD-TIME writer of all three tables (grepped tree-wide for INSERT/DELETE/UPDATE across pipeline/orchestrator/writers/*.py and bodha_writers/_idempotency.py: every other hit is a read -- bo_pramana_mapa/ka_yojaka/ph_phaladesa/ph_sankrama/bo_upaya/bo_cdlm_summary/bo_chart_gestalt read bodha_cdlm_cells; bo_pramana_mapa/bo_anveshana/bo_samvada read bodha_convergence; mi_darshana reads bodha_triangulation). Each table is replace-then-insert (or ON CONFLICT DO UPDATE preceded by an equivalent DELETE, for bodha_triangulation) scoped to (chart_id, ayanamsha_id), all 5 canonical ayanamshas rewritten every run. Live-verified 0 duplicate-key groups and 0 NULLs across all three tables for the canonical chart (280 bodha_cdlm_cells + 60 bodha_convergence + 195 bodha_triangulation rows). Two order-sensitive array columns (bodha_convergence.top_signal_ids_array, bodha_triangulation.signal_ids) are excluded from this asset''s output_digest_spec (migration 990) due to a confirmed live salience-tie non-determinism in their top-N-by-salience selection over an ORDER-BY-less bodha_msr_signals fetch -- see 990''s header for the full live-verified account and the untouched (order-independent) aggregate columns that remain safely digested.'
 WHERE asset_id = 'bo_sangati'
   AND natural_key_partition IS NULL;

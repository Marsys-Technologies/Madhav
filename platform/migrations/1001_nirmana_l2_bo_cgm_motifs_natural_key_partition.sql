-- 1001_nirmana_l2_bo_cgm_motifs_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 1000 (bo_cgm_motifs output_digest_spec) -- see that
-- migration's header for the full verified account: the three-table
-- co-writer investigation (BoCgmMotifsWriter is the confirmed sole live
-- writer of bodha_cgm_motifs/bodha_cgm_sub_graphs/
-- bodha_cgm_chart_topology_summary; every other hit across all three tables
-- is a read), the confirmed and FIXED (not carved-out) non-determinism
-- defect (unordered source SELECTs plus a Python set/frozenset-order
-- dependency in mutual-aspect detection, live-verified real via two
-- different PYTHONHASHSEED runs against the pre-fix code, then live-
-- verified fixed the same way against the post-fix code across all 5
-- ayanamshas), the dead/never-written column exclusions, and the live
-- duplicate/NULL-key check (0 duplicate groups, 0 NULLs across
-- 600+5+5 rows for the canonical chart). Declared per the DEP-ASSERT
-- precedent (880/908/909/910/927/930/939-940/941-942/943-944/946-947/
-- 948-949/950-951/952-953/954-955/956-957/958-959/960-961/962-963/
-- 964-965/968-969/970-971/972-973/974-975/978-979/980-981/982-983/
-- 984-985/986-987/988-989/996-997): natural_key_partition being NULL reads
-- as freshness_state='unknown' (reason 'partition_undeclared') regardless
-- of writer exclusivity or build success.
--
-- bo_cgm_motifs owns THREE independent output tables at once, each
-- replace-then-insert per chart_id (all 5 ayanamshas rewritten every run),
-- each with its own natural key (bodha_cgm_motifs: chart_id/ayanamsha_id/
-- snapshot_type/fingerprint_hash; bodha_cgm_sub_graphs: chart_id/
-- ayanamsha_id/subgraph_centroid_node_id; bodha_cgm_chart_topology_summary:
-- chart_id/ayanamsha_id/snapshot_type, its own live UNIQUE constraint minus
-- build_id). The recorded partition text below names all three tables and
-- their per-table keys so a reader does not need to cross-reference the
-- writer source to know what this asset owns.

UPDATE asset_registry
   SET natural_key_partition = 'bodha_cgm_motifs (chart_id, ayanamsha_id, snapshot_type, fingerprint_hash) + bodha_cgm_sub_graphs (chart_id, ayanamsha_id, subgraph_centroid_node_id) + bodha_cgm_chart_topology_summary (chart_id, ayanamsha_id, snapshot_type) -- BoCgmMotifsWriter (@register(''bo_cgm_motifs'')) is the confirmed sole live BUILD-TIME writer of all three tables (grepped tree-wide for INSERT/DELETE/UPDATE across pipeline/orchestrator/writers/*.py: every other hit is a read -- bo_yantra_mechanism/bo_karanajala/bo_bimba/bo_upaya read bodha_cgm_motifs and/or the other two tables). Each table is a per-chart delete-then-insert covering all 5 canonical ayanamshas every run. Live-verified 0 duplicate-key groups and 0 NULLs across all three tables for the canonical chart (600 bodha_cgm_motifs + 5 bodha_cgm_sub_graphs + 5 bodha_cgm_chart_topology_summary rows). A genuine non-determinism defect in the writer itself (Python set/frozenset hash-order dependency in mutual-aspect pair detection, plus two ORDER-BY-less source SELECTs) was found and FIXED at the source rather than carved out of the digest -- see migration 1000''s header for the full live-verified before/after account across all 5 ayanamshas and multiple PYTHONHASHSEED values.'
 WHERE asset_id = 'bo_cgm_motifs'
   AND natural_key_partition IS NULL;

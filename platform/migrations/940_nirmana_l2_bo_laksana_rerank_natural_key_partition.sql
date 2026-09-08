-- 940_nirmana_l2_bo_laksana_rerank_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 908/909/910/927/930/880 -- see 880 for the full
-- partition_undeclared rationale (adjudication #2180): `bodha_msr_signals`
-- is shared by seven active L2 writers and `has_cowriters` is true for all
-- seven, so DEP-ASSERT reads `freshness_state='unknown'`
-- (reason `partition_undeclared`) for any one of them without its own
-- declared partition, regardless of a successful build. Authored alongside
-- bo_laksana_rerank's output-digest spec (migration 939) -- see that
-- migration's header for the full verified account of exactly what this
-- writer touches.
--
-- bo_laksana_rerank differs from every other bodha_msr_signals co-writer
-- migrated so far (930/905-907/926/880, all of which own a
-- signal_type_class slice via row insertion): it is UPDATE-only and never
-- inserts a row, so it owns no signal_type_class value at all -- it can
-- touch a row of ANY class, chart-wide, that resolves a primary graha via
-- CGM centrality or that started as valence_source='keyword_heuristic_v1'
-- (confirmed directly against BoLaksanaRerankWriter.run()'s actual UPDATE
-- statements, pipeline/orchestrator/writers/bo_laksana.py:3910-4029 -- no
-- signal_type_class predicate anywhere in the writer body). A class-based
-- partition description would therefore misrepresent this asset's real
-- scope; the honest partition is the COLUMN set it exclusively writes
-- (mirrors migration 939's value_columns exactly, for the same reason:
-- valence/valence_source are shared-write columns, deliberately excluded).

UPDATE asset_registry
   SET natural_key_partition = 'bodha_msr_signals.graph_node_strength_contribution_jsonb / system_convergence_count / cross_system_consensus_count / contradicts_signals_array (UPDATE-only enrichment, chart-wide, no signal_type_class scope)'
 WHERE asset_id = 'bo_laksana_rerank'
   AND natural_key_partition IS NULL;

-- Migration 446: register bo_laksana_rerank (CR-84, D-2 Lane V-4)
-- Created: 2026-07-16
--
-- CR-84: close the CGM-metrics -> MSR structural_role dead link. The serving-side
-- fallback (platform/src/lib/retrieval/ranking/composite_ranker.ts::structuralRole)
-- is OUT of V-4's may_touch glob (platform/src/lib/retrieval/** is V-3's), so V-4
-- closes the link at the DATA layer: a new, acyclic post-CGM pass writes each
-- MSR signal's real CGM centrality (pagerank/eigenvector/betweenness/harmonic,
-- via its primary graha's bodha_cgm_nodes row) into the EXISTING
-- bodha_msr_signals.graph_node_strength_contribution_jsonb hook column (created
-- by migration 325 for exactly this purpose, previously always NULL).
--
-- Registered as a SEPARATE asset_id ('bo_laksana_rerank') in the SAME file
-- (bo_laksana.py, V-4's exclusive re-rank-pass file per BRIEF_D2.md Lane V-4)
-- rather than folded into bo_laksana's own depends_on, because bo_karanajala
-- already depends_on bo_laksana — adding the reverse edge onto bo_laksana
-- itself would create a DAG cycle, which is a FROZEN-orchestrator-contract-class
-- change (CLAUDE.md §N.2: "if a writer seems to need a contract change -> STOP
-- and raise with the native"). A second @register'd WriterBase in the same file,
-- ordered strictly after bo_karanajala/bo_cgm_paths in the DAG, is the
-- extension-not-modification path §N.2 already sanctions.
--
-- bo_laksana_rerank performs an UPDATE-only pass (never delete-then-insert —
-- it never touches row identity/ownership, only enriches an existing NULL hook
-- column bo_laksana itself already declares), so it is safe against the
-- bo_laksana/bo_sudarshana shared-table class of defect (F2/PR#574): it never
-- deletes any bodha_msr_signals row, of bo_laksana's or any sibling's classes.

BEGIN;

INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, target_table, count_sql,
  target_floor, depends_on, scope, has_writer, created_at
) VALUES (
  'bo_laksana_rerank', 'bodha', 21,
  'laksana_punaranka', 'Lakṣaṇa Re-rank (post-CGM)',
  'Post-CGM structural re-rank pass: writes real CGM centrality (pagerank/eigenvector/betweenness/harmonic) onto each MSR signal''s graph_node_strength_contribution_jsonb hook column, closing the CR-84 dead link. UPDATE-only, never touches row ownership.',
  'postgres_table', 'bodha_msr_signals',
  'SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND graph_node_strength_contribution_jsonb IS NOT NULL',
  1, ARRAY['bo_karanajala'], 'per_chart', true, NOW()
)
ON CONFLICT (asset_id) DO UPDATE SET
  layer                = EXCLUDED.layer,
  sanskrit_name         = EXCLUDED.sanskrit_name,
  english_name          = EXCLUDED.english_name,
  english_description   = EXCLUDED.english_description,
  storage_type          = EXCLUDED.storage_type,
  target_table          = EXCLUDED.target_table,
  count_sql             = EXCLUDED.count_sql,
  target_floor          = EXCLUDED.target_floor,
  depends_on            = EXCLUDED.depends_on,
  scope                 = EXCLUDED.scope,
  has_writer            = true;

COMMIT;

-- Migration 1416: bo_cdlm_summary full three-table receipt declaration
-- Created: 2026-11-14. Transaction owned by platform/scripts/migrate.ts.
-- Forward correction of 986/987 after qualifying the #1770 ordering fixes.
-- Preserve migration 358, its applied ledger SHA and every existing receipt.
-- This migration does NOT change the floor or output rows. Registry trigger 596
-- intentionally invalidates freshness; only a governed current-writer build may
-- establish a fresh receipt. No orchestrator or writer interface is changed.
-- Counts are chart-dependent across all three tables, not universally 5 or 70.
-- The deployed 358 floor is 1; replaying its disclosed edited source yields 5.
-- Accept both reviewed baselines without changing either; reject other drift.
-- Semantic columns include every output column except surrogate ID/build/time.
-- Reversal after receipt use must be a new reviewed forward declaration, never
-- deletion or reactivation of historical specs/receipts.

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE p text; f bigint; c text; active_sha text;
BEGIN
  SELECT md5(natural_key_partition), target_floor, md5(count_sql)
    INTO p, f, c FROM asset_registry
   WHERE asset_id = 'bo_cdlm_summary' FOR UPDATE;
  IF NOT FOUND OR f IS NULL OR f NOT IN (1, 5) OR c IS DISTINCT FROM '436138f8ef007f232680cf2673233019' THEN
    RAISE EXCEPTION 'CDLM registry floor/count contract changed; reconcile before applying 1416';
  END IF;
  SELECT spec_sha256 INTO STRICT active_sha FROM asset_output_digest_specs
   WHERE asset_id = 'bo_cdlm_summary' AND retired_at IS NULL FOR UPDATE;
  IF NOT ((active_sha = 'f6520a32a0791a64083daed074bb45592b7da430a7d1912da4a3e0f240800497' AND p = '8351098ab26c97e304038150ea7baf17')
       OR (active_sha = '635258ecb9fbfd137a048875e5a5b3a53d5179b3ac9ed64481a60fe5b402ac8e' AND p = '92288d671a134367e47f9e02f87cecdd')) THEN
    RAISE EXCEPTION 'CDLM digest/partition differs from reviewed old or new pair';
  END IF;
END
$pre$;

UPDATE asset_output_digest_specs SET retired_at = now()
 WHERE asset_id = 'bo_cdlm_summary' AND spec_sha256 = 'f6520a32a0791a64083daed074bb45592b7da430a7d1912da4a3e0f240800497'
   AND retired_at IS NULL;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES ('bo_cdlm_summary', '635258ecb9fbfd137a048875e5a5b3a53d5179b3ac9ed64481a60fe5b402ac8e', '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bodha_cdlm_chart_summary","relation":"bodha_cdlm_chart_summary","key_columns":["chart_id","ayanamsha_id","snapshot_type"],"value_columns":["chart_id","ayanamsha_id","snapshot_type","dynamic_system_id","dynamic_maha_lord","dynamic_antar_lord","tradition_view_id","chart_typology_class","pattern_cluster_markers_jsonb","total_chart_linkage","contradiction_density","house_to_domain_strength_jsonb","karaka_to_domain_strength_jsonb","dominant_3_domains_array","weakest_3_domains_array","bridge_link_count","asymmetric_link_count","verification_pass_status","citation_ref","citation_human"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}},{"name":"bodha_cdlm_domain_rollups","relation":"bodha_cdlm_domain_rollups","key_columns":["chart_id","ayanamsha_id","snapshot_type","domain"],"value_columns":["chart_id","ayanamsha_id","snapshot_type","dynamic_system_id","dynamic_maha_lord","dynamic_antar_lord","tradition_view_id","domain","total_inbound_linkage","total_outbound_linkage","diagonal_density","signal_count_for_domain","top_3_linked_domains_jsonb","contradiction_density","pattern_markers_for_domain_array","verification_pass_status","citation_ref","citation_human"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}},{"name":"bodha_cdlm_pattern_clusters","relation":"bodha_cdlm_pattern_clusters","key_columns":["chart_id","ayanamsha_id","snapshot_type","pattern_marker_type"],"value_columns":["chart_id","ayanamsha_id","snapshot_type","dynamic_system_id","dynamic_maha_lord","dynamic_antar_lord","tradition_view_id","pattern_marker_type","involved_domains_array","cluster_strength_total","involved_cells_array","involved_signals_array","contradicts_other_patterns_array","remedy_theme_jsonb","cgm_subgraph_cluster_seed","classical_archetype_match","predicted_outcome_class","active_dasha_windows_jsonb","verification_pass_status","citation_ref","citation_human"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}}]}'::jsonb)
ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

UPDATE asset_registry SET natural_key_partition = 'bodha_cdlm_chart_summary (chart_id, ayanamsha_id, snapshot_type); bodha_cdlm_domain_rollups (chart_id, ayanamsha_id, snapshot_type, domain); bodha_cdlm_pattern_clusters (chart_id, ayanamsha_id, snapshot_type, pattern_marker_type) -- BoCdlmSummaryWriter owns all three chart-replaced static_natal outputs. Canonical cell fetch order, strength-desc/domain-asc ties and sorted cluster members qualify full-table receipts. Dynamic hooks remain NULL; no temporal data or verification is fabricated. Execution IDs/build/time are excluded from the digest. Scope remains canonical chart 482012f1-710e-4a25-994a-93821f5871aa, as in 986. Prior summary-only spec and receipts remain historical evidence.'
 WHERE asset_id = 'bo_cdlm_summary'
   AND md5(natural_key_partition) = '8351098ab26c97e304038150ea7baf17';

DO $post$
BEGIN
  IF (SELECT count(*) FROM asset_output_digest_specs WHERE asset_id = 'bo_cdlm_summary' AND retired_at IS NULL) <> 1
     OR NOT EXISTS (SELECT 1 FROM asset_output_digest_specs
       WHERE asset_id = 'bo_cdlm_summary' AND spec_sha256 = '635258ecb9fbfd137a048875e5a5b3a53d5179b3ac9ed64481a60fe5b402ac8e'
         AND retired_at IS NULL AND spec = '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"bodha_cdlm_chart_summary","relation":"bodha_cdlm_chart_summary","key_columns":["chart_id","ayanamsha_id","snapshot_type"],"value_columns":["chart_id","ayanamsha_id","snapshot_type","dynamic_system_id","dynamic_maha_lord","dynamic_antar_lord","tradition_view_id","chart_typology_class","pattern_cluster_markers_jsonb","total_chart_linkage","contradiction_density","house_to_domain_strength_jsonb","karaka_to_domain_strength_jsonb","dominant_3_domains_array","weakest_3_domains_array","bridge_link_count","asymmetric_link_count","verification_pass_status","citation_ref","citation_human"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}},{"name":"bodha_cdlm_domain_rollups","relation":"bodha_cdlm_domain_rollups","key_columns":["chart_id","ayanamsha_id","snapshot_type","domain"],"value_columns":["chart_id","ayanamsha_id","snapshot_type","dynamic_system_id","dynamic_maha_lord","dynamic_antar_lord","tradition_view_id","domain","total_inbound_linkage","total_outbound_linkage","diagonal_density","signal_count_for_domain","top_3_linked_domains_jsonb","contradiction_density","pattern_markers_for_domain_array","verification_pass_status","citation_ref","citation_human"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}},{"name":"bodha_cdlm_pattern_clusters","relation":"bodha_cdlm_pattern_clusters","key_columns":["chart_id","ayanamsha_id","snapshot_type","pattern_marker_type"],"value_columns":["chart_id","ayanamsha_id","snapshot_type","dynamic_system_id","dynamic_maha_lord","dynamic_antar_lord","tradition_view_id","pattern_marker_type","involved_domains_array","cluster_strength_total","involved_cells_array","involved_signals_array","contradicts_other_patterns_array","remedy_theme_jsonb","cgm_subgraph_cluster_seed","classical_archetype_match","predicted_outcome_class","active_dasha_windows_jsonb","verification_pass_status","citation_ref","citation_human"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}}]}'::jsonb)
     OR NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'bo_cdlm_summary'
       AND md5(natural_key_partition) = '92288d671a134367e47f9e02f87cecdd' AND target_floor IN (1, 5)
       AND md5(count_sql) = '436138f8ef007f232680cf2673233019') THEN
    RAISE EXCEPTION 'CDLM three-table receipt declaration postcondition failed';
  END IF;
END
$post$;

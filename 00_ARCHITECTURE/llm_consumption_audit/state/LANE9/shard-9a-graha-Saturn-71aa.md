# shard-9a-graha-Saturn-71aa

- shard_id: graha-Saturn
- node_key: graha:Saturn:71aa
- node_id: 62db1981-2f9f-49bf-aae9-a43d4d7d2e6e
- chart_id: 482012f1-710e-4a25-994a-93821f5871aa
- axis: STRUCTURAL only (9a). Consumption=LCA-1, leverage=LCA-2 (known fixed) — not re-probed.

## Verbatim SQL — structural recipe
```sql
WITH nbr AS (SELECT e.edge_id,e.edge_type,e.from_node_id,e.to_node_id,e.citation_ref,e.underlying_msr_signal_ids_array FROM bodha_cgm_edges e WHERE e.chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND (e.from_node_id='62db1981-2f9f-49bf-aae9-a43d4d7d2e6e' OR e.to_node_id='62db1981-2f9f-49bf-aae9-a43d4d7d2e6e'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count, (SELECT string_agg(DISTINCT edge_type,',') FROM nbr) edge_types,
  (SELECT SUM((citation_ref IS NOT NULL)::int)||'/'||COUNT(*) FROM nbr) cited,
  (SELECT SUM((underlying_msr_signal_ids_array IS NOT NULL AND array_length(underlying_msr_signal_ids_array,1)>0)::int)||'/'||COUNT(*) FROM nbr) msr_backed;
```
plus neighbor-node-type and temporal-hook probes.

## Verbatim results
- edge_count = 25
- edge_types = argala,aspect,dispositor
- cited = 25/25
- msr_backed = 16/25
- neighbor node_types = graha (ONLY)
- temporal_dasha = 0 ; active_duration_class = natal_permanent

## Structural grades
- reaches_dispositor: TRUE
- reaches_bhava_lordship: FALSE (no bhava neighbor)
- reaches_yoga: FALSE (no yoga node_type)
- reaches_temporal_hook: FALSE (temporal_dasha=0)
- citation_ratio: 25/25 (100%)
- msr_backed_ratio: 16/25 (64.0%)
- structural_verdict: THIN (reaches 1 of 4)

## Findings
1. [class 1 UNREACHABLE, HIGH] Saturn reaches ZERO bhava nodes (neighbors=graha only; 60 bhava exist chart-wide). Bhava-lordship linkage untraversable.
2. [class 4 EMPTY SHELL, HIGH] reaches_yoga structurally impossible (no yoga node_type). Saturn's yoga memberships unreachable. Consistent with G-6.
3. [class 4 EMPTY SHELL, MED] No temporal hook: active_dasha_periods_jsonb empty on all 25 edges; natal_permanent only; no temporal edge_type. Especially notable for Saturn (sade-sati / dasha relevance) — temporal presence facet absent.
4. [class 6 UNUSABLE FORM, LOW] MSR attribution partial: 9 of 25 edges lack underlying_msr_signal_ids_array (16/25, 64% — lowest MSR-backing of the sampled grahas).

## Completion marker
STRUCTURAL axis COMPLETE for graha:Saturn:71aa.

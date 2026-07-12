# shard-9a-graha-Sun-71aa

- shard_id: graha-Sun
- node_key: graha:Sun:71aa
- node_id: 76796059-1c1a-4ba9-a8e7-191f38ea6cf6
- chart_id: 482012f1-710e-4a25-994a-93821f5871aa
- axis: STRUCTURAL only (9a). Consumption=LCA-1, leverage=LCA-2 (known fixed) — not re-probed.

## Verbatim SQL — structural recipe
```sql
WITH nbr AS (SELECT e.edge_id,e.edge_type,e.from_node_id,e.to_node_id,e.citation_ref,e.underlying_msr_signal_ids_array FROM bodha_cgm_edges e WHERE e.chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND (e.from_node_id='76796059-1c1a-4ba9-a8e7-191f38ea6cf6' OR e.to_node_id='76796059-1c1a-4ba9-a8e7-191f38ea6cf6'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count, (SELECT string_agg(DISTINCT edge_type,',') FROM nbr) edge_types,
  (SELECT SUM((citation_ref IS NOT NULL)::int)||'/'||COUNT(*) FROM nbr) cited,
  (SELECT SUM((underlying_msr_signal_ids_array IS NOT NULL AND array_length(underlying_msr_signal_ids_array,1)>0)::int)||'/'||COUNT(*) FROM nbr) msr_backed;
```
plus neighbor-node-type and temporal-hook probes.

## Verbatim results
- edge_count = 23
- edge_types = argala,aspect,dispositor
- cited = 23/23
- msr_backed = 16/23
- neighbor node_types = graha (ONLY)
- temporal_dasha = 0 ; active_duration_class = natal_permanent

## Structural grades
- reaches_dispositor: TRUE
- reaches_bhava_lordship: FALSE (no bhava neighbor)
- reaches_yoga: FALSE (no yoga node_type)
- reaches_temporal_hook: FALSE (temporal_dasha=0)
- citation_ratio: 23/23 (100%)
- msr_backed_ratio: 16/23 (69.6%)
- structural_verdict: THIN (reaches 1 of 4)

## Findings
1. [class 1 UNREACHABLE, HIGH] Sun reaches ZERO bhava nodes (neighbors=graha only; 60 bhava exist chart-wide). Bhava-lordship linkage untraversable.
2. [class 4 EMPTY SHELL, HIGH] reaches_yoga structurally impossible (no yoga node_type). Sun's yoga memberships unreachable. Consistent with G-6.
3. [class 4 EMPTY SHELL, MED] No temporal hook: active_dasha_periods_jsonb empty on all 23 edges; natal_permanent only; no temporal edge_type.
4. [class 6 UNUSABLE FORM, LOW] MSR attribution partial: 7 of 23 edges lack underlying_msr_signal_ids_array (16/23).

## Completion marker
STRUCTURAL axis COMPLETE for graha:Sun:71aa.

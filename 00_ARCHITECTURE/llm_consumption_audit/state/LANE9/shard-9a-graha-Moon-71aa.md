# shard-9a-graha-Moon-71aa

- shard_id: graha-Moon
- node_key: graha:Moon:71aa
- node_id: 42f702df-86b5-443c-ba4e-625604e29658
- chart_id: 482012f1-710e-4a25-994a-93821f5871aa
- axis: STRUCTURAL only (9a). Consumption=LCA-1 (known fixed), leverage=LCA-2 (known fixed) — not re-probed.

## Verbatim SQL — structural recipe
```sql
WITH nbr AS (SELECT e.edge_id,e.edge_type,e.from_node_id,e.to_node_id,e.citation_ref,e.underlying_msr_signal_ids_array FROM bodha_cgm_edges e WHERE e.chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND (e.from_node_id='42f702df-86b5-443c-ba4e-625604e29658' OR e.to_node_id='42f702df-86b5-443c-ba4e-625604e29658'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count,
  (SELECT string_agg(DISTINCT edge_type,',') FROM nbr) edge_types,
  (SELECT SUM((citation_ref IS NOT NULL)::int)||'/'||COUNT(*) FROM nbr) cited,
  (SELECT SUM((underlying_msr_signal_ids_array IS NOT NULL AND array_length(underlying_msr_signal_ids_array,1)>0)::int)||'/'||COUNT(*) FROM nbr) msr_backed;
```
plus neighbor-node-type and temporal-hook probes (same as Mercury shard).

## Verbatim results
- edge_count = 26
- edge_types = argala,aspect,dispositor,dosha_domain
- cited = 26/26
- msr_backed = 19/26
- neighbor node_types = domain,graha  (reaches domain nodes via dosha_domain edge; still ZERO bhava)
- temporal_dasha = 0 ; active_duration_class = natal_permanent

## Structural grades
- reaches_dispositor: TRUE
- reaches_bhava_lordship: FALSE (neighbors are graha + domain; no node_type='bhava')
- reaches_yoga: FALSE (no yoga node_type exists in graph)
- reaches_temporal_hook: FALSE (temporal_dasha=0; natal_permanent only)
- citation_ratio: 26/26 (100%)
- msr_backed_ratio: 19/26 (73.1%)
- structural_verdict: THIN (reaches 1 of 4)

## Findings
1. [class 1 UNREACHABLE, HIGH] Moon reaches ZERO bhava nodes despite 60 in-graph. Bhava-lordship linkage untraversable. Moon DOES reach `domain` nodes (via dosha_domain edge) — the only sampled graha to reach a non-graha type — but domain != bhava; house rulership still unrecoverable.
2. [class 4 EMPTY SHELL, HIGH] reaches_yoga structurally impossible (no node_type='yoga'; types=bhava/graha/domain). Moon's yoga memberships unreachable via graph. Consistent with G-6.
3. [class 4 EMPTY SHELL, MED] No temporal hook: active_dasha_periods_jsonb empty on all 26 edges; active_duration_class=natal_permanent only; no temporal edge_type.
4. [class 6 UNUSABLE FORM, LOW] MSR attribution partial: 7 of 26 edges (19/26) lack underlying_msr_signal_ids_array.

## Completion marker
STRUCTURAL axis COMPLETE for graha:Moon:71aa.

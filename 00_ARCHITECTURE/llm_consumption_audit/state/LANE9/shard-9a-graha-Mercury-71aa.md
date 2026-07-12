# shard-9a-graha-Mercury-71aa

- shard_id: graha-Mercury
- node_key: graha:Mercury:71aa
- node_id: d2665fe6-9f72-496a-914c-6060fa93f90f
- chart_id: 482012f1-710e-4a25-994a-93821f5871aa
- axis: STRUCTURAL only (9a). Consumption axis = KNOWN fixed finding LCA-1 (get_cgm_subgraph→cgm_graph_walk dead/unresolvable); leverage axis = KNOWN fixed finding LCA-2 (consult broken). Not re-probed per lane assignment.

## Verbatim SQL — structural recipe (proven on Jupiter=23 edges)
```sql
WITH nbr AS (SELECT e.edge_id,e.edge_type,e.from_node_id,e.to_node_id,e.citation_ref,e.underlying_msr_signal_ids_array FROM bodha_cgm_edges e WHERE e.chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND (e.from_node_id='d2665fe6-9f72-496a-914c-6060fa93f90f' OR e.to_node_id='d2665fe6-9f72-496a-914c-6060fa93f90f'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count,
  (SELECT string_agg(DISTINCT edge_type,',') FROM nbr) edge_types,
  (SELECT SUM((citation_ref IS NOT NULL)::int)||'/'||COUNT(*) FROM nbr) cited,
  (SELECT SUM((underlying_msr_signal_ids_array IS NOT NULL AND array_length(underlying_msr_signal_ids_array,1)>0)::int)||'/'||COUNT(*) FROM nbr) msr_backed;
-- neighbor node types:
SELECT DISTINCT n.node_type FROM bodha_cgm_nodes n WHERE n.chart_id='482012f1-...' AND n.node_id IN (SELECT to_node_id FROM bodha_cgm_edges WHERE ... from_node_id='d2665fe6-...' UNION SELECT from_node_id ... to_node_id='d2665fe6-...');
-- temporal hook probe (active_dasha_periods_jsonb populated + active_duration_class):
--   SUM(active_dasha_periods_jsonb NOT IN null/[]/{}) AS temporal_dasha, string_agg(DISTINCT active_duration_class)
```

## Verbatim results
- edge_count = 23
- edge_types = argala,aspect,dispositor
- cited (citation_ref) = 23/23
- msr_backed (underlying_msr_signal_ids_array non-empty) = 16/23
- neighbor node_types = graha  (ONLY graha; zero bhava, zero domain)
- temporal_dasha = 0 ; active_duration_class = natal_permanent (only value)

## Graph vocabulary context (chart-level)
`SELECT node_type,COUNT(*) FROM bodha_cgm_nodes WHERE chart_id='482012f1-...' GROUP BY node_type` →
bhava=60, graha=45, domain=35. **No node_type='yoga' exists in the graph at all.**

## Structural grades
- reaches_dispositor: TRUE (edge_type='dispositor' present)
- reaches_bhava_lordship: FALSE (no neighbor node_type='bhava'; 60 bhava nodes exist in graph but Mercury links to none)
- reaches_yoga: FALSE (no node_type='yoga' exists — yogas are not first-class graph nodes)
- reaches_temporal_hook: FALSE (temporal_dasha=0; all edges natal_permanent; no temporal edge_type)
- citation_ratio: 23/23 (100%)
- msr_backed_ratio: 16/23 (69.6%)
- structural_verdict: THIN (reaches 1 of 4 completeness targets)

## Findings
1. [class 1 UNREACHABLE, HIGH] Mercury graha node reaches ZERO bhava nodes. Its dispositor/aspect/argala neighborhood terminates entirely on other grahas; bhava-lordship linkage (which bhavas Mercury owns/occupies) is not traversable from the node. Evidence: neighbor node_types = "graha" only, though bhava=60 exist chart-wide. A synthesis consuming Mercury's neighborhood cannot recover its house rulership from the graph.
2. [class 4 EMPTY SHELL, HIGH] reaches_yoga structurally impossible: no node_type='yoga' in bodha_cgm_nodes (types = bhava/graha/domain only). Consistent with G-6 (no multi-hop/yoga chain surface). Mercury's yoga memberships cannot be reached via graph traversal.
3. [class 4 EMPTY SHELL, MED] No temporal hook: active_dasha_periods_jsonb empty on all 23 edges (temporal_dasha=0), active_duration_class uniformly natal_permanent, no temporal edge_type. The MD/AD/PD temporal presence facet is absent from the neighborhood.
4. [class 6 UNUSABLE FORM, LOW] MSR attribution partial: 7 of 23 edges (16/23 backed) carry no underlying_msr_signal_ids_array, so ~30% of Mercury's edges cannot be traced to an MSR signal (citation_ref is present 23/23, so classical-citation correctness holds, but MSR-signal provenance is incomplete).

## Completion marker
STRUCTURAL axis COMPLETE for graha:Mercury:71aa.

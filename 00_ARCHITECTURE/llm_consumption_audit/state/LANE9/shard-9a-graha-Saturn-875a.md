# Lane 9a STRUCTURAL shard — graha:Saturn:875a

- node_id: 2d3b88a3-8cba-43b7-a509-aafef105069e
- node_type: graha, node_subject: Saturn
- chart_id: 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan)
- axis: STRUCTURAL only (consumption/leverage = KNOWN fixed LCA-1/LCA-2, not re-probed)

## Recipe query (verbatim) + result
```sql
WITH nbr AS (SELECT e.edge_id,e.edge_type,e.from_node_id,e.to_node_id,e.citation_ref,e.underlying_msr_signal_ids_array
  FROM bodha_cgm_edges e WHERE e.chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a'
  AND (e.from_node_id='2d3b88a3-8cba-43b7-a509-aafef105069e' OR e.to_node_id='2d3b88a3-8cba-43b7-a509-aafef105069e'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count, (SELECT string_agg(DISTINCT edge_type,',') FROM nbr) edge_types,
  (SELECT SUM((citation_ref IS NOT NULL)::int)||'/'||COUNT(*) FROM nbr) cited,
  (SELECT SUM((underlying_msr_signal_ids_array IS NOT NULL AND array_length(underlying_msr_signal_ids_array,1)>0)::int)||'/'||COUNT(*) FROM nbr) msr_backed;
```
RESULT (verbatim): edge_count=24 · edge_types=`argala,aspect,dispositor` · cited=`24/24` · msr_backed=`16/24`

Neighbor node_types query result (verbatim): only `graha`.

Temporal check (active_dasha_periods_jsonb / active_duration_class over the 24 edges):
temporal_pop=0 · dur_classes=`natal_permanent` · n=24.

## Grades
- reaches_dispositor: TRUE (edge_types contains `dispositor`)
- reaches_bhava_lordship: FALSE (all 24 neighbors node_type=graha; zero bhava neighbor. Chart-wide: edges touch only graha(1031)+domain(15) endpoints — NO edge in the whole graph touches a bhava node)
- reaches_yoga: FALSE (bodha_cgm_nodes has no node_type=yoga; 140 signal_type_class=yoga MSR signals exist but are absent as graph nodes)
- reaches_temporal_hook: FALSE (active_dasha_periods_jsonb empty on all 24 edges; active_duration_class uniformly `natal_permanent`; no temporal edge_type)
- citation_ratio: 24/24 (100%) · msr_backed_ratio: 16/24 (66.7%)

## Structural verdict: THIN (reaches 1 of 4: dispositor only)

## Findings
- F1 class-1 UNREACHABLE (high): graha node reaches NO bhava lordship — graph never wires graha↔bhava edges (chart-wide 0 bhava endpoints). Dispositor chain to bhava lords not traversable.
- F2 class-1 UNREACHABLE (high): 140 yoga MSR signals not represented as graph nodes; yoga membership structurally unreachable from any graha node.
- F3 class-1 UNREACHABLE (medium): no temporal hook — active_dasha_periods_jsonb null across all edges, natal_permanent only; structural×temporal convergence not available in graph.
- F4 class-6 UNUSABLE FORM (low): 8/24 edges (33%) carry no underlying_msr_signal_ids_array (msr_backed 16/24), weakening derivation-ledger traceability though citation_ref is 100%.

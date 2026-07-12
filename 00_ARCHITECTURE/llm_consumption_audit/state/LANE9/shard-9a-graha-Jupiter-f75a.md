# Shard 9a STRUCTURAL — node_key `graha:Jupiter:f75a`

- node_id: `e1a7bdb2-316c-42a1-900d-bad02d51f992`
- chart_id: `1c826d5a-41cb-4450-b4dc-59d440e5f75a`

## Query 1 — edge recipe (verbatim)
```sql
WITH nbr AS (SELECT e.edge_id,e.edge_type,e.from_node_id,e.to_node_id,e.citation_ref,e.underlying_msr_signal_ids_array FROM bodha_cgm_edges e WHERE e.chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a' AND (e.from_node_id='e1a7bdb2-316c-42a1-900d-bad02d51f992' OR e.to_node_id='e1a7bdb2-316c-42a1-900d-bad02d51f992'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count, (SELECT string_agg(DISTINCT edge_type,',') FROM nbr) edge_types, (SELECT SUM((citation_ref IS NOT NULL)::int)||'/'||COUNT(*) FROM nbr) cited, (SELECT SUM((underlying_msr_signal_ids_array IS NOT NULL AND array_length(underlying_msr_signal_ids_array,1)>0)::int)||'/'||COUNT(*) FROM nbr) msr_backed;
```
Result (verbatim): edge_count=`26` · edge_types=`argala,aspect,dispositor` · cited=`26/26` · msr_backed=`16/26`

## Query 2 — neighbor node types + temporal hook
Result (verbatim): neighbor_types=`graha` · temporal(active_dasha_periods_jsonb populated)=`0/26`

## Grades
- reaches_dispositor: **true** (`dispositor` in edge_types)
- reaches_bhava_lordship: **false** (neighbor_types=`graha` only; no `bhava` neighbor)
- reaches_yoga: **false** (no `yoga` node_type exists in bodha_cgm_nodes; no yoga edge)
- reaches_temporal_hook: **false** (`0/26` edges carry active_dasha_periods_jsonb; no temporal edge_type)
- citation_ratio: `26/26` (100% — B.3 satisfied)
- msr_backed_ratio: `16/26`
- structural_verdict: **THIN** (reaches 1 of 4 required dimensions)

## Findings
- F1 (class 1 UNREACHABLE, high): Jupiter's node reaches no `bhava` node — bhava-lordship context is structurally unreachable via graph traversal. Evidence: neighbor_types=`graha` only over 26 edges.
- F2 (class 1 UNREACHABLE, high): yogas are not first-class graph nodes; Jupiter cannot reach any yoga. Evidence: 0 yoga neighbors; bodha_cgm_nodes has no node_type='yoga'.
- F3 (class 4 EMPTY SHELL, high): temporal hooks absent — active_dasha_periods_jsonb populated on `0/26` edges; the temporal column exists but is never filled.

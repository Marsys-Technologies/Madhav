# Lane 9a STRUCTURAL shard — bhava:4:f75a

- node_id: 53e5244e-d6cf-4b27-b5c2-8618d0e0659d
- node_type: bhava, node_subject: 4
- chart_id: 1c826d5a-41cb-4450-b4dc-59d440e5f75a
- axis: STRUCTURAL only (consumption=LCA-1 fixed, leverage=LCA-2 fixed — not re-probed)

## SQL (proven recipe)
```sql
WITH nbr AS (SELECT e.edge_id,e.edge_type,e.from_node_id,e.to_node_id,e.citation_ref,e.underlying_msr_signal_ids_array
 FROM bodha_cgm_edges e WHERE e.chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a'
 AND (e.from_node_id='53e5244e-d6cf-4b27-b5c2-8618d0e0659d' OR e.to_node_id='53e5244e-d6cf-4b27-b5c2-8618d0e0659d'))
SELECT (SELECT COUNT(*) FROM nbr) edge_count, (SELECT string_agg(DISTINCT edge_type,',') FROM nbr) edge_types,
  (SELECT SUM((citation_ref IS NOT NULL)::int)||'/'||COUNT(*) FROM nbr) cited,
  (SELECT SUM((underlying_msr_signal_ids_array IS NOT NULL AND array_length(underlying_msr_signal_ids_array,1)>0)::int)||'/'||COUNT(*) FROM nbr) msr_backed;
```

## VERBATIM RESULT
```
edge_count=0  edge_types=null  cited=null  msr_backed=null
```
Neighbor node types query returned zero rows (no incident edges → no neighbors).

## Grades
- edge_count: 0
- reaches_dispositor: false
- reaches_bhava_lordship: false (bhava-4 lord graha never reached — 0 edges)
- reaches_yoga: false (no edge; AND bodha_cgm_nodes has NO node_type='yoga' — yogas are not first-class graph nodes)
- reaches_temporal_hook: false
- citation_ratio: 0/0 (n/a — no edges)
- msr_backed_ratio: 0/0 (n/a — no edges)
- structural_verdict: ISOLATED

## Systemic context (conductor cross-check query)
All 60 bhava nodes in this chart: 0 with edges, 0 total incident edges.
Graha: 45/45 with edges, 1031 edges. Domain: 15/35, 15 edges.
Bhava isolation is systemic, not node-specific.

## Findings
1. [class 1 UNREACHABLE, HIGH] Bhava-4 node is ISOLATED (0 edges). The CGM promise — "for any
   node it should yield the associated relevant data points a synthesis must consider" — fails
   completely for this node: no dispositor, no bhava-lord, no occupant, no aspect, no temporal
   hook edge exists. A consuming LLM traversing bhava-4's neighborhood receives nothing.
   Evidence: edge_count=0 verbatim above; systemic 0/60 bhava nodes edged.
   Suspected layer: L-writer (bo_karanajala edge-build never emits bhava-incident edges).
2. [class 4 EMPTY SHELL, MED] reaches_yoga structurally impossible: bodha_cgm_nodes has only
   node_types {bhava,domain,graha} — no yoga node. Yogas cannot be reached via the graph for
   any node. (G-6-adjacent structural finding.)
